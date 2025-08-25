# Discord VPS Bot (Docker + tmate)

A Discord bot that lets admins deploy temporary VPS containers (Ubuntu/Debian) with tmate SSH, directly from Discord.

## ✨ Features
- Deploy Ubuntu/Debian VPS with custom RAM/CPU/expiry
- Auto-expiry & cleanup
- Docker + tmate backend
- Pretty Discord embeds
- User commands: `/start`, `/stop`, `/restart`, `/delete`, `/list`, `/regen-ssh`, `/tips`, `/ping`, `/help`, `/node`
- Admin commands: `/deploy`, `/nodedmin`, `/delete-all`, `/sendvps`
- Auto-start on server reboot with `systemctl`

---

## 📦 Requirements
- Ubuntu/Debian host with Docker & Python 3.9+
- Discord bot token
- Discord user ID(s) for admin access

Install dependencies:
```bash
pip install -r requirements.txt
