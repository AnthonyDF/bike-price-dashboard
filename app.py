import dash
# https://dash.plotly.com/dash-core-components
from dash import dcc, dash_table, html
from dash.dash_table import FormatTemplate
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
from flask_caching import Cache

# https://dashcheatsheet.pythonanywhere.com/

import plotly.graph_objs as go
from plotly.subplots import make_subplots
import plotly.express as px
import plotly.figure_factory as ff

import pandas as pd
import numpy as np

from utilities.data import get_table
from utilities.calculation import running_sum

from datetime import datetime, timedelta

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.SLATE])
server = app.server
cache = Cache(app.server, config={
    'CACHE_TYPE': 'filesystem',
    'CACHE_DIR': 'cache-directory'
})
TIMEOUT = 60

percentage = FormatTemplate.percentage(0)

# Import data from postgresql
filter_date = datetime.today() - timedelta(days=40)
# raw data
df_raw = get_table("master", max_scraped_date=filter_date.date())
df_raw_daily_count = df_raw[['scraped_date', 'source', 'url']].groupby(by=['scraped_date', 'source'], axis=0,
                                                                       as_index=False).count()
# clean data
df_clean_pro = get_table("master_clean_pro")
df_clean_pro.sort_values('scraped_date', ascending=False, inplace=True)
df_clean_pro_daily_count = df_clean_pro[['scraped_date', 'url']].groupby(by=['scraped_date'], axis=0,
                                                                         as_index=False).count()
df_clean_pro_daily_count['cumul_count'] = df_clean_pro_daily_count.apply(
    lambda x: running_sum(df_clean_pro_daily_count, x.scraped_date), axis=1)


def create_markdown_url(url):
    markdown = f"[View]({str(url)})"
    return markdown


df_clean_pro['url'] = df_clean_pro['url'].apply(lambda x: create_markdown_url(x))
palette = {'red': '#EE553B',
           'green': '#00CC96'}

dropdown_brand = df_clean_pro['brand'].sort_values(ascending=True).unique()
dropdown_category = df_clean_pro['category'].sort_values(ascending=True).unique()
dropdown_model = df_clean_pro['model'].value_counts()
dropdown_model = dropdown_model[dropdown_model > 5].index
dropdown_localisation = df_clean_pro['code_name'].sort_values(ascending=True).unique()



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


def gen_correlation_matrix():
    df_corr = df_clean_pro.drop(columns=['circulation_year']).corr()  # Generate correlation matrix
    mask = np.triu(np.ones_like(df_corr, dtype=bool))
    df_corr = df_corr[mask]

    fig_corr = ff.create_annotated_heatmap(
        np.array(df_corr),
        x=list(df_corr.columns),
        y=list(df_corr.index),
        annotation_text=np.around(np.array(df_corr), decimals=2),
        colorscale='Viridis'
    )

    fig_corr.update_layout(template='plotly_dark',
                           plot_bgcolor='rgba(0, 0, 0, 0)',
                           paper_bgcolor='rgba(0, 0, 0, 0)', )

    return fig_corr


##########
# Layout #
##########

card_scraping = \
    dbc.Card([
        dbc.CardBody([
            html.H3("📈️ Scraping spiders surveillance", className="card-title"),
            dcc.Graph(id='fig_daily_spiders', figure=gen_fig_daily_spiders())
        ])
    ])

card_daily_avg = \
    dbc.Card([
        dbc.CardBody([
            html.H3("💽 Database surveillance", className="card-title"),
            html.H4("Database size after advanced cleaning", className="card-title"),
            dcc.Graph(id='fig_daily_master_clean',
                      figure=gen_fig_daily_master_clean_count())
        ])
    ])

card_dropdown = \
    dbc.Card([
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.H3("🔍 Select Filters", className="card-title"),
                    html.Br(),
                    dcc.Dropdown(dropdown_brand, id='brand-dropdown', placeholder='Select brand'),
                    html.Br(),
                    dcc.Dropdown(dropdown_category, id='category-dropdown', placeholder='Select category'),
                    html.Br(),
                    dcc.Dropdown(dropdown_model, id='model-dropdown', multi=True, placeholder='Select model(s)'),
                    html.Br(),
                ]),
                dbc.Col([
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
                    html.Div("Select bike price (€) range"),
                    dcc.RangeSlider(df_clean_pro['price'].min(),
                                    df_clean_pro['price'].max(),
                                    1,
                                    value=[500, 30000],
                                    id='price-slider',
                                    marks=None,
                                    tooltip={"placement": "bottom", "always_visible": True}),
                ]),
                dbc.Col([
                    html.Br(),
                    dcc.Dropdown(dropdown_localisation, id='localisation-dropdown', placeholder='Select localisation'),
                    html.Br(),
                ])
            ])
        ])
    ])

card_market_price = \
    dbc.Card([
        dbc.CardBody([
            html.H3("💵 Market price overview (€)", className="card-title"),
            dcc.Graph(id='fig_daily_master_clean_price')
        ])
    ])

card_corr_matrix = \
    dbc.Card([
        dbc.CardBody([
            html.H3("🧮 Correlation Matrix", className="card-title"),
            dcc.Graph(id='fig_corr_matrix', figure=gen_correlation_matrix())
        ])
    ])

card_3D_plot = \
    dbc.Card([
        dbc.CardBody([
            html.H3("💵 Bike price history (€)", className="card-title"),
            dcc.Graph(id='fig_master_clean_price_3d')
        ])
    ])

card_distsubplot = \
    dbc.Card([
        dbc.CardBody([
            html.H3("📊 Distribution", className="card-title"),
            dcc.Graph(id='fig_distsubplot')
        ])
    ])

card_distplot_brand = \
    dbc.Card([
        dbc.CardBody([
            dcc.Graph(id='fig_distplot_brand')
        ])
    ])

card_distplot_category = \
    dbc.Card([
        dbc.CardBody([
            dcc.Graph(id='fig_distplot_category')
        ])
    ])

card_datatable_ads = \
    dbc.Card([
        dbc.CardBody([
            dash_table.DataTable(id='datatable_ads',
                                 data=[],
                                 sort_action='native',
                                 page_current=0,
                                 page_size=20,
                                 # page_action='custom',
                                 filter_action='custom',
                                 filter_query='',
                                 editable=False,
                                 row_deletable=False,
                                 hidden_columns=['id',
                                                 'comment',
                                                 'circulation_date',
                                                 'warranty_bool',
                                                 'warranty_date',
                                                 'vendor_type',
                                                 'source',
                                                 'first_hand',
                                                 'condition',
                                                 'options',
                                                 'annonce_date',
                                                 'engine_type',
                                                 'bike_age',
                                                 'dept_code',
                                                 'localisation'
                                                 ],
                                 style_header={
                                     'backgroundColor': 'rgb(30, 30, 30)',
                                     'color': 'white'
                                 },
                                 style_data={
                                     'backgroundColor': 'rgb(50, 50, 50)',
                                     'color': 'white',
                                     'whiteSpace': 'normal',
                                     'height': 'auto',
                                 },
                                 style_cell={'fontSize': 12,
                                             # 'font-family': 'sans-serif'
                                             }
                                 )
        ])
    ])

app.layout = html.Div([
    html.H1('🏍️ Bike price project dashboard'),
    dbc.Container([
        card_scraping,
        html.Br(),
        card_daily_avg,
        html.Br(),
        card_dropdown,
        html.Br(),
        card_datatable_ads,
        html.Br(),
        card_market_price,
        html.Br(),
        card_3D_plot,
        html.Br(),
        dbc.Row([
            dbc.Col([card_distsubplot,
                     html.Br(),
                     card_distplot_brand]),
            dbc.Col([card_corr_matrix,
                     html.Br(),
                     card_distplot_category])
        ]),
    ], fluid=True)
])


#############
# Callbacks #
#############
def boolean_mask(brand=None, category=None, model=None, engine_size=None,
                 circulation_year=None, price=None, localisation=None):
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

    if localisation is not None:
        bool_loc = df_clean_pro['code_name'] == localisation
    else:
        bool_loc = ~df_clean_pro['code_name'].isnull()

    return bool_lists & bool_brand & bool_category & bool_model & bool_loc


@app.callback(
    Output('category-dropdown', 'options'),
    Input('brand-dropdown', 'value'),
    Input('category-dropdown', 'value'),
    Input('model-dropdown', 'value'),
    Input('engine_size-slider', 'value'),
    Input('circulation_year-slider', 'value'),
    Input('price-slider', 'value'),
    Input('localisation-dropdown', 'value'))
def update_dd_category(brand, category, model, engine_size, circulation_year, price, localisation):
    return df_clean_pro[boolean_mask(brand=brand,
                                     category=None,
                                     model=model,
                                     engine_size=engine_size,
                                     circulation_year=circulation_year,
                                     price=price,
                                     localisation=localisation)]['category'].unique()


@app.callback(
    Output('model-dropdown', 'options'),
    Input('brand-dropdown', 'value'),
    Input('category-dropdown', 'value'),
    Input('model-dropdown', 'value'),
    Input('engine_size-slider', 'value'),
    Input('circulation_year-slider', 'value'),
    Input('price-slider', 'value'),
    Input('localisation-dropdown', 'value'))
def update_dd_model(brand, category, model, engine_size, circulation_year, price, localisation):
    return df_clean_pro[boolean_mask(brand=brand,
                                     category=category,
                                     model=None,
                                     engine_size=engine_size,
                                     circulation_year=circulation_year,
                                     price=price,
                                     localisation=localisation)]['model'].unique()


@app.callback(
    Output('brand-dropdown', 'options'),
    Input('brand-dropdown', 'value'),
    Input('category-dropdown', 'value'),
    Input('model-dropdown', 'value'),
    Input('engine_size-slider', 'value'),
    Input('circulation_year-slider', 'value'),
    Input('price-slider', 'value'),
    Input('localisation-dropdown', 'value'))
def update_dd_brand(brand, category, model, engine_size, circulation_year, price, localisation):
    return df_clean_pro[boolean_mask(brand=None,
                                     category=category,
                                     model=model,
                                     engine_size=engine_size,
                                     circulation_year=circulation_year,
                                     price=price,
                                     localisation=localisation)]['brand'].unique()


@app.callback(
    Output('fig_daily_master_clean_price', 'figure'),
    Input('brand-dropdown', 'value'),
    Input('category-dropdown', 'value'),
    Input('model-dropdown', 'value'),
    Input('engine_size-slider', 'value'),
    Input('circulation_year-slider', 'value'),
    Input('price-slider', 'value'),
    Input('localisation-dropdown', 'value'))
def gen_fig_daily_master_clean_price(brand, category, model, engine_size, circulation_year, price, localisation):
    df_filtered = df_clean_pro[boolean_mask(brand, category, model, engine_size, circulation_year, price, localisation)]
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
    Output('fig_distsubplot', 'figure'),
    Input('brand-dropdown', 'value'),
    Input('category-dropdown', 'value'),
    Input('model-dropdown', 'value'),
    Input('engine_size-slider', 'value'),
    Input('circulation_year-slider', 'value'),
    Input('price-slider', 'value'),
    Input('localisation-dropdown', 'value'))
def update_distrib_subplot(brand, category, model, engine_size, circulation_year, price, localisation):
    df_filtered = df_clean_pro[boolean_mask(brand, category, model, engine_size, circulation_year, price, localisation)]
    fig_distplot = make_subplots(rows=2, cols=2, subplot_titles=tuple(['price', 'bike_age', 'mileage', 'engine_size']))
    fig_distplot.add_trace(go.Histogram(x=df_filtered['price'], histfunc="count", nbinsx=50), row=1, col=1)
    fig_distplot.add_trace(go.Histogram(x=df_filtered['bike_age'], histfunc="count", nbinsx=50), row=1, col=2)
    fig_distplot.add_trace(go.Histogram(x=df_filtered['mileage'], histfunc="count", nbinsx=50), row=2, col=1)
    fig_distplot.add_trace(go.Histogram(x=df_filtered['engine_size'], histfunc="count", nbinsx=50), row=2, col=2)
    fig_distplot.update_layout(showlegend=False,
                               template='plotly_dark',
                               plot_bgcolor='rgba(0, 0, 0, 0)',
                               paper_bgcolor='rgba(0, 0, 0, 0)', )
    # height=350)

    fig_distplot.update_yaxes(showgrid=False)
    return fig_distplot


@app.callback(
    Output('fig_distplot_brand', 'figure'),
    Input('brand-dropdown', 'value'),
    Input('category-dropdown', 'value'),
    Input('model-dropdown', 'value'),
    Input('engine_size-slider', 'value'),
    Input('circulation_year-slider', 'value'),
    Input('price-slider', 'value'),
    Input('localisation-dropdown', 'value'))
def update_distrib_plot_brand(brand, category, model, engine_size, circulation_year, price, localisation):
    df_filtered = df_clean_pro[boolean_mask(brand, category, model, engine_size, circulation_year, price, localisation)]
    fig_distplot = make_subplots(rows=1, cols=1, subplot_titles=tuple(['brand']))
    fig_distplot.add_trace(go.Histogram(x=df_filtered['brand'], histfunc="count", nbinsx=50), row=1, col=1)
    fig_distplot.update_layout(showlegend=False,
                               template='plotly_dark',
                               plot_bgcolor='rgba(0, 0, 0, 0)',
                               paper_bgcolor='rgba(0, 0, 0, 0)', )
    # height=350)

    fig_distplot.update_yaxes(showgrid=False)

    return fig_distplot


@app.callback(
    Output('fig_distplot_category', 'figure'),
    Input('brand-dropdown', 'value'),
    Input('category-dropdown', 'value'),
    Input('model-dropdown', 'value'),
    Input('engine_size-slider', 'value'),
    Input('circulation_year-slider', 'value'),
    Input('price-slider', 'value'),
    Input('localisation-dropdown', 'value'))
def update_distrib_plot_brand(brand, category, model, engine_size, circulation_year, price, localisation):
    df_filtered = df_clean_pro[boolean_mask(brand, category, model, engine_size, circulation_year, price, localisation)]
    fig_distplot = make_subplots(rows=1, cols=1, subplot_titles=tuple(['category']))
    fig_distplot.add_trace(go.Histogram(x=df_filtered['category'], histfunc="count", nbinsx=50), row=1, col=1)
    fig_distplot.update_layout(showlegend=False,
                               template='plotly_dark',
                               plot_bgcolor='rgba(0, 0, 0, 0)',
                               paper_bgcolor='rgba(0, 0, 0, 0)', )
    # height=350)

    fig_distplot.update_yaxes(showgrid=False)

    return fig_distplot


@app.callback(
    Output('fig_master_clean_price_3d', 'figure'),
    Input('brand-dropdown', 'value'),
    Input('category-dropdown', 'value'),
    Input('model-dropdown', 'value'),
    Input('engine_size-slider', 'value'),
    Input('circulation_year-slider', 'value'),
    Input('price-slider', 'value'),
    Input('localisation-dropdown', 'value'))
def update_scatter_3d(brand, category, model, engine_size, circulation_year, price, localisation):
    df_filtered = df_clean_pro[boolean_mask(brand, category, model, engine_size, circulation_year, price, localisation)]
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


@app.callback(
    Output('datatable_ads', 'data'),
    Output('datatable_ads', 'columns'),
    Input('brand-dropdown', 'value'),
    Input('category-dropdown', 'value'),
    Input('model-dropdown', 'value'),
    Input('engine_size-slider', 'value'),
    Input('circulation_year-slider', 'value'),
    Input('price-slider', 'value'),
    Input('localisation-dropdown', 'value'),
    Input('datatable_ads', "page_current"),
    Input('datatable_ads', "page_size"))
def update_datatable_ads(brand, category, model, engine_size, circulation_year, price, localisation, page_current, page_size):
    df_filtered = df_clean_pro[boolean_mask(brand, category, model, engine_size, circulation_year, price, localisation)]
    columns = [{'id': x, 'name': x, 'presentation': 'markdown'} if x == 'url' else {'id': x, 'name': x} for x in
               df_filtered.columns]
    # return df_filtered.iloc[page_current * page_size:(page_current + 1) * page_size].to_dict('records'), [
    return df_filtered.to_dict('records'), columns


if __name__ == "__main__":
    app.run_server(debug=False, host="0.0.0.0", port=8080, use_reloader=True)
