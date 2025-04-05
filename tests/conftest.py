import pytest
import sys
import os
from unittest.mock import patch, MagicMock

# Add the parent directory to the path so we can import the local_agent module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from local_agent import LocalAgent

@pytest.fixture
def basic_agent():
    """Basic fixture to create a LocalAgent instance for testing."""
    with patch('local_agent.requests.get') as mock_get, \
         patch('local_agent.requests.post') as mock_post:
        # Mock the model check response
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"models": [{"name": "llama3:latest"}]}
        
        # Mock the model pull response
        mock_post.return_value.status_code = 200
        
        agent = LocalAgent()
        return agent

@pytest.fixture
def agent_with_subprocess():
    """Fixture to create a LocalAgent instance with subprocess mocking."""
    with patch('local_agent.requests.get') as mock_get, \
         patch('local_agent.requests.post') as mock_post, \
         patch('local_agent.subprocess.run') as mock_run:
        # Mock the model check response
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"models": [{"name": "llama3:latest"}]}
        
        # Mock the model pull response
        mock_post.return_value.status_code = 200
        
        # Mock the subprocess run
        mock_process = MagicMock()
        mock_process.stdout = "Command output"
        mock_process.stderr = ""
        mock_run.return_value = mock_process
        
        agent = LocalAgent()
        return agent

@pytest.fixture
def agent_with_prompts():
    """Fixture to create a LocalAgent instance with prompt mocking."""
    with patch('local_agent.requests.get') as mock_get, \
         patch('local_agent.requests.post') as mock_post, \
         patch('local_agent.Prompt.ask') as mock_prompt, \
         patch('local_agent.Confirm.ask') as mock_confirm:
        # Mock the model check response
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"models": [{"name": "llama3:latest"}]}
        
        # Mock the model pull response
        mock_post.return_value.status_code = 200
        
        # Mock the prompt to return '1' (first command)
        mock_prompt.return_value = '1'
        
        # Mock the confirm to return True (yes)
        mock_confirm.return_value = True
        
        agent = LocalAgent()
        return agent

@pytest.fixture
def full_agent():
    """Complete fixture to create a LocalAgent instance with all mocking."""
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