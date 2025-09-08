from telegram import Update
from telegram.ext import MessageHandler, CommandHandler, filters, ContextTypes
from shivu import application

from .guess import guess_text_handler, active_guesses
from .guess import start_anime_guess_cmd
from .guess import guessboard_cmd


# ====== All Text Messages Handler ====== #
async def all_text_messages_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    # Agar guess game chal rha hai to guesses handle kare
    if chat_id in active_guesses and active_guesses[chat_id].get("active", False):
        await guess_text_handler(update, context)


# ====== Register Handlers ====== #
application.add_handler(
    MessageHandler(filters.TEXT & ~filters.COMMAND, all_text_messages_handler, block=False)
)
application.add_handler(
    CommandHandler("nguess", start_anime_guess_cmd, block=False)
)
application.add_handler(
    CommandHandler("nboard", guessboard_cmd, block=False)
)
