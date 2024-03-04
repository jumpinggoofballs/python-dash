from dash import Dash, html, dcc, callback, Output, Input, dash_table
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from tessa import price_history, SymbolCollection

###
# DEFINITIONS
###

# Definition of 1 month (in working days)
MONTH = 22          

###
# UTILITY FUNCTIONS
###

# Function to normalise a data series to 100
def normalise(list):
    return list / list.iloc[0] * 100

# Function to calculate the statistics of a data series
def frame_stats(source):
    
    frame = pd.DataFrame(source)

    # Sub-Function to calculate the range of a data series
    def range(list):
        return list.max() - list.min()

    # Sub-Function to calculate the mean absolute deviation of a data series
    def mad(list):
        return np.mean(np.abs(list - list.mean()))

    # Sub-Function to prettify the output numbers
    def prettify_stats(stat):
        return float(stat.iloc[0].round(2))
    
    return {
        'HitRatio': f'{(round(len(frame[frame > 100].dropna()) / len(source) * 100, 2))}%',
        'Minimum': prettify_stats(frame.min()),
        'Maximum': prettify_stats(frame.max()),
        'Mean': prettify_stats(frame.mean()),
        'Median': prettify_stats(frame.median()),
        'Range': prettify_stats(range(frame)),
        'Standard Deviation': prettify_stats(frame.std()),
        'Variance': prettify_stats(frame.var()),
        'Mean Absolute Deviation': mad(frame).round(2),
    }

# formatted data for the stats table 
# def data_for_stats_table():
#     data = []
#     for key, _ in statsAtHorizons['M1']['stats'].items():
#         data.append({
#             ' ': str(key),
#             '1 Month': str(statsAtHorizons['M1']['stats'][key]),
#             '3 Months': str(statsAtHorizons['M3']['stats'][key]),
#             '6 Months': str(statsAtHorizons['M6']['stats'][key]),
#         })
#     return data

###
# DATA
###

# Get FTSE 100 and AZN stock price data
df, _ = price_history("^FTSE")
df = df.set_index(df.index.date)

stock, _ = price_history("AZN")
stock = stock.set_index(stock.index.date)

# Merge the two dataframes
df['AZN'] = stock['close']

# Drop the last row of the dataframe (because it's today's data and it's incomplete)
df = df.drop(df.tail(1).index)

# Rename the columns
df.columns = ['FTSE', 'AZN']

# Calculate the relative performance of the stock against the index
df['AZN/FTSE'] = df['AZN'] / df['FTSE']

# Column which calculates the rolling 3 months high of the relative performance
# df['R3MH'] = df['AZN/FTSE'].rolling(MONTH*3).max() 

# Column identifying the dates when the rolling 3 months is touched by the relative performance
# df['R3MHTouched'] = df['AZN/FTSE'] == df['R3MH']

# Create an independent list with only the signals - for utility
# signals = []
# i = 0
# while i < len(df):
#     if df['R3MHTouched'][i] == True:
#         signals.append(df['Dates'].iloc[i])
#         i += MONTH*4
#     else:
#         i += 1


# print(signals)

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