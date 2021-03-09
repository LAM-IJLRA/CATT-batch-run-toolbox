import re
import pathlib
import numpy as np
import fileinput # to modify file inplace with re

class Material:
	def __init__(self, name, absCoeff, scatCoeff = [], filename = None):
		self.name = name
		self.absCoeff = absCoeff
		self.scatCoeff = scatCoeff
	def __str__(self):
		return f"Material '{self.name}'\nabs coeff: {*self.absCoeff,}\nscatt coeff: {*self.scatCoeff,}"


class MaterialFileModifier:
	def __init__(self, filename):
		if isinstance(filename, pathlib.Path):
			self.__filename = filename
		else:
			self.__filename = pathlib.Path(filename)
		self.__M = readAllMaterials(self.__filename)
		#self.__updateFromFile()
		self.__updateStatusVectorInfo()

	def __str__(self):
		# return formatted string with information about all materials
		string = ""
		string = string + "{:<20}".format("MATERIALS")
		for ff in [125, 250, 500, 1000, 2000, 4000, 8000, 16000]: 
			string += f"{ff:^12}"
		for matName in self.__M:
			string += "\n"
			string += "{:<20s}".format(matName)
			if "scatCoeff" not in self.__M[matName] or not self.__M[matName]["scatCoeff"]:
				for	absCoeff in self.__M[matName]["absCoeff"]:
					string += f"  {absCoeff:>3d}{'':7}"
			else:
				for	absCoeff, scatCoeff in zip(self.__M[matName]["absCoeff"], self.__M[matName]["scatCoeff"]): 
					string += f"  {absCoeff:>3d} ({scatCoeff:>3d}) "
		return string

	def __updateStatusVectorInfo(self):
		info = {}
		idx = 0
		for matName in self.__M: # iterate along keys of dictionary
			idxEnd = idx + len(self.__M[matName]["absCoeff"]) - 1
			info[matName] = {"absCoeff": {"startIdx": idx, "endIdx": idxEnd}}
			idx = idxEnd + 1
		for matName in self.__M:
			if self.__M[matName]["scatCoeff"]:
				idxEnd = idx + len(self.__M[matName]["scatCoeff"]) - 1
				info[matName]["scatCoeff"] = {"startIdx": idx, "endIdx": idxEnd}
				idx = idxEnd + 1
		self.__statusVectorInfo = info

	def getStatusVector(self, getInfo=True):
		# return vector containing all parameters (absCoeff and scatCoeff), these are created from
		# status vector format:
		# all absorption coefficients are serialized material after material.
		# If scatt coefficients must be included, then all scattering 
		# coefficients are serialized mat after mat and appended at the end of 
		# the vector
		matAbs =  np.hstack([self.__M[matName]["absCoeff"] for matName in self.__M])
		matScatt = np.hstack([self.__M[matName]["scatCoeff"] for matName in self.__M if self.__M[matName]["scatCoeff"]])
		mat = np.hstack([matAbs, matScatt])

		if getInfo:
			return mat, self.__statusVectorInfo
		else:
			return mat

	def setStatusVector(self, x):
		# set all absorption and scattering coefficient from a vector
		if any(y < 0 and y > 0 for y in x): raise ValueError("values must lie within [0, 100]")
		for matName in self.__M:
			print(f"setting material {matName} properties")
			for coeffType in ["absCoeff", "scatCoeff"]:
				if self.__M[matName][coeffType]:
					startIdx = self.__statusVectorInfo[matName][coeffType]["startIdx"]
					endIdx = self.__statusVectorInfo[matName][coeffType]["endIdx"]
					print(f"start idx :{startIdx}")
					print(f"end idx : {endIdx}")
					self.__M[matName][coeffType] = x[startIdx:endIdx+1].astype(int).tolist()
		self.updateFile()	
		
	def updateFile(self):
		# abs coeff
		for matName in self.__M:
			newStrAbs = ' '.join([str(x) for x in self.__M[matName]["absCoeff"]])
			if "scatCoeff" not in self.__M[matName] or not bool(self.__M[matName]["scatCoeff"]):
				pattern = re.compile(r"(^\s*ABS\s*" + matName + r"\s*=\s*)<[\d\s]*>(.*)$")
				for line in fileinput.input(self.__filename, inplace = True):
					line = pattern.sub(r"\1<" + newStrAbs + r" >\2", line.rstrip())
					print(line)
			else: # modify both abs and scat coefficients
				pattern = re.compile(r"(^\s*ABS\s*" + matName + r"\s*=\s*)<[\d\s]*>\s*L\s*<[\d\s]*>(.*)$")
				newStrScat = ' '.join([str(x) for x in self.__M[matName]["scatCoeff"]])
				for line in fileinput.input(self.__filename, inplace = True):
					line = pattern.sub(r"\1<" + newStrAbs + r" > L <" + newStrScat + r" >\2", line.rstrip())
					print(line)
		
	def __getitem__(self, x):
		# get coefficient for specific material and frequency band	
		if len(x) == 2:
			matName, freqIdx = x
			coeffType = "absCoeff"
		elif len(x) == 3:
			matName, freqIdx, coeffType = x
		else:
			raise ValueError("invalid argument")

		return self.__M[matName][coeffType][freqIdx]

	def __setitem__(self, x, y):
		# set coefficient for specific material and frequency band
		if len(x) == 2:
			matName, freqIdx = x
			coeffType = "absCoeff"
		elif len(x) == 3:
			matName, freqIdx, coeffType = x
		else:
			raise ValueError("invalid argument")

		if y < 0 or y > 100: raise ValueError("value must lie within [0, 100]")

		if matName in self.__M and self.__M[matName][coeffType] and len(self.__M[matName][coeffType]) > freqIdx:
			self.__M[matName][coeffType][freqIdx] = y
		else:
			raise IndexError("cannot set this parameter")
		self.updateFile()

	

		
	







def readAllMaterials(filename):
# return a list of all materials found in a given geo file
#
# zagala - 03.03.2021
	
	# group1 is material name
	# group2 is absorption coefficients 
	# group3 is scattering coefficients (optional)
	patternMatName = r"([A-Za-z0-9_]+)" # alpha num with "_"
	pattern0to100 = r"0*(?:[1-9]?[0-9]|100)" # only 0 to 100 with optional leading 0s
	patternGrpNbrs = r"<(\s*(?:" + pattern0to100 + r"\s*){6,8})>"
	pattern = r"^\s*ABS\s+" + patternMatName + "\s*=\s*" + patternGrpNbrs + r"(?:\s*L\s*" + patternGrpNbrs + ")?"

#	if format == "dict":
#		formatOutput = lambda name, abso, scat : {"name":name, "absCoeff": abso, "scatCoeff":scat }
#	elif format == "obj":
#		formatOutput = lambda name, abso, scat : Material(name, abso, scat)
#	elif format == "tuple":
#		formatOutput = lambda name, abso, scat : (name, abso, scat)
#
#	A = [formatOutput(x[0][0],
#		[int(s) for s in x[0][1].strip().split(' ')],
#		[int(s) for s in x[0][2].strip().split(' ') if x[0][2]])
#		for line
#		in open("testMATERIAUX")
#		if (x := re.findall(pattern, line))]


	A = {x[0][0]:
		{"absCoeff": [int(s) for s in re.split("\s+", x[0][1].strip())],
		"scatCoeff": [int(s) for s in re.split("\s+", x[0][2].strip()) if x[0][2]]}
		for line
		in open(filename)
		if (x := re.findall(pattern, line))}

	print(A)

	return A


def readMaterial(filename, material, format="dict"):

	# group1 is absorption coefficients 
	# group2 is scattering coefficients (optional)
	patternMatName = material
	pattern0to100 = r"0*(?:[1-9]?[0-9]|100)" # only 0 to 100 with optional leading 0s
	patternGrpNbrs = r"<((?:" + pattern0to100 + r"\s?){6,8})>"
	pattern = r"^\s*ABS\s" + patternMatName + "\s=\s" + patternGrpNbrs + r"(?:\s?L\s" + patternGrpNbrs + ")?"


	if format == "dict":
		formatOutput = lambda abso, scat : {"absCoeff": abso, "scatCoeff":scat }
	elif format == "tuple":
		formatOutput = lambda abso, scat : (abso, scat)

	A = [formatOutput([int(s) for s in x[0][0].strip().split(' ')],
		[int(s) for s in x[0][1].strip().split(' ') if x[0][1]])
		for line
		in open("testMATERIAUX")
		if (x := re.findall(pattern, line))]
	
	if len(A) > 1:
		raise("Material is defined more than once")
	
	return A



