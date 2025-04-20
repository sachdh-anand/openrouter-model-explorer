#!/usr/bin/env bash
# Script to run the OpenRouter Model Explorer using uv
set -e
# Ensure uv is installed
if ! command -v uv &> /dev/null; then
    echo "Error: uv is not installed. Install it via 'pip install uv'"
    exit 1
fi

# Create virtual environment if missing
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment with uv..."
    uv venv .venv --seed
fi


# (pip is seeded by uv venv)

# Install dependencies
echo "Installing dependencies..."
uv pip install -e .

# Launch the application
echo "Starting OpenRouter Model Explorer..."

uv run --project . --module streamlit run app.py