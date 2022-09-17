import dash
from dash import dcc
from dash import html


app = dash.Dash(__name__,)
server = app.server

app.layout = html.Div([
    html.H1('Hello Dash!'),
    html.Div('hey hey hey')
    ])

if __name__ == "__main__":
    app.run_server(debug=True, host="0.0.0.0", port=8080, use_reloader=False)