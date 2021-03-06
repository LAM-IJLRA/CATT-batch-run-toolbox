# This script contains functions and objects relative to CATT and TUCT projects configurations
# zagala - 04.03.2021

import re
import pathlib

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
			"inputDir": pathlib.PureWindowsPath( pathExtr.findall( data[269:529].decode("ASCII"))[0] ),
			"outputDir": pathlib.PureWindowsPath( pathExtr.findall( data[530:790].decode("ASCII"))[0] ),
			"geoFile": pathlib.PureWindowsPath( geoExtr.findall( data[791:1046].decode("ASCII"))[0] ),
			"rcvLoc": pathlib.PureWindowsPath( locExtr.findall( data[1047:1302].decode("ASCII"))[0] ),
			"srcLoc": pathlib.PureWindowsPath( locExtr.findall( data[1303:1558].decode("ASCII"))[0] )
		}

	return projectConfig


