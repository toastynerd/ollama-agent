import pytest
import sys
import os
from unittest.mock import patch, MagicMock

# Add the parent directory to the path so we can import the local_agent module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from local_agent import LocalAgent

@pytest.fixture
def agent():
    """Fixture to create a LocalAgent instance for testing."""
    with patch('local_agent.requests.get') as mock_get, \
         patch('local_agent.requests.post') as mock_post:
        # Mock the model check response
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"models": [{"name": "llama3:latest"}]}
        
        # Mock the model pull response
        mock_post.return_value.status_code = 200
        
        agent = LocalAgent()
        return agent

def test_extract_command_single_command(agent):
    """Test extracting a single command from a response."""
    response = """
    To check your system information, I'll use the `uname` command:
    ```bash
    uname -a
    ```
    This will display detailed information about your system.
    """
    command = agent.extract_command(response)
    assert command == "uname -a"

def test_extract_command_multiple_commands(agent):
    """Test extracting multiple commands from a response."""
    response = """
    Here are some commands to check your system:
    
    ```bash
    uname -a
    ```
    
    ```bash
    lscpu
    ```
    
    ```bash
    free -h
    ```
    """
    command = agent.extract_command(response)
    # Should return the first command only
    assert command == "uname -a"

def test_extract_command_no_commands(agent):
    """Test extracting commands when none are present."""
    response = "This is just some text without any commands."
    command = agent.extract_command(response)
    assert command is None

def test_extract_command_with_explanatory_text(agent):
    """Test extracting commands when there's explanatory text."""
    response = """
    To check your system information, I'll use the `uname` command.
    This will display detailed information about your system.
    
    ```bash
    uname -a
    ```
    
    Next, let's check your CPU information with:
    ```bash
    lscpu
    ```
    """
    command = agent.extract_command(response)
    assert command == "uname -a"

def test_extract_command_with_inline_code(agent):
    """Test extracting commands from inline code blocks."""
    response = """
    You can use the `uname -a` command to check your system information.
    Or try `lscpu` for CPU details.
    """
    command = agent.extract_command(response)
    assert command == "uname -a"

def test_extract_command_with_comments(agent):
    """Test extracting commands when there are comments in the code blocks."""
    response = """
    ```bash
    # This is a comment
    uname -a
    # Another comment
    ```
    """
    command = agent.extract_command(response)
    assert command == "uname -a"

def test_extract_command_with_prompt_characters(agent):
    """Test extracting commands with prompt characters."""
    response = """
    ```bash
    $ uname -a
    ```
    """
    command = agent.extract_command(response)
    assert command == "uname -a"

def test_extract_command_with_sudo(agent):
    """Test extracting commands with sudo."""
    response = """
    ```bash
    sudo apt update
    ```
    """
    command = agent.extract_command(response)
    assert command == "sudo apt update"

def test_extract_command_with_pipes(agent):
    """Test extracting commands with pipes."""
    response = """
    ```bash
    ps aux | grep python
    ```
    """
    command = agent.extract_command(response)
    assert command == "ps aux | grep python" 