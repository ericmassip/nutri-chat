# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

NutriChat is a web application that enables nutritionists to share nutritional plans with their clients through an interactive chat interface. The application allows nutritionists to upload nutritional plans in various document formats (PDF, DOCX, etc.), which clients can then interact with through an AI-powered conversational interface.

**Current Status:** Planning phase - architecture and features are still being defined.

## Tech Stack

- **Backend:** Django
- **Frontend:** HTMX
- **AI/Chat:** LangGraph
- **Python Version:** 3.13+

## Project Structure

The repository is in early stages with:
- `experimentation/` - Contains sample nutritional plan documents and experimental code for testing concepts
- `main.py` - Placeholder sample file (PyCharm template)
- Sample nutritional plans in `experimentation/data/` in both PDF and DOCX formats

## Development Commands

This project uses `uv` for dependency management (indicated by pyproject.toml).

### Environment Setup
```bash
# Activate virtual environment
source .venv/bin/activate
```

### Dependency Management
```bash
# Install dependencies
uv sync

# Add a new dependency
uv add <package-name>
```

## Architecture Notes

The application follows a multi-tenant model where:
- Nutritionists upload client-specific nutritional plans
- Each client has secure, isolated access to their own plans
- LangGraph handles the conversational AI layer for interactive queries about nutritional plans
- HTMX provides dynamic frontend interactions without heavy JavaScript frameworks

The document processing pipeline will need to:
1. Accept multiple document formats (PDF, DOCX)
2. Extract and structure nutritional information
3. Make the data queryable through the LangGraph AI interface
4. Maintain client-nutritionist relationships and access control
