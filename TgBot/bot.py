import asyncio                           # [1]
from os import getenv                    # [1]
from dotenv import load_dotenv

# pip install aiogram
from aiogram import Bot, Dispatcher      # [1]
from aiogram.types import Message        # [1]
from aiogram.filters import Command      

dp = Dispatcher()                        # [2]


@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer("Let`s talk!")


@dp.message()
async def any_message(                  
        message: Message,                
):
    print(f"{message.from_user.full_name}: {message.text}")
    await message.answer("Hello world!") 

async def main():
    load_dotenv()
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