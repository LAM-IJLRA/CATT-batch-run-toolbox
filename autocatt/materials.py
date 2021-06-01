import re
from itertools import zip_longest
import fileinput
import autocatt.projects
import pathlib



patternMatName = r"(?P<MaterialName>[a-zA-Z][a-zA-Z0-9_]{0,15})" # max 15 characters, first must be a letter, trailing ones can be also numbers or '_'
patternInt0to100 = r"(?<![\d-])0*(?:[1-9]?[0-9]|100)(?!\d)" # only integer from 0 to 100 with possible leading zeros
patternFloat0to1 = r"(?<![\d-])0*(?:\.\d*|\.\d*|1|1\.\d*)?(?!\d)" # only floating point between 0 and 1
patternFloatPos = r"(?:(?:\d+\.\d+)|(?:\.\d+)|\d+)"

patternInt0to255 = r"(?<![\d-])(?:1?[0-9]{1,2}|2[0-4][0-9]|25[0-5])(?!\d)"
patternColor = r"{[ \t]*(?P<ColorRGB>(?:" + patternInt0to255 + r"[ \t]*){3})}"
patternColorOpt = r"(?:" + patternColor + r")?"

# RE patterns for number groups
patternGrpNbr0to100 = r"[ \t]*(?:" + patternInt0to100 + r"[ \t]*){6}(?::[ \t]*(?:" + patternInt0to100 + r"[ \t]*){0,2})?"
patternGrpNbr0to100slash = r"[ \t]*(?:" + patternInt0to100 + r"\/" + patternInt0to100 + r"[ \t]*){6}(?::[ \t]*(?:" + patternInt0to100 + r"\/" + patternInt0to100 + r"[ \t]*){0,2})?"

patternGrpNbr0to1 = r"[ \t]*(?:" + patternFloat0to1 + r"[ \t]*){6}(?::[ \t]*(?:" + patternFloat0to1 + r"[ \t]*){0,2})?"
patternGrpNbr0to1slash = r"[ \t]*(?:" + patternFloat0to1 + r"\/" + patternFloat0to1 + r"[ \t]*){6}(?::[ \t]*(?:" + patternFloat0to1 + r"\/" + patternFloat0to1 + r"[ \t]*){0,2})?"

patternScattEstimate = r"<[ \t]*estimate\([ \t]*(?P<scattCoeffEstimate>" + patternFloatPos + r")[ \t]*\)[ \t]*>"

# re patterns for abs, abs-transparency, and scattering
patternAbs = r"<[ \t]*(?P<absCoeff>" + patternGrpNbr0to100 + r")[ \t]*>"
patternAbsTransp = r"<[ \t]*(?P<absTranspCoeff>" + patternGrpNbr0to100slash + r")[ \t]*>"
patternAbsOrAbsTransp = r"(?:(?:" + patternAbs + r")|(?:" + patternAbsTransp + r"))"
patternScatt = r"<[ \t]*(?P<scattCoeff>" + patternGrpNbr0to100 + r")[ \t]*>"
patternScatt = r"(?:(?:" + patternScatt + ")|(?:" + patternScattEstimate + "))"

patternAbs1 = r"<[ \t]*(?P<absCoeff>" + patternGrpNbr0to1 + r")[ \t]*>"
patternAbsTransp1 = r"<[ \t]*(?P<absTranspCoeff>" + patternGrpNbr0to1slash + r")[ \t]*>"
patternAbsOrAbsTransp1 = r"(?:(?:" + patternAbs1 + r")|(?:" + patternAbsTransp1 + r"))"
patternScatt1 = r"<[ \t]*(?P<scattCoeff>" + patternGrpNbr0to1 + r")[ \t]*>"
patternScatt1 = r"(?:(?:" + patternScatt1 + ")|(?:" + patternScattEstimate + "))"

patternLambertType = r"(?P<LambertType>L1?)"

patternContent100 = patternAbsOrAbsTransp + r"[ \t]*(?:" + patternLambertType + r"[ \t]*" + patternScatt + r")?[ \t]*" + patternColorOpt + "(?P<Comments>.*)?"
patternContent1 = patternAbsOrAbsTransp1 + r"[ \t]*(?:" + patternLambertType + r"[ \t]*" + patternScatt1 + r")?[ \t]*" + patternColorOpt + "(?P<Comments>.*)?"



class FreqDependentValues:
	# values are stored as floating point values
	frequencies = [125, 250, 500, 1000, 2000, 4000, 8000, 16000]
	def __init__(self, *args, defaultValue = 0.0, callback = None):
		vals = args[0] if args else []
		assert len(vals) <= len(FreqDependentValues.frequencies)
		self._dictionary = dict(zip_longest(FreqDependentValues.frequencies, vals, fillvalue = defaultValue))
		self._callback = callback
	def __str__(self):
		return str(self._dictionary)
	def __setitem__(self, key, item):
		if key not in self._dictionary:
			raise KeyError(f"Frequency {key} is not defined.")
		assert (item >= 0.0) and (item <= 1.0)
		self._dictionary[key] = float(item)
		if self._callback is not None:
			self._callback()
	def __getitem__(self, key):
		return self._dictionaryValues[key]
	def setFromArray(self, x):
		for ii in range(len(x)):
			self[FreqDependentValues.frequencies[ii]] = x[ii]
	def getArray(self, n = 8):
		return list(self._dictionary.values())[0:n]	


		

class SingleMaterialWrapper:
	frequencies = FreqDependentValues.frequencies
	def __init__(self, name, filenames):
		assert re.fullmatch(patternMatName, name)
		self._name = name
		self._filenames = filenames

		self._absCoeff = FreqDependentValues(callback = self.updateFile)
		self._transpCoeff = FreqDependentValues(callback = self.updateFile)
		self._scattCoeff = FreqDependentValues(callback = self.updateFile)

		self._color = [255, 255, 255]

		self._isAudience = False
		self._floatFormat = False

		self._transpDefined = False
		self._scattDefined = True
		self._colorDefined = False

		self._nbrAbsTranspCoeffs = 6

		self._lambert1D = False
		self._nbrScattCoeffs = 6
		self._estimateScatt = False
		self._scattRoughness = 0.1

		self._isReading = False # just to make sure one does not try to write in the file while reading it

		self._patternPrime = re.compile(r"^[ \t]*(?P<Audience>AUD)?ABS(?P<FloatFormat>1)?[ \t]*" + self._name + r"[ \t]*=[ \t]*(?P<Content>.*)$")

		self._comments = ""

		self.updateFromFile()

	def __str__(self):
		return (
			f"ABS\n"
			f"{self.absCoeff}\n"
			f"TRANSP\n"
			f"{self.transpCoeff}\n"
			f"SCATT\n"
			f"{self.scattCoeff}\n"
			f"COLOR\n"
			f"{self._color}\n"
			f"{self.scattDefined=}"
			f"{self.estimateScatt=}")
	
	@property
	def name(self):
		return self._name
	
	@property
	def filenames(self):
		return self._filenames

	@property
	def absCoeff(self):
		return self._absCoeff

	@property
	def transpCoeff(self):
		return self._transpCoeff

	@property
	def scattCoeff(self):
		return self._scattCoeff

	@property
	def nbrAbsTranspCoeffs(self):
		return self._nbrAbsTranspCoeffs
	@nbrAbsTranspCoeffs.setter
	def nbrAbsTranspCoeffs(self, x):
		assert x == 6 or x == 7 or x == 8
		self._nbrAbsTranspCoeffs = x
		self.updateFile()

	@property
	def nbrScattCoeffs(self):
		return self._nbrScattCoeffs
	@nbrScattCoeffs.setter
	def nbrScattCoeffs(self, x):
		assert x == 6 or x == 7 or x == 8
		self._nbrScattCoeffs = x
		self.updateFile()
	
	@property
	def transpDefined(self):
		return self._transpDefined
	@transpDefined.setter
	def transpDefined(self, x):
		assert x is True or x is False
		self._transpDefined = x
		self.updateFile()

	@property
	def scattDefined(self):
		return self._scattDefined
	@scattDefined.setter
	def scattDefined(self, x):
		assert x is True or x is False
		self._scattDefined = x
		self.updateFile()

	@property
	def colorDefined(self):
		return self._colorDefined
	@colorDefined.setter
	def colorDefined(self, x):
		assert x is True or x is False
		self._colorDefined = x
		self.updateFile()
		print("colorDefined:", self._colorDefined)

	@property
	def floatFormat(self):
		return self._floatFormat
	@floatFormat.setter
	def floatFormat(self, x):
		assert x is True or x is False
		self._floatFormat = x
		self.updateFile()

	@property
	def color(self):
		return self._color
	@color.setter
	def color(self, x):
		assert len(x) == 3
		assert all([xx <= 255 and xx >= 0] for xx in x)
		self._color = [int(xx) for xx in x]
		self.updateFile()

	@property
	def isAudience(self):
		return self._isAudience
	@isAudience.setter
	def isAudience(self, x):
		assert x is True or x is False
		self._isAudience = x
		self.updateFile()

	@property
	def lambert1D(self):
		return self._lambert1D
	@lambert1D.setter
	def lambert1D(self, x):
		assert x is True or x is False
		self._lambert1D = x
		self.updateFile()

	@property
	def estimateScatt(self):
		return self._estimateScatt == 1
	@estimateScatt.setter
	def estimateScatt(self, x):
		assert x is True or x is False
		self._estimateScatt = x
		self.updateFile()

	@property
	def scattRoughness(self):
		return self._scattRoughness
	@scattRoughness.setter
	def scattRoughness(self, x):
		assert x > 0.0
		self._scattRoughness = float(x)
		self.updateFile()

	def updateFromFile(self):
		# search stops after finding first instance of material, 
		# it does not check whether the material is defined more than once
		with fileinput.input(files = self._filenames, mode = 'r') as f:
			for line in f:
				if (x := self._patternPrime.search(line)):
					self.updateFromMatch(x)
					return
		raise RuntimeError(f"material '{self._name}' does not exist or is badly formatted")

	def updateFromMatch(self, match):
		self._isReading = True
		self.isAudience = match.group("Audience") == "AUD"
		self.floatFormat = match.group("FloatFormat") == "1"

		if self._floatFormat:
			content = re.search(patternContent1, match.group("Content"))
		else:
			content = re.search(patternContent100, match.group("Content"))

		assert content is not None

		self.transpDefined = content.group("absTranspCoeff") is not None
		self.colorDefined = content.group("ColorRGB") is not None


		# abs and transp coeffs
		if self._transpDefined:
			assert content.group("absTranspCoeff") is not None
			absTranspCoeff = [float(aa) if self._floatFormat else int(aa)/100.0 for aa in re.split(r"(?:[ \t]*:[ \t]*)|\/|[ \t]+", content.group("absTranspCoeff").strip())]
			print(absTranspCoeff)
			assert len(absTranspCoeff) % 2 == 0
			absCoeff, transpCoeff = (absTranspCoeff[ii::2] for ii in [0, 1])
			self.transpCoeff.setFromArray(transpCoeff)
		else:
			assert content.group("absCoeff") is not None
			absCoeff = [float(aa) if self._floatFormat else int(aa)/100.0 for aa in re.split(r"(?:[ \t]*:[ \t]*)|[ \t]+", content.group("absCoeff").strip())]

		self.nbrAbsTranspCoeffs = len(absCoeff)
		self.absCoeff.setFromArray(absCoeff)

		# scatt coeffs
		print(content)
		print(content.groupdict())
		if content.group("scattCoeff") is not None:
			self.scattDefined = True
			scattCoeff = [float(aa) if self._floatFormat else int(aa)/100.0 for aa in re.split(r"(?:[ \t]*:[ \t]*)|[ \t]+", content.group("scattCoeff").strip())]
			self.lambert1D = content.group("LambertType") == "L1"
			self.nbrScattCoeffs = len(scattCoeff)
			self.scattCoeff.setFromArray(scattCoeff)
			self.estimateScatt = False
			print("cas 1")
		elif content.group("scattCoeffEstimate") is not None:
			self.scattDefined = True
			self.lambert1D = content.group("LambertType") == "L1"
			self.estimateScatt = True
			self.scattRoughness = float(content.group("scattCoeffEstimate"))
			print("cas 2")
		else:
			self.scattDefined = False
			print("cas 3")

		# color
		if self.colorDefined:
			color = [int(s) for s in re.split(r"[ \t]+", content.group("ColorRGB").strip())] 
			self.color = color

		self._comments = content.group("Comments")

		self._isReading = False

	
	def updateFile(self):
		if self._isReading is False:
			with fileinput.input(files = self._filenames, inplace = True) as f:
				for line in f:
					if (x := self._patternPrime.match(line)):
						try:
							newLine = self.createLine()
						except:
							# in case of error, make sure the rest of the file is not erased
							from datetime import date
							print("; (!!) potential error in next line caused by 'autocatt' (" + now.strftime('%d/%m/%Y %H:%M:%S') + ")")
							newline = line.rstrip()
					else:
						newLine = line.rstrip()
					print(newLine, end = '\r\n')



	def _createNumGroupString(self, x):
		if len(x) > 6:
			x.insert(6, ':')
		if self.floatFormat:
			return ' '.join([str(xx) for xx in x])
		else:
			return ' '.join([str(int(round(xx * 100))) if xx != ':' else xx for xx in x])

	def _createAbsString(self):
		return self._createNumGroupString(self.absCoeff.getArray(self.nbrAbsTranspCoeffs))
	
	def _createScattString(self):
		if self.estimateScatt:
			return " estimate(" + str(self.scattRoughness) + ")"
		else:
			return self._createNumGroupString(self.scattCoeff.getArray(self.nbrScattCoeffs))

	def _createAbsTranspString(self):
		a = zip([str(xx) if self.floatFormat else str(int(round(xx * 100))) 
				for xx in self.absCoeff.getArray()[0:self.nbrAbsTranspCoeffs]], 
				[str(xx) if self.floatFormat else str(int(round(xx * 100))) 
				for xx in self.transpCoeff.getArray()[0:self.nbrAbsTranspCoeffs]])
		b = ['/'.join(xx) for xx in list(a)]
		if len(b) > 6:
			b.insert(6, ':')
		return ' '.join(b)


	def _createColorString(self):
		return ' '.join([str(cc) for cc in self.color])

	def createLine(self, comments = None):
		line = ""

		if self.isAudience:
			line += "AUD"

		line += "ABS"

		if self.floatFormat:
			line += "1"

		line += (" " + self._name + " = ")

		if self.transpDefined:
			line += ("<" + self._createAbsTranspString() + " >")
		else:
			line += ("<" + self._createAbsString()  + " >")

		if self.scattDefined:
			if self._lambert1D:
				line += " L1 "
			else:
				line += " L "
			line += ("<" + self._createScattString() + " >")

		if self.colorDefined:
			line += (" {" + self._createColorString() + "}")

		if self._comments:
			line += self._comments

		return line



class ProjectMaterialsWrapper:
	def __init__(self, proj):
		if isinstance(proj, autocatt.projects.MD9Wrapper):
			self._filenames = autocatt.projects.getAllNestedGeoFiles(proj.masterGeoFile)
		elif isinstance(proj, str) or isinstance(proj, pathlib.Path):
			self._filenames = autocatt.projects.getAllNestedGeoFiles(proj)
		else:
			self._filenames = proj

		self._pattern = re.compile(r"^[ \t]*(?:AUD)?ABS1?[ \t]*" + patternMatName + r"[ \t]*=[ \t]*<.*>.*")
		self.getAllMaterialsFromFiles()

	def getAllMaterialsFromFiles(self):
		self._materials = dict()
		with fileinput.input(self._filenames, mode = 'r') as f:
			for line in f:
				if (x := self._pattern.search(line)):
					name = x.group("MaterialName")
					if name in self._materials:
						raise(f"Material {name} is defined more than once")
					self.materials[name] = None
		# sort dictionary
		self._materials = dict(sorted(self._materials.items()))
		
		for kk in self._materials.keys():
			# singleMaterialWrapper are constructed only now, to ensure that their creation does not interfere with the reading of the files above
			print(f"creating material wrapper for '{kk}'")
			self._materials[kk] = SingleMaterialWrapper(kk, self._filenames)

	@property
	def materials(self):
		return self._materials

	def getDataFrame(self):
		import pandas as pd
		lst = []
		for matName, mat in self.materials.items():
			lst.append({"material": matName, "command": mat.createLine()})
		return pd.DataFrame(lst)

		

					
		

	



		
					

						

						




#A = SingleMaterialWrapper('haha', 'testFileInput/text1.txt')	
#A.updateFromFile()
#print(A)
##print('$$$$$')
#print(A.createLine())
#A.transpDefined = False
#A.floatFormat = True
##A.isAudience = False
#A.lambert1D = False
#A.estimateScatt = True
##print(A.createLine())
#
#
##B = ProjectMaterialsWrapper("testFileInput/text1.txt")
##print(B.materials)
			


