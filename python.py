import sqlite3
import requests
import time
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from telegram import Update, ForceReply, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler
from telethon import TelegramClient
import time
from tronpy import Tron
from tronpy.keys import PrivateKey
from tronpy.providers import HTTPProvider
from threading import Thread
import pandas as pd
import os
import asyncio
from concurrent.futures import ThreadPoolExecutor
# Asynchronous functions
from telegram.error import Conflict

# Ваши токены и настройки
TELEGRAM_TOKEN = '7233049532:AAGgroWUXMFoqq0VuqrVHVZU1NzecuLG0oY'
API_ID = '26744762'  # ID API, полученный от my.telegram.org
API_HASH = '71dfb38f90351d1b25ef1818ba86b905' # Хэш API, полученный от my.telegram.org
SESSION_NAME = 'YOUR_SESSION_NAME'  # Имя вашей сессии
TARGET_BOT_USERNAME = '@TRXEnergyMarket_bot'
# Путь к драйверу Chrome
CHROMEDRIVER_PATH = '/usr/local/bin/chromedriver'
USDT_PER_TRANSACTION = 29.8
pass_word = "MedvedevArtyom08" # пароль для врмененного акаунта кошелька для оплаты bandwidth 
api_key = "9250cd97-47a4-42e8-a0c9-212ab222169c"  # api key from TRONGRID
# Введите свой приватный ключ
private_key_hex = "471514b3bdbbf7d275e987933eb7bd1771b0ea09df05c8cd6c532c2bd0a31a1e"  # from tronlik

def init_db():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    cursor.execute("PRAGMA table_info(users)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'approved' not in columns:
        cursor.execute('''
        ALTER TABLE users ADD COLUMN approved INTEGER DEFAULT 0
        ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id INTEGER UNIQUE,
        admin INTEGER DEFAULT 0,
        date_added TEXT,
        approved INTEGER DEFAULT 0
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_addresses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        tron_address TEXT,
        energy_remaining TEXT,
        free_bandwidth TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    ''')
    
    conn.commit()
    conn.close()

init_db()

def get_new_users():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, tron_address FROM user_addresses ORDER BY id DESC LIMIT 1')
    new_user = cursor.fetchone()
    conn.close()
    return new_user

# Функция для проверки, является ли пользователь администратором
def is_admin(chat_id):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT admin FROM users WHERE chat_id = ?', (chat_id,))
    result = cursor.fetchone()
    conn.close()
    return result and result[0] == 1

# Функция для получения списка пользователей
def get_user_list():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT chat_id FROM users')
    users = cursor.fetchall()
    conn.close()
    return [user[0] for user in users]

# Команда /apanel
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.message.chat_id
    if is_admin(chat_id):
        user_list = get_user_list()
        buttons = [[InlineKeyboardButton(str(user_id), callback_data=f"user_{user_id}")] for user_id in user_list]
        reply_markup = InlineKeyboardMarkup(buttons)
        await update.message.reply_text("Список пользователей:", reply_markup=reply_markup)
    else:
        await update.message.reply_text("У вас нет прав для доступа к этой панели.")

# Вспомогательные функции
async def auto_energy_reg(update: Update, address: str):
    print(f"Starting auto_energy_reg for address: {address}")
    try:
        async with TelegramClient(SESSION_NAME, API_ID, API_HASH) as client:
            await client.send_message(
                TARGET_BOT_USERNAME,
                f"/order {address} 70000 14"
            )
        print(f"auto_energy_reg completed successfully for address: {address}")
        await update.message.reply_text(
            f"Энергия успешно зарегистрирована для адреса {address}."
        )
    except Exception as e:
        print(f"Error in auto_energy_reg for address {address}: {str(e)}")
        raise

async def auto_band_reg(update: Update, address: str):
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    service = Service(CHROMEDRIVER_PATH)
    
    try:
        driver = webdriver.Chrome(service=service, options=chrome_options)
        # Открытие сайта
        driver.get("https://tronenergy.market/")
        
        # Явное ожидание, пока страница загрузится
        wait = WebDriverWait(driver, 5)

        # Проверка невидимости известных элементов загрузки
        known_loaders = ['loading', 'some_other_loading_element_id']
        for loader in known_loaders:
            try:
                wait.until(EC.invisibility_of_element_located((By.ID, loader)))
            except Exception as e:
                print(f"Loader '{loader}' not found or already invisible: {e}")

        # Дополнительная задержка для надежности
        time.sleep(1)

        # Клик на 14-й элемент с классом "select-dropdown dropdown-trigger" для открытия первого выпадающего списка
        dropdown1_trigger = wait.until(EC.element_to_be_clickable((By.XPATH, "(//input[@class='select-dropdown dropdown-trigger'])[14]")))
        dropdown1_trigger.click()

        time.sleep(1)
        
        # Ожидание появления выпадающего меню и выбор опции "Bandwidth"
        bandwidth_option = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[text()='Bandwidth']")))
        bandwidth_option.click()
        
        time.sleep(1)

        # Ввод значения 1750
        amount_input = wait.until(EC.visibility_of_element_located((By.ID, "rent-resource-amount")))
        amount_input.clear()
        amount_input.send_keys("1750")

        time.sleep(1)
        
        # Клик на 15-й элемент с классом "select-dropdown dropdown-trigger" для открытия второго выпадающего списка
        dropdown2_trigger = wait.until(EC.element_to_be_clickable((By.XPATH, "(//input[@class='select-dropdown dropdown-trigger'])[15]")))
        dropdown2_trigger.click()

        time.sleep(1)
        
        one_day_option_xpath = "//ul[contains(@id, 'select-options')]//li[34]"
        one_day_option = wait.until(EC.presence_of_element_located((By.XPATH, one_day_option_xpath)))

        try:
            one_day_option = wait.until(EC.element_to_be_clickable((By.XPATH, one_day_option_xpath)))
            one_day_option.click()
        except Exception as e:
            print(f"Error while clicking on one_day_option: {e}")

        time.sleep(1)

        # Очистка поля ввода и запись значения адреса
        address_input = wait.until(EC.visibility_of_element_located((By.ID, "rent-trx-address")))
        address_input.clear()
        address_input.send_keys(address)

        time.sleep(1)
        
        # Извлечение значения из span с id "form-subtotal-value"
        price_span = wait.until(EC.visibility_of_element_located((By.ID, "form-subtotal-value")))
        price = price_span.text

        # Клик на кнопку с идентификатором "rent-button"
        rent_button = wait.until(EC.element_to_be_clickable((By.ID, "rent-button")))
        rent_button.click()

        time.sleep(1)

        # Клик на второй элемент с классом "btn-small custom-purple-small-button custom-purple-text modal-accept"
        accept_terms_button_xpath = "(//a[contains(@class, 'btn-small custom-purple-small-button custom-purple-text modal-accept')])[2]"
        accept_terms_button = wait.until(EC.element_to_be_clickable((By.XPATH, accept_terms_button_xpath)))
        accept_terms_button.click()

        time.sleep(1)

        # Очистка и ввод пароля в первый элемент с id "wallet-setup-password"
        password_input_xpath = "(//input[@id='wallet-setup-password'])[1]"
        password_input = wait.until(EC.visibility_of_element_located((By.XPATH, password_input_xpath)))
        password_input.clear()
        password_input.send_keys(pass_word)

        time.sleep(1)

        # Очистка и ввод пароля в первый элемент с id "wallet-setup-password-repeat"
        password_repeat_input_xpath = "(//input[@id='wallet-setup-password-repeat'])[1]"
        password_repeat_input = wait.until(EC.visibility_of_element_located((By.XPATH, password_repeat_input_xpath)))
        password_repeat_input.clear()
        password_repeat_input.send_keys(pass_word)

        time.sleep(1)

        # Клик на кнопку "Сохранить"
        save_button = wait.until(EC.element_to_be_clickable((By.ID, "wallet-setup-save")))
        save_button.click()

        time.sleep(1)

        # Клик на кнопку "Не сейчас"
        cancel_button_xpath = "//a[contains(@class, 'btn-flat modal-close waves-effect') and contains(@data-i18n, 'modal.wallet_export_advice.cancel')]"
        cancel_button = wait.until(EC.element_to_be_clickable((By.XPATH, cancel_button_xpath)))
        cancel_button.click()

        ## Извлечение текста из поля ввода и вывод его в терминал
        address_field = wait.until(EC.visibility_of_element_located((By.ID, "trx-recharge-address")))
        address_value = address_field.get_attribute("value")
        print("Text inside 'trx-recharge-address':", address_value)
        print("Total Price:", price, "TRX")

        # Задержка, чтобы дать время для выполнения предыдущих команд
        time.sleep(5)

        # Укажите ваш TronGrid API-ключ
        api_key = "9250cd97-47a4-42e8-a0c9-212ab222169c"

        # Инициализация клиента Tron с использованием TronGrid и API-ключа
        client = Tron(HTTPProvider(api_key=api_key))

        # Введите свой приватный ключ
        private_key_hex = "471514b3bdbbf7d275e987933eb7bd1771b0ea09df05c8cd6c532c2bd0a31a1e"
        priv_key = PrivateKey(bytes.fromhex(private_key_hex))

        # Укажите адреса отправителя и получателя
        from_addr = priv_key.public_key.to_base58check_address()
        to_addr = address_value  # Используйте значение, полученное из Selenium

        # Укажите сумму перевода в TRX (1 TRX = 1_000_000 Sun)
        amount = int(float(price) * 1_000_000)  # Перевод суммы в TRX

        # Создание транзакции
        txn = (
            client.trx.transfer(from_addr, to_addr, amount)
            .memo("Hello, Tron!")
            .build()
            .sign(priv_key)
        )

        # Отправка транзакции
        txid = txn.broadcast()

        print(f"Transaction ID: {txid}")

        # Обновление страницы
        driver.refresh()

        # Явное ожидание, пока страница загрузится
        wait = WebDriverWait(driver, 5)

        # Проверка невидимости известных элементов загрузки
        known_loaders = ['loading', 'some_other_loading_element_id']
        for loader in known_loaders:
            try:
                wait.until(EC.invisibility_of_element_located((By.ID, loader)))
            except Exception as e:
                print(f"Loader '{loader}' not found or already invisible: {e}")

        # Дополнительная задержка для надежности
        time.sleep(1)

        # Клик на 14-й элемент с классом "select-dropdown dropdown-trigger" для открытия первого выпадающего списка
        dropdown1_trigger = wait.until(EC.element_to_be_clickable((By.XPATH, "(//input[@class='select-dropdown dropdown-trigger'])[14]")))
        dropdown1_trigger.click()

        time.sleep(1)
        
        # Ожидание появления выпадающего меню и выбор опции "Bandwidth"
        bandwidth_option = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[text()='Bandwidth']")))
        bandwidth_option.click()
        
        time.sleep(1)

        # Ввод значения 1750
        amount_input = wait.until(EC.visibility_of_element_located((By.ID, "rent-resource-amount")))
        amount_input.clear()
        amount_input.send_keys("1750")

        time.sleep(1)
        
        # Клик на 15-й элемент с классом "select-dropdown dropdown-trigger" для открытия второго выпадающего списка
        dropdown2_trigger = wait.until(EC.element_to_be_clickable((By.XPATH, "(//input[@class='select-dropdown dropdown-trigger'])[15]")))
        dropdown2_trigger.click()

        time.sleep(1)
        
        one_day_option_xpath = "//ul[contains(@id, 'select-options')]//li[34]"
        one_day_option = wait.until(EC.presence_of_element_located((By.XPATH, one_day_option_xpath)))

        try:
            one_day_option = wait.until(EC.element_to_be_clickable((By.XPATH, one_day_option_xpath)))
            one_day_option.click()
        except Exception as e:
            print(f"Error while clicking on one_day_option: {e}")

        time.sleep(1)

        # Очистка поля ввода и запись значения адреса
        address_input = wait.until(EC.visibility_of_element_located((By.ID, "rent-trx-address")))
        address_input.clear()
        address_input.send_keys(address)

        time.sleep(1)
        
        # Извлечение значения из span с id "form-subtotal-value"
        price_span = wait.until(EC.visibility_of_element_located((By.ID, "form-subtotal-value")))
        price = price_span.text

        # Клик на кнопку с идентификатором "rent-button"
        rent_button = wait.until(EC.element_to_be_clickable((By.ID, "rent-button")))
        rent_button.click()

        # Ввод пароля в элемент с id "wallet-password-prompt-password"
        password_prompt_input = wait.until(EC.visibility_of_element_located((By.ID, "wallet-password-prompt-password")))
        password_prompt_input.clear()
        password_prompt_input.send_keys(pass_word)

        time.sleep(5)

        # Клик на кнопку с id "wallet-password-ok"
        wallet_password_ok_button = wait.until(EC.element_to_be_clickable((By.ID, "wallet-password-ok")))
        wallet_password_ok_button.click()

        time.sleep(100)

        # Подтверждение аренды
        await update.message.reply_text(
            f"Вы успешно арендовали Bandwidth для адреса {address} на срок 30 дней."
        )
    except Exception as e:
        await update.message.reply_text(f"Произошла ошибка при аренде Bandwidth: {str(e)}")
    finally:
        try:
            driver.quit()
        except:
            pass

async def add_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.message.chat_id

    if len(context.args) == 2:
        user_id_str = context.args[0]
        tron_address = context.args[1]

        try:
            new_user_id = int(user_id_str)
        except ValueError:
            await update.message.reply_text('Ошибка: ID пользователя должен быть числом.')
            return

        if is_admin(chat_id):
            conn = sqlite3.connect('users.db')
            cursor = conn.cursor()

            cursor.execute('SELECT id FROM users WHERE chat_id = ?', (new_user_id,))
            user_record = cursor.fetchone()

            if user_record is None:
                date_added = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                cursor.execute('INSERT INTO users (chat_id, date_added) VALUES (?, ?)', (new_user_id, date_added))
                user_id = cursor.lastrowid
                conn.commit()
                cursor.execute('INSERT INTO user_addresses (user_id, tron_address) VALUES (?, ?)', (user_id, tron_address))
                conn.commit()
                await update.message.reply_text(f'Пользователь с ID {new_user_id} успешно добавлен с адресом {tron_address}.')
            else:
                user_id = user_record[0]
                cursor.execute('SELECT id FROM user_addresses WHERE user_id = ?', (user_id,))
                address_record = cursor.fetchone()
                if address_record is None:
                    cursor.execute('INSERT INTO user_addresses (user_id, tron_address) VALUES (?, ?)', (user_id, tron_address))
                    conn.commit()
                    await update.message.reply_text(f'Адрес {tron_address} успешно добавлен для пользователя с ID {new_user_id}.')
                else:
                    await update.message.reply_text(f'Адрес для пользователя с ID {new_user_id} уже существует.')

            conn.close()

            # Выполнение регистрации ресурсов
            await auto_energy_reg(update, tron_address)
            await auto_band_reg(update, tron_address)
        else:
            await update.message.reply_text('У вас нет прав для выполнения этой команды.')
    else:
        await update.message.reply_text('Ошибка: Неправильный формат команды. Используйте: /aduser <user_id> <tron_address>')

# Функция для получения статистики по адресам пользователя
def get_user_addresses(chat_id):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM users WHERE chat_id = ?', (chat_id,))
    user_id = cursor.fetchone()[0]
    cursor.execute('SELECT tron_address, energy_remaining, free_bandwidth FROM user_addresses WHERE user_id = ?', (user_id,))
    addresses = cursor.fetchall()
    conn.close()
    return addresses

async def get_user_info(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> tuple[str, str, str]:
    # Получение информации о пользователе из Telegram
    user = await context.bot.get_chat(user_id)
    username = user.username if user.username else f"User {user_id}"
    first_name = user.first_name

    # Получение даты добавления пользователя из базы данных
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT date_added FROM users WHERE chat_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()

    # Если пользователь найден, извлекаем дату добавления
    if result:
        date_added = result[0]
    else:
        date_added = 'Дата не установлена'

    return username, first_name, date_added

# Первый обработчик
async def button_handler1(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if query.data.startswith('approve_'):
        user_id = int(query.data.split('_')[1])
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET approved = 1 WHERE chat_id = ?', (user_id,))
        date_added = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('UPDATE users SET date_added = ? WHERE chat_id = ?', (date_added, user_id))
        conn.commit()
        conn.commit()
        conn.commit()
        conn.close()
        await context.bot.send_message(
            chat_id=user_id,
            text='Ваша заявка на регистрацию одобрена. Пожалуйста, введите ваш первый адрес TRON.',
            reply_markup=ForceReply(selective=True)
        )
        await query.edit_message_text(text=f"Пользователь с ID {user_id} одобрен.")
    elif query.data.startswith('reject_'):
        user_id = int(query.data.split('_')[1])
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM users WHERE chat_id = ?', (user_id,))
        conn.commit()
        conn.close()
        await context.bot.send_message(
            chat_id=user_id,
            text='Ваша заявка на регистрацию отклонена.'
        )
        await query.edit_message_text(text=f"Пользователь с ID {user_id} отклонен.")
    else:
        print(f"Unexpected callback data: {query.data}")

# Второй обработчик
async def button_handler2(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == 'add_wallet':
        await query.message.reply_text('Пожалуйста, введите новый адрес TRON.', reply_markup=ForceReply(selective=True))
    elif query.data == 'delete_wallet':
        await query.message.reply_text('Пожалуйста, введите адрес TRON, который вы хотите удалить.', reply_markup=ForceReply(selective=True))
    elif query.data.startswith('user_'):
        try:
            user_id = int(query.data.split("_")[1])
            # Теперь вызываем get_user_info правильно с контекстом
            username, first_name, date_added_str = await get_user_info(user_id, context)
            addresses = get_user_addresses(user_id)

            # Расчет оставшегося времени подписки
            try:
                date_added = datetime.strptime(date_added_str, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                date_added = datetime.now()  # Если дата не установлена, используем текущую дату
            subscription_end_date = date_added + timedelta(days=30)
            remaining_days = (subscription_end_date - datetime.now()).days
            if remaining_days < 0:
                remaining_days = 0

            now = datetime.now()
            start_date = now - timedelta(days=30)
            start_timestamp = int(start_date.timestamp() * 1000)
            end_timestamp = int(now.timestamp() * 1000)

            if addresses:
                response = f"Пользователь <a href='tg://user?id={user_id}'>{first_name}</a>:\n\n"
                for address, energy, bandwidth in addresses:
                    transaction_count = get_transaction_count(address, start_timestamp, end_timestamp)
                    response += (
                        f"username: @{username}\n"
                        f"ID: <code>{user_id}</code>\n"
                        f"Адрес: <code>{address}</code>\n"
                        f"Энергия: {energy}\n"
                        f"Бесплатный bandwidth: {bandwidth}\n"
                        f"Количество транзакций за текущий месяц: {transaction_count}\n"
                        f"Дата добавления: {date_added.strftime('%Y-%m-%d %H:%M:%S')}\n"
                        f"Оставшееся время подписки: {remaining_days} дней\n\n"
                    )
            else:
                response = f"У пользователя {first_name} нет подключенных адресов.\n\nДата добавления: {date_added.strftime('%Y-%m-%d %H:%M:%S')}\nОставшееся время подписки: {remaining_days} дней"

            await query.edit_message_text(text=response, parse_mode='HTML')
        except ValueError as e:
            print(f"Error parsing user_id: {e}")
        except Exception as e:
            print(f"Error retrieving user info: {e}")
    else:
        print(f"Unexpected callback data: {query.data}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message
    chat_id = message.chat_id
    text = message.text

    # Проверяем длину сообщения
    if len(text) != 34:
        return  # Игнорируем сообщения, длина которых не равна 34 символам

    # Проверяем, что сообщение является ответом на другое сообщение
    if message.reply_to_message:
        reply_text = message.reply_to_message.text

        # Обрабатываем ввод нового адреса TRON
        if 'новый адрес TRON' in reply_text:
            conn = sqlite3.connect('users.db')
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM users WHERE chat_id = ?', (chat_id,))
            user_id = cursor.fetchone()

            if user_id:
                user_id = user_id[0]
                cursor.execute('SELECT * FROM user_addresses WHERE tron_address = ?', (text,))
                address_data = cursor.fetchone()

                if address_data:
                    if address_data[1] == user_id:
                        await message.reply_text(
                            'Ошибка ⚠️ - такой адрес уже привязан к вашему аккаунту.'
                        )
                    else:
                        keyboard = [[InlineKeyboardButton("Поддержка", url="https://t.me/usdt_il")]]
                        reply_markup = InlineKeyboardMarkup(keyboard)
                        await message.reply_text(
                            'Ошибка ⚠️ - такой адрес уже привязан к другому аккаунту\n'
                            'Проверьте правильность введенного адреса или обратитесь в поддержку',
                            reply_markup=reply_markup
                        )
                    await message.reply_text(
                        'Пожалуйста, введите ваш адрес TRON снова.',
                        reply_markup=ForceReply(selective=True)
                    )
                else:
                    energy_used, energy_limit, energy_remaining = get_energy_usage(text)
                    free_bandwidth = get_bandwidth_data(text)

                    cursor.execute('INSERT INTO user_addresses (user_id, tron_address, energy_remaining, free_bandwidth) VALUES (?, ?, ?, ?)',
                                   (user_id, text, energy_remaining, free_bandwidth))
                    conn.commit()

                    await message.reply_text(
                        f"Адрес добавлен успешно, ваш адрес - {text}, Оставшаяся энергия: {energy_remaining}, Свободное количество Bandwidth: {free_bandwidth}"
                    )

                    # Создаем задачи для асинхронного выполнения
                    energy_task = asyncio.create_task(auto_energy_reg(update, text))
                    band_task = asyncio.create_task(auto_band_reg(update, text))

                    try:
                        # Ждем выполнения обеих задач
                        await asyncio.gather(energy_task, band_task)
                        await message.reply_text(
                            "Автоматическое пополнение энергии и bandwidth выполнено успешно."
                        )
                    except Exception as e:
                        await message.reply_text(
                            f"Произошла ошибка при автоматическом пополнении: {str(e)}"
                        )
            else:
                await message.reply_text('Вы не зарегистрированы. Пожалуйста, используйте команду /start для регистрации.')
            conn.close()
        
        # Обрабатываем удаление адреса TRON
        elif 'адрес TRON, который вы хотите удалить' in reply_text:
            tron_address = text
            conn = sqlite3.connect('users.db')
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM users WHERE chat_id = ?', (chat_id,))
            user_id = cursor.fetchone()
            if user_id:
                user_id = user_id[0]
                cursor.execute('SELECT id FROM user_addresses WHERE tron_address = ? AND user_id = ?', (tron_address, user_id))
                address_data = cursor.fetchone()
                if address_data:
                    cursor.execute('DELETE FROM user_addresses WHERE tron_address = ? AND user_id = ?', (tron_address, user_id))
                    conn.commit()
                    await message.reply_text(f'Кошелек {tron_address} был успешно удален.')
                else:
                    await message.reply_text('Ошибка: кошелек с таким адресом не найден!')
            conn.close()
        
        # Обрабатываем запрос на добавление пользователя
        elif 'ID пользователя, которого хотите добавить' in reply_text:
            await add_user(update, context)
        return

    # Проверяем, что сообщение не является ответом на другое сообщение
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM users WHERE chat_id = ?', (chat_id,))
    user_id = cursor.fetchone()

    if user_id:
        user_id = user_id[0]
        cursor.execute('SELECT * FROM user_addresses WHERE tron_address = ?', (text,))
        address_data = cursor.fetchone()

        if address_data:
            if address_data[1] == user_id:
                await update.message.reply_text(
                    'Ошибка ⚠️ - такой адрес уже привязан к вашему аккаунту.'
                )
            else:
                keyboard = [[InlineKeyboardButton("Поддержка", url="https://t.me/usdt_il")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text(
                    'Ошибка ⚠️ - такой адрес уже привязан к другому аккаунту\n'
                    'Проверьте правильность введенного адреса или обратитесь в поддержку',
                    reply_markup=reply_markup
                )
            await update.message.reply_text(
                'Пожалуйста, введите ваш адрес TRON снова.',
                reply_markup=ForceReply(selective=True)
            )
        else:
            energy_used, energy_limit, energy_remaining = get_energy_usage(text)
            free_bandwidth = get_bandwidth_data(text)

            cursor.execute('INSERT INTO user_addresses (user_id, tron_address, energy_remaining, free_bandwidth) VALUES (?, ?, ?, ?)',
                           (user_id, text, energy_remaining, free_bandwidth))
            
            conn.commit()

            await update.message.reply_text(
                f"Адрес добавлен успешно, ваш адрес - {text}, Оставшаяся энергия: {energy_remaining}, Свободное количество Bandwidth: {free_bandwidth}"
            )

            # Создаем задачи для асинхронного выполнения
            energy_task = asyncio.create_task(auto_energy_reg(update, text))
            band_task = asyncio.create_task(auto_band_reg(update, text))

            try:
                # Ждем выполнения обеих задач
                await asyncio.gather(energy_task, band_task)
                await update.message.reply_text(
                    "Автоматическое пополнение энергии и bandwidth выполнено успешно."
                )
            except Exception as e:
                await update.message.reply_text(
                    f"Произошла ошибка при автоматическом пополнении: {str(e)}"
                )
    else:
        await update.message.reply_text('Вы не зарегистрированы. Пожалуйста, используйте команду /start для регистрации.')
    
    conn.close()

def get_bandwidth_data(address):
    account_url = "https://apilist.tronscanapi.com/api/account"
    params = {'address': address}
    response = requests.get(account_url, params=params)
    
    if response.status_code == 200:
        data = response.json()
        bandwidth = data.get('bandwidth', {})
        net_remaining = bandwidth.get('netRemaining', 'Не доступно')
        return net_remaining
    else:
        return 'Ошибка'

# Function to get energy usage
def get_energy_usage(address):
    account_url = "https://apilist.tronscanapi.com/api/accountv2"
    params = {'address': address}
    response = requests.get(account_url, params=params)
    
    if response.status_code == 200:
        data = response.json()
        bandwidth = data.get('bandwidth', {})
        energy_used = bandwidth.get('energyUsed', 'Не доступно')
        energy_limit = bandwidth.get('energyLimit', 'Не доступно')
        energy_remaining = bandwidth.get('energyRemaining', 'Не доступно')
        return energy_used, energy_limit, energy_remaining
    else:
        return 'Ошибка', 'Ошибка', 'Ошибка'
    
# Define the fetch_tron_addresses function
def fetch_tron_addresses():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT tron_address FROM user_addresses')
    addresses = cursor.fetchall()
    conn.close()
    return [address[0] for address in addresses]

def get_transaction_count(address, start_timestamp, end_timestamp):
    chrome_options = Options()
    
    service = Service(CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    url = (
        f"https://tronscan.org/#/tools/advanced-filter?type=tx"
        f"&times={start_timestamp}%2C{end_timestamp}"
        f"&fromAddress={address}&token=TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t&imgUrl=https%3A%2F%2Fstatic.tronscan.org%2Fproduction%2Flogo%2Fusdtlogo.png&tokenName=Tether%20USD&tokenAbbr=USDT&relation=or"
    )
    
    driver.get(url)
    
    try:
        WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.XPATH, "//span[contains(text(), 'transaction(s) found')]"))
        )

        time.sleep(3)

        WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.XPATH, "//span[@class='tron-font-default-color']"))
        )
        
        transaction_count_element = driver.find_element(By.XPATH, "//span[@class='tron-font-default-color']")
        if transaction_count_element:
            return transaction_count_element.text.strip()
        else:
            return "Количество транзакций не найдено"
    except Exception as e:
        return f"Ошибка: {str(e)}"
    finally:
        driver.quit()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    chat_id = user.id

    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE chat_id = ?', (chat_id,))
    user_data = cursor.fetchone()

    if user_data:
        approved_index = None
        for i, column in enumerate(cursor.description):
            if column[0] == 'approved':
                approved_index = i
                break

        if approved_index is not None and len(user_data) > approved_index:
            if user_data[approved_index] == 1:
                await update.message.reply_text(
                    'Вы уже зарегистрированы и одобрены!\nВсе команды - /help'
                )
            else:
                await update.message.reply_text(
                    'Ваша заявка на регистрацию находится на рассмотрении. Пожалуйста, ожидайте одобрения администратора.'
                )
        else:
            await update.message.reply_text(
                'Ваша заявка на регистрацию находится на рассмотрении. Пожалуйста, ожидайте одобрения администратора.'
            )
    else:
        cursor.execute('INSERT INTO users (chat_id, approved) VALUES (?, 0)', (chat_id,))
        conn.commit()
        
        # Отправка уведомления администратору
        admin_chat_id = get_admin_chat_id()
        if admin_chat_id:
            keyboard = [
                [InlineKeyboardButton("Разрешить", callback_data=f'approve_{chat_id}'),
                 InlineKeyboardButton("Отклонить", callback_data=f'reject_{chat_id}')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await context.bot.send_message(
                chat_id=admin_chat_id,
                text=f"Пользователь: @{user.username} хочет воспользоваться ботом. Разрешить?",
                reply_markup=reply_markup
            )
        
        await update.message.reply_text(
            'Ваша заявка на регистрацию отправлена. Пожалуйста, ожидайте одобрения администратора.'
        )
    conn.close()

def get_admin_chat_id():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT chat_id FROM users WHERE admin = 1 LIMIT 1')
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

async def register(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    tron_address = update.message.text
    chat_id = update.message.chat_id

    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    # Проверяем, зарегистрирован ли пользователь
    cursor.execute('SELECT id FROM users WHERE chat_id = ?', (chat_id,))
    user_data = cursor.fetchone()

    if user_data:
        user_id = user_data[0]

        # Проверяем, существует ли адрес TRON
        cursor.execute('SELECT * FROM user_addresses WHERE tron_address = ?', (tron_address,))
        address_data = cursor.fetchone()

        if address_data:
            # Адрес уже существует
            keyboard = [[InlineKeyboardButton("Поддержка", url="https://t.me/usdt_il")]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(
                'Ошибка ⚠️ - такой адрес уже привязан к другому аккаунту\n'
                'Проверьте правильность введенного адреса или обратитесь в поддержку',
                reply_markup=reply_markup
            )

            await update.message.reply_text(
                'Пожалуйста, введите ваш адрес TRON снова.',
                reply_markup=ForceReply(selective=True)
            )
        else:
            # Добавляем новый адрес TRON
            _, _, energy_remaining = get_energy_usage(tron_address)
            free_bandwidth = get_bandwidth_data(tron_address)

            cursor.execute('INSERT INTO user_addresses (user_id, tron_address, energy_remaining, free_bandwidth) VALUES (?, ?, ?, ?)',
                           (user_id, tron_address, energy_remaining, free_bandwidth))
            conn.commit()

            await update.message.reply_text(
                f"Адрес добавлен успешно, ваш адрес - {tron_address}, Оставшаяся энергия: {energy_remaining}, Свободное количество Bandwidth: {free_bandwidth}"
            )

            # Вызываем функции автоматического пополнения энергии и bandwidth
            try:
                await auto_energy_reg(update, tron_address)
                await auto_band_reg(update, tron_address)
                await update.message.reply_text(
                    "Автоматическое пополнение энергии и bandwidth выполнено успешно."
                )
            except Exception as e:
                await update.message.reply_text(
                    f"Произошла ошибка при автоматическом пополнении: {str(e)}"
                )

    else:
        await update.message.reply_text('Вы не зарегистрированы. Пожалуйста, используйте команду /start для регистрации.')

    conn.close()

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.args:
        address = context.args[0]
        energy_used, energy_limit, energy_remaining = get_energy_usage(address)
        free_bandwidth = get_bandwidth_data(address)
        
        now = datetime.now()
        start_date = now - timedelta(days=30)
        start_timestamp = int(start_date.timestamp() * 1000)
        end_timestamp = int(now.timestamp() * 1000)
        
        transaction_count = get_transaction_count(address, start_timestamp, end_timestamp)
        transaction_cost = USDT_PER_TRANSACTION * int(transaction_count)
        
        response_message = (
            f"Данные для адреса {address}:\n"
            f"Использовано энергии: {energy_used}\n"
            f"Лимит энергии: {energy_limit}\n"
            f"Оставшаяся энергия: {energy_remaining}\n"
            f"Свободное количество Bandwidth: {free_bandwidth}\n"
            f"Количество транзакций за текущий месяц: {transaction_count}\n"
            f"Сумма транзакций: {transaction_cost:.2f} USDT"
        )
        await update.message.reply_text(response_message)
    else:
        await update.message.reply_text('Пожалуйста, укажите адрес после команды /stats.')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    help_text = (
        "Доступные команды:\n"
        "/start - Начать регистрацию\n"
        "/stats <адрес> - Получить статистику для указанного адреса TRON\n"
        "/profile - Показать профиль пользователя\n"
        "/ahelp - Показать команды админа\n"
        "/help - Показать это сообщение"
    )
    await update.message.reply_text(help_text)

async def admin_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.message.chat_id
    if not is_admin(chat_id):
        await update.message.reply_text("У вас нет прав для доступа к этой команде.")
        return
    else:
        help_text = (
            "Доступные команды:\n"
            "/apanel - просмотреть статистику пользователей\n"
            "/order <адрес> <количество> <срок в днях> - Отправить заказ\n"
            "/band <адрес> <количество> <срок в днях> - Арендовать Bandwidth для указанного адреса\n"
            "/aduser <user_id> <tron_address> - Добавить нового пользователя вручную\n"
            "/data - Поулчить статистику тразакций пользовтаелей в таблице exel\n"
            "/ahelp - Показать это сообщение"
        )
        await update.message.reply_text(help_text)

async def order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    
    if len(context.args) != 3:
        await update.message.reply_text('Пожалуйста, используйте формат: /order <адрес> <количество> <срок в днях>')
        return
    
    address, quantity, duration = context.args

    async with TelegramClient(SESSION_NAME, API_ID, API_HASH) as client:
        await client.send_message(
            TARGET_BOT_USERNAME,
            f"/order {address} {quantity} {duration}"
        )

    await update.message.reply_text(
        f"Количество бесплатных транзакций пополнено на +1!\n"
        f"Скоро USDT будут в вашем кошельке {address}!"
    )

async def band(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) != 3:
        await update.message.reply_text('Пожалуйста, используйте формат: /band <адрес> <количество> <срок в днях>')
        return
    
    address, amount_band, duration = context.args

    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    service = Service(CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        driver.get("https://tronenergy.market/")

         # Явное ожидание, пока страница загрузится
        wait = WebDriverWait(driver, 10)

        # Проверка невидимости известных элементов загрузки
        known_loaders = ['loading', 'some_other_loading_element_id']
        for loader in known_loaders:
            try:
                wait.until(EC.invisibility_of_element_located((By.ID, loader)))
            except Exception as e:
                print(f"Loader '{loader}' not found or already invisible: {e}")

        # Дополнительная задержка для надежности
        time.sleep(1)

        # Клик на 14-й элемент с классом "select-dropdown dropdown-trigger" для открытия первого выпадающего списка
        dropdown1_trigger = wait.until(EC.element_to_be_clickable((By.XPATH, "(//input[@class='select-dropdown dropdown-trigger'])[14]")))
        dropdown1_trigger.click()

        time.sleep(1)

         # Ожидание появления выпадающего меню и выбор опции "Bandwidth"
        bandwidth_option = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[text()='Bandwidth']")))
        bandwidth_option.click()
    
        time.sleep(1)

        # Ввод значения 1500
        amount_input = wait.until(EC.visibility_of_element_located((By.ID, "rent-resource-amount")))
        amount_input.clear()
        amount_input.send_keys(amount_band)

        time.sleep(1)

        # Клик на 15-й элемент с классом "select-dropdown dropdown-trigger" для открытия второго выпадающего списка
        dropdown2_trigger = wait.until(EC.element_to_be_clickable((By.XPATH, "(//input[@class='select-dropdown dropdown-trigger'])[15]")))
        dropdown2_trigger.click()

        time.sleep(1)

        one_day_option_xpath = "//ul[contains(@id, 'select-options')]//li[5]"
        one_day_option = wait.until(EC.presence_of_element_located((By.XPATH, one_day_option_xpath)))

        try:
            one_day_option = wait.until(EC.element_to_be_clickable((By.XPATH, one_day_option_xpath)))
            one_day_option.click()
        except Exception as e:
            print(f"Error while clicking on one_day_option: {e}")

        time.sleep(1)

        # Очистка поля ввода и запись значения адреса
        address_input = wait.until(EC.visibility_of_element_located((By.ID, "rent-trx-address")))
        address_input.clear()
        address_input.send_keys(address)

        time.sleep(1)

        # Извлечение значения из span с id "form-subtotal-value"
        price_span = wait.until(EC.visibility_of_element_located((By.ID, "form-subtotal-value")))
        price = price_span.text

        # Клик на кнопку с идентификатором "rent-button"
        rent_button = wait.until(EC.element_to_be_clickable((By.ID, "rent-button")))
        rent_button.click()

        time.sleep(1)

        # Клик на второй элемент с классом "btn-small custom-purple-small-button custom-purple-text modal-accept"
        accept_terms_button_xpath = "(//a[contains(@class, 'btn-small custom-purple-small-button custom-purple-text modal-accept')])[2]"
        accept_terms_button = wait.until(EC.element_to_be_clickable((By.XPATH, accept_terms_button_xpath)))
        accept_terms_button.click()

        time.sleep(1)

        # Очистка и ввод пароля в первый элемент с id "wallet-setup-password"
        password_input_xpath = "(//input[@id='wallet-setup-password'])[1]"
        password_input = wait.until(EC.visibility_of_element_located((By.XPATH, password_input_xpath)))
        password_input.clear()
        password_input.send_keys(pass_word)

        time.sleep(1)

        # Очистка и ввод пароля в первый элемент с id "wallet-setup-password-repeat"
        password_repeat_input_xpath = "(//input[@id='wallet-setup-password-repeat'])[1]"
        password_repeat_input = wait.until(EC.visibility_of_element_located((By.XPATH, password_repeat_input_xpath)))
        password_repeat_input.clear()
        password_repeat_input.send_keys(pass_word)

        time.sleep(1)

        # Клик на кнопку "Сохранить"
        save_button = wait.until(EC.element_to_be_clickable((By.ID, "wallet-setup-save")))
        save_button.click()

        time.sleep(1)

        # Клик на кнопку "Не сейчас"
        cancel_button_xpath = "//a[contains(@class, 'btn-flat modal-close waves-effect') and contains(@data-i18n, 'modal.wallet_export_advice.cancel')]"
        cancel_button = wait.until(EC.element_to_be_clickable((By.XPATH, cancel_button_xpath)))
        cancel_button.click()

        ## Извлечение текста из поля ввода и вывод его в терминал
        address_field = wait.until(EC.visibility_of_element_located((By.ID, "trx-recharge-address")))
        address_value = address_field.get_attribute("value")
        print("Text inside 'trx-recharge-address':", address_value)
        print("Total Price:", price, "TRX")

        # Задержка, чтобы дать время для выполнения предыдущих команд
        time.sleep(5)

        # Инициализация клиента Tron с использованием TronGrid и API-ключа
        client = Tron(HTTPProvider(api_key=api_key))
        priv_key = PrivateKey(bytes.fromhex(private_key_hex))

        # Укажите адреса отправителя и получателя
        from_addr = priv_key.public_key.to_base58check_address()
        to_addr = address_value  # Используйте значение, полученное из Selenium

        # Укажите сумму перевода в TRX (1 TRX = 1_000_000 Sun)
        amount = int(float(price) * 1_000_000)  # Перевод суммы в TRX

        # Создание транзакции
        txn = (
            client.trx.transfer(from_addr, to_addr, amount)
            .memo("Hello, Tron!")
            .build()
            .sign(priv_key)
        )

        # Отправка транзакции
        txid = txn.broadcast()

        print(f"Transaction ID: {txid}")

        # Обновление страницы
        driver.refresh()

         # Явное ожидание, пока страница загрузится
        wait = WebDriverWait(driver, 5)

        # Проверка невидимости известных элементов загрузки
        known_loaders = ['loading', 'some_other_loading_element_id']
        for loader in known_loaders:
            try:
                wait.until(EC.invisibility_of_element_located((By.ID, loader)))
            except Exception as e:
                print(f"Loader '{loader}' not found or already invisible: {e}")

        # Дополнительная задержка для надежности
        time.sleep(1)

        # Клик на 14-й элемент с классом "select-dropdown dropdown-trigger" для открытия первого выпадающего списка
        dropdown1_trigger = wait.until(EC.element_to_be_clickable((By.XPATH, "(//input[@class='select-dropdown dropdown-trigger'])[14]")))
        dropdown1_trigger.click()

        time.sleep(1)
    
        # Ожидание появления выпадающего меню и выбор опции "Bandwidth"
        bandwidth_option = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[text()='Bandwidth']")))
        bandwidth_option.click()
    
        time.sleep(1)

        # Ввод значения 1500
        amount_input = wait.until(EC.visibility_of_element_located((By.ID, "rent-resource-amount")))
        amount_input.clear()
        amount_input.send_keys(amount_band)

        time.sleep(1)
    
        # Клик на 15-й элемент с классом "select-dropdown dropdown-trigger" для открытия второго выпадающего списка
        dropdown2_trigger = wait.until(EC.element_to_be_clickable((By.XPATH, "(//input[@class='select-dropdown dropdown-trigger'])[15]")))
        dropdown2_trigger.click()

        time.sleep(1)
    
        one_day_option_xpath = "//ul[contains(@id, 'select-options')]//li[5]"
        one_day_option = wait.until(EC.presence_of_element_located((By.XPATH, one_day_option_xpath)))

        try:
            one_day_option = wait.until(EC.element_to_be_clickable((By.XPATH, one_day_option_xpath)))
            one_day_option.click()
        except Exception as e:
            print(f"Error while clicking on one_day_option: {e}")

        time.sleep(1)

        # Очистка поля ввода и запись значения адреса
        address_input = wait.until(EC.visibility_of_element_located((By.ID, "rent-trx-address")))
        address_input.clear()
        address_input.send_keys(address)

        time.sleep(1)
    
        # Извлечение значения из span с id "form-subtotal-value"
        price_span = wait.until(EC.visibility_of_element_located((By.ID, "form-subtotal-value")))
        price = price_span.text

        # Клик на кнопку с идентификатором "rent-button"
        rent_button = wait.until(EC.element_to_be_clickable((By.ID, "rent-button")))
        rent_button.click()

        # Ввод пароля в элемент с id "wallet-password-prompt-password"
        password_prompt_input = wait.until(EC.visibility_of_element_located((By.ID, "wallet-password-prompt-password")))
        password_prompt_input.clear()
        password_prompt_input.send_keys(pass_word)

        time.sleep(5)

        # Клик на кнопку с id "wallet-password-ok"
        wallet_password_ok_button = wait.until(EC.element_to_be_clickable((By.ID, "wallet-password-ok")))
        wallet_password_ok_button.click()

        time.sleep(100)    

        # Дополнительная задержка для надежности
        time.sleep(1)

        await update.message.reply_text(
                f"Вы успешно арендовали {amount_band} Bandwidth для адреса {address} на срок {duration} дней."
            )
    except Exception as e:
            await update.message.reply_text(
                f"Произошла ошибка при аренде Bandwidth: {str(e)}"
            )
    finally:
        driver.quit()

# Function to show the user's profile
async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    chat_id = user.id

    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM users WHERE chat_id = ?', (chat_id,))
    user_id = cursor.fetchone()

    if user_id:
        user_id = user_id[0]
        cursor.execute('SELECT tron_address, energy_remaining, free_bandwidth FROM user_addresses WHERE user_id = ?', (user_id,))
        addresses = cursor.fetchall()

        if addresses:
            profile_text = "Ваш профиль:\n"
            for address in addresses:
                tron_address, energy_remaining, free_bandwidth = address
                profile_text += (
                    f"Адрес TRON: {tron_address}\n"
                    f"Оставшаяся энергия: {energy_remaining}\n"
                    f"Свободное количество Bandwidth: {free_bandwidth}\n\n"
                )
            keyboard = [
                [InlineKeyboardButton("Добавить кошелек", callback_data='add_wallet')],
                [InlineKeyboardButton("Удалить кошелек", callback_data='delete_wallet')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(profile_text, reply_markup=reply_markup)
        else:
            await update.message.reply_text('У вас нет добавленных адресов. Пожалуйста, используйте команду /start для добавления адреса.')
    else:
        await update.message.reply_text('Вы не зарегистрированы. Пожалуйста, используйте команду /start для регистрации.')
    conn.close()

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == 'add_wallet':
        await query.message.reply_text('Пожалуйста, введите новый адрес TRON.', reply_markup=ForceReply(selective=True))

# Команда /data
async def data_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.message.chat_id
    if not is_admin(chat_id):
        await update.message.reply_text("У вас нет прав для доступа к этой команде.")
        return
    else:
        await update.message.reply_text("Ожидайте, идет обработка данных кошельков")
        
    
    addresses = fetch_tron_addresses()
    for address in addresses:
        filename = f"{address}.xlsx"
        generate_excel_for_address(address, filename)
        if os.path.exists(filename):
            try:
                await context.bot.send_document(chat_id, document=open(filename, 'rb'))
            except Exception as e:
                await update.message.reply_text(f"Ошибка при отправке файла {filename}: {str(e)}")
        else:
            await update.message.reply_text(f"Файл {filename} не был создан")

def fetch_tron_addresses():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT tron_address FROM user_addresses')
    addresses = cursor.fetchall()
    conn.close()
    return [address[0] for address in addresses]

def generate_excel_for_address(address, filename):
    start_date, end_date = get_start_and_end_of_month()
    
    transactions = get_transactions(address, start_date, end_date)
    
    usdt_transactions = filter_usdt_transactions(transactions)
    
    transactions_data = []
    for tx_hash in usdt_transactions:
        energy, bandwidth, timestamp, recipient, amount, trx_consumed, fee_limit = get_transaction_details(tx_hash)
        transactions_data.append((tx_hash, energy, bandwidth, timestamp, recipient, amount, trx_consumed, fee_limit))
    
    update_excel(transactions_data, filename)

def get_transaction_details(tx_id):
    url = f"https://apilist.tronscanapi.com/api/transaction-info?hash={tx_id}"
    response = requests.get(url)
    data = response.json()
    
    energy_used = data.get('cost', {}).get('energy_usage_total', 0)
    bandwidth_used = data.get('cost', {}).get('net_usage', 0)
    
    energy_fee = data.get('cost', {}).get('energy_fee', 0)
    net_fee = data.get('cost', {}).get('net_fee', 0)
    trx_consumed = (energy_fee + net_fee) / 1_000_000  # Convert from SUN to TRX

    fee_limit_sun = data.get('fee_limit', 0)
    fee_limit = fee_limit_sun / 1_000_000
    
    trc20_info = data.get('trc20TransferInfo', [])
    if trc20_info:
        trc20_info = trc20_info[0]
        amount = float(trc20_info.get('amount_str', 0)) / 1_000_000
        recipient = trc20_info.get('to_address', 'N/A')
    else:
        amount = 0
        recipient = 'N/A'
    
    timestamp = datetime.fromtimestamp(data.get('timestamp', 0) / 1000)
    
    return energy_used, bandwidth_used, timestamp, recipient, amount, trx_consumed, fee_limit

def get_start_and_end_of_month():
    today = datetime.today()
    start_date = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    next_month = start_date.replace(day=28) + timedelta(days=4)
    end_date = next_month - timedelta(days=next_month.day)
    end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
    return start_date, end_date

def get_transactions(address, start_date, end_date):
    transactions = []
    limit = 200
    start = 0
    
    while True:
        url = f"https://apilist.tronscanapi.com/api/transaction?address={address}&limit={limit}&start={start}"
        response = requests.get(url)
        data = response.json()
        batch = data.get('data', [])
        
        if not batch:
            break
        
        for tx in batch:
            timestamp = tx.get('timestamp')
            if timestamp:
                tx_date = datetime.fromtimestamp(timestamp / 1000)
                if start_date <= tx_date <= end_date:
                    transactions.append(tx)
        
        start += limit

    return transactions

def filter_usdt_transactions(transactions):
    usdt_contract_address = 'TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t'
    usdt_transactions = []
    
    for tx in transactions:
        contract_data = tx.get('contractData', [])
        
        if isinstance(contract_data, list):
            for contract in contract_data:
                if isinstance(contract, dict):
                    if contract.get('contract_address') == usdt_contract_address and contract.get('data'):
                        usdt_transactions.append(tx['hash'])
        elif isinstance(contract_data, dict):
            if contract_data.get('contract_address') == usdt_contract_address and contract_data.get('data'):
                usdt_transactions.append(tx['hash'])
        else:
            print(f"Unexpected contractData format: {contract_data}")
    
    return usdt_transactions

def update_excel(transactions_data, filename="transactions.xlsx"):
    file_exists = os.path.exists(filename)
    
    if file_exists:
        df = pd.read_excel(filename)
    else:
        df = pd.DataFrame(columns=["Txn Hash", "Amount (USDT)", "Recipient", "Timestamp", "Energy Used", "Bandwidth Used", "TRX Consumed", "Total Transaction Cost", "Fee Limit", "For Payment"])
    
    existing_hashes = set(df["Txn Hash"])
    
    new_data = []
    for tx_hash, energy, bandwidth, timestamp, recipient, amount, trx_consumed, fee_limit in transactions_data:
        if tx_hash not in existing_hashes:
            total_cost = calculate_transaction_cost(energy, bandwidth)
            if fee_limit >= total_cost:
                for_payment = (total_cost - trx_consumed) / 2
            else:
                for_payment = (fee_limit - trx_consumed) / 2
            new_data.append([tx_hash, amount, recipient, timestamp, energy, bandwidth, trx_consumed, total_cost, fee_limit, for_payment])
    
    if new_data:
        new_df = pd.DataFrame(new_data, columns=["Txn Hash", "Amount (USDT)", "Recipient", "Timestamp", "Energy Used", "Bandwidth Used", "TRX Consumed", "Total Transaction Cost", "Fee Limit", "For Payment"])
        df = pd.concat([df, new_df], ignore_index=True)
        
        total_energy = df["Energy Used"].sum()
        total_bandwidth = df["Bandwidth Used"].sum()
        total_trx_consumed = df["TRX Consumed"].sum()
        total_cost = df["Total Transaction Cost"].sum()
        fee_limit = df["Fee Limit"].sum()
        
        totals_df = pd.DataFrame([["Total", None, None, None, total_energy, total_bandwidth, total_trx_consumed, total_cost, fee_limit, None]], 
                                 columns=["Txn Hash", "Amount (USDT)", "Recipient", "Timestamp", "Energy Used", "Bandwidth Used", "TRX Consumed", "Total Transaction Cost", "Fee Limit", "For Payment"])
        df = pd.concat([df, totals_df], ignore_index=True)
        
        df.to_excel(filename, index=False)
        print(f"Excel file updated and saved as {filename}")

def calculate_transaction_cost(energy_used, bandwidth_used, bandwidth_cost_per_byte=0.00001, energy_cost_per_unit=0.00084):
    bandwidth_cost = bandwidth_used * bandwidth_cost_per_byte
    energy_cost = energy_used * energy_cost_per_unit
    total_transaction_cost = bandwidth_cost + energy_cost
    return total_transaction_cost

def generate_excel_for_address(address, filename):
    start_date, end_date = get_start_and_end_of_month()
    
    transactions = get_transactions(address, start_date, end_date)
    
    usdt_transactions = filter_usdt_transactions(transactions)
    
    transactions_data = []
    for tx_hash in usdt_transactions:
        energy, bandwidth, timestamp, recipient, amount, trx_consumed, fee_limit = get_transaction_details(tx_hash)
        transactions_data.append((tx_hash, energy, bandwidth, timestamp, recipient, amount, trx_consumed, fee_limit))
    
    update_excel(transactions_data, filename)

def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    init_db()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("ahelp", admin_help))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(CommandHandler("order", order))
    application.add_handler(CommandHandler("band", band))
    application.add_handler(CommandHandler("profile", show_profile))
    application.add_handler(CommandHandler("apanel", admin_panel))
    application.add_handler(CommandHandler("aduser", add_user))
    application.add_handler(CommandHandler("data", data_command))
    application.add_handler(CallbackQueryHandler(button_handler1, pattern='approve_|reject_'))
    application.add_handler(CallbackQueryHandler(button_handler2, pattern='add_wallet|delete_wallet|user_'))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, register))

    application.run_polling()

if __name__ == "__main__":
    main()