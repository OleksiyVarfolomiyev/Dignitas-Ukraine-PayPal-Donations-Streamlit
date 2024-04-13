import numpy as np
import data_aggregation_tools as da
import read_PayPal_data_from_AWS as etl

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

def hide_axis_title(fig):
    fig.update_layout(margin=dict(l=0, r=0, b=0), yaxis_title='')
    fig.update_layout(xaxis_title='')

def fig_add_mean(fig, val, col):
    """ Add a horizontal line for the mean"""
    mean_value = val[col].mean()
    fig.add_shape(
        type='line',
        x0 = val.index[0],
        x1 = val.index[-1],
        y0=mean_value,
        y1=mean_value,
        name='mean',
        line=dict(color='blue', dash = 'dot')
    )
    return fig

def subplot_horizontal(fig1, fig2, rows, cols, type1, type2, title1, title2, show):
    fig = make_subplots(rows=rows, cols=cols,
                    specs=[[{'type': type1}, {'type': type2}]],
                    subplot_titles=[title1, title2])

    fig.add_trace(fig1.data[0], row=1, col=1)
    fig.add_trace(fig2.data[0], row=1, col=2)

    fig.update_layout(grid={'columns': cols, 'rows': rows, 'pattern': "independent"})
    if show:
        fig.show(renderer="notebook")
    else:
        return fig

def subplot_vertical(val, fig1, fig2, rows, cols, type1, type2, barmode, title1, title2, show):
    fig = make_subplots(rows=rows, cols=cols,
                    specs=[[{'type': type1}], [{'type': type2}]],
                    subplot_titles=[title1, title2])

    if not val.empty:
        fig_add_mean(fig, val, 'USD')

    fig.update_layout(
    barmode = barmode,
    legend=dict(orientation='h', x=0.2, y=-0.1))

    for trace in fig1.data:
        fig.add_trace(trace, row=1, col=1)

    for trace in fig2.data:
        fig.add_trace(trace, row=2, col=1)

    fig.update_layout(grid={'columns': cols, 'rows': rows, 'pattern': "independent"})
    fig.update_layout(height=800)

    if show:
        fig.show(renderer="notebook")
    else:
        return fig

def pie_plot(data, col, title, show):
    """ pie plot with hole"""

    fig = px.pie(data,
            values = data[col],
            names = data.index,
            hole=0.5,
            title = title
    )
    fig.update_traces(textinfo='label+percent')
    fig.update_traces(textposition='inside', insidetextorientation='radial')
    fig.update_layout(showlegend=False)

    if show:
        fig.show(renderer="notebook")
    else:
        return fig


def bar_plot(val, col, fig_title, show):
    """ bar plot with mean"""
    fig = px.bar(val, x = val.index, y = col,
            color = col,
            text_auto = '.2s',
            title = fig_title
            )
    fig_add_mean(fig, val, col)
    hide_axis_title(fig)
    if show:
        fig.show(renderer="notebook")
    else:
        return fig

def bar_plot_horizontal(data, col, title):
    """ horizontal bar plot with mean"""
    fig = px.bar(data, x = data[col], y = data.index, orientation='h',
            title = title, color=col,  text_auto='.2s')
    hide_axis_title(fig)
    fig_add_mean(fig, data, col)

    fig.show(renderer="notebook")

def stack_bar_plot(df, title, show):
    """stacked bar plot with mean"""
    df['Date'] = df['Date'].astype(str)
    mean_value = df[df.columns[1:]].sum(axis=1).mean()

    fig = go.Figure()
#    for column in df.columns[1:]:
    for column in df.select_dtypes(include=[np.number]).columns:
        fig.add_trace(
                go.Bar(name=column, x = df['Date'], y = df[column],
                    text = df[column].apply(etl.format_money_USD)
        ))

    fig.update_layout(
        barmode='stack',
        title = title,
        legend=dict(orientation='h', x=0.1, y=-0.1),
        xaxis=dict(tickformat='%b')
    # Add a horizontal line at the mean value
        # shapes=[
        #     dict(
        #         type='line',
        #         x0=df['Date'].iloc[0],
        #         x1=df['Date'].iloc[-1],
        #         y0=mean_value,
        #         y1=mean_value,
        #         line=dict(color='blue', dash='dot')
        #     )
        # ]
    )
    if show:
        fig.show(renderer="notebook")
    else:
        return fig

def line_plot(val, col, title, show):
    """ line plot with moving average"""
    fig = px.line(val, x = val.index, y = val[col], title = title)
    fig.update_traces(line=dict(color='green'))

    # Add the moving average
    window = 14
    moving_avg = val[col].rolling(window=window).mean()

    fig.add_trace(go.Scatter(x = val.index, y = moving_avg,
                            mode='lines', name=f'{window}-Day Moving Average',
                            showlegend = False,
                            line=dict(color='orange', dash = 'dot') ))
    hide_axis_title(fig)
    fig_add_mean(fig, val, col)

    if show:
        fig.show(renderer="notebook")
    else:
        return fig

def bar_plot_with_line(df, col, fig_title, show):

    fig = go.Figure()

# Create a color scale
    scale = px.colors.sequential.Viridis
# Map y-values to colors
    df['color'] = df[col].apply(lambda y: scale[int(y * (len(scale) - 1) / max(df[col]))])

# Add a Bar trace for the bar plot
    fig.add_trace(
    go.Bar(x = df.index,
            y = df[col],
            marker_color = df['color'],
            text = [f'{round(val/1e6, 2)}M' for val in df[col]],
            textposition='auto'
        )
    )

    fig.add_trace(
    go.Scatter(x = df.index, y = df[col],
            mode='lines+markers', line_shape='linear',
            line=dict(color='green'))
    )

    fig.update_layout(
    title=fig_title,
    xaxis_title='',
    yaxis_title='',
    template='plotly_white',
    showlegend = False
    )
    fig_add_mean(fig, df, col)
    if show:
        fig.show(renderer="notebook")
    else:
        return fig

def bar_plot_grouped(data, col1, col2, fig_title, show):
    trace1 = go.Bar(x=data.index, y=data[col1], name=col1, text=data[col1].apply(etl.format_money_USD), marker_color = 'blue')
    trace2 = go.Bar(x=data.index, y=data[col2], name=col2, text=data[col2].apply(etl.format_money_USD), marker_color = 'yellow')

    layout = go.Layout(
        barmode='group',
        title=fig_title,
        xaxis=dict(title='', tickangle=-45),
        yaxis=dict(title='')
    )
    fig = go.Figure(data=[trace1, trace2], layout=layout)
    fig.update_layout(xaxis=dict(tickformat='%b'), showlegend=False)
                    #legend=dict(orientation='h', x=0.2, y=-0.1)
    fig = fig_add_mean(fig, data, col1)
    hide_axis_title(fig)

    if show:
        fig.show(renderer="notebook")
    else:
        return fig

def bar_plot_grouped_general(data, col1, col2, fig_title, show):

    trace1 = go.Bar(x=data.index, y = data[col1],
                    name = col1,
                    text = data[col1].apply(etl.format_money_USD),
                    marker_color = 'blue')
    trace2 = go.Bar(x = data.index, y = data[col2],
                    name = col2,
                    text = data[col2].apply(etl.format_money_USD),
                    marker_color = 'red')

    layout = go.Layout(
        barmode='group',
        title=fig_title,
        xaxis=dict(title='', tickangle=-45),
        yaxis=dict(title='')
    )

    fig = go.Figure(data=[trace1, trace2], layout=layout)

    if show:
        fig.show(renderer="notebook")
    else:
        return fig

def chart_by_period(data, categories, period, title):
    """bar plot by period on top and stacked bar plot by period on the bottom"""
    data_sum_by_period_by_category = da.sum_by_period_by_category(categories, period, data, 'Category').fillna(0)
    if period == 'w':
        data_sum_by_period_by_category['Date'] = data_sum_by_period_by_category['Date'].astype(str).str.split('/').str[0]

    fig = stack_bar_plot(data_sum_by_period_by_category, title, False)

    return fig
