import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Load ADMIN_IDS, splitting by comma and converting to int.
# Example: "123,456" -> [123, 456]
ADMIN_IDS_STR = os.getenv("ADMIN_IDS", "")
ADMIN_IDS = [int(admin_id.strip()) for admin_id in ADMIN_IDS_STR.split(',') if admin_id.strip()]

# Database file path
DB_FILE = "storage/bot_database.db"

# Exchange Rate (default, can be changed by admin)
# This is just an initial value. It will be stored and retrieved from the database.
DEFAULT_EXCHANGE_RATE = 120.0  # 1 USD = 120 BDT

# Bot status (default, can be changed by admin)
DEFAULT_BOT_STATUS = "on"
