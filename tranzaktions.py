from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def get_transaction_count(address, start_timestamp, end_timestamp):
    chrome_options = Options()
    # chrome_options.add_argument("--headless")  # Запуск в фоновом режиме
    
    service = Service('/usr/local/bin/chromedriver')  # Убедитесь, что указываете правильный путь
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    url = (
        f"https://tronscan.org/#/tools/advanced-filter?type=tx"
        f"&times={start_timestamp}%2C{end_timestamp}"
        f"&fromAddress={address}&relation=or"
    )
    
    driver.get(url)
    
    try:
        # Дождитесь, пока появится элемент, который указывает, что данные загружены
        WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.XPATH, "//span[contains(text(), 'transaction(s) found')]"))
        )

        time.sleep(1)

        # Дождитесь загрузки элемента с числом транзакций
        WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.XPATH, "//span[@class='tron-font-default-color']"))
        )
        
        # Найдите элемент с количеством транзакций
        transaction_count_element = driver.find_element(By.XPATH, "//span[@class='tron-font-default-color']")
        if transaction_count_element:
            return transaction_count_element.text.strip()
        else:
            return "Количество транзакций не найдено"
    except Exception as e:
        return f"Ошибка: {str(e)}"
    finally:
        driver.quit()

# Пример использования
address = "TVpo91xSEChP5ipV49diQu7kUTAYbbGu8y"
start_timestamp = 1719781200000
end_timestamp = 1722027599999

transaction_count = get_transaction_count(address, start_timestamp, end_timestamp)
print(f"Количество транзакций: {transaction_count}")
