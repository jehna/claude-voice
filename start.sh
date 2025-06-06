#!/bin/bash

# Start script for Claude Voice module
# Runs the claude_voice module using uv

echo "Starting Claude Voice..."
uv run python -m claude_voice "$@"