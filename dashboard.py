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
def data_for_stats_table():
    data = []
    for key, _ in statsAtHorizons['M1']['stats'].items():
        data.append({
            ' ': str(key),
            '1 Month': str(statsAtHorizons['M1']['stats'][key]),
            '3 Months': str(statsAtHorizons['M3']['stats'][key]),
            '6 Months': str(statsAtHorizons['M6']['stats'][key]),
        })
    return data

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

# Remove the rows where df['AZN/FTSE'] is NaN - dataset from the API seems incomplete
df = df.dropna()

# Column which calculates the rolling 3 months high of the relative performance
df['R3MH'] = df['AZN/FTSE'].rolling(MONTH*3).max() 

# Column identifying the dates when the rolling 3 months is touched by the relative performance
df['R3MHTouched'] = df['AZN/FTSE'] == df['R3MH']

# For compatibility with the previous code, convert the index to a column
df['Dates'] = df.index

# Create an independent list with only the signals - excluding the last 6 months of data (so we do not have signals with incomplete data)
signals = []
i = 0
while i < len(df) - MONTH*6:
    if df['R3MHTouched'].iloc[i] == True:
        signals.append(df['Dates'].iloc[i])
        i += MONTH*4
    else:
        i += 1

# Create a column in the dataframe which identifies the Signals
df['Signals'] = df['Dates'].isin(signals)

# Create a dataframe with the 6 months of data after each Signal
derivedDFs = {}
for date in signals:
    frame = df[df['Dates'] >= date].iloc[:MONTH*6]
    frame['PerformanceNormalised'] = normalise(frame['AZN/FTSE'])
    derivedDFs[date] = frame

# Create a dictionary with the statistics for each Signal
statsAtHorizons = {
    'M1': { 'data': [], 'stats': {}},
    'M3': { 'data': [], 'stats': {}},
    'M6': { 'data': [], 'stats': {}},
}
# / First get the relevant data
for date in signals:
    statsAtHorizons['M6']['data'].append(derivedDFs[date]['PerformanceNormalised'].iloc[-1])
    statsAtHorizons['M3']['data'].append(derivedDFs[date]['PerformanceNormalised'].iloc[MONTH*3-1])
    statsAtHorizons['M1']['data'].append(derivedDFs[date]['PerformanceNormalised'].iloc[MONTH-1])

# / Then calculate the statistics
for horizon, item in statsAtHorizons.items():
    statsAtHorizons[horizon]['stats'] = frame_stats(item['data'])


###
# DASH APP
###

# Define the app
# / With title
appTitle = 'AstraZeneca share price performance against FTSE 100'
app = Dash(appTitle)

# Define the layout for the Dash app
app.layout = html.Div([

    html.H1(children=appTitle, style={'textAlign':'center'}),

    # Graph for the main dataset
    html.H4(children='Graph 1: Relative performance of AZN/FTSE, 3 months rolling high, and dates where the rolling 3 month high is reached', style={'textAlign':'center'}),
    dcc.Graph(
        id='graph-rolling-3-month-high-and-dates',
        figure=px.line(df, x='Dates', y=['AZN/FTSE', 'R3MH'])
                    .add_scatter(
                        x=df[df['Signals'] == True]['Dates'], 
                        y=df[df['Signals'] == True]['AZN/FTSE'], 
                        mode='markers', 
                        marker=dict(size=12), 
                        name='Signals'
                    )
    ),

    html.H4(children=f'Number of Signals: {len(signals)}', style={'textAlign':'center'}),

    # Graph for the derived dataset - populated by the callback below
    html.H4(children='Graph 2: Normalised relative performance of AZN/FTSE after each Signal', style={'textAlign':'center'}),
    dcc.Graph(
        id='graph-post-signal-performance',        
    ),

    # Scatterplot for the distribution of relative performance after each Signal per horizon
    html.H4(children='Graph 3: Distribution of the normalised relative performance of AZN/FTSE after each Signal, by Horizon', style={'textAlign':'center'}),
    dcc.Graph(
        id='graph-distribution-relative-performance'
    ),

    # Table for the statistics per horizon
    html.H4(children='Table 1: Statistics of the normalised relative performance of AZN/FTSE after each Signal, by Horizon', style={'textAlign':'center'}),
    dash_table.DataTable(
        id='table-stats-relative-performance',
        columns=[{"name": i, "id": i} for i in [' ', '1 Month', '3 Months', '6 Months']],
        data=data_for_stats_table(),
        style_cell={'textAlign': 'center'},
        style_table={ 'table-layout': 'fixed' }
    ),
])

@callback(
    Output('graph-post-signal-performance', 'figure'),
    Input('graph-post-signal-performance', 'clickData')
)
def update_graph(clickData):
    traces = []

    for date in signals:
        x_data = derivedDFs[date].index - derivedDFs[date].index[0]
        x_data = [int(x.days) for x in x_data]
        y_data = derivedDFs[date]['PerformanceNormalised']

        trace = go.Scatter(
            x=x_data,
            y=y_data,
            name=date.strftime("%d-%m-%Y"),
            mode='lines',
        )
        traces.append(trace)

    figure = go.Figure(data=traces)

    figure.update_layout(
        xaxis_title='Days after Signal',
        yaxis_title='Normalised Relative Performance',
        xaxis_range=[0, MONTH*6-1],
    )
    figure.add_vline(x=MONTH-1, annotation_text='1 Month', line_width=1)
    figure.add_vline(x=MONTH*3-1, annotation_text='3 Months', line_width=1)
    figure.add_vline(x=MONTH*6-1, annotation_text='6 Months', line_width=1)

    return figure

@callback(
    Output('graph-distribution-relative-performance', 'figure'),
    Input('graph-distribution-relative-performance', 'clickData')
)
def update_graph(clickData):
    traces = []

    for horizon, _ in statsAtHorizons.items():
        trace = go.Box(
            y=statsAtHorizons[horizon]['data'],
            name=horizon,
            boxpoints='all',
            jitter=0.5,
            whiskerwidth=0.2,
            marker_size=5,
            line_width=1,
        )
        traces.append(trace)

    figure = go.Figure(data=traces)

    figure.update_layout(
        xaxis_title='Horizon',
        yaxis_title='Normalised Relative Performance',
    )

    return figure


if __name__ == '__main__':
    app.run(debug=True)