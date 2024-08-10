import streamlit as st; st.set_page_config(layout="wide")

import data_aggregation_tools as da
import charting_tools
import read_PayPal_data_from_AWS as rpd

import pandas as pd
import datetime as dt

df, large_donations_by_category, donations_below_large_by_category, \
donations_total, donations_total_by_category = rpd.read_new_PayPal_txs_from_AWS()


#st.title("Dignitas Ukraine **PayPal Donations**")
st.markdown("<h1 style='text-align: center;'>Dignitas Ukraine <b>PayPal Donations</b></h1>", unsafe_allow_html=True)


def show_metrics(donations_total, df):
    """ Show metrics"""
    starting_date = donations_total['Date'].min()
    end_date = donations_total.Date.max()

    donations_yesterday = rpd.format_money_USD(donations_total[donations_total['Date'] == end_date]['Amount'].iloc[0])
    donations_yesterday_count = df[df['Date'].dt.date == end_date].shape[0]
    donations_total_count = df.shape[0]

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Days", (end_date - starting_date).days, "1", delta_color="normal")
    col3.metric("Donations $", rpd.format_money_USD(donations_total.Amount.sum()), donations_yesterday, delta_color="normal")
    col5.metric("Donations #", donations_total_count, int(donations_yesterday_count), delta_color="normal")

show_metrics(donations_total, df)

def show_donations(donations_total):
    """ Show donations by time period"""
    col0, col1, col2, col3 = st.columns(4)
    with col0:
        timeperiod = st.selectbox(' ', ['Monthly  ',  'Weekly  ', 'Daily  '])
    with col3:
        timespan = st.selectbox(' ',['Since launch', '1 Year ', '1 Week', '1 Month ', 'Quarter ', '6 Months '])


    donations = da.sum_by_period(donations_total, timeperiod[0])
    if timespan == '1 Week':
        donations = donations.loc[donations.index > (pd.Timestamp.now() - pd.DateOffset(weeks=1)).strftime("%Y-%m-%d")]
    if timespan == '1 Month ':
        donations = donations.loc[donations.index > (pd.Timestamp.now() - pd.DateOffset(months=1)).strftime("%Y-%m-%d")]
    elif timespan == 'Quarter ':
        donations = donations.loc[donations.index > (pd.Timestamp.now() - pd.DateOffset(months=3)).strftime("%Y-%m")]
    elif timespan == '6 Months ':
        donations = donations.loc[donations.index > (pd.Timestamp.now() - pd.DateOffset(months=6)).strftime("%Y-%m")]
    elif timespan == '1 Year ':
        donations = donations.loc[donations.index > (pd.Timestamp.now() - pd.DateOffset(years=1)).strftime("%Y")]

    donations.index = donations.index.to_timestamp()

    fig = charting_tools.bar_plot(donations, 'Amount', '', False)
    st.plotly_chart(fig, use_container_width=True)

show_donations(donations_total)


def show_donations_by_category(donations_by_category):
    """ Show donations by category"""

    col0, col1, col2, col3 = st.columns(4)
    with col0:
        over_below_all = st.selectbox(' ',['all donations', 'over $2,500', 'below $2,500'])
    with col3:
        period = st.selectbox(' ', ['Year', 'Quarter', 'Month', 'Week', 'Day', 'All time'])


    donations_by_category['Date'] = pd.to_datetime(donations_by_category['Date'])

    if period == 'Month':
        donations = donations_by_category[donations_by_category['Date'] >= pd.to_datetime(pd.Timestamp.now() - pd.DateOffset(months=1))]
    elif period == 'Week':
        donations = donations_by_category[donations_by_category['Date'] >= pd.to_datetime(pd.Timestamp.now() - pd.DateOffset(weeks=1))]
    elif period == 'Day':
        day = donations_by_category['Date'].max()
        donations = donations_by_category[donations_by_category['Date'] == donations_by_category.Date.max()]
    elif period == 'Quarter':
        donations = donations_by_category[donations_by_category['Date'] >= dt.date.today() - pd.DateOffset(months=3)]
    elif period == 'Year':
        donations = donations_by_category[donations_by_category['Date'] >= dt.date.today() - pd.DateOffset(years=1)]
    else:
        donations = donations_by_category

    amount = 2500
    if over_below_all == 'over $2,500':
        donations = donations[donations.Amount >= amount]
    elif over_below_all == 'below $2,500':
        donations = donations[donations.Amount < amount]

    donations_by_cat = pd.DataFrame(donations.groupby('Category')['Amount'].sum())

    fig = charting_tools.pie_plot(donations_by_cat, 'Amount', '', False)
    st.plotly_chart(fig, use_container_width=True)

show_donations_by_category(donations_total_by_category)


def donations_by_period_by_category(donations_total_by_category, large_donations_by_category, donations_below_large_by_category):
    """Donations by time period (d, w, m) and large/regular amounts"""

    main_categories = donations_total_by_category.groupby('Category')['Amount'].sum().sort_values(ascending=False).index.tolist()

    col0, col1, col2 = st.columns(3)
    with col0:
        amount = st.selectbox(' ',['all donations', '<$2,500', '>$2,500'])
    with col1:
        selected_period = st.selectbox(' ',['Monthly ', 'Weekly ', 'Daily ', 'Quarterly ', 'Yearly '])

    with col2:
        if selected_period == 'Yearly ':
            timespan_options = ['all time']
        elif selected_period == 'Quarterly ':
            timespan_options = ['all time', 'quarter', '6 months', 'year']
        else:
            timespan_options = ['all time', 'month', 'quarter', '6 months', 'year']
        timespan = st.selectbox(' ', timespan_options)

    if  amount == '>$2,500':
        donations_by_category = large_donations_by_category
    elif amount == '<$2,500':
        donations_by_category = donations_below_large_by_category
    else:
        donations_by_category = donations_total_by_category

    tx_by_category = donations_by_category

    if timespan == 'month':
        tx_by_category = tx_by_category[tx_by_category['Date'] > pd.Timestamp.now() - pd.DateOffset(months=1)]
    elif timespan == 'quarter':
        tx_by_category = tx_by_category[tx_by_category['Date'] > pd.Timestamp.now() - pd.DateOffset(months=3)]
    elif timespan == '6 months':
        tx_by_category = tx_by_category[tx_by_category['Date'] > pd.Timestamp.now() - pd.DateOffset(months=6)]
    elif timespan == 'year':
        tx_by_category = tx_by_category[tx_by_category['Date'] > pd.Timestamp.now() - pd.DateOffset(years=1)]

    data_sum_by_period_by_category = da.sum_by_period_by_category(main_categories, selected_period[0].upper(), tx_by_category, 'Category').fillna(0)
    if selected_period[0] == 'W':
        data_sum_by_period_by_category['Date'] = data_sum_by_period_by_category['Date'].astype(str).str.split('/').str[0]

    fig = charting_tools.stack_bar_plot(data_sum_by_period_by_category, '', False)
    st.plotly_chart(fig, use_container_width=True)

donations_by_period_by_category(donations_total_by_category, large_donations_by_category, donations_below_large_by_category)


st.markdown("<br>", unsafe_allow_html=True)
# Donations list
if df.index.min() == 0:
    df.index += 1
df.sort_index(ascending=False, inplace=True)
st.dataframe(df, use_container_width = True)


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