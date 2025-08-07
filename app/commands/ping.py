COMMAND = 'ping'

RESPONSE = b'+PONG\r\n'

async def handle_command() -> bytes:
    return RESPONSE
