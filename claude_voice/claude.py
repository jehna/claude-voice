from .terminal import Terminal
from enum import Enum
import time

class ClaudeState(Enum):
    TEXT_INPUT = "text_input"
    CHOICE_INPUT = "choice_input"

class Claude:
    def __init__(self):
        self.terminal = Terminal("/bin/bash", ["/bin/bash", "-c", "claude", "--print"], enable_keyboard=False)
        self.terminal.add_change_callback(self.on_output_change)
        self.log_file = open("claude.log", "w")
        self.state = ClaudeState.TEXT_INPUT

    def log(self, message: str):
        self.log_file.write(message + "\n")
        self.log_file.flush()

    def on_output_change(self, _diff: str):
        output = self.terminal.get_output_buffer_text()
        if "❯" in output:
            if self.state != ClaudeState.CHOICE_INPUT:
                self.log(f"State changed to CHOICE_INPUT")
            self.state = ClaudeState.CHOICE_INPUT
        else:
            if self.state != ClaudeState.TEXT_INPUT:
                self.log(f"State changed to TEXT_INPUT")
            self.state = ClaudeState.TEXT_INPUT

    def process_instruction(self, instruction: str):
        self.log(f"Processing instruction: {instruction}")
        if self.state == ClaudeState.TEXT_INPUT:
            self._send_instruction(instruction)
        elif self.state == ClaudeState.CHOICE_INPUT:
            if "yes" in instruction.lower():
                self.log(f"Sending enter")
                self.terminal.send_key("enter")
            elif "no" in instruction.lower():
                self.log(f"Sending esc")
                self.terminal.send_key("esc")
            else:
                pass

    def _send_instruction(self, instruction: str):
        self.terminal.send_input(instruction)
        time.sleep(0.1)
        self.terminal.send_key("enter")

    def start(self):
        self.terminal.start()
        self.terminal.wait()

    def stop(self):
        self.terminal.stop()