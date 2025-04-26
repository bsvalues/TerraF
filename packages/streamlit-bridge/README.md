# TerraFusion Bridge Package

This package provides connectivity between Streamlit applications and the TerraFusion Node.js backend.

## Installation

```bash
pip install -e packages/streamlit-bridge
```

## Usage

```python
from tf_bridge import call_api
import streamlit as st

# Make an API call to the TerraFusion backend
data = call_api("/api/v1/levy?propertyId=123")
st.json(data)
```

## Development

This package is part of the TerraFusion monorepo. It enables the migration from the pure Streamlit application to the new TypeScript-based microservices architecture while maintaining compatibility.