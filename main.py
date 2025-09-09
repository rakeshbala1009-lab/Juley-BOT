import asyncio
import logging
from telegram.ext import Application
from config import TELEGRAM_BOT_TOKEN
from handlers import (
    start_handler,
    back_to_main_callback_handler,
    balance_callback_handler, # Corrected name
    payment_methods_callback_handler, # Corrected name
    price_list_callback_handler, # Corrected name
    help_callback_handler, # Corrected name
    history_callback_handler, # Corrected name
    my_proxies_callback_handler, # Corrected name
    add_balance_conv_handler,
    approve_callback_handler,
    reject_callback_handler,
    buy_proxy_conv_handler,
    turn_on_bot_callback_handler,
    turn_off_bot_callback_handler,
    pending_orders_callback_handler,
    add_proxy_conv_handler,
    remove_proxy_conv_handler,
    add_price_conv_handler,
    remove_price_callback_handler,
    admin_remove_price_entry_handler,
    add_payment_method_conv_handler,
    remove_payment_method_callback_handler,
    admin_remove_payment_method_entry_handler,
    set_exchange_rate_conv_handler,
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def main() -> None:
    """Run the bot."""
    if not TELEGRAM_BOT_TOKEN:
        logger.error("FATAL: TELEGRAM_BOT_TOKEN not found in environment variables.")
        return

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Add all handlers
    application.add_handler(start_handler)
    application.add_handler(back_to_main_callback_handler)
    application.add_handler(balance_callback_handler) # Corrected name
    application.add_handler(payment_methods_callback_handler) # Corrected name
    application.add_handler(price_list_callback_handler) # Corrected name
    application.add_handler(help_callback_handler) # Corrected name
    application.add_handler(history_callback_handler) # Corrected name
    application.add_handler(my_proxies_callback_handler) # Corrected name

    application.add_handler(add_balance_conv_handler)
    application.add_handler(approve_callback_handler)
    application.add_handler(reject_callback_handler)

    application.add_handler(buy_proxy_conv_handler)

    application.add_handler(turn_on_bot_callback_handler)
    application.add_handler(turn_off_bot_callback_handler)
    application.add_handler(pending_orders_callback_handler)

    application.add_handler(add_proxy_conv_handler)
    application.add_handler(remove_proxy_conv_handler)

    application.add_handler(add_price_conv_handler)
    application.add_handler(remove_price_callback_handler)
    application.add_handler(admin_remove_price_entry_handler)

    application.add_handler(add_payment_method_conv_handler)
    application.add_handler(remove_payment_method_callback_handler)
    application.add_handler(admin_remove_payment_method_entry_handler)

    application.add_handler(set_exchange_rate_conv_handler)

    logger.info("Bot is starting...")
    application.run_polling()

if __name__ == "__main__":
    main()
