import logging
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import (
    ContextTypes,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)
from config import ADMIN_IDS
from keyboards import get_main_menu_keyboard, get_back_keyboard, get_payment_methods_keyboard, get_admin_approval_keyboard, get_proxy_packages_keyboard, get_remove_proxy_keyboard, get_remove_price_keyboard
from database import db

# (The rest of the file is the same as before)
# ...
