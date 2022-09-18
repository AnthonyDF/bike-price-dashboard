import dash
# https://dash.plotly.com/dash-core-components
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc

# https://dashcheatsheet.pythonanywhere.com/

import plotly.graph_objs as go
from plotly.subplots import make_subplots

from utilities.data import get_table
from utilities.calculation import running_sum

from datetime import datetime, timedelta

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.COSMO])
server = app.server

# Import data from postgresql
filter_date = datetime.today() - timedelta(days=21)
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

df_clean_pro_daily_count['cumul_count'] = df_clean_pro_daily_count.apply(
    lambda x: running_sum(df_clean_pro_daily_count, x.scraped_date), axis=1)

palette = {'red': '#BF3A3A',
           'green': '#469955'}


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

    fig_daily_spiders.update_layout(height=1500, width=1500)
    fig_daily_spiders.update_layout(showlegend=False)
    return fig_daily_spiders


def gen_fig_daily_master_clean():
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
    fig_daily_master_clean.update_yaxes(title_text="Cumulated rows", secondary_y=False)
    fig_daily_master_clean.update_yaxes(title_text="Daily rows", secondary_y=True)

    # plotly manual axis adjustments
    fig_daily_master_clean.update_yaxes(range=[0, 2000], secondary_y=False)
    fig_daily_master_clean.update_xaxes(range=[datetime(2021, 11, 1), datetime.today()])

    return fig_daily_master_clean


##########
# Layout #
##########

app.layout = html.Div(children=[
    html.H1('🏍️ Bike price project dashboard'),
    html.Div([
        html.H3('📈️ Scraping spiders surveillance'),
        dcc.Graph(id='fig_daily_spiders', figure=gen_fig_daily_spiders())
    ]),
    html.Div([
        html.H3('💽 Database surveillance'),
        html.H4('Database size after advanced cleaning'),
        dcc.Graph(id='fig_daily_master_clean',
                  figure=gen_fig_daily_master_clean())
    ])
])

if __name__ == "__main__":
    app.run_server(debug=True, host="0.0.0.0", port=8080, use_reloader=True)
