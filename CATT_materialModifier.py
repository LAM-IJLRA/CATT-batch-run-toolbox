# -*- coding: utf-8 -*-
#!/usr/bin/python

# Franck Zagala - 02.03.2021

import click
import os
os.environ["KIVY_NO_CONSOLELOG"] = "1"
os.environ["KIVY_NO_ARGS"] = "1"
import autocatt.materials
import autocatt.projects
import autocatt.materialsGUI
import pathlib
import fileinput
import re

@click.command()
@click.option("-i", "--input-file", "inputFile", 
		prompt="input file", 
		help="full path to the .md9 file", 
		type=click.Path(exists=True, file_okay=True, dir_okay=False, resolve_path=True))

def main(inputFile):

	# conversion to Pathlib.path to ease path manipulations
	inputFile = pathlib.Path(inputFile)

	geoFile = autocatt.projects.readMD9(inputFile)["geoFile"]

	print("----------------")
	print("input File :     ", inputFile.as_posix())
	print("geo file :       ", geoFile.as_posix())

 	# modify config file of materialsApp
	# One cannot directly pass parameters to the App, therefore the input files are passed through the config file

	allFilesWithMat = autocatt.projects.getAllNestedGeoFiles(geoFile, keepOnlyMaterialRelevant = True)
	print(f"Geo files with materials definitions: {allFilesWithMat}")
	allFilesWithMat = [str(x.absolute()) for x in allFilesWithMat]
	allFilesWithMat = ', '.join(allFilesWithMat)

	configFilename = "autocatt/materials.ini"
	configFilename = pathlib.Path(configFilename)
	absPath = os.path.realpath(__file__)
	configFilename = pathlib.Path(absPath).parent / configFilename
	configFilename = str(configFilename.absolute())
	f = open(configFilename, "w+")
	f.write("[input]\n")
	f.write("geofilenames = " + allFilesWithMat + "\n")
	f.close()
			
	A = autocatt.materialsGUI.MaterialsApp()
	A.run()






if __name__ == "__main__":
   main()
