import asyncio
import os
from datetime import datetime, timedelta

import discord

from cogs.tadhkirah.tadhkeer_backend import TadhkeerBackend
from framework import group
from framework.cog import Cog
from framework.permissions import perms, is_owner
from model.file import YamlFile
from statics import storageDir


# TODO: command to list all availabe categories
class TadhkeerCommands(Cog):
    data_file_name = 'tadhkeer.yaml'

    def __init__(self, bot):
        super().__init__(bot)
        self.backend = TadhkeerBackend(bot.loop)

        self.default_config['enabled'] = True
        self.default_config['channel_id'] = None
        self.default_config['interval_in_seconds'] = 86400
        self.bot.loop.create_task(self.remind())

    @group(aliases=['reminder'], invoke_without_command=True)
    async def tadhkirah(self, ctx, category = None):
        """
        Get a random reminder, optionally from a specific category

        To configure the bot to post reminders in a certain channel,
        run `tadhkirah channel #channel-mention` and you're set!

        By default, the bot will post there every 24 hours. You
        can change that with the `tadhkirah interval` command.
        """
        if ctx.invoked_subcommand is not None:
            return

        await self.post_tadhkirah_in(ctx.channel, category)

    @tadhkirah.command()
    async def id(self, ctx, n: int):
        """
        Get a reminder by its row number in the sheet
        """
        await ctx.send(embed=await self.backend.get_by_id(n))

    @perms(kick_members=True)
    @tadhkirah.command()
    async def channel(self, ctx, channel: discord.TextChannel = None):
        """
        Get or set the channel to post reminders in
        """
        if channel is None:
            channel_id = ctx.cog_config['channel_id']
            if channel_id is None:
                await ctx.send("I'm not posting reminders anywhere. You should set a channel!")
            else:
                channel = ctx.guild.get_channel(channel_id)
                await ctx.send("I'm posting reminders in {}.".format(channel.mention))
        else:
            ctx.cog_config['channel_id'] = channel.id
            self.bot.configs.save(ctx.guild.id)
            await ctx.send("Alright, I'll be posting reminders in {}.".format(channel.mention))

    @perms(kick_members=True)
    @tadhkirah.command()
    async def interval(self, ctx, interval_in_hours: float = None):
        """
        Get or set how often the bot posts in the configured channel.

        The minimum value for this is 0.25. That is, 15 minutes.
        If you try to set a value lower than that, it'll work, but the bot won't post
        more often than that.

        Defaults to 24 hours.
        """
        if interval_in_hours is None:
            interval_in_hours = ctx.cog_config['interval_in_seconds'] / (60 * 60)
            await ctx.send("I'm posting reminders every {} hour(s).".format(interval_in_hours))
        else:
            ctx.cog_config['interval_in_seconds'] = interval_in_hours * 60 * 60
            self.bot.configs.save(ctx.guild.id)
            await ctx.send("Alright, I'll be posting reminders every {} hour(s).".format(interval_in_hours))

    @is_owner()
    @tadhkirah.command()
    async def refresh(self):
        """Refresh sheet data"""
        await self.backend.refresh()

    async def post_tadhkirah_in(self, channel, category = None):
        if category is None:
            embed = await self.backend.get_random()
        else:
            embed = await self.backend.get_from_category(category)

        await channel.send(embed=embed)

    async def remind(self):
        await self.bot.wait_until_ready()
        while True:
            for guild in self.bot.guilds:
                conf = self.config_for(guild.id)
                if not conf.enabled or conf.channel_id is None:
                    continue

                data_file = YamlFile(os.path.join(storageDir, str(guild.id), self.data_file_name))
                if data_file.read() == {}:
                    data_file.write({'last_tadhkirah_timestamp': 0})

                last_tadhkirah_timestamp = datetime.fromtimestamp(data_file.read().last_tadhkirah_timestamp)

                if datetime.now() - last_tadhkirah_timestamp > timedelta(seconds=conf.interval_in_seconds):
                    await self.post_tadhkirah_in(guild.get_channel(conf.channel_id))
                    data_file.write({'last_tadhkirah_timestamp': datetime.now().timestamp()})

            await asyncio.sleep(900)
