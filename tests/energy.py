import requests

def get_energy_usage(address):
    # URL для получения данных о аккаунте
    account_url = "https://apilist.tronscanapi.com/api/accountv2"
    params = {
        'address': address
    }
    
    response = requests.get(account_url, params=params)
    
    if response.status_code == 200:
        data = response.json()
        
        # Печатаем весь ответ для диагностики
        print("Ответ API:", data)
        
        # Извлечение данных о энергии из JSON-ответа
        bandwidth = data.get('bandwidth', {})
        energy_used = bandwidth.get('energyUsed', 'Не доступно')
        energy_limit = bandwidth.get('energyLimit', 'Не доступно')
        energy_remaining = bandwidth.get('energyRemaining', 'Не доступно')
        
        return energy_used, energy_limit, energy_remaining
    else:
        print("Ошибка при запросе данных о аккаунте:", response.status_code)
        return 'Ошибка', 'Ошибка', 'Ошибка'

# Адрес TRON
address = 'TGfWsfVxVK4PMDo3w6rmQwATdF7pVE5wwK'

# Получение данных о потреблении энергии
energy_used, energy_limit, energy_remaining = get_energy_usage(address)
print(f"Использовано энергии: {energy_used}")
print(f"Лимит энергии: {energy_limit}")
print(f"Оставшаяся энергия: {energy_remaining}")