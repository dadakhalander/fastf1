import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
import fastf1
import os
import sys
from pathlib import Path

# Ensure module path is correct
base_dir = os.path.dirname(Path(__file__).resolve())
if base_dir not in sys.path:
    sys.path.append(base_dir)

# Enable FastF1 plotting
fastf1.plotting.setup_mpl(misc_mpl_mods=False)

# Initialize the Dash app
app = dash.Dash(__name__)
server = app.server  # for deployment

# Load available years
available_years = list(range(2018, 2024))  # Or hardcoded if needed
initial_year = available_years[-1]
initial_races_df = fastf1.get_event_schedule(initial_year)
initial_race_name = initial_races_df['EventName'].iloc[0]

# Layout
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

# Callback: Race Dropdown Options
@app.callback(
    Output('race-dropdown', 'options'),
    Input('year-dropdown', 'value')
)
def update_race_options(year):
    try:
        races_df = fastf1.get_event_schedule(year)
        return [{'label': row['EventName'], 'value': row['EventName']} for _, row in races_df.iterrows()]
    except Exception as e:
        print(f"Race dropdown error: {e}")
        return []

# Callback: Driver Dropdown Options
@app.callback(
    Output('driver-dropdown', 'options'),
    [Input('year-dropdown', 'value'),
     Input('race-dropdown', 'value')]
)
def update_driver_options(year, race):
    try:
        races_df = fastf1.get_event_schedule(year)
        race_row = races_df[races_df['EventName'] == race].iloc[0]
        session = fastf1.get_session(year, race_row['RoundNumber'], 'R')
        session.load()
        drivers = session.laps['Driver'].unique()
        return [{'label': d, 'value': d} for d in drivers]
    except Exception as e:
        print(f"Driver dropdown error: {e}")
        return []

# Callback: Lap Times Graph
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
        races_df = fastf1.get_event_schedule(year)
        race_row = races_df[races_df['EventName'] == race].iloc[0]
        session = fastf1.get_session(year, race_row['RoundNumber'], 'R')
        session.load()

        driver_laps = session.laps.pick_driver(driver).reset_index()
        driver_laps['LapTime(s)'] = driver_laps['LapTime'].dt.total_seconds()

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=driver_laps['LapNumber'],
            y=driver_laps['LapTime(s)'],
            mode='lines+markers',
            name='Lap Times'
        ))
        fig.update_layout(
            title=f'Lap Times for {driver} - {race} {year}',
            xaxis_title='Lap Number',
            yaxis_title='Lap Time (seconds)'
        )
        return fig
    except Exception as e:
        print(f"Lap time error: {e}")
        return go.Figure()

# Callback: Speed Analysis Graph
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
        races_df = fastf1.get_event_schedule(year)
        race_row = races_df[races_df['EventName'] == race].iloc[0]
        session = fastf1.get_session(year, race_row['RoundNumber'], 'R')
        session.load()

        fastest_lap = session.laps.pick_driver(driver).pick_fastest()
        tel = fastest_lap.get_telemetry()

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=tel['Distance'],
            y=tel['Speed'],
            mode='lines',
            name='Speed'
        ))
        fig.update_layout(
            title=f'Speed Analysis - Fastest Lap for {driver}',
            xaxis_title='Distance (m)',
            yaxis_title='Speed (km/h)'
        )
        return fig
    except Exception as e:
        print(f"Speed analysis error: {e}")
        return go.Figure()

# Callback: Position Changes
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
        races_df = fastf1.get_event_schedule(year)
        race_row = races_df[races_df['EventName'] == race].iloc[0]
        session = fastf1.get_session(year, race_row['RoundNumber'], 'R')
        session.load()

        laps = session.laps.pick_driver(driver)

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=laps['LapNumber'],
            y=laps['Position'],
            mode='lines+markers',
            name='Position'
        ))
        fig.update_layout(
            title=f'Position Changes for {driver} - {race} {year}',
            xaxis_title='Lap Number',
            yaxis_title='Position',
            yaxis_autorange='reversed'
        )
        return fig
    except Exception as e:
        print(f"Position change error: {e}")
        return go.Figure()

# Callback: Tire Strategy
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
        races_df = fastf1.get_event_schedule(year)
        race_row = races_df[races_df['EventName'] == race].iloc[0]
        session = fastf1.get_session(year, race_row['RoundNumber'], 'R')
        session.load()

        laps = session.laps.pick_driver(driver).reset_index()
        fig = go.Figure()

        compound_colors = {
            'SOFT': 'red',
            'MEDIUM': 'yellow',
            'HARD': 'white',
            'INTERMEDIATE': 'green',
            'WET': 'blue'
        }

        for compound in laps['Compound'].dropna().unique():
            stint = laps[laps['Compound'] == compound]
            fig.add_trace(go.Bar(
                x=[stint['LapNumber'].min()],
                width=[stint['LapNumber'].max() - stint['LapNumber'].min() + 1],
                y=[compound],
                orientation='h',
                name=compound,
                marker_color=compound_colors.get(compound, 'gray')
            ))

        fig.update_layout(
            title=f'Tire Strategy for {driver} - {race} {year}',
            xaxis_title='Lap Number',
            yaxis_title='Compound',
            barmode='stack'
        )
        return fig
    except Exception as e:
        print(f"Tire strategy error: {e}")
        return go.Figure()

if __name__ == '__main__':
    app.run_server(debug=True)
