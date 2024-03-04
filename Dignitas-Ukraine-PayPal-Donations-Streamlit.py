import streamlit as st; st.set_page_config(layout="wide")

import ETL as etl
import data_aggregation_tools as da
import charting_tools

import pandas as pd
import datetime as dt

import plotly.express as px
from plotly.offline import iplot
import plotly.figure_factory as ff
import plotly.io as pio
from plotly.subplots import make_subplots

# ! run once to ELT data, then comment out and run the app
#etl.ETL_raw_data()

# app code
large_donations_by_category, donations_below_large_by_category, \
donations_total,  donations_total_by_category = etl.read_clean_data()

st.title("Dignitas Ukraine **PayPal Donations**")

def show_metrics(donations_total):
    """ Show metrics"""
    #end_date = df['Date'].max()
    starting_date = donations_total['Date'].min().date()
    #starting_date = dt.date(2023, 2, 15)
    end_date = dt.date.today()
    #dt.date(2023, 10, 31)

    #donations_today = etl.format_money(donations_total[donations_total['Date'] == donations_total['Date'].max()]['USD'].iloc[0])
    yesterday = donations_total['Date'].max()# - pd.Timedelta(days=1)
    donations_yesterday = etl.format_money_USD(donations_total[donations_total['Date'] == yesterday]['Amount'].iloc[0])

    col1, col2, col3 = st.columns(3)
    col1.metric("Days", (end_date - starting_date).days, "1", delta_color="normal")
    col2.metric("Donations", etl.format_money_USD(donations_total.Amount.sum()), donations_yesterday, delta_color="normal")

show_metrics(donations_total)


def show_donations(donations_total):
    """ Show donations and spending by time period"""
    col0, col1, col2, col3 = st.columns(4)
    with col0:
        timeperiod = st.selectbox(' ', ['Monthly  ',  'Weekly  ', 'Daily  '])
    with col3:
        timespan = st.selectbox(' ',['Since launch', '1 Year ', '1 Month ', '3 Months ', '6 Months '])


    donations = da.sum_by_period(donations_total, timeperiod[0])
    #if not isinstance(donations.index, pd.core.indexes.period.PeriodIndex):
    #    donations.index = donations.index.to_period(timeperiod[0])

    if timespan == '1 Month ':
        donations = donations.loc[donations.index > (pd.Timestamp.now() - pd.DateOffset(months=1)).strftime("%Y-%m-%d")]
    elif timespan == '3 Months ':
        donations = donations.loc[donations.index > (pd.Timestamp.now() - pd.DateOffset(months=3)).strftime("%Y-%m")]
    elif timespan == '6 Months ':
        donations = donations.loc[donations.index > (pd.Timestamp.now() - pd.DateOffset(months=6)).strftime("%Y-%m")]
    elif timespan == '1 Year ':
        donations = donations.loc[donations.index > (pd.Timestamp.now() - pd.DateOffset(years=1)).strftime("%Y")]

    # Convert the Period index back to datetime index
    donations.index = donations.index.to_timestamp()

    fig = charting_tools.bar_plot(donations, 'Amount', '', False)
    st.plotly_chart(fig, use_container_width=True)

show_donations(donations_total)

# Ring plot - Donations  by Category
def show_donations_by_category(large_donations_by_category, donations_below_large_by_category, donations_total_by_category):
    """ Show donations and spending by category"""
    donations_by_category = donations_total_by_category


    col0, col1, col2, col3 = st.columns(4)
    with col0:
        over_below_all = st.selectbox(' ',['all txs', 'over $2,666', 'below $2,666'])
    with col3:
        period = st.selectbox(' ', ['Year', 'Month', 'Week', 'Day', 'All time'])

    if period == 'Month':
        donations = donations_by_category[donations_by_category['Date'] >= pd.Timestamp.now(tz='UTC').floor('D') - pd.DateOffset(months=1)]

    elif period == 'Week':
        donations = donations_by_category[donations_by_category['Date'] >= pd.Timestamp.now(tz='UTC').floor('D') - pd.DateOffset(weeks=1)]
    elif period == 'Day':
        day = donations_by_category['Date'].max()
        donations = donations_by_category[donations_by_category['Date'] == donations_by_category.Date.max()]
    elif period == 'Year':
        donations = donations_by_category[donations_by_category['Date'] >= pd.Timestamp.now(tz='UTC').floor('D') - pd.DateOffset(years=1)]
    else:
        donations = donations_by_category

    amount = 2666
    if over_below_all == 'over $2,666':
        donations = donations[donations.Amount >= amount]
    elif over_below_all == 'below $2,666':
        donations = donations[donations.Amount < amount]

    # else:
    #     donations = donations_total_by_category
    #     spending = spending_total_by_category

    donations_by_cat = pd.DataFrame(donations.groupby('Category')['Amount'].sum())


    fig = charting_tools.pie_plot(donations_by_cat, 'Amount', '', False)
    st.plotly_chart(fig, use_container_width=True)

show_donations_by_category(large_donations_by_category, donations_below_large_by_category, donations_total_by_category)

def donations_by_period_by_category(donations_total_by_category, large_donations_by_category, donations_below_large_by_category):
    """Donations/Spending by time period (d, w, m) and large/regular amounts"""
    #main_donation_categories = donations_total_by_category.groupby('Category')['USD'].sum().sort_values(ascending = False).index[:4].tolist()
    main_donation_categories = donations_total_by_category.groupby('Category')['Amount'].sum().sort_values(ascending=False).index.tolist()

    col0, col1, col2 = st.columns(3)
    with col0:
        amount = st.selectbox(' ',['all txs', '<$2,666', '>$2,666'])
    with col1:
        selected_period = st.selectbox(' ',['Monthly ', 'Weekly ', 'Daily '])
    with col2:
        timespan = st.selectbox(' ',[ 'all time', '1 month', '3 months', '1 Year'])

    if amount == '>$2,666':
        donations_by_category = large_donations_by_category

    elif amount == '<$2,666':
        donations_by_category = donations_below_large_by_category

    else:
        donations_by_category = donations_total_by_category


    #if donations_spending == 'donations':
    main_categories = main_donation_categories
    tx_by_category = donations_by_category
    #else:
    #    main_categories = main_spending_categories

    if timespan == '1 month':
        tx_by_category = tx_by_category[tx_by_category['Date'] > pd.Timestamp.now(tz='UTC').floor('D') - pd.DateOffset(months=1)]
    elif timespan == '3 months':
        tx_by_category = tx_by_category[tx_by_category['Date'] > pd.Timestamp.now(tz='UTC').floor('D') - pd.DateOffset(months=3)]
    elif timespan == '1 year':
        tx_by_category = tx_by_category[tx_by_category['Date'] > pd.Timestamp.now(tz='UTC').floor('D') - pd.DateOffset(years=1)]

    fig = charting_tools.chart_by_period(tx_by_category, main_categories, selected_period[0],'')
    st.plotly_chart(fig, use_container_width=True)

donations_by_period_by_category(donations_total_by_category, large_donations_by_category, donations_below_large_by_category)


st.markdown("<br>", unsafe_allow_html=True)
# Donate button
import webbrowser
url_to_open = "https://www.dignitas.fund/donate"
col1, col2, col3 = st.columns(3)
if col2.button("Donate", key="donate_button", help="Click to donate"):
    webbrowser.open_new_tab(url_to_open)

# Links
st.write("---")
col1, col2, col3, col4 = st.columns(4)
with col1: st.markdown("[Dignitas Fund Site](https://dignitas.fund/)")
with col4: st.markdown(f"[{'Contact'}](mailto:{'info@dignitas.fund'})")