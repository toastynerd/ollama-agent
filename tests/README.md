# Local Agent Tests

This directory contains tests for the Local Agent application.

## Test Structure

The tests are organized into the following files:

- `test_local_agent.py`: Tests for the command extraction functionality
- `test_command_execution.py`: Tests for the command execution functionality
- `test_ollama_interaction.py`: Tests for the Ollama interaction functionality
- `test_fish_shell_conversion.py`: Tests for the fish shell conversion functionality
- `test_main.py`: Tests for the main functionality and integration tests
- `conftest.py`: Shared fixtures for all tests

## Running Tests

To run the tests, use the following command:

```bash
pytest
```

To run a specific test file:

```bash
pytest tests/test_local_agent.py
```

To run a specific test function:

```bash
pytest tests/test_local_agent.py::test_extract_command_single_command
```

To run tests with verbose output:

```bash
pytest -v
```

To run tests with coverage report:

```bash
pytest --cov=local_agent
```

## Test Fixtures

The tests use several fixtures to create LocalAgent instances with different mocking configurations:

- `basic_agent`: Basic fixture with minimal mocking
- `agent_with_subprocess`: Fixture with subprocess mocking
- `agent_with_prompts`: Fixture with prompt mocking
- `full_agent`: Complete fixture with all mocking

## Adding New Tests

When adding new tests, follow these guidelines:

1. Use the appropriate fixture for your test
2. Add descriptive docstrings to your test functions
3. Use meaningful test names that describe what is being tested
4. Mock external dependencies to ensure tests are isolated
5. Add tests for both success and error cases 