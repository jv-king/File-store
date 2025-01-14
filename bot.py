import logging
from aiohttp import web
from plugins import web_server
import pyromod.listen
from pyrogram import Client
from pyrogram.enums import ParseMode
import sys
from datetime import datetime
from config import (
    API_HASH,
    APP_ID,
    TG_BOT_TOKEN,
    TG_BOT_WORKERS,
    FORCE_SUB_CHANNELS,
    CHANNEL_ID,
    PORT
)

class Bot(Client):
    def __init__(self):
        # Initialize the Pyrogram Client
        super().__init__(
            name="Bot",
            api_hash=API_HASH,
            api_id=APP_ID,
            plugins={"root": "plugins"},
            workers=TG_BOT_WORKERS,
            bot_token=TG_BOT_TOKEN,
        )
        # Initialize the logger
        self.LOGGER = logging.getLogger(__name__)
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s"
        )

    async def start(self):
        await super().start()
        usr_bot_me = await self.get_me()
        self.uptime = datetime.now()
        self.LOGGER.info(f"Bot Started as @{usr_bot_me.username}")

        # Handle FORCE_SUB_CHANNELS
        if FORCE_SUB_CHANNELS:
            await self._handle_force_sub_channels()

        # Handle CHANNEL_ID
        await self._handle_db_channel()

        # Set parse mode for messages
        self.set_parse_mode(ParseMode.HTML)
        self.LOGGER.info("Bot Running..!\n\nCreated by https://t.me/CodeXBotz")
        self.LOGGER.info("""
░█████╗░░█████╗░██████╗░███████╗██╗░░██╗██████╗░░█████╗░████████╗███████╗
██╔══██╗██╔══██╗██╔══██╗██╔════╝╚██╗██╔╝██╔══██╗██╔══██╗╚══██╔══╝╚════██║
██║░░╚═╝██║░░██║██║░░██║█████╗░░░╚███╔╝░██████╦╝██║░░██║░░░██║░░░░░███╔═╝
██║░░██╗██║░░██║██║░░██║██╔══╝░░░██╔██╗░██╔══██╗██║░░██║░░░██║░░░██╔══╝░░
╚█████╔╝╚█████╔╝██████╔╝███████╗██╔╝╚██╗██████╦╝╚█████╔╝░░░██║░░░███████╗
░╚════╝░░╚════╝░╚═════╝░╚══════╝╚═╝░░╚═╝╚═════╝░░╚════╝░░░░╚═╝░░░╚══════╝
        """)

        # Start the web server
        app = web.AppRunner(await web_server())
        await app.setup()
        bind_address = "0.0.0.0"
        await web.TCPSite(app, bind_address, PORT).start()

    async def stop(self, *args):
        await super().stop()
        self.LOGGER.info("Bot stopped.")

    async def _handle_force_sub_channels(self):
        """
        Handles FORCE_SUB_CHANNELS for ensuring the bot is an admin 
        and processing group chats or channels.
        """
        if not isinstance(FORCE_SUB_CHANNELS, list):
            raise ValueError("FORCE_SUB_CHANNELS must be a list of channel/group IDs.")

        self.invitelinks = {}  # Dictionary to store invite links for channels

        for channel in FORCE_SUB_CHANNELS:
            try:
                chat = await self.get_chat(channel)

                if chat.type == "channel":
                    # Process channels by managing invite links
                    link = chat.invite_link
                    if not link:
                        await self.export_chat_invite_link(channel)
                        link = (await self.get_chat(channel)).invite_link
                    self.invitelinks[channel] = link
                    self.LOGGER.info(f"Processed channel '{chat.title}' with invite link: {link}")

                elif chat.type in ["supergroup", "group"]:
                    # Ensure the bot is present in groups
                    self.LOGGER.info(f"Processed group '{chat.title}': Bot is present.")
                else:
                    self.LOGGER.warning(f"Unsupported chat type for '{chat.title}': {chat.type}")

            except Exception as e:
                self.LOGGER.warning(f"Error processing chat {channel}: {e}")

    async def _handle_db_channel(self):
        """
        Ensures the bot can access the database channel and verify permissions.
        """
        try:
            db_channel = await self.get_chat(CHANNEL_ID)
            self.db_channel = db_channel
            test = await self.send_message(chat_id=db_channel.id, text="Test Message")
            await test.delete()
            self.LOGGER.info(f"Database channel '{db_channel.title}' is accessible.")
        except Exception as e:
            self.LOGGER.warning(f"Failed to access database channel ({CHANNEL_ID}): {e}")
            sys.exit()
