import math
import matplotlib.pyplot as plt
from datetime import datetime


def factorize(x):
    """Вычисляет все простые делители числа x, кроме 1"""
    factors = []
    while x > 1:
        # перебор делителей от 2 до √x + 1
        for i in range(2, int(round(math.sqrt(x))) + 2):
            if x % i == 0:
                factors.append(i)
                x //= i
                break
        else:
            # простое число
            factors.append(x)
            break
    return factors

def tau(x):
    """Вычисляет количество всех положительных делителей числа x"""
    # https://math.stackexchange.com/questions/433848/prime-factors-number-of-divisors
    
    # раскладываем число на простые делители
    factors = factorize(x)

    # считаем, сколько раз встречается каждый делитель
    factor_amounts = dict()
    for factor in factors:
        if factor in factor_amounts.keys():
            factor_amounts[factor] += 1
        else:
            factor_amounts[factor] = 1
    
    product = 1
    for factor, amount in factor_amounts.items():
        product *= (1 + amount)
    return product


def stat(range):
    """Вычисляет частоты значений tau(x) для каждого x из range"""
    stats = dict()
    values = dict()

    for x in range:
        value = tau(x)

        values[x] = value

        if value in stats.keys():
            stats[value] += 1
        else:
            stats[value] = 1
    
    return stats, values

def M(stats):
    """Вычисляет математическое ожидание по частотам"""
    return sum(value * amount for value, amount in stats.items()) / sum(stats.values())

def sig(stats):
    """Вычисляет дисперсию по частотам"""
    m = M(stats)
    n = sum(stats.values())

    sig_2 = (1 / (n - 1)) * sum((value - m)**2 for value in stats.keys())
    return math.sqrt(sig_2)

def plot(stats):
    """Строит график частот значений tau(x)"""

    # сортировка пар по X по возрастанию
    items = list(stats.items())
    items.sort(key=lambda v: v[0])
    X, Y = zip(*items)

    # построение графика
    plt.ioff() # выключить интерактивный режим (чтобы не всплывало окошко)
    fig, ax = plt.subplots()
    ax.plot(X, Y, label='Частота количества делителей')
    ax.legend()
    ax.set_xlabel('Количество делителей')
    ax.set_ylabel('Количество наблюдений')

    # сохранение графика в файл
    filename = "last_plot.png"
    fig.savefig(filename)
    return filename

