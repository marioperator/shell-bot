# shell-bot
<img width="1536" height="1024" alt="image" src="https://github.com/user-attachments/assets/033346c2-6dce-4d26-b813-b37d1cfdefba" />

A Telegram bot that lets you run shell commands and scripts on a remote Linux machine.

## Features

- Send any shell command via Telegram and get the output back
- Add custom scripts as bot commands by dropping `.sh` files in the `commands/` folder
- Commands auto-register in the Telegram menu on every restart
- Graceful handling of interactive commands (htop, top, nano, etc.)

## Requirements

- Python 3.6+
- pip3

## Installation
```bash
git clone https://github.com/marioperator/shell-bot
cd shellbot
pip3 install python-telegram-bot==13.15 python-dotenv
cp .env.example .env
nano .env
mkdir commands
```

## Configuration

Edit `.env`:
```
TOKEN=your_telegram_bot_token
ALLOWED_USER_ID=your_telegram_user_id
```

- **TOKEN**: get it from [@BotFather](https://t.me/botfather) on Telegram
- **ALLOWED_USER_ID**: get it from [@userinfobot](https://t.me/userinfobot)

## Adding commands

Drop any `.sh` script in the `commands/` folder and restart the bot:
```bash
cp myscript.sh commands/
systemctl restart shellbot
```

The command will automatically appear in the Telegram menu.

## Run as a service

Copy the systemd service file and enable it:
```bash
cp shellbot.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable shellbot
systemctl start shellbot
```

## Usage

- Type any shell command directly in the chat → get the output
- Use `/help` or `/start` to list available script commands
- Interactive commands like `htop` are automatically replaced with non-interactive alternatives
