from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import time

# Установка опций Chrome
chrome_options = Options()
chrome_options.add_argument("--start-maximized")

# Инициализация веб-драйвера
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

try:
    # Открытие сайта
    driver.get("https://tronenergy.market/")
    
    # Явное ожидание, пока поле для ввода будет доступно
    wait = WebDriverWait(driver, 10)
    
    # Ввод значения 1500
    amount_input = wait.until(EC.visibility_of_element_located((By.ID, "rent-resource-amount")))
    amount_input.clear()
    amount_input.send_keys("1500")

    time.sleep(2)
    
    # Клик на 14-й элемент с классом "select-dropdown dropdown-trigger" для открытия первого выпадающего списка
    dropdown1_trigger = wait.until(EC.element_to_be_clickable((By.XPATH, "(//input[@class='select-dropdown dropdown-trigger'])[14]")))
    dropdown1_trigger.click()
    
    # Ожидание появления выпадающего меню и выбор опции "Bandwidth"
    bandwidth_option = wait.until(EC.element_to_be_clickable((By.XPATH, "//ul[@id='select-options-b151adce-176b-a963-d69d-503943c0aa1d']//span[text()='Bandwidth']")))
    bandwidth_option.click()
    
    # Клик на элемент для открытия второго выпадающего списка (проверяем 14-й элемент аналогично)
    dropdown2_trigger = wait.until(EC.element_to_be_clickable((By.XPATH, "(//input[@class='select-dropdown dropdown-trigger'])[14]")))
    dropdown2_trigger.click()
    
    # Ожидание появления выпадающего меню и выбор опции "1 дни"
    days_option = wait.until(EC.element_to_be_clickable((By.XPATH, "//ul[@id='select-options-c6efaa3a-ae03-c0a3-b0fe-69c7f867b058']//span[contains(text(), '1 дни')]")))
    days_option.click()

finally:
    # Закрытие браузера
    driver.quit()
