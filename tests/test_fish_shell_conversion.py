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

def test_convert_to_fish_syntax_variable_assignment(agent):
    """Test converting bash variable assignment to fish syntax."""
    bash_command = "VAR=$(command)"
    fish_command = agent.convert_to_fish_syntax(bash_command)
    assert fish_command == "VAR=(command)"

def test_convert_to_fish_syntax_for_loop(agent):
    """Test converting bash for loop to fish syntax."""
    bash_command = "for i in {1..5}; do echo $i; done"
    fish_command = agent.convert_to_fish_syntax(bash_command)
    assert fish_command == "for i in (seq 1 5)\necho $i\nend"

def test_convert_to_fish_syntax_for_loop_with_multiple_commands(agent):
    """Test converting bash for loop with multiple commands to fish syntax."""
    bash_command = "for i in {1..5}; do echo $i; echo 'Hello'; done"
    fish_command = agent.convert_to_fish_syntax(bash_command)
    assert fish_command == "for i in (seq 1 5)\necho $i\necho 'Hello'\nend"

def test_convert_to_fish_syntax_for_loop_with_variable_range(agent):
    """Test converting bash for loop with variable range to fish syntax."""
    bash_command = "for i in $(seq 1 5); do echo $i; done"
    fish_command = agent.convert_to_fish_syntax(bash_command)
    assert fish_command == "for i in (seq 1 5)\necho $i\nend"

def test_convert_to_fish_syntax_for_loop_with_multiple_variables(agent):
    """Test converting bash for loop with multiple variables to fish syntax."""
    bash_command = "for i in {1..5}; do for j in {1..3}; do echo $i $j; done; done"
    fish_command = agent.convert_to_fish_syntax(bash_command)
    assert fish_command == "for i in (seq 1 5)\nfor j in (seq 1 3)\necho $i $j\nend\nend"

def test_convert_to_fish_syntax_no_conversion_needed(agent):
    """Test when no conversion is needed."""
    command = "ls -la"
    fish_command = agent.convert_to_fish_syntax(command)
    assert fish_command == "ls -la"

def test_convert_to_fish_syntax_with_pipes(agent):
    """Test converting commands with pipes."""
    command = "ps aux | grep python"
    fish_command = agent.convert_to_fish_syntax(command)
    assert fish_command == "ps aux | grep python"

def test_convert_to_fish_syntax_with_redirection(agent):
    """Test converting commands with redirection."""
    command = "echo 'Hello' > output.txt"
    fish_command = agent.convert_to_fish_syntax(command)
    assert fish_command == "echo 'Hello' > output.txt"

def test_convert_to_fish_syntax_with_background(agent):
    """Test converting commands with background execution."""
    command = "long_running_command &"
    fish_command = agent.convert_to_fish_syntax(command)
    assert fish_command == "long_running_command &"

def test_convert_to_fish_syntax_with_semicolon(agent):
    """Test converting commands with semicolon."""
    command = "command1; command2"
    fish_command = agent.convert_to_fish_syntax(command)
    assert fish_command == "command1; command2" 