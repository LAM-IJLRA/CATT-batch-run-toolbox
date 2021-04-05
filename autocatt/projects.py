# This script contains functions and objects relative to CATT and TUCT projects configurations
# zagala - 04.03.2021

import re
import pathlib
import fileinput
import autocatt.materials
import struct
from bitarray import bitarray
import string
import warnings



class MD9Prop:
	def __init__(self, parent, byteStart, byteEnd, byteStep):
		self._byteStart = byteStart
		self._byteEnd = byteEnd
		self._byteStep = byteStep
		self._parent = parent
	@property
	def byteWidth(self):
		return self._byteEnd - self._byteStart
	@property
	def numElements(self):
		return self.byteWidth // self._byteStep
	def _readBytesFromFile(self):
		currSlice = slice(self._byteStart, self._byteEnd, 1)
		with open(self._parent._filename, 'rb') as f:
			return f.read()[currSlice]
	def _writeBytesToFile(self, x):
		if len(x) > self.byteWidth:
			x = x[:self.byteWidth]
			warnings.warn("Byte sequence is too long for this property, extra bytes ignored.")
		with open(self._parent._filename, 'r+b') as f:
			f.seek(self._byteStart)
			f.write(x)

class MD9Prop_bits(MD9Prop):
	def __init__(self, parent, byteStart, byteEnd, endian = "little"):
		super().__init__(parent, byteStart, byteEnd, 1)
		self.endian = "little"
	def readBitsFromFile(self):
		bytes = self._readBytesFromFile()
		bits = bitarray(endian = self.endian)
		bits.frombytes(bytes)
		return bits
	def writeBitsToFile(self, bits):
		bits = bitarray(bits, endian = self.endian)
		self._writeBytesToFile(bits.tobytes())


class MD9Prop_bitsArray(MD9Prop_bits):
	# used for receivers which are index from 0 to 100
	def __init__(self, parent, byteStart, byteEnd, **kwargs):
		super().__init__(parent, byteStart, byteEnd, **kwargs)
	def readBitsFromFile(self):
		bits = super().readBitsFromFile()
		return bits.tolist()
	def writeBitsToFile(self, bitsAr):
		bits = bitarray(bitsAr, endian = self.endian)
		super().writeBitsToFile(bits.to01())
	def __getitem__(self, idx):
		return self.readBitsFromFile()[idx]
	def __setitem__(self, idx, value):
		bitsAr = self.readBitsFromFile()
		bitsAr[idx] = value
		self.writeBitsToFile(bitsAr)
	
	

class MD9Prop_bitsMatrix(MD9Prop_bits):
	# used for sources which are indexes by (alpha, int)
	def __init__(self, parent, byteStart, byteEnd, ncols = 10, **kwargs):
		super().__init__(parent, byteStart, byteEnd, **kwargs)
		self._ncols = ncols
	def readBitsFromFile(self):
		bits = super().readBitsFromFile()
		boolValues = bits.tolist()
		bitsAr = [boolValues[i : i + self._ncols] for i in range(0, len(boolValues), self._ncols)]
		return bitsAr
	def writeBitsToFile(self, bitsAr):
		# bool array to bits list
		boolValues = [b for row in bitsAr for b in row]
		bits = bitarray(boolValues, endian = self.endian)
		super().writeBitsToFile(bits.to01())

	@staticmethod
	def _letterToIndex(letter):
		# could be a letter of "letter-slice"
		if isinstance(letter, slice):
			if (letter.start.isalpha() == False or 
				letter.stop.isalpha() == False):
				raise ErrorValue("input must be a letter (alpha)")

			start = ord(letter.start.lower()) - 97
			stop = ord(letter.stop.lower()) - 97
			idx = slice(start, stop, 1) 
		else:
			if letter.isalpha() == False:
				raise ErrorValue("input must be a letter (alpha)")
			idx = ord(letter.lower()) - 97
		return idx 
	def __getitem__(self, xy):
		# xy is a tuple (alpha, int)
		x, y = xy
		x = self._letterToIndex(x)
		return self.readBitsFromFile()[x][y]
	def __setitem__(self, xy, value):
		x, y = xy
		x = self._letterToIndex(x)
		bitsAr = self.readBitsFromFile()
		bitsAr[x][y] = value
		self.writeBitsToFile(bitsAr)




		

class MD9Prop_string(MD9Prop):
	def __init__(self, parent, byteStart, byteEnd, encoding = "latin1"):
		if encoding == "latin1":
			byteStep = 0.5
		super().__init__(parent, byteStart, byteEnd, byteStep)
		self._encoding = encoding
	def readTextFromFile(self, trim = True):
		txt = self._readBytesFromFile()
		if trim:
			txt = txt.split(b'\x00', 1)[0]
		return txt
	def writeTextToFile(self, txt):
		if len(txt) > self.byteWidth // self._byteStep:
			txt = txt[:self.byteWidth]
		else:
			txt = txt.ljust(self.byteWidth, '\x00')
		self._writeBytesToFile(txt.encode(self._encoding))
		

class MD9Prop_num(MD9Prop):
# TODO: implement min / max
	def __init__(self, parent, byteStart, byteEnd, byteOrder = '<', format = 'f', min = float('-inf'), max = float('inf')):
		# refer to struct.pack fot byteOrder syntax
		super().__init__(parent, byteStart, byteEnd, 1) # value 1 is irrelevant as it will be reset by the property setter
		self._format = '' # need to initialize before calling format setter
		self.format = format
		self.byteOrder = byteOrder
		self.min, self.max = min, max
		if self.min > self.max:
			raise ValueError("min value cannot be greater than max value.")
	@property 
	def format(self):
		return self._format
	@format.setter
	def format(self, format):
		self._byteStep = self.getByteStepForFormat(format)
		self._format = format
	@property
	def byteOrder(self):
		return self._byteOrder
	@byteOrder.setter
	def byteOrder(self, byteOrder):
		if len((byteOrder,)) == 1 and byteOrder in "<>%@=!":
			self._byteOrder = byteOrder
	
	@property
	def formatCode(self):
		return self._byteOrder + self.format * self.numElements
		
	def readValueFromFile(self):
		code = self._readBytesFromFile()
		return struct.unpack(self.formatCode, code)
	def writeValueToFile(self, *args):
		args = list(args)
		for idx, a in enumerate(args):
			if a < self.min:
				warnings.warn(f"value {a} clipped to minimum {self.min}")
				args[idx] = self.min
			if a > self.max:
				warnings.warn(f"value {a} clipped to maximum {self.max}")
				args[idx] = self.max
		self._writeBytesToFile(struct.pack(self.formatCode, *args))

	@staticmethod
	def getByteStepForFormat(format):
		if format in 'fi':
			return 4
		elif format == 'd':
			return 8
		elif format in 'b?':
			return 1
		else:
			raise ValueError("Unrecognized format, maybe you could implement it?")


class MD9Prop_scalar(MD9Prop_num):
	def __init__(self, parent, byteStart, format = 'f', **kwargs):
		byteStep = super().getByteStepForFormat(format)
		super().__init__(parent, byteStart, byteStart + byteStep, format = format, **kwargs)


		
class MD9Prop_freqValues(MD9Prop_num):
	def __init__(self, parent, byteStart, format = 'f', **kwargs):	
		frequencies = [125, 250, 500, 1000, 2000, 4000, 8000, 16000]
		step = self.getByteStepForFormat(format)
		super().__init__(parent, byteStart, byteStart + step * len(frequencies), format = format, **kwargs)
		self._frequencies = frequencies
	def __getitem__(self, freq):
		idx = self._frequencies.index(freq)
		values = self.readValueFromFile()
		return values[idx]
	def __setitem__(self, freq, val):
		idx = self._frequencies.index(freq)
		values = list(self.readValueFromFile())
		values[idx] = val
		self.writeValueToFile(*tuple(values))


class MD9Prop_3Dvec(MD9Prop_num):
	def __init__(self, parent, byteStart, format = 'f', **kwargs):
		step = self.getByteStepForFormat(format)
		super().__init__(parent, byteStart, byteStart + step * 3, format = format, **kwargs)
	def __getitem__(self, idx):
		values = self.readValueFromFile()
		return values[idx]
	def __setitem__(self, idx, vals):
		values = list(self.readValueFromFile())
		values[idx] = vals
		self.writeValueToFile(*tuple(values))
	

		
class MD9Prop_planeSelection():
	def __init__(self, parent, byteStartList, bytePosNumOnlySome, bytePosNumWithoutSome, finalBytes = b'\x0A'):
		self._parent = parent
		self._byteStartList = byteStartList
		self._prop_numOnlySome = MD9Prop_num(parent, 0x0000064B, 0x0000064F, format = 'i')
		self._prop_numWithoutSome = MD9Prop_num(parent, 0x000008BF, 0x000008C3, format = 'i')
		self._prop_listOnlySome = MD9Prop_num(parent, self.byteStartOnlySome, self.byteEndOnlySome, format = 'i')
		self._prop_listWithoutSome = MD9Prop_num(parent, self.byteStartWithoutSome, self.byteEndWithoutSome, format = 'i')
		self._finalBytes = finalBytes
	@property
	def numOnlySome(self):
		return self._prop_numOnlySome.readValueFromFile()[0]
	@property
	def numWithoutSome(self):
		return self._prop_numWithoutSome.readValueFromFile()[0]
	@property
	def numTotal(self):
		return self.numOnlySome + self.numWithoutSome
	@property
	def byteStartOnlySome(self):
		return self._byteStartList
	@property
	def byteEndOnlySome(self):
		return self.byteStartWithoutSome
	@property
	def byteStartWithoutSome(self):
		return self._byteStartList + self.numOnlySome * 4
	@property
	def byteEndWithoutSome(self):
		return self.byteStartWithoutSome + self.numWithoutSome * 4
	

	@property
	def listOnlySome(self):
		return self._prop_listOnlySome.readValueFromFile()
	@listOnlySome.setter
	def listOnlySome(self, values):
		# modifying len of list "only" yiels to a shift of the list "without".
		# Therefore, the list "without" is stored prior to re-writing end file part
		self._prop_numOnlySome.writeValueToFile(len(values))

		# get values from withoutSome
		valuesWithout = sorted(self.listWithoutSome)
		self._clear(self.numTotal)

		self._prop_listOnlySome = MD9Prop_num(self._parent, 
				self.byteStartOnlySome, 
				self.byteEndOnlySome, 
				format = 'i')
		self._prop_listOnlySome.writeValueToFile(*sorted(values))

		self._prop_listWithoutSome = MD9Prop_num(self._parent, 
				self.byteStartWithoutSome, 
				self.byteEndWithoutSome, 
				format = 'i')
		self._prop_listWithoutSome.writeValueToFile(*valuesWithout)


	@property
	def listWithoutSome(self):
		return self._prop_listWithoutSome.readValueFromFile()
	@listWithoutSome.setter
	def listWithoutSome(self, values):
		self._prop_numWithoutSome.writeValueToFile(len(values))
		self._clear(self.numWithoutSome, fromSec = "without")
		self._prop_listWithoutSome = MD9Prop_num(self._parent, 
				self.byteStartWithoutSome, 
				self.byteEndWithoutSome, 
				format = 'i')
		self._prop_listWithoutSome.writeValueToFile(*sorted(values))


	def _clear(self, le, fromSec = "only"):
		# clear end of binary files and adjust size to desired length
		with open(self._parent._filename, 'rb+') as f:
			if fromSec == "only":
				f.seek(self.byteStartOnlySome)
			elif fromSec == "without":
				f.seek(self.byteStartWithoutSome)
			else:
				raise ValueError("Unkown mode for 'from', must be either 'only' or 'without'.")
			# write dummy values on desired bytes slice	
			f.write(b'\00' * le * 4)
			f.write(self._finalBytes)
			f.truncate()
			
		


		
				

class MD9Wrapper:
# Wrapper for MD9 file (CATT-acoustics)
# 
# To instantiate from an existing MD9.file:

# ```
# 	A = MD9Wrapper("project.MD9")
# ```
# 
#
# Project name and files:
# The following property are getable / setable:
# - projName 				string
# - inputFolder				string
# - outputFolder			string
# - masterGeoFile			string
# - receverLocFile			string
# - sourceLocFile			string
#
# Diffuse relfections:
# - diffReflMode 			among "off", "surface", "surface + edge" 
# - diffRelfUseDefault 		True or False
# - diffReflDefaultValues  	individual frequency can be set/get as follows:	
# 	```
#	A.diffReflDefaultValues[125] = 0.2
#	```
#
# Head direction:
# - headDirectionMode
# - headDirection 			individual component can be set/get as follows:
# 	```
#	A.headDirection[1:3] = [1, 0, 0]
#	xyz = A.headDirection[:]
#	A.headDirection = [7, 8, 9]
#	```
#
# Air properties:
# - temperature				air temperature in degree celsius
# - humidity				relative hmidity, in %
# - airDensity 				in kg/m^3
#
# Air absorption:
# - airAbsorptionMode 		among 'estimated', 'user defined', 'off', 'estimated + edge'
# - airAbsorptionUserValues	individual frequency values can be set/get as follows (in dB/m):
#	```
# 	A.airAbsorptionUserValues[16000] = -12.0
# 	```
# 
# Background noise:
# - backgroundNoiseLevelTotal 	(used for receivers for which noise level has not be individually defined) defined for each frequency band
# - backgroundNoiseLevelresidual (added to all sources for which background noise has been individually defined) defined for ech frequency band
# 
# Sources and receivers used:
# - sourcesUsed 			can be activated using a alphanumeric coordinates, e.g.
#	```
#	A.sourcesUsed['A', 0] = True
#	A.sourcesUsed['B':'E', 0] = True # activate the first sources of each group from B to E
#	```
# - receiversUsed 			can be activated using a numerci index, e.g.
#	```
#	A.receiversUsed[0:10] = True # activate the first 10 receivers
#	```	
#
# Planes selection
# - planeSelectionMode 		among 'only', or 'without'
# - planeSelection 			object used to manage list of planes for modes 'only', and 'without'
# 	```
# 	A.planeSelection.listOnlyWithSome = [0, 1, 2] # only planes 0, 1, and 2
# 	a = A.planeSelection.listOnlyWithoutSome # get indices of planes omitted when 'without' mode is activated
# 	```
# 
# zagala - 04.2021
	def __init__(self, filename):
		self._filename = filename
		
		self._prop_projName = MD9Prop_string(self, 0x00000008, 0x00000010D)
		self._prop_inputFolder = MD9Prop_string(self, 0x0000010D, 0x00000212)
		self._prop_outputFolder = MD9Prop_string(self, 0x00000212, 0x00000317)
		self._prop_masterGeoFile = MD9Prop_string(self, 0x00000317, 0x00000417)
		self._prop_receiverLocFile = MD9Prop_string(self, 0x00000417, 0x00000517)
		self._prop_sourceLocFile = MD9Prop_string(self, 0x00000517, 0x00000617)

		self._prop_diffReflMode = MD9Prop_num(self, 0x00000B34, 0x00000B36, format = '?')	
		self._prop_diffReflUseDefault = MD9Prop_scalar(self, 0x00000B36, format = '?')	
		self._prop_diffReflDefaultValues = MD9Prop_freqValues(self, 0x00000B37, format = 'f')

		self._prop_headDirectionMode = MD9Prop_scalar(self, 0x00000B57, format = 'b')
		self._prop_headDirection = MD9Prop_3Dvec(self, 0x00000B58, format = 'f')

		self._prop_temperature = MD9Prop_scalar(self, 0x0000B85, format = 'f', min = -20.0, max = 50)
		self._prop_humidity = MD9Prop_scalar(self, 0x0000B89, format = 'f', min = 0.0, max = 100.0)
		self._prop_airDensity = MD9Prop_scalar(self, 0x0000B8D, format = 'f', min = 1.0, max = 2.0)

		self._prop_airAbsorptionMode = MD9Prop_scalar(self, 0x00000B64, format = 'b')
		self._prop_airAbsorptionUserValues = MD9Prop_freqValues(self, 0x00000B65, format = 'f')

		self._prop_backgroundNoiseLevelTotal = MD9Prop_freqValues(self, 0x00000B91, format = 'f')
		self._prop_backgroundNoiseLevelResidual = MD9Prop_freqValues(self, 0x00000BB1, format = 'f')

		self._prop_sourcesUsed = MD9Prop_bitsMatrix(self, 0x00000627, 0x00000647, ncols = 10)
		self._prop_receiversUsed = MD9Prop_bitsArray(self, 0x00000617, 0x00000624)

		self._prop_planeSelectionMode = MD9Prop_scalar(self, 0x00000B33, format = 'i')
		self._prop_planeSelection = MD9Prop_planeSelection(self, 0x00001108, 0x0000064B, 0x000008BF)
		
	@property
	def projName(self):
		return self._prop_projName.readTextFromFile()
	@projName.setter
	def projName(self, name):
		self._prop_projName.writeTextToFile(name)

	@property
	def inputFolder(self):
		return self._prop_inputFolder.readTextFromFile()
	@inputFolder.setter
	def inputFolder(self, folder):
		self._prop_inputFolder.writeTextToFile(folder)

	@property
	def outputFolder(self):
		return self._prop_outputFolder.readTextFromFile()
	@outputFolder.setter
	def outputFolder(self, folder):
		self._prop_outputFolder.writeTextToFile(folder)

	@property
	def masterGeoFile(self):
		return self._prop_masterGeoFile.readTextFromFile()
	@masterGeoFile.setter
	def masterGeoFile(self, file):
		self._prop_masterGeoFile.writeTextToFile(file)

	@property
	def receiverLocFile(self):
		return self._prop_receiverLocFile.readTextFromFile()
	@receiverLocFile.setter
	def masterGeoFile(self, file):
		self._prop_receiverLocFile.writeTextToFile(file)

	@property
	def sourceLocFile(self):
		return self._prop_sourceLocFile.readTextFromFile()
	@sourceLocFile.setter
	def sourceLocFile(self, file):
		self._prop_sourceLocFile.writeTextToFile(file)

	@property
	def diffReflMode(self):
		content = self._prop_diffReflMode.readValueFromFile()
		diffSurface = bool(content[0])
		diffEdge = bool(content[1])
		if diffSurface is False:
			if diffEdge is False:
				return "off"
			else:
				raise RuntimeError("Edge diffraction requires surface diffraction to be activated")
		else: # surface diffraction is active
			if diffEdge is False:
	   			return "surface"
			else:
				return "surface + edge"	
	@diffReflMode.setter
	def diffReflMode(self, mode):
		if mode == "off":
			code = (False, False)
		elif mode == "surface":
			code = (True, False)
		elif mode == "surface + edge":
			code = (True, True)
		else:
			raise ValueError("Unknown diffuse reflection mode. It must be either 'off', 'surface', or 'surface + edge'")
		self._prop_diffReflMode.writeValueToFile(*code)

	@property
	def diffReflUseDefault(self):
		return self._prop_diffReflUseDefault.readValueFromFile()[0]
	@diffReflUseDefault.setter
	def diffReflUseDefault(self, value):
		self._prop_diffReflUseDefault.writeValueToFile(bool(value))

	@property
	def diffReflDefaultValues(self):
		# to call it 
		#  - index it with the frequency 
		# 		e.g. A.diffReflDefautValues[2000]
		#  		to get or set the value at 2000Hz
		return self._prop_diffReflDefaultValues

	@property
	def headDirectionMode(self):
		code = self._prop_headDirectionMode.readValueFromFile()[0]
		if code == 0:
			mode = "source"
		elif code == 1:
			mode = "stage"
		elif code == 2:
			mode = "fix"
		else:
			raise ValueError("Unkown headDirectionMode")
		return mode
	@headDirectionMode.setter
	def headDirectionMode(self, mode):
		if mode == "source":
			code = 0
		elif mode == "stage":
			code = 1
		elif mode == "fix":
			code = 2
		else:
			raise ValueError("Unknown head direction code")
		self._prop_headDirectionMode.writeValueToFile(code)
		
	@property
	def headDirection(self):
		return self._prop_headDirection
	@headDirection.setter
	def headDirection(self, values):
		if len(values) != 3:
			raise ValueError("head direction requires 3 values")
		self._prop_headDirection.writeValueToFile(*tuple(values))
		
	@property
	def temperature(self):
		return self._prop_temperature.readValueFromFile()[0]
	@temperature.setter
	def temperature(self, temp):
		if (temp < -20.0) or (temp > 50):
			raise ValueError("CATT does not accept temperatures outside the range [-20, 50] deg. Celsius")
		self._prop_temperature.writeValueToFile(temp)
	
	@property
	def humidity(self):
		return self._prop_humidity.readValueFromFile()[0]
	@humidity.setter
	def humidity(self, x):
		if (x < 0.0) or (x > 100):
			raise ValueError("CATT does not accept relative humidity outside the range [0, 100] %")
		self._prop_humidity.writeValueToFile(x)
		
	@property
	def airDensity(self):
		return self._prop_airDensity.readValueFromFile()[0]
	@airDensity.setter
	def airDensity(self, x):
		# TODO check range [1.0, 2.0] kg/m3
		if (x < 1.0) or (x > 2.0):
			raise ValueError("CATT does not accept air density outside the range [1.0, 2.0] kg/m^3")
		self._prop_airDensity.writeValueToFile(x)
	
	@property
	def airAbsorptionMode(self):
		code = self._prop_airDensity.readValueFromFile()
		if code == 0:
			return "estimated"
		elif code == 1:
			return "user defined"
		elif code == 2:
			return "off"
		elif code == 3:
			return "estimated + edge"
		else:
			raise ValueError("Unkown airAbsorptionMode code")
	@airAbsorptionMode.setter
	def airAbsorptionMode(self, mode):
		# TODO: check range
		if mode == "estimated":
			code = 0
		elif mode == "user defined":
			code = 1
		elif mode == "off":
			code = 2
		elif mode == "estimated + edge":
			code = 3
		self._prop_airAbsorptionMode.writeValueToFile(code)


	@property
	def airAbsorptionUserValues(self):
		# to call it, 
		#  - index it with the frequency 
		# 		e.g. A.airAbsorptionValues[2000]
		#  		to get or set the value at 2000Hz
		return self._prop_airAbsorptionUserValues


	@property
	def backgroundNoiseLevelTotal(self):
		# to call it, 
		#  - index it with the frequency 
		# 		e.g. A.backgroundNoiseLevelTotal[2000]
		#  		to get or set the value at 2000Hz
		return self._prop_backgroundNoiseLevelTotal
		
	@property
	def backgroundNoiseLevelResidual(self):
		# to call it, 
		#  - index it with the frequency 
		# 		e.g. A.backgroundNoiseLevelResidual[2000]
		#  		to get or set the value at 2000Hz
		return self._prop_backgroundNoiseLevelResidual

	def readBinStuff(self):
		return self._prop_sourcesUsed.readBitsFromFile()

	@property
	def sourcesUsed(self):
		return self._prop_sourcesUsed

	@property
	def receiversUsed(self):
		return self._prop_receiversUsed

	@property
	def planeSelectionMode(self):
		code = self._prop_planeSelectionMode.readValueFromFile()[0]
		if code == 0:
			mode = "all"
		elif code == 1:
			mode = "only some"
		elif code == 2:
			mode = "without some"
		else:
			raise ValueError("Unkown plane selection code.")
		return mode
	@planeSelectionMode.setter
	def headDirectionMode(self, mode):
		if mode == "all":
			code = 0
		elif mode == "only some":
			code = 1
		elif mode == "without some":
			code = 2
		else:
			raise ValueError("Unknown plane selection mode, must be either 'all', 'only some', or 'without some'.")
		self._prop_planeSelection.writeValueToFile(code)

	@property
	def planeSelection(self):
		return self._prop_planeSelection








def readMD9(filename: pathlib.Path):
# read MD9-file and store basic information in dictionnary such as
# - project name
# - inout directory
# - output directory
# - geo file
# - receiver loc file
# - source loc file
# 
# NOTE: This is the legacy function for accessing MD9 data, please use the class MD9Wrapper.
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

		
			

	
