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
        self.model = "llama3:latest"  # Updated to match available model
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
                        "num_thread": 4,  # Adjust based on your CPU
                        "model_size": "8b"  # Specify 8B parameter model
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
        # Extract all commands from code blocks
        commands = []
        
        # Find all code blocks
        import re
        code_blocks = re.findall(r'```(?:bash|shell)\n(.*?)\n```', response, re.DOTALL)
        
        for block in code_blocks:
            # Split by newlines and clean up each command
            block_commands = [cmd.strip() for cmd in block.split('\n') if cmd.strip()]
            commands.extend(block_commands)
        
        # If no commands found, return None
        if not commands:
            return None
            
        # If only one command, return it directly
        if len(commands) == 1:
            return commands[0]
            
        # If multiple commands, join them with newlines
        return '\n'.join(commands)

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
        # Split multiple commands if they exist
        commands = [cmd.strip() for cmd in command.split('\n') if cmd.strip()]
        
        if len(commands) > 1:
            self.console.print("\n[bold yellow]Multiple commands detected:[/bold yellow]")
            for i, cmd in enumerate(commands, 1):
                self.console.print(f"[cyan]{i}.[/cyan] {cmd}")
            
            self.console.print("\n[bold green]Select command to execute:[/bold green]")
            self.console.print("[cyan]Options:[/cyan]")
            self.console.print(f"  [cyan]1-{len(commands)}[/cyan] - Execute a specific command")
            self.console.print("  [cyan]a[/cyan] - Execute all commands")
            self.console.print("  [cyan]c[/cyan] - Cancel and return to chat")
            self.console.print("  [bold red]q[/bold red] - [bold red]QUIT: Exit the program[/bold red]")
            
            choice = Prompt.ask(
                "\n[bold green]Your choice[/bold green]",
                choices=[str(i) for i in range(1, len(commands) + 1)] + ['a', 'c', 'q'],
                default='c'
            )
            
            if choice == 'c':
                self.console.print("[yellow]Command execution cancelled. Returning to chat.[/yellow]")
                return None
            elif choice == 'q':
                self.console.print("[bold red]Exiting the program. Goodbye![/bold red]")
                sys.exit(0)
            elif choice == 'a':
                # Execute all commands in sequence
                all_output = []
                for cmd in commands:
                    self.console.print(f"\n[bold blue]Executing:[/bold blue] {cmd}")
                    output = self._run_single_command(cmd, default_yes=True)
                    if output:
                        all_output.append(output)
                return "\n".join(all_output) if all_output else None
            else:
                command = commands[int(choice) - 1]
        
        return self._run_single_command(command, default_yes=True)

    def _run_single_command(self, command, default_yes=False):
        self.console.print(f"\n[bold blue]Command to execute:[/bold blue] {command}")
        if Confirm.ask("[bold green]Execute this command?[/bold green]", default=default_yes):
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
                    self.console.print("[bold green]Output:[/bold green]")
                    self.console.print(result.stdout)
                    output.append(result.stdout)
                if result.stderr:
                    self.console.print("[bold red]Error:[/bold red]")
                    self.console.print(result.stderr)
                    output.append(f"Error: {result.stderr}")
                return "\n".join(output) if output else None
            except Exception as e:
                error_msg = f"[bold red]Error executing command: {str(e)}[/bold red]"
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
    
    # Add test mode
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        print("Running in test mode...")
        # Simulate multiple commands for testing
        test_commands = """
        ls -la
        pwd
        uname -a
        """
        output = agent.execute_command(test_commands)
        sys.exit(0)
    
    print("Starting chat with Local Agent...")
    print("Using", agent.shell_type, "shell")
    print("Model:", agent.model)
    print('Type \'exit\' to end the chat, \'help\' for commands\n')
    
    agent.start_chat()

if __name__ == "__main__":
    main() 