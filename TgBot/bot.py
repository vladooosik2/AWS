import asyncio                           # [1]
from os import getenv                    # [1]
from dotenv import load_dotenv

# pip install aiogram
from aiogram import Bot, Dispatcher      # [1]
from aiogram.types import Message        # [1]
from aiogram.filters import Command

# pip install google-genai
from google import genai

load_dotenv()

dp = Dispatcher()                        # [2]
client = genai.Client()

@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer("Let`s talk!")

@dp.message()                            # [3]
async def any_message(                   # [4]
        message: Message,                # [5]
):
    print(f"{message.from_user.full_name}: {message.text}")
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
    token = getenv("BOT_TOKEN")          # [7]
    if not token:                        # [7]
        error = "No token provided"      # [7]
        raise ValueError(error)          # [7]
    bot = Bot(token=token)               # [8]

    print("Starting bot...")
    try:
        await dp.start_polling(bot)      # [9]
    finally:
        print("Bot stopped")


if __name__ == '__main__':
    asyncio.run(main())