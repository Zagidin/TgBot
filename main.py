import asyncio
import sqlite3

from random import choice, shuffle
from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardButton
from aiogram.types import ChatActions


db = sqlite3.connect('zagura_bot.db')
cursor = db.cursor()

cursor.execute(
    """CREATE TABLE IF NOT EXISTS users (
           id INTEGER PRIMARY KEY, 
           username TEXT, 
           lovegenres TEXT
    )
""")

db.commit()
db.close()


storage = MemoryStorage()

bot = Bot(token='6595000010:AAFNnPSbdi6C8HjrTnlbAWu1p5okdh5EHeo')
dp = Dispatcher(bot, storage=storage)

datas = {
    None
}


class Registration(StatesGroup):
    name = State()
    love_genres = State()


class Anagramma(StatesGroup):
    user_word = State()


@dp.message_handler(commands=['start'])
async def start(message: types.Message):

    await message.reply(
        f"👋 Привет @{message.from_user.username}!\n"
        f"\nЭто Мини-Бот << Zagura >>\n"
        f"\nЧтобы понять что я умею\nНажмите на /help 👨‍🏫"
    )


@dp.message_handler(commands=['help'])
async def help_bot(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(types.KeyboardButton('Начать регистрацию 📝'))
    await message.answer(
        f"Привет, это Бот << Zagura >>\n"
        f"\nДля начала Вас нужно зарегистировать\n"
        f"Чтобы пользоваться ботом было удобно ✏🗒"
        f"\n\nДля началы регистрации\nнажмите на /registration 📝"
        f"\n\nИли Нажмите на кнопку, которая появилась внизу 🛎️",
        reply_markup=keyboard
    )

    await message.answer(
        "Вы в любое время можете вызвать помощь бота\nНаписав /help.\n\n"
        "Команды бота прописаны в МЕНЮ команд, чтобы её открыть\n"
        "пропишите << / >> - Слеш\n\n1) Вывести данные людей:\n/compare"
        "\n\n2) Выбрать игру:\n/play_game"
        "\n\n3) Регистрация:\n/registration\n\n"
        "P. S. Во время Регистрации\nв конце нажмите на /save"
    )


# ---------------------------- Регаем пользователя --------------------------------


@dp.message_handler(commands=['registration'])
async def registration_bot(message: types.Message) -> None:
    await message.answer(
        "Как, Вас зовут? 😊",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await Registration.name.set()


@dp.message_handler(content_types=['text'], state=Registration.name)
async def name_polzovatel(message: types.Message, state: FSMContext) -> None:

    async with state.proxy() as data:
        data['name'] = message.text

    await message.answer("Введите Ваши любимые жанры через запятую и пробел 😜")
    await Registration.next()


@dp.message_handler(content_types=['text'], state=Registration.love_genres)
async def love_genres_polzovat(message: types.Message, state: FSMContext) -> None:

    global datas

    async with state.proxy() as data:
        data['love_genres'] = message.text.lower()

        datas = {
            'Имя': data['name'],
            'Любимые жанры': data['love_genres']
        }

    await message.answer("📝")
    await message.answer("Вы зарегистрировались! ❤️‍🔥")
    await message.answer(
        text=f'Чтобы сохранить данные\nНажмите на\t<b><i>/save</i></b> 📌\n'
        f'\nЕсли вы хотите отредактировать данные\n'
        f'нажмите на \t/registration 📝🗑️'
             f'\n\nДополнительная информация /help',
        parse_mode='HTML'
    )

    await state.finish()


@dp.message_handler(lambda message: message.text == 'Начать регистрацию 📝')
async def send_message(message: types.Message):
    await message.answer('Как Вас зовут? 😊', reply_markup=types.ReplyKeyboardRemove())
    await Registration.name.set()


@dp.message_handler(state=Registration.name)
async def process_name(message: types.Message, state: FSMContext):

    async with state.proxy() as data:
        data['name'] = message.text

    await message.answer('Введите ТРИ (3) любимых жанра 😜')

    await Registration.next()


@dp.message_handler(state=Registration.love_genres)
async def process_love_genres(message: types.Message, state: FSMContext):

    global datas

    async with state.proxy() as data:
        data['love_genres'] = message.text.lower()

        datas = {
            'Имя': data['name'],
            'Любимые жанры': data['love_genres']
        }

    await message.answer('Спасибо за регистрацию! ❤️‍🔥')

    await state.finish()

# ------------------------- Сохранение челика в базу данных ----------------------


@dp.message_handler(commands=['save'])
async def user_data(message: types.Message):

    conn = sqlite3.connect('zagura_bot.db')
    cursors = conn.cursor()

    await message.answer(f"Данные 🗒\n\n\tИмя 🪪 :\n{datas['Имя']}\n\nЛюбимые жанры 💬 :\n{datas['Любимые жанры']}")

    name = datas['Имя']
    love_genres = datas['Любимые жанры']

    cursors.execute(
        """INSERT INTO users (username, lovegenres) VALUES (?, ?)""",
        (name, love_genres)
    )

    conn.commit()
    conn.close()

# ------------------------------- Сравнение интересов ( жанров ) ----------------------------


def transform_dict_format(input_data):
    result = {}
    for entry in input_data:
        name, *rest = entry
        elements = [el for el in rest if el]
        result[name] = elements
    return dict(result)


def convert_to_sets(input_dict):
    result = {key: set(value) for key, value in input_dict.items()}
    return result


def print_dict_on_separate_lines(input_dict):
    output = ""
    for key, value in input_dict.items():
        output += f"{key}: {value}\n"
    return output


def find_names_with_same_values(input_dict):
    result = {}
    for key, value in input_dict.items():
        value_tuple = tuple(value)
        if value_tuple not in result:
            result[value_tuple] = []
        result[value_tuple].append(key)

    names_with_same_values = {value: names for value, names in result.items() if len(names) > 1}
    return names_with_same_values


@dp.message_handler(commands=['compare'])
async def compare(message: types.Message):
    conn = sqlite3.connect('zagura_bot.db')
    cursors = conn.cursor()

    cursors.execute("""SELECT username, lovegenres FROM users""")
    users = cursors.fetchall()
    conn.close()

    transformed_data = transform_dict_format(users)

    converted_data = convert_to_sets(transformed_data)

    print_polzovalet_all = print_dict_on_separate_lines(converted_data)
    otstup = '\n'
    await message.answer(f"Вот Весь список людей с разными жанрами интересов, "
                         f"посморите у кого совпадают интересы с Вами\n"
                         f"\n{print_polzovalet_all}")

    # print(converted_data)
    result = find_names_with_same_values(converted_data)
    # print("Имена с совпадающими значениями:", result)
    await message.answer(f"Вот Люди у которых совпадают Жанры ( Интересы )\n\n{result}")

# --------------------------------- Игры ----------------------------------------------


@dp.message_handler(commands=['play_game'])
async def play_game(message: types.Message):

    keyboards = ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = InlineKeyboardButton(text='Скрабл 🔠')
    btn2 = InlineKeyboardButton(text='Уникальные символы 🦊')
    btn3 = InlineKeyboardButton(text='Анаграммы 🎭')
    btn4 = InlineKeyboardButton(text='Пенальти ⚽')
    btn5 = InlineKeyboardButton(text='Баскетболл 🏀')
    btn6 = InlineKeyboardButton(text='Боулинг 🎳')
    keyboards.row(btn1, btn3)
    keyboards.add(btn2)
    keyboards.add(btn5)
    keyboards.row(btn6, btn4)

    await message.answer(
        f"@{message.from_user.username} "
        f"Выбери одну игру из предложных снизу 😉",
        reply_markup=keyboards
    )

# ------------- Игра Анаграмма ------------
word_bot = ''

# -------------- Игра Скрабл --------------
dictionary = {
    'apple',
    'banana',
    'cherry',
    'grape',
    'orange',
    'kiwi',
    'lemon',
    'melon',
    'pear',
    'plum'
}

game_state = {
    'current_word': '',
    'current_player': None,
    'scores': {}
}


@dp.message_handler(lambda message: message.text)
async def send_message(message: types.Message):

    global word_bot

    if message.text == 'Анаграммы 🎭':

        words = ['Priora', 'Школа', 'Python', 'Старт', 'Aiogram', 'Анаграмма', 'import']

        await message.reply("Подожди немного, я придумываю слово!")

        await bot.send_chat_action(
            message.chat.id,
            ChatActions.TYPING
        )
        await asyncio.sleep(3.5)

        word = choice(words)
        word_bot += word

        await message.answer(
            f"Всё, я Загадал слово ✍ \n\n"
            f"Посморишь тогда когда сдашься 🫡 "
            f"\n<tg-spoiler>🫵👁\n{word}</tg-spoiler>",
            parse_mode='HTML'
        )

        word_shuffled = list(word)
        shuffle(word_shuffled)
        shuffled_word = ''.join(word_shuffled)

        await message.answer(f"Вот Анограмма: "
                             f"\n\n\t{shuffled_word}\n\n"
                             f"Угадай что-за слово я загадал изначально"
                             f"\nУдачи!")
        await Anagramma.user_word.set()

    elif message.text == 'Скрабл 🔠':

        game_state['current_player'] = message.from_user.id
        game_state['current_word'] = ''
        game_state['scores'][message.from_user.id] = 0

        await message.answer("Добро пожаловать в игру! Начнем с вас. Напишите слово:")

    elif message.text == 'Пенальти ⚽':
        await message.answer_dice("⚽")
    elif message.text == 'Баскетболл 🏀':
        await message.answer_dice("🏀")
    elif message.text == 'Боулинг 🎳':
        await message.answer_dice("🎳")
    else:
        await message.answer("Пока в разработке :)")


# ------------------------------------- Игра Анаграмма ----------------------------------


@dp.message_handler(state=Anagramma.user_word)
async def anagram(message: types.Message, state: FSMContext):

    global word_bot

    async with state.proxy() as data:
        data['user_word'] = message.text

    if data['user_word'] == word_bot:
        await message.answer("Вы верно угадали!")
        await state.finish()
        word_bot = ''

    elif data['user_word'].lower() == 'стоп':
        await state.finish()

        word_bot = ''

        gif = open('GIF/Otmena.gif', 'rb')
        await message.reply_animation(animation=gif)

        await message.answer("Можете выбирать другую игру 🤖\n\n   /help - Помощь")

    else:
        await message.answer(
            f"Неверно, я такого не загадывал!\n"
            f"\nНапишите   ==  <b><u><code>Стоп</code></u></b>  ==   чтобы Выйти",
            parse_mode='HTML'
        )


# ---------------------------------- Игра Скрабл -----------------------------------


@dp.message_handler()
async def process_word(message: types.Message):
    word = message.text.lower()
    if word in dictionary and message.from_user.id == game_state['current_player']:
        game_state['current_word'] = word
        game_state['scores'][game_state['current_player']] += len(word)
        await message.answer(
            f"Хорошо! Слово принято. "
            f"Ваше текущее очко: {game_state['scores'][game_state['current_player']]}")
    else:
        await message.answer("Ошибка! Попробуйте еще раз.")


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
