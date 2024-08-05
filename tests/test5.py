# Функция для вычисления стоимости Bandwidth и Energy
def calculate_transaction_cost(energy_used, bandwidth_used, bandwidth_cost_per_byte, energy_cost_per_unit):
    # Вычисляем стоимость Bandwidth
    bandwidth_cost = bandwidth_used * bandwidth_cost_per_byte
    
    # Вычисляем стоимость Energy
    energy_cost = energy_used * energy_cost_per_unit
    
    # Вычисляем общую стоимость транзакции
    total_transaction_cost = bandwidth_cost + energy_cost
    
    return bandwidth_cost, energy_cost, total_transaction_cost

# Исходные данные
energy_used = 31895
bandwidth_used = 345

# Стоимость за единицу ресурсов
bandwidth_cost_per_byte = 0.00001  # TRX за байт
energy_cost_per_unit = 0.00084  # TRX за единицу энергии

# Вычисляем стоимости
bandwidth_cost, energy_cost, total_transaction_cost = calculate_transaction_cost(energy_used, bandwidth_used, bandwidth_cost_per_byte, energy_cost_per_unit)

# Выводим результаты
print(f"Bandwidth Cost: {bandwidth_cost} TRX")
print(f"Energy Cost: {energy_cost} TRX")
print(f"Total Transaction Cost: {total_transaction_cost} TRX")