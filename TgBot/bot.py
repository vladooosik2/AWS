import asyncio
import os
import re
from os import getenv
from dotenv import load_dotenv

# pip install aiogram
from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    CallbackQuery,
)
from aiogram.filters import Command

# pip install google-genai
from google import genai

import aiohttp
import random
from bs4 import BeautifulSoup

from PromptBuilder import PromptBuilder
from TicTacToe import TicTacToe
from TicTacToeAI import TicTacToeAI
from db import DataBase

dp = Dispatcher()
client = None
bot = None
db = None
price_checker_task = None

try:
    test_db = DataBase("TestTable")
except Exception as err:
    print(f"{type(err)}: {err}")

active_games = {}
ttt_ai = None

# Telegram and Gemini initialization helpers
def auth_telegram():
    token = getenv('BOT_TOKEN')
    if not token:
        raise ValueError('No BOT_TOKEN provided')
    return Bot(token=token)


def auth_gemini_api():
    api_key = getenv('GEMINI_API_KEY')
    if not api_key:
        print('No GEMINI_API_KEY provided. Running without Gemini API')
        return None
    try:
        return genai.Client()
    except Exception:
        print('Can\'t connect to Gemini API. Running without one.')
        return None

PRICE_CHECK_INTERVAL_HOURS = float(getenv('PRICE_CHECK_INTERVAL_HOURS', '6'))
PRICE_CHECK_INTERVAL_MINUTES = os.getenv('PRICE_CHECK_INTERVAL_MINUTES')
PRICE_CHECK_INTERVAL_SECONDS = os.getenv('PRICE_CHECK_INTERVAL_SECONDS')

if PRICE_CHECK_INTERVAL_SECONDS is not None:
    PRICE_CHECK_INTERVAL = float(PRICE_CHECK_INTERVAL_SECONDS)
elif PRICE_CHECK_INTERVAL_MINUTES is not None:
    PRICE_CHECK_INTERVAL = float(PRICE_CHECK_INTERVAL_MINUTES) * 60
else:
    PRICE_CHECK_INTERVAL = PRICE_CHECK_INTERVAL_HOURS * 3600

USER_AGENT = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
    'AppleWebKit/537.36 (KHTML, like Gecko) '
    'Chrome/122.0.0.0 Safari/537.36'
)

@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "Hello! I can track product prices. Use /add_track <url> [target_price] or /my_tracks."
    )

@dp.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "Available commands:\n"
        "/start — start the bot\n"
        "/help — show this help\n"
        "/add_track <url> [target_price] — track a product\n"
        "/my_tracks — show your tracked products\n"
        "/db — show database info\n"
        "/roll [max] — roll a random number\n"
        "/meowfact [count] — get cat facts\n"
        "/play_ttt — start Tic-Tac-Toe\n"
        "/quit_ttt — quit the current game"
    )

@dp.message(Command("db"))
async def cmd_db(message: Message):
    try:
        await message.answer(str(test_db))
    except Exception as err:
        await message.answer(f"{type(err)}: {err}")

@dp.message(Command("add_track"))
async def cmd_add_track(message: Message):
    parts = message.text.strip().split(maxsplit=2)
    if len(parts) < 2:
        await message.answer("Usage: /add_track <url> [target_price]")
        return

    product_url = parts[1].strip()
    target_price = None
    if len(parts) == 3:
        try:
            target_price = float(parts[2].replace(',', '.'))
        except ValueError:
            await message.answer("Invalid target price format. Use a number.")
            return

    await message.answer("Checking product page, please wait...")
    try:
        product_info = await fetch_product_info(product_url)
    except Exception as err:
        await message.answer(f"Could not fetch product info: {err}")
        return

    current_price = product_info['price']
    if current_price is None:
        await message.answer(
            "Could not parse price from this page. Try another link or check the URL."
        )
        return

    if target_price is None:
        target_price = current_price

    try:
        item_id = db.add_tracked_product(
            message.from_user.id,
            product_url,
            product_info['name'],
            current_price,
            target_price,
        )
    except Exception as err:
        print(f"Error saving tracked product: {err}")
        await message.answer('Failed to save the product to the database.')
        return

    await message.answer(
        f"✅ Product added to tracking:\n"
        f"{product_info['name']}\n"
        f"Current price: {current_price}\n"
        f"Target price: {target_price}\n"
        f"ID: {item_id}"
    )

@dp.message(Command("my_tracks"))
async def cmd_my_tracks(message: Message):
    print(f"🔍 DEBUG: /my_tracks command received from user {message.from_user.id}")
    products = db.get_user_tracked_products(message.from_user.id)
    if not products:
        await message.answer("You have no tracked products.")
        return

    text_lines = ["Your tracked products:"]
    inline_keyboard = []
    for item in products:
        text_lines.append(
            f"ID {item['id']}: {item['product_name']}\n"
            f"Price {item['current_price']} -> {item['target_price']}\n"
            f"{item['product_url']}"
        )
        inline_keyboard.append([
            InlineKeyboardButton(
                text=f"🗑 Delete {item['id']}",
                callback_data=f"delete_track:{item['id']}",
            )
        ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=inline_keyboard)
    await message.answer("\n\n".join(text_lines), reply_markup=keyboard)
    print(f"✅ /my_tracks response sent")

@dp.callback_query(lambda query: query.data and query.data.startswith('delete_track:'))
async def callback_delete_track(callback: CallbackQuery):
    data = callback.data.split(':')
    if len(data) != 2:
        await callback.answer('Invalid callback data.', show_alert=True)
        return

    try:
        item_id = int(data[1])
    except ValueError:
        await callback.answer('Invalid product ID.', show_alert=True)
        return

    if db.remove_tracked_product(item_id, callback.from_user.id):
        await callback.answer('Product removed successfully.')
        try:
            await callback.message.edit_text('Update the list using /my_tracks')
        except Exception:
            pass
    else:
        await callback.answer('Could not find or delete this product.', show_alert=True)

async def fetch_product_info(product_url: str) -> dict:
    if not product_url.startswith(('http://', 'https://')):
        raise ValueError('URL must start with http:// or https://')

    timeout = aiohttp.ClientTimeout(total=20)
    headers = {'User-Agent': USER_AGENT}
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(product_url, headers=headers) as response:
            if response.status != 200:
                raise ValueError(f'Page returned status {response.status}')
            text = await response.text()

    soup = BeautifulSoup(text, 'html.parser')
    name = None
    if soup.title and soup.title.string:
        name = soup.title.string.strip()
    if not name:
        h1 = soup.find('h1')
        if h1:
            name = h1.get_text(strip=True)
    if not name:
        name = product_url

    price_text = None
    selectors = [
        'meta[itemprop="price"]',
        'meta[property="product:price:amount"]',
        'span[class*="price"]',
        'div[class*="price"]',
        'p[class*="price"]',
        'span[class*="product-price"]',
        'div[class*="product-card__price"]',
    ]
    for selector in selectors:
        tag = soup.select_one(selector)
        if tag:
            price_text = tag.get('content') if tag.has_attr('content') else tag.get_text()
            if price_text:
                break

    if not price_text:
        candidates = ' '.join(
            tag.get_text(separator=' ', strip=True)
            for tag in soup.find_all(['span', 'div', 'p'])
        )
        currency_search = re.search(
            r'([\d\s.,]+)\s*(грн|uah|₴|rub|руб|usd)?',
            candidates,
            re.IGNORECASE,
        )
        if currency_search:
            price_text = currency_search.group(1)

    price = parse_price(price_text) if price_text else None
    return {'name': name, 'price': price}


def parse_price(price_text: str) -> float:
    if not price_text:
        raise ValueError('Price is missing')

    cleaned = re.sub(r'[^\d,\.]+', '', price_text)
    if not cleaned:
        raise ValueError('Could not clean price string')

    if cleaned.count(',') > 1 and cleaned.count('.') == 0:
        cleaned = cleaned.replace(',', '')
    elif cleaned.count('.') > 1 and cleaned.count(',') == 0:
        cleaned = cleaned.replace('.', '')
    elif cleaned.count(',') == 1 and cleaned.count('.') == 0:
        cleaned = cleaned.replace(',', '.')
    elif cleaned.count(',') > 0 and cleaned.count('.') > 0:
        if cleaned.rfind(',') > cleaned.rfind('.'):
            cleaned = cleaned.replace('.', '').replace(',', '.')
        else:
            cleaned = cleaned.replace(',', '')

    try:
        return float(cleaned)
    except ValueError as err:
        raise ValueError(f'Could not parse price: {price_text}') from err

async def check_price_updates():
    products = db.get_all_tracked_products()
    if not products:
        return

    for item in products:
        try:
            product_info = await fetch_product_info(item['product_url'])
        except Exception as err:
            print(f"Could not check {item['product_url']}: {err}")
            continue

        if product_info['price'] is None:
            continue

        old_price = item['current_price']
        new_price = product_info['price']
        if new_price != old_price:
            db.update_product_price(item['id'], new_price)
            title = '🔔 Price changed!'
            if item['target_price'] is not None and new_price <= item['target_price']:
                title = '🔔 Price dropped to target or below!'

            try:
                await bot.send_message(
                    item['user_id'],
                    (
                        f"{title}\n"
                        f"{item['product_name']}\n"
                        f"From: {old_price} -> To: {new_price}\n"
                        f"Target: {item['target_price']}\n"
                        f"{item['product_url']}"
                    ),
                )
            except Exception as err:
                print(
                    f"Could not send message to user {item['user_id']}: {err}"
                )

        await asyncio.sleep(1)

async def price_check_scheduler():
    await asyncio.sleep(10)
    while True:
        try:
            print('Start background price check')
            await check_price_updates()
        except Exception as err:
            print(f'Background price check error: {err}')
        await asyncio.sleep(PRICE_CHECK_INTERVAL)

@dp.message(Command("roll"))
async def cmd_roll(message: Message):
    args = message.text.split()[1:]
    if len(args) > 0:
        try:
            max_value = int(args[0])
        except ValueError:
            await message.answer("Please provide a valid number.")
            return
    else:
        max_value = 100

    roll_result = random.randint(1, max_value)
    await message.answer(f"Your result: {roll_result}")

@dp.message(Command("meowfact"))
async def cmd_meowfact(message: Message):
    args = message.text.split()[1:]
    count = 1
    if len(args) > 0:
        count = int(args[0])
    response = await fetch_meow_fact(count)
    if response:
        await message.answer("\n\n".join(response))
    else:
        await message.answer("Something went wrong!")

async def fetch_meow_fact(count: int):
    url = 'https://meowfacts.herokuapp.com/'
    params = {'count': count}
    try:
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    return None
                data = await response.json()
                return data.get('data')
    except Exception:
        return None

@dp.message(Command("play_ttt"))
async def cmd_play_ttt(message: Message):
    try:
        user_id = message.from_user.id
        if user_id in active_games:
            await message.answer("You already have an active game. Finish it or send /quit_ttt")
            return

        if client is None:
            await message.answer("AI is not available. Try later.")
            return

        if ttt_ai is None:
            await message.answer("AI initialization error.")
            return

        game = TicTacToe()
        active_games[user_id] = game

        board_display = game.get_board_display()
        await message.answer(
            f"🎮 Tic-tac-toe!\n\n"
            f"You are X, I am O\n\n"
            f"{board_display}\n\n"
            f"Your move! Enter a number 1-9\n"
            f"Use /quit_ttt to exit"
        )
    except Exception as err:
        print(f"Error in play_ttt: {type(err).__name__}: {err}")
        await message.answer(f"Error: {err}")

@dp.message(Command("quit_ttt"))
async def cmd_quit_ttt(message: Message):
    user_id = message.from_user.id
    if user_id in active_games:
        del active_games[user_id]
        await message.answer("Game finished.")
    else:
        await message.answer("No active game.")

@dp.message(F.text)
async def any_message(message: Message):
    user_id = message.from_user.id
    
    # Защита: НЕ обрабатываем команды (начинающиеся со слэша)
    if message.text.startswith('/'):
        print(f"⚠️ WARNING: Command '{message.text}' was NOT caught by command handler! It reached text handler!")
        print(f"   This should NOT happen. Command handler failed to process it.")
        return
    
    print(f"💬 Text message from {message.from_user.full_name}: {message.text}")

    if user_id in active_games:
        game = active_games[user_id]
        print(f"Game in progress for user {user_id}")
        try:
            move_num = int(message.text)
            print(f"User move: {move_num}")
            pos = game.is_valid_move(move_num)
            if pos is None:
                await message.answer("❌ Invalid move. Try again.")
                return

            game.make_move(pos, game.human)
            game.update_game_state()

            if game.game_over:
                board_display = game.get_board_display()
                if game.winner == 'X':
                    await message.answer(f"🎉 You won!\n\n{board_display}")
                else:
                    await message.answer(f"🤖 I won!\n\n{board_display}")
                del active_games[user_id]
                return

            print("Getting AI move...")
            ai_move = await ttt_ai.get_ai_move(game)
            print(f"AI move result: {ai_move}")
            if ai_move is None:
                await message.answer("AI error. Game ended.")
                del active_games[user_id]
                return

            game.make_move(ai_move - 1, game.ai)
            game.update_game_state()
            board_display = game.get_board_display()

            if game.game_over:
                if game.winner == 'O':
                    await message.answer(f"🤖 I won!\n\n{board_display}")
                else:
                    await message.answer(f"🤝 Draw!\n\n{board_display}")
                del active_games[user_id]
                return

            await message.answer(f"My move: {ai_move}\n\n{board_display}\nYour move:")

        except ValueError:
            await message.answer("Enter a number from 1 to 9")
            return

    if client is None:
        await message.answer("Hello world!")
    else:
        try:
            prompt = PromptBuilder.simplePrompt(message.text)
            await message.answer(f"Prompt: {prompt}")
            response = client.models.generate_content(
                model="gemini-3.5-flash",
                contents=prompt,
            )
        except Exception as err:
            print(f"{type(err)}: {err}")
            await message.answer("Something went wrong")
        else:
            await message.answer(str(response.text))

async def main():
    global bot, client, ttt_ai, db, price_checker_task

    load_dotenv()
    bot = auth_telegram()
    client = auth_gemini_api()
    ttt_ai = TicTacToeAI(client)
    db = DataBase()

    price_checker_task = asyncio.create_task(price_check_scheduler())

    print("=" * 60)
    print("🤖 BOT STARTING...")
    print(f"Client initialized: {client is not None}")
    print(f"AI initialized: {ttt_ai is not None}")
    print(f"Database initialized: {db is not None}")
    print("Command handlers registered:")
    print("  - /start")
    print("  - /db")
    print("  - /add_track")
    print("  - /my_tracks ← THIS SHOULD CATCH YOUR COMMAND")
    print("  - /roll")
    print("  - /meowfact")
    print("  - /play_ttt")
    print("  - /quit_ttt")
    print("=" * 60)

    try:
        await dp.start_polling(bot)
    finally:
        if price_checker_task:
            price_checker_task.cancel()
        db.close()
        print("Bot stopped")

if __name__ == '__main__':
    asyncio.run(main())
