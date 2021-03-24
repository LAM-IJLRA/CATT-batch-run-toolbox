# This script contains functions and objects relative to CATT and TUCT projects configurations
# zagala - 04.03.2021

import re
import pathlib
import fileinput
import autocatt.materials

def readMD9(filename: pathlib.Path):
# read MD9-file and store basic information in dictionnary such as
# - project name
# - inout directory
# - output directory
# - geo file
# - receiver loc file
# - source loc file
#
# zagala - 04.03.2021


	projExtr = re.compile(r"[\w\d\-\_]+")
	pathExtr = re.compile(r"(?:[A-Z]\:)?[\w\d\-\_\/\\\:]+")
	geoExtr = re.compile(r"[\w\d\-\_]+\.(?:GEO|geo)")
	locExtr = re.compile(r"[\w\d\-\_]+\.(?:LOC|loc)")

	with open(filename.as_posix(), 'rb') as binFile:
		data = binFile.read()

		projectConfig = {
			"project": projExtr.findall(data[8:268].decode("ASCII"))[0],
			"inputDir": pathlib.Path( pathExtr.findall( data[269:529].decode("ASCII"))[0] ),
			"outputDir": pathlib.Path( pathExtr.findall( data[530:790].decode("ASCII"))[0] ),
			"geoFile": pathlib.Path( geoExtr.findall( data[791:1046].decode("ASCII"))[0] ),
			"rcvLoc": pathlib.Path( locExtr.findall( data[1047:1302].decode("ASCII"))[0] ),
			"srcLoc": pathlib.Path( locExtr.findall( data[1303:1558].decode("ASCII"))[0] )
		}

	return projectConfig


def getNestedGeoFiles(geoFilename: pathlib.Path):

	pattern = r"^\s*INCLUDE\s+(.+\.(?:GEO|geo))\b"
	patternComp = re.compile(pattern)

	if isinstance(geoFilename, pathlib.Path) == False:
		geoFilename = pathlib.Path(geoFilename)
	geoFilename.resolve()
	inputFolder = geoFilename.parent

	nestedFiles = []
	if geoFilename.exists():
		with open(geoFilename) as f:
			for line in f:
				if (x := patternComp.findall(line)):
					currFile = x[0]
					currFile = pathlib.Path(currFile)
					if currFile.is_absolute() == False:
						currFile = inputFolder / currFile
	
					nestedFiles.append(currFile)
	else:
		print("file '{geoFilename}' does not exist")
		nestedFiles = []
	return nestedFiles


def getAllNestedGeoFiles(geoMasterFilename: pathlib.Path, keepOnlyMaterialRelevant = False):

	if isinstance(geoMasterFilename, pathlib.Path) == False:
		geoMasterFilename = pathlib.Path(geoMasterFilename)

	allFilenames = []
	newFilenamesCurrOrder = [geoMasterFilename]
	while bool(newFilenamesCurrOrder):
		allFilenames.extend(newFilenamesCurrOrder)
		newFilenamesNextOrder = []
		for f in newFilenamesCurrOrder:
			nestedFilenames = getNestedGeoFiles(f)
			newFilenamesNextOrder.extend(nestedFilenames)
		newFilenamesCurrOrder = newFilenamesNextOrder

	if keepOnlyMaterialRelevant:
		patternComp = re.compile(autocatt.materials.patternLine)
		tmpFilesToKeep = []
		for geoFile in allFilenames:
			with open(geoFile) as f:
				for line in f:
					if patternComp.match(line):
						tmpFilesToKeep.append(geoFile)
						break
		allFilenames = tmpFilesToKeep
	

	return allFilenames

		
			

	

