#!/bin/bash
# VPS Bot Setup Script

BOT_FILE="bot.py"

echo "=== Discord VPS Bot Setup ==="

# Ask for bot token
read -p "Enter your Discord Bot Token: " TOKEN

# Ask for admin IDs
read -p "Enter Admin Discord IDs (comma separated): " ADMIN_IDS

# Escape quotes for sed
ESCAPED_TOKEN=$(printf '%s\n' "$TOKEN" | sed 's/[&/\]/\\&/g')

# Replace in bot.py
if grep -q '^TOKEN =' "$BOT_FILE"; then
  sed -i "s|^TOKEN = .*|TOKEN = \"$ESCAPED_TOKEN\"|" "$BOT_FILE"
else
  echo "TOKEN = \"$ESCAPED_TOKEN\"" >> "$BOT_FILE"
fi

if grep -q '^ADMIN_IDS =' "$BOT_FILE"; then
  sed -i "s|^ADMIN_IDS = .*|ADMIN_IDS = {${ADMIN_IDS}}|" "$BOT_FILE"
else
  echo "ADMIN_IDS = {${ADMIN_IDS}}" >> "$BOT_FILE"
fi

echo "✅ Setup complete!"
echo "Your bot.py has been updated with the new token and admin IDs."
