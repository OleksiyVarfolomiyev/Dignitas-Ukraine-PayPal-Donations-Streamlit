import pandas as pd
from functools import reduce

def sum_category_by_date(category_name, period, data, category):
    data = data.copy()  # Create a copy of the data to avoid SettingWithCopyWarning
    data['Date'] = pd.to_datetime(data['Date'])
    return pd.DataFrame(data[((
            data[category] == category_name))]['Amount'].groupby(
            data['Date'].dt.to_period(period)).sum().reset_index(name = category_name))


def sum_by_period_by_category(categories, period, data, category):
    ''' sum ALL categories values by period (day, week, month, year) for multiple categories'''
    data_frames = [
        sum_category_by_date(category_name, period, data, category)
        for category_name in categories
    ]
    return reduce(lambda left, right: pd.merge(left, right, on='Date', how='outer'), data_frames)


def sum_by_period(data, period):
    data['Date'] = pd.to_datetime(data['Date'])
    return pd.DataFrame(data['Amount'].groupby(data['Date'].dt.to_period(period)).sum())