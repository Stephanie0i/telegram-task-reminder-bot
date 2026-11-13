# Telegram Task & Daily Reminder Bot

A lightweight, multi-user Telegram bot written in Python that helps users organize personal to-do lists, track task completion statistics, and receive scheduled daily reminder notifications.

## Key Features

- **Personalized Lists:** Each user maintains an isolated to-do list identified by their Telegram ID.
- **Task Management:** Add new tasks, mark completed items as DONE, and remove obsolete items.
- **Progress Tracking:** Calculate your completion rate and view structured progress statistics.
- **Scheduled Reminders:** Configure automated daily reminders at a custom time with timezone support (`Africa/Algiers`).
- **Persistent Storage:** Tasks and reminder preferences persist safely across bot reboots in JSON format.
- <img width="877" height="1024" alt="image" src="https://github.com/user-attachments/assets/93d581cc-7409-436a-b73c-a8d972885af1" />
<img width="869" height="929" alt="image" src="https://github.com/user-attachments/assets/c5c414ce-a7c8-4822-9077-4cff8ee24fc9" />



## Available Commands

| Command | Description |
| :--- | :--- |
| `/start` | Welcome message and summary of available commands |
| `/add <task>` | Append a new task to your active TODO list |
| `/done <task>` | Mark an existing task as completed and move to DONE |
| `/remove <task>` | Delete a task from either list |
| `/tasks` | Display your current TODO and DONE lists |
| `/stats` | View total tasks and your completion percentage |
| `/remind <HH:MM>` | Schedule a daily task reminder (24-hour format) |
| `/ask` | AI assistant command (planned expansion) |

## Tech Stack

- **Language:** Python 3.10+
- **Framework:** `python-telegram-bot` (with JobQueue support)
- **Environment Management:** `python-dotenv`
- **Timezone Support:** `tzdata` / `zoneinfo`
- **Storage:** JSON persistence

## Getting Started

### 1. Clone the Repository
```bash
git clone https://github.com/Stephanie0i/telegram-task-reminder-bot.git
cd telegram-task-reminder-bot
```

### 2. Set Up Virtual Environment & Dependencies
```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux / macOS:
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Configure Secrets
Create a `.env` file in the root directory (refer to `.env.example`):
```env
TOKEN=your_bot_token_from_botfather
ID=your_telegram_user_id
```

> **Security Note:** Never commit your `.env` file or bot tokens to version control.

### 4. Run the Bot
```bash
python bot.py
```

## Deployment Notes

This bot is configured to run continuously on a cloud host (such as Wispbyte, VPS, or cloud container):
1. Deploy `bot.py`, `requirements.txt`, and dependencies.
2. Supply `TOKEN` and `ID` securely via environment variables or secret store.
3. Start `bot.py` as a managed system service or background worker.

