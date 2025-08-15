import logging
import json
import os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
BOT_TOKEN = "8476995132:AAFmh4jFkBvyHV7eCL5aMpLWgOd3M1VftOw"
ADMIN_USER_IDS = ["6058266328"]  # Your admin user ID (as string for compatibility)

# States for conversations
ADD_COUNTRY_CODE, ADD_NUMBERS = range(2)

# Data storage files
DATA_FILE = "data.json"
USERS_FILE = "users.json"
LOGS_FILE = "logs.json"
BANNED_FILE = "banned.json"
WELCOME_FILE = "welcome.txt"
STATUS_FILE = "status.json"
USED_NUMBERS_FILE = "used_numbers.json"

# Initialize data files if they don't exist
def initialize_files():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w") as f:
            json.dump({}, f)
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w") as f:
            json.dump({}, f)
    if not os.path.exists(LOGS_FILE):
        with open(LOGS_FILE, "w") as f:
            json.dump([], f)
    if not os.path.exists(BANNED_FILE):
        with open(BANNED_FILE, "w") as f:
            json.dump([], f)
    if not os.path.exists(WELCOME_FILE):
        with open(WELCOME_FILE, "w") as f:
            f.write("🌍 Welcome! Please select a country to get a number:")
    if not os.path.exists(STATUS_FILE):
        with open(STATUS_FILE, "w") as f:
            json.dump({"status": "running"}, f)
    if not os.path.exists(USED_NUMBERS_FILE):
        with open(USED_NUMBERS_FILE, "w") as f:
            json.dump([], f)

initialize_files()

# Load data from files
def load_data():
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, separators=(',', ':'))

def load_users():
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, separators=(',', ':'))

def load_logs():
    with open(LOGS_FILE, "r") as f:
        return json.load(f)

def save_logs(logs):
    with open(LOGS_FILE, "w") as f:
        json.dump(logs, f, separators=(',', ':'))

def load_banned():
    with open(BANNED_FILE, "r") as f:
        return json.load(f)

def save_banned(banned):
    with open(BANNED_FILE, "w") as f:
        json.dump(banned, f, separators=(',', ':'))

def load_welcome():
    with open(WELCOME_FILE, "r") as f:
        return f.read().strip()

def save_welcome(message):
    with open(WELCOME_FILE, "w") as f:
        f.write(message)

def load_status():
    with open(STATUS_FILE, "r") as f:
        return json.load(f)

def save_status(status):
    with open(STATUS_FILE, "w") as f:
        json.dump({"status": status}, f, separators=(',', ':'))

def load_used_numbers():
    with open(USED_NUMBERS_FILE, "r") as f:
        return json.load(f)

def save_used_numbers(used_numbers):
    with open(USED_NUMBERS_FILE, "w") as f:
        json.dump(used_numbers, f, separators=(',', ':'))

# Country flags mapping (extended for more countries)
COUNTRY_FLAGS = {
    "BD": "🇧🇩", "IN": "🇮🇳", "US": "🇺🇸", "GB": "🇬🇧", "CA": "🇨🇦",
    "AU": "🇦🇺", "DE": "🇩🇪", "FR": "🇫🇷", "JP": "🇯🇵", "KR": "🇰🇷",
    "CN": "🇨🇳", "RU": "🇷🇺", "BR": "🇧🇷", "MX": "🇲🇽", "ES": "🇪🇸",
    "IT": "🇮🇹", "NL": "🇳🇱", "SE": "🇸🇪", "NO": "🇳🇴", "DK": "🇩🇰",
    "FI": "🇫🇮", "PL": "🇵🇱", "TR": "🇹🇷", "SA": "🇸🇦", "AE": "🇦🇪",
    "EG": "🇪🇬", "NG": "🇳🇬", "ZA": "🇿🇦", "KE": "🇰🇪", "MA": "🇲🇦",
    "PK": "🇵🇰", "LK": "🇱🇰", "NP": "🇳🇵", "VN": "🇻🇳", "TH": "🇹🇭",
    "ID": "🇮🇩", "MY": "🇲🇾", "SG": "🇸🇬", "PH": "🇵🇭", "MM": "🇲🇲",
    "IL": "🇮🇱", "IR": "🇮🇷", "IQ": "🇮🇶", "JO": "🇯🇴", "LB": "🇱🇧",
    "AR": "🇦🇷", "CL": "🇨🇱", "PE": "🇵🇪", "CO": "🇨🇴", "VE": "🇻🇪",
    "UY": "🇺🇾", "PY": "🇵🇾", "BO": "🇧🇴", "EC": "🇪🇨", "CR": "🇨🇷",
    "PA": "🇵🇦", "GT": "🇬🇹", "HN": "🇭🇳", "SV": "🇸🇻", "NI": "🇳🇮",
    "CU": "🇨🇺", "DO": "🇩🇴", "HT": "🇭🇹", "JM": "🇯🇲", "PR": "🇵🇷"
}

# Pagination settings
COUNTRIES_PER_PAGE = 30 # 15 rows of 2 buttons

# Helper functions
def create_country_keyboard(countries, page=0):
    """Create a paginated inline keyboard for country selection."""
    start_offset = page * COUNTRIES_PER_PAGE
    end_offset = start_offset + COUNTRIES_PER_PAGE

    paginated_countries = sorted(countries)[start_offset:end_offset] # Sort for consistent order

    keyboard = []
    row = []
    for i, country in enumerate(paginated_countries):
        flag = get_country_flag(country)
        button = InlineKeyboardButton(f"{flag} {country}", callback_data=f"select_{country}")
        row.append(button)
        if (i + 1) % 2 == 0:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    # Pagination controls
    nav_row = []
    total_pages = (len(countries) + COUNTRIES_PER_PAGE - 1) // COUNTRIES_PER_PAGE

    if page > 0:
        nav_row.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"page_{page-1}"))

    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton("Next ➡️", callback_data=f"page_{page+1}"))

    if nav_row:
        keyboard.append(nav_row)

    return InlineKeyboardMarkup(keyboard)

def get_country_flag(country_code):
    return COUNTRY_FLAGS.get(country_code.upper(), "🏳️")

def get_available_countries():
    data = load_data()
    return list(data.keys())

def get_numbers_for_country(country_code):
    data = load_data()
    return data.get(country_code.upper(), [])

def add_numbers(country_code, numbers):
    data = load_data()
    country_code = country_code.upper()
    if country_code not in data:
        data[country_code] = []
    data[country_code].extend(numbers)
    save_data(data)

def remove_number(country_code, number):
    data = load_data()
    country_code = country_code.upper()
    if country_code in data and number in data[country_code]:
        data[country_code].remove(number)
        if not data[country_code]:
            del data[country_code]
        save_data(data)
        return True
    return False

def remove_all_numbers_for_country(country_code):
    """Remove all numbers for a specific country"""
    data = load_data()
    country_code = country_code.upper()
    if country_code in data:
        del data[country_code]
        save_data(data)
        return True
    return False

def assign_number_to_user(user_id, country_code, number):
    """Assign a number to a user and remove it from pool"""
    users = load_users()
    user_id_str = str(user_id)
    users.setdefault(user_id_str, {
        "current_number": None,
        "current_country": None,
        "history": [],
        "assigned_at": None
    })

    # Add previous number to history if exists
    if users[user_id_str]["current_number"]:
        users[user_id_str]["history"].append({
            "number": users[user_id_str]["current_number"],
            "country": users[user_id_str]["current_country"],
            "assigned_at": users[user_id_str]["assigned_at"],
            "released_at": datetime.now().isoformat()
        })

    # Assign new number
    users[user_id_str]["current_number"] = number
    users[user_id_str]["current_country"] = country_code
    users[user_id_str]["assigned_at"] = datetime.now().isoformat()

    save_users(users)

    # Remove number from pool
    remove_number(country_code, number)

    return True

def get_user_current_number(user_id):
    users = load_users()
    user_data = users.get(str(user_id), {})
    return user_data.get("current_number"), user_data.get("current_country")

def get_user_history(user_id):
    users = load_users()
    user_data = users.get(str(user_id), {})
    return user_data.get("history", [])

def get_user_name(user_id, update=None):
    """Get user name from update or return user ID"""
    if update and update.effective_user:
        user = update.effective_user
        if user.username:
            return f"@{user.username}"
        elif user.first_name:
            return user.first_name
        else:
            return str(user_id)
    return str(user_id)

def log_usage(user_id, country_code, number, update=None):
    logs = load_logs()
    used_numbers = load_used_numbers()

    timestamp = datetime.now().isoformat()
    user_name = get_user_name(user_id, update)

    # Log to general logs
    logs.append({
        "user_id": str(user_id),
        "user_name": user_name,
        "country_code": country_code.upper(),
        "number": number,
        "timestamp": timestamp
    })
    save_logs(logs)

    # Log to used numbers
    used_numbers.append({
        "user_id": str(user_id),
        "user_name": user_name,
        "country_code": country_code.upper(),
        "number": number,
        "timestamp": timestamp
    })
    save_used_numbers(used_numbers)

def is_user_banned(user_id):
    banned = load_banned()
    return str(user_id) in banned

def ban_user(user_id):
    banned = load_banned()
    user_id_str = str(user_id)
    if user_id_str not in banned:
        banned.append(user_id_str)
        save_banned(banned)
        return True
    return False

def unban_user(user_id):
    banned = load_banned()
    user_id_str = str(user_id)
    if user_id_str in banned:
        banned.remove(user_id_str)
        save_banned(banned)
        return True
    return False

def get_bot_statistics():
    data = load_data()
    users = load_users()
    logs = load_logs()

    total_numbers = sum(len(numbers) for numbers in data.values())
    total_countries = len(data)
    total_users = len(users)
    total_assigned = len(logs)

    return {
        "total_users": total_users,
        "total_assigned": total_assigned,
        "total_numbers": total_numbers,
        "total_countries": total_countries
    }

def is_bot_running():
    status = load_status()
    return status.get("status") == "running"

def reset_statistics():
    """Reset all statistics"""
    # Clear logs
    with open(LOGS_FILE, "w") as f:
        json.dump([], f)

    # Clear used numbers
    with open(USED_NUMBERS_FILE, "w") as f:
        json.dump([], f)

    # Reset user history (but keep user records)
    users = load_users()
    for user_id in users:
        users[user_id]["history"] = []
        users[user_id]["current_number"] = None
        users[user_id]["current_country"] = None
        users[user_id]["assigned_at"] = None
    save_users(users)

# Bot handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user_id = update.effective_user.id

    # Check if user is banned
    if is_user_banned(user_id):
        await update.message.reply_text("❌ You have been banned from using this bot.")
        return

    # Check if bot is running
    if not is_bot_running():
        await update.message.reply_text("🔴 BOT IS ON MAINTENANCE")
        return

    welcome_message = load_welcome()
    countries = get_available_countries()

    if not countries:
        await update.message.reply_text("❌ No countries available. Please contact admin.")
        return

    reply_markup = create_country_keyboard(countries, page=0)
    await update.message.reply_text(f"{welcome_message}\n\n📲 Tap a country below to get a number:", reply_markup=reply_markup)

async def country_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle country selection"""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id

    # Check if user is banned
    if is_user_banned(user_id):
        await query.edit_message_text("❌ You have been banned from using this bot.")
        return

    # Check if bot is running
    if not is_bot_running():
        await query.edit_message_text("🔴 BOT IS ON MAINTENANCE")
        return

    country_code = query.data.split("_")[1]
    numbers = get_numbers_for_country(country_code)

    if not numbers:
        await query.edit_message_text("❌ No numbers available for this country. Please select another country.")
        return

    number = numbers[0]  # Use the first available number

    # Assign number to user and remove from pool
    assign_number_to_user(user_id, country_code, number)
    log_usage(user_id, country_code, number, update)

    # Send the number to the user
    flag = get_country_flag(country_code)
    message = f"📱 Your assigned number is:\n\n`{number}`\n\n{flag} {country_code}\n\n🔄 Tap 'Change' to get a different number."
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Change", callback_data="change")]])
    await query.edit_message_text(message, parse_mode="Markdown", reply_markup=reply_markup)

async def change_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle 'Change' button - Show country selection again"""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id

    # Check if user is banned
    if is_user_banned(user_id):
        await query.edit_message_text("❌ You have been banned from using this bot.")
        return

    # Check if bot is running
    if not is_bot_running():
        await query.edit_message_text("🔴 BOT IS ON MAINTENANCE")
        return

    countries = get_available_countries()

    if not countries:
        await query.edit_message_text("❌ No countries available. Please contact admin.")
        return

    reply_markup = create_country_keyboard(countries, page=0)
    await query.edit_message_text("🌍 Select a new country to get a number:", reply_markup=reply_markup)

async def page_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle pagination for country list."""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id

    # Check if user is banned
    if is_user_banned(user_id):
        await query.edit_message_text("❌ You have been banned from using this bot.")
        return

    # Check if bot is running
    if not is_bot_running():
        await query.edit_message_text("🔴 BOT IS ON MAINTENANCE")
        return

    page = int(query.data.split("_")[1])

    countries = get_available_countries()
    reply_markup = create_country_keyboard(countries, page=page)

    await query.edit_message_text("🌍 Select a new country to get a number:", reply_markup=reply_markup)

async def mynumber(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /mynumber command"""
    user_id = update.effective_user.id

    # Check if user is banned
    if is_user_banned(user_id):
        await update.message.reply_text("❌ You have been banned from using this bot.")
        return

    # Check if bot is running
    if not is_bot_running():
        await update.message.reply_text("🔴 BOT IS ON MAINTENANCE")
        return

    current_number, country_code = get_user_current_number(user_id)

    if not current_number:
        await update.message.reply_text("📱 You don't have an assigned number yet. Use /start to get one.")
        return

    flag = get_country_flag(country_code)
    message = f"📱 Your current assigned number is:\n\n`{current_number}`\n\n{flag} {country_code}\n\nIf you want a new number, type /change"
    await update.message.reply_text(message, parse_mode="Markdown")

async def history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /history command"""
    user_id = update.effective_user.id

    # Check if user is banned
    if is_user_banned(user_id):
        await update.message.reply_text("❌ You have been banned from using this bot.")
        return

    # Check if bot is running
    if not is_bot_running():
        await update.message.reply_text("🔴 BOT IS ON MAINTENANCE")
        return

    history_list = get_user_history(user_id)

    if not history_list:
        await update.message.reply_text("📜 You don't have any number history yet.")
        return

    message = "📜 Your previously assigned numbers:\n\n"
    for i, record in enumerate(history_list[-10:], 1):  # Show last 10
        flag = get_country_flag(record["country"])
        message += f"{i}. `{record['number']}` {flag} {record['country']}\n"

    message += "\nUse /change to get a new number anytime."
    await update.message.reply_text(message, parse_mode="Markdown")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    user_id = update.effective_user.id

    # Check if user is banned
    if is_user_banned(user_id):
        await update.message.reply_text("❌ You have been banned from using this bot.")
        return

    # Check if bot is running
    if not is_bot_running():
        await update.message.reply_text("🔴 BOT IS ON MAINTENANCE")
        return

    help_text = """❓ Available commands:

/start - Get a number by selecting a country
/mynumber - Show your current assigned number
/change - Change your assigned number
/history - View your previously assigned numbers
/report - Report issues with your number or OTP
/about - Learn about this bot"""

    await update.message.reply_text(help_text)

async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /report command"""
    user_id = update.effective_user.id

    # Check if user is banned
    if is_user_banned(user_id):
        await update.message.reply_text("❌ You have been banned from using this bot.")
        return

    # Check if bot is running
    if not is_bot_running():
        await update.message.reply_text("🔴 BOT IS ON MAINTENANCE")
        return

    await update.message.reply_text("⚠️ Please describe the problem you're having with your number or OTP. Our admin team will look into it.")

async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /about command"""
    user_id = update.effective_user.id

    # Check if user is banned
    if is_user_banned(user_id):
        await update.message.reply_text("❌ You have been banned from using this bot.")
        return

    # Check if bot is running
    if not is_bot_running():
        await update.message.reply_text("🔴 BOT IS ON MAINTENANCE")
        return

    about_text = """🤖 Telegram OTP Number Provider Bot
Developed by: Your Team
Contact: @your_contact"""

    await update.message.reply_text(about_text)

# Admin commands
async def is_admin(user_id):
    return str(user_id) in ADMIN_USER_IDS

async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stop command - Put bot in maintenance mode"""
    user_id = update.effective_user.id
    if not await is_admin(user_id):
        await update.message.reply_text("❌ You don't have permission to use this command.")
        return

    save_status("stopped")
    await update.message.reply_text("🔴 Bot has been STOPPED! It is now in maintenance mode.\nUsers will see 'BOT IS ON MAINTENANCE' message.")

async def run_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /run command - Start the bot"""
    user_id = update.effective_user.id
    if not await is_admin(user_id):
        await update.message.reply_text("❌ You don't have permission to use this command.")
        return

    save_status("running")
    await update.message.reply_text("🟢 Bot has been STARTED! It is now running normally.")

async def addnum_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /addnum command"""
    user_id = update.effective_user.id
    if not await is_admin(user_id):
        await update.message.reply_text("❌ You don't have permission to use this command.")
        return

    # Check if bot is running
    if not is_bot_running():
        await update.message.reply_text("🔴 BOT IS ON MAINTENANCE")
        return

    await update.message.reply_text("✏️ Enter the country code (e.g., BD, IN, US):")
    return ADD_COUNTRY_CODE

async def add_country_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle country code input"""
    # Check if bot is running
    if not is_bot_running():
        await update.message.reply_text("🔴 BOT IS ON MAINTENANCE")
        return ConversationHandler.END

    country_code = update.message.text.strip().upper()
    context.user_data["country_code"] = country_code
    await update.message.reply_text("Now send the numbers one by one (each number on a new line):\n\n[number1]\n[number2]\n...")
    return ADD_NUMBERS

async def add_numbers_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle numbers input"""
    # Check if bot is running
    if not is_bot_running():
        await update.message.reply_text("🔴 BOT IS ON MAINTENANCE")
        return ConversationHandler.END

    numbers_text = update.message.text.strip()
    numbers = [num.strip() for num in numbers_text.split('\n') if num.strip()]

    if not numbers:
        await update.message.reply_text("❌ No valid numbers found. Please try again.")
        return ConversationHandler.END

    country_code = context.user_data.get("country_code", "UNKNOWN")
    add_numbers(country_code, numbers)

    flag = get_country_flag(country_code)
    await update.message.reply_text(f"✅ {len(numbers)} numbers added for {flag} {country_code}!")
    return ConversationHandler.END

async def removenum_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /removenum command"""
    user_id = update.effective_user.id
    if not await is_admin(user_id):
        await update.message.reply_text("❌ You don't have permission to use this command.")
        return

    # Check if bot is running
    if not is_bot_running():
        await update.message.reply_text("🔴 BOT IS ON MAINTENANCE")
        return

    countries = get_available_countries()

    if not countries:
        await update.message.reply_text("❌ No countries available.")
        return

    # Create country buttons (2 per row)
    keyboard = []
    row = []
    for i, country in enumerate(countries):
        flag = get_country_flag(country)
        button = InlineKeyboardButton(f"{flag} {country}", callback_data=f"remove_{country}")
        row.append(button)
        if (i + 1) % 2 == 0:
            keyboard.append(row)
            row = []

    if row:
        keyboard.append(row)

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🗑 Please select the country whose numbers you want to remove:\n\n⚠️ Warning: This will delete ALL numbers for the selected country from the bot.", reply_markup=reply_markup)

async def remove_country_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle country removal"""
    query = update.callback_query
    await query.answer()

    # Check if bot is running
    if not is_bot_running():
        await query.edit_message_text("🔴 BOT IS ON MAINTENANCE")
        return

    country_code = query.data.split("_")[1]
    flag = get_country_flag(country_code)

    if remove_all_numbers_for_country(country_code):
        await query.edit_message_text(f"✅ All numbers for {flag} {country_code} have been removed from the bot!")
    else:
        await query.edit_message_text(f"❌ No numbers found for {flag} {country_code}.")

async def numlist_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /numlist command"""
    user_id = update.effective_user.id
    if not await is_admin(user_id):
        await update.message.reply_text("❌ You don't have permission to use this command.")
        return

    # Check if bot is running
    if not is_bot_running():
        await update.message.reply_text("🔴 BOT IS ON MAINTENANCE")
        return

    data = load_data()

    if not data:
        await update.message.reply_text("❌ No numbers available.")
        return

    message = "📋 Available numbers by country:\n\n"
    for country, numbers in data.items():
        flag = get_country_flag(country)
        message += f"{flag} {country}: {len(numbers)} numbers\n"

    await update.message.reply_text(message)

async def countrylist_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /countrylist command"""
    user_id = update.effective_user.id
    if not await is_admin(user_id):
        await update.message.reply_text("❌ You don't have permission to use this command.")
        return

    # Check if bot is running
    if not is_bot_running():
        await update.message.reply_text("🔴 BOT IS ON MAINTENANCE")
        return

    countries = get_available_countries()

    if not countries:
        await update.message.reply_text("❌ No countries available.")
        return

    message = "🌍 Countries currently available with numbers:\n\n"
    for country in countries:
        flag = get_country_flag(country)
        message += f"{flag} {country} "

    await update.message.reply_text(message)

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stats command - Enhanced statistics"""
    user_id = update.effective_user.id
    if not await is_admin(user_id):
        await update.message.reply_text("❌ You don't have permission to use this command.")
        return

    # Check if bot is running
    if not is_bot_running():
        await update.message.reply_text("🔴 BOT IS ON MAINTENANCE")
        return

    data = load_data()
    users = load_users()
    logs = load_logs()

    # Get current statistics
    total_numbers = sum(len(numbers) for numbers in data.values())
    total_countries = len(data)
    total_users = len(users)
    total_assigned = len(logs)

    # Count numbers by country
    country_stats = {}
    for country, numbers in data.items():
        country_stats[country] = len(numbers)

    # Count usage by country
    usage_by_country = {}
    usage_by_user = {}

    for log in logs:
        country = log['country_code']
        user = log['user_id']

        usage_by_country[country] = usage_by_country.get(country, 0) + 1
        usage_by_user[user] = usage_by_user.get(user, 0) + 1

    # Create detailed statistics message
    message = "📊 **BOT STATISTICS**\n\n"

    # Basic stats
    message += f"**Basic Information:**\n"
    message += f"Total Users: {total_users}\n"
    message += f"Total Countries: {total_countries}\n"
    message += f"Numbers Available: {total_numbers}\n"
    message += f"Numbers Assigned: {total_assigned}\n\n"

    # Numbers by country (available)
    message += "**Numbers Available by Country:**\n"
    if data:
        for country, count in sorted(country_stats.items(), key=lambda x: x[1], reverse=True):
            flag = get_country_flag(country)
            message += f"{flag} {country}: {count} numbers\n"
    else:
        message += "No numbers available\n"
    message += "\n"

    # Usage statistics
    message += "**Usage Statistics:**\n"
    if usage_by_country:
        message += "By Country:\n"
        for country, count in sorted(usage_by_country.items(), key=lambda x: x[1], reverse=True):
            flag = get_country_flag(country)
            message += f"{flag} {country}: {count} numbers taken\n"

        message += "\nBy User (Top 10):\n"
        sorted_users = sorted(usage_by_user.items(), key=lambda x: x[1], reverse=True)[:10]
        for user_id, count in sorted_users:
            message += f"User {user_id}: {count} numbers taken\n"
    else:
        message += "No usage data available\n"

    await update.message.reply_text(message, parse_mode="Markdown")

async def usednumbers_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /usednumbers command - Show list of used numbers"""
    user_id = update.effective_user.id
    if not await is_admin(user_id):
        await update.message.reply_text("❌ You don't have permission to use this command.")
        return

    # Check if bot is running
    if not is_bot_running():
        await update.message.reply_text("🔴 BOT IS ON MAINTENANCE")
        return

    used_numbers = load_used_numbers()

    if not used_numbers:
        await update.message.reply_text("📋 No numbers have been used yet.")
        return

    # Parse filters
    filters_dict = {}
    if context.args:
        for arg in context.args:
            if "=" in arg:
                key, value = arg.split("=", 1)
                filters_dict[key.lower()] = value.upper()
            elif arg.lower() == "today":
                filters_dict["today"] = True

    # Apply filters
    filtered_numbers = used_numbers.copy()

    # Filter by country
    if "country" in filters_dict:
        filtered_numbers = [num for num in filtered_numbers if num["country_code"] == filters_dict["country"]]

    # Filter by today
    if "today" in filters_dict:
        today = datetime.now().date().isoformat()
        filtered_numbers = [num for num in filtered_numbers if num["timestamp"].startswith(today)]

    if not filtered_numbers:
        await update.message.reply_text("📋 No used numbers match the specified filters.")
        return

    # Sort by timestamp (newest first)
    filtered_numbers.sort(key=lambda x: x["timestamp"], reverse=True)

    # Create message
    message = "📋 **Used Numbers (Latest)**\n\n"

    # Show up to 20 most recent entries
    for i, record in enumerate(filtered_numbers[:20], 1):
        flag = get_country_flag(record["country_code"])
        # Format timestamp
        try:
            timestamp = datetime.fromisoformat(record["timestamp"]).strftime("%Y-%m-%d %H:%M")
        except:
            timestamp = record["timestamp"][:16]  # Take first 16 characters

        message += f"{i}️⃣ {record['user_name']} — {flag} {record['number']} — {timestamp}\n"

    if len(filtered_numbers) > 20:
        message += f"\n... and {len(filtered_numbers) - 20} more entries"

    await update.message.reply_text(message, parse_mode="Markdown")

async def clearused_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /clearused command - Clear used numbers list"""
    user_id = update.effective_user.id
    if not await is_admin(user_id):
        await update.message.reply_text("❌ You don't have permission to use this command.")
        return

    # Check if bot is running
    if not is_bot_running():
        await update.message.reply_text("🔴 BOT IS ON MAINTENANCE")
        return

    # Clear used numbers file
    with open(USED_NUMBERS_FILE, "w") as f:
        json.dump([], f)

    await update.message.reply_text("✅ Used numbers list has been cleared!")

async def restats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /restats command - Reset all statistics (no confirmation required)"""
    user_id = update.effective_user.id
    if not await is_admin(user_id):
        await update.message.reply_text("❌ You don't have permission to use this command.")
        return

    # Check if bot is running
    if not is_bot_running():
        await update.message.reply_text("🔴 BOT IS ON MAINTENANCE")
        return

    # Reset statistics immediately
    reset_statistics()

    await update.message.reply_text("✅ Stats have been successfully reset!\n📊 New stats collection has started in real-time.")

async def ban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /ban command"""
    user_id = update.effective_user.id
    if not await is_admin(user_id):
        await update.message.reply_text("❌ You don't have permission to use this command.")
        return

    # Check if bot is running
    if not is_bot_running():
        await update.message.reply_text("🔴 BOT IS ON MAINTENANCE")
        return

    if not context.args:
        await update.message.reply_text("Usage: /ban <user_id>")
        return

    try:
        target_user_id = int(context.args[0])
        if ban_user(target_user_id):
            await update.message.reply_text(f"✅ User {target_user_id} has been banned!")
        else:
            await update.message.reply_text(f"⚠️ User {target_user_id} was already banned.")
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID. Please enter a valid number.")

async def unban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /unban command"""
    user_id = update.effective_user.id
    if not await is_admin(user_id):
        await update.message.reply_text("❌ You don't have permission to use this command.")
        return

    # Check if bot is running
    if not is_bot_running():
        await update.message.reply_text("🔴 BOT IS ON MAINTENANCE")
        return

    if not context.args:
        await update.message.reply_text("Usage: /unban <user_id>")
        return

    try:
        target_user_id = int(context.args[0])
        if unban_user(target_user_id):
            await update.message.reply_text(f"✅ User {target_user_id} has been unbanned!")
        else:
            await update.message.reply_text(f"⚠️ User {target_user_id} was not banned.")
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID. Please enter a valid number.")

async def setwelcome_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /setwelcome command"""
    user_id = update.effective_user.id
    if not await is_admin(user_id):
        await update.message.reply_text("❌ You don't have permission to use this command.")
        return

    # Check if bot is running
    if not is_bot_running():
        await update.message.reply_text("🔴 BOT IS ON MAINTENANCE")
        return

    if not context.args:
        current_welcome = load_welcome()
        await update.message.reply_text(f"Current welcome message:\n\n{current_welcome}\n\nUsage: /setwelcome <new message>")
        return

    new_message = " ".join(context.args)
    save_welcome(new_message)
    await update.message.reply_text("✅ Welcome message updated successfully!")

def main():
    """Start the bot"""
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()

    # User commands
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("mynumber", mynumber))
    application.add_handler(CommandHandler("history", history))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("report", report))
    application.add_handler(CommandHandler("about", about))

    # Callback handlers
    application.add_handler(CallbackQueryHandler(country_callback, pattern="^select_"))
    application.add_handler(CallbackQueryHandler(change_callback, pattern="^change$"))
    application.add_handler(CallbackQueryHandler(page_callback, pattern="^page_"))
    application.add_handler(CallbackQueryHandler(remove_country_callback, pattern="^remove_"))

    # Admin commands - Stop/Run
    application.add_handler(CommandHandler("stop", stop_command))
    application.add_handler(CommandHandler("run", run_command))

    # Admin commands - Add Numbers
    add_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("addnum", addnum_command)],
        states={
            ADD_COUNTRY_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_country_code)],
            ADD_NUMBERS: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_numbers_input)]
        },
        fallbacks=[CommandHandler("cancel", lambda u, c: ConversationHandler.END)]
    )
    application.add_handler(add_conv_handler)

    # Admin commands - Remove Numbers
    application.add_handler(CommandHandler("removenum", removenum_command))

    # Admin commands - List Numbers
    application.add_handler(CommandHandler("numlist", numlist_command))
    application.add_handler(CommandHandler("countrylist", countrylist_command))

    # Admin commands - Stats
    application.add_handler(CommandHandler("stats", stats_command))

    # Admin commands - Used Numbers
    application.add_handler(CommandHandler("usednumbers", usednumbers_command))
    application.add_handler(CommandHandler("clearused", clearused_command))

    # Admin commands - Reset Stats
    application.add_handler(CommandHandler("restats", restats_command))

    # Admin commands - Ban/Unban
    application.add_handler(CommandHandler("ban", ban_command))
    application.add_handler(CommandHandler("unban", unban_command))

    # Admin commands - Set Welcome
    application.add_handler(CommandHandler("setwelcome", setwelcome_command))

    # Start the bot
    logger.info("Starting bot...")
    application.run_polling()

if __name__ == "__main__":
    main()
