#%%
#==============================================================================================================
#   Python Script 
#   
#   This script has multiple functions to:
#       - Read SWAT outputs as timeseries
#       - Read SWAT outputs referenced to objects to create maps
#       - Read and write model files
#       - Create new decision tables
#
#   Jose Teran
#==============================================================================================================


#%%
#Import libraries
import pandas as pd
import numpy as np
import geopandas as gpd
import dask.dataframe as dd

#%% Objects and functions
def get_period(df,start_date,end_date): # Filter period from output (geo)dataframe
    
    df_p = df.loc[df["date"].between(start_date, end_date)] 
    
    return df_p

class swat_table(): #This is a table object inteded to analyse output as time series (e.g. Streamflow)

    def __init__(self,path:str):
        '''
        path : Path to the txt SWAT+ output file (e.g., hru_wb_yr.txt)
        '''
        self.path = path
        
        with open(self.path,"r") as file:   # Here we are looking for the row with variable names in txt file
            for current_line_number,line in enumerate(file,start=1):
                if current_line_number==2:
                    header_line=line.strip()
                    break
    
        self.vars=header_line.split()

        file.close()

        df=dd.read_csv(path,
                skiprows=3,
                sep="\s+",
                header=None)
        
        # df=df.compute()       Better to compute it later when an object is specified in obj_output method
        
        df.columns=self.vars

        self.dframe=df  # This is a dask dataframe yet
    
    
    def obj_output(self,gis_id:int,var:str):    # Here we are specifying an object (e.g. HRU number 10) and getting the data from it
        '''
        gis_id : Object number (e.g, HRU number 1 --> gis_id = 1)
        var : SWAT+ output variable name (e.g., surq_gen)
        '''
        df=self.dframe[self.dframe["gis_id"]==gis_id].reset_index(drop=True).compute()
        dates=pd.to_datetime(dict(year=df.yr, month=df.mon, day=df.day))
        df["date"]=dates
        
        return df[["date",var]]
    

class swat_ModelFile(): #This is a table object intended to read model files (e.g. Hydrology.res)

    def __init__(self,path:str):
        '''
        path : Path to the txt SWAT+ output file (e.g., hru_wb_yr.txt)
        '''
        self.path = path
        
        with open(self.path,"r") as file:   # Here we are looking for the row with variable names in txt file
            for current_line_number,line in enumerate(file,start=1):
                if current_line_number==2:
                    header_line=line.strip()
                    break
    
        self.vars=header_line.split()

        file.close()

        df=dd.read_csv(path,
                skiprows=2,
                sep="\s+",
                header=None)
        
        # df=df.compute()       Better to compute it later when an object is specified in obj_output method
        
        df.columns=self.vars

        self.dframe=df.compute()  # This is a dask dataframe yet
    
    def write(self,name:str,overwrite = True ,write_path = "Null"):

        if overwrite == True:
            write_path = self.path
        else:
            write_path = write_path
            
        # with open(write_path,"w") as file:
        #     file.write("hydrology.res: written by read_swat - Jose Teran for SWAT+ rev.61.0.1"+"\n")
        #     self.dframe.to_csv(file, index=False, sep="\t\t\t", float_format="%.2f",lineterminator='\n')
        with open(write_path, "w") as file:
            file.write(f"{name}: written by read_swat - Jose Teran for SWAT+ rev.61.0.1" + "\n")
            file.write(self.dframe.to_string(index=False, float_format="%.4f",justify="left",col_space=10))
            print(f"{write_path} was written") 

class swat_map():   # This is a "map" object - it is an instance that has a shapefile (geodataframe) associated with an output table (e.g., HRUs shape with hru_wb_aa table)

    def __init__(self,shp_path:str,table:swat_table):
        '''
        shp_path : String or pathlike object for shapefile of SWAT+ objects
        tabel : Instance of swat_table class that corresponds to SWAT+ objects
        '''

        df_table=table.dframe.compute()

        self.shp_path=shp_path

        gdf=gpd.read_file(shp_path)
        ids=np.arange(1,len(gdf)+1)

        gdf["unit"]=ids
        geoms=gdf[["unit","geometry"]]
        
        dframe=pd.merge(df_table,geoms,on="unit",how="left")    #By this we assign a geometry to each row of the table that corresponds with the unit (HRU or LUS basically)
        dates=pd.to_datetime(dict(year=dframe.yr, month=dframe.mon, day=dframe.day))
        dframe["date"]=dates

        self.gdframe=gpd.GeoDataFrame(data=dframe,geometry=dframe["geometry"]) #This is the resulting geodataframe containing all data


def merge_data(obs_df, sim_df):
    """ Merge observed and simulated data on 'date' and drop NaN values in observed flow. """
    merged = pd.merge(obs_df, sim_df, on="date", suffixes=("_obs", "_sim"))
    return merged.dropna(subset=["flow_obs"])

def nse(obs_df, sim_df):
    """ Calculate Nash-Sutcliffe Efficiency (NSE). """
    merged = merge_data(obs_df, sim_df)
    obs, sim = merged["flow_obs"], merged["flow_sim"]
    return 1 - (np.sum((obs - sim) ** 2) / np.sum((obs - obs.mean()) ** 2))

# def log_nse(obs_df, sim_df):
#     """ Calculate log-transformed Nash-Sutcliffe Efficiency (logNSE). """
#     merged = merge_data(obs_df, sim_df)
#     obs, sim = np.log(merged["flow_obs"]), np.log(merged["flow_sim"])
#     return 1 - (np.sum((obs - sim) ** 2) / np.sum((obs - obs.mean()) ** 2))

def pbias(obs_df, sim_df):
    """ Calculate Percent Bias (PBIAS). """
    merged = merge_data(obs_df, sim_df)
    obs, sim = merged["flow_obs"], merged["flow_sim"]
    return 100 * (np.sum(sim - obs) / np.sum(obs))

def mse(obs_df, sim_df):
    """ Calculate Mean Squared Error (MSE). """
    merged = merge_data(obs_df, sim_df)
    obs, sim = merged["flow_obs"], merged["flow_sim"]
    return np.mean((obs - sim) ** 2)

def rmse(obs_df, sim_df):
    """ Calculate Root Mean Squared Error (RMSE). """
    return np.sqrt(mse(obs_df, sim_df))

def kge(obs_df, sim_df):
    """ Calculate Kling-Gupta Efficiency (KGE). """
    merged = merge_data(obs_df, sim_df)
    obs, sim = merged["flow_obs"], merged["flow_sim"]
    
    r = np.corrcoef(obs, sim)[0, 1]  # Correlation coefficient
    alpha = np.std(sim) / np.std(obs)  # Variability ratio
    beta = np.mean(sim) / np.mean(obs)  # Bias ratio

    return 1 - np.sqrt((r - 1) ** 2 + (alpha - 1) ** 2 + (beta - 1) ** 2)

class flow_stats():
    
    def __init__(self,obs_df,sim_df):
        self.nse = nse(obs_df,sim_df)
        # self.lognse = log_nse(obs_df,sim_df)
        self.pbias = pbias(obs_df,sim_df)
        self.rmse = rmse(obs_df,sim_df)
        self.mse = mse(obs_df,sim_df)
        self.kge = kge(obs_df,sim_df)
        
    

class swat_Dtl(): #This is a decision table file

    def __init__(self,path:str):
        '''
        path : Path to the txt SWAT+ output file (e.g., res_rel.dtl)
        '''
        self.path = path
        
        # Look for number of decision tables currently
        with open(self.path,"r") as file:   # Here we are looking for the row with variable names in txt file
            for current_line_number,line in enumerate(file,start=1):
                if current_line_number==2:
                    self.dtl_number=int(line.strip()[0]) # Number of decision tables currently
                    break
        file.close()
        
        with open(self.path, "r") as file:   
            lines = file.readlines()  # Read all lines into a list
                    
        file.close()
        
        self.lines = lines # Saving lines from first read
        
    def add_dtl(self,name:str,conds:int,alts:int,acts:int,cond_table,action_table,overwrite=False,write_path="null"):
        '''
        name: A string type (max 15 chars) for the table
        conds: Number of conditions
        alts: Number of alternatives
        acts: Number of actions
        cond_table: Dataframe with var,obj,obj_num,lim_var,lim_op,lim_const,alts for each condition
        action_table: Dataframe with act_typ,obj,obj_num,name,option,const,const2,fp,outcome
        
        '''
        # Reading file and adding new text line
        if overwrite == True:
            write_path = self.path
        else:
            write_path = write_path
            if write_path == "null":
                raise Exception("No file name provided, either change overwrite to True, or provide a write_path name")
                    
        # Adding a new line with the name, condition, alts and actions
        new_lines = self.lines
        new_lines.append(f"name\t\t\tconds\t\t\talts\t\t\tacts  \n")
        new_lines.append(f"{name}\t\t\t{conds}\t\t\t{alts}\t\t\t{acts}  \n")
        
        # Adding conditions and alternatives
        var_header = "var\t\tobj\t\tobj_num\t\tlim_var\t\tlim_op\t\tlim_const\t\t"
        
        alt_string = []
        for i in range(1,alts+1):
            alt_string.append(f"alt{i}")
            
        alt_string = "      ".join(alt_string)
        var_header = var_header+alt_string+"\n"
        new_lines.append(var_header)
        
        for index, row in cond_table.iterrows():
            formatted_row = [f"{x:.5f}" if isinstance(x, float) else str(x) for x in row]
            new_lines.append("\t\t\t\t".join(formatted_row) + "\n")
        
        # Adding actions
        act_header = "act_typ\t\tobj\t\tobj_num\t\tname\t\toption\t\tconst\t\tconst2\t\tfp\t\toutcome \n"
        
        new_lines.append(act_header)
        
        for index, row in action_table.iterrows():
            formatted_row = [f"{x:.5f}" if isinstance(x, float) else str(x) for x in row]
            new_lines.append("\t\t\t\t".join(formatted_row) + "\n")
        
        # Updating decision table number
        self.dtl_number+=1
        
        new_lines[1] = f"{self.dtl_number} \n"
        new_lines.append("\n")
        self.lines = new_lines
         

        
        with open(write_path, "w") as file:
            file.writelines(self.lines)
        
            
        