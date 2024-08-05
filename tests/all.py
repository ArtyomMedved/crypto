import requests
from datetime import datetime, timedelta

# Константа для расчета суммы транзакций в USDT
USDT_PER_TRANSACTION = 29.8

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
        print("Ошибка при запросе данных о аккаунте:", response.status_code)
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
        print("Ошибка при запросе данных о аккаунте:", response.status_code)
        return 'Ошибка', 'Ошибка', 'Ошибка'

def get_monthly_transactions_count(address):
    now = datetime.now()
    start_of_month = datetime(now.year, now.month, 1)
    end_of_month = (start_of_month + timedelta(days=31)).replace(day=1) - timedelta(milliseconds=1)
    start_timestamp = int(start_of_month.timestamp() * 1000)
    end_timestamp = int(end_of_month.timestamp() * 1000)
    
    base_url = "https://apilist.tronscanapi.com/api/transaction"
    params = {
        'address': address,
        'limit': 200,
        'start': start_timestamp,
        'end': end_timestamp
    }
    
    response = requests.get(base_url, params=params)
    
    if response.status_code == 200:
        data = response.json()
        transactions = data.get('data', [])
        return len(transactions)
    else:
        print("Ошибка при запросе данных:", response.status_code)
        return 0

# Адрес TRON
address = 'TGfWsfVxVK4PMDo3w6rmQwATdF7pVE5wwK'

# Получение данных о потреблении энергии
energy_used, energy_limit, energy_remaining = get_energy_usage(address)
print(f"Использовано энергии: {energy_used}")
print(f"Лимит энергии: {energy_limit}")
print(f"Оставшаяся энергия: {energy_remaining}")

# Получение свободного количества Bandwidth
free_bandwidth = get_bandwidth_data(address)
print(f"Свободное количество Bandwidth: {free_bandwidth}")

# Получение количества транзакций за текущий месяц
transaction_count = get_monthly_transactions_count(address)
total_transaction_sum_usdt = transaction_count * USDT_PER_TRANSACTION

print(f"Количество транзакций за текущий месяц: {transaction_count}")
print(f"Сумма транзакций: {total_transaction_sum_usdt:.2f} USDT")