# 'autocatt' Python library and complience commands

Zagala & De Muynke
-------

This repository offers a python library that aims to simplify the use of the *CATT-Acoustics* software and its companion software *TUCT*.

As many of you probably noticed, simulations using CATT-A can be difficult to automatize as nearly all functionnalities require the user to be in front of the computer screen, try to understand the design choices of the GUI, use its mouse for literally everything, and try to not to cry...
As an example, if one wants to launch simulations with different sets of parameters (material parameters, air parameters, more than 260 sources, more than 100 listeners, ...), or dynamically adjust the parameters between each simulation, one has to be physically present in order to modify the parameters and start the next simulation.
This would be:
	- extremely time consuming
	- error prone (at least I trust my script way more than my hands on a keyboard or a mouse)
	- stressful
	- boring
	- limiting
	- ...

Fortunately, CATT-A and TUCT processing pipeline is mainly based on binary files being written to store parameters and information used by the executables.
...and "even more fortunately", it appears that the way those binary files are written is quite (maybe too) naively designed, in a way that data could be read and written without too much troubles (at least after someone spent times trying to understand the structure of those binary files -- you can thank me...)
Therefore, I exploited this particularities of the CATT-A software to wrap CATT-A and TUCT with python code, such that you could then automatize your workflow more easily.

In this repository, you will find a useful python package called *autocatt* that offers a few tools, i.e.:
	- wrapper classes for reading/writting some data structure from/to binary files
	- wrapper class to any `.MD9` file
	- wrapper class to any `*_predictionsettings.DAT` file
	- wrapper class to modify the materials properties in `.GEO` files
	- many other tools

You will also find some convenience command line tools:
	- *acmaterials* to create GUI to modify all material properties more easily in the `.GEO` files
	- *acbatch* to launch arbitrarily many simulation
	- a lot more tools could appear, you could also contribute by proposing some scripts



## To install/use:

1. Before anything else , enable auto-run-save hidden options. Copy the following code in the hidden options  .txt files for CATT and TUCT ("CATTDATA\hidddenoptions_v9.txt" and "CATTDATA\hidddenoptions_TUCT.txt"). The code is the same for both files:

> C2009-05641-49C61-6B041 ;AutoRunSaveCAG

2. create a virtual environement with all required modules (e.g. using conda)
```
conda env create -f environement.yml
```
3. activate the environement
```
conda activate autocatt-env
```
Install the autocatt package as follows
```
cd /the/right/directory
pip install --editable .
```
this will enable you to modify the module yourself without having to re-install it everytime.

Then:
	- either use the 'autocatt' library, e.g.
```Python
from autocatt.projects import readMD9
...
```
	- use the command line tools, e.g.
```
acmaterials -i project.MD9
```
```
acbatch -i project.MD9
```



<!---
--------


# CATT-batch-run-toolbox
Matlab and Python scripts for batch processing of CATT/TUCT2 simulations

CATT_batch_processing.py and CATT_batch_processing.m allow to execute multiple runs of a TUCT2 project and to save the IRs in various formats (OMNI, BIN, BF from 1rst to 3rd order). The IRs are stored in .WAV and the measures in .MAT.

Before anything else , enable auto-run-save hidden options. Copy the following code in the hidden options  .txt files for CATT and TUCT ("CATTDATA\hidddenoptions_v9.txt" and "CATTDATA\hidddenoptions_TUCT.txt"). The code is the same for both files:<br/>
 C2009-05641-49C61-6B041 ;AutoRunSaveCAG

TUCT2 will read the prediction settings from the file room_predictionsettings.DAT contained in the output folder defined in your CATT project. Consequently, if you want to run a single CATT project with different prediction settings, you need to define them prior to running the script.

To do so :
1.	open CATT and load your project
2.	in General settings/Output folder, define the output folder name
3.	launch TUCT2 (‘Save CAG and Run’)
4.	click ‘Predict SxR’ and choose your prediction settings
5.	click ‘OK’ -> room_predictionsettings.DAT is saved in the output folder
6.	exit TUCT2

If you want to define other prediction settings for the same CATT project:

7.	repeat steps [2:6] with a new output folder each time

In any case:

8.	in CATT, make sure that the output folder corresponds to the simulation you want to run
9.	exit CATT and save the settings

## CATT_batch_processing.py
To run it, you need to:
- have python 3, numpy and scipy installed
- define the path to your own CATT folder at line 66

Help section: ‘python CATT_batch_processing.py -h’

When you execute the script, the output folder (`- -o OUTPUT_FOLDER `) MUST BE THE SAME as that set in step 8. Note that the default output folder is ‘<input_file>/OUTPUT’.
Every time you want to use other prediction settings, repeat steps 8 and 9 in order to set the desired output folder.

## CATT_batch_processing.m

Help section: ‘help CATT_batch_processing.m’

To run it, you need to:
- define the path to your own CATT folder at line 54
- set the desired input parameters in the INPUT PARAMETERS SECTION


-->
