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

When you execute the script, the output folder (‘ --o ‘’ OUTPUT_FOLDER’’ ’) MUST BE THE SAME as that set in step 8. Note that the default output folder is ‘<input_file>/OUTPUT’.
Every time you want to use other prediction settings, repeat steps 8 and 9 in order to set the desired output folder.

## CATT_batch_processing.m

Help section: ‘help CATT_batch_processing.m’

To run it, you need to:
- define the path to your own CATT folder at line 54
- set the desired input parameters in the INPUT PARAMETERS SECTION

