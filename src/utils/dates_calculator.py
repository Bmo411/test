import pandas as pd
### FUNCTIONS FOR CALCULATING RANGE OF DATES 


def range_of_months_to_dates(base_month: str, base_year: str, range_of_months: int):
    """Function that accepts a base month (number), and (number)
        representig the amount of past month the range must reprent"""
    
    # Due to databse format, base month a base_year are numbers in str type 

    base_month = int(base_month)
    base_year = int(base_year)

    start_month = base_month - range_of_months + 1 
    start_year = base_year
    
    while start_month <= 0:
        start_month += 12 
        start_year -= 1
    
    start_date = pd.Timestamp(year=start_year, month=start_month, day=1)
    end_date = pd.Timestamp(year=base_year, month=base_month, day=1) + pd.offsets.MonthEnd(1)

    return start_date, end_date


def filter_dataframe_by_range_of_months(df: pd.DataFrame, date_col: str, base_month: str, base_year: str, range_of_months: str) -> pd.DataFrame:
    
    start_date, end_date = range_of_months_to_dates(base_month, base_year, range_of_months)
    
    if not pd.api.types.is_datetime64_any_dtype(df[date_col]):
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')

    df = df[df[date_col].between(start_date, end_date)]

    return df