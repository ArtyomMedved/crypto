from tronpy import Tron
from tronpy.keys import PrivateKey

def generate_wallet():
    # Генерация нового приватного ключа
    private_key = PrivateKey.random()
    print(f"Приватный ключ: {private_key.hex()}")
    print(f"Публичный адрес: {private_key.public_key.to_base58check_address()}")

generate_wallet()


cc8ad0a2cdc9691a0193452548a488e8d59957274b2015685c8b8e48ec28786e