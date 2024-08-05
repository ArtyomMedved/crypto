import time
import pyautogui
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Путь к вашему расширению
extension_path = "/Users/artemmedvedev/Desktop/crypto/IBNEJDFJMMKPCNLPEBKLMNKOEOIHOFEC_4_1_9_0.crx"

# Настраиваем драйвер Chrome с загрузкой расширения
options = webdriver.ChromeOptions()
options.add_extension(extension_path)
options.add_argument("--start-maximized")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# Переходим на страницу Google
driver.get("https://www.google.com")


# Координаты кнопки расширений (приблизительные, нужно определить вручную)
extension_button_coords = (1300, 80)  # Пример координат, нужно заменить на реальные

# Координаты кнопки расширения TronLink (приблизительные, нужно определить вручную)
tronlink_extension_coords = (1200, 260)  # Пример координат, нужно заменить на реальные

# Нажимаем на кнопку расширений
pyautogui.click(extension_button_coords)
time.sleep(1)  # Ждем одну секунду для открытия меню

# Нажимаем на расширение TronLink
pyautogui.click(tronlink_extension_coords)

# Ждем 5 секунд перед закрытием браузера
time.sleep(5)
driver.quit()