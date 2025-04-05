import pytest
import sys
import os
from unittest.mock import patch, MagicMock, Mock, call
import requests

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from local_agent import LocalAgent

@pytest.fixture
def agent():
    """Create a LocalAgent instance with mocked HTTP requests."""
    with patch('requests.get') as mock_get, \
         patch('requests.post') as mock_post:
        agent = LocalAgent()
        agent.console.print = MagicMock()
        yield agent

def test_check_ollama_status_running(agent):
    """Test checking Ollama status when it's running."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    requests.get.return_value = mock_response
    
    assert agent.check_ollama_status() is True
    assert requests.get.call_count >= 1
    assert requests.get.call_args_list[-1] == call('http://localhost:11434/api/tags')

def test_check_ollama_status_not_running(agent):
    """Test checking Ollama status when it's not running."""
    requests.get.side_effect = requests.exceptions.ConnectionError()
    
    assert agent.check_ollama_status() is False
    assert requests.get.call_count >= 1
    assert requests.get.call_args_list[-1] == call('http://localhost:11434/api/tags')

def test_get_ollama_response_success(agent):
    """Test getting a successful response from Ollama."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {'response': 'Test response'}
    requests.post.return_value = mock_response
    
    response = agent.get_ollama_response('Test prompt')
    assert response == 'Test response'
    requests.post.assert_called_once()

def test_get_ollama_response_error(agent):
    """Test handling an error response from Ollama."""
    mock_response = MagicMock()
    mock_response.status_code = 500
    requests.post.return_value = mock_response
    
    response = agent.get_ollama_response('Test prompt')
    assert response is None
    requests.post.assert_called_once()

def test_get_ollama_response_connection_error(agent):
    """Test handling a connection error from Ollama."""
    requests.post.side_effect = requests.exceptions.ConnectionError()
    
    response = agent.get_ollama_response('Test prompt')
    assert response is None
    requests.post.assert_called_once()

def test_pull_model_success(agent):
    """Test successfully pulling a model."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {'status': 'success'}
    requests.post.return_value = mock_response
    
    assert agent.pull_model() is True
    requests.post.assert_called_once()

def test_pull_model_error(agent):
    """Test handling an error when pulling a model."""
    mock_response = MagicMock()
    mock_response.status_code = 500
    requests.post.return_value = mock_response
    
    assert agent.pull_model() is False
    requests.post.assert_called_once()

def test_pull_model_connection_error(agent):
    """Test handling a connection error when pulling a model."""
    requests.post.side_effect = requests.exceptions.ConnectionError()
    
    assert agent.pull_model() is False
    requests.post.assert_called_once()

def test_extract_command_with_command():
    """Test extracting a command from a response that contains one."""
    agent = LocalAgent()
    response = "Here's a command:\n```bash\nls -la\n```"
    
    command = agent.extract_command(response)
    assert command == "ls -la"

def test_extract_command_without_command():
    """Test extracting a command from a response that doesn't contain one."""
    agent = LocalAgent()
    response = "This is just a regular response without a command."
    
    command = agent.extract_command(response)
    assert command is None

def test_extract_command_with_multiple_commands():
    """Test extracting a command when multiple commands are present."""
    agent = LocalAgent()
    response = "Here are some commands:\n```bash\nls -la\n```\n```bash\necho 'test'\n```"
    
    command = agent.extract_command(response)
    assert command == "ls -la\necho 'test'"  # Should return all commands found 