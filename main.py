# (Omitting imports and setup for brevity)
# ...
from handlers import (
    # ... all the existing ones
    set_exchange_rate_conv_handler,
)

# ...

def main() -> None:
    # ...
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Add handlers
    # ... (all the existing ones)
    application.add_handler(set_exchange_rate_conv_handler)

    # ...
    application.run_polling()

if __name__ == "__main__":
    main()
