from dash import Dash, html, dcc, callback, Output, Input, dash_table
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from tessa import price_history, search

index, _ = price_history("^FTSE")
stock, _ = price_history("AZN")


print(stock)

###
# DASH APP
###

# Define the app
# / With title
appTitle = 'Share price performance against index'
app = Dash(appTitle)

# Define the layout for the Dash app
app.layout = html.Div([

    html.H1(children=appTitle, style={'textAlign':'center'}),

])

# if __name__ == '__main__':
#     app.run(debug=True)