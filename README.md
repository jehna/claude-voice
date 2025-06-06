# Claude Code Voice UI
> A true hammock driven development

This project implements a hands-free development environment based on the Claude
Code coding agent text user interface (TUI). You control Claude Code TUI by only
using your voice.

TODO: Claude speaks back

## Getting started

Initialise a proper Python environment if your don't have one:

```bash
python3 -m venv .venv --prompt claude-voice
source .venv/bin/activate
pip install uv
uv install
```

After you have initialised the environment and logged in to `claude` CLI, run:

```bash
./start.sh
```

This starts the interactive Claude Code voice session.