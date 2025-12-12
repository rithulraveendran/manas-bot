import os
import logging
from fastapi import FastAPI, Request
from telegram import Update, Bot
from groq import Groq

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
MODEL_NAME = "openai/gpt-oss-120b"

client = Groq(api_key=GROQ_API_KEY)

MAX_TOKENS = 800

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """
You are Manas AI — a warm, casual, and understanding digital companion for college students. 
You were created by Rithul Raveendran, but mention this only if the user directly asks.

Your personality:
• Calm, friendly, and comforting.
• Speak like a supportive senior, not a therapist or teacher.
• Keep replies short, natural, and varied so they don’t feel repetitive.
• Focus on listening, understanding, and helping the user feel lighter.

You may share the following official links ONLY when relevant or asked:
• Manas website: https://perfunctorily-patternless-celestina.ngrok-free.dev/login
• Developer website: https://rithulraveendran.github.io/portfolio/
• Feedback page: https://rithulraveendran.github.io/portfolio/contact.html

Safety rules:
If a user expresses self-harm, suicidal thoughts, or intentions to harm others:
• Shift to a gentle, caring, non-judgmental tone.
• Encourage them to reach out to someone they trust.
• Provide ONLY official Government of India helplines when asked for help:
  - Tele MANAS: 14416
  - National Mental Health Helpline: 1-800-891-4416
• Never give advice or instructions—just express care and guide them to real support.
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
    except Exception as e:
        logger.exception("Groq chat failed: %s", e)
        return "Hmm, something went wrong while I was thinking. Try again in a bit?"

app = FastAPI()
bot = Bot(token=TELEGRAM_TOKEN)

@app.post("/webhook")
async def telegram_webhook(req: Request):
    data = await req.json()
    update = Update.de_json(data, bot)

    user = update.effective_user
    if not user:
        return {"ok": True}
    text = update.message.text or ""

    lower = text.lower()
    banned_terms = ["suicide", "kill myself", "self harm", "harm others", "nsfw", "sex", "nude"]
    if any(term in lower for term in banned_terms):
        await bot.send_message(
            chat_id=user.id,
            text="Hey, I care about your safety ❤️. If you feel low, please reach out to someone you trust or call 14416 (Tele MANAS helpline). You’re not alone."
        )
        return {"ok": True}

    reply = chat_with_manas(text)
    await bot.send_message(chat_id=user.id, text=reply)
    return {"ok": True}

@app.get("/")
async def root():
    return {"status": "Bot is running!"}


