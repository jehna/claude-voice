#!/usr/bin/env python3

"""
Main module for Claude Voice TUI wrapper
"""

from .listener import AudioListener
from .claude import Claude
import time

def main():
    print("Hello from Claude Voice!")

    audio_listener = AudioListener()
    audio_listener.start()

    time.sleep(3)
    claude = Claude()

    audio_listener.add_transcription_callback(claude.process_instruction)

    try:
        claude.start()
    except KeyboardInterrupt:
        print("\nTerminal interrupted.")
    finally:
        audio_listener.stop()
        claude.stop()

if __name__ == "__main__":
    main()