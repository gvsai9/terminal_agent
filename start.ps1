$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "========================================"
Write-Host "       MCP FILESYSTEM AGENT"
Write-Host "========================================"
Write-Host ""

# -----------------------------------------
# Move to project directory
# -----------------------------------------

Set-Location $PSScriptRoot

# -----------------------------------------
# Check Python
# -----------------------------------------

Write-Host "[1/4] Checking Python..."

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host ""
    Write-Host "Python is not installed."
    Write-Host "Please install Python 3.11+ and run this again."
    exit 1
}

python --version

# -----------------------------------------
# Check Node / npm / npx
# -----------------------------------------

Write-Host ""
Write-Host "[2/4] Checking Node.js / npm / npx..."

if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Host ""
    Write-Host "Node.js is not installed."
    Write-Host "Please install Node.js LTS and run this again."
    exit 1
}

node --version
npm --version
npx --version

# -----------------------------------------
# Create virtual environment
# -----------------------------------------

Write-Host ""
Write-Host "[3/4] Preparing Python environment..."

if (-not (Test-Path ".venv")) {

    Write-Host "Creating virtual environment..."

    python -m venv .venv
}

# -----------------------------------------
# Activate environment
# -----------------------------------------

& ".\.venv\Scripts\Activate.ps1"

# -----------------------------------------
# Install dependencies
# -----------------------------------------

Write-Host ""
Write-Host "Installing Python dependencies..."

python -m pip install --upgrade pip

pip install -r requirements.txt

# -----------------------------------------
# NVIDIA API KEY
# -----------------------------------------

Write-Host ""
Write-Host "[4/4] Checking NVIDIA API configuration..."
# -----------------------------------------
# NVIDIA API KEY
# -----------------------------------------

$env:NVIDIA_API_KEY = "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"

Write-Host "NVIDIA API configured."

if (-not $env:NVIDIA_API_KEY) {

    Write-Host ""
    Write-Host "NVIDIA_API_KEY is not configured."
    Write-Host ""
    Write-Host "For now, configure it in this terminal:"
    Write-Host ""
    Write-Host '$env:NVIDIA_API_KEY="YOUR_KEY"'
    Write-Host ""
    Write-Host "Then run .\start.ps1 again."

    exit 1
}

Write-Host "NVIDIA API key detected."

# -----------------------------------------
# Start agent
# -----------------------------------------

Write-Host ""
Write-Host "========================================"
Write-Host "Starting MCP Agent..."
Write-Host "Filesystem root:"
Write-Host (Get-Location)
Write-Host "========================================"
Write-Host ""

python agent.py -pwd