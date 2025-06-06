#!/usr/bin/env bash

# Activate your Python virtual environment
VENV_PATH="./env"

if [ -d "$VENV_PATH" ]; then
    source "$VENV_PATH/bin/activate"
    echo "✅ Activated virtual environment at $VENV_PATH"
else
    echo "❌ Virtual environment not found at $VENV_PATH"
    exit 1
fi

# Set environment variables
export PYTHON_ENV="development"
export LOG_LEVEL="DEBUG"
export PNM_CONFIG_PATH="${PWD}/config/pnm_config.json"
export PYTHONPATH="${PWD}/src"

echo "✅ Environment variables set:"
echo "   PYTHON_ENV=$PYTHON_ENV"
echo "   LOG_LEVEL=$LOG_LEVEL"
echo "   PNM_CONFIG_PATH=$PNM_CONFIG_PATH"
echo "   PYTHONPATH=$PYTHONPATH"
