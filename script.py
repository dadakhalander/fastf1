import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
import pandas as pd
import fastf1 as f1
import fastf1.plotting

# Enable FastF1 plotting
f1.plotting.setup_mpl(misc_mpl_mods=False)

# Initialize the Dash app
app = dash.Dash(__name__)

# Load available years and initial data
available_years = f1.get_event_schedule(2023)['EventDate'].dt.year.unique()[::-1]
initial_year = available_years[0]
races = f1.get_event_schedule(initial_year)
drivers = f1.get_driver_schedule(initial_year)

# Create the layout
app.layout = html.Div([
    html.H1("Formula 1 Race Analysis Dashboard", style={'textAlign': 'center'}),

    html.Div([
        html.H3("Filters"),
        dcc.Dropdown(
            id='year-dropdown',
            options=[{'label': str(year), 'value': year} for year in available_years],
            value=initial_year,
            placeholder="Select a Year"
        ),
        dcc.Dropdown(
            id='race-dropdown',
            placeholder="Select a Race"
        ),
        dcc.Dropdown(
            id='driver-dropdown',
            placeholder="Select a Driver"
        ),
    ], style={'padding': '20px'}),

    html.Div([
        html.Div([
            html.H3("Lap Times Analysis"),
            dcc.Graph(id='lap-times-graph')
        ], style={'width': '50%', 'display': 'inline-block'}),

        html.Div([
            html.H3("Speed Analysis"),
            dcc.Graph(id='speed-analysis-graph')
        ], style={'width': '50%', 'display': 'inline-block'}),

        html.Div([
            html.H3("Position Changes"),
            dcc.Graph(id='position-changes-graph')
        ], style={'width': '50%', 'display': 'inline-block'}),

        html.Div([
            html.H3("Tire Strategy"),
            dcc.Graph(id='tire-strategy-graph')
        ], style={'width': '50%', 'display': 'inline-block'})
    ])
])

# Update race dropdown when year changes
@app.callback(
    Output('race-dropdown', 'options'),
    Input('year-dropdown', 'value')
)
def update_race_options(year):
    schedule = f1.get_event_schedule(year)
    return [{'label': row['EventName'], 'value': row['EventName']} for _, row in schedule.iterrows()]

# Update driver dropdown when year changes
@app.callback(
    Output('driver-dropdown', 'options'),
    Input('year-dropdown', 'value')
)
def update_driver_options(year):
    session = f1.get_session(year, 1, 'R')
    session.load()
    drivers = session.laps['Driver'].unique()
    return [{'label': d, 'value': d} for d in drivers]

# Lap Times Graph
@app.callback(
    Output('lap-times-graph', 'figure'),
    [Input('year-dropdown', 'value'),
     Input('race-dropdown', 'value'),
     Input('driver-dropdown', 'value')]
)
def update_lap_times(year, race, driver):
    if not all([year, race, driver]):
        return go.Figure()

    try:
        session = f1.get_session(year, race, 'R')
        session.load()
        laps = session.laps.pick_driver(driver).reset_index()
        laps['LapTime(s)'] = laps['LapTime'].dt.total_seconds()

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=laps['LapNumber'],
            y=laps['LapTime(s)'],
            mode='lines+markers',
            name='Lap Time'
        ))
        fig.update_layout(title=f'Lap Times for {driver} in {race} {year}',
                          xaxis_title='Lap Number',
                          yaxis_title='Lap Time (s)')
        return fig
    except Exception as e:
        print(f"Lap time error: {e}")
        return go.Figure()

# Speed Graph
@app.callback(
    Output('speed-analysis-graph', 'figure'),
    [Input('year-dropdown', 'value'),
     Input('race-dropdown', 'value'),
     Input('driver-dropdown', 'value')]
)
def update_speed_analysis(year, race, driver):
    if not all([year, race, driver]):
        return go.Figure()

    try:
        session = f1.get_session(year, race, 'R')
        session.load()
        lap = session.laps.pick_driver(driver).pick_fastest()
        tel = lap.get_telemetry()

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=tel['Distance'],
            y=tel['Speed'],
            mode='lines',
            name='Speed'
        ))
        fig.update_layout(title=f'Speed Analysis - Fastest Lap for {driver}',
                          xaxis_title='Distance (m)',
                          yaxis_title='Speed (km/h)')
        return fig
    except Exception as e:
        print(f"Speed analysis error: {e}")
        return go.Figure()

# Position Graph
@app.callback(
    Output('position-changes-graph', 'figure'),
    [Input('year-dropdown', 'value'),
     Input('race-dropdown', 'value'),
     Input('driver-dropdown', 'value')]
)
def update_position_changes(year, race, driver):
    if not all([year, race, driver]):
        return go.Figure()

    try:
        session = f1.get_session(year, race, 'R')
        session.load()
        laps = session.laps.pick_driver(driver)

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=laps['LapNumber'],
            y=laps['Position'],
            mode='lines+markers',
            name='Position'
        ))
        fig.update_layout(title=f'Position Changes - {driver}',
                          xaxis_title='Lap Number',
                          yaxis_title='Position',
                          yaxis_autorange='reversed')
        return fig
    except Exception as e:
        print(f"Position change error: {e}")
        return go.Figure()

# Tire Strategy Graph
@app.callback(
    Output('tire-strategy-graph', 'figure'),
    [Input('year-dropdown', 'value'),
     Input('race-dropdown', 'value'),
     Input('driver-dropdown', 'value')]
)
def update_tire_strategy(year, race, driver):
    if not all([year, race, driver]):
        return go.Figure()

    try:
        session = f1.get_session(year, race, 'R')
        session.load()
        stints = session.laps.pick_driver(driver).reset_index()
        colors = {
            'SOFT': 'red', 'MEDIUM': 'yellow', 'HARD': 'white',
            'INTERMEDIATE': 'green', 'WET': 'blue'
        }

        fig = go.Figure()
        for compound in stints['Compound'].unique():
            stint_data = stints[stints['Compound'] == compound]
            fig.add_trace(go.Bar(
                x=[stint_data['LapNumber'].min()],
                y=[compound],
                width=[stint_data['LapNumber'].max() - stint_data['LapNumber'].min() + 1],
                orientation='h',
                name=compound,
                marker_color=colors.get(compound, 'gray')
            ))

        fig.update_layout(title=f'Tire Strategy - {driver}',
                          xaxis_title='Lap Number',
                          yaxis_title='Compound',
                          barmode='stack')
        return fig
    except Exception as e:
        print(f"Tire strategy error: {e}")
        return go.Figure()

if __name__ == '__main__':
    app.run_server(debug=True)

