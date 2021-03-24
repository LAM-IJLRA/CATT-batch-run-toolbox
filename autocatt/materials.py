import re
import pathlib
import numpy as np
import fileinput # to modify file inplace with re
import numbers
#import materialsGUI

patternMatName = r"([A-Za-z0-9_]+)"
pattern0to100 = r"0*(?:[1-9]?[0-9]|100)" # only integer from 0 to 100 with possible leading zeros
patternGrpNbrs = r"<(\s*(?:" + pattern0to100 + r"\s*){6,8})>"
patternLine = r"^\s*ABS\s*[a-zA-Z0-9_-]+\s*=\s*" + patternGrpNbrs + r"(?:\s*L\s*" + patternGrpNbrs + r"\s*)?"

class FreqBandValues:
	def __init__(self, values, callback=None):
		firstFreq = 125
		freqs = [int(firstFreq*2**(x)) for x in range(len(values))]
		self._values = dict(zip(freqs, values))
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
				raise ValueError(f"Unkonw frequency {freqs}")
			self._values[freqs] = vals

		if self.callback is not None:
			self.callback()

	def values(self):
		return list(self._values.values())

	def frequencies(self):
		return list(self._values.keys())
			
		
		
		

class Material:
	def __init__(self, name, filenames = ()):
		self._name = name
		self._absCoeff = []
		self._scattCoeff = []
		self._filenames = filenames

		self._pattern = r"^\s*ABS\s*" + self._name + r"\s*=\s*" + patternGrpNbrs + r"(?:\s*L\s*" + patternGrpNbrs + r")?"
		self._patternComp = re.compile(self._pattern)

		# pattern used to replace the content of abs coeffs only
		# new values must be inserted between 1st and 2nd group 
		self._patternShort = r"(^\s*ABS\s*" + self._name + r"\s*=\s*<)[\d\s]*(>.*$)"
		self._patternShortComp = re.compile(self._patternShort)

		# pattern used to replace the content of abs coeffs and scatt coeffs
		# new values for abs coeffs must be inserted between 1st and 2nd group 
		# new values for scatt coeffs must be inserted between 2nd and 3nd group 
		self._patternLong = r"(^\s*ABS\s*" + self._name + r"\s*=\s*<)[\d\s]*(>\s*L\s*<)[\d\s]*(>.*$)"
		self._patternLongComp = re.compile(self._patternLong)



		# import values for absCoeff and scattCoeff from files
		self.importValuesFromFiles()

	def __str__(self):
		return f"Material '{self._name}'\nabs coeff: {*self._absCoeff.values(),}\nscatt coeff: {*self._scattCoeff.values(),}"

	
	@property
	def absCoeff(self):
		return self._absCoeff

	@property
	def scattCoeff(self):
		return self._scattCoeff

	def importValuesFromFiles(self):
		with fileinput.input(files=self._filenames) as f:
			for line in f:
				if (x := self._patternComp.findall(line)):
					if "absCoeff" in locals():
						raise RuntimeError("Material seems to be defined more than once in the files")
					absCoeff = [int(s) for s in x[0][0].strip().split(' ')]
					scattCoeff = [int(s) for s in x[0][1].strip().split(' ') if x[0][1]]

		self._absCoeff = FreqBandValues(absCoeff, callback = self.updateValuesInFile)
		self._scattCoeff = FreqBandValues(scattCoeff, callback = self.updateValuesInFile)


	def updateValuesInFile(self):
		newStrAbsCoeffs = ' '.join([str(int(x)) for x in self._absCoeff.values()])

		if not bool(self._scattCoeff.values()):
			# only needs to modify abs coeffs
			with fileinput.input(files = self._filenames, inplace = True) as f:
				for line in f:
					line = self._patternShortComp.sub(r"\g<1>" + newStrAbsCoeffs + r" \g<2>", line.rstrip())
					print(line)
		else:
			# both abs coeffs AND scatt coeffs are updated
			newStrScattCoeffs = ' '.join([str(int(x)) for x in self._scattCoeff.values()])
			with fileinput.input(files = self._filenames, inplace = True) as f:
				for line in f:
					line = self._patternLongComp.sub(r"\g<1>" + newStrAbsCoeffs + r" \g<2>" + newStrScattCoeffs + r"\3", line.rstrip())
					print(line)



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


	
