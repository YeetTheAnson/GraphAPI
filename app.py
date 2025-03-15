import matplotlib
matplotlib.use('Agg')

from flask import Flask, request, send_file, jsonify
import matplotlib.pyplot as plt
import numpy as np
import urllib.parse
import io
import random
import time
import re
from collections import deque
import threading
import psutil


app = Flask(__name__)

graph_cache = deque(maxlen=50)
cache_lock = threading.Lock()

last_health_check = 0
health_check_lock = threading.Lock()

class CachedGraph:
    def __init__(self, equation, image_buffer, category=None, params=None):
        self.equation = equation
        self.image_buffer = image_buffer
        self.category = category
        self.params = params
        self.timestamp = time.time()
        self.expires_at = self.timestamp + (5 * 60 * 60)  # 5 hours in seconds
        self.id = str(hash(f"{equation}_{self.timestamp}"))[-8:]

def clean_expired_graphs():
    current_time = time.time()
    with cache_lock:
        expired = [graph for graph in list(graph_cache) if current_time > graph.expires_at]
        for graph in expired:
            graph_cache.remove(graph)
        return len(expired)

def parse_latex_to_python(latex_expr):
    original_expr = latex_expr

    latex_expr = latex_expr.replace('\\left', '').replace('\\right', '')

    # Convert latex \frac to to matplotlib fractions
    while '\\frac' in latex_expr:
        # Using chatgpt to write the regrex expression 😭
        # Basically what it does is matching the \frac latex expression and then isolating the numerator and denominator
        match = re.search(r'\\frac\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}', latex_expr)
        if not match:
            break
        
        numerator = match.group(1)
        denominator = match.group(2)

        replacement = f"(({numerator})/({denominator}))"
        latex_expr = latex_expr[:match.start()] + replacement + latex_expr[match.end():]

    while '\\sqrt' in latex_expr:
        match = re.search(r'\\sqrt\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}', latex_expr)
        if not match:
            break

        content = match.group(1)

        replacement = f"np.sqrt({content})"
        latex_expr = latex_expr[:match.start()] + replacement + latex_expr[match.end():]


    latex_expr = latex_expr.replace('\\cdot','*')


    replacements = {
        '\\sin': 'np.sin',
        '\\cos': 'np.cos',
        '\\tan': 'np.tan',
        '\\arcsin': 'np.arcsin',
        '\\arccos': 'np.arccos',
        '\\arctan': 'np.arctan',
        '\\sinh': 'np.sinh',
        '\\cosh': 'np.cosh',
        '\\tanh': 'np.tanh',
        '\\exp': 'np.exp',
        '\\log': 'np.log',
        '\\ln': 'np.log',
        '\\pi': 'np.pi',
        '^': '**'
    }

    for latex_func, py_func in replacements.items():
        latex_expr = latex_expr.replace(latex_func, py_func)

    latex_expr = latex_expr.replace('{', '(').replace('}', ')')

    np_functions = ["np.sin", "np.cos", "np.tan", "np.arcsin", "np.arccos", "np.arctan", "np.sinh", "np.cosh", "np.tanh", "np.exp", "np.log", "np.sqrt"]
    
    for func in np_functions:
        pattern = f"{func} ([a-zA-Z0-9]+)"
        latex_expr = re.sub(pattern, f"{func}(\\1)", latex_expr)

    latex_expr = re.sub(r'\)\s*\(', ')*(', latex_expr)
    
    # When numbers are next to variables, it needs to be converted into multiplication
    latex_expr = re.sub(r'(\d)([a-zA-Z])', r'\1*\2', latex_expr)

    open_count = latex_expr.count('(')
    close_count = latex_expr.count(')')

    if open_count > close_count:
        latex_expr += ')' * (open_count - close_count)

    return latex_expr


def generate_random_equation(category):
    # Parameter n are random integers while p are float to one decimal point
    equations = {
        'sqrt': [
            (r'\sqrt{\frac{n}{x}}\cdot x', (-10, 10), None)
        ],
        'polynomial': [
            (r'5^{x^{p}}', None, (-5, 3)),
            (r'x^{n}+x^{n}+x^{n}+x^{n}', (1, 6), None)
        ],
        'linear': [
            (r'5\cdot p\cdot(x-p)+p', None, (-10, 10))
        ],
        'trigonometry': [
            (r'n\sin(n\arccos x)', (-5, 5), None),
            (r'\frac{n}{x}\cdot\sinh(n\cdot x)', (-3, 3), None),
            (r'p\cdot\sin(p\cdot x)+p', None, (-5, 5))
        ],
        'exponential': [
            (r'p\cdot p ^{p\cdot(x-p)}+p', None, (-3, 3))
        ],
        'logarithm': [
            (r'p\cdot\ln(p\cdot(x-p))+p', None, (-3,3))
        ],
        'reciprocal': [
            (r'\frac{p}{(x-p)}+p', None, (-5, 5))
        ]
    }

    if category not in equations or not equations[category]:
        return None, None, None
    
    equation_template, n_range, p_range = random.choice(equations[category])

    params = {}

    # Substitute n and p with random numbers to make random graph
    if n_range:
        modified_template = equation_template
        n_count = modified_template.count('n')

        for i in range (n_count):
            params[f'n_{i}'] = random.randint(n_range[0], n_range[1])

        for i in range (n_count):
            # Regex to make sure other part of the string is not matched
            modified_template = re.sub(r'(?<![a-zA-Z])n(?![a-zA-Z])', str(params[f'n_{i}']), modified_template, count=1)

        equation_template = modified_template

    if p_range:
        modified_template = equation_template
        p_count = modified_template.count('p')

        for i in range(p_count):
            params[f'p_{i}'] = round(random.uniform(p_range[0], p_range[1]), 1)
        
        for i in range(p_count):
            # Regex to make sure other part of the string is not matched
            modified_template = re.sub(r'(?<![a-zA-Z])p(?![a-zA-Z])', str(params[f'p_{i}']), modified_template, count=1)
        
        equation_template = modified_template
    
    original_eq = equation_template

    return equation_template, params, original_eq


def generate_plot(equation, python_eq, x_scale, y_scale, data_points, title=None, params=None):
    x_min = -x_scale / 2
    x_max = x_scale / 2
    x_vals = np.linspace(x_min, x_max, data_points)

    def safe_eval(eq, x_val):
        try:
            eq_with_value = eq.replace('x', f'({x_val})')

            if eq_with_value.count('(') != eq_with_value.count(')'):
                print(f"Parentheses are not balanced: {eq_with_value}")
                return np.nan
            
            result = eval(eq_with_value)

            # Upper and lower boundaries

            if isinstance(result, (int, float)):
                if result > 1e10:
                    return 1e10
                if result < -1e10:
                    return -1e10
                
            return result
        except Exception as e:
            print(f"Error evaluating at x={x_val}: {e}")
            return np.nan
        
    y_vals = np.array([safe_eval(python_eq, x) for x in x_vals])
    plt.figure(figsize=(10, 8), dpi=100, facecolor='white')

    y_min = -y_scale / 2
    y_max = y_scale / 2

    valid_indices = np.where((y_vals >= y_min) & (y_vals <= y_max) & ~np.isnan(y_vals) & ~np.isinf(y_vals))
    valid_x = x_vals[valid_indices]
    valid_y = y_vals[valid_indices]

    if len(valid_x) > 1:
        x_step = (x_max - x_min) / (data_points - 1)
        x_gaps = np.where(np.diff(valid_x) > 1.5 * x_step)[0]
        y_jumps = np.where(np.abs(np.diff(valid_y)) > (y_max - y_min) / 20)[0]

        all_breaks = np.unique(np.concatenate((x_gaps, y_jumps)))
        segments_x = np.split(valid_x, all_breaks + 1)
        segments_y = np.split(valid_y, all_breaks + 1)

        for seg_x, seg_y in zip(segments_x, segments_y):
            if len(seg_x) > 1:
                plt.plot(seg_x, seg_y, 'b-', linewidth=2)
            elif len(seg_x) == 1:
                plt.scatter(seg_x, seg_y, color='blue', s=20)
    elif len(valid_x) == 1:
        plt.scatter(valid_x, valid_y, color='blue', s=20)
    else:
        y_vals_clipped = np.clip(y_vals, y_min, y_max)
        mask = np.isnan(y_vals_clipped) | np.isinf(y_vals_clipped)
        y_vals_clipped[mask] = np.nan
        mask = ~np.isnan(y_vals_clipped)
        runs = np.split(np.arange(len(mask)), np.where(~mask)[0])

        for run in runs:
            if len(run) > 0:
                plt.plot(x_vals[run], y_vals_clipped[run], 'b-', linewidth=2)
    
    plt.xlim(x_min, x_max)
    plt.ylim(y_min, y_max)

    plt.grid(True, alpha=0.3)
    plt.axhline(y=0, color='k', linestyle='-', alpha=0.5, linewidth=1)
    plt.axvline(x=0, color='k', linestyle='-', alpha=0.5, linewidth=1)

    if title:
        plt.title(title, fontsize=12)
    else:
        plt.title(f"Plot of {equation}", fontsize=12)

    plt.xlabel('x', fontsize=12)
    plt.ylabel('y', fontsize=12)

    if params:
        param_text = ", ".join([f"{k.split('_')[0]} = {v}" for k, v in params.items()])
        plt.figtext(0.5, 0.01, f"Parameters: {param_text}", ha='center', fontsize=10)
    
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close('all')

    return buf

def create_no_cache_image():
    plt.figure(figsize=(10, 8), dpi=100, facecolor='white')
    plt.text(0.5, 0.5, "No cached graphs available", ha='center', fontsize=20)
    plt.text(0.5, 0.4, "Generate some graphs first!", ha='center', va='center', fontsize=16)
    plt.axis('off')
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close('all')
    return buf

@app.route('/plot', methods=['GET'])
def plot_equation():
    eq_string = request.args.get('equation', '')
    x_scale = int(request.args.get('x_scale', 20))
    y_scale = int(request.args.get('y_scale', 20))
    data_points = int(request.args.get('data_points', 1000))
    
    MAX_DATA_POINTS = 100000
    if data_points > MAX_DATA_POINTS:
        data_points = MAX_DATA_POINTS

    eq_string = urllib.parse.unquote(eq_string)
    print(f"Received: {eq_string}")
    try:
        python_eq = parse_latex_to_python(eq_string)
        print(f"Converted equation: {python_eq}")
        buf = generate_plot(eq_string, python_eq, x_scale, y_scale, data_points)
        cache_buf = io.BytesIO(buf.getvalue())
        cache_buf.seek(0)
        with cache_lock:
            graph_cache.append(CachedGraph(eq_string, cache_buf))
            print(f"Graph cached. Total cached graphs: {len(graph_cache)}")
        return send_file(buf, mimetype='image/png')
    except Exception as e:
        import traceback
        traceback_str = traceback.format_exc()
        print(f"Error: {str(e)}\n{traceback_str}")
        return f"Error: {str(e)}", 400
    

@app.route('/random', methods =['GET'])
def random_equation():
    category = request.args.get('category', '')
    x_scale = int(request.args.get('x_scale', 20))
    y_scale = int(request.args.get('y_scale', 20))
    data_points = int(request.args.get('data_points', 1000))
    
    MAX_DATA_POINTS = 100000
    if data_points > MAX_DATA_POINTS:
        data_points = MAX_DATA_POINTS

    valid_categories = ['sqrt', 'polynomial', 'linear', 'trigonometry', 'exponential', 'logarithm', 'reciprocal']

    if category not in valid_categories:
        return f"Error: Invalid category. Valid options are: {', '.join(valid_categories)}", 400
    try:
        equation, params, original_eq = generate_random_equation(category)
        if not equation:
            return f"Error: No equations available for selected category '{category}'", 400
    
        print(f"Generated equations: {equation}")
        print(f"With parameters: {params}")

        python_eq = parse_latex_to_python(equation)
        print(f"Converted  to Python: {python_eq}")
        title = f"Random {category} equation: {equation}"

        buf = generate_plot(equation, python_eq, x_scale, y_scale, data_points, title, params)
        cache_buf = io.BytesIO(buf.getvalue())
        cache_buf.seek(0)

        with cache_lock:
            graph_cache.append(CachedGraph(equation, cache_buf, category, params))
            print(f"Random graph cached. Total cached graphs: {len(graph_cache)}")
        
        return send_file(buf, mimetype='image/png')
    except Exception as e:
        import traceback
        traceback_str = traceback.format_exc()
        print(f"Error: {str(e)}\n{traceback_str}")
        return f"Error: {str(e)}", 400
    

@app.route('/cached', methods=['GET'])
def get_random_cached_graph():
    print("Accessing /cached endpoint")
    
    expired_count = clean_expired_graphs()
    if expired_count > 0:
        print(f"Removed {expired_count} expired graphs from cache")
    
    with cache_lock:
        if not graph_cache:
            print("Cache is empty, returning placeholder image")
            return send_file(create_no_cache_image(), mimetype='image/png')
        
        cached_graph = random.choice(list(graph_cache))
        print(f"Selected cached graph: {cached_graph.equation}")
        buf_copy = io.BytesIO(cached_graph.image_buffer.getvalue())
        buf_copy.seek(0)
        cached_graph.image_buffer.seek(0)

        return send_file(buf_copy, mimetype='image/png')

@app.route('/cache', methods=['POST'])
def clear_cache():
    print("Clearing cache")
    with cache_lock:
        graph_cache.clear()

    return jsonify({"status": "success", "message": "Cache cleared successfully"})

@app.route('/cache/info', methods=['GET'])
def cache_info():
    print("Accessing cache info")
    
    expired_count = clean_expired_graphs()
    if expired_count > 0:
        print(f"Removed {expired_count} expired graphs from cache")
    
    with cache_lock:
        info = {
            "cache_size": len(graph_cache),
            "max_cache_size": graph_cache.maxlen,
            "graphs": [
                {
                    "id": g.id,
                    "equation": g.equation,
                    "category": g.category,
                    "timestamp": g.timestamp,
                    "expires_at": g.expires_at,
                    "expires_in": round((g.expires_at - time.time()) / 60 / 60, 2)
                } for g in graph_cache
            ]
        }
    return jsonify(info)

@app.route('/systemhealth', methods=['GET'])
def system_health():
    print("Accessing /systemhealth endpoint")
    
    cpu_percent = psutil.cpu_percent(interval=0.5)
    
    memory = psutil.virtual_memory()
    ram_used_bytes = memory.used
    ram_total_bytes = memory.total
    ram_percent = memory.percent
    
    def bytes_to_human_readable(bytes_value):
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0 or unit == 'TB':
                return f"{bytes_value:.2f} {unit}"
            bytes_value /= 1024.0
    
    ram_used_readable = bytes_to_human_readable(ram_used_bytes)
    ram_total_readable = bytes_to_human_readable(ram_total_bytes)
    
    global last_health_check
    current_time = time.time()
    with health_check_lock:
        previous_check = last_health_check
        last_health_check = current_time
    
    health_data = {
        "cpu_usage_percent": cpu_percent,
        "ram_usage": {
            "used_bytes": ram_used_bytes,
            "total_bytes": ram_total_bytes,
            "used_readable": ram_used_readable,
            "total_readable": ram_total_readable,
            "percent": ram_percent
        },
        "current_timestamp": current_time,
        "previous_health_check_timestamp": previous_check
    }
    
    return jsonify(health_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
