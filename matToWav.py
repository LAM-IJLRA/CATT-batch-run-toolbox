import scipy.io, scipy.io.wavfile
import numpy as np
import os
import re
import math

def matToWav(filename):

	# resolve path to absolute
	filename = os.path.abspath(filename)
	print(f"abspath: {filename!s}")

	mat = scipy.io.loadmat(filename)

	baseNameMatch = re.search(r"_A(.*)\.(?=MAT|mat)", filename)
	baseName = baseNameMatch.group(1) # without extension
	print(f"base name: {baseName!s}")

	audioName = re.sub(r"(.*)(?:\.MAT|\.mat)$", r"\1.wav", filename)
	print(f"audio name: {audioName!s}")

	fs = int(mat["TUCT_fs"])


	if re.search("_OMNI", baseName):
		# OMNI
		varName = "h_A" + baseName
		print(f"var name: {varName!s}")
	
		y = np.array(mat[varName][:])

	elif re.search("_BIN", baseName):
		# BINAURAL
		nbrChannels = len(mat) - 1;
		maxOrder = sqrt(nbrChannel) - 1
		print(f"order {maxOrder}")
		if maxOrder = 1:
		elif

	mat.clear()

	scipy.io.wavfile.write(audioName, fs, y)
