# TerraFusion AI Platform

An advanced AI-powered code analysis and optimization platform that provides intelligent workflow management through multi-agent AI orchestration and interactive development insights.

![TerraFusion AI Platform](generated-icon.png)

## Overview

TerraFusion AI Platform integrates advanced AI capabilities from OpenAI and Anthropic to provide comprehensive code analysis, workflow optimization, and development insights. The platform uses a multi-agent architecture where specialized AI agents focus on different aspects of software analysis and optimization.

## Core Features

- **Sync Service Dashboard**: Monitor and manage synchronization operations with real-time metrics and dynamic batch sizing
- **Code Analysis Dashboard**: AI-powered analysis of code quality, architecture, performance, and security
- **Agent Orchestration**: Management interface for specialized AI agents with different capabilities
- **Workflow Visualization**: Analysis and optimization of code workflows with bottleneck identification
- **Repository Analysis**: In-depth analysis of entire code repositories to evaluate structure and quality
- **AI Chat Interface**: Interactive communication with specialized AI agents for development assistance

## Technologies

- **Python & Streamlit**: Interactive web application framework
- **OpenAI API**: GPT-4o integration for advanced code analysis
- **Anthropic API**: Claude integration for alternative model capabilities
- **NetworkX & Plotly**: Graph visualization for code and workflow analysis
- **Pandas & NumPy**: Data processing and analysis

## Installation & Setup

### Prerequisites

- Python 3.10+
- Streamlit
- OpenAI API key (optional but recommended)
- Anthropic API key (optional but recommended)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/username/terrafusion-ai-platform.git
   cd terrafusion-ai-platform
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   ```bash
   export OPENAI_API_KEY="your_openai_api_key"
   export ANTHROPIC_API_KEY="your_anthropic_api_key"
   ```

### Running the Application

Start the Streamlit server:

```bash
streamlit run app.py
```

The application will be available at http://localhost:5000

## Module Structure

- **app.py**: Main application entry point and dashboard
- **model_interface.py**: Unified interface for AI model interactions
- **pages/**: Directory containing all specialized dashboard pages
  - **1_Sync_Service_Dashboard.py**: Sync service monitoring and management
  - **2_Code_Analysis_Dashboard.py**: Code quality analysis interface
  - **3_Agent_Orchestration.py**: AI agent management dashboard 
  - **4_Workflow_Visualization.py**: Workflow analysis and optimization
  - **5_Repository_Analysis.py**: Code repository analysis
  - **6_AI_Chat_Interface.py**: Interactive AI chat interface

## AI Service Integration

The platform integrates both OpenAI and Anthropic APIs for AI capabilities, with automatic fallback between services if one is unavailable. The `ModelInterface` class provides a unified interface for:

- Text generation
- Embeddings creation
- Image analysis

## Multi-Agent System

The platform uses a multi-agent architecture where specialized AI agents focus on different aspects:

- **CodeQualityAgent**: Code quality, style, and readability
- **ArchitectureAgent**: Software architecture and design patterns
- **DatabaseAgent**: Database schema and query optimization
- **DocumentationAgent**: Documentation completeness and quality
- **SecurityAgent**: Security vulnerability identification
- **PerformanceAgent**: Performance analysis and optimization

## Deployment

The application is configured for deployment on Replit with proper port binding to 0.0.0.0:5000 and headless mode enabled.

## License

This project is released under the MIT License. See the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For support, please open an issue in the GitHub repository or contact the development team.