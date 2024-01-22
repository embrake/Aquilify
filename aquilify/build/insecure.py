import string
import random

def ax_insecure_key(
    key_length=64,
    include_uppercase=True,
    include_lowercase=True,
    include_digits=True,
    include_symbols=True,
    symbols="#=*$%@",
    prefix="aquilify-insecure"
):
    if key_length < (len(prefix) + sum([include_uppercase, include_lowercase, include_digits, include_symbols])):
        raise ValueError("Key length should be greater than or equal to the sum of chosen character types and prefix length.")

    characters = string.ascii_uppercase if include_uppercase else ''
    characters += string.ascii_lowercase if include_lowercase else ''
    characters += string.digits if include_digits else ''
    characters += symbols if include_symbols else ''

    key_length -= len(prefix)
    special_chars_count = min(len(symbols), key_length // 4)

    key = [random.choice(characters) for _ in range(key_length - special_chars_count)]
    special_char_positions = random.sample(range(key_length), special_chars_count)

    for position in special_char_positions:
        key.insert(position, random.choice(symbols))

    generated_key = ''.join(key)
    return f"{prefix}-{generated_key}"