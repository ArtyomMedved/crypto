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
import secrets
from telegram.ext import Updater, CommandHandler, CallbackContext
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

# Ваши токены и настройки
TELEGRAM_TOKEN = '7283223352:AAGAhHAVwogRTD1U42_-OsHVpfc8gOONL48'
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
BASE_URL = "https://t.me/"
BOT_USERNAME = "freeTRC_Bot"

def init_db():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    # Проверяем и добавляем столбец 'approved', если его нет
    cursor.execute("PRAGMA table_info(users)")
    columns = [column[1] for column in cursor.fetchall()]
    if 'approved' not in columns:
        cursor.execute('''
        ALTER TABLE users ADD COLUMN approved INTEGER DEFAULT 0
        ''')

    # Проверяем и добавляем столбец 'ref_url', если его нет
    if 'ref_url' not in columns:
        cursor.execute('''
        ALTER TABLE users ADD COLUMN ref_url TEXT
        ''')

    # Проверяем и добавляем столбец 'coment', если его нет
    if 'coment' not in columns:
        cursor.execute('''
        ALTER TABLE users ADD COLUMN coment TEXT
        ''')

    # Проверяем и добавляем столбец 'language', если его нет
    if 'language' not in columns:
        cursor.execute('''
        ALTER TABLE users ADD COLUMN language TEXT DEFAULT 'en'
        ''')

    # Создание таблицы, если она не существует
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id INTEGER UNIQUE,
        admin INTEGER DEFAULT 0,
        date_added TEXT,
        approved INTEGER DEFAULT 0,
        ref_url TEXT,
        coment TEXT,
        language TEXT DEFAULT 'en'
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

# Function to generate a referral link
def generate_referral_link(user_id: int) -> str:
    referral_token = secrets.token_urlsafe(16)  # Generate a secure token
    return f"{BASE_URL}{BOT_USERNAME}?start={user_id}_{referral_token}"

# Handler for the /ref command
async def ref_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    referral_link = generate_referral_link(user_id)

    # Сохранение реферальной ссылки в базе данных
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''
    UPDATE users
    SET ref_url = ?
    WHERE chat_id = ?
    ''', (referral_link, user_id))
    conn.commit()
    conn.close()

    # Отправка сообщения с реферальной ссылкой
    await update.message.reply_text(f"Ваша реферальная ссылка: {referral_link}")

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
        await update.message.reply_text("List of users:", reply_markup=reply_markup)
    else:
        await update.message.reply_text("You do not have permission to access this panel.")

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
            f"Energy has been successfully registered for the address {address}."
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
            f"You have successfully rented Bandwidth for the {address} address for a period of 30 days."
        )
    except Exception as e:
        await update.message.reply_text(f"An error occurred when renting Bandwidth: {str(e)}")
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
            await update.message.reply_text('Error: The user ID must be a number.')
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
                await update.message.reply_text(f'User with ID {new_user_id} successfully added with address {tron_address}.')
            else:
                user_id = user_record[0]
                cursor.execute('SELECT id FROM user_addresses WHERE user_id = ?', (user_id,))
                address_record = cursor.fetchone()
                if address_record is None:
                    cursor.execute('INSERT INTO user_addresses (user_id, tron_address) VALUES (?, ?)', (user_id, tron_address))
                    conn.commit()
                    await update.message.reply_text(f'The address {tron_address} was successfully added for the user with the ID {new_user_id}.')
                else:
                    await update.message.reply_text(f'The address for the user with the ID {new_user_id} already exists.')

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
        date_added = 'No date has been set'

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
            text='Your registration application has been approved. Please enter your first TRON address.',
            reply_markup=ForceReply(selective=True)
        )
        await query.edit_message_text(text=f"The user with the ID {user_id} is approved.")
    elif query.data.startswith('reject_'):
        user_id = int(query.data.split('_')[1])
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM users WHERE chat_id = ?', (user_id,))
        conn.commit()
        conn.close()
        await context.bot.send_message(
            chat_id=user_id,
            text='Your application for registration has been rejected.'
        )
        await query.edit_message_text(text=f"The user with the ID {user_id} has been rejected.")
    else:
        print(f"Unexpected callback data: {query.data}")

# Второй обработчик
async def button_handler2(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == 'add_wallet':
        await query.message.reply_text('Please enter the new TRON address.', reply_markup=ForceReply(selective=True))
    elif query.data == 'delete_wallet':
        await query.message.reply_text('Please enter the TRON address that you want to delete.', reply_markup=ForceReply(selective=True))
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
                response = f"User: <a href='tg://user?id={user_id}'>{first_name}</a>:\n\n"
                for address, energy, bandwidth in addresses:
                    transaction_count = get_transaction_count(address, start_timestamp, end_timestamp)
                    response += (
                        f"username: @{username}\n"
                        f"ID: <code>{user_id}</code>\n"
                        f"Address: <code>{address}</code>\n"
                        f"Energy: {energy}\n"
                        f"Free bandwidth: {bandwidth}\n"
                        f"The number of transactions for the current month: {transaction_count}\n"
                        f"Date of addition: {date_added.strftime('%Y-%m-%d %H:%M:%S')}\n"
                        f"Remaining subscription time: {remaining_days} дней\n\n"
                    )
            else:
                response = f"The user {first_name} has no connected addresses.\n\nDate of addition: {date_added.strftime('%Y-%m-%d %H:%M:%S')}\nRemaining subscription time: {remaining_days} days"

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
                            'Error ⚠️ - this address is already linked to your account.'
                        )
                    else:
                        keyboard = [[InlineKeyboardButton("Поддержка", url="https://t.me/usdt_il")]]
                        reply_markup = InlineKeyboardMarkup(keyboard)
                        await message.reply_text(
                            'Error ⚠️ - this address is already linked to another account\n'
                            'Check that the entered address is correct or contact support',
                            reply_markup=reply_markup
                        )
                    await message.reply_text(
                        'Please enter your TRON address again.',
                        reply_markup=ForceReply(selective=True)
                    )
                else:
                    energy_used, energy_limit, energy_remaining = get_energy_usage(text)
                    free_bandwidth = get_bandwidth_data(text)

                    cursor.execute('INSERT INTO user_addresses (user_id, tron_address, energy_remaining, free_bandwidth) VALUES (?, ?, ?, ?)',
                                   (user_id, text, energy_remaining, free_bandwidth))
                    conn.commit()

                    await message.reply_text(
                        f"The address was added successfully, your address - {text}, Remaining energy: {energy_remaining}, Free Bandwidth Amount: {free_bandwidth}"
                    )

                    # Создаем задачи для асинхронного выполнения
                    energy_task = asyncio.create_task(auto_energy_reg(update, text))
                    band_task = asyncio.create_task(auto_band_reg(update, text))

                    try:
                        # Ждем выполнения обеих задач
                        await asyncio.gather(energy_task, band_task)
                        await message.reply_text(
                            "Automatic replenishment of energy and bandwidth has been completed successfully."
                        )
                    except Exception as e:
                        await message.reply_text(
                            f"An error occurred during automatic replenishment: {str(e)}"
                        )
            else:
                await message.reply_text('You are not registered. Please use the /start command to register.')
            conn.close()
        
        # Обрабатываем удаление адреса TRON
        elif 'the TRON address that you want to delete' in reply_text:
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
                    await message.reply_text(f'The {tron_address} wallet has been successfully deleted.')
                else:
                    await message.reply_text('Error: the wallet with this address was not found!')
            conn.close()
        
        # Обрабатываем запрос на добавление пользователя
        elif 'The ID of the user you want to add' in reply_text:
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
            return "The number of transactions was not found"
    except Exception as e:
        return f"Mistake: {str(e)}"
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
                    'You are already registered and approved!\nAll commands are /help'
                )
            else:
                await update.message.reply_text(
                    'Your application for registration is under consideration by the administrator. Please wait for approval. If you have received an invitation, you can speed up the registration process by clicking on the referral link.'
                )
        else:
            await update.message.reply_text(
                'Your registration application is under consideration by the administrator. Please wait for approval. If you have received an invitation, you can speed up the registration process by clicking on the referral link.'
            )
    else:
        cursor.execute('INSERT INTO users (chat_id, approved) VALUES (?, 0)', (chat_id,))
        conn.commit()
        
        # Отправка уведомления администратору
        admin_chat_id = get_admin_chat_id()
        if admin_chat_id:
            keyboard = [
                [InlineKeyboardButton("Allow", callback_data=f'approve_{chat_id}'),
                 InlineKeyboardButton("Reject", callback_data=f'reject_{chat_id}')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await context.bot.send_message(
                chat_id=admin_chat_id,
                text=f"User: @{user.username} he wants to use a bot. Allow it?",
                reply_markup=reply_markup
            )
        
        await update.message.reply_text(
            'Your registration request has been sent. Please wait for the administrators approval.'
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
                'Error ⚠️ - this address is already linked to another account\n'
                'Check that the entered address is correct or contact support',
                reply_markup=reply_markup
            )

            await update.message.reply_text(
                'Please enter your TRON address again.',
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
                f"The address was added successfully, your address - {tron_address}, Remaining energy: {energy_remaining}, Free Bandwidth Amount: {free_bandwidth}"
            )

            # Вызываем функции автоматического пополнения энергии и bandwidth
            try:
                await auto_energy_reg(update, tron_address)
                await auto_band_reg(update, tron_address)
                await update.message.reply_text(
                    "Automatic replenishment of energy and bandwidth has been completed successfully."
                )
            except Exception as e:
                await update.message.reply_text(
                    f"An error occurred during automatic replenishment: {str(e)}"
                )

    else:
        await update.message.reply_text('You are not registered. Please use the /start command to register.')

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
            f"Address information {address}:\n"
            f"Energy used: {energy_used}\n"
            f"Energy limit: {energy_limit}\n"
            f"Remaining energy: {energy_remaining}\n"
            f"Free Bandwidth Amount: {free_bandwidth}\n"
            f"The number of transactions for the current month: {transaction_count}\n"
            f"Transaction amount: {transaction_cost:.2f} USDT"
        )
        await update.message.reply_text(response_message)
    else:
        await update.message.reply_text('Please enter the address after the /stats command.')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    help_text = (
        "Available commands:\n"
        "/start - Start registration\n"
        "/stats <address> - Get statistics for the specified TRON address\n"
        "/profile - Show user profile\n"
        "/ahelp - Show admin commands\n"
        "/help - Show this message"
    )
    await update.message.reply_text(help_text)

async def admin_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.message.chat_id
    if not is_admin(chat_id):
        await update.message.reply_text("You do not have permission to access this command.")
        return
    else:
        help_text = (
            "Available commands:\n"
            "/apanel - view user statistics\n"
            "/order <address> <quantity> <time in days> - Send the order\n"
            "/band <address> <quantity> <period in days> - Rent Bandwidth for the specified address\n"
            "/aduser <user_id> <tron_address> - Add a new user manually\n"
            "/data - To improve the statistics of user transactions in the exel table\n"
            "/ahelp - Show this message"
        )
        await update.message.reply_text(help_text)

async def order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    
    if len(context.args) != 3:
        await update.message.reply_text('Please use the format: /order <address> <quantity> <period in days>')
        return
    
    address, quantity, duration = context.args

    async with TelegramClient(SESSION_NAME, API_ID, API_HASH) as client:
        await client.send_message(
            TARGET_BOT_USERNAME,
            f"/order {address} {quantity} {duration}"
        )

    await update.message.reply_text(
        f"The number of free transactions has been replenished by +1!\n"
        f"Soon USDT will be in your wallet {address}!"
    )

async def band(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) != 3:
        await update.message.reply_text('Please use the format: /band <address> <quantity> <period in days>')
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
                f"You have successfully rented the {amount_band} Bandwidth for the {address} address for a period of {duration} days."
            )
    except Exception as e:
            await update.message.reply_text(
                f"An error occurred when renting Bandwidth: {str(e)}"
            )
    finally:
        driver.quit()

async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    chat_id = user.id

    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    # Получаем user_id и ref_url для текущего пользователя
    cursor.execute('SELECT id, ref_url FROM users WHERE chat_id = ?', (chat_id,))
    user_data = cursor.fetchone()

    if user_data:
        user_id, ref_url = user_data
        
        # Экранирование реферальной ссылки (HTML)
        ref_url_escaped = ref_url.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&#39;')
        
        # Получаем адреса пользователя
        cursor.execute('SELECT tron_address, energy_remaining, free_bandwidth FROM user_addresses WHERE user_id = ?', (user_id,))
        addresses = cursor.fetchall()

        profile_text = "Your profile:\n"
        if addresses:
            for address in addresses:
                tron_address, energy_remaining, free_bandwidth = address
                profile_text += (
                    f"TRON Address: {tron_address}\n"
                    f"Remaining energy: {energy_remaining}\n"
                    f"Free Bandwidth Amount: {free_bandwidth}\n\n"
                )
            
            # Добавляем гиперссылку в формате HTML
            profile_text += f"Your referral link: <a href=\"{ref_url_escaped}\">➡️Click ME⬅️</a>\n"

            # Создаем клавиатуру
            keyboard = [
                [InlineKeyboardButton("Add a wallet", callback_data='add_wallet')],
                [InlineKeyboardButton("Delete a wallet", callback_data='delete_wallet')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(profile_text, reply_markup=reply_markup, parse_mode='HTML')
        else:
            profile_text += 'You dont have any addresses added.\n'
            # Добавляем гиперссылку в формате HTML даже если нет адресов
            profile_text += f"Your referral link: <a href=\"{ref_url_escaped}\">➡️Click ME⬅️</a>\n"
            keyboard = [
                [InlineKeyboardButton("Add a wallet", callback_data='add_wallet')],
                [InlineKeyboardButton("Delete a wallet", callback_data='delete_wallet')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(profile_text, reply_markup=reply_markup, parse_mode='HTML')
    else:
        await update.message.reply_text('You are not registered. Please use the /start command to register.')
    
    conn.close()

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == 'add_wallet':
        await query.message.reply_text('Please enter a new TRON address.', reply_markup=ForceReply(selective=True))

# --------------------------------------------------------------------------------------------------------------------------
# exel function

async def data_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.message.chat_id
    if not is_admin(chat_id):
        await update.message.reply_text("You don't have the rights to access this command.")
        return
    else:
        await update.message.reply_text("Expect that wallet data is being processed")
        
    addresses = fetch_tron_addresses()
    all_data = []

    for address in addresses:
        filename = f"{address}.xlsx"
        generate_excel_for_address(address, filename)
        if os.path.exists(filename):
            try:
                await context.bot.send_document(chat_id, document=open(filename, 'rb'))
                df = pd.read_excel(filename)
                all_data.append(df)
            except Exception as e:
                await update.message.reply_text(f"Error sending the file {filename}: {str(e)}")
        else:
            await update.message.reply_text(f"The {filename} file was not created")
    
    if all_data:
        combined_df = pd.concat(all_data, ignore_index=True)
        combined_filename = "combined_transactions.xlsx"
        combined_df.to_excel(combined_filename, index=False)
        try:
            await context.bot.send_document(chat_id, document=open(combined_filename, 'rb'))
        except Exception as e:
            await update.message.reply_text(f"Error when sending a shared file {combined_filename}: {str(e)}")

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

# ---------------------------------------------------------------------------------------------------------------------------
# Function to update the energy and bandwidth for all addresses
def update_energy_bandwidth():
    while True:
        addresses = fetch_tron_addresses()
        for address in addresses:
            _, _, energy_remaining = get_energy_usage(address)
            free_bandwidth = get_bandwidth_data(address)
            
            # Update the database
            conn = sqlite3.connect('users.db')
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE user_addresses
                SET energy_remaining = ?, free_bandwidth = ?
                WHERE tron_address = ?
            ''', (energy_remaining, free_bandwidth, address))
            conn.commit()
            conn.close()

            # Print the updated values to the terminal
            print(f"Кошелек: {address}")
            print(f"Новое energy_remaining: {energy_remaining}")
            print(f"Новое free_bandwidth: {free_bandwidth}")
            print(f"")

            # Sleep for 10 seconds before updating the next address
            time.sleep(10)

# Function to start the background thread
def start_update_thread():
    update_thread = Thread(target=update_energy_bandwidth)
    update_thread.daemon = True
    update_thread.start()

# Start the update thread
start_update_thread()

# ---------------------------------------------------------------------------------------------------------------------------

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
    application.add_handler(CommandHandler('ref', ref_command))
    application.add_handler(CallbackQueryHandler(button_handler1, pattern='approve_|reject_'))
    application.add_handler(CallbackQueryHandler(button_handler2, pattern='add_wallet|delete_wallet|user_'))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, register))

    application.run_polling()

if __name__ == "__main__":
    main()