# -*- coding: utf-8 -*-
#!/usr/bin/python

# Franck Zagala - 02.03.2021

import click
import os
os.environ["KIVY_NO_CONSOLELOG"] = "0"
os.environ["KIVY_NO_ARGS"] = "0"
import autocatt.materials
import autocatt.projects
import autocatt.materialsGUI
import pathlib
import fileinput
import re

@click.command()
@click.option("-i", "--input-file", "inputFile", 
		prompt="input file", 
		help="full path to the .MD9 file", 
		type=click.Path(exists=True, file_okay=True, dir_okay=False, resolve_path=True))

def main(inputFile):

	# conversion to Pathlib.path to ease path manipulations
	inputFile = pathlib.Path(inputFile)

	A = autocatt.projects.MD9Wrapper(inputFile)
	geoFile = A.inputFolder / A.masterGeoFile
	if A.inputFolder.is_absolute() == False:
		geoFile = inputFile.parent / geoFile


	print("----------------")
	print("input File :     ", str(inputFile))
	print("geo file :       ", str(geoFile))

 	# modify config file of materialsApp
	# One cannot directly pass parameters to the App, therefore the input files are passed through the config file

	modulePath = pathlib.Path(autocatt.__file__).parent
	configFilename = "materialmodifier.ini"
	configFilename = modulePath / configFilename
	configFilename = str(configFilename.absolute())

	print(geoFile)
	with open(configFilename, 'w+') as f:
		f.write("[input]\n")
		f.write("geofilename = " + str(geoFile) + "\n")

	print("test")
			
	A = autocatt.materialsGUI.MaterialModifierApp()
	A.run()






if __name__ == "__main__":
	print('1')
	main()
