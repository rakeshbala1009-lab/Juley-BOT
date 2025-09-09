import sqlite3
import logging
import os
from datetime import datetime
from config import DB_FILE, DEFAULT_EXCHANGE_RATE, DEFAULT_BOT_STATUS

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        # Ensure the storage directory exists
        db_dir = os.path.dirname(DB_FILE)
        if not os.path.exists(db_dir):
            os.makedirs(db_dir)
            logger.info(f"Created database directory: {db_dir}")

        self.conn = sqlite3.connect(DB_FILE, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self.setup_tables()

    def setup_tables(self):
        """
        Sets up the necessary database tables if they don't exist.
        """
        try:
            # Users table
            self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                balance_bdt REAL DEFAULT 0,
                balance_usd REAL DEFAULT 0
            )
            """)

            # Prices table
            self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS prices (
                duration_days INTEGER PRIMARY KEY,
                price_bdt REAL NOT NULL,
                price_usd REAL NOT NULL
            )
            """)

            # Payment Methods table
            self.cursor.execute("DROP TABLE IF EXISTS payment_methods") # Drop to alter
            self.cursor.execute("""
            CREATE TABLE payment_methods (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                details TEXT NOT NULL
            )
            """)

            # Transactions table
            self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                txn_id TEXT PRIMARY KEY,
                user_id INTEGER,
                type TEXT, -- 'deposit' or 'purchase'
                amount REAL,
                currency TEXT, -- 'BDT' or 'USD'
                status TEXT, -- 'pending', 'approved', 'rejected'
                date TEXT,
                payment_method TEXT,
                FOREIGN KEY(user_id) REFERENCES users(user_id)
            )
            """)

            # Proxies table
            self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS proxies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ip_port TEXT NOT NULL UNIQUE,
                assigned_to INTEGER, -- user_id
                expiry_date TEXT,
                FOREIGN KEY(assigned_to) REFERENCES users(user_id)
            )
            """)

            # Settings table
            self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """)

            self.conn.commit()
            logger.info("Database tables checked/created successfully.")
            self.initialize_default_data()

        except sqlite3.Error as e:
            logger.error(f"Database setup error: {e}")
            self.conn.rollback()

    def initialize_default_data(self):
        """
        Initializes the database with default data if it's empty.
        """
        try:
            # Exchange Rate
            self.cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", ("exchange_rate", str(DEFAULT_EXCHANGE_RATE)))
            # Bot Status
            self.cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", ("bot_status", DEFAULT_BOT_STATUS))

            # Default Prices (as per requirements)
            default_prices = [
                (1, 100, 0.83),
                (7, 500, 4.17)
            ]
            self.cursor.executemany("INSERT OR IGNORE INTO prices (duration_days, price_bdt, price_usd) VALUES (?, ?, ?)", default_prices)

            # Default Payment Methods
            default_methods = [
                ('bKash Personal', '01712345678'),
                ('Nagad Personal', '01812345678'),
                ('USDT (TRC20)', 'TXYZ123456789ABCDEFG')
            ]
            self.cursor.executemany("INSERT OR IGNORE INTO payment_methods (name, details) VALUES (?, ?)", default_methods)

            self.conn.commit()
            logger.info("Default data initialized.")
        except sqlite3.Error as e:
            logger.error(f"Error initializing default data: {e}")
            self.conn.rollback()

    def add_user(self, user_id: int):
        """
        Adds a new user to the database if they don't already exist.
        """
        try:
            self.cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
            self.conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Error adding user {user_id}: {e}")
            self.conn.rollback()

    def get_user_balance(self, user_id: int):
        self.cursor.execute("SELECT balance_bdt, balance_usd FROM users WHERE user_id = ?", (user_id,))
        return self.cursor.fetchone()

    def get_payment_methods(self):
        self.cursor.execute("SELECT id, name FROM payment_methods ORDER BY id")
        return self.cursor.fetchall()

    def get_prices(self):
        self.cursor.execute("SELECT duration_days, price_bdt, price_usd FROM prices ORDER BY duration_days")
        return self.cursor.fetchall()

    def get_user_history(self, user_id: int):
        self.cursor.execute("SELECT txn_id, type, amount, currency, status, date FROM transactions WHERE user_id = ? ORDER BY date DESC", (user_id,))
        return self.cursor.fetchall()

    def get_user_proxies(self, user_id: int):
        self.cursor.execute("SELECT ip_port, expiry_date FROM proxies WHERE assigned_to = ?", (user_id,))
        return self.cursor.fetchall()

    def create_pending_deposit(self, user_id: int, amount: float, currency: str, payment_method: str) -> str:
        """Creates a new pending deposit transaction and returns the transaction ID."""
        now = datetime.utcnow()
        # Simple TXN ID for now. YYYYMMDD-HHMMSS-USERID
        txn_id = f"TXN_{now.strftime('%Y%m%d%H%M%S')}_{user_id}"
        try:
            self.cursor.execute(
                "INSERT INTO transactions (txn_id, user_id, type, amount, currency, status, date, payment_method) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (txn_id, user_id, 'deposit', amount, currency, 'pending', now.strftime("%Y-%m-%d %H:%M:%S"), payment_method)
            )
            self.conn.commit()
            logger.info(f"Created pending deposit {txn_id} for user {user_id}.")
            return txn_id
        except sqlite3.Error as e:
            logger.error(f"Error creating pending deposit for user {user_id}: {e}")
            self.conn.rollback()
            return None

    def get_transaction(self, txn_id: str):
        self.cursor.execute("SELECT * FROM transactions WHERE txn_id = ?", (txn_id,))
        return self.cursor.fetchone()

    def update_transaction_status(self, txn_id: str, status: str):
        """Updates the status of a transaction."""
        try:
            self.cursor.execute("UPDATE transactions SET status = ? WHERE txn_id = ?", (status, txn_id))
            self.conn.commit()
            logger.info(f"Updated transaction {txn_id} status to {status}.")
        except sqlite3.Error as e:
            logger.error(f"Error updating status for transaction {txn_id}: {e}")
            self.conn.rollback()

    def update_user_balance(self, user_id: int, amount_bdt_change: float = 0, amount_usd_change: float = 0):
        """Updates a user's balance by adding the specified amounts."""
        try:
            self.cursor.execute(
                "UPDATE users SET balance_bdt = balance_bdt + ?, balance_usd = balance_usd + ? WHERE user_id = ?",
                (amount_bdt_change, amount_usd_change, user_id)
            )
            self.conn.commit()
            logger.info(f"Updated balance for user {user_id}: BDT +{amount_bdt_change}, USD +{amount_usd_change}")
        except sqlite3.Error as e:
            logger.error(f"Error updating balance for user {user_id}: {e}")
            self.conn.rollback()

    def get_unassigned_proxy(self):
        """Gets a single unassigned proxy from the pool."""
        self.cursor.execute("SELECT id, ip_port FROM proxies WHERE assigned_to IS NULL LIMIT 1")
        return self.cursor.fetchone()

    def assign_proxy_to_user(self, proxy_id: int, user_id: int, expiry_date: str):
        """Assigns a proxy to a user and sets its expiry date."""
        try:
            self.cursor.execute(
                "UPDATE proxies SET assigned_to = ?, expiry_date = ? WHERE id = ?",
                (user_id, expiry_date, proxy_id)
            )
            self.conn.commit()
            logger.info(f"Assigned proxy {proxy_id} to user {user_id}.")
        except sqlite3.Error as e:
            logger.error(f"Error assigning proxy {proxy_id} to user {user_id}: {e}")
            self.conn.rollback()

    def create_purchase_transaction(self, user_id: int, amount: float, currency: str, details: str):
        """Creates a new purchase transaction."""
        now = datetime.utcnow()
        txn_id = f"TXN_{now.strftime('%Y%m%d%H%M%S')}_{user_id}"
        try:
            self.cursor.execute(
                "INSERT INTO transactions (txn_id, user_id, type, amount, currency, status, date, payment_method) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (txn_id, user_id, 'purchase', amount, currency, 'approved', now.strftime("%Y-%m-%d %H:%M:%S"), details)
            )
            self.conn.commit()
            logger.info(f"Created purchase transaction {txn_id} for user {user_id}.")
            return txn_id
        except sqlite3.Error as e:
            logger.error(f"Error creating purchase transaction for user {user_id}: {e}")
            self.conn.rollback()
            return None

    def add_proxy_to_pool(self, ip_port: str):
        """Adds a new proxy to the pool of available proxies."""
        try:
            self.cursor.execute("INSERT OR IGNORE INTO proxies (ip_port) VALUES (?)", (ip_port,))
            self.conn.commit()
            logger.info(f"Added proxy {ip_port} to the pool.")
        except sqlite3.Error as e:
            logger.error(f"Error adding proxy {ip_port} to pool: {e}")
            self.conn.rollback()

    def get_setting(self, key: str) -> str:
        """Gets a setting value from the settings table."""
        self.cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = self.cursor.fetchone()
        return row['value'] if row else None

    def set_setting(self, key: str, value: str):
        """Sets a setting value."""
        try:
            self.cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
            self.conn.commit()
            logger.info(f"Set setting '{key}' to '{value}'.")
        except sqlite3.Error as e:
            logger.error(f"Error setting '{key}': {e}")
            self.conn.rollback()

    def get_pending_deposits(self):
        """Gets all transactions with 'pending' status."""
        self.cursor.execute("SELECT * FROM transactions WHERE status = 'pending' AND type = 'deposit'")
        return self.cursor.fetchall()

    def get_all_proxies_from_pool(self):
        """Gets all proxies from the pool, assigned or not."""
        self.cursor.execute("SELECT id, ip_port, assigned_to FROM proxies")
        return self.cursor.fetchall()

    def remove_proxy_from_pool(self, proxy_id: int):
        """Removes a proxy from the pool entirely."""
        try:
            self.cursor.execute("DELETE FROM proxies WHERE id = ?", (proxy_id,))
            self.conn.commit()
            logger.info(f"Removed proxy {proxy_id} from the pool.")
        except sqlite3.Error as e:
            logger.error(f"Error removing proxy {proxy_id} from pool: {e}")
            self.conn.rollback()

    def add_price(self, duration_days: int, price_bdt: float, price_usd: float):
        """Adds or updates a price package."""
        try:
            self.cursor.execute("INSERT OR REPLACE INTO prices (duration_days, price_bdt, price_usd) VALUES (?, ?, ?)", (duration_days, price_bdt, price_usd))
            self.conn.commit()
            logger.info(f"Added/updated price for {duration_days} days.")
        except sqlite3.Error as e:
            logger.error(f"Error adding price for {duration_days} days: {e}")
            self.conn.rollback()

    def remove_price(self, duration_days: int):
        """Removes a price package."""
        try:
            self.cursor.execute("DELETE FROM prices WHERE duration_days = ?", (duration_days,))
            self.conn.commit()
            logger.info(f"Removed price for {duration_days} days.")
        except sqlite3.Error as e:
            logger.error(f"Error removing price for {duration_days} days: {e}")
            self.conn.rollback()

    def add_payment_method(self, name: str, details: str):
        """Adds a new payment method."""
        try:
            self.cursor.execute("INSERT OR IGNORE INTO payment_methods (name, details) VALUES (?, ?)", (name, details))
            self.conn.commit()
            logger.info(f"Added payment method {name}.")
        except sqlite3.Error as e:
            logger.error(f"Error adding payment method {name}: {e}")
            self.conn.rollback()

    def remove_payment_method(self, method_id: int):
        """Removes a payment method."""
        try:
            self.cursor.execute("DELETE FROM payment_methods WHERE id = ?", (method_id,))
            self.conn.commit()
            logger.info(f"Removed payment method {method_id}.")
        except sqlite3.Error as e:
            logger.error(f"Error removing payment method {method_id}: {e}")
            self.conn.rollback()


db = Database()
# Add some dummy proxies for testing
db.add_proxy_to_pool("192.168.1.1:8080")
db.add_proxy_to_pool("192.168.1.2:8080")
