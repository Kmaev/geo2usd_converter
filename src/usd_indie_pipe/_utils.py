import re


def flatten_input_data(data_str: str) -> str:
    return re.sub(r'[^a-zA-Z0-9]', '', data_str).lower()
