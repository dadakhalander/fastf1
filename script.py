import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import fastf1
import module.fastf1 as f1

import sys
from pathlib import Path
import os

base_dir = os.path.dirname(Path(__file__).resolve())
if base_dir not in sys.path:
    sys.path.append(base_dir)
import module.fastf1 as f1

# Enable FastF1 plotting
fastf1.plotting.setup_mpl(misc_mpl_mods=False)

# Initialize the Dash app
app = dash.Dash(__name__)

# Load available years and initial data
available_years = f1.available_years()
initial_year = available_years[0]
races = f1.season_races_df(initial_year)
drivers = f1.season_drivers_df(initial_year)

# Create the layout
app.layout = html.Div([
    html.H1("Formula 1 Race Analysis Dashboard", style={'textAlign': 'center'}),
    
    # Filters section
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
            options=[{'label': race, 'value': race} for race in races['EventName'].values],
            value=races['EventName'].values[0],
            placeholder="Select a Race"
        ),
        dcc.Dropdown(
            id='driver-dropdown',
            options=[{'label': driver, 'value': driver} for driver in drivers['Abbreviation'].values],
            value=drivers['Abbreviation'].values[0],
            placeholder="Select a Driver"
        ),
    ], style={'padding': '20px'}),
    
    # Graphs section
    html.Div([
        # Lap Times Graph
        html.Div([
            html.H3("Lap Times Analysis"),
            dcc.Graph(id='lap-times-graph')
        ], style={'width': '50%', 'display': 'inline-block'}),
        
        # Speed Analysis
        html.Div([
            html.H3("Speed Analysis"),
            dcc.Graph(id='speed-analysis-graph')
        ], style={'width': '50%', 'display': 'inline-block'}),
        
        # Position Changes
        html.Div([
            html.H3("Position Changes"),
            dcc.Graph(id='position-changes-graph')
        ], style={'width': '50%', 'display': 'inline-block'}),
        
        # Tire Strategy
        html.Div([
            html.H3("Tire Strategy"),
            dcc.Graph(id='tire-strategy-graph')
        ], style={'width': '50%', 'display': 'inline-block'})
    ])
])

# Callback to update race dropdown based on year selection
@app.callback(
    Output('race-dropdown', 'options'),
    [Input('year-dropdown', 'value')]
)
def update_race_options(year):
    races = f1.season_races_df(year)
    return [{'label': race, 'value': race} for race in races['EventName'].values]

# Callback to update driver dropdown based on year selection
@app.callback(
    Output('driver-dropdown', 'options'),
    [Input('year-dropdown', 'value')]
)
def update_driver_options(year):
    drivers = f1.season_drivers_df(year)
    return [{'label': driver, 'value': driver} for driver in drivers['Abbreviation'].values]

# Callback to update lap times graph
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
        races = f1.season_races_df(year)
        race_info = races[races['EventName'] == race].iloc[0]
        session = fastf1.get_session(year, race_info['RoundNumber'], 'R')
        session.load()
        
        driver_laps = session.laps.pick_driver(driver).reset_index()
        driver_laps['LapTime(s)'] = driver_laps['LapTime'].dt.total_seconds()
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=driver_laps['LapNumber'],
            y=driver_laps['LapTime(s)'],
            mode='lines+markers',
            name='Lap Times',
            hovertemplate='Lap %{x}<br>Time: %{y:.2f}s'
        ))
        
        fig.update_layout(
            title=f'Lap Times for {driver} - {race} {year}',
            xaxis_title='Lap Number',
            yaxis_title='Lap Time (seconds)',
            showlegend=True
        )
        
        return fig
    except Exception as e:
        print(f"Error updating lap times: {e}")
        return go.Figure()

# Callback to update speed analysis graph
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
        races = f1.season_races_df(year)
        race_info = races[races['EventName'] == race].iloc[0]
        session = fastf1.get_session(year, race_info['RoundNumber'], 'R')
        session.load()
        
        fastest_lap = session.laps.pick_driver(driver).pick_fastest()
        tel = fastest_lap.get_telemetry()
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=tel.index,
            y=tel['Speed'],
            mode='lines',
            name='Speed',
            hovertemplate='Distance: %{x:.0f}m<br>Speed: %{y:.0f}km/h'
        ))
        
        fig.update_layout(
            title=f'Speed Analysis - Fastest Lap for {driver}',
            xaxis_title='Distance (meters)',
            yaxis_title='Speed (km/h)',
            showlegend=True
        )
        
        return fig
    except Exception as e:
        print(f"Error updating speed analysis: {e}")
        return go.Figure()

# Callback to update position changes graph
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
        races = f1.season_races_df(year)
        race_info = races[races['EventName'] == race].iloc[0]
        session = fastf1.get_session(year, race_info['RoundNumber'], 'R')
        session.load()
        
        driver_laps = session.laps.pick_driver(driver)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=driver_laps['LapNumber'],
            y=driver_laps['Position'],
            mode='lines+markers',
            name='Position',
            hovertemplate='Lap %{x}<br>Position: %{y}'
        ))
        
        fig.update_layout(
            title=f'Position Changes for {driver} - {race} {year}',
            xaxis_title='Lap Number',
            yaxis_title='Position',
            yaxis_autorange='reversed',
            showlegend=True
        )
        
        return fig
    except Exception as e:
        print(f"Error updating position changes: {e}")
        return go.Figure()

# Callback to update tire strategy graph
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
        races = f1.season_races_df(year)
        race_info = races[races['EventName'] == race].iloc[0]
        session = fastf1.get_session(year, race_info['RoundNumber'], 'R')
        session.load()
        
        driver_stints = session.laps.pick_driver(driver).reset_index()
        
        fig = go.Figure()
        
        colors = {
            'SOFT': 'red',
            'MEDIUM': 'yellow',
            'HARD': 'white',
            'INTERMEDIATE': 'green',
            'WET': 'blue'
        }
        
        for compound in driver_stints['Compound'].unique():
            stint_data = driver_stints[driver_stints['Compound'] == compound]
            fig.add_trace(go.Bar(
                x=[stint_data['LapNumber'].min()],
                width=[stint_data['LapNumber'].max() - stint_data['LapNumber'].min() + 1],
                y=[compound],
                orientation='h',
                name=compound,
                marker_color=colors.get(compound, 'gray')
            ))
        
        fig.update_layout(
            title=f'Tire Strategy for {driver} - {race} {year}',
            xaxis_title='Lap Number',
            yaxis_title='Compound',
            showlegend=True,
            barmode='stack'
        )
        
        return fig
    except Exception as e:
        print(f"Error updating tire strategy: {e}")
        return go.Figure()

if __name__ == '__main__':
    app.run_server(debug=True)
