# --- IMPORTS ---
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
from keyboards import (
    get_main_menu_keyboard,
    get_back_keyboard,
    get_payment_methods_keyboard,
    get_admin_approval_keyboard,
    get_proxy_packages_keyboard,
    get_remove_proxy_keyboard,
    get_remove_price_keyboard,
    get_remove_payment_method_keyboard,
)
from database import db

# --- SETUP ---
logger = logging.getLogger(__name__)

# --- STATES ---
(SELECTING_METHOD, ENTERING_AMOUNT, SELECTING_PACKAGE, ENTERING_PROXY_TO_ADD,
 SELECTING_PROXY_TO_REMOVE, ENTERING_PRICE_DURATION, ENTERING_PRICE_BDT,
 ENTERING_PAYMENT_METHOD_NAME, ENTERING_PAYMENT_METHOD_DETAILS, ENTERING_EXCHANGE_RATE,
 AWAITING_PROXY_FILE) = range(11)

# --- ASYNC FUNCTION DEFINITIONS ---

async def check_bot_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if hasattr(update.effective_user, 'id') and update.effective_user.id in ADMIN_IDS:
        return True
    bot_status = db.get_setting('bot_status')
    if bot_status == 'off':
        text = "⚠️ Bot Under Maintenance — Try again later."
        if update.callback_query:
            await update.callback_query.answer(text, show_alert=True)
        elif update.message:
            await update.message.reply_text(text)
        return False
    return True

async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_bot_status(update, context): return
    user_id = update.effective_user.id
    is_admin = user_id in ADMIN_IDS
    welcome_message = "👋 Welcome to ProxyHub! Tap below to explore services 🌐👇"
    reply_markup = get_main_menu_keyboard(is_admin=is_admin)
    query = update.callback_query
    if query:
        await query.answer()
        await query.edit_message_text(text=welcome_message, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.message.reply_text(text=welcome_message, reply_markup=reply_markup, parse_mode='Markdown')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if user:
        db.add_user(user.id)
        logger.info(f"User {user.full_name} (ID: {user.id}) started the bot.")
    await main_menu(update, context)

async def back_to_main_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await main_menu(update, context)

async def balance_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await check_bot_status(update, context): return
    query = update.callback_query
    await query.answer()
    balance = db.get_user_balance(query.from_user.id)
    text = f"Your Balance: {balance['balance_bdt']:.2f} BDT / ${balance['balance_usd']:.2f} USD"
    await query.edit_message_text(text=text, reply_markup=get_back_keyboard())

async def payment_methods_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await check_bot_status(update, context): return
    query = update.callback_query
    await query.answer()
    methods = db.get_payment_methods()
    text = "💳 *Payment Methods*\n\n"
    if methods:
        for m in methods:
            text += f"• *{m['name']}*: `{m['details']}`\n"
    else:
        text += "No payment methods are currently available."
    await query.edit_message_text(text=text, reply_markup=get_back_keyboard(), parse_mode='Markdown')

async def price_list_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await check_bot_status(update, context): return
    query = update.callback_query
    await query.answer()
    prices = db.get_prices()
    text = "📊 *Price List*\n\n"
    if prices:
        for price in prices:
            text += f"• *{price['duration_days']} Day(s)*: {price['price_bdt']:.2f} BDT / ${price['price_usd']:.2f} USD\n"
    else:
        text = "📊 *Price List*\n\nNo proxy packages are currently available."
    await query.edit_message_text(text=text, reply_markup=get_back_keyboard(), parse_mode='Markdown')

async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await check_bot_status(update, context): return
    query = update.callback_query
    await query.answer()
    text = "📋 *Button Guide*\n\n💵 BALANCE → Check your funds\n💰 ADD BALANCE → Deposit via payment method\n🌐 BUY PROXY → Purchase new IP\n🔍 MY PROXIES → View assigned IPs\n📜 HISTORY → See all transactions\n💳 PAYMENT METHODS → View accepted methods\n📊 PRICE LIST → See current rates\n🔙 BACK → Return to previous menu"
    await query.edit_message_text(text=text, reply_markup=get_back_keyboard(), parse_mode='Markdown')

async def history_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await check_bot_status(update, context): return
    query = update.callback_query
    await query.answer()
    history = db.get_user_history(query.from_user.id)
    text = "📜 *Transaction History*\n\n"
    if history:
        for item in history:
            text += f"*{item['type'].capitalize()}* - {item['amount']} {item['currency']} ({item['status']}) on {item['date']}\nTXN: `{item['txn_id']}`\n\n"
    else:
        text += "You have no transactions yet."
    await query.edit_message_text(text=text, reply_markup=get_back_keyboard(), parse_mode='Markdown')

async def my_proxies_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await check_bot_status(update, context): return
    query = update.callback_query
    await query.answer()
    proxies = db.get_user_proxies(query.from_user.id)
    text = "🔍 *My Proxies*\n\n"
    if proxies:
        for proxy in proxies:
            text += f"• `{proxy['ip_port']}`\n  *Expires*: {proxy['expiry_date']}\n  *Status*: Active\n"
    else:
        text += "You have no active proxies."
    await query.edit_message_text(text=text, reply_markup=get_back_keyboard(), parse_mode='Markdown')

async def add_balance_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not await check_bot_status(update, context): return ConversationHandler.END
    query = update.callback_query
    await query.answer()
    methods = db.get_payment_methods()
    if not methods:
        await query.edit_message_text(text="❌ No payment methods available.", reply_markup=get_back_keyboard())
        return ConversationHandler.END
    await query.edit_message_text(text="💳 *Select Payment Method:*", reply_markup=get_payment_methods_keyboard(methods), parse_mode='Markdown')
    return SELECTING_METHOD

async def select_method(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    method_name = query.data.replace('select_method_', '')
    context.user_data['payment_method'] = method_name
    await query.edit_message_text(text=f"🔢 *Enter Amount (in BDT or USD)* for {method_name}:\n\nExample: `1000 BDT` or `10 USD`", parse_mode='Markdown')
    return ENTERING_AMOUNT

async def enter_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    payment_method = context.user_data.get('payment_method')
    try:
        amount_str, currency = update.message.text.upper().split()
        amount = float(amount_str)
        if currency not in ['BDT', 'USD']: raise ValueError
    except (ValueError, IndexError):
        await update.message.reply_text("❌ Invalid format. Please use format like `1000 BDT` or `10 USD`.")
        return ENTERING_AMOUNT
    txn_id = db.create_pending_deposit(user.id, amount, currency, payment_method)
    if not txn_id:
        await update.message.reply_text("❌ An error occurred. Please try again.")
        return ConversationHandler.END
    await update.message.reply_text("⏳ *Pending Approval* — Your request has been submitted and an admin will review it shortly.")
    admin_message = f"🔔 *New Balance Request*\nUser: {user.full_name} (`{user.id}`)\nMethod: {payment_method}\nAmount: {amount} {currency}\nTXN: `{txn_id}`"
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(chat_id=admin_id, text=admin_message, reply_markup=get_admin_approval_keyboard(txn_id), parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Failed to send notification to admin {admin_id}: {e}")
    return ConversationHandler.END

async def add_balance_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await main_menu(update, context)
    return ConversationHandler.END

async def buy_proxy_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not await check_bot_status(update, context): return ConversationHandler.END
    query = update.callback_query
    await query.answer()
    prices = db.get_prices()
    if not prices:
        await query.edit_message_text(text="❌ No proxy packages are currently available.", reply_markup=get_back_keyboard())
        return ConversationHandler.END
    await query.edit_message_text(text="📊 *Select a Proxy Package:*", reply_markup=get_proxy_packages_keyboard(prices), parse_mode='Markdown')
    return SELECTING_PACKAGE

async def select_package(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    duration_days = int(query.data.replace('buy_package_', ''))
    user_id = query.from_user.id
    prices = {p['duration_days']: p for p in db.get_prices()}
    package_price_bdt = prices[duration_days]['price_bdt']
    balance = db.get_user_balance(user_id)
    if balance['balance_bdt'] < package_price_bdt:
        await query.edit_message_text(text="❌ Insufficient Balance — Add funds first via 💰 ADD BALANCE.", reply_markup=get_back_keyboard())
        return ConversationHandler.END
    proxy = db.get_unassigned_proxy()
    if not proxy:
        await query.edit_message_text(text="❌ We are currently out of stock for proxies. Please check back later.", reply_markup=get_back_keyboard())
        return ConversationHandler.END
    db.update_user_balance(user_id, amount_bdt_change=-package_price_bdt)
    expiry_date = (datetime.utcnow() + timedelta(days=duration_days)).strftime("%Y-%m-%d %H:%M:%S")
    db.assign_proxy_to_user(proxy['id'], user_id, expiry_date)
    db.create_purchase_transaction(user_id, package_price_bdt, 'BDT', f"{duration_days}-day proxy")
    success_message = f"🎉 *Success!* Your proxy is ready:\n\nProxy: `{proxy['ip_port']}`\nValid until: {expiry_date}"
    await query.edit_message_text(text=success_message, reply_markup=get_back_keyboard(), parse_mode='Markdown')
    return ConversationHandler.END

async def buy_proxy_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await main_menu(update, context)
    return ConversationHandler.END

async def handle_approval(update: Update, context: ContextTypes.DEFAULT_TYPE, approve: bool):
    query = update.callback_query
    await query.answer()
    logger.info(f"Handling approval flow. Callback data: {query.data}")
    txn_id = query.data.split('_')[-1]
    logger.info(f"Extracted TXN_ID: {txn_id}")
    transaction = db.get_transaction(txn_id)
    logger.info(f"Transaction found in DB: {transaction}")
    if not transaction or transaction['status'] != 'pending':
        logger.warning(f"Transaction {txn_id} is invalid or not pending. Status: {transaction['status'] if transaction else 'Not Found'}")
        await query.edit_message_text("⚠️ This request has already been processed or is invalid.")
        return
    new_status = "approved" if approve else "rejected"
    db.update_transaction_status(txn_id, new_status)
    user_id = transaction['user_id']
    amount = transaction['amount']
    currency = transaction['currency']
    if approve:
        logger.info(f"Processing approval for {amount} {currency} for user {user_id}")
        exchange_rate = float(db.get_setting('exchange_rate'))
        bdt_change = amount if currency == 'BDT' else amount * exchange_rate
        usd_change = amount if currency == 'USD' else amount / exchange_rate
        logger.info(f"Updating user balance. BDT change: {bdt_change}, USD change: {usd_change}")
        db.update_user_balance(user_id, bdt_change, usd_change)
        new_balance = db.get_user_balance(user_id)
        user_message = f"✅ Payment Approved! New Balance: {new_balance['balance_bdt']:.2f} BDT / ${new_balance['balance_usd']:.2f} USD"
        admin_feedback = f"✅ Request `{txn_id}` approved."
    else:
        logger.info(f"Processing rejection for transaction {txn_id}")
        user_message = "❌ Your payment request was rejected. Please contact an admin for support."
        admin_feedback = f"❌ Request `{txn_id}` rejected."
    try:
        await context.bot.send_message(chat_id=user_id, text=user_message)
        logger.info(f"Sent notification to user {user_id}")
    except Exception as e:
        logger.error(f"Failed to send notification to user {user_id}: {e}")
    await query.edit_message_text(admin_feedback, parse_mode='Markdown')

async def approve_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await handle_approval(update, context, approve=True)

async def reject_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await handle_approval(update, context, approve=False)

async def set_bot_status_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, status: str):
    query = update.callback_query
    db.set_setting('bot_status', status)
    await query.answer(f"Bot is now {status.upper()}", show_alert=True)
    await main_menu(update, context)

async def turn_on_bot_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await set_bot_status_handler(update, context, 'on')

async def turn_off_bot_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await set_bot_status_handler(update, context, 'off')

async def pending_orders_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    pending = db.get_pending_deposits()
    if not pending:
        await query.edit_message_text("✅ No pending orders.", reply_markup=get_back_keyboard('main'))
        return
    await query.edit_message_text("⏳ *Pending Deposit Requests*\n\n", parse_mode='Markdown')
    for p in pending:
        try:
            user_info = await context.bot.get_chat(p['user_id'])
            user_full_name = user_info.full_name
        except Exception:
            user_full_name = "Unknown User"
        admin_message = f"🔔 *New Balance Request*\nUser: {user_full_name} (`{p['user_id']}`)\nMethod: {p['payment_method']}\nAmount: {p['amount']} {p['currency']}\nTXN: `{p['txn_id']}`"
        await query.message.reply_text(text=admin_message, reply_markup=get_admin_approval_keyboard(p['txn_id']), parse_mode='Markdown')
    await query.message.reply_text(text="--- End of List ---", reply_markup=get_back_keyboard('main'))

async def admin_add_proxy_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("➕ Please send the proxy you want to add in `IP:PORT` format.")
    return ENTERING_PROXY_TO_ADD

async def admin_add_proxy_receive(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    proxy_str = update.message.text
    if ':' not in proxy_str or len(proxy_str.split(':')) != 2:
        await update.message.reply_text("❌ Invalid format. Please use `IP:PORT`.")
        return ENTERING_PROXY_TO_ADD
    db.add_proxy_to_pool(proxy_str)
    await update.message.reply_text(f"✅ Proxy `{proxy_str}` added to the pool.")
    await start(update, context)
    return ConversationHandler.END

async def admin_remove_proxy_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    proxies = db.get_all_proxies_from_pool()
    if not proxies:
        await query.edit_message_text("❌ There are no proxies in the pool to remove.", reply_markup=get_back_keyboard())
        return ConversationHandler.END
    await query.edit_message_text("➖ Select a proxy to remove from the list below:", reply_markup=get_remove_proxy_keyboard(proxies))
    return SELECTING_PROXY_TO_REMOVE

async def admin_remove_proxy_select(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    proxy_id = int(query.data.replace('admin_delete_proxy_', ''))
    db.remove_proxy_from_pool(proxy_id)
    await query.edit_message_text("✅ Proxy successfully removed.", reply_markup=get_back_keyboard())
    return ConversationHandler.END

async def admin_add_price_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("➕ Please send the duration for the new price package (in days).")
    return ENTERING_PRICE_DURATION

async def admin_add_price_duration(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        duration = int(update.message.text)
        context.user_data['price_duration'] = duration
        await update.message.reply_text(f"Got it. Duration is {duration} days. Now, please send the price in BDT.")
        return ENTERING_PRICE_BDT
    except ValueError:
        await update.message.reply_text("❌ Invalid number. Please send the duration in days (e.g., 30).")
        return ENTERING_PRICE_DURATION

async def admin_add_price_bdt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        price_bdt = float(update.message.text)
        duration = context.user_data['price_duration']
        exchange_rate = float(db.get_setting('exchange_rate'))
        price_usd = price_bdt / exchange_rate
        db.add_price(duration, price_bdt, price_usd)
        await update.message.reply_text(f"✅ New price added for {duration} days: {price_bdt:.2f} BDT / ${price_usd:.2f} USD.")
        await start(update, context)
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("❌ Invalid number. Please send the price in BDT (e.g., 1000.00).")
        return ENTERING_PRICE_BDT

async def admin_remove_price_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    prices = db.get_prices()
    if not prices:
        await query.edit_message_text("❌ There are no prices to remove.", reply_markup=get_back_keyboard())
        return ConversationHandler.END
    await query.edit_message_text("➖ Select a price package to remove:", reply_markup=get_remove_price_keyboard(prices))
    return ConversationHandler.END

async def admin_remove_price_select(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    duration_days = int(query.data.replace('admin_delete_price_', ''))
    db.remove_price(duration_days)
    await query.edit_message_text("✅ Price package successfully removed.", reply_markup=get_back_keyboard())
    return ConversationHandler.END

async def admin_add_payment_method_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("➕ Please send the name for the new payment method (e.g., bKash Personal).")
    return ENTERING_PAYMENT_METHOD_NAME

async def admin_add_payment_method_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['payment_method_name'] = update.message.text
    await update.message.reply_text("Got it. Now please send the payment details (e.g., the account number or address).")
    return ENTERING_PAYMENT_METHOD_DETAILS

async def admin_add_payment_method_details(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    name = context.user_data['payment_method_name']
    details = update.message.text
    db.add_payment_method(name, details)
    await update.message.reply_text(f"✅ Payment method '{name}' with details '{details}' added.")
    await start(update, context)
    return ConversationHandler.END

async def admin_remove_payment_method_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    methods = db.get_payment_methods()
    if not methods:
        await query.edit_message_text("❌ There are no payment methods to remove.", reply_markup=get_back_keyboard())
        return
    await query.edit_message_text("➖ Select a payment method to remove:", reply_markup=get_remove_payment_method_keyboard(methods))

async def admin_remove_payment_method_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    method_id = int(query.data.replace('admin_delete_method_', ''))
    db.remove_payment_method(method_id)
    await query.edit_message_text("✅ Payment method successfully removed.", reply_markup=get_back_keyboard())

async def admin_set_exchange_rate_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    current_rate = db.get_setting('exchange_rate')
    await query.edit_message_text(f"💱 The current exchange rate is 1 USD = {current_rate} BDT.\n\nPlease send the new rate (e.g., 120.5).")
    return ENTERING_EXCHANGE_RATE

async def admin_set_exchange_rate_receive(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        new_rate = float(update.message.text)
        db.set_setting('exchange_rate', str(new_rate))
        await update.message.reply_text(f"✅ Exchange rate updated to 1 USD = {new_rate} BDT.")
        await start(update, context)
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("❌ Invalid number. Please send the rate as a number (e.g., 120.5).")
        return ENTERING_EXCHANGE_RATE

async def admin_import_proxies_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("📂 Please upload a `.txt` or `.csv` file containing one proxy (`IP:PORT`) per line.")
    return AWAITING_PROXY_FILE

async def admin_import_proxies_receive(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    document = update.message.document
    if not document or document.file_name.split('.')[-1] not in ['txt', 'csv']:
        await update.message.reply_text("❌ Invalid file type. Please upload a `.txt` or `.csv` file.")
        return AWAITING_PROXY_FILE
    try:
        file = await context.bot.get_file(document.file_id)
        file_content = (await file.download_as_bytearray()).decode('utf-8')
        proxies = [line.strip() for line in file_content.splitlines() if line.strip()]
        if not proxies:
            await update.message.reply_text("❌ The file is empty or contains no valid proxy lines.")
            await start(update, context)
            return ConversationHandler.END
        added_count = 0
        for proxy in proxies:
            if ':' in proxy:
                db.add_proxy_to_pool(proxy)
                added_count += 1
        await update.message.reply_text(f"✅ Import complete. Added {added_count} new proxies to the pool.")
    except Exception as e:
        logger.error(f"Error processing proxy file: {e}")
        await update.message.reply_text("❌ An error occurred while processing the file.")
    await start(update, context)
    return ConversationHandler.END

# --- HANDLER ASSIGNMENTS ---
start_handler = CommandHandler("start", start)
back_to_main_callback_handler = CallbackQueryHandler(back_to_main_handler, pattern="^back_to_main$")
balance_callback_handler = CallbackQueryHandler(balance_handler, pattern="^balance$")
payment_methods_callback_handler = CallbackQueryHandler(payment_methods_handler, pattern="^payment_methods$")
price_list_callback_handler = CallbackQueryHandler(price_list_handler, pattern="^price_list$")
help_callback_handler = CallbackQueryHandler(help_handler, pattern="^help$")
history_callback_handler = CallbackQueryHandler(history_handler, pattern="^history$")
my_proxies_callback_handler = CallbackQueryHandler(my_proxies_handler, pattern="^my_proxies$")
approve_callback_handler = CallbackQueryHandler(approve_handler, pattern=r'^admin_approve_')
reject_callback_handler = CallbackQueryHandler(reject_handler, pattern=r'^admin_reject_')
turn_on_bot_callback_handler = CallbackQueryHandler(turn_on_bot_handler, pattern="^admin_turn_on_bot$")
turn_off_bot_callback_handler = CallbackQueryHandler(turn_off_bot_handler, pattern="^admin_turn_off_bot$")
pending_orders_callback_handler = CallbackQueryHandler(pending_orders_handler, pattern="^admin_pending_orders$")
remove_price_callback_handler = CallbackQueryHandler(admin_remove_price_select, pattern='^admin_delete_price_')
admin_remove_price_entry_handler = CallbackQueryHandler(admin_remove_price_start, pattern='^admin_remove_price$')
remove_payment_method_callback_handler = CallbackQueryHandler(admin_remove_payment_method_select, pattern='^admin_delete_method_')
admin_remove_payment_method_entry_handler = CallbackQueryHandler(admin_remove_payment_method_start, pattern='^admin_remove_payment$')

add_balance_conv_handler = ConversationHandler(entry_points=[CallbackQueryHandler(add_balance_start, pattern='^add_balance$')], states={SELECTING_METHOD: [CallbackQueryHandler(select_method, pattern='^select_method_')], ENTERING_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_amount)],}, fallbacks=[CallbackQueryHandler(add_balance_cancel, pattern='^back_to_main$')])
buy_proxy_conv_handler = ConversationHandler(entry_points=[CallbackQueryHandler(buy_proxy_start, pattern='^buy_proxy$')], states={SELECTING_PACKAGE: [CallbackQueryHandler(select_package, pattern='^buy_package_')]}, fallbacks=[CallbackQueryHandler(buy_proxy_cancel, pattern='^back_to_main$')])
add_proxy_conv_handler = ConversationHandler(entry_points=[CallbackQueryHandler(admin_add_proxy_start, pattern='^admin_add_proxy$')], states={ENTERING_PROXY_TO_ADD: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_add_proxy_receive)]}, fallbacks=[CallbackQueryHandler(back_to_main_handler, pattern='^back_to_main$')])
remove_proxy_conv_handler = ConversationHandler(entry_points=[CallbackQueryHandler(admin_remove_proxy_start, pattern='^admin_remove_proxy$')], states={SELECTING_PROXY_TO_REMOVE: [CallbackQueryHandler(admin_remove_proxy_select, pattern='^admin_delete_proxy_')]}, fallbacks=[CallbackQueryHandler(back_to_main_handler, pattern='^back_to_main$')])
add_price_conv_handler = ConversationHandler(entry_points=[CallbackQueryHandler(admin_add_price_start, pattern='^admin_add_price$')], states={ENTERING_PRICE_DURATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_add_price_duration)], ENTERING_PRICE_BDT: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_add_price_bdt)],}, fallbacks=[CallbackQueryHandler(back_to_main_handler, pattern='^back_to_main$')])
add_payment_method_conv_handler = ConversationHandler(entry_points=[CallbackQueryHandler(admin_add_payment_method_start, pattern='^admin_add_payment$')], states={ENTERING_PAYMENT_METHOD_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_add_payment_method_name)], ENTERING_PAYMENT_METHOD_DETAILS: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_add_payment_method_details)],}, fallbacks=[CallbackQueryHandler(back_to_main_handler, pattern='^back_to_main$')])
set_exchange_rate_conv_handler = ConversationHandler(entry_points=[CallbackQueryHandler(admin_set_exchange_rate_start, pattern='^admin_set_exchange_rate$')], states={ENTERING_EXCHANGE_RATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_set_exchange_rate_receive)]}, fallbacks=[CallbackQueryHandler(back_to_main_handler, pattern='^back_to_main$')])
import_proxies_conv_handler = ConversationHandler(entry_points=[CallbackQueryHandler(admin_import_proxies_start, pattern='^admin_import_proxies$')], states={AWAITING_PROXY_FILE: [MessageHandler(filters.Document.ALL, admin_import_proxies_receive)],}, fallbacks=[CallbackQueryHandler(back_to_main_handler, pattern='^back_to_main$')])
