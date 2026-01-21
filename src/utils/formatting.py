import math 

def to_currency(x: float) -> str:
    if math.isnan(x) or math.isinf(x):
        return ""
    if x > 999:
        return f'${x:,.0f}'
    return f'${x:,.2f}'

def to_kg(x: float) -> str:
    if math.isnan(x) or math.isinf(x):
        return ''
    if x > 999:
        return f'{x:,.0f} KG'
    return f'{x:,.2f} KG'

def to_percentage(x : float, with_decimals: bool = True) -> str:
    x = x * 100
    if with_decimals:
        return f'{x:,.2f}%'
    return f'{x:,.0f}%'