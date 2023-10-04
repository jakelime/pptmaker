# PPT Maker

Using tetk framework (python3.10, tkinter UI),

PPMK is a basic GUI for generating wafer map reports

## Quickstart

```bash
git clone git@github.com:jakelime/pptmaker.git
pip install -r requirements-win.txt
cd pptmaker
python tetk/main.py
```

Once the GUI application is started, follow the `buttons` and read the logs for instructions.

Basic usage - load files into `input dir`, click `run`, results will be contained in `output dir`

## Running unittests

`pytest` is used in this project. Used `pytest -v` for automated testing.

```bash
(py311) ➜  pptmaker git:(main) pytest -v
================================================================= test session starts ==================================================================
platform darwin -- Python 3.11.5, pytest-7.4.2, pluggy-1.3.0 -- /Users/jakelim/anaconda3/envs/py311/bin/python
cachedir: .pytest_cache
rootdir: /Users/jakelim/SynologyDrive/cloud-active_project/pptmaker
collected 2 items

tetk/test_main.py::test_detect_images PASSED                                                                                                     [ 50%]
tetk/test_main.py::test_main_production_run PASSED                                                                                               [100%]

================================================================== 2 passed in 1.19s ===================================================================
```

The tkinter interface is not tested because of the complexity. Only functional unittests are conducted.

1. test_detect_images()
   - intermediate step required to ensure that there are input files

1. test_main_production_run()
   - full sequence of production run step
   - a pytest-results-20231005_032538.pptx output is generated if successful

## Detailed guide

### Description

- App is customizable using recipe control
  - Switch between recipes using `File > Recipe`
  - Create new file `recipe.yml` for new projects
  - Variables are set inside the `recipe.yml` file

### How to use version control

Refer to detailed guide here for [git & ssh](https://github.com/jakelime/guide-git-ssh/).

### Using `MacOS`

1. Download `python` from official source,
   [PSF](https://www.python.org/downloads/macos/)

1. Install `python`, create virtual environment `venv` and then `pip install -r requirements.txt`

   ```bash

   N2390113:~ jli8$ which python3
   /Library/Frameworks/Python.framework/Versions/3.10/bin/python3
   N2390113:~ jli8$ python3 --version
   Python 3.10.10

   N2390113:190-pptmaker jli8$ python3 -m venv venv
   N2390113:190-pptmaker jli8$ source venv/bin/activate
   (venv) N2390113:190-pptmaker jli8$ which python
   /Users/jli8/Library/CloudStorage/SynologyDrive-OnDemand/190-pptmaker/venv/bin/python
   (venv) N2390113:190-pptmaker jli8$ python --version
   Python 3.10.10

   (venv) N2390113:190-pptmaker jli8$ python -m pip install -r requirements-macos.txt
   ```

1. Execute the app using `python`

   ```bash
   (venv) N2390113:190-pptmaker jli8$ python tetk/main.py
   ```

1. Compile executable using `pyinstaller`
   ```bash
   (venv) N2390113:190-pptmaker jli8$ pyinstaller tetk/main.py --name tetk --add-data=tetk/bundles/\*:bundles/ --windowed --icon=icon.png
   ```

### Setting up `python` on `Windows`

1.  Download latest python3.10 stable from [PSF](https://www.python.org/downloads/)

1.  Install locally for single user, select `modify path variable`

1.  Use powershell(`pwsh`) or commandprompt(`cmd.exe`). Commands may differ but concept is the same

1.  Make sure you are using `venv`, and double check your `python` path

    ```powershell
    PS C:\> cd ~
    PS C:\Users\jli8> cd "~\AppData\Local\Programs\Python\Python310"
    PS C:\Users\jli8\AppData\Local\Programs\Python\Python310> .\python.exe --version
    Python 3.10.10
    PS C:\Users\jli8\AppData\Local\Programs\Python\Python310> .\python.exe -m venv ~\git_repos\pptmaker\venv
    PS C:\Users\jli8\AppData\Local\Programs\Python\Python310> .\git_repos\pptmaker\venv\Scripts\activate
    (venv) PS C:\Users\jli8\git_repos\pptmaker> python -m pip install -r requirements-win.txt
    ```

1.  Execute the app using `python`

    ```powershell
    (venv) PS C:\Users\jli8\git_repos\pptmaker> python .\tetk\main.py
    ```

1.  Compile executable using `pyinstaller`
    ```powershell
    (venv) PS C:\Users\jli8\git_repos\pptmaker> pyinstaller .\tetk\main.py --name tetk --add-data "tetk/bundles/*;bundles/" --windowed --icon="tetk/bundles/icon.ico" --noconfirm
    ```

## Changelogs

- v1.2.0
  - Added error catching features
    - Use debug=True in configuration file
    - Hashmap of input file to aid in debugging
  - Used error catching to bypass exception if a single image failed
    - Bad image will be skipped
    - The coor_x, coor_y of the bad image will be empty, but
      subsequent images will continue processing
- v1.0.0
  - KEY Feature: Detects
    - wafer images in `input folder`
    - sorts, throwaway (discard)
    - hashmapping for other functions
    - display to UI for debugging
  - KEY Feature: Plot all images, in a lot per slide
  - KEY Feature: Plot all images, 1-to-1 comparison
  - Features:
    - Debug with text output window
    - Configurable config.yml file
    - Easy to use UI
    - Factory reset function

## Miscellaneous

### `pip` commands

```bash
(base) N2390113:190-pptmaker jli8$ python -m venv venv
(base) N2390113:190-pptmaker jli8$ source venv/bin/activate
(venv) (base) N2390113:190-pptmaker jli8$ conda deactivate
(venv) N2390113:190-pptmaker jli8$ which python
/Users/jli8/Library/CloudStorage/SynologyDrive-OnDemand/190-pptmaker/venv/bin/python

pip install PyYAML pandas python-pptx pyinstaller
python -m pip freeze > requirements-macos.txt
python -m pip freeze > requirements-win.txt
```

### Documentation using `sphinx`

```bash
sphinx-quickstart
separate source and build directories: y
sphinx-build -b html source build/html
cd ..
sphinx-apidoc -o docs/source tetk
```

### Convert `readme.rst` to `readme.md`

```bash
FILES=readme.rst
for f in $FILES
do
filename="${f%.*}"
echo "Converting $f to $filename.md"
`pandoc $f -f rst -t markdown -o $filename.md`
done
```

- Requires `pandoc`
  - <https://stackoverflow.com/questions/45633709/how-to-convert-rst-files-to-md>
  - <https://gist.github.com/zaiste/77a946bbba73f5c4d33f3106a494e6cd>
  - <https://pandoc.org/>
  - `brew install pandoc`
