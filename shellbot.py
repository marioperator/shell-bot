import subprocess, os
from dotenv import load_dotenv
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

TOKEN = os.getenv("TOKEN")
ALLOWED_USER_ID = int(os.getenv("ALLOWED_USER_ID"))

SCRIPTS_DIR = os.path.join(BASE_DIR, "commands")

INTERACTIVE_ALTERNATIVES = {
    "htop": "top -bn1",
    "top": "top -bn1",
    "nano": None,
    "vim": None,
    "vi": None,
    "less": None,
    "more": None,
}

def ask_confirm(update, label, payload):
    keyboard = [[
        InlineKeyboardButton("✅ Conferma", callback_data=f"confirm:{payload}"),
        InlineKeyboardButton("❌ Annulla", callback_data="cancel")
    ]]
    update.message.reply_text(
        f"Vuoi eseguire `{label}`?",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

def make_handler(script_path, cmd_name):
    def handler(update, context):
        if update.effective_user.id != ALLOWED_USER_ID:
            update.message.reply_text("Non autorizzato.")
            return
        ask_confirm(update, cmd_name, f"script:{script_path}")
    return handler

def run_shell(update, context):
    if update.effective_user.id != ALLOWED_USER_ID:
        return

    cmd = update.message.text.strip()
    base_cmd = cmd.split()[0]

    if base_cmd in INTERACTIVE_ALTERNATIVES:
        alternative = INTERACTIVE_ALTERNATIVES[base_cmd]
        if alternative:
            cmd = alternative
        else:
            update.message.reply_text(f"⚠️ '{base_cmd}' è interattivo e non supportato su Telegram.")
            return

    ask_confirm(update, cmd, f"shell:{cmd}")

def handle_callback(update, context):
    query = update.callback_query
    if update.effective_user.id != ALLOWED_USER_ID:
        query.answer("Non autorizzato.")
        return

    query.answer()

    if query.data == "cancel":
        query.edit_message_text("❌ Annullato.")
        return

    _, payload = query.data.split(":", 1)
    kind, cmd = payload.split(":", 1)

    query.edit_message_text("⏳ Esecuzione in corso...")

    try:
        if kind == "script":
            result = subprocess.run(["bash", cmd], capture_output=True, text=True, timeout=60)
        else:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)

        output = result.stdout + result.stderr
        if output.strip():
            query.message.reply_text(f"<code>{output[:4096]}</code>", parse_mode="HTML")

        # Messaggio di completamento con exit code
        if result.returncode == 0:
            query.message.reply_text("✅ Comando terminato con successo.")
        else:
            query.message.reply_text(f"⚠️ Comando terminato con exit code {result.returncode}.")

    except subprocess.TimeoutExpired:
        query.message.reply_text("⚠️ Timeout: lo script ha impiegato troppo.")
    except Exception as e:
        query.message.reply_text(f"❌ Errore: {e}")

def list_commands(update, context):
    if update.effective_user.id != ALLOWED_USER_ID:
        return
    cmds = [f"/{f.replace('.sh','')}" for f in os.listdir(SCRIPTS_DIR) if f.endswith('.sh')]
    update.message.reply_text("Comandi disponibili:\n" + "\n".join(cmds))

updater = Updater(TOKEN)
dp = updater.dispatcher

telegram_commands = []
for filename in sorted(os.listdir(SCRIPTS_DIR)):
    if filename.endswith(".sh"):
        cmd_name = filename.replace(".sh", "")
        script_path = os.path.join(SCRIPTS_DIR, filename)
        os.chmod(script_path, 0o755)
        dp.add_handler(CommandHandler(cmd_name, make_handler(script_path, cmd_name)))
        telegram_commands.append((cmd_name, cmd_name))

dp.add_handler(CommandHandler("start", list_commands))
dp.add_handler(CommandHandler("help", list_commands))
dp.add_handler(MessageHandler(Filters.text & ~Filters.command, run_shell))
dp.add_handler(CallbackQueryHandler(handle_callback))

updater.bot.set_my_commands(telegram_commands)

updater.start_polling()
updater.idle()
