import requests

def get_transaction_resources(tx_id):
    url = f"https://apilist.tronscanapi.com/api/transaction-info?hash={tx_id}"
    response = requests.get(url)
    data = response.json()
    
    # Извлечение информации об использовании энергии и пропускной способности
    energy_used = data.get('cost', {}).get('energy_usage_total', 'N/A')
    bandwidth_used = data.get('cost', {}).get('net_usage', 'N/A')
    
    return energy_used, bandwidth_used

tx_id = "755b2443fe11e62665e1ba315b6d9564e3cc0f1cb5963b41b714b19e83adea0d"
energy, bandwidth = get_transaction_resources(tx_id)

print(f"Energy used: {energy}")
print(f"Bandwidth used: {bandwidth}")