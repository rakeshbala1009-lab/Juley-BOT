#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# --- Install Dependencies ---
echo "Installing dependencies from requirements.txt..."
pip install -r requirements.txt

# --- Run the Bot ---
echo "Starting the Telegram bot..."
python main.py
