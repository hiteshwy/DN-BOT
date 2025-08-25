# 🚀 Discord VPS Bot (Docker + tmate)

A Discord bot that lets admins create and manage lightweight VPS containers (Ubuntu/Debian) with **tmate SSH sessions** — all from Discord.

---

## ✨ Features
- Deploy VPS with chosen **OS, RAM, CPU, expiry**
- Built on **Docker + tmate**
- Auto-expiry cleanup
- Rich **Discord embeds**
- System resource monitoring (`/node`)
- **User commands:** `/list`, `/start`, `/stop`, `/restart`, `/delete`, `/regen-ssh`, `/tips`, `/ping`, `/help`, `/node`
- **Admin commands:** `/deploy`, `/nodedmin`, `/delete-all`, `/sendvps`
- Supports **auto-start on reboot** via `systemctl`

---

## 📦 Full Setup Guide

```bash
# 1. Update system and install dependencies
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip docker.io git

# 2. Clone the repository (or place bot files somewhere safe)
git clone https://github.com/yourname/vps-bot.git
cd vps-bot

# 3. Install Python requirements
pip install -r requirements.txt

# 4. Edit bot config
nano vps_bot.py
# → Replace TOKEN with your bot token
# → Replace ADMIN_IDS with your Discord User ID(s)

# Example:
# TOKEN = "YOUR_DISCORD_BOT_TOKEN"
# ADMIN_IDS = {123456789012345678}

# 5. Build Docker images with tmate
docker build -t ubuntu-22.04-with-tmate -f Dockerfile.ubuntu .
docker build -t debian-with-tmate -f Dockerfile.debian .

# 6. Run the bot manually (for testing)
python3 vps_bot.py

# 7. (Optional) Setup systemctl service for auto-start
sudo nano /etc/systemd/system/vps-bot.service
