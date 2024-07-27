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
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telethon import TelegramClient
import time
from tronpy import Tron
from tronpy.keys import PrivateKey
from tronpy.providers import HTTPProvider

# Ваши токены и настройки
TELEGRAM_TOKEN = '7233049532:AAGgroWUXMFoqq0VuqrVHVZU1NzecuLG0oY'
API_ID = '26744762'  # ID API, полученный от my.telegram.org
API_HASH = '71dfb38f90351d1b25ef1818ba86b905'  # Хэш API, полученный от my.telegram.org
SESSION_NAME = 'YOUR_SESSION_NAME'  # Имя вашей сессии
TARGET_BOT_USERNAME = '@TRXEnergyMarket_bot'

# Путь к драйверу Chrome
CHROMEDRIVER_PATH = '/usr/local/bin/chromedriver'

USDT_PER_TRANSACTION = 29.8

pass_word = "MedvedevArtyom08" # пароль для врмененного акаунта кошелька для оплаты bandwidth 
api_key = "9250cd97-47a4-42e8-a0c9-212ab222169c"  # api key from TRONGRID
# Введите свой приватный ключ
private_key_hex = "471514b3bdbbf7d275e987933eb7bd1771b0ea09df05c8cd6c532c2bd0a31a1e" # from tronlik

def init_db():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id INTEGER UNIQUE,
        tron_address TEXT UNIQUE,
        energy_remaining TEXT,
        free_bandwidth TEXT
    )
    ''')
    conn.commit()
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

def get_transaction_count(address, start_timestamp, end_timestamp):
    chrome_options = Options()
    # chrome_options.add_argument("--headless")  # Запуск в фоновом режиме
    
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
    conn.close()

    if user_data:
        await update.message.reply_text(
            'Вы уже зарегистрированы!\nВсе команды - /help'
        )
    else:
        await update.message.reply_text(
            rf'Привет {user.mention_html()}! Пожалуйста, введите ваш адрес TRON.',
            parse_mode='HTML',
            reply_markup=ForceReply(selective=True),
        )

async def register(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    tron_address = update.message.text
    chat_id = update.message.chat_id

    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE tron_address = ?', (tron_address,))
    address_data = cursor.fetchone()

    if address_data:
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
        _, _, energy_remaining = get_energy_usage(tron_address)
        free_bandwidth = get_bandwidth_data(tron_address)

        cursor.execute('INSERT INTO users (chat_id, tron_address, energy_remaining, free_bandwidth) VALUES (?, ?, ?, ?)', 
                       (chat_id, tron_address, energy_remaining, free_bandwidth))
        conn.commit()
        conn.close()

        await update.message.reply_text(
            f"Регистрация прошла успешно, ваш адрес - {tron_address}, Оставшаяся энергия: {energy_remaining}, Свободное количество Bandwidth: {free_bandwidth}"
        )

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
        "/order <адрес> <количество> <срок в днях> - Отправить заказ\n"
        "/band <адрес> <количество> <срок в днях> - Арендовать Bandwidth для указанного адреса\n"
        "/help - Показать это сообщение"
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

def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    init_db()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(CommandHandler("order", order))
    application.add_handler(CommandHandler("band", band))

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, register))

    application.run_polling()

if __name__ == "__main__":
    main()
