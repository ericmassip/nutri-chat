# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

NutriChat is a web application that enables nutritionists to share nutritional plans with their clients through an
interactive chat interface. The application allows nutritionists to upload nutritional plans in various document
formats (PDF, DOCX, etc.), which clients can then interact with through an AI-powered conversational interface.

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

## Design guidelines

This agent is guided by the principles from John Ousterhout's "A Philosophy of Software Design," which focuses on
managing complexity to create maintainable and extensible software. All design, planning, and code changes must adhere
to these core ideas.

Software design guiding principles:

* Information Hiding: Encapsulate implementation details within modules. Only expose what is necessary through the
  module's interface.

* Readability Over Writability: Write code that is easy for others to read and understand, not just easy to write
  quickly.

* Meaningful Comments: Comments should explain the "why" and "what" that is not immediately obvious from the code
  itself.

* General-Purpose Code: Prefer creating general-purpose modules and code that can be reused in different contexts. Keep
  special-purpose code separate.

* Design It Twice: Before writing any code, draft an initial design and then consider a second, alternative design. This
  process of comparing and contrasting helps to reveal weaknesses and lead to a superior final design.

Software design red flags. The presence of these symptoms indicates a design problem. When you encounter any of these,
refactor the code to eliminate them:

* Shallow Modules: An interface for a class or method is not significantly simpler than its implementation.

* Information Leakage: A single design decision is reflected in multiple modules, creating tight coupling.

* Temporal Decomposition: The code structure is based on the order in which operations are executed, not on information
  hiding.

* Pass-Through Methods: A method that does nothing but pass arguments to another method with a similar signature. This
  indicates a poor separation of responsibilities.

* Repetition: A non-trivial piece of code is repeated. This suggests a lack of a proper abstraction.

* Special-General Mixture: General-purpose code is not cleanly separated from special-purpose code.

* Conjoined Methods: Two methods have so many dependencies that it's hard to understand the implementation of one
  without understanding the implementation of the other.

* Comment Repeats Code: All of the information in a comment is immediately obvious from the code next to the comment.

* Vague Naming: A variable or method name is so imprecise that it does not convey useful information.

* Hard to Pick a Name: If it's difficult to find a precise and intuitive name for an entity, it's a sign of a design
  flaw.

* Nonobvious Code: The behavior or meaning of a piece of code cannot be understood easily.
