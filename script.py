import os
import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import fastf1 as ff1
from fastf1 import plotting, utils
from matplotlib.lines import Line2D
from matplotlib.collections import LineCollection

def setup_cache():
    cache_dir = "formula/cache"
    os.makedirs(cache_dir, exist_ok=True)
    ff1.Cache.enable_cache(cache_dir)

def get_race_data(year, event, session):
    race = ff1.get_session(year, event, session)
    race.load()
    return race

def plot_laptime(race, driver1, driver2):
    laps_d1 = race.laps.pick_driver(driver1)
    laps_d2 = race.laps.pick_driver(driver2)

    color1 = plotting.driver_color(driver1)
    color2 = plotting.driver_color(driver2)

    fig, ax = plt.subplots()
    ax.plot(laps_d1['LapNumber'], laps_d1['LapTime'], color=color1, label=driver1)
    ax.plot(laps_d2['LapNumber'], laps_d2['LapTime'], color=color2, label=driver2)
    ax.set_xlabel('Lap Number')
    ax.set_ylabel('Lap Time')
    ax.legend()
    plt.title(f"Lap Time Comparison - {race.event.year} {race.event.EventName} {race.name}")
    return fig

def main():
    st.title("F1 Telemetry Dashboard")
    setup_cache()

    year = st.number_input("Enter Year", min_value=2000, max_value=2024, value=2022)
    event = st.text_input("Enter Event Name", "Austria")
    session = st.selectbox("Select Session", ["FP1", "FP2", "FP3", "Q", "R"])

    if st.button("Load Race Data"):
        race = get_race_data(year, event, session)
        st.success(f"Loaded {year} {event} {session} session")

        driver1 = st.text_input("Enter First Driver Code", "VER")
        driver2 = st.text_input("Enter Second Driver Code", "HAM")
        
        if st.button("Plot Lap Time Comparison"):
            fig = plot_laptime(race, driver1, driver2)
            st.pyplot(fig)

if __name__ == "__main__":
    main()
