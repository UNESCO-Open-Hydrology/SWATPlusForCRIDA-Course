'''
This script is used to run the future scenarios using parallel processing
'''

# imports
import multiprocessing
import os, sys
import shutil
from genericpath import exists
import subprocess

# Functions

def runModel(swatDir: str, exePath: str) -> None:
    """
    Runs the SWAT+ model and writes output to a log file in the parent of swatDir.
    Compatible with multiprocessing on Windows.
    """
    swatDir = os.path.abspath(swatDir)
    exePath = os.path.abspath(exePath)
    

    print(f"Running model in: {swatDir} \n")

    if not exePath.endswith(".exe"):
        exePath += ".exe"

    # print(f"[DEBUG] Main script CWD: {os.getcwd()}")
    subprocess.run([exePath], cwd=swatDir)
        
# Models, experiments and paths
model_list=["SAM_44_RCA4_EC_EARTH",
            "SAM_44_RCA4_GFDL",
            "SAM_44_RCA4_HadGEM2",
            "SAM_44_RCA4_IPSL",
            "SAM_44_RCA4_MIROC5"]

experiment_list=["historical",
                 "rcp45",
                 "rcp85"]


models_folder = "data/CaseStudy/Models/katari-swat-crida-spt/scenarios/Toolbox"
exePath       = "data/swat_exe/rev61.0.1_64rel.exe"
process_nr    = 14

# Create list of model directories
swatDirs = []
for scenario in experiment_list:
    for model in model_list:
        swatDirs.append(f"{models_folder}/{scenario}_{model}")
         
# Running
# set default working directory to the script location
if __name__ == "__main__":
    exePath = os.path.abspath("data/swat_exe/rev61.0.1_64rel.exe")  # Ensure absolute path

    # Build job list
    jobs = [(os.path.abspath(sdir), exePath) for sdir in swatDirs]

    # Run models in parallel
    with multiprocessing.Pool(processes=process_nr) as pool:
        pool.starmap(runModel, jobs)


