import os
import logging
from logging.handlers import RotatingFileHandler
import pyrogram
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Bot token @Botfather
TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN", "8122813255:AAFNwBSTPSyD4ylnEy6Ia6mE8OTf7hbtoxU")

# Your API ID and Hash from my.telegram.org
APP_ID = int(os.environ.get("APP_ID", "25026077"))
API_HASH = os.environ.get("API_HASH", "1868dea7a187d9060a3c57be6a0f4182")

# Channel and other configurations
CHANNEL_ID = int(os.environ.get("CHANNEL_ID", "-1002433338956"))
FORCE_SUB_CHANNELS = os.environ.get("FORCE_SUB_CHANNELS", "-1002097394516,-1002271867183,-1002325985046 ").split(",")   # Multiple force sub channels

DB_URI = os.environ.get("DATABASE_URL", "mongodb+srv://Soulreapers: jayvardhan@@@reapers.hvxag.mongodb.net/?retryWrites=true&w=majority&appName=Reapers")
DB_NAME = os.environ.get("DATABASE_NAME", "Reapers")

TG_BOT_WORKERS = int(os.environ.get("TG_BOT_WORKERS", 10))

PORT = int(os.environ.get("PORT", 8080))  # Default to port 8080 if not provided

# Database or in-memory structure to store user subscription status
user_subscribed_channels = {}

# Logger setup
LOG_FILE_NAME = "filesharingbot.txt"
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s - %(levelname)s] - %(name)s - %(message)s",
    datefmt='%d-%b-%y %H:%S',
    handlers=[
        RotatingFileHandler(LOG_FILE_NAME, maxBytes=50000000, backupCount=10),
        logging.StreamHandler()
    ]
)

LOGGER = logging.getLogger("FileSharingBot")

logging.getLogger("pyrogram").setLevel(logging.WARNING)

# Initialize Pyrogram client
app = Client("my_bot", bot_token=TG_BOT_TOKEN, api_id=APP_ID, api_hash=API_HASH)

# Force Subscription Message
FORCE_MSG = os.environ.get("FORCE_SUB_MESSAGE", "Hello {first}\n\n<b>You need to join in Channels to use me\n\nKindly Please join the Channels</b>")

# Fetch invite links for FORCE_SUB_CHANNELS
async def get_invite_links():
    invite_links = {}
    for channel_id in FORCE_SUB_CHANNELS:
        try:
            chat = await app.get_chat(channel_id)
            if chat.invite_link:
                # Use existing invite link if available
                invite_links[channel_id] = chat.invite_link
            else:
                # Generate a new invite link
                invite_links[channel_id] = (await app.create_chat_invite_link(channel_id)).invite_link
        except pyrogram.errors.ChatAdminRequired:
            LOGGER.error(f"Bot must be an admin in the channel {channel_id} to fetch or generate invite links.")
            invite_links[channel_id] = None
        except Exception as e:
            LOGGER.error(f"Error fetching invite link for channel {channel_id}: {e}")
            invite_links[channel_id] = None
    return invite_links

# Start command
@app.on_message(filters.command("start"))
async def start(bot, message):
    user_id = message.chat.id
    first_name = message.from_user.first_name

    if not await check_user_channels(user_id):
        invite_links = await get_invite_links()

        # Create buttons with invite links
        buttons = [
            [InlineKeyboardButton("Join Channel", url=invite_links[channel_id])]
            for channel_id in FORCE_SUB_CHANNELS if invite_links.get(channel_id)
        ]

        markup = InlineKeyboardMarkup(buttons)

        await message.reply(
            FORCE_MSG.format(first=first_name),
            reply_markup=markup
        )
    else:
        await message.reply("You have joined all required channels! You can now use the bot.")

# Function to check if a user has joined all the force sub channels
async def check_user_channels(user_id):
    for channel_id in FORCE_SUB_CHANNELS:
        try:
            # Check if the user is a member of the channel
            chat_member = await app.get_chat_member(channel_id, user_id)
            if chat_member.status not in ["member", "administrator"]:
                return False
        except pyrogram.errors.ChatAdminRequired:
            LOGGER.error(f"Bot must be an admin in channel {channel_id}.")
        except pyrogram.errors.UserNotParticipant:
            return False
        except Exception as e:
            LOGGER.error(f"Error checking subscription status for user {user_id} in channel {channel_id}: {e}")
            return False
    return True


    # Store the user's subscription status
    user_subscribed_channels[user_id] = len(joined_channels) == len(FORCE_SUB_CHANNELS)
    return user_subscribed_channels[user_id]

# Handle "Try Again" button
@app.on_message(filters.text & filters.regex(r"Try Again"))
async def try_again(bot, message):
    user_id = message.chat.id
    first_name = message.from_user.first_name

    if await check_user_channels(user_id):
        # If the user is in all channels now, grant access
        await message.reply("You have joined all required channels! You can now use the bot.")
    else:
        # If still not in all channels, prompt to try again
        markup = InlineKeyboardMarkup(
            [[InlineKeyboardButton(text="Join Channel", url=f"https://t.me/{channel}") for channel in FORCE_SUB_CHANNELS]]
        )
        await message.reply(f"You still haven't joined all the channels, {first_name}. Please join them and try again.", reply_markup=markup)

# Start bot
if __name__ == "__main__":
    app.run()