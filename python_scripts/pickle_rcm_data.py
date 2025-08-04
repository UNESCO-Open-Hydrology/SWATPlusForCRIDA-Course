import os
import xarray as xr
import pickle

# Define the root directory where all scenario folders are located
root_dir = r"D:\VUB-PHD\First_year\Katari_2024\RCM_data"
scenarios = ["historical", "rcp45", "rcp85"]
variables = ["pr", "tasmin", "tasmax"]

for scenario in scenarios:
    print(f"\n🔄 Processing scenario: {scenario}")
    scenario_path = os.path.join(root_dir, scenario)
    if not os.path.isdir(scenario_path):
        print(f"⚠️  Skipping: {scenario_path} not found.")
        continue

    scenario_dict = {}

    for model_name in os.listdir(scenario_path):
        model_path = os.path.join(scenario_path, model_name)
        if not os.path.isdir(model_path):
            continue

        print(f"  📁 Model: {model_name}")
        variable_dict = {}

        for var in variables:
            # Collect NetCDF files for this variable
            nc_files = sorted([
                os.path.join(model_path, f)
                for f in os.listdir(model_path)
                if f.startswith(var) and f.endswith(".nc")
            ])

            if not nc_files:
                print(f"    ⚠️  No files found for variable: {var}")
                continue

            try:
                ds = xr.open_mfdataset(nc_files, combine="by_coords", parallel=True)
                variable_dict[var] = ds
                print(f"    ✅ Loaded: {var} ({len(nc_files)} files)")
            except Exception as e:
                print(f"    ❌ Error loading {var}: {e}")

        scenario_dict[model_name] = variable_dict

    # Save to pickle
    output_pickle = f"{scenario}.pkl"
    with open(output_pickle, "wb") as f:
        pickle.dump(scenario_dict, f)
    print(f"💾 Saved: {output_pickle}")
