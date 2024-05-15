import numpy as np
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

    fig.update_layout(
        showlegend = False,
        grid={'columns': cols, 'rows': rows, 'pattern': "independent"})
    if show:
        fig.show(renderer="notebook")
    else:
        return fig


def pie_plot(data, col, title, show):
    """ pie plot with hole"""

    data['hover_text'] = [f'{idx}: {etl.format_money_USD(val)}' for idx, val in zip(data.index, data[col])]
    data['labels'] = data.index.where(data[col] != 0, '')

    fig = px.pie(data,
                values = col,
                names = data.index,
                hole=0.5,
                title = title,
                custom_data =['hover_text']
                )

    fig.update_traces(  text=data['labels'],
                        textinfo='text+percent',
                        textposition='inside',
                        insidetextorientation='radial',
                        hovertemplate='%{customdata[0]}<extra></extra>'
                    )
    fig.update_layout(showlegend=False)

    if show:
        fig.show(renderer="notebook")
    else:
        return fig

def bar_plot(data, col, fig_title, show):
    """ bar plot with mean"""
    data['hover_text'] = data.index.astype(str) + ': ' + data[col].apply(etl.format_money_USD)
    fig = px.bar(data,
                x = data.index,
                y = col,
                color = col,
                text_auto = '.2s',
                title = fig_title,
                hover_data = {'hover_text': True, col: False}
            )

    fig.update_traces(hovertemplate='%{customdata[0]}<extra></extra>')

    fig_add_mean(fig, data, col)
    hide_axis_title(fig)

    if show:
        fig.show(renderer="notebook")
    else:
        return fig


# def stack_bar_plot(df, title, show):
#     """stacked bar plot with mean"""
#     df['Date'] = df['Date'].astype(str)
#     mean_value = df[df.columns[1:]].sum(axis=1).mean()

#     fig = go.Figure()
# #    for column in df.columns[1:]:
#     for column in df.select_dtypes(include=[np.number]).columns:
#         fig.add_trace(
#                 go.Bar(name=column, x = df['Date'], y = df[column],
#                     text = df[column].apply(etl.format_money_USD)
#         ))

#     fig.update_layout(
#         barmode='stack',
#         title = title,
#         legend=dict(orientation='h', x=0, y=1.15),
#         xaxis=dict(tickformat='%b'),
#     # Add a horizontal line at the mean value
#         shapes=[
#             dict(
#                 type='line',
#                 x0=df['Date'].iloc[0],
#                 x1=df['Date'].iloc[-1],
#                 y0=mean_value,
#                 y1=mean_value,
#                 line=dict(color='blue', dash='dot')
#             )
#         ]
#     )
#     if show:
#         fig.show(renderer="notebook")
#     else:
#         return fig


def stack_bar_plot(df, title, show):
    """Stacked bar plot with mean, displaying formatted monetary values on each slice."""
    # Ensure 'Date' is of type string for plotting
    df['Date'] = df['Date'].astype(str)
    # Calculate the overall mean value of sums across numeric columns for each date
    mean_value = df[df.select_dtypes(include=[np.number]).columns].sum(axis=1).mean()

    # Initialize the figure
    fig = go.Figure()

    # Iterate through numeric columns to add as separate bar traces
    for column in df.select_dtypes(include=[np.number]).columns:
        fig.add_trace(
            go.Bar(
                name=column,
                x=df['Date'],
                y=df[column],
                text=df[column].apply(etl.format_money_USD),
                textposition='auto'  # This ensures text labels are placed on the bars
            )
        )

    # Set up the layout with stacking, title, and axis formatting
    fig.update_layout(
        barmode='stack',
        title=title,
        legend=dict(orientation='h', x=0, y=1.15),
        xaxis=dict(tickformat='%b'),

        # Add a horizontal line at the mean value
        shapes=[
            dict(
                type='line',
                x0=df['Date'].iloc[0],
                x1=df['Date'].iloc[-1],
                y0=mean_value,
                y1=mean_value,
                line=dict(color='blue', dash='dot')
            )
        ]
    )

    # Show or return the plot based on the 'show' parameter
    if show:
        fig.show(renderer="notebook")
    else:
        return fig

