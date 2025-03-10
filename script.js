document.addEventListener('DOMContentLoaded', function() {
    const customEquationInput = document.getElementById('custom-equation');
    const xScaleInput = document.getElementById('x-scale');
    const yScaleInput = document.getElementById('y-scale');
    const dataPointsInput = document.getElementById('data-points');
    const plotButton = document.getElementById('plot-button');
    const plotCode = document.getElementById('plot-code');
    const plotResult = document.getElementById('plot-result');

    const randomCategorySelect = document.getElementById('random-category');
    const randomXScaleInput = document.getElementById('random-x-scale');
    const randomYScaleInput = document.getElementById('random-y-scale');
    const randomDataPointsInput = document.getElementById('random-data-points');
    const randomButton = document.getElementById('random-button');
    const randomCode = document.getElementById('random-code');
    const randomResult = document.getElementById('random-result');

    const viewCachedButton = document.getElementById('view-cached-button');
    const cacheInfoButton = document.getElementById('cache-info-button');
    const clearCacheButton = document.getElementById('clear-cache-button');
    const cacheCode = document.getElementById('cache-code');
    const cacheResult = document.getElementById('cache-result');

    const systemHealthButton = document.getElementById('system-health-button');
    const healthCode = document.getElementById('health-code');
    const healthResult = document.getElementById('health-result');

    const baseUrl = 'https://api.ansonlai.website';

    function encodeLatex(latex){
        return encodeURIComponent(latex);
    }

    function updateCopyButtons() {
        document.querySelectorAll('.copy-btn').forEach(button => {
            button.addEventListener('click', function() {
                const text = this.getAttribute('data-text');
                navigator.clipboard.writeText(text).then(() => {
                    const originalHTML = this.innerHTML;
                    this.innerHTML = '<i class="fas fa-check"></i>';
                    setTimeout(() => {
                        this.innerHTML = originalHTML;
                    }, 1500);
                });
            });
        });
    }

    updateCopyButtons();

    plotButton.addEventListener('click', function() {
        const equation = customEquationInput.value;
        const xScale = xScaleInput.value;
        const yScale = yScaleInput.value;
        const dataPoints = dataPointsInput.value;

        const apiUrl = `${baseUrl}/plot?equation=${encodeLatex(equation)}&x_scale=${xScale}&y_scale=${yScale}&data_points=${dataPoints}`;

        plotCode.querySelector('code').textContent = apiUrl;
        plotCode.querySelector('.copy-btn').setAttribute('data-text', apiUrl);

        plotResult.innerHTML = '<div class="placeholder">Loading...</div>';

        fetch(apiUrl)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
            return response.blob();
            })
            .then(blob => {
                const imageUrl = URL.createObjectURL(blob);
                plotResult.innerHTML = `<img src="${imageUrl}" alt="Plot of ${equation}">`;
            })
            .catch(error => {
                plotResult.innerHTML = `<div class="placeholder">Error: ${error.message}</div>`;
            });
    });

    randomButton.addEventListener('click', function() {
        const category = randomCategorySelect.value;
        const xScale = randomXScaleInput.value;
        const yScale = randomYScaleInput.value;
        const dataPoints = randomDataPointsInput.value;

        const apiUrl = `${baseUrl}/random?category=${category}&x_scale=${xScale}&y_scale=${yScale}&data_points=${dataPoints}`;

        randomCode.querySelector('code').textContent = apiUrl;
        randomCode.querySelector('.copy-btn').setAttribute('data-text', apiUrl);

        randomResult.innerHTML = '<div class="placeholder">Loading...</div>';

        fetch(apiUrl)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.blob();
            })
            .then(blob => {
                const imageUrl = URL.createObjectURL(blob);
                randomResult.innerHTML = `<img src="${imageUrl}" alt="Random ${category} equation plot">`;
            })
            .catch(error => {
                randomResult.innerHTML = `<div class="placeholder">Error: ${error.message}</div>`;
            });
    });

    viewCachedButton.addEventListener('click', function() {
        const apiUrl = `${baseUrl}/cached`;

        cacheCode.querySelector('code').textContent = apiUrl;
        cacheCode.querySelector('.copy-btn').setAttribute('data-text', apiUrl);

        cacheResult.innerHTML = '<div class="placeholder">Loading...</div>';

        fetch(apiUrl)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.blob();
            })
            .then(blob => {
                const imageUrl = URL.createObjectURL(blob);
                cacheResult.innerHTML = `<img src="${imageUrl}" alt="Random cached equation plot">`;
            })
            .catch(error => {
                cacheResult.innerHTML = `<div class="placeholder">Error: ${error.message}</div>`;
            });

    });

    cacheInfoButton.addEventListener('click', function() {
        const apiUrl = `${baseUrl}/cache/info`;

        cacheCode.querySelector('code').textContent = apiUrl;
        cacheCode.querySelector('.copy-btn').setAttribute('data-text', apiUrl);

        cacheResult.innerHTML = '<div class="placeholder">Loading...</div>';

        fetch(apiUrl)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                const jsonString = JSON.stringify(data, null, 2);
                cacheResult.innerHTML = `<pre class="json">${jsonString}</pre>`;
            })
            .catch(error => {
                cacheResult.innerHTML = `<div class="placeholder">Error: ${error.message}</div>`;
            });
    });

    clearCacheButton.addEventListener('click', function() {
        const apiUrl = `${baseUrl}/cache`;

        cacheCode.querySelector('code').textContent = apiUrl;
        cacheCode.querySelector('.copy-btn').setAttribute('data-text', apiUrl);

        cacheResult.innerHTML = '<div class="placeholder">Loading...</div>';

        fetch(apiUrl, {
            method: 'POST'
        })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                cacheResult.innerHTML = `<div class="placeholder success">
                    <i class="fas fa-check-circle"></i>
                    <p>${data.message || 'Cache cleared successfully'}</p>
                </div>`;
            })
            .catch(error => {
                cacheResult.innerHTML = `<div class="placeholder">Error: ${error.message}</div>`;
            });
    });

    systemHealthButton.addEventListener('click', function() {
        const apiUrl = `${baseUrl}/systemhealth`;

        healthCode.querySelector('code').textContent = apiUrl;
        healthCode.querySelector('.copy-btn').setAttribute('data-text', apiUrl);

        healthResult.innerHTML = '<div class="placeholder">Loading...</div>';

        fetch(apiUrl)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                const jsonString = JSON.stringify(data, null, 2);
                healthResult.innerHTML = `<pre class="json">${jsonString}</pre>`;
            })
            .catch(error => {
                healthResult.innerHTML = `<div class="placeholder">Error: ${error.message}</div>`;
            });
    });

    function updateCustomEquationCode() {
        const equation = customEquationInput.value;
        const xScale = xScaleInput.value;
        const yScale = yScaleInput.value;
        const dataPoints = dataPointsInput.value;
        const apiUrl = `${baseUrl}/plot?equation=${encodeLatex(equation)}&x_scale=${xScale}&y_scale=${yScale}&data_points=${dataPoints}`;
        plotCode.querySelector('code').textContent = apiUrl;
        plotCode.querySelector('.copy-btn').setAttribute('data-text', apiUrl);
    }

    function updateRandomCode() {
        const category = randomCategorySelect.value;
        const xScale = randomXScaleInput.value;
        const yScale = randomYScaleInput.value;
        const dataPoints = randomDataPointsInput.value;
        
        const apiUrl = `${baseUrl}/random?category=${category}&x_scale=${xScale}&y_scale=${yScale}&data_points=${dataPoints}`;
        randomCode.querySelector('code').textContent = apiUrl;
        randomCode.querySelector('.copy-btn').setAttribute('data-text', apiUrl);
    }

    customEquationInput.addEventListener('input', updateCustomEquationCode);
    xScaleInput.addEventListener('input', updateCustomEquationCode);
    yScaleInput.addEventListener('input', updateCustomEquationCode);
    dataPointsInput.addEventListener('input', updateCustomEquationCode);

    randomCategorySelect.addEventListener('change', updateRandomCode);
    randomXScaleInput.addEventListener('input', updateRandomCode);
    randomYScaleInput.addEventListener('input', updateRandomCode);
    randomDataPointsInput.addEventListener('input', updateRandomCode);

    updateCustomEquationCode();
    updateRandomCode();

    document.querySelectorAll('nav a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();

            const targetId = this.getAttribute('href');
            const targetElement = document.querySelector(targetId);

            if (targetElement) {
                window.scrollTo({
                    top: targetElement.offsetTop - 80,
                    behavior: 'smooth'
                });
            }
        });
    });

    const style = document.createElement('style');
    style.textContent = `
        .placeholder.success {
            color: var(--secondary-color);
            text-align: center;
            font-weight: bold;
        }
        .placeholder.success i {
            font-size: 2rem;
            margin-bottom: 1rem;
        }
        .json {
            white-space: pre-wrap;
            word-break: break-word;
            font-family: 'Consolas', 'Monaco', monospace;
            max-height: 300px;
            overflow-y: auto;
        }
    `;
    document.head.appendChild(style);
});

document.addEventListener('DOMContentLoaded', function() {
    const currentTheme = localStorage.getItem('theme') || 'light';

    if (currentTheme === 'dark') {
        document.body.classList.add('dark-mode');
        document.getElementById('theme-switch').checked = true;
    }

    const themeSwitch = document.getElementById('theme-switch');

    themeSwitch.addEventListener('change', function(e) {
        if (e.target.checked) {
            document.body.classList.add('dark-mode');
            localStorage.setItem('theme', 'dark');
        } else {
            document.body.classList.remove('dark-mode');
            localStorage.setItem('theme', 'light');
        }
    });

    if (!localStorage.getItem('theme')) {
        const prefersDarkMode = window.matchMedia('(prefers-color-scheme: dark)').matches;

        if (prefersDarkMode) {

            document.body.classList.add('dark-mode');
            document.getElementById('theme-switch').checked = true;
            localStorage.setItem('theme', 'dark');

        }
    }

    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
        if (!localStorage.getItem('theme')) {
            if (e.matches) {
                document.body.classList.add('dark-mode');
                document.getElementById('theme-switch').checked = true;
            } else {
                document.body.classList.remove('dark-mode');
                document.getElementById('theme-switch').checked = false;
            }
        }
    });
});
