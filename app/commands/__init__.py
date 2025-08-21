"""Package containing Redis command implementations and dispatcher.

This package contains modules that implement various Redis commands. Each command is
implemented as a class that inherits from the base Command class and implements
the execute method.

Key Components:
    - Command: Base class for all Redis commands
    - CommandDispatcher: Handles command registration and execution
"""

# Import the base classes and dispatcher directly
from .base_command import Command
from .dispatcher import CommandDispatcher

# Individual command imports will be handled by the modules that need them
from .list.blpop_command import command as blpop_command
from .list.lpop_command import command as lpop_command
from .list.lpush_command import command as lpush_command
from .list.lrange_command import command as lrange_command
from .list.rpush_command import command as rpush_command

# This avoids circular imports while keeping the interface clean

# Command registry
COMMANDS = {
    "blpop": blpop_command,
    "lpop": lpop_command,
    "rpush": rpush_command,
}

__all__ = [
    "Command",
    "CommandDispatcher",
    "COMMANDS",
]
