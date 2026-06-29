"""
Отдельные хендлеры для команд бота.
Этот файл нужно импортировать в bot.py для регистрации всех хендлеров.
"""
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup

# Создаем отдельный роутер для команд
router = Router()


async def register_command_handlers(dp, db):
    """Регистрирует все обработчики команд в диспетчер"""
    
    @dp.message(Command("my_tracks"))
    async def cmd_my_tracks(message: Message):
        """Обработчик команды /my_tracks - выводит отслеживаемые продукты"""
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
        print(f"✅ Command /my_tracks processed for user {message.from_user.id}")
