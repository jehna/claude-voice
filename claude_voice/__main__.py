#!/usr/bin/env python3

"""
Claude Voice - A voice-enabled TUI wrapper for Claude CLI

This module provides a voice interface to interact with Claude CLI,
allowing users to speak commands and receive spoken responses.

Usage:
    python -m claude_voice
"""

import sys
from .main import main

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nProgram terminated by user.")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)