#!/usr/bin/env python3

import requests
import json
import subprocess
from rich.console import Console
from rich.prompt import Prompt, Confirm
import sys
import os

class LocalAgent:
    def __init__(self):
        self.console = Console()
        self.ollama_url = "http://localhost:11434"
        self.model = "llama2"  # default model, can be changed
        self.ensure_model()

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
            response = requests.post(
                f"{self.ollama_url}/api/pull",
                json={"name": self.model}
            )
            if response.status_code == 200:
                self.console.print(f"[green]Successfully pulled model {self.model}[/green]")
            else:
                self.console.print(f"[red]Error pulling model: {response.status_code}[/red]")
        except Exception as e:
            self.console.print(f"[red]Error pulling model: {str(e)}[/red]")

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

        self.console.print("[green]Starting chat with Local Agent...[/green]")
        self.console.print("[yellow]Type 'exit' to end the chat, 'help' for commands[/yellow]")

        while True:
            user_input = Prompt.ask("\n[blue]You[/blue]")
            
            if user_input.lower() == 'exit':
                break
            elif user_input.lower() == 'help':
                self.show_help()
                continue

            # Get response from Ollama
            response = self.get_ollama_response(user_input)
            if response:
                self.console.print(f"\n[green]Assistant:[/green] {response}")
            
            # Check if the response contains a command to execute
            if response and ("```bash" in response or "```shell" in response):
                command = self.extract_command(response)
                if command:
                    self.execute_command(command)

    def get_ollama_response(self, prompt):
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False
                }
            )
            if response.status_code == 200:
                return response.json().get("response", "")
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
        return command

    def execute_command(self, command):
        self.console.print(f"\n[yellow]Command to execute:[/yellow] {command}")
        if Confirm.ask("Do you want to execute this command?"):
            try:
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True
                )
                if result.stdout:
                    self.console.print("[green]Output:[/green]")
                    self.console.print(result.stdout)
                if result.stderr:
                    self.console.print("[red]Error:[/red]")
                    self.console.print(result.stderr)
            except Exception as e:
                self.console.print(f"[red]Error executing command: {str(e)}[/red]")
        else:
            self.console.print("[yellow]Command execution cancelled[/yellow]")

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