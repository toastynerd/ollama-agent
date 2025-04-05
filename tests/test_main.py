import pytest
import sys
import os
from unittest.mock import patch, MagicMock, Mock

# Add the parent directory to the path so we can import the local_agent module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from local_agent import LocalAgent, main

@pytest.fixture
def agent():
    """Fixture to create a LocalAgent instance for testing."""
    with patch('local_agent.requests.get') as mock_get, \
         patch('local_agent.requests.post') as mock_post, \
         patch('local_agent.subprocess.run') as mock_run, \
         patch('local_agent.Prompt.ask') as mock_prompt, \
         patch('local_agent.Confirm.ask') as mock_confirm, \
         patch('local_agent.Console.print') as mock_print, \
         patch('local_agent.Live') as mock_live:
        # Mock the model check response
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"models": [{"name": "llama3:latest"}]}
        
        # Mock the model pull response
        mock_post.return_value.status_code = 200
        
        # Mock the prompt to return 'exit'
        mock_prompt.return_value = 'exit'
        
        # Mock the confirm to return True (yes)
        mock_confirm.return_value = True
        
        # Mock the subprocess run
        mock_process = MagicMock()
        mock_process.stdout = "Command output"
        mock_process.stderr = ""
        mock_run.return_value = mock_process
        
        # Mock the Live context manager
        mock_live_context = MagicMock()
        mock_live.return_value.__enter__.return_value = mock_live_context
        
        agent = LocalAgent()
        return agent

def test_start_chat_ollama_not_running(agent):
    """Test starting chat when Ollama is not running."""
    # Mock check_ollama_status to return False
    agent.check_ollama_status = MagicMock(return_value=False)
    
    # Mock console.print to capture the output
    agent.console.print = MagicMock()
    
    agent.start_chat()
    
    # Check that the error was logged
    agent.console.print.assert_called_with("[red]Error: Ollama is not running. Please start it using 'docker-compose up -d'[/red]")

def test_start_chat_exit_command(agent):
    """Test starting chat and exiting immediately."""
    # Mock check_ollama_status to return True
    agent.check_ollama_status = MagicMock(return_value=True)
    
    # Mock get_ollama_response to return a response with a command
    agent.get_ollama_response = MagicMock(return_value="```bash\nuname -a\n```")
    
    # Mock process_response to do nothing
    agent.process_response = MagicMock()
    
    # Mock console.print
    agent.console.print = MagicMock()
    
    # Mock Prompt.ask to return 'exit'
    with patch('rich.prompt.Prompt.ask', return_value='exit'):
        agent.start_chat()
    
    # Check that the welcome message was printed
    agent.console.print.assert_any_call("[green]Starting chat with Local Agent...[/green]")
    agent.console.print.assert_any_call(f"[yellow]Using {agent.shell_type} shell[/yellow]")
    agent.console.print.assert_any_call("[yellow]Model: llama3:latest[/yellow]")
    agent.console.print.assert_any_call("[yellow]Type 'exit' to end the chat, 'help' for commands[/yellow]")

def test_start_chat_help_command(agent):
    """Test starting chat and using the help command."""
    # Mock check_ollama_status to return True
    agent.check_ollama_status = MagicMock(return_value=True)
    
    # Mock console.print
    agent.console.print = MagicMock()
    
    # Mock Prompt.ask to return 'help' first, then 'exit'
    with patch('rich.prompt.Prompt.ask', side_effect=['help', 'exit']):
        agent.start_chat()
    
    # Check that the help message was printed
    help_text = """
        Available commands:
        - help: Show this help message
        - exit: End the chat session
        - Any other input will be processed by the AI
        """
    agent.console.print.assert_any_call(help_text)

def test_start_chat_with_command_execution(agent):
    """Test starting chat and executing a command."""
    # Mock check_ollama_status to return True
    agent.check_ollama_status = MagicMock(return_value=True)
    
    # Mock console.print
    agent.console.print = MagicMock()
    
    # Mock get_ollama_response to return a response with a command
    agent.get_ollama_response = MagicMock(return_value="```bash\nuname -a\n```")
    
    # Mock process_response to execute the command
    agent.process_response = MagicMock()
    
    # Mock Prompt.ask to return a command first, then 'exit'
    with patch('rich.prompt.Prompt.ask', side_effect=['show system info', 'exit']):
        agent.start_chat()
    
    # Check that process_response was called with the command
    agent.process_response.assert_called_with("```bash\nuname -a\n```")

def test_start_chat_with_error(agent):
    """Test starting chat and handling an error."""
    # Mock check_ollama_status to return True
    agent.check_ollama_status = MagicMock(return_value=True)
    
    # Mock console.print
    agent.console.print = MagicMock()
    
    # Mock Prompt.ask to raise an exception first, then return 'exit'
    prompt_mock = Mock()
    prompt_mock.side_effect = [Exception("Test error"), 'exit']
    
    with patch('rich.prompt.Prompt.ask', side_effect=prompt_mock.side_effect):
        agent.start_chat()
    
    # Check that the error was logged
    agent.console.print.assert_any_call("[red]An error occurred: Test error[/red]")

def test_main_function(agent):
    """Test the main function."""
    # Mock LocalAgent to return our agent
    with patch('local_agent.LocalAgent', return_value=agent):
        # Mock start_chat
        agent.start_chat = MagicMock()
        
        # Mock sys.argv
        with patch('sys.argv', ['local_agent.py']):
            main()
        
        # Check that start_chat was called
        agent.start_chat.assert_called_once()

def test_main_function_test_mode(monkeypatch):
    """Test the main function in test mode"""
    # Create a mock agent
    mock_agent = Mock()
    mock_agent.execute_command = Mock(return_value="Test output")
    
    # Mock LocalAgent to return our mock agent
    monkeypatch.setattr('local_agent.LocalAgent', Mock(return_value=mock_agent))
    
    # Create a mock for Prompt.ask that returns different values based on the prompt
    prompt_mock = Mock()
    def prompt_side_effect(*args, **kwargs):
        if 'Your choice' in str(args[0]):
            return 'a'  # Execute all commands when asked for command choice
        return 'exit'  # Exit the chat loop otherwise
    prompt_mock.side_effect = prompt_side_effect
    monkeypatch.setattr('rich.prompt.Prompt.ask', prompt_mock)
    
    # Mock Confirm.ask to always return True
    monkeypatch.setattr('rich.prompt.Confirm.ask', Mock(return_value=True))
    
    # Mock sys.argv to simulate running in test mode
    monkeypatch.setattr('sys.argv', ['local_agent.py', '--test'])
    
    # Mock sys.exit to prevent the program from actually exiting
    mock_exit = Mock()
    monkeypatch.setattr('sys.exit', mock_exit)
    
    # Run the main function
    main()
    
    # Verify that execute_command was called with the test commands
    mock_agent.execute_command.assert_called_with("""
        ls -la
        pwd
        uname -a
        """)
    
    # Verify that sys.exit was called with status 0
    mock_exit.assert_called_with(0)

def test_process_response_with_command(agent):
    """Test processing a response with a command."""
    response = "```bash\nuname -a\n```"
    
    # Mock extract_command to return a command
    agent.extract_command = MagicMock(return_value="uname -a")
    
    # Mock execute_command to return output
    agent.execute_command = MagicMock(return_value="Command output")
    
    # Mock get_ollama_response to return a response
    agent.get_ollama_response = MagicMock(return_value="Analysis of the output")
    
    # Mock console.print
    agent.console.print = MagicMock()
    
    agent.process_response(response)
    
    # Check that extract_command was called with the response
    agent.extract_command.assert_called_once_with(response)
    
    # Check that execute_command was called with the command
    agent.execute_command.assert_called_once_with("uname -a")
    
    # Check that get_ollama_response was called with the feedback
    agent.get_ollama_response.assert_called_once_with("I executed the command 'uname -a' and got this output:\nCommand output\nPlease analyze this output and let me know if you need any clarification or if there's anything important I should know.")
    
    # Check that the analysis was printed
    agent.console.print.assert_any_call("\n[green]Assistant:[/green] Analysis of the output")

def test_process_response_without_command(agent):
    """Test processing a response without a command."""
    response = """```bash
    # This is just a comment
    """
    
    # Create a new mock for extract_command
    mock_extract = Mock(return_value=None)
    agent.extract_command = mock_extract
    
    # Mock execute_command
    mock_execute = Mock()
    agent.execute_command = mock_execute
    
    # Mock console.print
    agent.console.print = MagicMock()
    
    agent.process_response(response)
    
    # Check that extract_command was called with the response
    mock_extract.assert_called_once_with(response)
    
    # Check that execute_command was not called
    mock_execute.assert_not_called()

def test_process_response_with_empty_response(agent):
    """Test processing an empty response."""
    response = ""
    
    # Create a new mock for extract_command
    mock_extract = Mock()
    agent.extract_command = mock_extract
    
    # Mock execute_command
    mock_execute = Mock()
    agent.execute_command = mock_execute
    
    # Mock console.print
    agent.console.print = MagicMock()
    
    agent.process_response(response)
    
    # Check that extract_command was not called
    mock_extract.assert_not_called()
    
    # Check that execute_command was not called
    mock_execute.assert_not_called() 