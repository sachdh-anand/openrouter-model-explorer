#!/usr/bin/env pwsh
# Script to run the OpenRouter Model Explorer using uv
$ErrorActionPreference = 'Stop'

# Change to script directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Push-Location $scriptDir

# Ensure uv is installed
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Error "uv is not installed. Install it via 'pip install uv'"
    exit 1
}

# Create virtual environment if missing
if (-not (Test-Path '.venv')) {
    Write-Host "Creating virtual environment with uv..."
    uv venv .venv --seed
}

# Install dependencies
Write-Host "Installing dependencies..."
uv pip install -e .

# Launch the Streamlit application
Write-Host "Starting OpenRouter Model Explorer..."
uv run --project . --module streamlit run app.py

# Return to original directory
Pop-Location