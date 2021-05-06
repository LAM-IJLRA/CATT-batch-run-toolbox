import ImpResSiF.signals
import ImpResSiF.filtering
import numpy as np
from scipy.io import wavfile
import pandas as pd
import pathlib
import re

# IR are "stored" in a Dataframe with the following columns:
# - folder
# - filename
# - source
# - receiver
# - repetition
# - origin (e.g. measurement, simulation, ...)
# - processing (e.g. denoised) 
# The following columns are then computed from the impulse response in post processing:
# - frequency bands
# - T30 (per freq band)
# - C80 (per freq band)


class IRToImport(dict):
# this class wraps a dictionnary and is moslty used to setting default key values
	def __init__(self, filename: pathlib.Path, *args, source = "1", receiver = "1",\
			repetition = 1, origin = "", processing = "", **kwargs):

		folder = str(filename.parent)
		filename = str(filename.name)
		super().__init__(*args, folder = folder, filename = filename,\
				source = source, receiver = receiver, repetition = repetition,\
				origin = origin, processing = processing, **kwargs)
		


def importFiles(folder, pattern = r"mic(?P<receiver>[a-zA-Z0-9]+)_(?P<source>[a-zA-Z0-9]+)_(?P<repetition>\d+)\.(?:wav|WAV)"):
	# pattern must be a raw string used for regexp, catching groups must be using symbolic group names
	# e.g. to capture an alphanumeric source name, this should be done with the group (?P<source>[a-zA-Z0-9])

	pattern_comp = re.compile(pattern)

	# get all files that match the required formatting
	allFN = [f for f in folder.glob("*") if pattern_comp.search(str(f))]

	# create dataframe
	dataList = [IRToImport(fn, **pattern_comp.search(str(fn)).groupdict()) for fn in allFN]

	print(dataList)

	df = pd.DataFrame(dataList)
	
	print('$$$$')
	print(df)
	print('$$$$')

	# make sure the right data types are used
	df = df.astype(dtype= {"folder": "string", "filename": "string", "source": "category", "receiver": "category", "repetition": "uint16", "origin": "category", "processing": "category"})
	return df


def loadIRData(row, FB):
# dirty implementation, but for now: FB is a dictionnary of filter bank according to different sampling frequencies, hence avoiding the creation of the right filter bank everytime
	filename = pathlib.Path(row["folder"]) / row["filename"]
	print(f"{filename=}")
	fs, data = wavfile.read(str(filename))
	ir = ImpResSiF.signals.ImpulseResponse(data, fs = fs)
	ir_oct = FB[fs].filter(ir)
	freqs = list(ir_oct.keys())
	T30 = np.hstack([ir_o.T30 for ir_o in ir_oct.values()])
	C80 = np.hstack([ir_o.C80 for ir_o in ir_oct.values()])
	return freqs, T30, C80


def computeAcousticParameters(df):
	potentialFs = [44100, 48000, 96000]
	FB = {fs: ImpResSiF.filtering.FractionnalBandFilterBank(fLow = 125.0, fHigh = 16000.0, width = "octave", fs = fs) for fs in potentialFs}
	a = df.apply(lambda row : loadIRData(row, FB), axis = 1)
	a = list(zip(*a))
	df["frequency band"] = a[0]
	df["T30"] = a[1]
	df["C80"] = a[2]


def createCATTResultsDataframe(projName, outputFolder: pathlib.Path):
	outputFolder = pathlib.Path(outputFolder)

	pattern = projName + r"_(?P<repetition>\d+)_(?P<source>[A-Z]\d{1,2})_(?P<receiver>\d{1,2}_OMNI.(?:WAV|wav))"
	print(pattern)
	df = importFiles(outputFolder, pattern = pattern)
	computeAcousticParameters(df)

	df["origin"] = "CATT-Acoustics / TUCT"
	
	df.to_csv(outputFolder / f"{projName}_dataframe.csv")


if __name__ == "__main__":
	folder = pathlib.Path("/Users/zagala/Documents/Doctorat_IRCAM_UPMC/misc/amphi55a/measures/irs/")
	df = importFiles(folder, pattern = r"mic(?P<receiver>[a-zA-Z0-9]+)_(?P<source>[a-zA-Z0-9]+)_(?P<repetition>\d+)\.(?:wav|WAV)")
	df_denoised = importFiles(folder, pattern = r"mic(?P<receiver>[a-zA-Z0-9]+)_(?P<source>[a-zA-Z0-9]+)_(?P<repetition>\d+)_denoised\.(?:wav|WAV)")

	df_denoised["processing"] = "denoised"

	df = pd.concat([df, df_denoised]).reset_index(drop=True)

	df["origin"] = "measures"
	
	computeAcousticParameters(df)

	df.to_csv("/Users/zagala/Documents/Doctorat_IRCAM_UPMC/misc/amphi55a/measures/dataframe2.csv", index = False)
	print(df)


