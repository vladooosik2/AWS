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
import random

from PromptBuilder import PromptBuilder
from TicTacToe import TicTacToe
from TicTacToeAI import TicTacToeAI

dp = Dispatcher()                        # [2]
client = None
bot = None
active_games = {}  # {user_id: TicTacToe instance}
ttt_ai = None

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

# Обробник команди /roll
@dp.message(Command("roll"))
async def cmd_roll(message: Message):
    args = message.text.split()[1:]
    if len(args) > 0:
        try:
            max_value = int(args[0])
        except ValueError:
            await message.answer("Будь ласка, надайте коректне число.")
            return
    else:
        max_value = 100

    roll_result = random.randint(1, max_value)
    await message.answer(f"Твій результат: {roll_result}")

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
        await message.answer("Щось пішло не так!")

# Обробник команди /play_ttt
@dp.message(Command("play_ttt"))
async def cmd_play_ttt(message: Message):
    try:
        user_id = message.from_user.id
        if user_id in active_games:
            await message.answer("Ви вже маєте активну гру! Завершіть її або введіть /quit_ttt")
            return

        if client is None:
            await message.answer("AI недоступна. Спробуйте пізніше.")
            return

        if ttt_ai is None:
            await message.answer("Помилка ініціалізації AI.")
            return

        game = TicTacToe()
        active_games[user_id] = game

        board_display = game.get_board_display()
        await message.answer(
            f"🎮 Крестики-нолики!\n\n"
            f"Ви грієте Х, я гаю O\n\n"
            f"{board_display}\n\n"
            f"Ваш хід! Введіть число від 1 до 9\n"
            f"Команда /quit_ttt щоб вийти"
        )
    except Exception as err:
        print(f"Error in play_ttt: {type(err).__name__}: {err}")
        await message.answer(f"Помилка: {err}")

# Обробник команди /quit_ttt
@dp.message(Command("quit_ttt"))
async def cmd_quit_ttt(message: Message):
    user_id = message.from_user.id
    if user_id in active_games:
        del active_games[user_id]
        await message.answer("Гру завершено.")
    else:
        await message.answer("Нема активної гри.")

# Обробних всіх інших повідомлень
@dp.message()                            # [3]
async def any_message(                   # [4]
        message: Message,                # [5]
):
    user_id = message.from_user.id
    print(f"{message.from_user.full_name}: {message.text}")

    # Перевіряємо, чи є активна гра
    if user_id in active_games:
        game = active_games[user_id]
        print(f"Game in progress for user {user_id}")
        try:
            move_num = int(message.text)
            print(f"User move: {move_num}")
            pos = game.is_valid_move(move_num)

            if pos is None:
                await message.answer(f"❌ Невалідний хід. Спробуйте ще раз.")
                return

            # Людина робить хід
            game.make_move(pos, game.human)
            game.update_game_state()

            if game.game_over:
                board_display = game.get_board_display()
                if game.winner == 'X':
                    await message.answer(f"🎉 Ви виграли!\n\n{board_display}")
                else:
                    await message.answer(f"🤖 Я виграв!\n\n{board_display}")
                del active_games[user_id]
                return

            # AI робить хід
            print("Getting AI move...")
            ai_move = await ttt_ai.get_ai_move(game)
            print(f"AI move result: {ai_move}")
            if ai_move is None:
                await message.answer("Помилка AI. Гру завершено.")
                del active_games[user_id]
                return

            game.make_move(ai_move - 1, game.ai)
            game.update_game_state()

            board_display = game.get_board_display()

            if game.game_over:
                if game.winner == 'O':
                    await message.answer(f"🤖 Я виграв!\n\n{board_display}")
                else:
                    await message.answer(f"🤝 Нічия!\n\n{board_display}")
                del active_games[user_id]
                return

            await message.answer(f"Мій хід: {ai_move}\n\n{board_display}\nВаш хід:")

        except ValueError:
            await message.answer("Введіть число від 1 до 9")
            return

    # Звичайне повідомлення (не гра)
    if client is None:
        await message.answer("Hello world!")
    else:
        try:
            prompt = PromptBuilder.simplePrompt(message.text)
            await message.answer(f"Запит: {prompt}")
            response = client.models.generate_content(
                model="gemini-3.5-flash",
                contents=prompt,
            )
        except Exception as err:
            print(f"{type(err)}: {err}")
            await message.answer("Щось пішло не так")
        else:
            await message.answer(str(response.text)) # [6]


async def main():
    global bot, client, ttt_ai

    load_dotenv()
    bot = auth_telegram()
    client = auth_gemini_api()
    ttt_ai = TicTacToeAI(client)

    print("Starting bot...")
    print(f"Client initialized: {client is not None}")
    print(f"AI initialized: {ttt_ai is not None}")
    try:
        await dp.start_polling(bot)      # [9]
    finally:
        print("Bot stopped")


if __name__ == '__main__':
    asyncio.run(main())
