# Installation

To install just the chsimpy module and its CLI application:
```bash
pip install git+https://github.com/uncertaintyhub/chsimpy.git
```

Additional requirements also can be selected with:
```bash
# 'interactive' installs jupyter packages
# 'qt5' installs PyQt5 for faster GUI response times
pip install "chsimpy[interactive, qt5] @ git+https://github.com/uncertaintyhub/chsimpy.git"
```

If there are version issues with already existing python packages, use [python virtual environments](https://packaging.python.org/en/latest/guides/installing-using-pip-and-virtual-environments/) (or see below) or the chsimpy docker container build method (see section [Docker / Jupyter](#docker--jupyter)).

### Installation on Windows

- Get **python** from <https://www.python.org/>, if it is not already installed on your system
  - Alternatively: Anaconda from <https://www.anaconda.com/> also works
- Get **git** from <https://git-scm.com/download/win>, if it is not already installed on your system
- Run a Windows _command prompt_ (WindowsKey+R or Windows Starter, then entering 'cmd')
  - Alternatively: run Anaconda command prompt from Windows Starter
- Enter in the command prompt:
```
py -3 -m pip install git+https://github.com/uncertaintyhub/chsimpy.git
```
- Alternatively: download [chsimpy as zip](https://github.com/uncertaintyhub/chsimpy/archive/refs/heads/main.zip), unpack it, open _command prompt_ there and run:
  - `py -3 -m chsimpy --help` (run within unpacked chsimpy folder)
  - or to install chsimpy as package: `py -3 -m pip install .`

- if chsimpy is installed as package, run it from a _command prompt_ by:
```
chsimpy --help
```

### Using Python Virtual Environments (conda)

```bash
git clone https://github.com/uncertaintyhub/chsimpy.git
cd chsimpy
conda create -n chsimpy_env python
conda activate chsimpy_env
conda install --file requirements.txt -c conda-forge
python setup.py install
```

### Using Python Virtual Environments (venv)

```bash
git clone https://github.com/uncertaintyhub/chsimpy.git
cd chsimpy
python -m venv venv-folder
source venv-folder/bin/activate
pip install .
```
