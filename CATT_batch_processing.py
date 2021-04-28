# -*- coding: utf-8 -*-
#!/usr/bin/python

# Franck Zagala - 02.03.2021

import click
import os
import autocatt.materials
import autocatt.audio
import autocatt.projects
import pathlib
import re
import subprocess

@click.command()
@click.option("-i", "--input-file", "inputFile", 
		prompt="input file", 
		help="full path to the .md9 file", 
		type=click.Path(exists=True, file_okay=True, dir_okay=False, resolve_path=True))
@click.option("-N", "--nbr-runs", "nbrRuns",
		default=1, 
		help="number of runs", 
		type=click.INT)
@click.option("-f", "--ir-format", "irFormat",
		multiple=True,
		default=["omni", "bf", "bin"], 
		type=click.Choice(["omni", "bf", "bin"], case_sensitive=False))
@click.option("-m/-M", "--meas/--no-meas", 
		default=True,
		help="whether measure files should be created")
@click.option("-e", "--executable", "CATTexe",
		prompt=True,
		default=lambda: os.environ.get("AUTOCATT_CATT_EXE", ""),
		type=click.Path(exists=True, file_okay=True))
@click.option("-t", "--tuct-executable", "TUCTexe",
		prompt=True,
		default=lambda: os.environ.get("AUTOCATT_TUCT_EXE", ""),
		type=click.Path(exists=True, file_okay=True))
def main(inputFile, nbrRuns, irFormat, meas, CATTexe, TUCTexe):
# launch CATT and TUCT simulations nbrRuns times from MD9 file
# MD9 file must have been generated before

	# conversion to Pathlib.path to ease path manipulations
	inputFile = pathlib.Path(inputFile)

	A = autocatt.projects.MD9Wrapper(inputFile)

	inputFolder = A.inputFolder
	outputFolder = A.outputFolder
	geoFile = A.masterGeoFile
	rcvLoc = A.receiverLocFile
	srcLoc = A.sourceLocFile
	projectName = A.projName


	CATTexe = pathlib.Path(CATTexe)
	TUCTexe = pathlib.Path(TUCTexe)


	print("----------------")
	print(A)
	print("number of runs : ", nbrRuns)
	print("irFormat :       ", irFormat)
	print("export meas :	", meas)
	print("CATT exe :       ", CATTexe)
	print("TUCT exe :       ", TUCTexe)



	CAGBaseName = outputFolder / projectName
	print(f"CAG basename: {CAGBaseName}")

	# check for count number
	counterFile = CAGBaseName.with_name(projectName + "_count.DAT")
	if counterFile.exists():
		counterFileW = autocatt.projects.CounterFileWrapper(counterFile)
		count = counterFileW.count
		print(counterFileW)
	else:
		count = 0
			

	for ii in range(nbrRuns):
		count += 1

		subprocess.run([str(CATTexe), str(inputFile), '/AUTO'], shell = True, check = True)
		print("CATT exe done\n")

		CAGFile = CAGBaseName.parent / (CAGBaseName.stem + f"_{count:d}.CAG")
		subprocess.run([str(TUCTexe), str(CAGFile), "/AUTO", f"/SAVE:{','.join(irFormat)}"], shell = True, check = True)
		print("TUCT exe done\n")

		# move all CATT anbd TUCT output files to folder of current run 
#outputRunFolder = outputFolder.parent / f"OUTPUT_{projectName}_finalResults" / f"run{ii:d}"

		print("\n")

	
	


if __name__ == "__main__":
   main()
