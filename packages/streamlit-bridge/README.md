# TerraFusion Bridge Package

This package provides Python connectivity to the TerraFusion API server, enabling seamless integration between Python applications (like Streamlit) and the Node.js backend.

## Installation

```bash
pip install -e .
```

## Usage

```python
from tf_bridge import get_bridge

# Get a bridge instance with the default API URL
bridge = get_bridge()

# Or specify a custom API URL
bridge = get_bridge("http://localhost:4000")

# Check API status
status = bridge.get_api_status()
print(status)

# Calculate property levy
result = bridge.calculate_property_levy("123")
print(result)
```

## Features

- Seamless Python-to-Node connectivity
- Easy API access from Python applications
- Error handling and response formatting
- Configurable API URL

## Levy Calculator POC

This package includes a Proof of Concept (POC) Streamlit application that demonstrates the Python-to-Node connectivity by calculating property taxes. To run it:

```bash
streamlit run src/levy_app.py
```