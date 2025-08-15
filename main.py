import logging
import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# Load environment variables from .env file
load_dotenv()

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get environment variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_IDS = [int(admin_id) for admin_id in os.getenv("ADMIN_IDS", "").split(',') if admin_id]
USER_IDS_FILE = "storage/user_ids.txt"

# States for conversation handler
AWAITING_BROADCAST_MESSAGE = 0

def get_registered_users():
    """Reads the list of registered user IDs from the file."""
    try:
        with open(USER_IDS_FILE, "r") as f:
            return {int(line.strip()) for line in f if line.strip()}
    except FileNotFoundError:
        return set()

def save_user_id(user_id):
    """Saves a new user ID to the file, avoiding duplicates."""
    registered_users = get_registered_users()
    if user_id not in registered_users:
        with open(USER_IDS_FILE, "a") as f:
            f.write(f"{user_id}\n")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /start command, registering the user."""
    user_id = update.message.chat_id
    save_user_id(user_id)
    await update.message.reply_text(
        "👋 Welcome! You are now registered with this bot.\n"
        "You will receive important updates here."
    )

async def message_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles the /message command, starting the broadcast process."""
    user_id = update.message.from_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ You are not authorized to use this command.")
        return ConversationHandler.END

    await update.message.reply_text(
        "📨 Please enter the message you want to send to all users.\n"
        "(You can type /cancel to abort.)"
    )
    return AWAITING_BROADCAST_MESSAGE

async def broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles the broadcast message from the admin."""
    broadcast_text = update.message.text
    user_ids = get_registered_users()
    success_count = 0

    for user_id in user_ids:
        try:
            await context.bot.send_message(chat_id=user_id, text=broadcast_text)
            success_count += 1
        except Exception as e:
            logger.error(f"Failed to send message to {user_id}: {e}")

    await update.message.reply_text(
        f"✅ Broadcast complete.\nMessage sent to {success_count} users."
    )
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels the broadcast conversation."""
    await update.message.reply_text("❌ Broadcast cancelled.")
    return ConversationHandler.END

def main() -> None:
    """Start the bot."""
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not found in .env file")
        return

    if not ADMIN_IDS:
        logger.error("ADMIN_IDS not found in .env file")
        return

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Conversation handler for the /message command
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("message", message_command)],
        states={
            AWAITING_BROADCAST_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, broadcast_message)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(conv_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling()

if __name__ == "__main__":
    main()
