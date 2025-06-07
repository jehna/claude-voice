#!/usr/bin/env python3

"""
Main module for Claude Voice TUI wrapper
"""

from .listener import AudioListener, Model
from .claude import Claude
from .pushtotalk import PushToTalk
from pynput import keyboard

def main():
    print("Starting up...")
    audio_listener = AudioListener(model=Model.LARGE)
    audio_listener.start()

    ptt = PushToTalk(audio_listener, hotkey=keyboard.Key.ctrl_l)
    print("Hello from Claude Voice!")

    claude = Claude()

    audio_listener.add_transcription_callback(claude.process_instruction)

    try:
        ptt.start()
        claude.start()
    except KeyboardInterrupt:
        print("\nTerminal interrupted.")
    finally:
        audio_listener.stop()
        claude.stop()

if __name__ == "__main__":
    main()