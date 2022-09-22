import dash
# https://dash.plotly.com/dash-core-components
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc

# https://dashcheatsheet.pythonanywhere.com/

import plotly.graph_objs as go
from plotly.subplots import make_subplots
import plotly.express as px

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

df_clean_pro_daily_count['cumul_count'] = df_clean_pro_daily_count.apply(
    lambda x: running_sum(df_clean_pro_daily_count, x.scraped_date), axis=1)

palette = {'red': '#EE553B',
           'green': '#00CC96'}

dropdown_brand = df_clean_pro['brand'].sort_values(ascending=True).unique()
dropdown_category = df_clean_pro['category'].sort_values(ascending=True).unique()
dropdown_model = df_clean_pro['model'].value_counts()
dropdown_model = dropdown_model[dropdown_model > 5].index


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
    fig_daily_spiders.update_xaxes(showgrid=False, range=[df_raw.scraped_date.min(), df_raw.scraped_date.max()])

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
    fig_daily_master_clean.update_yaxes(secondary_y=False, showgrid=False, color=palette['green'])
    fig_daily_master_clean.update_yaxes(secondary_y=True, showgrid=False, color=palette['red'])

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
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        dcc.Dropdown(dropdown_brand, id='brand-dropdown', placeholder='Select brand'),
                        html.Br(),
                        dcc.Dropdown(dropdown_category, id='category-dropdown', placeholder='Select category'),
                        html.Br(),
                        html.Div("Select engine size range"),
                        dcc.RangeSlider(df_clean_pro['engine_size'].min(),
                                        df_clean_pro['engine_size'].max(),
                                        10,
                                        value=[0, 1800],
                                        id='engine_size-slider',
                                        marks=None,
                                        tooltip={"placement": "bottom", "always_visible": True}),
                        html.Br(),
                        html.Div("Select bike year range"),
                        dcc.RangeSlider(df_clean_pro['circulation_year'].min(),
                                        df_clean_pro['circulation_year'].max(),
                                        1,
                                        value=[2000, 2022],
                                        id='circulation_year-slider',
                                        marks=None,
                                        tooltip={"placement": "bottom", "always_visible": True}),
                        html.Br(),
                        dcc.Dropdown(dropdown_model, id='model-dropdown', multi=True,
                                     placeholder='Select model(s)'),
                        html.Br(),
                        dcc.RangeSlider(df_clean_pro['price'].min(),
                                        df_clean_pro['price'].max(),
                                        1,
                                        value=[500, 30000],
                                        id='price-slider',
                                        marks=None,
                                        tooltip={"placement": "bottom", "always_visible": True}),
                        html.Br(),
                    ])
                ])
            ], width=2),
            html.Br(),
            dbc.Col([
                dbc.Row([
                    dbc.Card([
                        dbc.CardBody([
                            html.H3("💵 Market price overview (€)", className="card-title"),
                            dcc.Graph(id='fig_daily_master_clean_price')
                        ])
                    ])
                ]),
                html.Br(),
                dbc.Row([
                    dbc.Card([
                        dbc.CardBody([
                            html.H3("Bike price history (€)", className="card-title"),
                            dcc.Graph(id='fig_master_clean_price_3d')
                        ])
                    ])
                ])
            ])
        ]),
    ],
        fluid=True)
])


#############
# Callbacks #
#############
def boolean_mask(brand=None, category=None, model=None, engine_size=None, circulation_year=None, price=None):
    bool_lists = ((df_clean_pro['engine_size'] >= min(engine_size)) &
                  (df_clean_pro['engine_size'] <= max(engine_size)) &
                  (df_clean_pro['circulation_year'] >= min(circulation_year)) &
                  (df_clean_pro['circulation_year'] <= max(circulation_year)) &
                  (df_clean_pro['price'] >= min(price)) &
                  (df_clean_pro['price'] <= max(price)))

    if brand is not None:
        bool_brand = df_clean_pro['brand'] == brand
    else:
        bool_brand = ~df_clean_pro['brand'].isnull()

    if category is not None:
        bool_category = df_clean_pro['category'] == category
    else:
        bool_category = ~df_clean_pro['category'].isnull()

    if model is not None:
        bool_model = df_clean_pro['model'].isin(model)
    else:
        bool_model = ~df_clean_pro['model'].isnull()

    return bool_lists & bool_brand & bool_category & bool_model


@app.callback(
    Output('category-dropdown', 'options'),
    Input('brand-dropdown', 'value'),
    Input('category-dropdown', 'value'),
    Input('model-dropdown', 'value'),
    Input('engine_size-slider', 'value'),
    Input('circulation_year-slider', 'value'),
    Input('price-slider', 'value'))
def update_dd_category(brand, category, model, engine_size, circulation_year, price):
    return df_clean_pro[boolean_mask(brand=brand,
                                     category=None,
                                     model=model,
                                     engine_size=engine_size,
                                     circulation_year=circulation_year,
                                     price=price)]['category'].unique()


@app.callback(
    Output('model-dropdown', 'options'),
    Input('brand-dropdown', 'value'),
    Input('category-dropdown', 'value'),
    Input('model-dropdown', 'value'),
    Input('engine_size-slider', 'value'),
    Input('circulation_year-slider', 'value'),
    Input('price-slider', 'value'))
def update_dd_model(brand, category, model, engine_size, circulation_year, price):
    return df_clean_pro[boolean_mask(brand=brand,
                                     category=category,
                                     model=None,
                                     engine_size=engine_size,
                                     circulation_year=circulation_year,
                                     price=price)]['model'].unique()


@app.callback(
    Output('brand-dropdown', 'options'),
    Input('brand-dropdown', 'value'),
    Input('category-dropdown', 'value'),
    Input('model-dropdown', 'value'),
    Input('engine_size-slider', 'value'),
    Input('circulation_year-slider', 'value'),
    Input('price-slider', 'value'))
def update_dd_brand(brand, category, model, engine_size, circulation_year, price):
    return df_clean_pro[boolean_mask(brand=None,
                                     category=category,
                                     model=model,
                                     engine_size=engine_size,
                                     circulation_year=circulation_year,
                                     price=price)]['brand'].unique()

@app.callback(
    Output('fig_daily_master_clean_price', 'figure'),
    Input('brand-dropdown', 'value'),
    Input('category-dropdown', 'value'),
    Input('model-dropdown', 'value'),
    Input('engine_size-slider', 'value'),
    Input('circulation_year-slider', 'value'),
    Input('price-slider', 'value'))
def gen_fig_daily_master_clean_price(brand, category, model, engine_size, circulation_year, price):
    df_filtered = df_clean_pro[boolean_mask(brand, category, model, engine_size, circulation_year, price)]
    df_clean_pro_daily_price = df_filtered[['scraped_date', 'price']].groupby(by=['scraped_date'], axis=0,
                                                                              as_index=False).mean()
    # mooving average
    df_clean_pro_daily_price['SMA30'] = df_clean_pro_daily_price['price'].rolling(30).mean()

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
    fig_daily_master_clean_price.update_yaxes(secondary_y=False, showgrid=False, color=palette['green'])
    fig_daily_master_clean_price.update_yaxes(secondary_y=True, showgrid=False, color=palette['red'])

    # plotly manual axis adjustments
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


@app.callback(
    Output('fig_master_clean_price_3d', 'figure'),
    Input('brand-dropdown', 'value'),
    Input('category-dropdown', 'value'),
    Input('model-dropdown', 'value'),
    Input('engine_size-slider', 'value'),
    Input('circulation_year-slider', 'value'),
    Input('price-slider', 'value'))
def update_scatter_3d(brand, category, model, engine_size, circulation_year, price):
    df_filtered = df_clean_pro[boolean_mask(brand, category, model, engine_size, circulation_year, price)]
    if brand is None:
        color_col = 'brand'
    elif brand is not None:
        if category is None:
            color_col = 'category'
        elif category is not None:
            color_col = 'engine_size'

    fig_master_clean_price_3d = px.scatter_3d(df_filtered,
                                              x='mileage',
                                              y='bike_age',
                                              z='price',
                                              hover_name='model',
                                              color=color_col,
                                              log_x=True,
                                              log_y=False,
                                              log_z=False,
                                              height=800,
                                              color_continuous_scale='rdylgn')

    fig_master_clean_price_3d.update_layout(template='plotly_dark',
                                            plot_bgcolor='rgba(0, 0, 0, 0)',
                                            paper_bgcolor='rgba(0, 0, 0, 0)')
    fig_master_clean_price_3d.update_traces(marker_size=2)
    return fig_master_clean_price_3d


if __name__ == "__main__":
    app.run_server(debug=True, host="0.0.0.0", port=8080, use_reloader=True)
