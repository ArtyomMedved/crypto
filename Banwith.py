import requests

# URL для API запроса
url = 'https://apilist.tronscanapi.com/api/account?address=TGfWsfVxVK4PMDo3w6rmQwATdF7pVE5wwK'

# Выполнение GET-запроса
response = requests.get(url)

# Проверка успешности запроса
if response.status_code == 200:
    # Парсинг JSON-ответа
    data = response.json()
    
    # Извлечение значения netRemaining из секции bandwidth
    if 'bandwidth' in data and 'netRemaining' in data['bandwidth']:
        net_remaining_value = data['bandwidth']['netRemaining']
        print("Значение 'netRemaining':", net_remaining_value)
    else:
        print("'netRemaining' не найден в секции 'bandwidth'.")
else:
    print("Ошибка при выполнении запроса:", response.status_code)