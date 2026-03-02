#!/bin/bash
set -e

echo '***************************Configuring conda-forge************************'

conda config --remove-key channels 2>/dev/null || true
conda config --add channels conda-forge
conda config --set channel_priority strict

# Required for conda activate inside script
source "$(conda info --base)/etc/profile.d/conda.sh"

echo '***************************lbzip2************************'
conda install -y lbzip2

########################################
# Python 2.7
########################################

echo '***************************raw27************************'
conda create -n raw27 python=2.7 -y
conda activate raw27
pip install --upgrade pip
pip install nbdime ipywidgets==6.0.0 pipenv
pip install -e archaeology
conda deactivate

echo '***************************py27************************'
conda create -n py27 python=2.7 -y
conda activate py27
pip install --upgrade pip
pip install nbdime ipywidgets==6.0.0 pipenv
pip install -e archaeology
conda deactivate

########################################
# Python 3.4
########################################

echo '***************************raw34************************'
conda create -n raw34 python=3.4 -y
conda activate raw34
pip install --upgrade pip
pip install jupyter nbdime pipenv pathlib2
pip install -e archaeology
conda deactivate

echo '***************************py34************************'
conda create -n py34 python=3.4 -y
conda activate py34
pip install --upgrade pip
pip install nbdime pipenv
pip install -e archaeology
conda deactivate

########################################
# Python 3.5
########################################

echo '***************************raw35************************'
conda create -n raw35 python=3.5 -y
conda activate raw35
pip install --upgrade pip
pip install nbdime pipenv
pip install -e archaeology
conda deactivate

echo '***************************py35************************'
conda create -n py35 python=3.5 -y
conda activate py35
conda install -y appdirs atomicwrites keyring secretstorage tqdm jeepney automat constantly
pip install --upgrade pip
pip install nbdime pipenv
pip install -e archaeology
conda deactivate

########################################
# Python 3.6
########################################

echo '***************************raw36************************'
conda create -n raw36 python=3.6 -y
conda activate raw36
pip install --upgrade pip
pip install nbdime pipenv
pip install -e archaeology
conda deactivate

echo '***************************py36************************'
conda create -n py36 python=3.6 -y
conda activate py36
conda install -y anaconda-navigator jupyterlab_server navigator-updater
pip install --upgrade pip
pip install nbdime flake8-nb biopython pipenv
pip install -e archaeology
python -c "import nltk; nltk.download('stopwords')"
conda deactivate

########################################
# Python 3.7
########################################

echo '***************************raw37************************'
conda create -n raw37 python=3.7 -y
conda activate raw37
pip install --upgrade pip
pip install nbdime pipenv
pip install -e archaeology
conda deactivate

echo '***************************py37************************'
conda create -n py37 python=3.7 -y
conda activate py37
conda install -y \
  alabaster anaconda-client appdirs asn1crypto astroid astropy atomicwrites attrs automat \
  babel backports.shutil_get_terminal_size beautifulsoup4 bitarray blaze blosc bokeh boto bottleneck \
  cairo colorama constantly contextlib2 curl cycler cython defusedxml docutils et_xmlfile \
  fastcache filelock gevent glob2 gmpy2 graphite2 greenlet harfbuzz html5lib hyperlink \
  imageio imagesize incremental isort jdcal jeepney jupyter jupyter_console \
  keyring kiwisolver libxslt lxml matplotlib mccabe mpmath nltk nose numpydoc \
  openpyxl pango pathlib2 patsy pep8 pkginfo ply pyasn1 pyasn1-modules \
  pycodestyle pycosat pycurl pyflakes pylint pyodbc pywavelets \
  rope scikit-image scikit-learn seaborn service_identity singledispatch \
  spyder spyder-kernels statsmodels sympy tqdm traitlets twisted \
  unicodecsv xlrd xlsxwriter xlwt zope.interface sortedcollections typed-ast

pip install --upgrade pip
pip install nbdime pipenv
pip install -e archaeology
conda deactivate

########################################
# Modern Python versions
########################################

for PY in 3.8 3.9 3.10
do
  SHORT=$(echo $PY | tr -d '.')
  
  echo "***************************raw${SHORT}************************"
  conda create -n raw${SHORT} python=${PY} -y
  conda activate raw${SHORT}
  pip install --upgrade pip
  pip install nbdime pipenv
  pip install -e archaeology
  conda deactivate

  echo "***************************py${SHORT}************************"
  conda create -n py${SHORT} python=${PY} -y
  conda activate py${SHORT}
  pip install --upgrade pip
  pip install nbdime pipenv
  pip install -e archaeology
  conda deactivate
done

echo "All environments created successfully."
