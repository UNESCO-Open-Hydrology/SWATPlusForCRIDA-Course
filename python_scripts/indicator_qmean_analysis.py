# Imports
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
import math
from scipy import stats
import geopandas as gpd
import read_swat as swat
from matplotlib.patches import Patch
import matplotlib.ticker as mticker

print(os.getcwd())

# Functions
def mean_monthly(df):
    df["month"] = df["date"].dt.month
    return df.groupby("month").mean(numeric_only=True).reset_index()

# Models and paths
model_list = ["SAM_44_RCA4_EC_EARTH",
              "SAM_44_RCA4_GFDL",
              "SAM_44_RCA4_HadGEM2",
              "SAM_44_RCA4_IPSL",
              "SAM_44_RCA4_MIROC5"]

scenarios = ["historical", "rcp45", "rcp85"]

models_folder = "data/CaseStudy/Models/katari-swat-crida-spt/scenarios/Toolbox"

model_dirs = []
combinations = []

for model in model_list:
    for scenario in scenarios:
        model_dirs.append(f"{models_folder}/{scenario}_{model}")

for model in model_list:
    for scenario in scenarios:
        combinations.append(f"{scenario}_{model}")

plt.style.use('default')
plt.rcParams['font.family'] = 'Arial'  # Set font globally

chan_table = "channel_sd_mon.txt"
chan_nr = 47

chan_hist = {}
chan_future = {'rcp45': {}, 'rcp85': {}}

for combination in combinations:
    if "historical" in combination:
        dir = f"{models_folder}/{combination}"
        chan_hist[combination] = swat.swat_table(f"{dir}/{chan_table}").obj_output(chan_nr, "flo_out")
    for scen in ['rcp45', 'rcp85']:
        if scen in combination:
            dir = f"{models_folder}/{combination}"
            chan_future[scen][combination] = swat.swat_table(f"{dir}/{chan_table}").obj_output(chan_nr, "flo_out")

# Compute mean monthly per model
wet_months = [11, 12, 1, 2, 3]
dry_months = [5, 6, 7, 8, 9]

mean_streamflow = {}

# Historical
mean_streamflow['historical'] = {'wet': {}, 'dry': {}}
for combination, df in chan_hist.items():
    model = combination.split('_', 1)[1]
    df = df.copy()
    df = df.rename(columns={"flo_out": model})  # Add this line
    df['month'] = df['date'].dt.month
    wet_mean = df[df['month'].isin(wet_months)][model].mean()
    dry_mean = df[df['month'].isin(dry_months)][model].mean()
    mean_streamflow['historical']['wet'][model] = wet_mean
    mean_streamflow['historical']['dry'][model] = dry_mean

# Future scenarios
for scen in ['rcp45', 'rcp85']:
    mean_streamflow[scen] = {'wet': {}, 'dry': {}}
    for combination, df in chan_future[scen].items():
        model = combination.split('_', 1)[1]
        df = df.copy()
        df = df.rename(columns={"flo_out": model})  # Add this line
        df['month'] = df['date'].dt.month
        wet_mean = df[df['month'].isin(wet_months)][model].mean()
        dry_mean = df[df['month'].isin(dry_months)][model].mean()
        mean_streamflow[scen]['wet'][model] = wet_mean
        mean_streamflow[scen]['dry'][model] = dry_mean

# Plotting function
def plot_mean_streamflow(data, season,labellist):
    models = model_list
    y_pos = np.arange(len(models))
    bar_width = 0.25

    fig, ax = plt.subplots(figsize=(10, 6))
    colors = ['skyblue', 'sandybrown', 'salmon']
    for idx, scen in enumerate(scenarios):
        scenario_values = []
        for model in models:
            if model in data[scen][season]:
                scenario_values.append(data[scen][season][model])
            else:
                scenario_values.append(np.nan)
        ax.barh(y_pos + idx * bar_width, scenario_values, height=bar_width,
                label=labellist[idx], color=colors[idx], edgecolor='black')

    ax.set_yticks(y_pos + bar_width)
    ax.set_yticklabels(models)
    ax.set_xlabel("Mean Streamflow (m³/s)")
    ax.set_title(f"Mean Streamflow per Model - {season.capitalize()} Season")
    ax.legend()
    ax.xaxis.set_major_locator(mticker.MaxNLocator(integer=True))
    plt.tight_layout()
    plt.show()

# Plot wet season
labels = ['Historical','RCP 4.5','RCP 8.5']
plot_mean_streamflow(mean_streamflow, 'wet',labels)

# Plot dry season
plot_mean_streamflow(mean_streamflow, 'dry',labels)