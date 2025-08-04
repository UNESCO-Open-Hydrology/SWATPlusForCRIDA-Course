"""
This script is used to analyze the changes in mean monhly Q95 on for the KRB on Tambillo
"""

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

# os.chdir("..") # Changing to main SWATPlusForCRIDA

print(os.getcwd())

#Functions
def mean_doy(df):
    df["doy"]=df["date"].dt.dayofyear
    return df.groupby("doy").mean().reset_index()

def max_doy(df):
    df["doy"]=df["date"].dt.dayofyear
    return df.groupby("doy").max().reset_index() 

def min_doy(df):
    df["doy"]=df["date"].dt.dayofyear
    return df.groupby("doy").min().reset_index()  

def mean_monthly(df):
    df["month"] = df["date"].dt.month
    return df.groupby("month").mean(numeric_only=True).reset_index()

def min_monthly(df):
    df["month"] = df["date"].dt.month
    return df.groupby("month").min().reset_index()

def max_monthly(df):
    df["month"] = df["date"].dt.month
    return df.groupby("month").max().reset_index()

def ensemble(dict):
    dict = pd.concat(dict.values(), keys=dict.keys())
    ensemble = dict.groupby(level=1).mean(numeric_only=True)
    return ensemble

def ensembleMin(dict):
    dict = pd.concat(dict.values(), keys=dict.keys())
    ensemble = dict.groupby(level=1).min(numeric_only=True)
    return ensemble

def ensembleMax(dict):
    dict = pd.concat(dict.values(), keys=dict.keys())
    ensemble = dict.groupby(level=1).max(numeric_only=True)
    return ensemble


# Models and paths
model_list = ["SAM_44_RCA4_EC_EARTH",
              "SAM_44_RCA4_GFDL",
              "SAM_44_RCA4_HadGEM2",
              "SAM_44_RCA4_IPSL",
              "SAM_44_RCA4_MIROC5"]

scenarios = ["historical",
             "rcp45",
             "rcp85"]

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

chan_table = "channel_sd_mon.txt"  # Instead of mon it can be day
chan_nr = 47

chan_hist = {}
chan_future = {'rcp45': {}, 'rcp85': {}}  # Added rcp85

for combination in combinations:
    if "historical" in combination:
        dir = f"{models_folder}/{combination}"
        chan_hist[combination] = swat.swat_table(f"{dir}/{chan_table}").obj_output(chan_nr, "flo_out")
    for scen in ['rcp45', 'rcp85']:  # Added rcp85
        if scen in combination:
            dir = f"{models_folder}/{combination}"
            chan_future[scen][combination] = swat.swat_table(f"{dir}/{chan_table}").obj_output(chan_nr, "flo_out")

combined_hist = None
combined_future = {'rcp45': None, 'rcp85': None}  # Added rcp85

for combination, df in chan_hist.items():
    df = df.copy()
    df = df.rename(columns={"flo_out": combination})
    if combined_hist is None:
        combined_hist = df
    else:
        combined_hist = pd.merge(combined_hist, df, on="date", how="inner")

for scen in ['rcp45', 'rcp85']:  # Added rcp85
    for combination, df in chan_future[scen].items():
        df = df.copy()
        df = df.rename(columns={"flo_out": combination})
        if combined_future[scen] is None:
            combined_future[scen] = df
        else:
            combined_future[scen] = pd.merge(combined_future[scen], df, on="date", how="inner")

chan_hist_ens = {
    "mean": combined_hist.drop(columns="date").mean(axis=1),
    "max": combined_hist.drop(columns="date").max(axis=1),
    "min": combined_hist.drop(columns="date").min(axis=1)
}

chan_future_ens = {}
for scen in ['rcp45', 'rcp85']:  # Added rcp85
    chan_future_ens[scen] = {
        "mean": combined_future[scen].drop(columns="date").mean(axis=1),
        "max": combined_future[scen].drop(columns="date").max(axis=1),
        "min": combined_future[scen].drop(columns="date").min(axis=1)
    }

start_hist, end_hist = 1978, 2005
start_fut, end_fut = 2073, 2100
frequency = "monthly"  # or "daily"

mean_hist = chan_hist_ens["mean"].mean()
q95_hist = chan_hist_ens["mean"].quantile(0.95)
q05_hist = chan_hist_ens["mean"].quantile(0.05)

mean_fut = {}
q95_fut = {}
q05_fut = {}
for scen in ['rcp45', 'rcp85']:  # Added rcp85
    mean_fut[scen] = chan_future_ens[scen]["mean"].mean()
    q95_fut[scen] = chan_future_ens[scen]["mean"].quantile(0.95)
    q05_fut[scen] = chan_future_ens[scen]["mean"].quantile(0.05)

freq = "MS" if frequency == "monthly" else "D"
date_range_hist = pd.date_range(start=f"{start_hist}-01-01", end=f"{end_hist}-12-31", freq=freq)
date_range_fut = pd.date_range(start=f"{start_fut}-01-01", end=f"{end_fut}-12-31", freq=freq)

for key in chan_hist_ens:
    chan_hist_ens[key].index = date_range_hist

for scen in ['rcp45', 'rcp85']:  # Added rcp85
    for key in chan_future_ens[scen]:
        chan_future_ens[scen][key].index = date_range_fut

# Box plot to appreciate changes
whis = 2
data = [
    chan_hist_ens["mean"].values,
    chan_future_ens["rcp45"]["mean"].values,
    chan_future_ens["rcp85"]["mean"].values
]  # Added rcp85
labels = ["Historical", "RCP 4.5", "RCP 8.5"]  # Added rcp85

fig, ax = plt.subplots(figsize=(7, 5))
box = ax.boxplot(data, tick_labels=labels, patch_artist=True, widths=0.5, whis=whis,
                 medianprops=dict(color='black'))

colors = ['skyblue', 'sandybrown', 'salmon']  # Updated colors
for patch, color in zip(box['boxes'], colors):
    patch.set_facecolor(color)

ax.axhline(q95_hist, linestyle=":", color="blue", label=f"Historical Q95 = {q95_hist:.2f} (m³/s)")
ax.axhline(q95_fut['rcp45'], linestyle=":", color="sandybrown", label=f"RCP4.5 Q95 = {q95_fut['rcp45']:.2f} (m³/s)")
ax.axhline(q95_fut['rcp85'], linestyle=":", color="salmon", label=f"RCP8.5 Q95 = {q95_fut['rcp85']:.2f} (m³/s)")

ax.set_ylabel("Streamflow")
ax.set_title("Streamflow Distribution: Historical vs Future")
ax.legend()
plt.tight_layout()
plt.show()

# Q95 per model
q95_hist_models = combined_hist.drop(columns="date").quantile(0.95)
q95_fut_models = {}
for scen in ['rcp45', 'rcp85']:  # Added rcp85
    q95_fut_models[scen] = combined_future[scen].drop(columns="date").quantile(0.95)

q95_hist_models.index = q95_hist_models.index.str.replace("historical_", "", regex=False)
for scen in ['rcp45', 'rcp85']:  # Added rcp85
    q95_fut_models[scen].index = q95_fut_models[scen].index.str.replace(f"{scen}_", "", regex=False)
    q95_hist_models, q95_fut_models[scen] = q95_hist_models.align(q95_fut_models[scen], join="inner")

models = q95_fut_models['rcp45'].index
y = np.arange(len(models))
height = 0.25  # Slightly thinner to fit all scenarios

fig, ax = plt.subplots(figsize=(8, len(models) * 0.5 + 2))

ax.barh(y - height, q95_hist_models.values, height, label='Historical Q95', color='skyblue',edgecolor='black')
ax.barh(y, q95_fut_models['rcp45'].values, height, label='RCP4.5 Q95', color='sandybrown',edgecolor='black')
ax.barh(y + height, q95_fut_models['rcp85'].values, height, label='RCP8.5 Q95', color='salmon',edgecolor='black')

ax.set_yticks(y)
ax.set_yticklabels(models)
ax.set_xlabel("Q95 Streamflow")
ax.set_title("Q95 Comparison by Model: Historical vs Future")
ax.legend()
plt.tight_layout()
plt.show()

threshold = 18

hist_df = combined_hist.drop(columns="date", errors="ignore")
fut_df = {}
for scen in ['rcp45', 'rcp85']:  # Added rcp85
    fut_df[scen] = combined_future[scen].drop(columns="date", errors="ignore")

exceed_hist = (hist_df > threshold).sum()
exceed_fut = {}
for scen in ['rcp45', 'rcp85']:  # Added rcp85
    exceed_fut[scen] = (fut_df[scen] > threshold).sum()

exceed_hist.index = exceed_hist.index.str.replace("historical_", "", regex=False)
for scen in ['rcp45', 'rcp85']:  # Added rcp85
    exceed_fut[scen].index = exceed_fut[scen].index.str.replace(f"{scen}_", "", regex=False)
    exceed_hist, exceed_fut[scen] = exceed_hist.align(exceed_fut[scen], join="inner")

models = exceed_hist.index
y = np.arange(len(models))
height = 0.25

fig, ax = plt.subplots(figsize=(8, len(models) * 0.5 + 2))

ax.barh(y - height, exceed_hist.values, height, label='Historical', color='skyblue',edgecolor='black')
ax.barh(y, exceed_fut['rcp45'].values, height, label='RCP4.5', color='sandybrown',edgecolor='black')
ax.barh(y + height, exceed_fut['rcp85'].values, height, label='RCP8.5', color='salmon',edgecolor='black')

ax.set_yticks(y)
ax.set_yticklabels(models)
ax.set_xlabel("Number of Exceedances")
ax.set_title(f"Times Streamflow > {threshold} m³/s by Model")
ax.legend()
plt.tight_layout()
plt.show()


tep_hist = (combined_hist.drop(columns="date", errors="ignore") > threshold).mean()
tep_fut = {}
for scen in ['rcp45', 'rcp85']:  # Added rcp85
    tep_fut[scen] = (combined_future[scen].drop(columns="date", errors="ignore") > threshold).mean()

tep_hist.index = tep_hist.index.str.replace("historical_", "", regex=False)
for scen in ['rcp45', 'rcp85']:  # Added rcp85
    tep_fut[scen].index = tep_fut[scen].index.str.replace(f"{scen}_", "", regex=False)
    tep_hist, tep_fut[scen] = tep_hist.align(tep_fut[scen], join="inner")

models = tep_hist.index
y = np.arange(len(models))
height = 0.25

fig, ax = plt.subplots(figsize=(8, len(models) * 0.5 + 2))

ax.barh(y - height, tep_hist.values * 100, height, label='Historical', color='skyblue',edgecolor='black')
ax.barh(y, tep_fut['rcp45'].values * 100, height, label='RCP4.5', color='sandybrown',edgecolor='black')
ax.barh(y + height, tep_fut['rcp85'].values * 100, height, label='RCP8.5', color='salmon',edgecolor='black')  # Added rcp85

ax.set_yticks(y)
ax.set_yticklabels(models)
ax.set_xlabel("Probability of Exceedance (%)")
ax.set_title(f"Threshold Exceedance Probability per Model (>{threshold} m³/s)")
ax.legend(loc='upper right')
plt.tight_layout()
plt.show()



colors = plt.get_cmap("tab20").colors

hist_df = combined_hist.set_index("date") if "date" in combined_hist.columns else combined_hist.copy()
fut_df_year = {}
for scen in ['rcp45', 'rcp85']:  # Added rcp85
    fut_df_year[scen] = combined_future[scen].set_index("date") if "date" in combined_future[scen].columns else combined_future[scen].copy()

exceed_hist_per_year = (hist_df > threshold).groupby(hist_df.index.year).sum()
exceed_fut_per_year = {}
for scen in ['rcp45', 'rcp85']:  # Added rcp85
    exceed_fut_per_year[scen] = (fut_df_year[scen] > threshold).groupby(fut_df_year[scen].index.year).sum()

exceed_hist_per_year.columns = exceed_hist_per_year.columns.str.replace("historical_", "", regex=False)
for scen in ['rcp45', 'rcp85']:  # Added rcp85
    exceed_fut_per_year[scen].columns = exceed_fut_per_year[scen].columns.str.replace(f"{scen}_", "", regex=False)
    

def plot_exceedance_per_year(data, title):
    years = data.index.astype(int)
    models = data.columns
    n_models = len(models)
    x = years.values
    bar_width = 0.8 / n_models

    fig, ax = plt.subplots(figsize=(12, 4))
    colors = plt.get_cmap("tab20").colors  # Always use tab20 colors
    for i, model in enumerate(models):
        offset = (i - (n_models - 1) / 2) * bar_width
        ax.bar(x + offset - 0.5, data[model], width=bar_width, label=model, color=colors[i % len(colors)])
    ax.set_xticks(np.append(years.values, years.values[-1]))
    ax.set_xticklabels(np.append(years.values, years.values[-1]))
    ax.grid(True, axis='x', linestyle='--', alpha=0.6)
    ax.set_axisbelow(True)
    ax.yaxis.set_major_locator(mticker.MaxNLocator(integer=True))
    ax.set_ylabel("Number of Exceedances")
    ax.set_xlabel("Year")
    ax.set_title(title)
    ax.legend(title="Model", frameon=True)
    plt.tight_layout()
    plt.show()

plot_exceedance_per_year(exceed_hist_per_year, f"Annual Exceedances per Model (Historical)")
plot_exceedance_per_year(exceed_fut_per_year['rcp45'], f"Annual Exceedances per Model (RCP 4.5)")
plot_exceedance_per_year(exceed_fut_per_year['rcp85'], f"Annual Exceedances per Model (RCP 8.5)")