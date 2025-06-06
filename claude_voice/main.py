#!/usr/bin/env python3

"""
Main module for Claude Voice TUI wrapper
"""

from .terminal import Terminal
from .listener import AudioListener
import time

def main():
    print("Hello from Claude Voice!")

    audio_listener = AudioListener()
    audio_listener.start()

    time.sleep(3)
    terminal = Terminal("/bin/bash", ["/bin/bash", "-c", "claude"])

    def on_transcription(text):
        terminal.send_input(text)
        terminal.send_key("enter")

    audio_listener.add_transcription_callback(on_transcription)

    try:
        terminal.start()
        terminal.wait()
    except KeyboardInterrupt:
        print("\nTerminal interrupted.")
    finally:
        audio_listener.stop()
        terminal.stop()

if __name__ == "__main__":
    main()