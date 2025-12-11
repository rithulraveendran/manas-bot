import os
import logging
from fastapi import FastAPI, Request
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, ContextTypes
from groq import Groq

# ---------------- Configuration ----------------
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
MODEL_NAME = "openai/gpt-oss-120b"

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

# ---------------- Groq Chat ----------------
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
    except Exception as e:
        logger.exception("Groq chat failed: %s", e)
        return "Hmm, something went wrong while I was thinking. Try again in a bit?"

# ---------------- FastAPI App ----------------
app = FastAPI()
bot = Bot(token=TELEGRAM_TOKEN)

@app.post("/webhook")
async def telegram_webhook(req: Request):
    data = await req.json()
    update = Update.de_json(data, bot)

    user = update.effective_user
    if not user:
        return {"ok": True}
    user_id = user.id
    text = update.message.text or ""

    # cooldown
    import time
    now = time.time()
    last = last_request_at.get(user_id, 0)
    if now - last < USER_COOLDOWN_SECONDS:
        remaining = USER_COOLDOWN_SECONDS - (now - last)
        await bot.send_message(chat_id=user.id, text=f"Slow down 😅 Try again in {int(remaining)+1}s.")
        return {"ok": True}
    last_request_at[user_id] = now

    # banned words
    lower = text.lower()
    banned_terms = ["suicide", "kill myself", "self harm", "harm others", "nsfw", "sex", "nude"]
    if any(term in lower for term in banned_terms):
        await bot.send_message(
            chat_id=user.id,
            text="Hey, I care about your safety ❤️. If you feel low, please reach out to someone you trust or call 14416 (Tele MANAS helpline). You’re not alone."
        )
        return {"ok": True}

    # normal chat
    reply = chat_with_manas(text)
    await bot.send_message(chat_id=user.id, text=reply)
    return {"ok": True}

@app.get("/")
async def root():
    return {"status": "Bot is running!"}
