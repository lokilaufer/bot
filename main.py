from telebot import TeleBot, types
from telebot.states import StatesGroup, State
from telebot.storage import StateMemoryStorage

from datebase_connect import cursor, conn

print('Start telegram bot...')

state_storage = StateMemoryStorage()
token_bot = 'YOUR_BOT_TOKEN_HERE'
bot = TeleBot(token_bot, state_storage=state_storage)

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
        userStep[uid] = 0
        print("New user detected, who hasn't used \"/start\" yet")
        return 0


@bot.message_handler(commands=['start'])
def start_message(message):
    cid = message.chat.id
    create_user(uid=cid)
    create_cards(message)


def create_user(uid):
    cursor.execute('SELECT id FROM users WHERE uid = %s', (uid,))
    user = cursor.fetchone()
    if user is None:
        cursor.execute('INSERT INTO users (uid) VALUES (%s)', (uid,))
        conn.commit()


def create_cards(message):
    cid = message.chat.id

    markup = types.ReplyKeyboardMarkup(row_width=2)

    cursor.execute('SELECT * FROM common_words ORDER BY RANDOM() LIMIT 4')
    word_pairs = cursor.fetchall()

    buttons = []

    for pair in word_pairs:
        target_word = pair[1]
        translate = pair[2]
        target_word_btn = types.KeyboardButton(target_word)
        buttons.append(target_word_btn)

    add_word_btn = types.KeyboardButton(Command.ADD_WORD)
    delete_word_btn = types.KeyboardButton(Command.DELETE_WORD)
    buttons.extend([add_word_btn, delete_word_btn])

    markup.add(*buttons)

    bot.send_message(message.chat.id, "Choose the translation for the word:", reply_markup=markup)

    bot.set_state(message.from_user.id, MyStates.target_word, message.chat.id)

    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['word_pairs'] = word_pairs


@bot.message_handler(func=lambda message: message.text == Command.DELETE_WORD)
def delete_word(message):
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        word_pairs = data['word_pairs']
        target_word = message.text
        cursor.execute('DELETE FROM common_words WHERE original_word = %s', (target_word,))
        word_pairs = [(w, t) for w, t in word_pairs if w != target_word]
        data['word_pairs'] = word_pairs
        conn.commit()


@bot.message_handler(func=lambda message: message.text == Command.ADD_WORD)
def add_word(message):
    cid = message.chat.id
    userStep[cid] = 1


@bot.message_handler(func=lambda message: get_user_step(message.chat.id) == 1)
def save_new_word(message):
    word = message.text.strip()
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        word_pairs = data['word_pairs']
        word_exists = any(w == word for w, _ in word_pairs)
        if not word_exists:
            translation = input("Enter translation for the word: ")
            cursor.execute('INSERT INTO common_words (original_word, translation) VALUES (%s, %s)', (word, translation))
            word_pairs.append((word, translation))
            data['word_pairs'] = word_pairs
            conn.commit()
            bot.send_message(message.chat.id, "Word added successfully!")
        else:
            bot.send_message(message.chat.id, "Try again!))")
