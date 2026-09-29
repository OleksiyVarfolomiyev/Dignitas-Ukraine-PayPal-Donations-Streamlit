import os
import boto3
import json
import pandas as pd
from datetime import datetime
import streamlit as st
from botocore.exceptions import ClientError, NoCredentialsError
from streamlit.errors import StreamlitSecretNotFoundError


def format_money_USD(value):
    if abs(value) >= 1e6:
        return '${:.2f}M'.format(value / 1e6)
    elif abs(value) >= 1e3:
        return '${:.2f}K'.format(value / 1e3)
    else:
        return '${:.2f}'.format(value)


def read_PayPal_txs(start_date):
    '''Read only the new PayPal transactions from AWS'''

    access_key_id = os.environ.get('AWS_ACCESS_KEY_ID')
    secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')

    if not access_key_id or not secret_access_key:
        try:
            aws_secrets = st.secrets.get('aws', {})
        except StreamlitSecretNotFoundError:
            aws_secrets = {}

        access_key_id = access_key_id or aws_secrets.get('aws_access_key_id')
        secret_access_key = secret_access_key or aws_secrets.get('aws_secret_access_key')

    if not access_key_id or not secret_access_key:
        print('AWS credentials not configured; using the local CSV snapshot.')
        return pd.DataFrame()

    s3 = boto3.client('s3', aws_access_key_id=access_key_id,
                            aws_secret_access_key=secret_access_key,
                            region_name='us-east-1')

    objects = []
    continuation_token = None
    bucket_name = 'finmap-trans'

    try:
        while True:
            if continuation_token:
                response = s3.list_objects_v2(Bucket=bucket_name, ContinuationToken=continuation_token)
            else:
                response = s3.list_objects_v2(Bucket=bucket_name)

            if 'Contents' in response:
                objects.extend(response['Contents'])

            if response.get('IsTruncated'):
                continuation_token = response.get('NextContinuationToken')
            else:
                break
    except (NoCredentialsError, ClientError) as exc:
        print(f'Could not access S3 bucket {bucket_name!r}: {exc}. Using the local CSV snapshot.')
        return pd.DataFrame()

    transactions = []

    for obj in objects:

        if 'trans-paypal' in obj['Key']:
            # Extract the date from the object key
            obj_date_str = '-'.join(obj['Key'].split('-')[2:5]).split('.')[0]
            obj_date = datetime.strptime(obj_date_str, '%Y-%m-%d')

            if obj_date > start_date:

                try:
                    file = s3.get_object(Bucket='finmap-trans', Key=obj['Key'])
                    file_content = file['Body'].read().decode('utf-8')
                except (NoCredentialsError, ClientError) as exc:
                    print(f"Could not read S3 object {obj['Key']}: {exc}. Skipping it.")
                    continue

                while file_content:
                    json_content, idx = json.JSONDecoder().raw_decode(file_content)
                    file_content = file_content[idx:].lstrip()

                for item in json_content:
                    transaction_info = item.get('transaction_info', {})
                    payer_info = item.get('payer_info', {})
                    payer_name = payer_info.get('payer_name', {})
                    shipping_info = item.get('shipping_info', {})
                    address = shipping_info.get('address', {})
                    transaction_note = transaction_info.get('transaction_note', '')

                    transaction_data = {
                        'Date': transaction_info.get('transaction_initiation_date'),
                        'FullName': payer_name.get('alternate_full_name'),
                        'City': address.get('city'),
                        'Currency': transaction_info.get('transaction_amount', {}).get('currency_code'),
                        'Gross': transaction_info.get('transaction_amount', {}).get('value'),
                        'Fee': transaction_info.get('fee_amount', {}).get('value'),
                        'Category': transaction_info.get('transaction_subject'),
                        'TransactionNote': transaction_note
                    }
                    transactions.append(transaction_data)

    print("obj_date", obj_date)

    return pd.DataFrame(transactions)


def etl(df):
    '''Extract, transform, and load the new PayPal transactions,
    append to existing data in PayPal.csv'''

    # anonimization, store only the first name
    df['FullName'] = df['FullName'].str.split().str[0]
    df['FullName'] = df['FullName'].str.capitalize()
    df['Fee'].fillna(0)
    df = df.fillna('')
    df['Date'] = pd.to_datetime(df['Date'])
    df['Gross'] = df['Gross'].astype(float).abs()
    df['Gross'] = df['Gross'].abs()
    df['Fee'] = pd.to_numeric(df['Fee'], errors='coerce').fillna(0).astype(float)

    df['Amount'] = df['Gross'] + df['Fee']
    df = df.drop(['Gross', 'Fee'], axis=1)

    df['City'] = df['City'].str.title()
    df.loc[df.City == 'Kiev', 'City'] = 'Kyiv'

    mask = df['Category'].str.contains('General', case=False, na=False)
    df.loc[mask, 'Category'] = 'General'
    mask = df['Category'].str.contains('1000', case=False, na=False)
    df.loc[mask, 'Category'] = '1000 Drones for Ukraine'
    mask = df['Category'].str.contains('Milan', case=False, na=False)
    df.loc[mask, 'Category'] = '1000 Drones for Ukraine'
    mask = df['Category'].str.contains('BOSTON', case=False, na=False)
    df.loc[mask, 'Category'] = '1000 Drones for Ukraine'

    mask = df['Category'].str.contains('support ukraine', case=False, na=False)
    df.loc[mask, 'Category'] = 'General'
    mask = df['Category'].str.contains('custom', case=False, na=False)
    df.loc[mask, 'Category'] = 'General'

    mask = df['Category'].str.contains('victory', case=False, na=False)
    df.loc[mask, 'Category'] = 'Victory Drones'

    mask = df['Category'].str.contains('flight', case=False, na=False)
    df.loc[mask, 'Category'] = 'Flight to Recovery'

    mask = df['Category'].str.contains('units', case=False, na=False)
    df.loc[mask, 'Category'] = 'Mobile Shower Laundry Units'
    mask = df['Category'].str.contains('shower', case=False, na=False)
    df.loc[mask, 'Category'] = 'Mobile Shower Laundry Units'

    file_path = 'data/PayPal.csv'

    try:
        if os.path.exists(file_path):
            df_existing = pd.read_csv(file_path)
        else:
            df_existing = pd.DataFrame()
    except pd.errors.EmptyDataError:
        df_existing = pd.DataFrame()
    except FileNotFoundError:
        df_existing = pd.DataFrame()

    # Append new transactions
    df_combined = pd.concat([df_existing, df])
    df_combined['Date'] = pd.to_datetime(df_combined['Date'])

    df_combined.to_csv(file_path, index=False)

@st.cache_data(ttl=24*60*60)
def ETL_raw_data():
    '''Extract and transform data and save it to csv files'''

    dtypes = {
        'FullName': 'str',
        'City': 'str',
        'Currency': 'str',
        'Amount': 'float',
        'Category': 'str'
    }

    df = pd.read_csv('data/PayPal.csv', dtype = dtypes, parse_dates=['Date'])

    #df = df.drop_duplicates()

    df.loc[:, 'Category'] = df['Category'].fillna('')

    df['Category'] = df['Category'].replace('100 Drones for Ukraine', '1000 Drones for Ukraine')
    df['Category'] = df['Category'].replace('Milan', '1000 Drones for Ukraine')
    df['Category'] = df['Category'].replace('BOSTON', '1000 Drones for Ukraine')
    df['Category'] = df['Category'].replace('"VD_TEP"', 'Victory Drones')
    df['Date'] = df['Date'].dt.strftime('%Y-%m-%d %H:%M')
    df['Date'] = pd.to_datetime(df['Date'])

    df_original = df.copy()

    donations_total_by_category = df.groupby([df.Date.dt.date, 'Category'])['Amount'].sum().reset_index()
    donations_total = df.groupby(df.Date.dt.date)['Amount'].sum().reset_index()

    # above $2500 (large donations)
    amount = 2500
    large_donations = df[df['Amount'] >= amount].fillna('')
    large_donations['Date'] = large_donations['Date'].dt.date
    large_donations_by_category = large_donations.groupby(['Date', 'Category']).sum().reset_index()

    # below $2500 (crowdfunding)
    donations_below_large_by_category = df[df.Amount < amount]
    donations_below_large_by_category['Date'] = donations_below_large_by_category['Date'].dt.date
    donations_below_large_by_category = donations_below_large_by_category.groupby(
                                        ['Date', 'Category']).sum().reset_index()
    df = df_original
    df['First Name'] = df['FullName']
    df = df.rename(columns={'TransactionNote': 'Commentary'})
    df['City'] = df['City'].fillna('')
    df['Commentary'] = df['Commentary'].fillna('')

    return  df[['Date', 'First Name', 'City', 'Currency', 'Amount', 'Commentary']], \
            large_donations_by_category, donations_below_large_by_category, \
            donations_total, donations_total_by_category

#######################################################################################
# Main function
#######################################################################################

def read_new_PayPal_txs_from_AWS():
    try:
        df_date = pd.read_csv('data/PayPal.csv', usecols=['Date'], parse_dates=['Date'])
        start_date = df_date['Date'].max().strftime('%Y-%m-%d')
    except FileNotFoundError:
        start_date = '2023-03-05'

    yesterday = pd.Timestamp.now().normalize() - pd.DateOffset(days=1)
    start_date = datetime.strptime(start_date, '%Y-%m-%d')

    if start_date < yesterday:
        df_new = read_PayPal_txs(start_date)
        print("df_new", df_new.tail())
        if not df_new.empty:
            etl(df_new)
        else:
            print('No new AWS transactions; using the existing CSV snapshot.')

    return ETL_raw_data()
