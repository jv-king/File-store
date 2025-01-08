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
        logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    
    async def start(self):
        await super().start()
        usr_bot_me = await self.get_me()
        self.uptime = datetime.now()
        self.LOGGER.info(f"Bot Started as @{usr_bot_me.username}")

        # Handle FORCE_SUB_CHANNELS
if FORCE_SUB_CHANNELS:
    try:
        if isinstance(FORCE_SUB_CHANNELS, list):
            for channel in FORCE_SUB_CHANNELS:
                link = (await self.get_chat(channel)).invite_link
                if not link:
                    await self.export_chat_invite_link(channel)
                    link = (await self.get_chat(channel)).invite_link
                self.invitelink = link  # Save the last valid invite link
        else:
            # If it's a single string or ID, handle it directly
            link = (await self.get_chat(FORCE_SUB_CHANNELS)).invite_link
            if not link:
                await self.export_chat_invite_link(FORCE_SUB_CHANNELS)
                link = (await self.get_chat(FORCE_SUB_CHANNELS)).invite_link
            self.invitelink = link
    except Exception as e:
        self.LOGGER.warning(f"Error handling FORCE_SUB_CHANNELS: {e}")
        self.LOGGER.warning(
            f"Please double-check the FORCE_SUB_CHANNELS value and ensure the bot is an admin in the channel "
            f"with 'Invite Users via Link' permission. Current FORCE_SUB_CHANNELS value: {FORCE_SUB_CHANNELS}"
        )
        sys.exit()


        # Handle CHANNEL_ID
        try:
            db_channel = await self.get_chat(CHANNEL_ID)
            self.db_channel = db_channel
            test = await self.send_message(chat_id=db_channel.id, text="Test Message")
            await test.delete()
        except Exception as e:
            self.LOGGER.warning(f"Failed to access database channel ({CHANNEL_ID}): {e}")
            sys.exit()

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
