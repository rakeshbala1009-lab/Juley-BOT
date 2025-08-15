# 📢 Global Message Broadcaster

A Telegram bot that allows Admins to broadcast a custom message to all registered bot users.

## Core Functionalities

-   **/start**: Any user can start the bot to register and receive broadcast messages.
-   **/message**: Admins can initiate a broadcast to all registered users.
-   **/cancel**: Admins can cancel the broadcast process.

## Setup and Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```

2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment Variables:**
    -   Create a `.env` file in the root directory.
    -   Add your Telegram Bot Token and Admin User IDs to the `.env` file:
        ```
        TELEGRAM_BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN
        ADMIN_IDS=ADMIN_ID_1,ADMIN_ID_2
        ```
    -   You can get a bot token by talking to [@BotFather](https://t.me/BotFather) on Telegram.
    -   Admin IDs are the numerical Telegram user IDs of the users who are allowed to send broadcasts.

## Usage

1.  **Run the bot:**
    ```bash
    python main.py
    ```
    The bot will start polling for updates.

2.  **Register Users:**
    -   Any user can find the bot on Telegram and send the `/start` command. They will be registered to receive broadcasts.

3.  **Send a Broadcast (Admin only):**
    -   An admin sends the `/message` command.
    -   The bot will ask for the message to be sent.
    -   The admin sends the message text.
    -   The bot will send this message to all registered users and confirm the count to the admin.
    -   To abort, the admin can use the `/cancel` command.

## Project Structure

-   `main.py`: The main application file containing the bot's logic.
-   `requirements.txt`: A list of Python dependencies.
-   `.env`: Configuration file for secrets (not version controlled).
-   `storage/`: Directory for persistent data.
    -   `user_ids.txt`: A file to store the chat IDs of registered users.
-   `README.md`: This file.
