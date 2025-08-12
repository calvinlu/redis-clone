# Redis Python Implementation

[![progress-banner](https://backend.codecrafters.io/progress/redis/bce7133e-d6dd-497d-800e-b9b409e5649d)](https://app.codecrafters.io/users/codecrafters-bot?r=2qF)

This is a Python implementation of a Redis clone, built for the ["Build Your Own Redis" Challenge](https://codecrafters.io/challenges/redis).

## Features

- [x] Basic Redis protocol (RESP) support
- [x] Command dispatching system
- [x] In-memory key-value store
- [x] Support for basic commands: `PING`, `SET`, `GET`

## Development Setup

### Prerequisites

- Python 3.8+
- pip (Python package manager)

### Installation

1. Create and activate a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install development dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```

### Running Tests

Run all tests:
```bash
pytest
```

Run tests with coverage report:
```bash
pytest --cov=app tests/
```

### Running the Server

Start the Redis server:
```bash
python -m app.main
```

Connect using the Redis CLI:
```bash
redis-cli -p 6379
```

## Project Structure

```
app/
├── commands/          # Command implementations
│   ├── __init__.py
│   ├── base_command.py
│   ├── dispatcher.py
│   ├── echo_command.py
│   ├── get_command.py
│   ├── ping_command.py
│   └── set_command.py
├── parser/           # RESP protocol parser
│   ├── __init__.py
│   └── parser.py
├── store/            # Data storage
│   ├── __init__.py
│   └── store.py
├── connection.py     # Connection handler
└── main.py           # Server entry point

tests/               # Test files
├── commands/        # Command tests
└── parser/          # Parser tests
```

## Development Workflow

1. Make your changes
2. Run tests: `pytest`
3. Format code: `black . && isort .`
4. Check types: `mypy .`
5. Lint code: `flake8`
6. Commit changes with a descriptive message

## License

This project is part of the CodeCrafters Redis Challenge.
