#!/usr/bin/env python3

import requests
import json
import subprocess
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.spinner import Spinner
from rich.live import Live
import sys
import os
import platform
import shutil

class LocalAgent:
    def __init__(self):
        self.console = Console()
        self.ollama_url = "http://localhost:11434"
        # Using a smaller model for better performance
        self.model = "llama3:8b"  # 8B parameter model
        self.ensure_model()
        self.conversation_history = []
        self.shell_type = self.detect_shell()
        self.system_prompt = f"""You are a helpful AI assistant that can execute commands on the user's system.
When asked to show information or perform actions, you should:
1. Use appropriate commands to gather the requested information
2. Always wrap commands in ```bash or ```shell code blocks
3. Explain what each command does before executing it
4. Be helpful but maintain system security
5. Use {self.shell_type} shell syntax when appropriate

Example response format:
To show your home directory, I'll use the `ls` command:
```bash
ls ~/
```

This will list all files and directories in your home folder."""

    def detect_shell(self):
        """Detect the current shell type"""
        shell = os.environ.get('SHELL', '')
        if 'fish' in shell:
            return 'fish'
        elif 'zsh' in shell:
            return 'zsh'
        elif 'bash' in shell:
            return 'bash'
        else:
            return 'sh'  # default to sh

    def ensure_model(self):
        try:
            # Check if model exists
            response = requests.get(f"{self.ollama_url}/api/tags")
            if response.status_code == 200:
                models = response.json().get("models", [])
                if not any(model["name"] == self.model for model in models):
                    self.console.print(f"[yellow]Model {self.model} not found. Pulling it now...[/yellow]")
                    self.pull_model()
        except Exception as e:
            self.console.print(f"[red]Error checking model status: {str(e)}[/red]")

    def pull_model(self):
        try:
            # Pull model with GPU configuration
            response = requests.post(
                f"{self.ollama_url}/api/pull",
                json={
                    "name": self.model,
                    "insecure": True  # Allow pulling from insecure sources if needed
                }
            )
            if response.status_code == 200:
                self.console.print(f"[green]Successfully pulled model {self.model}[/green]")
                # Verify GPU usage
                self.check_gpu_usage()
            else:
                self.console.print(f"[red]Error pulling model: {response.status_code}[/red]")
        except Exception as e:
            self.console.print(f"[red]Error pulling model: {str(e)}[/red]")

    def check_gpu_usage(self):
        """Check if GPU is being used by Ollama"""
        try:
            response = requests.get(f"{self.ollama_url}/api/show", params={"name": self.model})
            if response.status_code == 200:
                model_info = response.json()
                if model_info.get("gpu_layers", 0) > 0:
                    self.console.print("[green]GPU acceleration is enabled[/green]")
                else:
                    self.console.print("[yellow]GPU acceleration is not enabled. Make sure NVIDIA drivers and nvidia-container-toolkit are installed.[/yellow]")
        except Exception as e:
            self.console.print(f"[red]Error checking GPU status: {str(e)}[/red]")

    def check_ollama_status(self):
        try:
            response = requests.get(f"{self.ollama_url}/api/tags")
            return response.status_code == 200
        except requests.exceptions.ConnectionError:
            return False

    def start_chat(self):
        if not self.check_ollama_status():
            self.console.print("[red]Error: Ollama is not running. Please start it using 'docker-compose up -d'[/red]")
            return

        self.console.print(f"[green]Starting chat with Local Agent...[/green]")
        self.console.print(f"[yellow]Using {self.shell_type} shell[/yellow]")
        self.console.print(f"[yellow]Model: {self.model}[/yellow]")
        self.console.print("[yellow]Type 'exit' to end the chat, 'help' for commands[/yellow]")

        # Initialize conversation with system prompt
        self.conversation_history.append({"role": "system", "content": self.system_prompt})

        while True:
            try:
                user_input = Prompt.ask("\n[blue]You[/blue]")
                
                if user_input.lower() == 'exit':
                    break
                elif user_input.lower() == 'help':
                    self.show_help()
                    continue

                # Get response from Ollama with spinner
                with Live(Spinner("dots", text="Thinking..."), refresh_per_second=10, transient=True) as live:
                    response = self.get_ollama_response(user_input)
                    if response:
                        self.console.print(f"\n[green]Assistant:[/green] {response}")
                        self.conversation_history.append({"role": "assistant", "content": response})
                
                # Check if the response contains a command to execute
                if response and ("```bash" in response or "```shell" in response):
                    command = self.extract_command(response)
                    if command:
                        output = self.execute_command(command)
                        if output:
                            # Send command output back to Ollama for context with spinner
                            with Live(Spinner("dots", text="Analyzing output..."), refresh_per_second=10, transient=True) as live:
                                feedback_prompt = f"I executed the command '{command}' and got this output:\n{output}\nPlease analyze this output and let me know if you need any clarification or if there's anything important I should know."
                                feedback_response = self.get_ollama_response(feedback_prompt)
                                if feedback_response:
                                    self.console.print(f"\n[green]Assistant:[/green] {feedback_response}")
                                    self.conversation_history.append({"role": "assistant", "content": feedback_response})
            except KeyboardInterrupt:
                self.console.print("\n[yellow]Chat session ended by user.[/yellow]")
                break
            except Exception as e:
                self.console.print(f"[red]An error occurred: {str(e)}[/red]")
                continue

    def get_ollama_response(self, prompt):
        try:
            # Include conversation history in the context
            context = "\n".join([f"{msg['role']}: {msg['content']}" for msg in self.conversation_history[-5:]])  # Last 5 messages for context
            full_prompt = f"{context}\n\nUser: {prompt}\nAssistant:"
            
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {
                        "num_gpu": 1,  # Use GPU if available
                        "num_thread": 4  # Adjust based on your CPU
                    }
                }
            )
            if response.status_code == 200:
                response_text = response.json().get("response", "")
                self.conversation_history.append({"role": "user", "content": prompt})
                return response_text
            else:
                self.console.print(f"[red]Error: Ollama returned status code {response.status_code}[/red]")
                return ""
        except Exception as e:
            self.console.print(f"[red]Error getting response from Ollama: {str(e)}[/red]")
            return ""

    def extract_command(self, response):
        # Extract command from code blocks
        if "```bash" in response:
            start = response.find("```bash") + 7
        elif "```shell" in response:
            start = response.find("```shell") + 8
        else:
            return None

        end = response.find("```", start)
        if end == -1:
            return None

        command = response[start:end].strip()
        # Remove any markdown formatting that might have been included
        command = command.replace("`", "").strip()
        return command

    def convert_to_fish_syntax(self, command):
        """Convert bash commands to fish shell syntax"""
        # Replace bash variable assignment
        command = command.replace("$(command)", "(command)")
        
        # Replace bash for loops with fish for loops
        if "for" in command and "do" in command and "done" in command:
            # Extract the loop variable and range
            import re
            for_match = re.search(r'for\s+(\w+)\s+in\s+\((.*?)\);?\s*do', command)
            if for_match:
                var_name = for_match.group(1)
                loop_range = for_match.group(2)
                
                # Extract the loop body
                body_start = command.find("do") + 2
                body_end = command.rfind("done")
                if body_start > 1 and body_end > body_start:
                    loop_body = command[body_start:body_end].strip()
                    
                    # Create fish for loop
                    fish_loop = f"for {var_name} in {loop_range}\n{loop_body}\nend"
                    return fish_loop
        
        return command

    def execute_command(self, command):
        self.console.print(f"\n[yellow]Command to execute:[/yellow] {command}")
        if Confirm.ask("Do you want to execute this command?"):
            try:
                # Use the appropriate shell based on the detected shell type
                if self.shell_type == 'fish':
                    # For fish shell, convert bash syntax to fish syntax
                    fish_command = self.convert_to_fish_syntax(command)
                    self.console.print(f"[yellow]Converted to fish syntax:[/yellow] {fish_command}")
                    
                    # For fish shell, we need to use fish -c
                    result = subprocess.run(
                        ['fish', '-c', fish_command],
                        capture_output=True,
                        text=True
                    )
                else:
                    # For other shells, use the shell directly
                    result = subprocess.run(
                        command,
                        shell=True,
                        capture_output=True,
                        text=True
                    )
                
                output = []
                if result.stdout:
                    self.console.print("[green]Output:[/green]")
                    self.console.print(result.stdout)
                    output.append(result.stdout)
                if result.stderr:
                    self.console.print("[red]Error:[/red]")
                    self.console.print(result.stderr)
                    output.append(f"Error: {result.stderr}")
                return "\n".join(output) if output else None
            except Exception as e:
                error_msg = f"[red]Error executing command: {str(e)}[/red]"
                self.console.print(error_msg)
                return error_msg
        else:
            self.console.print("[yellow]Command execution cancelled[/yellow]")
            return None

    def show_help(self):
        help_text = """
        Available commands:
        - help: Show this help message
        - exit: End the chat session
        - Any other input will be processed by the AI
        """
        self.console.print(help_text)

def main():
    agent = LocalAgent()
    agent.start_chat()

if __name__ == "__main__":
    main() 