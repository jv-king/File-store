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
FORCE_SUB_CHANNELS = os.environ.get("FORCE_SUB_CHANNELS", "-1002097394516,").split(",")   # Multiple force sub channels

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
logging.getLogger("pyrogram").setLevel(logging.WARNING)

# Initialize Pyrogram client
app = Client("my_bot", bot_token=TG_BOT_TOKEN, api_id=APP_ID, api_hash=API_HASH)

# Force Subscription Message
FORCE_MSG = os.environ.get("FORCE_SUB_MESSAGE", "Hello {first}\n\n<b>You need to join in Channels to use me\n\nKindly Please join the Channels</b>")

# Content for users
CONTENT = {
    "file": "path_to_your_file.txt",  # Replace with your file path or URL
    "message": "Here is your exclusive content! Enjoy."
}

# Start command
@app.on_message(filters.command("start"))
async def start(bot, message):
    user_id = message.chat.id
    first_name = message.from_user.first_name

    # Check if user is in all required channels
    if not await check_user_channels(user_id):
        # If not in all channels, send the force sub message with the buttons
        markup = InlineKeyboardMarkup(
            [[InlineKeyboardButton(text="Join Channel", url=f"https://t.me/{channel}") for channel in FORCE_SUB_CHANNELS]]
        )
        await message.reply(FORCE_MSG.format(first=first_name), reply_markup=markup)
    else:
        # If in all channels, proceed to give access
        await message.reply("You have joined all required channels! Here is the content you requested.")
        # Provide content here, you can choose between sending a file or a message
        await send_content(message.chat.id)

# Function to check if a user has joined all the force sub channels
async def check_user_channels(user_id):
    joined_channels = []
    for channel in FORCE_SUB_CHANNELS:
        try:
            chat_member = await app.get_chat_member(channel, user_id)
            if chat_member.status in ["member", "administrator"]:
                joined_channels.append(channel)
        except pyrogram.errors.FloodWait as e:
            logging.error(f"Flood wait error: {e}")
        except Exception as e:
            logging.error(f"Error checking channel membership: {e}")
    
    # Store the user's subscription status
    user_subscribed_channels[user_id] = len(joined_channels) == len(FORCE_SUB_CHANNELS)
    return user_subscribed_channels[user_id]

# Send content to the user (file or message)
async def send_content(user_id):
    if user_id in user_subscribed_channels and user_subscribed_channels[user_id]:
        # Send file or message based on what you want to provide
        if "file" in CONTENT:
            # Send file
            file_path = CONTENT["file"]
            await app.send_document(user_id, file_path)
        elif "message" in CONTENT:
            # Send message
            await app.send_message(user_id, CONTENT["message"])
    else:
        # If the user has not joined all channels, remind them to join
        await app.send_message(user_id, "You still haven't joined all required channels. Please join them and try again.")

# Handle "Try Again" button
@app.on_message(filters.text & filters.regex(r"Try Again"))
async def try_again(bot, message):
    user_id = message.chat.id
    first_name = message.from_user.first_name

    if await check_user_channels(user_id):
        # If the user is in all channels now, grant access
        await message.reply("You have joined all required channels! Here is the content you requested.")
        # Send content here (file or message)
        await send_content(user_id)
    else:
        # If still not in all channels, prompt to try again
        markup = InlineKeyboardMarkup(
            [[InlineKeyboardButton(text="Join Channel", url=f"https://t.me/{channel}") for channel in FORCE_SUB_CHANNELS]]
        )
        await message.reply(f"You still haven't joined all the channels, {first_name}. Please join them and try again.", reply_markup=markup)

# Start bot
if __name__ == "__main__":
    app.run()
