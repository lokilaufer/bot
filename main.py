from telebot import TeleBot, types
from telebot.states import StatesGroup, State
from telebot.storage import StateMemoryStorage
import random
import sqlite3

conn = sqlite3.connect('vocab.db')
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        uid INTEGER,
        username TEXT
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS common_words (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        original_word TEXT,
        translation TEXT
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_words (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        uid INTEGER,
        original_word TEXT,
        translation TEXT
    )
""")

common_words = {
    'Peace': 'Мир',
    'Green': 'Зеленый',
    'White': 'Белый',
    'Hello': 'Привет',
    'Car': 'Машина',
    'Dog': 'Собака',
    'Cat': 'Кошка',
    'Sun': 'Солнце',
    'Moon': 'Луна',
    'Book': 'Книга'
}

print('Start telegram bot...')

state_storage = StateMemoryStorage()
token_bot = 'YOUR_BOT_TOKEN_HERE'
bot = TeleBot(token_bot, state_storage=state_storage)

known_users = []
userStep = {}


class Command:
    ADD_WORD = 'Add Word ➕'
    DELETE_WORD = 'Delete Word🔙'
    NEXT = 'Next ⏭'


class MyStates(StatesGroup):
    target_word = State()
    translate_word = State()
    another_words = State()


def get_user_step(uid):
    if uid in userStep:
        return userStep[uid]
    else:
        known_users.append(uid)
        userStep[uid] = 0
        print("New user detected, who hasn't used \"/start\" yet")
        return 0


@bot.message_handler(commands=['start'])
def start_message(message):
    cid = message.chat.id
    if cid not in known_users:
        known_users.append(cid)
        userStep[cid] = 0
        bot.send_message(cid, "Hello! Let's study English...")

    create_cards(message)


def create_cards(message):
    cid = message.chat.id

    markup = types.ReplyKeyboardMarkup(row_width=2)

    # Randomly select a word and its translation
    cursor.execute('SELECT * FROM common_words ORDER BY RANDOM() LIMIT 1')
    word_pair = cursor.fetchone()
    target_word = word_pair[1]
    translate = word_pair[2]

    target_word_btn = types.KeyboardButton(target_word)
    buttons = [target_word_btn]

    # Randomly select 3 incorrect translation options
    cursor.execute('SELECT translation FROM common_words WHERE translation != ? ORDER BY RANDOM() LIMIT 3',
                   (translate,))
    wrong_choices = cursor.fetchall()
    other_words = [item[0] for item in wrong_choices]

    other_words_btns = [types.KeyboardButton(word) for word in other_words]

    buttons.extend(other_words_btns)
    random.shuffle(buttons)

    next_btn = types.KeyboardButton(Command.NEXT)
    add_word_btn = types.KeyboardButton(Command.ADD_WORD)
    delete_word_btn = types.KeyboardButton(Command.DELETE_WORD)

    buttons.extend([next_btn, add_word_btn, delete_word_btn])

    markup.add(*buttons)

    greeting = f"Choose the translation for the word:\n 🇷🇺 {translate}"
    bot.send_message(message.chat.id, greeting, reply_markup=markup)

    bot.set_state(message.from_user.id, MyStates.target_word, message.chat.id)

    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['target_word'] = target_word
        data['translate_word'] = translate


@bot.message_handler(func=lambda message: message.text == Command.NEXT)
def next_cards(message):
    create_cards(message)


@bot.message_handler(func=lambda message: message.text == Command.DELETE_WORD)
def delete_word(message):
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        cursor.execute('DELETE FROM common_words WHERE original_word = ?', (data['target_word'],))
        conn.commit()


@bot.message_handler(func=lambda message: message.text == Command.ADD_WORD)
def add_word(message):
    cid = message.chat.id
    userStep[cid] = 1


@bot.message_handler(func=lambda message: get_user_step(message.chat.id) == 1)
def save_new_word(message):
    word = message.text.strip()

    # Add new word to the common_words table
    translation = input("Enter translation for the word: ")
    cursor.execute('INSERT INTO common_words (original_word, translation) VALUES (?, ?)', (word, translation))
    conn.commit()

    userStep[message.chat.id] = 0

    bot.send_message(message.chat.id, "Word added successfully!")

    num_words = len(common_words)
    bot.send_message(message.chat.id, f"Now you are learning {num_words} words!")


@bot.message_handler(func=lambda message: True, content_types=['text'])
def message_reply(message):
    word = None
    translation = None
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        word = data.get('target_word')
        translation = data.get('translate_word')

    if message.text == translation:
        bot.send_message(message.chat.id, 'Correct!')
    else:
        bot.send_message(message.chat.id, 'Try again!')


bot.infinity_polling(skip_pending=True)
