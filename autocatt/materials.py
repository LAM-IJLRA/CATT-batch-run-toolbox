import re
import pathlib
import numpy as np
import fileinput # to modify file inplace with re
import numbers
#import materialsGUI
from collections.abc import Iterable
import pandas as pd

patternMatName = r"([A-Za-z0-9_]{1,15})" # max 15 charcters among letters, numbers and '_'
pattern0to100 = r"0*(?:[1-9]?[0-9]|100)" # only integer from 0 to 100 with possible leading zeros
# TODO: allow for scientific notation, e.g. 1 1. 1.0 1E+00 1.E+00 1.0E+00 1E0 1.E0 1.0E0
# TODO: abs values are actually defined in interval ]0, 100[ not [0, 100]
# TODO: implement definition of transmission values, e.g. <10/2 9/19 ...>
# TODO: accept < estimate(0.4) > and control the parameter with slider
# TODO: accept 'ABS1' for defining values within ]0, 1[ instead of ]0, 100[
patternGrpNbrs = r"<(\s*(?:" + pattern0to100 + r"\s*){6}(?::?\s*" + pattern0to100 + r"\s*){0,2})>"
pattern0To255Int = r"\b(?:1?[0-9]{1,2}|2[0-4][0-9]|25[0-5])\b"
patternColor = r"{[ \t]*((?:" + pattern0To255Int + r"[ \t]*){3})}"
patternLine = r"^\s*(?:AUD)?ABS\s*[a-zA-Z0-9_-]+\s*=\s*" + patternGrpNbrs + r"(?:\s*L1?\s*" + patternGrpNbrs + r"[ \t]*)?" + r"[ \t]*(?:" + patternColor + ")?"


class FreqBandValues:
	def __init__(self, values, callback=None):
		firstFreq = 125
		frequencies = [125, 250, 500, 1000, 2000, 4000, 8000, 16000]
		self._values = dict(zip(frequencies, values))
		self.callback = callback

	def __getitem__(self, freq):
		return self._values[freq]

	def __setitem__(self, freqs, vals):
		# TODO: clean this mess
		if isinstance(vals, numbers.Number) == False and len(freqs) != len(vals):
			raise ValueError("'vals' must be a scalar or have the same length as 'freqs'")
		if isinstance(freqs, numbers.Number) == False:
			for ff in freqs:
				if ff not in self._values:
					raise ValueError(f"Unknown frequency {ff}")
			if isinstance(vals, numbers.Number) == False:
				for f, v in zip(freqs, vals):
					self._values[f] = v
			else:
				for f in freqs:
					self._values[f] = vals
		else:
			if freqs not in self._values:
				raise ValueError(f"Unknown frequency {freqs}")
			self._values[freqs] = vals

		if self.callback is not None:
			self.callback()

	@property
	def values(self):
		return list(self._values.values())

	@property
	def frequencies(self):
		return list(self._values.keys())
			
		
		
		

class Material:
	def __init__(self, name, filenames = ()):
		self._name = name
		self._absCoeff = []
		self._scattCoeff = []
		self._color = []
		self._filenames = filenames

		self._pattern = r"^\s*ABS\s*" + self._name + r"\s*=\s*" + patternGrpNbrs + r"(?:\s*L1?\s*" + patternGrpNbrs + r")?" + r"(?:[ \t]*" + patternColor + r")?"
		self._patternComp = re.compile(self._pattern)

		# pattern used to replace the content of abs coeffs only
		# new values must be inserted between 1st and 2nd group 
		self._patternShort = r"(^\s*ABS\s*" + self._name + r"\s*=\s*)<[\d\s:]*>[ \t]*(?:{" + patternColor + "})?(.*$)"
		self._patternShortComp = re.compile(self._patternShort)

		# pattern used to replace the content of abs coeffs and scatt coeffs
		# new values for abs coeffs must be inserted between 1st and 2nd group 
		# new values for scatt coeffs must be inserted between 2nd and 3nd group 
		self._patternLong = r"(^\s*ABS\s*" + self._name + r"\s*=\s*)<[\d\s:]*>([ \t]*L1?[ \t]*)<[\d\s:]*>[ \t]*(?:{" + patternColor + "})?(.*$)"
		self._patternLongComp = re.compile(self._patternLong)



		# import values for absCoeff and scattCoeff from files
		self.importValuesFromFiles()

	def __str__(self):
		return f"Material '{self._name}'\nabs coeff: {*self._absCoeff.values,}\nscatt coeff: {*self._scattCoeff.values,}"

	def getDataFrame(self):
		df = pd.DataFrame(self.absCoeff._values)
		if self.scattCoeff:
			df2  = pd.DataFrame(self.ScattCoeff._values)
			df = pd.concat([df, df2])
		df["material"] = self.name
		return df

	@property
	def name(self):
		return self._name
	
	@property
	def absCoeff(self):
		return self._absCoeff

	@property
	def scattCoeff(self):
		return self._scattCoeff

	@property
	def color(self):
		return self._color
	@color.setter
	def color(self, color):
		self._color = color
		self.updateValuesInFile()

	def importValuesFromFiles(self):
		materialRead = False
		with fileinput.input(files=self._filenames) as f:
			for line in f:
				if (x := self._patternComp.findall(line)):
					if materialRead is True:
						raise RuntimeError("Material seems to be defined more than once in the files")
					absCoeff = [int(s) for s in re.split(r"[ \t]+|(?:[ \t]*:[ \t]*)", x[0][0].strip()) if s]
					scattCoeff = [int(s) for s in re.split(r"[ \t]+|(?:[ \t]*:[ \t]*)", x[0][1].strip()) if x[0][1] and s]
					color = [int(s) for s in re.split(r"[ \t]+", x[0][2].strip()) if x[0][2]]
					materialRead = True

		self._absCoeff = FreqBandValues(absCoeff, callback = self.updateValuesInFile)
		self._scattCoeff = FreqBandValues(scattCoeff, callback = self.updateValuesInFile)
		if color:
			self._color = color # default value is set in constructor for ease


	def updateValuesInFile(self):
		newStrAbsCoeffsArray = [str(int(x)) for x in self._absCoeff.values]
		if len(newStrAbsCoeffsArray) > 6:
			newStrAbsCoeffsArray.insert(6, ':')
		newStrAbsCoeffs = ' '.join(newStrAbsCoeffsArray)
		if self.color:
			newStrColor = ' {' + ' '.join([str(int(cc)) for cc in self.color]) + '}'
		else:
			newStrColor = ''

		if not bool(self._scattCoeff.values):
			# only needs to modify abs coeffs
			with fileinput.input(files = self._filenames, inplace = True) as f:
				for line in f:
					line = self._patternShortComp.sub(r"\g<1><" + newStrAbsCoeffs + r" >" + newStrColor + "\g<2>", line.rstrip())
					print(line, end = '\r\n')
		else:
			# both abs coeffs AND scatt coeffs are updated
			newStrScattCoeffsArray = [str(int(x)) for x in self._scattCoeff.values]
			if len(newStrScattCoeffsArray) > 6:
				newStrScattCoeffsArray.insert(6, ':')
			newStrScattCoeffs = ' '.join(newStrScattCoeffsArray)
			with fileinput.input(files = self._filenames, inplace = True) as f:
				for line in f:
					line = self._patternLongComp.sub(r"\g<1><" + newStrAbsCoeffs + r" >\g<2><" + newStrScattCoeffs + r">" + newStrColor + "\g<3>", line.rstrip())
					print(line, end = '\r\n')
			



def getAllMaterialsFromFiles(filenames):
	pattern = r"^\s*ABS\s+" + patternMatName + "\s*=\s*" + patternGrpNbrs + r"(?:\s*L\s*" + patternGrpNbrs + r")?"

	patternComp = re.compile(pattern)

	allNames = []
	scattCoeffsDefined = []
	with fileinput.input(filenames) as f:
		for line in f:
			if (x := patternComp.findall(line)):
				name = x[0][0]
				if name in allNames:
					raise RuntimeError("Material seems to be defined more than once in the files")
				if x[0][2]:
					scattCoeffsDefined.append(True)
				else:
					scattCoeffsDefined.append(False)
				allNames.append(name)

	# sort materials according to their names
	allFilenamesWithScattDef = list(zip(allNames, scattCoeffsDefined))
	allFilenamesWithScattDef.sort(key=lambda x : x[0], reverse = False)

	return list(zip(*allFilenamesWithScattDef)) # unzip the zipped tuples with *



class ProjectMaterials:
	def __init__(self, filename):
		allMaterialNames, isScattDef = getAllMaterialsFromFiles(filename)
		self._materials = {mat: Material(mat, filenames = filename) for mat in allMaterialNames}
		self._NparamsAbs = 0
		self._NparamsScatt = 0
		for mat in self._materials.values():
			self._NparamsAbs += len(mat.absCoeff.values)
			self._NparamsScatt += len(mat.scattCoeff.values)

	def __str__(self):
		return '\n'.join([mat.__str__() for mat in self._materials.values()]) + '\n'

	def getDataFrame(self):
		all_df = []
		for mat in self._materials.values():
			all_df.append(mat.getDataFrame())
		return pd.concat(all_df)
		

	@property
	def materials(self):
		return self._materials.values()	

	def __getitem__(self, name):
		if isinstance(name, Iterable):
			return tuple(self._materials[n] for n in name)
		else:
			return self._materials[name]
	
	@property
	def vectorizedAbs(self):
		absCoeffs = [] 
		for mat in self._materials.values():
			absCoeffs.extend(mat.absCoeff.values)
		return absCoeffs
	@vectorizedAbs.setter
	def vectorizedAbs(self, x):
		if len(x) != self._NparamsAbs:
			raise ValueError(f"{self._NparamsAbs} values expected, received {len(x)}")
		idx = 0
		for mat in self._materials.values():
			for f in mat.absCoeff.frequencies():
				mat.absCoeff[f] = x[idx]
				idx += 1

	@property
	def vectorizedScatt(self):
		scattCoeffs = []
		for mat in self._materials.values():
			scattCoeffs.extend(mat.scattCoeff.values)
		return scattCoeffs
	@vectorizedScatt.setter
	def vectorizedScatt(self, x):
		if len(x) != self._NparamsScatt:
			raise ValueError(f"{self._NparamsScatt} values expected, received {len(x)}")
		idx = 0
		for mat in self._materials.values():
			for f in mat.scattCoeff.frequencies():
				mat.scattCoeff[f] = x[idx]
				idx += 1

	@property
	def vectorizedParams(self):
		# concatenate vectorized Abs and Scatt
		return self.vectorizedAbs + self.vectorizedScatt
	@vectorizedParams.setter
	def vectorizedParams(self, x):
		if len(x) != self._Nparam:
			raise ValueError(f"{self._Nparam} must be set, received {len(x)}")
		self.vectorizedAbs = x[0:self._NparamsAbs]
		self.vectorizedParams = x[self.NparamsAbs:]


