import subprocess, os
from dotenv import load_dotenv
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

TOKEN = os.getenv("TOKEN")
ALLOWED_USER_ID = int(os.getenv("ALLOWED_USER_ID"))

SCRIPTS_DIR = os.path.join(BASE_DIR, "commands")

# Comandi interattivi e loro alternativa non interattiva
INTERACTIVE_ALTERNATIVES = {
    "htop": "top -bn1",
    "top": "top -bn1",
    "nano": None,
    "vim": None,
    "vi": None,
    "less": None,
    "more": None,
}

def make_handler(script_path):
    def handler(update, context):
        if update.effective_user.id != ALLOWED_USER_ID:
            update.message.reply_text("Non autorizzato.")
            return
        update.message.reply_text("⏳ Lancio lo script...")
        try:
            result = subprocess.run(
                ["bash", script_path],
                capture_output=True, text=True, timeout=60
            )
            output = result.stdout + result.stderr
            update.message.reply_text(output[:4096] or "(nessun output)")
        except subprocess.TimeoutExpired:
            update.message.reply_text("⚠️ Timeout.")
        except Exception as e:
            update.message.reply_text(f"❌ Errore: {e}")
    return handler

def run_shell(update, context):
    if update.effective_user.id != ALLOWED_USER_ID:
        return

    cmd = update.message.text.strip()
    base_cmd = cmd.split()[0]

    # Controlla se è un comando interattivo
    if base_cmd in INTERACTIVE_ALTERNATIVES:
        alternative = INTERACTIVE_ALTERNATIVES[base_cmd]
        if alternative:
            update.message.reply_text(f"⚠️ '{base_cmd}' è interattivo, uso '{alternative}'...")
            cmd = alternative
        else:
            update.message.reply_text(f"⚠️ '{base_cmd}' è interattivo e non supportato su Telegram.")
            return

    try:
        result = subprocess.run(
            cmd, shell=True,
            capture_output=True, text=True, timeout=30
        )
        output = result.stdout + result.stderr
        # Manda in chunks se l'output è lungo
        output = output[:4096] or "(nessun output)"
        update.message.reply_text(f"<code>{output}</code>", parse_mode="HTML")
    except subprocess.TimeoutExpired:
        update.message.reply_text("⚠️ Timeout.")
    except Exception as e:
        update.message.reply_text(f"❌ Errore: {e}")

def list_commands(update, context):
    if update.effective_user.id != ALLOWED_USER_ID:
        return
    cmds = [f"/{f.replace('.sh','')}" for f in os.listdir(SCRIPTS_DIR) if f.endswith('.sh')]
    update.message.reply_text("Comandi disponibili:\n" + "\n".join(cmds))

updater = Updater(TOKEN)
dp = updater.dispatcher

# Registra script come comandi
telegram_commands = []
for filename in sorted(os.listdir(SCRIPTS_DIR)):
    if filename.endswith(".sh"):
        cmd_name = filename.replace(".sh", "")
        script_path = os.path.join(SCRIPTS_DIR, filename)
        os.chmod(script_path, 0o755)
        dp.add_handler(CommandHandler(cmd_name, make_handler(script_path)))
        telegram_commands.append((cmd_name, cmd_name))

dp.add_handler(CommandHandler("start", list_commands))
dp.add_handler(CommandHandler("help", list_commands))

# Testo libero -> esegue come comando shell
dp.add_handler(MessageHandler(Filters.text & ~Filters.command, run_shell))

# Aggiorna menu Telegram
updater.bot.set_my_commands(telegram_commands)

updater.start_polling()
updater.idle()
