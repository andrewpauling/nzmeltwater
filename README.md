nzmeltwater
==============================
[![License:MIT](https://img.shields.io/badge/License-MIT-lightgray.svg?style=flt-square)](https://opensource.org/licenses/MIT)


Code to reproduce results from Pauling et al., 2025 in GRL

To download the necessary data run the getdata.sh script from the command line. Note this will download a large (>50GB) quantity of data.
The script gets data from the CMIP6 archive and the Zenodo repository here: https://doi.org/10.5281/zenodo.14110477

To setup the conda environment run:
```
conda env create -f environment.yml
```
then, with the environment activated, run:
```
pip install -e .
```
This will install the user-created functions in the environment to allow them to be imported by the scripts. All plots in the paper and supporting information can be reproduced using the Jupyter notebooks in the notebooks directory.

--------

<p><small>Project based on the <a target="_blank" href="https://github.com/jbusecke/cookiecutter-science-project">cookiecutter science project template</a>.</small></p>
