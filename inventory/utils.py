import random
import string

def generate_random_barcode():
    return ''.join(random.choices(string.digits, k=12))
