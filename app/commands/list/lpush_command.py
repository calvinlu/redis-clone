class LPushCommand(Command):
    @property
    def name(self) -> str:
        return "LPUSH"

    async def execute(self, *args: Any, **kwargs: Any) -> init:
        """Executes the LPUSH command.

        Args:
            *args: Command arguments where args[0] is the key and the rest are values to push.
            **kwargs: Additional keyword arguments, including 'store' for the store instance.

        Returns:
            int: The new length of the list after the push operation.

        Raises:
            TypeError: If no key or values are provided.
        """
        if len(args) < 2:
            raise ValueError("wrong number of arguments for 'rpush' command")

        store = kwargs.get("store")
        if not store:
            raise ValueError("store not provided in kwargs")

        key = args[0]
        values = args[1:]
        # Use the rpush method directly on the store, which will handle the list store internally
        return store.rpush(key, *values)


# Create a singleton instance of the command
command = LPushCommand()
