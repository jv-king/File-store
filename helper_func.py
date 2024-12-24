import base64
import re
import asyncio
from pyrogram import filters
from pyrogram.enums import ChatMemberStatus
from config import FORCE_SUB_CHANNELS, ADMINS, START_MSG


from pyrogram.errors.exceptions.bad_request_400 import UserNotParticipant
from pyrogram.errors import FloodWait

# Use START_MSG in your logic
async def start_command(client, message):
    await message.reply(START_MSG)


# Function to check if a user is subscribed
async def is_subscribed(filter, client, update):
    if not FORCE_SUB_CHANNELS:  # If no subscription channels are set, return True
        return True
    user_id = update.from_user.id
    if user_id in ADMINS:  # Allow admins to bypass subscription checks
        return True
    try:
        # Check membership in the subscription channel
        member = await client.get_chat_member(chat_id=FORCE_SUB_CHANNELS, user_id=user_id)
        if member.status in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.MEMBER]:
            return True
    except UserNotParticipant:
        return False
    except Exception as e:
        print(f"Error checking subscription: {e}")
        return False
    return False

# Base64 encoding function
async def encode(string):
    string_bytes = string.encode("ascii")
    base64_bytes = base64.urlsafe_b64encode(string_bytes)
    base64_string = (base64_bytes.decode("ascii")).strip("=")
    return base64_string

# Base64 decoding function
async def decode(base64_string):
    base64_string = base64_string.strip("=")  # Handle padding errors
    base64_bytes = (base64_string + "=" * (-len(base64_string) % 4)).encode("ascii")
    string_bytes = base64.urlsafe_b64decode(base64_bytes)
    string = string_bytes.decode("ascii")
    return string

# Fetch multiple messages
async def get_messages(client, message_ids):
    messages = []
    total_messages = 0
    while total_messages != len(message_ids):
        temp_ids = message_ids[total_messages:total_messages + 200]
        try:
            msgs = await client.get_messages(
                chat_id=client.db_channel.id,
                message_ids=temp_ids
            )
        except FloodWait as e:
            print(f"FloodWait: Waiting for {e.x} seconds.")
            await asyncio.sleep(e.x)
            continue
        except Exception as e:
            print(f"Error fetching messages: {e}")
            break
        total_messages += len(temp_ids)
        messages.extend(msgs)
    return messages

# Get a specific message ID
async def get_message_id(client, message):
    if message.forward_from_chat:
        if message.forward_from_chat.id == client.db_channel.id:
            return message.forward_from_message_id
        else:
            return 0
    elif message.forward_sender_name:
        return 0
    elif message.text:
        pattern = r"https://t.me/(?:c/)?(.*)/(\d+)"
        matches = re.match(pattern, message.text)
        if not matches:
            return 0
        channel_id = matches.group(1)
        msg_id = int(matches.group(2))
        if channel_id.isdigit():
            if f"-100{channel_id}" == str(client.db_channel.id):
                return msg_id
        else:
            if channel_id == client.db_channel.username:
                return msg_id
    return 0

# Readable time formatting
def get_readable_time(seconds: int) -> str:
    count = 0
    up_time = ""
    time_list = []
    time_suffix_list = ["s", "m", "h", "days"]
    while count < 4:
        count += 1
        remainder, result = divmod(seconds, 60) if count < 3 else divmod(seconds, 24)
        if seconds == 0 and remainder == 0:
            break
        time_list.append(int(result))
        seconds = int(remainder)
    time_list.reverse()
    for idx, val in enumerate(time_list):
        up_time += f"{val}{time_suffix_list[idx]} "
    return up_time.strip()

# Custom filter for subscription
subscribed = filters.create(is_subscribed)
