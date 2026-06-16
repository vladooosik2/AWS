# Telegram bot | П35

Telegram-бот на Python, який інтегрується з Google Gemini API та відповідає на повідомлення користувачів за допомогою генеративного AI.

## Стек технологій

- **Python 3.10+**
- **aiogram 3.x** — асинхронний фреймворк для Telegram Bot API
- **google-genai** — клієнт Google Gemini API
- **python-dotenv** — завантаження змінних оточення з файлу `.env`

---

## Передумови

- Встановлений Python 3.10 або новіший
- Telegram-бот, створений через [@BotFather](https://t.me/BotFather) (отримайте `BOT_TOKEN`)
- API-ключ Google Gemini (отримайте на [Google AI Studio](https://aistudio.google.com/app/apikey))

---

## Розгортання

### 1. Клонування репозиторію

```bash
git clone https://github.com/<your-username>/P35TgBot.git
cd P35TgBot
```

### 2. Створення віртуального середовища

```bash
python -m venv .venv
```

Активація:

- **Linux / macOS:**
  ```bash
  source .venv/bin/activate
  ```
- **Windows (cmd):**
  ```cmd
  .venv\Scripts\activate.bat
  ```
- **Windows (PowerShell):**
  ```powershell
  .venv\Scripts\Activate.ps1
  ```

### 3. Встановлення залежностей

```bash
pip install -r requirements.txt
```

### 4. Налаштування змінних оточення

Скопіюйте файл-шаблон і заповніть свої дані:

```bash
cp .env-example .env
```

Відредагуйте `.env`:

```env
BOT_TOKEN=<YOUR TELEGRAM BOT TOKEN>
GEMINI_API_KEY=<YOUR GEMINI API KEY>
```

| Змінна           | Опис                                                  | Обов'язкова |
|------------------|-------------------------------------------------------|-------------|
| `BOT_TOKEN`      | Токен Telegram-бота від @BotFather                    | Так         |
| `GEMINI_API_KEY` | API-ключ Google Gemini для генерації відповідей       | Ні*         |

> Якщо `GEMINI_API_KEY` не вказаний, бот запуститься, але замість AI-відповідей відповідатиме статичним текстом `"Hello world!"`.

### 5. Запуск

```bash
python bot.py
```

Після запуску в терміналі з'явиться повідомлення `Starting bot...`. Бот готовий до роботи.

Для зупинки натисніть `Ctrl+C`.

---

## Використання

| Команда / дія       | Поведінка бота                                      |
|---------------------|-----------------------------------------------------|
| `/start`            | Бот відповідає `"Let's talk!"`                      |
| Будь-яке повідомлення | Запит передається до Gemini API, відповідь надсилається користувачу |

---

## Структура проєкту

```
P35TgBot/
├── bot.py              # Основний файл бота
├── requirements.txt    # Залежності Python
├── .env-example        # Шаблон змінних оточення
├── .gitignore
└── README.md
```

---

## Можливі проблеми

**Бот не відповідає / не запускається:**
- Перевірте правильність `BOT_TOKEN` у файлі `.env`.
- Переконайтеся, що бот не запущений в іншому місці (aiogram використовує polling).

**Помилка підключення до Gemini:**
- Перевірте правильність `GEMINI_API_KEY`.
- Переконайтеся, що ключ активований і ліміти не вичерпані.
- Бот продовжить роботу без Gemini, виводячи попередження в консоль.
