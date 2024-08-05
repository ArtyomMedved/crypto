from tronpy import Tron
from tronpy.keys import PrivateKey
from tronpy.providers import HTTPProvider

# Укажите ваш TronGrid API-ключ
api_key = "9250cd97-47a4-42e8-a0c9-212ab222169c"

# Инициализация клиента Tron с использованием TronGrid и API-ключа
client = Tron(HTTPProvider(api_key=api_key))

# Введите свой приватный ключ
private_key_hex = "471514b3bdbbf7d275e987933eb7bd1771b0ea09df05c8cd6c532c2bd0a31a1e"
priv_key = PrivateKey(bytes.fromhex(private_key_hex))

# Укажите адреса отправителя и получателя
from_addr = priv_key.public_key.to_base58check_address()
to_addr = "TVpo91xSEChP5ipV49diQu7kUTAYbbGu8y"

# Укажите сумму перевода в TRX (1 TRX = 1_000_000 Sun)
amount = 1 * 1_000_000  

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
