#!/usr/bin/env python3

"""
Terminal API module for running programs with PTY and capturing output
"""

import pty
import os
import sys
import threading
import select
import tty
import termios
from typing import List, Callable, Optional
from concurrent.futures import ThreadPoolExecutor


KEY_MAPPINGS = {
    'enter': '\r',
    'newline': '\n',
    'tab': '\t',
    'esc': '\x1b',
    # Arrow keys (VT100 codes)
    'up': '\x1b[A',
    'down': '\x1b[B',
    'right': '\x1b[C',
    'left': '\x1b[D',
    # Home/End
    'home': '\x1b[H',
    'end': '\x1b[F',
    # Page up/down
    'pageup': '\x1b[5~',
    'pagedown': '\x1b[6~',
    # Insert/Delete
    'insert': '\x1b[2~',
    'delete': '\x1b[3~',
    # Function keys
    'f1': '\x1bOP',
    'f2': '\x1bOQ',
    'f3': '\x1bOR',
    'f4': '\x1bOS',
    'f5': '\x1b[15~',
    'f6': '\x1b[17~',
    'f7': '\x1b[18~',
    'f8': '\x1b[19~',
    'f9': '\x1b[20~',
    'f10': '\x1b[21~',
    'f11': '\x1b[23~',
    'f12': '\x1b[24~',
    # Control characters
    'ctrl-c': '\x03',
    'ctrl-d': '\x04',
    'ctrl-z': '\x1a',
    # Shift combinations (may not be widely supported)
    'shift-tab': '\x1b[Z',
    'shift-enter': '\x1b[13;2u', # xterm modifyOtherKeys
}


class Terminal:
    """Terminal wrapper that provides API for running programs and monitoring output"""

    def __init__(self, program: str = "/bin/bash", args: Optional[List[str]] = None, enable_keyboard: bool = True):
        """
        Initialize Terminal with configurable program

        Args:
            program: Path to the program to run (default: /bin/bash)
            args: Arguments to pass to the program (default: [program])
        """
        self.program = program
        self.args = args or [program]
        self.output_buffer = []
        self.buffer_lock = threading.Lock()
        self.change_callbacks = []
        self.master_fd = None
        self.pid = None
        self.running = False
        self.output_thread = None
        self.input_thread = None
        self.enable_keyboard = enable_keyboard

    def add_change_callback(self, callback: Callable[[str], None]):
        """
        Add a callback function that gets called when output_buffer changes

        Args:
            callback: Function that takes the new output string as parameter
        """
        self.change_callbacks.append(callback)

    def remove_change_callback(self, callback: Callable[[str], None]):
        """Remove a previously added callback"""
        if callback in self.change_callbacks:
            self.change_callbacks.remove(callback)

    def get_output_buffer(self) -> List[str]:
        """
        Get a copy of the current output buffer

        Returns:
            List of output strings
        """
        with self.buffer_lock:
            return self.output_buffer.copy()

    def get_output_buffer_text(self) -> str:
        """
        Get the output buffer as a single string

        Returns:
            Concatenated output buffer content
        """
        with self.buffer_lock:
            return ''.join(self.output_buffer)

    def clear_output_buffer(self):
        """Clear the output buffer"""
        with self.buffer_lock:
            self.output_buffer.clear()

    def _notify_change(self, new_output: str):
        """Notify all registered callbacks about buffer changes"""
        for callback in self.change_callbacks:
            try:
                callback(new_output)
            except Exception as e:
                print(f"Error in change callback: {e}", file=sys.stderr)

    def _handle_output(self):
        """Handle output from the program process"""
        while self.running:
            try:
                ready, _, _ = select.select([self.master_fd], [], [], 0.1)

                if self.master_fd in ready:
                    data = os.read(self.master_fd, 1024)
                    if data:
                        decoded_data = data.decode('utf-8', errors='ignore')

                        # Check for clear screen sequence (ESC[2J or ESC[H)
                        if '\x1b[2J' in decoded_data or '\x1b[H' in decoded_data or '\x1bc' in decoded_data:
                            with self.buffer_lock:
                                self.output_buffer.clear()

                        with self.buffer_lock:
                            self.output_buffer.append(decoded_data)

                        # Notify callbacks about the change
                        self._notify_change(decoded_data)

                        # Also write to stdout immediately
                        sys.stdout.write(decoded_data)
                        sys.stdout.flush()
            except OSError:
                break

    def _handle_input(self):
        """Handle input to the program process"""
        old_settings = termios.tcgetattr(sys.stdin)
        try:
            tty.setraw(sys.stdin.fileno())

            while self.running:
                try:
                    ready, _, _ = select.select([sys.stdin], [], [], 0.1)

                    if sys.stdin in ready:
                        data = os.read(sys.stdin.fileno(), 1)
                        if data:
                            os.write(self.master_fd, data)
                except OSError:
                    break
        finally:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)

    def start(self):
        """Start the terminal process"""
        if self.running:
            raise RuntimeError("Terminal is already running")

        try:
            # Create a pty
            self.master_fd, slave_fd = pty.openpty()

            # Fork the process
            self.pid = os.fork()

            if self.pid == 0:
                # Child process - set up proper TTY session
                os.close(self.master_fd)

                # Create a new session and make this the controlling terminal
                os.setsid()

                # Set up file descriptors
                os.dup2(slave_fd, 0)  # stdin
                os.dup2(slave_fd, 1)  # stdout
                os.dup2(slave_fd, 2)  # stderr
                os.close(slave_fd)

                # Set environment variables for proper TTY behavior
                os.environ['TERM'] = 'xterm-256color'

                os.execv(self.program, self.args)
            else:
                # Parent process
                os.close(slave_fd)
                self.running = True

                # Start threads for handling I/O
                self.output_thread = threading.Thread(target=self._handle_output, daemon=True)
                if self.enable_keyboard:
                    self.input_thread = threading.Thread(target=self._handle_input, daemon=True)
                    self.input_thread.start()

                self.output_thread.start()

        except Exception as e:
            self.running = False
            if self.master_fd:
                os.close(self.master_fd)
            raise RuntimeError(f"Error starting terminal: {e}")

    def wait(self):
        """Wait for the terminal process to finish"""
        if not self.running:
            return

        try:
            os.waitpid(self.pid, 0)
        except KeyboardInterrupt:
            print("\nTerminal process interrupted.")
        finally:
            self.stop()

    def stop(self):
        """Stop the terminal process and clean up"""
        if not self.running:
            return

        self.running = False

        if self.master_fd:
            os.close(self.master_fd)
            self.master_fd = None

        if self.pid:
            try:
                os.kill(self.pid, 9)  # Force kill
                os.waitpid(self.pid, 0)
            except (OSError, ProcessLookupError):
                pass
            self.pid = None

    def send_input(self, text: str):
        """
        Send input text to the terminal process.
        For special keystrokes (e.g. 'enter', 'up'), use the send_key() method.

        Args:
            text: Text to send to the process
        """
        if not self.running or not self.master_fd:
            raise RuntimeError("Terminal is not running")

        try:
            os.write(self.master_fd, text.encode('utf-8'))
        except OSError as e:
            raise RuntimeError(f"Error sending input: {e}")

    def send_key(self, key: str):
        """
        Send a special key to the terminal process.

        Args:
            key: Name of the key to send (e.g., 'enter', 'up', 'f1', 'shift-enter').
                 Key names are case-insensitive. See KEY_MAPPINGS for a full list.

        Raises:
            ValueError: If the key name is not recognized.
            RuntimeError: If the terminal is not running.
        """
        if not self.running or not self.master_fd:
            raise RuntimeError("Terminal is not running")

        key_lower = key.lower()
        if key_lower not in KEY_MAPPINGS:
            raise ValueError(f"Unknown key: '{key}'. Supported keys are: {', '.join(KEY_MAPPINGS.keys())}")

        data_to_send = KEY_MAPPINGS[key_lower]
        try:
            os.write(self.master_fd, data_to_send.encode('utf-8'))
        except OSError as e:
            raise RuntimeError(f"Error sending key '{key}': {e}")

    def __enter__(self):
        """Context manager entry"""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop()