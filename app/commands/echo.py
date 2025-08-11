COMMAND = 'echo'


async def handle_command(message: str) -> str:
    """Handle ECHO command by returning the input message.
    
    Args:
        message: The message to echo back
        
    Returns:
        The same message that was received
    """
    return message
