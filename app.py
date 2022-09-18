import dash
# https://dash.plotly.com/dash-core-components
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc

# https://dashcheatsheet.pythonanywhere.com/

import plotly.graph_objs as go
from plotly.subplots import make_subplots

import pandas as pd

from utilities.data import get_table
from utilities.calculation import running_sum

from datetime import datetime, timedelta

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.SLATE])
server = app.server

# Import data from postgresql
filter_date = datetime.today() - timedelta(days=40)
# raw data
df_raw = get_table("master")
df_raw = df_raw[df_raw.source.isin(
    ['lepoledeloccasion', '4en1', 'fulloccaz', 'seb-moto', 'motoservices', 'motovente', 'montoconcess', 'moto-station',
     'autoscoot24', 'leparking'])]
df_raw = df_raw[df_raw['scraped_date'] >= filter_date.date()]
df_raw_daily_count = df_raw[['scraped_date', 'source', 'url']].groupby(by=['scraped_date', 'source'], axis=0,
                                                                       as_index=False).count()
# clean data
df_clean_pro = get_table("master_clean_pro")

df_clean_pro_daily_count = df_clean_pro[['scraped_date', 'url']].groupby(by=['scraped_date'], axis=0,
                                                                         as_index=False).count()
df_clean_pro_daily_price = df_clean_pro[['scraped_date', 'price']].groupby(by=['scraped_date'], axis=0,
                                                                           as_index=False).mean()
df_clean_pro_daily_price['SMA30'] = df_clean_pro_daily_price['price'].rolling(30).mean()

df_clean_pro_daily_count['cumul_count'] = df_clean_pro_daily_count.apply(
    lambda x: running_sum(df_clean_pro_daily_count, x.scraped_date), axis=1)

palette = {'red': '#EE553B',
           'green': '#00CC96'}


def gen_fig_daily_spiders():
    fig_daily_spiders = make_subplots(rows=len(df_raw.source.unique()), cols=1,
                                      subplot_titles=tuple(df_raw.source.unique()))

    for k, source in zip(range(1, len(df_raw.source.unique()) + 1), df_raw.source.unique()):
        df_temp = df_raw_daily_count[df_raw_daily_count['source'] == source]

        if df_temp['scraped_date'].max() < (datetime.today() - timedelta(days=2)).date():
            color = palette['red']
        else:
            color = palette['green']

        fig_daily_spiders.add_trace(
            go.Bar(x=df_temp.scraped_date,
                   y=df_temp.url,
                   name=source,
                   marker=dict(color=f'{color}')),
            row=k, col=1)

    fig_daily_spiders.update_layout(showlegend=False, height=1500,
                                    template='plotly_dark',
                                    plot_bgcolor='rgba(0, 0, 0, 0)',
                                    paper_bgcolor='rgba(0, 0, 0, 0)')
    fig_daily_spiders.update_yaxes(showgrid=False)
    fig_daily_spiders.update_xaxes(showgrid=False)

    return fig_daily_spiders


def gen_fig_daily_master_clean_count():
    fig_daily_master_clean = make_subplots(specs=[[{"secondary_y": True}]])

    fig_daily_master_clean.add_trace(
        go.Scatter(x=df_clean_pro_daily_count['scraped_date'],
                   y=df_clean_pro_daily_count['cumul_count'],
                   name="Cmulated rows",
                   mode="lines",
                   marker=dict(color=palette['red'])),
        secondary_y=True
    )

    fig_daily_master_clean.add_trace(
        go.Bar(x=df_clean_pro_daily_count['scraped_date'],
               y=df_clean_pro_daily_count['url'],
               name="Daily new rows",
               marker=dict(color=palette['green'])),
        secondary_y=False
    )

    fig_daily_master_clean.update_xaxes(title_text="scraped date")

    # Set y-axes titles
    fig_daily_master_clean.update_yaxes(secondary_y=False, showgrid=False)
    fig_daily_master_clean.update_yaxes(secondary_y=True, showgrid=False)

    # plotly manual axis adjustments
    fig_daily_master_clean.update_yaxes(range=[0, 2000], secondary_y=False, showgrid=False)
    fig_daily_master_clean.update_xaxes(range=[datetime(2021, 11, 1), datetime.today()], showgrid=False)
    fig_daily_master_clean.update_layout(template='plotly_dark',
                                         plot_bgcolor='rgba(0, 0, 0, 0)',
                                         paper_bgcolor='rgba(0, 0, 0, 0)',
                                         legend=dict(
                                             yanchor="top",
                                             y=0.99,
                                             xanchor="left",
                                             x=0.1,
                                             bgcolor='rgba(0, 0, 0, 0)'
                                         ))

    return fig_daily_master_clean


def gen_fig_daily_master_clean_price():
    fig_daily_master_clean_price = make_subplots(specs=[[{"secondary_y": True}]])

    fig_daily_master_clean_price.add_trace(
        go.Bar(x=df_clean_pro_daily_price['scraped_date'],
               y=df_clean_pro_daily_price['price'],
               name="Daily average price",
               marker=dict(color=palette['green'])),
        secondary_y=False
    )

    fig_daily_master_clean_price.add_trace(
        go.Scatter(x=df_clean_pro_daily_price['scraped_date'],
                   y=df_clean_pro_daily_price['SMA30'],
                   name="Price moving average (30 days)",
                   mode="lines",
                   marker=dict(color=palette['red'])),
        secondary_y=True
    )

    fig_daily_master_clean_price.update_xaxes(title_text="scraped date")

    # Set y-axes titles
    fig_daily_master_clean_price.update_yaxes(secondary_y=False, showgrid=False)
    fig_daily_master_clean_price.update_yaxes(secondary_y=True, showgrid=False)

    # plotly manual axis adjustments
    fig_daily_master_clean_price.update_yaxes(secondary_y=False, showgrid=False)
    fig_daily_master_clean_price.update_xaxes(range=[datetime(2021, 11, 1), datetime.today()], showgrid=False)
    fig_daily_master_clean_price.update_layout(template='plotly_dark',
                                               plot_bgcolor='rgba(0, 0, 0, 0)',
                                               paper_bgcolor='rgba(0, 0, 0, 0)',
                                               legend=dict(
                                                   yanchor="top",
                                                   y=0.99,
                                                   xanchor="left",
                                                   x=0.1,
                                                   bgcolor='rgba(0, 0, 0, 0)'
                                               ))

    return fig_daily_master_clean_price


##########
# Layout #
##########

app.layout = html.Div([
    html.H1('🏍️ Bike price project dashboard'),
    dbc.Container([
        dbc.Card([
            dbc.CardBody([
                html.H3("📈️ Scraping spiders surveillance", className="card-title"),
                dcc.Graph(id='fig_daily_spiders', figure=gen_fig_daily_spiders())
            ])
        ]),
        html.Br(),
        dbc.Card([
            dbc.CardBody([
                html.H3("💽 Database surveillance", className="card-title"),
                html.H4("Database size after advanced cleaning", className="card-title"),
                dcc.Graph(id='fig_daily_master_clean',
                          figure=gen_fig_daily_master_clean_count())
            ])
        ]),
        html.Br(),
        dbc.Card([
            dbc.CardBody([
                html.H3("💵 Market Price overview (€)", className="card-title"),
                dcc.Graph(id='fig_daily_master_clean_price',
                          figure=gen_fig_daily_master_clean_price())
            ])
        ])
    ], fluid=True)
])

if __name__ == "__main__":
    app.run_server(debug=True, host="0.0.0.0", port=8080, use_reloader=True)
