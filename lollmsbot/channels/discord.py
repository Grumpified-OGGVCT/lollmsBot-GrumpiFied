import asyncio
import logging
from typing import Optional, Any

import discord
from discord.ext import commands
import httpx

logger = logging.getLogger(__name__)

class DiscordChannel:
    """Discord bot channel that forwards messages to lollmsBot gateway."""

    def __init__(
        self,
        bot_token: Optional[str] = None,
        gateway_url: str = "http://localhost:8800",
        command_prefix: str = "!",
    ):
        self.bot_token = bot_token
        self.gateway_url = gateway_url
        self.client = httpx.AsyncClient(timeout=30.0)
        self._is_running = False
        self._ready_event = asyncio.Event()
        self.command_prefix = command_prefix
        
        # Discord intents - ALL required for proper message handling
        self.intents = discord.Intents.default()
        self.intents.message_content = True
        self.intents.guilds = True
        self.intents.guild_messages = True
        self.intents.dm_messages = True
        
        # Use discord.Client instead of commands.Bot to avoid command framework conflicts
        self.bot = discord.Client(intents=self.intents)

        @self.bot.event
        async def on_ready():
            self._is_running = True
            self._ready_event.set()
            logger.info(f"🤖 Discord bot '{self.bot.user}' ({self.bot.user.id}) connected!")
            logger.info(f"   Guilds: {len(self.bot.guilds)} servers")
            for guild in self.bot.guilds:
                logger.info(f"   - {guild.name} (ID: {guild.id})")
                # Log channel permissions
                for channel in guild.text_channels[:3]:  # Log first 3 channels
                    perms = channel.permissions_for(guild.me)
                    logger.info(f"     #{channel.name}: read_messages={perms.read_messages}, send_messages={perms.send_messages}")
            print(f"🤖 Discord bot '{self.bot.user}' ready!")

        @self.bot.event
        async def on_message(message: discord.Message):
            # CRITICAL: Log ALL messages to see if event fires
            logger.info(f"RAW MESSAGE from {message.author} in #{getattr(message.channel, 'name', 'DM')}: '{message.content[:100]}'")
            logger.info(f"  Message type: {message.type}, System: {message.is_system()}")
            logger.info(f"  Author bot? {message.author.bot}, Self? {message.author == self.bot.user}")
            logger.info(f"  Guild? {message.guild is not None}")
            
            # Ignore own messages
            if message.author == self.bot.user:
                logger.debug("  -> Ignoring: own message")
                return
            
            # Ignore other bots
            if message.author.bot:
                logger.debug("  -> Ignoring: other bot")
                return
            
            # Check if bot is mentioned in any form
            is_mentioned = False
            content_mentions_bot = False
            
            if self.bot.user:
                # Check mentions list
                is_mentioned = self.bot.user in message.mentions
                logger.info(f"  In mentions list: {is_mentioned}")
                
                # Check content for mention patterns
                mention_patterns = [
                    f"<@{self.bot.user.id}>",
                    f"<@!{self.bot.user.id}>",
                ]
                for pattern in mention_patterns:
                    if pattern in message.content:
                        content_mentions_bot = True
                        logger.info(f"  Found mention pattern: {pattern}")
                        break
                
                # Also check if message starts with @botname (though Discord converts this)
                if message.content.startswith(f"@{self.bot.user.name}"):
                    content_mentions_bot = True
                    logger.info(f"  Found @username mention")
            
            # Check for command prefix
            is_command = message.content.startswith(self.command_prefix + "ask")
            logger.info(f"  is_mentioned={is_mentioned}, content_mentions_bot={content_mentions_bot}, is_command={is_command}")
            
            # Must be mentioned OR use command
            if not is_mentioned and not content_mentions_bot and not is_command:
                logger.debug("  -> Ignoring: not mentioned and not command")
                return
            
            # Security: Don't respond to DMs unless explicitly enabled
            if not message.guild:
                logger.info(f"DM from {message.author}: {message.content[:50]}...")
            # Enable DMs - process normally

            logger.info(f"PROCESSING message from {message.author} in #{message.channel}: {message.content[:80]}...")
            
            # Clean message content - remove bot mentions for cleaner processing
            clean_content = message.content
            if self.bot.user:
                # Remove all mention patterns
                mention_patterns = [
                    f"<@{self.bot.user.id}>",
                    f"<@!{self.bot.user.id}>",
                    f"@{self.bot.user.name}",
                ]
                if self.bot.user.discriminator != "0":
                    mention_patterns.append(f"@{self.bot.user.name}#{self.bot.user.discriminator}")
                
                for pattern in mention_patterns:
                    clean_content = clean_content.replace(pattern, "")
                
                clean_content = clean_content.strip()
                logger.info(f"  Cleaned content: '{clean_content[:80]}'")

            # Show typing indicator while processing
            async with message.channel.typing():
                try:
                    payload = {"message": clean_content if clean_content else message.content}
                    logger.info(f"  POST to {self.gateway_url}/chat: {payload}")
                    
                    resp = await self.client.post(
                        f"{self.gateway_url}/chat",
                        json=payload,
                        headers={"Content-Type": "application/json"},
                    )
                    
                    logger.info(f"  Gateway response: {resp.status_code}")
                    
                    if resp.status_code == 200:
                        reply = resp.json().get("reply", "No response")[:1900]  # Discord limit
                        logger.info(f"  Reply: {reply[:80]}...")
                        await message.reply(f"```{reply}```")
                        logger.info(f"  -> Reply sent successfully")
                    else:
                        error_msg = f"Gateway error: HTTP {resp.status_code}"
                        logger.error(f"  {error_msg}")
                        await message.reply(f"❌ {error_msg}")
                        
                except httpx.RequestError as e:
                    error_msg = f"Network error connecting to gateway: {e}"
                    logger.error(f"  {error_msg}")
                    await message.reply(f"🌐 {error_msg}")
                except Exception as e:
                    error_msg = f"Unexpected error: {e}"
                    logger.error(f"  {error_msg}", exc_info=True)
                    await message.reply(f"🚨 {error_msg}")

    async def start(self):
        """Start Discord bot."""
        if not self.bot_token:
            raise ValueError("Discord bot token is required to start the channel")
        
        logger.info(f"Starting Discord bot (connecting to gateway at {self.gateway_url})...")
        # Set logging to INFO to see all messages
        logging.getLogger('discord').setLevel(logging.INFO)
        await self.bot.start(self.bot_token)

    async def stop(self):
        """Graceful shutdown."""
        self._is_running = False
        await self.client.aclose()
        await self.bot.close()
        logger.info("Discord bot stopped")

    @property
    def is_running(self) -> bool:
        """Check if the bot is running and ready."""
        return self._is_running and self._ready_event.is_set()

    async def wait_for_ready(self, timeout: float = 30.0) -> bool:
        """Wait for the bot to become ready.
        
        Args:
            timeout: Maximum time to wait in seconds.
            
        Returns:
            True if ready, False if timeout.
        """
        try:
            await asyncio.wait_for(self._ready_event.wait(), timeout=timeout)
            return True
        except asyncio.TimeoutError:
            return False

    def __repr__(self) -> str:
        status = "ready" if self.is_running else "connecting" if self._is_running else "stopped"
        return f"DiscordChannel({status}, guilds={len(self.bot.guilds) if self.bot.user else 'N/A'})"
