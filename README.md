# GraphAPI Documentation
## Overview
This API allows user to plot math equations encoded with LaTex. It can generate plots from custom LaTeX equations, create random equations for different categories/types of mathematical functions and manage cache of previously generated graphs.

## Base URL
```
https://api.ansonlai.website
```

## Endpoints

### 1. Plot Custom Equation
Generate a plot from a user provided LaTeX equation.

**Endpoint:** `/plot`
**Method:** `GET`

**Parameters:**
| **Parameter** | **Type** | **Required** | **Default** | **Description**|
| ---------     |  -----   |    -----     |    -----    |     -----      |
| equation | string | Yes | - | LaTeX formatted mathematical equation |
| x_scale | int | No | 20 | Width of the x-axis range (-{x_scale}/2 to {x_scale}/2) |
| y_scale | int | No | 20 | Height of the y-axis range (-{y_scale}/2 to {y_scale}/2) |
| data_points | int | No | 1000 | Number of data points for plotting |

**Example Request:**
```
GET https://api.ansonlai.website/plot?equation=x%5E2%2B5&x_scale=10&y_scale=50
```
> [!IMPORTANT]  
> The equation must be URL-encoded. The above example plots `x^2 + 5`.

**Success Response:**
- Content-Type: `image/png`
- Body: PNG image of the plotted equation

**Error Response:**
- Status Code: `400`
- Body: Error message describing what went wrong during plotting

### 2. Generate Random Equation
Generate and plot a random equation from a specified category.

**Endpoint:** `/random`
**Method:** `GET`

**Parameters:**
| **Parameter** | **Type** | **Required** | **Default** | **Description**|
| ---------     |  -----   |    -----     |    -----    |     -----      |
| equation | string | Yes | - | LaTeX formatted mathematical equation |
| x_scale | int | No | 20 | Width of the x-axis range (-{x_scale}/2 to {x_scale}/2) |
| y_scale | int | No | 20 | Height of the y-axis range (-{y_scale}/2 to {y_scale}/2) |
| data_points | int | No | 1000 | Number of data points for plotting | 

**Valid Categories:**
- `sqrt` Square root function
- `polynomial` Polynomial function (Up to 6 degrees)
- `linear` Linear function
- `trigonometry` Trogonometric function
- `exponential` Exponential function
- `logarithm` Logarithmic function
- `reciprocal` Reciprocal function

**Example Request:**
```
GET https://api.ansonlai.website/random?category=trigonometry&x_scale=30&y_scale=10
```

**Success Response:**
- Content-Type: `image/png`
- Body: PNG image of the plotted equation

**Error Response:**
- Status Code: `400`
- Body: Error message describing what went wrong during parsing

### 3. Generate Random Equation
Retrieve a random graph from the cache of previously generated plots (of all users).

**Endpoint:** `/cached`
**Method:** `GET`

**Parameters:**
`None`

**Example Request:**
```
GET https://api.ansonlai.website/cached
```

**Success Response:**
- Content-Type: `image/png`
- Body: PNG image of the plotted equation

**Error Response:**
- Status Code: `400`
- Body: Error message describing what went wrong during parsing

> [!NOTE]  
> If the cache is empty, a placeholder image will show 'No cached graphs available'

### 4. Clear Cache
Clear all cached graphs (includes all users).


**Endpoint:** `/cache`
**Method:** `POST`

**Parameters:**
`None`

**Example Request:**
```
POST https://api.ansonlai.website/cache
```

**Success Response:**
- Content-Type: `application/json`
- Status Code : `200`
- Body: 
```
{
  "status": "success",
  "message": "Cache cleared successfully"
}
```

### 5. Get Cache Information
Retrieve information about the current cache state.

**Endpoint:** `/cache/info`
**Method:** `GET`

**Parameters:**
`None`

**Example Request:**
```
GET https://api.ansonlai.website/cache/info
```

**Success Response:**
- Content-Type: `application/json`
- Status Code : `200`
- Body: 
```
{
  "cache_size": 3,
  "max_cache_size": 50,
  "graphs": [
    {
      "id": "12345678",
      "equation": "x^2+5",
      "category": "polynomial",
      "timestamp": 1677891234.567
    },
    {
      "id": "87654321",
      "equation": "\\sin(x)",
      "category": "trigonometry",
      "timestamp": 1677891234.000
    },
    {
      "id": "23456789",
      "equation": "\\frac{1}{x}",
      "category": "reciprocal",
      "timestamp": 1677891230.000
    }
  ]
}
```

## Error Codes
GraphAPI uses standard HTTP status codes:
- `200 OK` Request successful
- `400 Bad Request` Invalid input or processing error   
    - Invalid equation syntax
    - Invalid category for random equation
    - Missing required parameters
- `500 Internal Server Error` Server side issues

## LaTeX Equation Support
The API supports various LaTex mathematical notations:
- Basic operations: `+`, `-`, `\cdot`, `/`, `^{}`
- Fractions: `\frac{numerator}{denominator}`
- Square roots: `\sqrt{function}`
- Trigonometric functions: `\sin`, `\cos`, `\tan`, `\arcsin`, `\arccos`, `\arctan`
- Hyperbolic functions: `\sinh`, `\cosh`, `\tanh`
- Logarithmic and exponential: `\exp`, `\log`, `\ln`
- Constants: `\pi`

## Implementation notes
- Equations are rendered as PNG images with a resolution of 100 DPI
- The plotting engine uses Matplotlib with a white background
- The cache has a maximum capacity of 50 plots
- Plots do not have automatic axis scaling and grid lines
- Lines may break apart if insufficient data points are used


