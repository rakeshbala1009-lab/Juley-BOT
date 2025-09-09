from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# Main menu for regular users - 1x1 Layout
USER_MAIN_MENU_BUTTONS = [
    [InlineKeyboardButton("💵 BALANCE", callback_data='balance')],
    [InlineKeyboardButton("💰 ADD BALANCE", callback_data='add_balance')],
    [InlineKeyboardButton("🌐 BUY PROXY", callback_data='buy_proxy')],
    [InlineKeyboardButton("🔍 MY PROXIES", callback_data='my_proxies')],
    [InlineKeyboardButton("📜 HISTORY", callback_data='history')],
    [InlineKeyboardButton("💳 PAYMENT METHODS", callback_data='payment_methods')],
    [InlineKeyboardButton("📊 PRICE LIST", callback_data='price_list')],
    [InlineKeyboardButton("❓ HELP", callback_data='help')],
]

# Additional buttons for admins, shown below the user buttons - 1x1 Layout
ADMIN_MAIN_MENU_BUTTONS = [
    [InlineKeyboardButton("➕ ADD PRICE 💎", callback_data='admin_add_price')],
    [InlineKeyboardButton("➖ REMOVE PRICE 🗑️", callback_data='admin_remove_price')],
    [InlineKeyboardButton("💳 ADD PAYMENT ➕", callback_data='admin_add_payment')],
    [InlineKeyboardButton("🗑️ REMOVE PAYMENT ➖", callback_data='admin_remove_payment')],
    [InlineKeyboardButton("🔧 ASSIGN PROXY 🎯", callback_data='admin_assign_proxy')],
    [InlineKeyboardButton("🔁 CHANGE PROXY 🔄", callback_data='admin_change_proxy')],
    [InlineKeyboardButton("⏳ PENDING ORDERS ⚠️", callback_data='admin_pending_orders')],
    [InlineKeyboardButton("💱 SET EXCHANGE RATE 💱", callback_data='admin_set_exchange_rate')],
    [InlineKeyboardButton("➕ ADD PROXY", callback_data='admin_add_proxy')],
    [InlineKeyboardButton("➖ REMOVE PROXY", callback_data='admin_remove_proxy')],
    [InlineKeyboardButton("📂 IMPORT PROXIES", callback_data='admin_import_proxies')],
    [InlineKeyboardButton("🛑 TURN OFF BOT 🔌", callback_data='admin_turn_off_bot')],
    [InlineKeyboardButton("✅ TURN ON BOT ⚡", callback_data='admin_turn_on_bot')],
]

def get_main_menu_keyboard(is_admin=False):
    """
    Returns the main menu keyboard based on user role.
    """
    buttons = USER_MAIN_MENU_BUTTONS
    if is_admin:
        # For admins, add a separator and then the admin buttons
        separator = [[InlineKeyboardButton("--- 👑 ADMIN PANEL 👑 ---", callback_data='admin_panel_header')]]
        buttons = buttons + separator + ADMIN_MAIN_MENU_BUTTONS
    return InlineKeyboardMarkup(buttons)

def get_back_button(menu='main'):
    """
    Returns a single back button.
    """
    return InlineKeyboardButton(f"🔙 BACK", callback_data=f'back_to_{menu}')

def get_back_keyboard(menu='main'):
    """
    Returns an InlineKeyboardMarkup with just a back button.
    """
    return InlineKeyboardMarkup([[get_back_button(menu)]])

def get_payment_methods_keyboard(methods):
    """
    Creates a keyboard with payment methods.
    """
    buttons = []
    for method in methods:
        buttons.append([InlineKeyboardButton(f"💳 {method['name']}", callback_data=f"select_method_{method['name']}")])
    buttons.append([get_back_button('main')])
    return InlineKeyboardMarkup(buttons)

def get_admin_approval_keyboard(txn_id):
    """
    Creates the approval keyboard for admins.
    """
    buttons = [
        [
            InlineKeyboardButton("✅ APPROVE", callback_data=f"admin_approve_{txn_id}"),
            InlineKeyboardButton("❌ REJECT", callback_data=f"admin_reject_{txn_id}")
        ]
    ]
    return InlineKeyboardMarkup(buttons)

def get_proxy_packages_keyboard(prices):
    """
    Creates a keyboard with the available proxy packages for purchase.
    """
    buttons = []
    for price in prices:
        # callback_data will be like 'buy_package_7' for 7 days
        callback_data = f"buy_package_{price['duration_days']}"
        text = f"🌐 {price['duration_days']} Day(s) - {price['price_bdt']:.2f} BDT"
        buttons.append([InlineKeyboardButton(text, callback_data=callback_data)])

    buttons.append([get_back_button('main')])
    return InlineKeyboardMarkup(buttons)

def get_remove_payment_method_keyboard(methods):
    """
    Creates a keyboard for selecting a payment method to remove.
    """
    buttons = []
    for method in methods:
        text = f"🗑️ {method['name']}"
        buttons.append([InlineKeyboardButton(text, callback_data=f"admin_delete_method_{method['id']}")])

    buttons.append([get_back_button('main')])
    return InlineKeyboardMarkup(buttons)

def get_remove_price_keyboard(prices):
    """
    Creates a keyboard for selecting a price package to remove.
    """
    buttons = []
    for price in prices:
        text = f"🗑️ {price['duration_days']} Day(s) - {price['price_bdt']:.2f} BDT"
        buttons.append([InlineKeyboardButton(text, callback_data=f"admin_delete_price_{price['duration_days']}")])

    buttons.append([get_back_button('main')])
    return InlineKeyboardMarkup(buttons)

def get_remove_proxy_keyboard(proxies):
    """
    Creates a keyboard for selecting a proxy to remove.
    """
    buttons = []
    for proxy in proxies:
        status = "Assigned" if proxy['assigned_to'] else "Available"
        text = f"🗑️ {proxy['ip_port']} ({status})"
        buttons.append([InlineKeyboardButton(text, callback_data=f"admin_delete_proxy_{proxy['id']}")])

    buttons.append([get_back_button('main')])
    return InlineKeyboardMarkup(buttons)
