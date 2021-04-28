# This script contains functions to manipulate audio exported by TUCT
# zagala - 03.03.2021

import scipy.io, scipy.io.wavfile
import numpy as np
import re
import math
import pathlib

def matToWav(inputFilename: pathlib.Path):
# convert a MAT-files created by TUCT and containing audiodata to WAV data

	inputFilename = inputFilename.resolve()
	folder = inputFilename.parent
	inputfilename = inputFilename.name

	mat = scipy.io.loadmat(inputFilename)

	reMatches = re.search(r"(.*)_([A-Z]\d)_(\d{1,2})_((?:OMNI|BIN|BF))\.(?:MAT|mat)", inputFilename.as_posix())
	prjName = reMatches.group(1)
	src = reMatches.group(2)
	rcv = reMatches.group(3)
	audioType = reMatches.group(4) 

	outputFilename = f"{prjName!s}_{src!s}_{rcv!s}_{audioType!s}.wav"
	outputFilename = folder / outputFilename

	print(f"input file: {inputFilename!s}")
	print(f"output file: {outputFilename!s}")

	fs = int(mat["TUCT_fs"])


	if audioType == "OMNI":
		# OMNI
		suffix = [""]

	elif audioType == "BIN":
		# BINAURAL
		suffix = ["L", "R"]

	elif audioType == "BF":
		# B-FORMAT
		nbrChannels = len(mat) - 1
		maxOrder = nbrChannels ** 0.5 - 1.0

		if maxOrder > 0:
			suffix = ["W", "Y", "Z", "X"] # ACN (order matters !)
		if maxOrder > 1:
			suffix.extend(["V", "T", "R", "S", "U"]) # ACN (order matters !)
		if maxOrder == 3:
			suffix.extend(["Q", "O", "M", "K", "L", "N", "P"]) # ACN (order matters !)
		if maxOrder > 3:
			raise("wrong number of channels")

	else: 
		raise RuntimeError(f"Unkown audioType '{audioType}'")

	suffix = ['_' + suff if suff else '' for suff in suffix]
	varNames = [f"h_{src!s}_{rcv!s}_{audioType!s}{suff!s}" for suff in suffix]

	y = np.stack([np.array(mat[varName][0]) for varName in varNames], axis = 1)

	mat.clear()

	scipy.io.wavfile.write(outputFilename, fs, y)



def convertAllAudioMatToWav(path: pathlib.PosixPath):
# Convert all MAT-files found in path to wavfiles
# Mat-Files must containt "_A" and end with either "_OMNI.MAT" / "_BF.MAT" / "_BIN.MAT".
# suffixe ".MAT" can also be written small ".mat"

	path = pathlib.Path(path)
	pattern = r"[\w\d\_\-]+_A[\w\d\_\-]+_(?:OMNI|BIN|BF).(?:MAT|mat)$"
	pattern = re.compile(pattern)
	generatorMatFile = (matFile for matFile in path.iterdir() if pattern.search(matFile.name))

	for matFile in generatorMatFile:
		matToWav(matFile)
