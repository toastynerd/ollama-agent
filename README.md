# Local Agent

A command-line interface agent that can interact with Ollama and execute Linux commands with confirmation.

## Prerequisites

- Docker and Docker Compose
- Python 3.8 or higher
- pip (Python package manager)

## Setup

1. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

2. Start the Ollama container:
   ```bash
   docker-compose up -d
   ```

3. Make the Python script executable:
   ```bash
   chmod +x local_agent.py
   ```

## Usage

1. Start the agent:
   ```bash
   ./local_agent.py
   ```

2. The agent will start a chat session where you can:
   - Type your questions or requests
   - The agent will process them using Ollama
   - If the response contains a command, it will ask for confirmation before executing
   - Type 'help' for available commands
   - Type 'exit' to end the session

## Features

- Interactive chat interface with Ollama
- Command execution with confirmation
- Rich text formatting for better readability
- Error handling and status checking
- Dockerized Ollama instance

## Notes

- The default model is set to "llama2". You can change this in the `local_agent.py` file.
- All commands are executed with user confirmation for safety.
- The Ollama container runs on port 11434. 