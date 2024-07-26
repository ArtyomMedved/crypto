from telethon import TelegramClient
from telethon.sessions import StringSession

# Введите ваш api_id и api_hash, полученные при регистрации приложения
api_id = '26744762'
api_hash = '71dfb38f90351d1b25ef1818ba86b905'

# Имя сессии для хранения данных
session_name = 'my_session'

# Создание клиента
client = TelegramClient(session_name, api_id, api_hash)

async def main():
    await client.start()
    print("Сессия успешно создана и вы вошли в систему!")

    # Если вы хотите сохранить строку сессии для последующего использования
    string_session = client.session.save()
    print(f"Строка сессии: {string_session}")

with client:
    client.loop.run_until_complete(main())