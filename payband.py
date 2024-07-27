from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
import time
from tronpy import Tron
from tronpy.keys import PrivateKey
from tronpy.providers import HTTPProvider


# Установка опций Chrome
chrome_options = Options()
chrome_options.add_argument("--start-maximized")

# Инициализация веб-драйвера
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

# Переменные
address = "TVpo91xSEChP5ipV49diQu7kUTAYbbGu8y"
bandwidth_value = "1500"
pass_word = "MedvedevArtyom2008"

try:
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

    # Ввод значения 1500
    amount_input = wait.until(EC.visibility_of_element_located((By.ID, "rent-resource-amount")))
    amount_input.clear()
    amount_input.send_keys(bandwidth_value)

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

    # Ввод значения 1500
    amount_input = wait.until(EC.visibility_of_element_located((By.ID, "rent-resource-amount")))
    amount_input.clear()
    amount_input.send_keys(bandwidth_value)

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

    time.sleep(1)


finally:
    # Закрытие браузера
    driver.quit()
