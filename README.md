# PCARA - Polyglot Codebase Analyzer & Refactor Assistant

A comprehensive platform for analyzing and understanding complex, multi-language codebases with AI-powered insights and refactoring guidance.

## Features

### Core Analysis Capabilities
- **Multi-language Code Analysis**: Support for Python, JavaScript/TypeScript, C#, Java, Go, and more
- **Polyglot Cross-Language Dependencies**: Unique analysis of dependencies and communication patterns across different programming languages
- **Architectural Analysis**: Identify architectural debt, patterns, and hotspots
- **Complexity Analysis**: Identify high-complexity functions and areas for improvement
- **Security Analysis**: Basic security vulnerability detection
- **Syntax Analysis**: Comprehensive syntax validation and statistics

### Polyglot Intelligence (PCARA's Unique Value)
- **Cross-Language API Detection**: Identify HTTP APIs, message queues, and communication patterns between language components
- **Shared Resource Analysis**: Find configuration files, databases, and resources used across multiple languages
- **Architectural Insight Generation**: Assess coupling levels, communication complexity, and maintainability scores
- **Hotspot Identification**: Detect architectural bottlenecks and highly connected components
- **Migration Recommendations**: Get actionable advice for improving polyglot architecture

### AI-Powered Features
- **RAG System**: Get intelligent answers about your codebase using natural language
- **Code Interpreter**: Premium feature for deep codebase understanding
- **Automated Recommendations**: AI-generated suggestions for refactoring and improvements

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Git

### Development Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd pcara
```

2. Copy environment variables:
```bash
cp .env.example .env
```

3. Edit `.env` file and add your Google Gemini API key:
```bash
GEMINI_API_KEY=your_api_key_here
```

4. Start the development environment:
```bash
docker-compose -f docker-compose.dev.yml up --build
```

5. Access the application:
- Frontend: http://localhost:3001
- API Gateway: http://localhost:8081
- ChromaDB: http://localhost:8001

### Services

The application consists of several containerized services:

- **Frontend**: React.js application with Material-UI for user interface
- **API Gateway**: FastAPI backend handling authentication and orchestration
- **Language Analyzers**: 
  - Python Analyzer: Advanced Python code analysis
  - C# Analyzer: .NET and C# codebase analysis  
  - JavaScript Analyzer: JavaScript/TypeScript analysis with framework detection
- **Polyglot Analyzer**: Cross-language dependency and architectural analysis (PCARA's unique feature)
- **PostgreSQL**: Primary database for application data
- **Redis**: Job queue and caching for distributed analysis
- **ChromaDB**: Vector database for RAG and semantic search functionality

## Architecture

PCARA follows a microservices architecture with:
- Docker containerization for all services
- Redis-based job queue for asynchronous processing
- PostgreSQL for structured data storage
- ChromaDB for vector embeddings and semantic search
- Google Gemini API for AI-powered responses

## Development Workflow

1. **Add Repository**: Register a Git repository for analysis
2. **Start Analysis**: Choose languages and analysis types
3. **Monitor Progress**: Track analysis progress in real-time
4. **View Results**: Explore detailed analysis results and visualizations
5. **RAG Queries**: Ask questions about your codebase using natural language

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.