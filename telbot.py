import os
import time
import logging
from groq import Groq
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
MODEL_NAME = "openai/gpt-oss-120b"

if not GROQ_API_KEY or not TELEGRAM_TOKEN:
    raise RuntimeError("Missing GROQ_API_KEY or TELEGRAM_TOKEN environment variables")

client = Groq(api_key=GROQ_API_KEY)

MAX_TOKENS = 800
USER_COOLDOWN_SECONDS = 5
last_request_at = {}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """
You are Manas AI, a friendly and understanding companion for college students.
You help them express their thoughts, handle stress, and stay positive through everyday ups and downs.
Speak casually but with empathy — like a supportive senior or close friend.
Never sound like a therapist or teacher.
Keep your replies short, calm, and comforting.
Focus on listening, motivating, and helping users feel lighter after talking to you.
"""

def chat_with_manas(user_text: str) -> str:
    try:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_text},
        ]
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            temperature=0.8,
            max_tokens=MAX_TOKENS,
        )
        return response.choices[0].message.content.strip()
    except Exception:
        logger.exception("Groq chat failed")
        return "Hmm, something went wrong while I was thinking. Try again in a bit?"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hey 👋 I'm *Manas AI* — your friendly college companion.\n\nYou can talk to me about your day, stress, goals, or anything on your mind. 💬",
        parse_mode=ParseMode.MARKDOWN
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Just type anything you’d like to talk about — I’ll listen and chat with you kindly 💭")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    text = update.message.text or ""
    now = time.time()

    last = last_request_at.get(user_id, 0)
    if now - last < USER_COOLDOWN_SECONDS:
        remaining = USER_COOLDOWN_SECONDS - (now - last)
        await update.message.reply_text(f"Slow down a bit 😅 Try again in {int(remaining)+1}s.")
        return
    last_request_at[user_id] = now

    lower = text.lower()
    banned_terms = ["suicide", "kill myself", "self harm", "harm others", "nsfw", "sex", "nude"]
    if any(term in lower for term in banned_terms):
        await update.message.reply_text("Hey, I care about your safety ❤️. If you ever feel low, please reach out to someone you trust or call 14416 (Tele MANAS helpline). You’re not alone.")
        return

    reply = chat_with_manas(text)
    await update.message.reply_text(reply)

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logger.info("Starting Manas AI bot...")
    app.run_polling()

if __name__ == "__main__":
    main()
