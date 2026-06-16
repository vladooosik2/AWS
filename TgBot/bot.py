import asyncio                           # [1]
from os import getenv                    # [1]
from dotenv import load_dotenv

# pip install aiogram
from aiogram import Bot, Dispatcher      # [1]
from aiogram.types import Message        # [1]
from aiogram.filters import Command

# pip install google-genai
from google import genai

import requests

dp = Dispatcher()                        # [2]
client = None
bot = None

# Підключення до telegram-бота
def auth_telegram():
    token = getenv("BOT_TOKEN")  # [7]
    if not token:  # [7]
        error = "No token provided"  # [7]
        raise ValueError(error)  # [7]
    return Bot(token=token)  # [8]

# Підключення Gemini API
def auth_gemini_api():
    api_key = getenv("GEMINI_API_KEY")
    if not api_key:
        print("No GEMINI_API_KEY provided. Running without Gemini API")
        return None
    try:
        return genai.Client()
    except Exception:
        print("Can`t connect to Gemini API. Running without one.")
    return None

# Обробник команди /start
@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer("Let`s talk, dude!")

# Обробник команди /meowfact
@dp.message(Command("meowfact"))
async def cmd_meowfact(message: Message):
    args = message.text.split()[1:]
    count = 1
    if len(args) > 0:
        count = int(args[0])
    response = requests.get("https://meowfacts.herokuapp.com/", {"count": count})
    if response.ok:
        facts = response.json()['data']
        await message.answer("\n\n".join(facts))
    else:
        await message.answer("Something wrong!")

# Обробних всіх інших повідомлень
@dp.message()                            # [3]
async def any_message(                   # [4]
        message: Message,                # [5]
):
    print(f"{message.from_user.full_name}: {message.text}")
    if client is None:
        await message.answer("Hello world!")
    else:
        try:
            response = client.models.generate_content(
                model="gemini-3.5-flash",
                contents=message.text,
            )
        except Exception as err:
            print(f"{type(err)}: {err}")
            await message.answer("Щось пішло не так")
        else:
            await message.answer(str(response.text)) # [6]


async def main():
    global bot, client

    load_dotenv()
    bot = auth_telegram()
    client = auth_gemini_api()

    print("Starting bot...")
    try:
        await dp.start_polling(bot)      # [9]
    finally:
        print("Bot stopped")


if __name__ == '__main__':
    asyncio.run(main())
