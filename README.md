# Workspace Python Environments

This workspace contains exercises that use two different Python versions. Choose the environment that matches the exercise folder before running its commands.

## Quick reference

| Exercise folder | Python environment | Activation required? |
|---|---|---|
| `py3.13-exercises-and-project/` | Python 3.13 virtual environment | Yes |

| Task | Command |
|---|---|
| Check the active Python version | `python --version` |
| Activate Python 3.13 | `source /voc/data/py313-venv/bin/activate` |
| Leave Python 3.13 | `deactivate` |

> **Important:** Use Python 3.10 for the Python 3.10 exercises and activate the Python 3.13 environment before running the Python 3.13 exercises. Check `python --version` after selecting an environment.

## Prerequisites

- A terminal with Bash or a compatible shell.
- The workspace files available locally.
- The Python 3.13 environment at `/voc/data/py313-venv` for Python 3.13 exercises.


## Python 3.13 exercises and project

Activate the Python 3.13 virtual environment before running commands in `py3.13-exercises-and-project/`:

```bash
source /voc/data/py313-venv/bin/activate
python --version  # Should show Python 3.13.x
```

For example, to run the Claims Intake exercise:

```bash
cd "py3.13-exercises-and-project/Build a Claims Intake Agent with a stop_reason-Driven Loop/exercises/01-loop/starter"
python -m claims_intake.run --all
```

When finished, deactivate the environment to return to the system Python:

```bash
deactivate
```

The Python 3.13 environment includes modern development tools and packages such as the Anthropic SDK, Pydantic, pytest, mypy, Ruff, and uv. See [`py3.13-exercises-and-project/requirements.py313-venv.txt`](py3.13-exercises-and-project/requirements.py313-venv.txt) for the package list.

- **Exercises:** Tutorials on building AI systems with Claude, including claims intake, retail support context management, Claude Code configuration, and quality monitoring.
- **Capstone project:** An integrative project to build and run the four course systems, verify their implementations, capture artifacts, and write an evidence-based reflection brief.

Each exercise provides a `starter/` folder for the learning tasks and a `solution/` folder with a reference implementation.
