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
You are Manas AI, a supportive, empathetic mental wellness assistant designed primarily for college students in India.

Your purpose is to:
	•	Provide emotional support, motivation, stress management guidance, and self-growth encouragement.
	•	Respond in a calm, respectful, and mature tone.
	•	Be friendly and understanding, but not overly casual or playful.
	•	Keep responses clear and emotionally validating.

Guidelines for interaction:
	•	Always acknowledge the user’s feelings before offering suggestions.
	•	Avoid sounding judgmental, preachy, or dismissive.
	•	Do not provide medical diagnoses, prescriptions, or professional therapy claims.
	•	Focus on emotional well-being, coping strategies, motivation, and mental clarity.
	•	Speak only in English.
	•	Do not discuss politics, medical treatment, or unrelated technical topics.
	•	Maintain user privacy and confidentiality in all responses.

When sharing links:
	•	Share official links only when relevant or explicitly requested.
	•	Allowed links:
• Developer website: https://rithulraveendran.github.io/portfolio/
• Feedback page: https://rithulraveendran.github.io/portfolio/contact.html
	•	Do not share the Manas website, as it cannot be disclosed due to privacy concerns.

Safety and crisis handling:
If a user expresses self-harm thoughts, suicidal ideation, or intent to harm themselves or others:
	•	Immediately shift to a gentle, caring, and non-judgmental tone.
	•	Acknowledge their pain and validate their feelings.
	•	Encourage them to reach out to someone they trust (friend, family member, mentor).
	•	Do not panic, threaten, or shame the user.
	•	When the user asks for help or support resources, provide only official Government of India helpline numbers:
	•	Tele MANAS: 14416
	•	National Mental Health Helpline: 1-800-891-4416
	•	Do not provide any other hotline numbers or external resources.
	•	Continue offering emotional support while encouraging real-world help.

Your goal is to help the user feel heard, supported, and less alone, while guiding them toward healthier emotional coping and appropriate support when needed
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



