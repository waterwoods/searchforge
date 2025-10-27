# Code Lookup Agent

> An AI-powered agent to analyze, visualize, and explain your codebase.

## Overview

Code Lookup Agent is an intelligent code analysis tool designed for developers and architects. It helps you understand complex codebases quickly by combining AI technology with interactive visualizations. Whether you're exploring a new repository, analyzing system architecture, or onboarding to a project, this agent provides deep insights into your code structure, function relationships, and system dependencies.

### Who is it for?
- **Developers**: Quickly understand newly inherited codebases
- **Architects**: Analyze system architecture and module dependencies
- **Tech Leads**: Assess code quality and maintainability
- **New Team Members**: Get up to speed with project code structure

## Core Features

- **🔍 Interactive Code Graph Visualization**: Real-time generation of code dependency graphs, intuitively displaying connections between modules
- **🤖 AI-Powered Architectural Analysis & Explanation**: Intelligent code analysis powered by OpenAI GPT models
- **📊 Real-time "Action Log" Streaming**: Visualize the AI agent's thinking process with complete Chain-of-Thought execution traces
- **📋 Evidence-Based Analysis**: Built on Vibe Coding principles for transparent and auditable AI agents
- **⚡ Multiple Query Modes**: Support for overview, file analysis, function analysis, and more
- **🔄 Streaming Response**: Real-time analysis progress display for enhanced user experience

## Architecture Overview

Built with modern microservice architecture:

- **Backend**: FastAPI + Python 3.8+, providing RESTful API and streaming responses
- **Frontend**: React + Vite for a modern single-page application
- **AI Engine**: OpenAI GPT-4o-mini model for intelligent code analysis
- **Visualization**: Mermaid chart library for generating interactive code graphs
- **State Management**: Zustand for lightweight state management solution

The project is built on **Vibe Coding principles**, implementing transparent and auditable AI agents where every analysis step has clear evidence support.

## Getting Started

### Prerequisites

- **Python**: 3.8 or higher
- **Node.js**: 16.0 or higher
- **Package Manager**: npm, yarn, or pnpm (recommended)

### 1. Clone the Project

```bash
git clone <repository-url>
cd searchforge
```

### 2. Backend Setup

#### Install Python Dependencies

```bash
pip install -r requirements.txt
```

#### Configure Environment Variables

Copy the environment configuration file and set up your OpenAI API key:

```bash
cp agent_v3.env.example .env
```

Edit the `.env` file and add your OpenAI API key:

```bash
# OpenAI API Configuration
OPENAI_API_KEY=sk-your-api-key-here

# Optional: Specify model (default: gpt-4o-mini)
LLM_MODEL=gpt-4o-mini

# Optional: Set timeout (default: 8.0 seconds)
LLM_TIMEOUT=8.0
```

**Note**: If no API key is provided, the system will automatically fall back to rule-based code analysis mode and can still function normally.

### 3. Frontend Setup

```bash
cd code-lookup-frontend
npm install  # or use yarn/pnpm
```

### 4. Run the Application

Use the provided startup script to launch both frontend and backend services:

```bash
# Execute from project root directory
./scripts/start-agent.sh
```

The startup script will automatically:
- Start the backend service (port 8001)
- Start the frontend service (port 5173)
- Handle port conflicts
- Display service status and access URLs

### 5. Access the Application

Open your browser and navigate to: http://localhost:5173

## How to Use

### Query Syntax

The Code Lookup Agent supports multiple query modes:

#### 1. Overview Query
```bash
#overview
# Or use natural language
"show me an overview of the repository"
"what is this codebase about"
```

#### 2. File Analysis
```bash
#file src/api/routes.py
# Or use natural language
"analyze the file at services/main.py"
"examine the code at src/utils.py"
```

#### 3. Function Analysis
```bash
#func my_app.utils.clean_data
# Or use natural language
"analyze the function process_data"
"examine the method validate_input"
```

### Features

- **Intelligent Routing**: Automatically identifies query types and routes to appropriate processing modules
- **Plan Generation**: AI agent creates analysis plans to ensure completeness
- **Execution Engine**: Performs specific analysis tasks based on code graphs
- **Result Validation**: Judges module validates accuracy and completeness of analysis results
- **Explanation Generation**: Uses LLM to generate human-readable analysis explanations

### Real-time Monitoring

The application provides complete execution tracking:
- **Step Visualization**: Real-time display of AI agent execution steps
- **Cost Monitoring**: Show API call costs and token usage
- **Error Handling**: Intelligent error recovery and graceful degradation

## API Endpoints

### Main Endpoints

- `POST /v1/query`: Execute code analysis query
- `GET /v1/stream`: Stream query execution (real-time events)
- `GET /v1/supported-queries`: Get supported query types
- `GET /health`: Health check

### Example Request

```bash
curl -X POST "http://localhost:8001/v1/query" \
     -H "Content-Type: application/json" \
     -d '{"query": "#overview"}'
```

## Project Structure

```
searchforge/
├── services/fiqa_api/          # Backend API service
│   ├── agent/                 # AI agent components
│   │   ├── router.py         # Query router
│   │   ├── planner.py        # Plan generator
│   │   ├── executor.py       # Execution engine
│   │   ├── judge.py          # Result validator
│   │   └── explainer.py      # Explanation generator
│   ├── tools/                # Tool modules
│   └── main.py               # FastAPI application entry point
├── code-lookup-frontend/      # Frontend React application
│   ├── src/
│   │   ├── components/       # React components
│   │   └── App.jsx          # Main application component
│   └── package.json         # Frontend dependencies
├── scripts/
│   └── start-agent.sh       # Startup script
├── codegraph.v1.json       # Code graph data
└── requirements.txt         # Python dependencies
```

## Future Work

### Short-term Goals
- **Multi-language Support**: Extend support for TypeScript, Go, Java, and other languages
- **Performance Optimization**: Optimize analysis performance for large codebases
- **UI Enhancement**: Improve visualization interface and interaction experience

### Medium-term Goals
- **CI/CD Integration**: Integration with GitHub Actions, GitLab CI, and more
- **Team Collaboration**: Support multi-user collaboration and sharing features
- **Plugin System**: Support for custom analysis plugins

### Long-term Vision
- **Enterprise Deployment**: Support for on-premise deployment and permission management
- **Intelligent Suggestions**: Provide refactoring suggestions based on code analysis
- **Learning Mode**: Learn from user behavior to provide personalized analysis

## Contributing

Community contributions are welcome! Please check out the following resources:

- Submit Issues to report bugs or suggest features
- Fork the project and submit Pull Requests
- Follow the project's code standards and testing requirements

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

If you encounter issues during use, please:

1. Check the Getting Started section in this documentation
2. Verify that environment configuration is correct
3. Check the project's Issues page
4. Submit a new Issue describing your problem

---

**Code Lookup Agent** - Making code understanding simple and intelligent 🚀
