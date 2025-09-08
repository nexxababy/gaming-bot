import logging  
import os
from pyrogram import Client 
from telegram.ext import Application
from motor.motor_asyncio import AsyncIOMotorClient

# Logging
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    handlers=[logging.FileHandler("log.txt"), logging.StreamHandler()],
    level=logging.INFO,
)

from shivu.modules import ALL_MODULES
from shivu.config import Development as Config

logging.getLogger("apscheduler").setLevel(logging.ERROR)
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger("pyrate_limiter").setLevel(logging.ERROR)
LOGGER = logging.getLogger(__name__)

# Config
api_id = Config.api_id
api_hash = Config.api_hash
TOKEN = Config.TOKEN
GROUP_ID = Config.GROUP_ID
CHARA_CHANNEL_ID = Config.CHARA_CHANNEL_ID 
mongo_url = Config.mongo_url 
PHOTO_URL = Config.PHOTO_URL 
SUPPORT_CHAT = Config.SUPPORT_CHAT 
UPDATE_CHAT = Config.UPDATE_CHAT
BOT_USERNAME = Config.BOT_USERNAME 
sudo_users = Config.sudo_users
OWNER_ID = Config.OWNER_ID 

# Telegram bots
application = Application.builder().token(TOKEN).build()
shivuu = Client("Shivu", api_id, api_hash, bot_token=TOKEN)

# MongoDB Setup
lol = AsyncIOMotorClient(mongo_url)
db = lol['Waifu_Chan_bot']

#mongo db sotred database details change as your wishe 
collection = db['anime_characters_lol']
user_totals_collection = db['user_totals_lmaoooo']
user_collection = db["user_collection_lmaoooo"]
group_user_totals_collection = db['group_user_totalsssssss']
top_global_groups_collection = db['top_global_groups']
pm_users = db['total_pm_users']
safari_users_collection = db['safari_users']
safari_cooldown_collection = db['safari_cooldown']
redeem_collection = db["redeem_codes"]
gift_collection = db["gift_transction"]
auction_collection = db["auction_collection"]
all_characters_cache = {}
user_collection_cache = {}
power_users_db = db["power_users"]
protection_collection = db["protection_status"]
locks_collection = db["locks_collection"]
