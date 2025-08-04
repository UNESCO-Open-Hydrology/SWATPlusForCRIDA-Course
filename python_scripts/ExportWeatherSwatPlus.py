#%%
#==============================================================================================================
#   Python Script 
#   Export NETCDF and csv data in SWAT 2012 and SWAT+ format weather files
#   
#   Important: Be sure any spatial files have WGS84 projection (epsg:4326)
#   Make sure DEM and Data have the same extension

#   Jose Teran
#==============================================================================================================

#%%
#Import of libraries
import pandas as pd
import numpy as np
import xarray as xr
import rasterio
from itertools import product
import os
import re

#%%
#Function definition
def statElevDEM(nc_file,demfile,lat_label,lon_label):   # This function assigns elevation to stations if a DEM is provided - It estimates elevation for each centroid of the NC file

    '''
    nc_file : Path to the NETCDF file that will be used to produce weather data
    dmfile : Path to the TIF file of the DEM to get elevations
    lat_label : String indicating how latitude is specified in the NC file (e.g., lat, latitude, lats)
    lon_label : String indicating how longitude is specified in the NC file (e.g., lon, longitude, lons)

    '''
    ds = xr.open_dataset(nc_file)

    # Gettting grid locations
    lats = ds[lat_label].values
    lons = ds[lon_label].values

    coords = list(product(lons, lats))  # Create a grid of all lon/lat pairs

    
    with rasterio.open(demfile) as dem: # We open the DEM (tif) file
        
        elevations = list(dem.sample(coords)) # Sampling the DEM at the coordinates of the NC file
        centroid_ids = list(range(len(coords))) # Giving an ID to each centroid
        id_ints = np.arange(1,len(coords)+1)
        longs_sampled = [coord[0] for coord in coords]
        lats_sampled = [coord[1] for coord in coords]

        #Dataframe to store values
        df = pd.DataFrame({
            "ID"        : id_ints,
            "NAME"      : centroid_ids,
            "LAT"       : lats_sampled,
            "LONG"      : longs_sampled,
            "ELEVATION" : [e[0] for e in elevations]  # Flatten the elevations list
        })

    return df   # The result is a dataframe with each coordinate (station) and corresponding elevation

def statsListSwat(df,stat_prefix):    # This function gives a name to each station

    '''
    df : A dataframe containing the stations listed with their corresponding Lat, Long and elevation
    stat_prefix : A string giving a name prefix to the stations (e.g., statpcp, stattmp, stathmd)

    '''
    
    for i in range (0,len(df)):
        df.loc[i,"NAME"] = stat_prefix+str(i+1)
        
    return df   # It returns a dataframe with a name assigned to each station
        
def NCToSwat2012(df_list,nc_file:str,varname:str,save_path:str,startdate:str = "",enddate: str=""): # This function saves the weather data with the SWAT2012 format
    
    '''
    df_list     : A datafarme with each station ID number, Name, Lat, Long, and elevation
    nc_file     : Path to NC file that will be sampled for weather data
    varname     : The name of the variable specified on the NETCDF File (e.g., pr)
    save_path   : Path to SWAT weather folder where files will be saved
    startdate   : Format "yyyy-mm-dd" - Start date for creating weather files (optional)
    enddate     : Format "yyyy-mm-dd" - End date for creating weather files (optional)

    This function produces SWAT weather data with 2012 format as .txt files for each station

    It does not produce the pcp.txt, tmp.txt, etc., files - that can be done simply by exporting the df_list object to csv

    This function does not produce the Tmax Tmin weather files, for that one use NCToSwat2012Temp function

    '''

    #Creating the save path folder if it does not exists
    if not os.path.exists(save_path):
        os.makedirs(save_path)

    ds=xr.open_dataset(nc_file)
    
    for index,row in df_list.iterrows(): # For each station in the dataframe, the NC file is sampled and a value is assigned

        stat_name = row["NAME"]
        lat = row["LAT"]
        lon = row["LONG"]
        
        sample = ds.sel(latitude=lat,longitude=lon,method='nearest')
        
        if startdate != "" or enddate != "":
            sample = sample.sel(time=slice(startdate, enddate))
        
        df = sample.to_dataframe().reset_index(drop=True)
        df = df[[varname]]
        
        start_date_string = ds.time[0].values.astype(str)[0:10].replace("-", "")

        df[varname] = df[varname].apply(lambda x: f"{x:.2f}")
        
        df.loc[0,varname] = start_date_string
        
        
        df.to_csv(f"{save_path}/{stat_name}.txt", index = False, float_format = "%.2f",header=None)#Saving station timeseries in swat format
        
        print(f"File {save_path}/{stat_name}.txt successfully saved")
        

def NCToSwat2012Temp(df_list,nc_file_max:str,nc_file_min:str,varname_max:str,varname_min:str,save_path:str,startdate:str = "",enddate:str = ""):

    '''
    df_list     : A datafarme with each station ID number, Name, Lat, Long, and elevation
    nc_file_max : Path to NC file that will be sampled for weather data (Tmax)
    nc_file_min : Path to NC file that will be sampled for weather data (Tmin)
    varname_max : The name of the variable specified on the NETCDF File for Tmax (e.g., tasmax)
    varname_min : The name of the variable specified on the NETCDF File for Tmin (e.g., tasmin)
    save_path   : Path to SWAT weather folder where files will be saved
    startdate   : Format "yyyy-mm-dd" - Start date for creating weather files (optional)
    enddate     : Format "yyyy-mm-dd" - End date for creating weather files (optional)

    This function produces SWAT weather data with 2012 format as .txt files for each station

    It does not produce the pcp.txt, tmp.txt, etc., files - that can be done simply by exporting the df_list object to csv

    This function does not produce the Tmax Tmin weather files, for that one use NCToSwat2012Temp function

    '''
    
    #Creating the save path folder if it does not exists
    if not os.path.exists(save_path):
        os.makedirs(save_path)



    ds_max = xr.open_dataset(nc_file_max)
    ds_min = xr.open_dataset(nc_file_min)
    
    for index,row in df_list.iterrows():
        
        stat_name = row["NAME"]
        lat = row["LAT"]
        lon = row["LONG"]
        
        sample_max = ds_max.sel(lat=lat,lon=lon,method='nearest')
        sample_min = ds_min.sel(lat=lat,lon=lon,method='nearest')

        if startdate != "" or enddate != "":
            sample_max = sample_max.sel(time=slice(startdate, enddate))
            sample_min = sample_min.sel(time=slice(startdate, enddate))
        
        df_max = sample_max.to_dataframe().reset_index(drop=True)
        df_min = sample_min.to_dataframe().reset_index(drop=True)
        
        df_max[varname_max] = df_max[varname_max].apply(lambda x: f"{x:.2f}")
        df_min[varname_min] = df_min[varname_min].apply(lambda x: f"{x:.2f}")
        
        df_temp = pd.DataFrame(data={"tmax":df_max[varname_max],"tmin":df_min[varname_min]})
        
        start_date_string = ds_max.time[0].values.astype(str)[0:10].replace("-", "")

        
        with open(f"{save_path}/{stat_name}.txt", 'w') as f:
            f.write(start_date_string+"\n")
            df_temp.to_csv(f, index=False, header=None, float_format="%.2f",lineterminator='\n') 
            print(f"File {save_path}/{stat_name}.txt successfully saved")
        
        

def NCToSwatPlus(df_list,nc_file:str, weather_var:str,varname:str,
                 save_path:str,startdate:str = "",enddate: str="",
                 lat_label:str="lat",lon_label:str="lon",sample_by:str="coords"): # This function saves the weather data with the SWAT+ format
    
    '''
    df_list     : A datafarme with each station ID number, Name, Lat, Long, and elevation
    weather_var : The SWAT+ weather variable suffix : pcp,tmp,hmd,slr,etc.
    nc_file     : Path to NC file that will be sampled for weather data
    sample_by   : Chooes between "coords" (Default) if the data is gridded or "station" if the data is already referenced to stations 
    varname     : The name of the variable specified on the NETCDF File (e.g., pr)
    save_path   : Path to SWAT weather folder where files will be saved
    startdate   : Format "yyyy-mm-dd" - Start date for creating weather files (optional)
    enddate     : Format "yyyy-mm-dd" - End date for creating weather files (optional)

    This function produces SWAT weather data with 2012 format as .txt files for each station

    It does not produce the pcp.txt, tmp.txt, etc., files - that can be done simply by exporting the df_list object to csv

    This function does not produce the Tmax Tmin weather files, for that one use NCToSwat2012Temp function

    '''

    #Creating the save path folder if it does not exists
    if not os.path.exists(save_path):
        os.makedirs(save_path)

    ds=xr.open_dataset(nc_file)
    
    if lat_label != "lat":
        ds = ds.rename({lat_label: "lat"})
    
    if lat_label != "lon":
        ds = ds.rename({lon_label: "lon"})
    
    for index,row in df_list.iterrows(): # For each station in the dataframe, the NC file is sampled and a value is assigned

        stat_name = row["NAME"]
        lat = row["LAT"]
        lon = row["LONG"]
        elev = row["ELEVATION"]
        
        if sample_by=="coords":
            sample = ds.sel(lat=lat,lon=lon,method='nearest')
        
        if sample_by=="station":
            sample = ds.sel(station=stat_name)
        
        if startdate != "" or enddate != "":
            sample = sample.sel(time=slice(startdate, enddate))
        
        df = sample.to_dataframe().reset_index()    

        df["time"] = pd.to_datetime(df["time"])

        df[varname] = df[varname].apply(lambda x: f"{x:.2f}")

        nbyr = df["time"].dt.year.max() - df["time"].dt.year.min() + 1

        df["doy"]=df["time"].dt.dayofyear
        df["yr"]=df["time"].dt.year

        df=df[["yr","doy",varname]]

        with open(f"{save_path}/{stat_name}.{weather_var}", 'w') as f:
            f.write(f"{stat_name}: written by ExportWeatherSwatPlus.py - Jose Teran \n")
            f.write(f"nbyr\ttstep\tlat\tlon\telev \n")
            f.write(f"{nbyr}\t{0}\t{lat:.3f}\t{lon:.3f}\t{elev:.3f}\n")
            df.to_csv(f, index=False, header=None, sep="\t", float_format="%.2f",lineterminator='\n') 
        
        print(f"File {save_path}/{stat_name}.{weather_var} successfully saved")
    
def load_and_parse_csv(file):
    df = pd.read_csv(file)

    # Peek at the first date value
    sample_date = str(df["time"].iloc[0])

    # Basic regex to check if format is likely dd/mm/yyyy or dd-mm-yyyy
    if re.match(r'\d{2}[/-]\d{2}[/-]\d{4}', sample_date):
        df["time"] = pd.to_datetime(df["time"], dayfirst=True)
    else:
        df["time"] = pd.to_datetime(df["time"])

    return df

def CsvToSwatPlus(df_list,csv_path:str,weather_var:str,save_path:str): # This function saves the weather data with the SWAT+ format
    
    '''
    df_list     : A datafarme with each station ID number, Name, Lat, Long, and elevation
    csv_path    : Path to where the csv files are located - Files must have the same name as in the station list, the csv tables must have the columns "time" and "value"
    weather_var : The SWAT+ weather variable suffix : pcp,tmp,hmd,slr,etc.
    save_path   : Path to SWAT weather folder where files will be saved
    startdate   : Format "yyyy-mm-dd" - Start date for creating weather files (optional)
    enddate     : Format "yyyy-mm-dd" - End date for creating weather files (optional)

    This function produces SWAT weather data with 2012 format as .txt files for each station

    It does not produce the pcp.cli, tmp.cli, etc., files - that can be done simply by exporting the df_list object to csv

    This function does not produce the Tmax Tmin weather files, for that one use NCToSwat2012Temp function

    '''

    #Creating the save path folder if it does not exists
    if not os.path.exists(save_path):
        os.makedirs(save_path)

    csv_path_list = os.listdir(csv_path)
    
    c = 0
    
    for index,row in df_list.iterrows(): # For each station in the dataframe, the NC file is sampled and a value is assigned

        stat_name = row["NAME"]
        lat = row["LAT"]
        lon = row["LONG"]
        elev = row["ELEVATION"]

        file_path = f"{csv_path}/{csv_path_list[c]}"
        df = load_and_parse_csv(file_path)

        df["value"] = df["value"].apply(lambda x: f"{x:.2f}")

        nbyr = df["time"].dt.year.max() - df["time"].dt.year.min() + 1

        df["doy"]=df["time"].dt.dayofyear
        df["yr"]=df["time"].dt.year

        df=df[["yr","doy","value"]]

        with open(f"{save_path}/{stat_name}.{weather_var}", 'w') as f:
            f.write(f"{stat_name}: written by ExportWeatherSwatPlus.py - Jose Teran \n")
            f.write(f"nbyr\ttstep\tlat\tlon\telev \n")
            f.write(f"{nbyr}\t{0}\t{lat:.3f}\t{lon:.3f}\t{elev:.3f}\n")
            df.to_csv(f, index=False, header=None, sep="\t", float_format="%.2f",lineterminator='\n')
            
        
        c+=1 
        
        print(f"File {save_path}/{stat_name}.{weather_var} successfully saved")
        
        
def NCToSwatPlusTemp(df_list,nc_file_max:str,nc_file_min:str,varname_max:str,
                     varname_min:str,weather_var:str,save_path:str,startdate:str = "",enddate: str="",
                     lat_label:str="lat",lon_label:str="lon",sample_by:str="coords"): # This function saves the weather data with the SWAT+ format
    
    '''
    df_list     : A datafarme with each station ID number, Name, Lat, Long, and elevation
    weather_var : The SWAT+ weather variable suffix : pcp,tmp,hmd,slr,etc.
    nc_file_max : Path to NC file that will be sampled for weather data (Tmax)
    nc_file_min : Path to NC file that will be sampled for weather data (Tmin)
    sample_by   : Chooes between "coords" (Default) if the data is gridded or "station" if the data is already referenced to stations
    varname_max : The name of the variable specified on the NETCDF File for Tmax (e.g., tasmax)
    varname_min : The name of the variable specified on the NETCDF File for Tmin (e.g., tasmin)
    save_path   : Path to SWAT weather folder where files will be saved
    startdate   : Format "yyyy-mm-dd" - Start date for creating weather files (optional)
    enddate     : Format "yyyy-mm-dd" - End date for creating weather files (optional)

    This function produces SWAT weather data with 2012 format as .txt files for each station

    It does not produce the pcp.txt, tmp.txt, etc., files - that can be done simply by exporting the df_list object to csv

    This function does not produce the Tmax Tmin weather files, for that one use NCToSwat2012Temp function

    '''

    #Creating the save path folder if it does not exists
    if not os.path.exists(save_path):
        os.makedirs(save_path)

    ds_max = xr.open_dataset(nc_file_max)
    ds_min = xr.open_dataset(nc_file_min)
    
    
    if lat_label != "lat":
        ds_max = ds_max.rename({lat_label: "lat"})
        ds_min = ds_min.rename({lat_label: "lat"})
    
    if lat_label != "lon":
        ds_max = ds_max.rename({lon_label: "lon"})
        ds_min = ds_min.rename({lon_label: "lon"})
    
    for index,row in df_list.iterrows(): # For each station in the dataframe, the NC file is sampled and a value is assigned

        stat_name = row["NAME"]
        lat = row["LAT"]
        lon = row["LONG"]
        elev = row["ELEVATION"]

        if sample_by=="coords":
            sample_max = ds_max.sel(lat=lat,lon=lon,method='nearest')
            sample_min = ds_min.sel(lat=lat,lon=lon,method='nearest')
        
        if sample_by=="station":
            sample_max = ds_max.sel(station=stat_name)
            sample_min = ds_min.sel(station=stat_name)
            


        if startdate != "" or enddate != "":
            sample_max = sample_max.sel(time=slice(startdate, enddate))
            sample_min = sample_min.sel(time=slice(startdate, enddate))
        
        df_max = sample_max.to_dataframe().reset_index()
        df_min = sample_min.to_dataframe().reset_index()

        df_max["time"] = pd.to_datetime(df_max["time"])
        
        df_max[varname_max] = df_max[varname_max].apply(lambda x: f"{x:.2f}")
        df_min[varname_min] = df_min[varname_min].apply(lambda x: f"{x:.2f}")
        
        df_temp = pd.DataFrame(data={"time":df_max["time"],"tmin":df_min[varname_min],"tmax":df_max[varname_max]})

        nbyr = df_temp["time"].dt.year.max() - df_temp["time"].dt.year.min() + 1

        df_temp["doy"]=df_temp["time"].dt.dayofyear
        df_temp["yr"]=df_temp["time"].dt.year

        df=df_temp[["yr","doy","tmax","tmin"]]

        with open(f"{save_path}/{stat_name}.{weather_var}", 'w') as f:
            f.write(f"{stat_name}: written by ExportWeatherSwatPlus.py - Jose Teran \n")
            f.write(f"nbyr\ttstep\tlat\tlon\telev \n")
            f.write(f"{nbyr}\t{0}\t{lat:.3f}\t{lon:.3f}\t{elev:.3f}\n")
            df.to_csv(f, index=False, header=None, sep="\t", float_format="%.2f",lineterminator='\n') 
        
        print(f"File {save_path}/{stat_name}.{weather_var} successfully saved")
        

def CsvToSwatPlusTemp(df_list,csv_path:str,weather_var:str,save_path:str): # This function saves the weather data with the SWAT+ format
    
    '''
    df_list     : A datafarme with each station ID number, Name, Lat, Long, and elevation
    csv_path    : Path to where the csv files are located - Files must have the same name as in the station list, the csv tables must have the columns "time","tmax","tmin"
    weather_var : The SWAT+ weather variable suffix : pcp,tmp,hmd,slr,etc.
    save_path   : Path to SWAT weather folder where files will be saved
    startdate   : Format "yyyy-mm-dd" - Start date for creating weather files (optional)
    enddate     : Format "yyyy-mm-dd" - End date for creating weather files (optional)

    This function produces SWAT weather data with 2012 format as .txt files for each station

    It does not produce the pcp.cli, tmp.cli, etc., files - that can be done simply by exporting the df_list object to csv

    This function does not produce the Tmax Tmin weather files, for that one use NCToSwat2012Temp function

    '''

    #Creating the save path folder if it does not exists
    if not os.path.exists(save_path):
        os.makedirs(save_path)

    csv_path_list = os.listdir(csv_path)
    
    c = 0
    
    for index,row in df_list.iterrows(): # For each station in the dataframe, the NC file is sampled and a value is assigned

        stat_name = row["NAME"]
        lat = row["LAT"]
        lon = row["LONG"]
        elev = row["ELEVATION"]

        file_path = f"{csv_path}/{csv_path_list[c]}"
        df = load_and_parse_csv(file_path)

        df["tmax"] = df["tmax"].apply(lambda x: f"{x:.2f}")
        df["tmin"] = df["tmin"].apply(lambda x: f"{x:.2f}")

        nbyr = df["time"].dt.year.max() - df["time"].dt.year.min() + 1

        df["doy"]=df["time"].dt.dayofyear
        df["yr"]=df["time"].dt.year

        df=df[["yr","doy","tmax","tmin"]]

        with open(f"{save_path}/{stat_name}.{weather_var}", 'w') as f:
            f.write(f"{stat_name}: written by ExportWeatherSwatPlus.py - Jose Teran \n")
            f.write(f"nbyr\ttstep\tlat\tlon\telev \n")
            f.write(f"{nbyr}\t{0}\t{lat:.3f}\t{lon:.3f}\t{elev:.3f}\n")
            df.to_csv(f, index=False, header=None, sep="\t", float_format="%.2f",lineterminator='\n') 
        
        c+=1 
        print(f"File {save_path}/{stat_name}.{weather_var} successfully saved")
# %%
