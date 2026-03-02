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
# Python 3.6
########################################
echo '***************************raw36************************'
conda create -n raw36 python=3.6 -y
conda activate raw36
pip install --upgrade pip
pip install nbdime pipenv nltk
pip install -e archaeology
conda deactivate
echo '***************************py36************************'
conda create -n py36 python=3.6 -y
conda activate py36
conda install -y anaconda-navigator jupyterlab_server navigator-updater
pip install --upgrade pip
pip install nbdime flake8-nb biopython pipenv nltk
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
pip install nbdime pipenv nltk
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
pip install nbdime pipenv nltk
pip install -e archaeology
python -c "import nltk; nltk.download('stopwords')"
conda deactivate
########################################
# Modern Python versions (3.8, 3.9, 3.10)
########################################
for PY in 3.8 3.9 3.10
do
  SHORT=$(echo $PY | tr -d '.')
  
  echo "***************************raw${SHORT}************************"
  conda create -n raw${SHORT} python=${PY} -y
  conda activate raw${SHORT}
  pip install --upgrade pip
  pip install nbdime pipenv nltk
  pip install -e archaeology
  conda deactivate
  echo "***************************py${SHORT}************************"
  conda create -n py${SHORT} python=${PY} -y
  conda activate py${SHORT}
  pip install --upgrade pip
  pip install nbdime pipenv nltk
  pip install -e archaeology
  python -c "import nltk; nltk.download('stopwords')"
  conda deactivate
done
echo "All environments created successfully."
