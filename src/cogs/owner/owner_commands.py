from framework import command
from framework.cog import Cog
from framework.permissions import is_owner


class OwnerCommands(Cog):
    def __init__(self, bot):
        super().__init__(bot)
        self.default_config['enabled'] = True
        self.configurable = False

    @is_owner()
    @command()
    async def kill(self, ctx):
        """
        Kills the bot. It'll boot back up in a pinch.
        """
        await ctx.send("Shutting down...")
        exit()
