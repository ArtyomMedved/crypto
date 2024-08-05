import sqlite3
import requests
import time
import asyncio
from telethon import TelegramClient
from telethon.errors import RPCError, SessionPasswordNeededError
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from tronpy import Tron
from tronpy.keys import PrivateKey
from tronpy.providers import HTTPProvider
from telethon import TelegramClient, events
from telethon.errors import RPCError, SessionPasswordNeededError
import re

# Telegram and API configuration
API_ID = '26744762'
API_HASH = '71dfb38f90351d1b25ef1818ba86b905'
SESSION_NAME = 'YOUR_SESSION_NAME'
TARGET_BOT_USERNAME = '@TRXEnergyMarket_bot'
CHROMEDRIVER_PATH = '/usr/local/bin/chromedriver'
pass_word = "MedvedevArtyom08"
api_key = "9250cd97-47a4-42e8-a0c9-212ab222169c"
private_key_hex = "471514b3bdbbf7d275e987933eb7bd1771b0ea09df05c8cd6c532c2bd0a31a1e"

# Количество и даты для rebuy
energy_buy = "60000"
time_to_buy_energy = "3" # В днях
band_buy = "1600"
time_to_buy_band = "3" # 7 - столбик в выборе днях на сайте (3 дня)

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
    
def fetch_tron_addresses():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT tron_address FROM user_addresses')
    addresses = cursor.fetchall()
    conn.close()
    return [address[0] for address in addresses]

async def update_energy_user(address):
    try:
        async with TelegramClient(SESSION_NAME, API_ID, API_HASH) as client:
            # Отправляем сообщение
            message = await client.send_message(
                TARGET_BOT_USERNAME,
                f"/order {address} {energy_buy} {time_to_buy_energy}"
            )

            # Определяем функцию для обработки ответного сообщения
            @client.on(events.NewMessage(chats=TARGET_BOT_USERNAME, reply_to=message.id))
            async def handler(event):
                response = event.message.message
                print(f"Ответ от бота для {address}: {response}")
                
                # Извлекаем сумму из ответа
                match = re.search(r'OБЩАЯ СУММА ПЛАТЕЖА:\s*([0-9]+\.[0-9]+) TRX', response)
                if match:
                    amount_energy = float(match.group(1)) # сумма покупки energy
                    print(f"Сумма платежа для {address}: {amount_energy} TRX")

            # Убедитесь, что клиент продолжает работать, чтобы получить сообщение
            await client.run_until_disconnected()

    except (RPCError, SessionPasswordNeededError) as e:
        print(f"Ошибка Telethon для {address}: {e}")
    except Exception as e:
        print(f"Ошибка при авто-регистрации энергии для адреса {address}: {str(e)}")

async def update_band_user(address):
    print(f"Starting bandwidth purchase for address: {address}")
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    service = Service(CHROMEDRIVER_PATH)
    
    try:
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.get("https://tronenergy.market/")
        wait = WebDriverWait(driver, 5)

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

        # Ввод значения из band_buy
        amount_input = wait.until(EC.visibility_of_element_located((By.ID, "rent-resource-amount")))
        amount_input.clear()
        amount_input.send_keys(band_buy)

        time.sleep(1)

        # Клик на 15-й элемент с классом "select-dropdown dropdown-trigger" для открытия второго выпадающего списка
        dropdown2_trigger = wait.until(EC.element_to_be_clickable((By.XPATH, "(//input[@class='select-dropdown dropdown-trigger'])[15]")))
        dropdown2_trigger.click()

        time.sleep(1)

        one_day_option_xpath = "//ul[contains(@id, 'select-options')]//li[7]"
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

        # Ввод значения из band_buy
        amount_input = wait.until(EC.visibility_of_element_located((By.ID, "rent-resource-amount")))
        amount_input.clear()
        amount_input.send_keys(band_buy)

        time.sleep(1)

        # Клик на 15-й элемент с классом "select-dropdown dropdown-trigger" для открытия второго выпадающего списка
        dropdown2_trigger = wait.until(EC.element_to_be_clickable((By.XPATH, "(//input[@class='select-dropdown dropdown-trigger'])[15]")))
        dropdown2_trigger.click()

        time.sleep(1)

        one_day_option_xpath = "//ul[contains(@id, 'select-options')]//li[7]"
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

        time.sleep(40)    

        # Дополнительная задержка для надежности
        time.sleep(1)

        print(f"Bandwidth purchase completed successfully for address: {address}")
    except Exception as e:
        print(f"Error in bandwidth purchase for address {address}: {str(e)}")
    finally:
        try:
            driver.quit()
        except Exception as e:
            print(f"Error closing the driver: {str(e)}")

def update_energy_bandwidth():
        addresses = fetch_tron_addresses()
        for address in addresses:
            try:
                print(f"Fetching energy and bandwidth for {address}")
                
                energy_data = get_energy_usage(address)
                energy_remaining = energy_data[2]
                
                free_bandwidth = get_bandwidth_data(address)
                print(f"Energy remaining: {energy_remaining}, Free bandwidth: {free_bandwidth}")

                # # Update the database
                # conn = sqlite3.connect('users.db')
                # cursor = conn.cursor()
                # cursor.execute('''
                #     UPDATE user_addresses
                #     SET energy_remaining = ?, free_bandwidth = ?
                #     WHERE tron_address = ?
                # ''', (energy_remaining, free_bandwidth, address))
                # conn.commit()
                # conn.close()

                if energy_remaining != 'Не доступно' and int(energy_remaining) < 60000:
                    print(f"Low energy for {address}. Initiating energy registration.")
                    asyncio.run(update_energy_user(address))

                time.sleep(3)

                if free_bandwidth != 'Не доступно' and int(free_bandwidth) < 400:
                    print(f"Low free bandwidth for {address}. Initiating bandwidth purchase.")
                    asyncio.run(update_band_user(address))

                time.sleep(5)

            except Exception as e:
                print(f"Error updating data for {address}: {str(e)}")

# Start the update process
update_energy_bandwidth()
