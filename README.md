# SWATPlusForCRIDA
 Scripts used to perform climate scenarios using Climate data from CORDEX and SWAT+ for implementation of CRIDA Framework.


## Get the data to test it
 Please find the download data .txt file on the data folder, there, you can download the entire folder with all the required data. Due to it's large size and the GitHub limits, they were not uploaded directly.


## Install QGIS (>3.34) and SWAT+ Tools
 - Please follow the instructions on this link: https://swatplus.gitbook.io/docs/installation
 - Or the video tutorial: https://www.youtube.com/watch?v=2oBnX5MtJIg


## Using anaconda to install the environment to run this scripts

 a) **Install** [Anaconda](https://www.anaconda.com/products/distribution) or [Miniconda](https://docs.conda.io/en/latest/miniconda.html) if you haven't already.

 b) **Open the Anaconda Prompt** (on Windows) or a terminal (on macOS/Linux):


   1. **Create the environment** from the provided `.yml` file:
     
   
      ```bash
      conda env create -f swatcrida_env.yml
      ```
   
   2. **Activate** the environment:
   
      ```bash
      conda activate swatcrida_env
      ```
   
   3. *(Optional)* **Verify** the environment was created:
   
      ```bash
      conda env list
      ```

      
## Working with Jupyter Notebooks in VS Code

To run the notebooks in this project using the `swatcrida_env` environment, follow these steps:

### 1. Install Visual Studio Code

- Download and install [Visual Studio Code](https://code.visualstudio.com/).
- During installation, make sure to check the boxes:
  - **"Add to PATH"**
  - **"Install Code command in PATH"** (on macOS)

### 2. Install Python and Jupyter Extensions in VS Code

- Open VS Code.
- Go to the **Extensions** tab (left sidebar or `Ctrl+Shift+X`).
- Install the following extensions:
  - **Python**
  - **Jupyter**

### 3. Add the Conda Environment to Jupyter

In your Anaconda Prompt or terminal:
(You can skip this and VS Code will install it automatically if you try to run the notebook anyways)
```bash
conda activate swatcrida_env
conda install ipykernel
python -m ipykernel install --user --name=swatcrida_env
```

### 4. Open and Run Notebooks in VS Code

- Open a `.ipynb` notebook file in VS Code.
- In the top-right kernel dropdown, select **`swatcrida_env`**.
- Run cells using `Shift+Enter` or the ▶️ button.
