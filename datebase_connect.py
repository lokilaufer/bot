import psycopg2

conn = psycopg2.connect(
    dbname='your_database_name',
    user='your_username',
    password='your_password',
    host='your_host_address'
)
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        uid INTEGER,
        username TEXT
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS common_words (
        id SERIAL PRIMARY KEY,
        original_word TEXT,
        translation TEXT
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_words (
        id SERIAL PRIMARY KEY,
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
