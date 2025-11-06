Telegram Test Bot (Admin-created tests)

Overview
 - Admin can create a set of tests (default 30) using /admin. For each question admin sends the question text and then the four options. Put parentheses around the correct option's text when sending options so the bot can detect which is correct. The bot stores tests in a JSON file.
 - Users start with /start and answer questions using inline buttons (a/b/c/d). The bot checks answers and at the end shows total correct and incorrect counts.

Setup
1. Create a virtualenv and install dependencies:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Create environment variables (zsh example):
```bash
export BOT_TOKEN="<your-telegram-bot-token>"
export ADMIN_ID="<your-telegram-user-id>"
```

ADMIN_ID should be your Telegram numeric user id so only you can use /admin.

Run
```bash
python3 bot.py
```

Admin usage
- Send /admin to the bot (from the admin account). You'll see buttons: Create Tests, Delete All Tests, Cancel.
- Create Tests will ask how many questions to create (default 30). Then it asks Question 1 text, then the options as four lines starting with a), b), c), d). Put parentheses around the correct option's text. Example:

a) 30
b) 25
c) (29)
d) 27

The bot will parse and save tests. Repeat for the next questions until done.

User usage
- Any user can send /start to take the test. The bot will serve saved questions, accept answers via buttons, and at the end report counts.

Storage
- Tests: data/tests.json
- User progress: data/users/<user_id>.json

Notes
- This is a minimal implementation. For production, consider using a DB and securing admin access differently.
