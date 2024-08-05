import requests
import pandas as pd
import os
from datetime import datetime, timedelta

def get_transaction_details(tx_id):
    url = f"https://apilist.tronscanapi.com/api/transaction-info?hash={tx_id}"
    response = requests.get(url)
    data = response.json()
    
    # Extracting energy and bandwidth usage information
    energy_used = data.get('cost', {}).get('energy_usage_total', 0)
    bandwidth_used = data.get('cost', {}).get('net_usage', 0)
    
    # Extracting transaction details from trc20TransferInfo
    trc20_info = data.get('trc20TransferInfo', [])
    if trc20_info:
        trc20_info = trc20_info[0]
        amount = float(trc20_info.get('amount_str', 0)) / 1_000_000  # Convert from SUN to USDT
        recipient = trc20_info.get('to_address', 'N/A')
    else:
        amount = 0
        recipient = 'N/A'
    
    timestamp = datetime.fromtimestamp(data.get('timestamp', 0) / 1000)
    
    return energy_used, bandwidth_used, timestamp, recipient, amount

def get_start_and_end_of_month():
    today = datetime.today()
    start_date = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    next_month = start_date.replace(day=28) + timedelta(days=4)
    end_date = next_month - timedelta(days=next_month.day)
    end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
    return start_date, end_date

def get_transactions(address, start_date, end_date):
    transactions = []
    limit = 200
    start = 0
    
    while True:
        url = f"https://apilist.tronscanapi.com/api/transaction?address={address}&limit={limit}&start={start}"
        response = requests.get(url)
        data = response.json()
        batch = data.get('data', [])
        
        if not batch:
            break
        
        # Filter transactions based on date range
        for tx in batch:
            timestamp = tx.get('timestamp')
            if timestamp:
                tx_date = datetime.fromtimestamp(timestamp / 1000)  # Convert milliseconds to seconds
                if start_date <= tx_date <= end_date:
                    transactions.append(tx)
        
        start += limit

    return transactions

def filter_usdt_transactions(transactions):
    usdt_contract_address = 'TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t'
    usdt_transactions = []
    
    for tx in transactions:
        contract_data = tx.get('contractData', [])
        
        if isinstance(contract_data, list):
            for contract in contract_data:
                if isinstance(contract, dict):
                    if contract.get('contract_address') == usdt_contract_address and contract.get('data'):
                        usdt_transactions.append(tx['hash'])
        elif isinstance(contract_data, dict):
            if contract_data.get('contract_address') == usdt_contract_address and contract_data.get('data'):
                usdt_transactions.append(tx['hash'])
        else:
            print(f"Unexpected contractData format: {contract_data}")
    
    return usdt_transactions

def update_excel(transactions_data, filename="transactions.xlsx"):
    file_exists = os.path.exists(filename)
    print(f"File exists: {file_exists}")
    
    if file_exists:
        df = pd.read_excel(filename)
    else:
        df = pd.DataFrame(columns=["Txn Hash", "Amount (USDT)", "Recipient", "Timestamp", "Energy Used", "Bandwidth Used"])
    
    existing_hashes = set(df["Txn Hash"])
    
    new_data = []
    for tx_hash, energy, bandwidth, timestamp, recipient, amount in transactions_data:
        if tx_hash not in existing_hashes:
            new_data.append([tx_hash, amount, recipient, timestamp, energy, bandwidth])
    
    if new_data:
        new_df = pd.DataFrame(new_data, columns=["Txn Hash", "Amount (USDT)", "Recipient", "Timestamp", "Energy Used", "Bandwidth Used"])
        df = pd.concat([df, new_df], ignore_index=True)
        
        # Calculate totals
        total_energy = df["Energy Used"].sum()
        total_bandwidth = df["Bandwidth Used"].sum()
        
        # Append totals to the DataFrame
        totals_df = pd.DataFrame([["Total", None, None, None, total_energy, total_bandwidth]], columns=["Txn Hash", "Amount (USDT)", "Recipient", "Timestamp", "Energy Used", "Bandwidth Used"])
        df = pd.concat([df, totals_df], ignore_index=True)
        
        df.to_excel(filename, index=False)
        print(f"Excel file updated and saved as {filename}")
    else:
        print("No new transactions to update.")

def main(address):
    start_date, end_date = get_start_and_end_of_month()
    print(f"Fetching transactions from {start_date} to {end_date}.")
    
    transactions = get_transactions(address, start_date, end_date)
    print(f"Fetched {len(transactions)} transactions.")
    
    usdt_transactions = filter_usdt_transactions(transactions)
    print(f"Filtered to {len(usdt_transactions)} USDT transactions.")
    
    transactions_data = []
    for tx_hash in usdt_transactions:
        energy, bandwidth, timestamp, recipient, amount = get_transaction_details(tx_hash)
        transactions_data.append((tx_hash, energy, bandwidth, timestamp, recipient, amount))
    
    print(f"Updating Excel with {len(transactions_data)} transactions.")
    update_excel(transactions_data)

address = "TVpo91xSEChP5ipV49diQu7kUTAYbbGu8y"
main(address)
