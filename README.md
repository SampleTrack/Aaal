# Telegram Group Manager Bot 🛡️

A high-performance, asynchronous Telegram Group Management bot built with **Pyrogram** and **Motor** (MongoDB). This bot features a freemium architecture, offering basic moderation for free while locking advanced automation behind a **Telegram Stars** paywall.

Designed specifically for deployment on **Render's Free Web Service** tier using an `aiohttp` port-binding workaround to prevent timeout crashes.

---

## 🚀 Features

### Free Tier (Core Moderation)
* **Execution Commands:** `/ban`, `/mute`, `/kick` strictly locked to group administrators.
* **Smart Warn System:** `/warn` command that tracks offenses in MongoDB and automatically bans users upon reaching the configured threshold.
* **Anti-Link Filter:** Automatically deletes unauthorized URLs from standard users.
* **Welcome Engine:** Customizable, variable-injected welcome messages for new members.

### Premium Tier (Unlocked via Telegram Stars)
* **Automated Payments:** Fully integrated with Telegram Stars (`XTR`). Generates invoices and processes `successful_payment` updates automatically.
* **Captcha Verification:** Strips permissions from new users and forces them to solve a dynamic math problem within 60 seconds before they can speak.
* **Time-Based Expiration:** Database automatically tracks premium subscription length (30 days) and restricts feature access upon expiration.

---

## 🛠️ Architecture & Tech Stack

* **Framework:** Pyrogram (MTProto API)
* **Language:** Python 3.10+
* **Database:** MongoDB (Motor Asyncio)
* **Web Server:** aiohttp (Dummy server for Render port-binding)
* **Encryption:** TgCrypto (For high-speed Pyrogram execution)

---

## ⚙️ Environment Variables

Your deployment will fail if these are not set. Create a `.env` file locally, or paste these into your Render Environment Variables dashboard.

| Variable | Description |
|---|---|
| `API_ID` | Your Telegram API ID from my.telegram.org |
| `API_HASH` | Your Telegram API Hash from my.telegram.org |
| `BOT_TOKEN` | Your Bot Token from @BotFather |
| `MONGO_URI` | Your MongoDB connection string |
| `PORT` | (Render sets this automatically) Usually 8080 |
| `PREMIUM_PRICE_STARS` | Cost of the 30-day premium upgrade (Default: 250) |

---

## 🚀 Deployment Guide (Render)

This bot is configured to run on Render's Web Service tier, not a Background Worker, saving you money. 

1. **Fork or Clone** this repository to your GitHub account.
2. Log into **Render.com** and create a new **Web Service**.
3. Connect your repository.
4. **Build Command:** `pip install -r requirements.txt`
5. **Start Command:** `python main.py`
6. Add your Environment Variables.
7. Click **Deploy**.

**Anti-Sleep Hack:** Render puts free web services to sleep after 15 minutes of inactivity. To keep your bot running 24/7, copy your Render URL (e.g., `https://your-bot-name.onrender.com`) and set up a free ping using [cron-job.org](https://cron-job.org/) to visit the URL every 14 minutes.

---

## 📂 Project Structure

* `/database` - Motor client and MongoDB schema enforcement.
* `/plugins` - Modular Pyrogram handlers (Moderation, Filters, Payments, Captcha).
* `/utils` - Helper scripts (Admin verification).
* `main.py` - Entry point containing the Pyrogram client and the aiohttp web server.
* `config.py` - Centralized environment variable parsing.

---

## 📝 License & Contact

Built by [Your Name/Handle Here].
