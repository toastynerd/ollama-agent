# Local Agent

A command-line interface agent that can interact with Ollama and execute Linux commands with confirmation.

## System Requirements

- Linux (Supported distributions: Arch Linux, Ubuntu/Debian, Fedora)
- Python 3.8 or higher
- pip (Python package manager)
- Docker and Docker Compose
- systemd (for service management)

## Quick Setup

The easiest way to get started is to run the setup script:

```bash
./setup.sh
```

This script will:
1. Check for and install required system dependencies (Python, pip, Docker, Docker Compose)
2. Start the Docker service if not running
3. Add your user to the docker group if needed
4. Create a Python virtual environment and install Python dependencies
5. Guide you through any necessary post-installation steps

## Manual Setup

If you prefer to set things up manually:

1. Install system dependencies:
   - Python 3.8+
   - pip
   - Docker
   - Docker Compose

2. Start Docker and add your user to the docker group:
   ```bash
   sudo systemctl start docker
   sudo usermod -aG docker $USER
   # Log out and back in for group changes to take effect
   ```

3. Install Python dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate.fish  # For fish shell
   # OR
   source venv/bin/activate  # For bash/zsh
   pip install -r requirements.txt
   ```

4. Start Ollama:
   ```bash
   docker-compose up -d
   ```

## Usage

1. Activate the virtual environment:
   ```bash
   source venv/bin/activate.fish  # For fish shell
   # OR
   source venv/bin/activate  # For bash/zsh
   ```

2. Start the agent:
   ```bash
   ./local_agent.py
   ```

3. The agent will:
   - Check if the required Ollama model is available
   - Pull the model if needed
   - Start a chat session where you can:
     - Type questions or commands
     - Get AI responses
     - Execute suggested commands (with confirmation)
     - Type 'help' for available commands
     - Type 'exit' to end the session

## Features

- Interactive chat interface with Ollama
- Command execution with confirmation
- Rich text formatting for better readability
- Error handling and status checking
- Dockerized Ollama instance
- Automatic model management

## Notes

- The default model is set to "llama2". You can change this in the `local_agent.py` file.
- All commands require user confirmation before execution.
- The Ollama container runs on port 11434.
- If you're added to the docker group, you'll need to log out and back in for the changes to take effect.
- If you're using fish shell, make sure to use `source venv/bin/activate.fish` instead of the standard activation command. 