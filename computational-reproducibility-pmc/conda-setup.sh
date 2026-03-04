#!/bin/bash
set -e

echo '***************************Configuring conda-forge************************'
# Clean channels and set conda-forge
conda config --remove-key channels 2>/dev/null || true
conda config --add channels conda-forge
conda config --set channel_priority strict

# Required for conda activate inside script
source "$(conda info --base)/etc/profile.d/conda.sh"

echo '***************************lbzip2************************'
conda install -y lbzip2

########################################
# Python 3.10 — raw environment (minimal)
########################################
echo '***************************raw310************************'
conda create -n raw310 python=3.10 -y
conda activate raw310
pip install --upgrade pip
pip install nbdime pipenv nltk
pip install -e archaeology
conda deactivate

########################################
# Python 3.10 — full environment
########################################
echo '***************************py310************************'
conda create -n py310 python=3.10 -y
conda activate py310
conda install -y \
  alabaster appdirs astroid attrs \
  beautifulsoup4 bitarray blosc bokeh \
  colorama cycler cython defusedxml docutils et_xmlfile \
  filelock gevent glob2 \
  html5lib imageio imagesize isort \
  jeepney jupyter jupyter_console \
  keyring kiwisolver lxml matplotlib mccabe nltk numpydoc \
  openpyxl pathlib2 patsy pkginfo ply pyasn1 pyasn1-modules \
  pycodestyle pycosat pyflakes pylint \
  scikit-image scikit-learn seaborn \
  statsmodels sympy tqdm traitlets \
  unicodecsv xlrd xlsxwriter xlwt sortedcollections
pip install --upgrade pip
pip install nbdime pipenv nltk
pip install -e archaeology
python -c "import nltk; nltk.download('stopwords')"
conda deactivate

echo "All environments created successfully."
