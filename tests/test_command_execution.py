import pytest
import sys
import os
from unittest.mock import patch, MagicMock, Mock, call
import subprocess
from rich.prompt import Prompt, Confirm

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from local_agent import LocalAgent

@pytest.fixture
def agent():
    """Create a LocalAgent instance with mocked components."""
    with patch('subprocess.run') as mock_run, \
         patch('rich.prompt.Confirm.ask') as mock_confirm, \
         patch('rich.prompt.Prompt.ask') as mock_prompt:
        agent = LocalAgent()
        agent.console.print = MagicMock()
        # Set up default mock responses
        mock_confirm.return_value = True  # Default to confirming commands
        mock_prompt.return_value = 'c'    # Default to canceling in multiple command scenarios
        # Set up default subprocess response
        mock_process = MagicMock()
        mock_process.stdout = "Command output"
        mock_process.stderr = ""
        mock_run.return_value = mock_process
        yield agent

def test_execute_command_single_command(agent):
    """Test executing a single command."""
    command = "uname -a"
    # Mock subprocess to return success
    mock_process = MagicMock()
    mock_process.stdout = "Linux test 5.15.0"
    mock_process.stderr = ""
    subprocess.run.return_value = mock_process
    # Mock confirmation to return True
    Confirm.ask.return_value = True
    
    output = agent.execute_command(command)
    
    assert output == "Linux test 5.15.0"
    subprocess.run.assert_called_once()
    Confirm.ask.assert_called_once()

def test_execute_command_multiple_commands(agent):
    """Test executing multiple commands with selection."""
    commands = "uname -a\nlscpu\nfree -h"
    # Mock prompt to select first command
    Prompt.ask.return_value = '1'
    # Mock subprocess to return success
    mock_process = MagicMock()
    mock_process.stdout = "Linux test 5.15.0"
    mock_process.stderr = ""
    subprocess.run.return_value = mock_process
    
    output = agent.execute_command(commands)
    
    assert output == "Linux test 5.15.0"
    subprocess.run.assert_called_once()
    Prompt.ask.assert_called_once()

def test_execute_command_with_fish_shell(agent):
    """Test executing a command with fish shell."""
    # Mock the shell type to be fish
    agent.shell_type = 'fish'
    command = "for i in {1..5}; do echo $i; done"
    # Mock subprocess to return success
    mock_process = MagicMock()
    mock_process.stdout = "1\n2\n3\n4\n5\n"
    mock_process.stderr = ""
    subprocess.run.return_value = mock_process
    # Mock confirmation to return True
    Confirm.ask.return_value = True
    
    output = agent.execute_command(command)
    
    assert output == "1\n2\n3\n4\n5\n"
    subprocess.run.assert_called_once()
    Confirm.ask.assert_called_once()

def test_execute_command_with_error(agent):
    """Test executing a command that returns an error."""
    command = "nonexistent_command"
    # Mock subprocess to return error
    mock_process = MagicMock()
    mock_process.stdout = ""
    mock_process.stderr = "Error: Command not found"
    subprocess.run.return_value = mock_process
    # Mock confirmation to return True
    Confirm.ask.return_value = True
    
    output = agent.execute_command(command)
    
    assert "Error: Command not found" in output
    subprocess.run.assert_called_once()
    Confirm.ask.assert_called_once()

def test_execute_command_cancelled(agent):
    """Test cancelling command execution."""
    command = "uname -a"
    # Mock confirmation to return False
    Confirm.ask.return_value = False
    
    output = agent.execute_command(command)
    
    assert output is None
    subprocess.run.assert_not_called()
    Confirm.ask.assert_called_once()

def test_execute_command_all_commands(agent):
    """Test executing all commands when multiple are present."""
    commands = "uname -a\nlscpu\nfree -h"
    # Mock prompt to select 'a' for all commands
    Prompt.ask.return_value = 'a'
    # Mock subprocess to return success for each command
    mock_process = MagicMock()
    mock_process.stdout = "Command output"
    mock_process.stderr = ""
    subprocess.run.return_value = mock_process
    
    output = agent.execute_command(commands)
    
    assert output == "Command output\nCommand output\nCommand output"
    assert subprocess.run.call_count == 3
    Prompt.ask.assert_called_once()

def test_execute_command_quit(agent):
    """Test quitting when multiple commands are present."""
    commands = "uname -a\nlscpu\nfree -h"
    # Mock prompt to select 'q' for quit
    Prompt.ask.return_value = 'q'
    
    with pytest.raises(SystemExit):
        agent.execute_command(commands)
    
    subprocess.run.assert_not_called()
    Prompt.ask.assert_called_once()

def test_execute_command_cancel_multiple(agent):
    """Test cancelling when multiple commands are present."""
    commands = "uname -a\nlscpu\nfree -h"
    # Mock prompt to select 'c' for cancel
    Prompt.ask.return_value = 'c'
    
    output = agent.execute_command(commands)
    
    assert output is None
    subprocess.run.assert_not_called()
    Prompt.ask.assert_called_once() 