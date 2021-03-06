# This script contains functions to manipulate audio exported by TUCT
# zagala - 03.03.2021

import scipy.io, scipy.io.wavfile
import numpy as np
import re
import math
import pathlib

def matToWav(filename: pathlib.PosixPath):
# convert a MAT-files created by TUCT and containing audiodata to WAV data

	# resolve path to absolute
	filename = filename.resolve()

	mat = scipy.io.loadmat(filename)

	baseNameMatch = re.search(r".*_A(.*)\.(?=MAT|mat)", filename.as_posix())
	baseName = baseNameMatch.group(1) # without extension

	audioName = re.sub(r"(.*)(?:\.MAT|\.mat)$", r"\1.wav", filename.as_posix())

	print(f"input file: {filename!s}")
	print(f"output file: {audioName!s}")

	fs = int(mat["TUCT_fs"])


	if re.search("_OMNI", baseName):
		# OMNI
		suffix = [""]

	elif re.search("_BIN", baseName):
		# BINAURAL
		suffix = ["L", "R"]
		suffix = ["_" + suff for suff in suffix]

	elif re.search("_BF", baseName):
		# B-FORMAT
		nbrChannels = len(mat) - 1
		maxOrder = sqrt(nbrChannel) - 1
		print(f"order {maxOrder}")

		if maxOrder > 0:
			suffix = ["W", "Y", "Z", "X"] # FUMA (order matters !)
		elif maxOrder > 1:
			suffix.extend(["V", "T", "R", "S", "U"]) # FUMA (order matters !)
		elif maxOrder == 3:
			suffix.extend(["Q", "O", "M", "K", "L", "N", "P"]) # FUMA (order matters !)
		else:
			raise("wrong number of channels")

		suffix = ["_" + suff for suff in suffix]

	varNames = ["h_A" + baseName + suff for suff in suffix]
	y = np.hstack([np.array(mat[varName][0]) for varName in varNames])

	mat.clear()

	scipy.io.wavfile.write(audioName, fs, y)



def convertAllAudioMatToWav(path: pathlib.PosixPath):
# Convert all MAT-files found in path to wavfiles
# Mat-Files must containt "_A" and end with either "_OMNI.MAT" / "_BF.MAT" / "_BIN.MAT".
# suffixe ".MAT" can also be written small ".mat"

	pattern = r"[\w\d\_\-]+_A[\w\d\_\-]+_(?:OMNI|BIN|BF).(?:MAT|mat)$"
	pattern = re.compile(pattern)
	generatorMatFile = (matFile for matFile in path.iterdir() if pattern.search(matFile.name))

	for matFile in generatorMatFile:
		matToWav(matFile)
