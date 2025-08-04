# SWATPlusForCRIDA
 Scripts used to perform climate scenarios using Climate data from CORDEX and SWAT+ for implementation of CRIDA Framework.

## Get the data to test it
 Please find the download data .txt file on the data folder, there, you can download the entire folder with all the required data. Due to it's large size and the GitHub limits, they were not uploaded directly.

## Using anaconda to install the environment to run this scripts
1. **Install** [Anaconda](https://www.anaconda.com/products/distribution) or [Miniconda](https://docs.conda.io/en/latest/miniconda.html) if you haven't already.

2. **Create the environment** from the provided `.yml` file:

    ```bash
    conda env create -f swatcrida_env.yml
    ```

3. **Activate** the environment:

    ```bash
    conda activate swatcrida_env
    ```

4. *(Optional)* **Verify** the environment was created:

    ```bash
    conda env list
    ```
