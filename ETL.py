import pandas as pd
#import import_ipynb
import data_aggregation_tools as da
import streamlit as st

def format_money(value):
    if abs(value) >= 1e6:
        return '{:.2f}M'.format(value / 1e6)
    elif abs(value) >= 1e3:
        return '{:.2f}K'.format(value / 1e3)
    else:
        return '{:.2f}'.format(value)

def format_money_USD(value):
    if abs(value) >= 1e6:
        return '${:.2f}M'.format(value / 1e6)
    elif abs(value) >= 1e3:
        return '${:.2f}K'.format(value / 1e3)
    else:
        return '${:.2f}'.format(value)


def read_clean_data():
    """read clean data from csv files"""
    dtypes = {
        # 'FullName': 'str',
        # 'Email': 'str',
        # 'Country': 'str',
        # 'State': 'str',
        # 'City': 'str',
        # 'Currency': 'str',
        'Amount': 'float',
        'Category': 'str'
    }

    large_donations_by_category = pd.read_csv('data/large_donations_by_category.csv', dtype=dtypes, parse_dates=['Date'])

    donations_below_large_by_category = pd.read_csv('data/donations_below_large_by_category.csv', dtype=dtypes, parse_dates=['Date'])

    donations_total = pd.read_csv('data/donations_total.csv', dtype=dtypes, parse_dates=['Date'])

    donations_total_by_category = pd.read_csv('data/donations_total_by_category.csv', dtype=dtypes, parse_dates=['Date'])

    donations_total_by_category = pd.read_csv('data/donations_total_by_category.csv', dtype=dtypes, parse_dates=['Date'])

    return large_donations_by_category, donations_below_large_by_category, donations_total, donations_total_by_category

@st.cache_data(ttl=24*60*60)
def ETL_raw_data(nrows = None):
    '''Extract and transform data and save it to csv files'''

    dtypes = {
        'FullName': 'str',
        'Email': 'str',
        'Country': 'str',
        'State': 'str',
        'City': 'str',
        'Currency': 'str',
        'Amount': 'float',
        'Category': 'str'
    }

    df = pd.read_csv('data/PayPal.csv', dtype=dtypes, parse_dates=['Date'])

    df['Date'] = pd.to_datetime(df['Date'])
    df['Category'].fillna('', inplace=True)
    df['Country'].fillna('', inplace=True)
    df['Category'] = df['Category'].replace('100 Drones for Ukraine', '1000 Drones for Ukraine')
    df['Category'] = df['Category'].replace('Milan', '1000 Drones for Ukraine')

    donations_total_by_category = df.groupby(['Date', 'Category']).sum().reset_index()
    donations_total_by_category.to_csv('data/donations_total_by_category.csv', index=False)

    donations_total = df.drop('Category', axis=1).groupby('Date').sum().reset_index()
    donations_total.to_csv('data/donations_total.csv', index=False)

    # above 2666
    amount = 2666
    large_donations = df[df['Amount'] >= amount].fillna('')
    large_donations_by_category = large_donations.groupby(['Date', 'Category']).sum().reset_index()
    large_donations_by_category.to_csv('data/large_donations_by_category.csv', index=False)

    # below
    donations_below_large_by_category = df[df.Amount < amount]

    donations_below_large_by_category = donations_below_large_by_category.groupby(['Date', 'Category']).sum().reset_index()


    donations_below_large_by_category.to_csv('data/donations_below_large_by_category.csv', index=False)

    #return df, ds

