import struct
from bitarray import bitarray
import warnings
import pathlib
import re
from math  import ceil
from collections.abc import Iterable


class BinEncProp:
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

class BinEncProp_bits(BinEncProp):
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


class BinEncProp_bitsArray(BinEncProp_bits):
	# used for receivers which are index from 0 to 100
	def __init__(self, parent, byteStart, nValues, **kwargs):
		byteEnd = byteStart + ceil(nValues / 8)
		super().__init__(parent, byteStart, byteEnd, **kwargs)
		self._nValues = nValues
	def readBitsFromFile(self, keepFullLastByte = False):
		bits = super().readBitsFromFile()
		if keepFullLastByte:
			return bits.tolist()
		else:
			return bits.tolist()[:self._nValues] # avoid returning full last byte if only some bites are required
	def writeBitsToFile(self, bitsAr):
		bits = bitarray(bitsAr, endian = self.endian)
		super().writeBitsToFile(bits.to01())
	def __getitem__(self, idx):
		return self.readBitsFromFile()[idx]
	def __setitem__(self, idx, value):
		bitsArFull = self.readBitsFromFile(keepFullLastByte = True) # in case othr information are stored in the last bits of the last Byte
		bitsAr = self.readBitsFromFile()
		diffLength = len(bitsArFull) - len(bitsAr)
		bitsAr[idx] = value
		bitsAr.extend(bitsArFull[-diffLength:])
		self.writeBitsToFile(bitsAr)
	def __str__(self):
		values = self.readBitsFromFile()
		txt = '       ' + ''.join([f"{idx:3d}" for idx in range(10)])
		dozen = -10
		for mm in range(self._nValues):
			if mm % 10 == 0:
				dozen += 10
				txt += '\n'
				txt += f"   {dozen:3d} "
			if values[mm]:
				txt += ' ✓ '
			else:
				txt += ' . '
		return txt
	
	

class BinEncProp_bitsMatrix(BinEncProp_bits):
	# used for sources which are indexes by (alpha, int)
	def __init__(self, parent, byteStart, ncols = 10, **kwargs):
		nValues = 26 * ncols
		byteEnd = byteStart + ceil(nValues / 8)
		super().__init__(parent, byteStart, byteEnd, **kwargs)
		self._ncols = ncols
		self._nValues = nValues
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
			if letter.start is None: 
				start = 0
			elif letter.start.isalpha():
				start = ord(letter.start.lower()) - 97
			else:
				raise ErrorValue("index must be a letter (alpha) or slice using letters as indices")
			if letter.stop is None: 
				stop = 27
			elif letter.stop.isalpha():
				stop = ord(letter.stop.lower()) - 97
			else:
				raise ErrorValue("index must be a letter (alpha) or slice using letters as indices")
			idx = slice(start, stop, letter.step) 
		else:
			if str(letter).isalpha() == False:
				raise ErrorValue("input must be a letter (alpha)")
			idx = ord(letter.lower()) - 97
		return idx 
	def __getitem__(self, xy):
		# xy is a tuple (alpha, int)
		# TODO: this is a mess...
		x, y = xy
		x = self._letterToIndex(x)
		allValues = self.readBitsFromFile()
		value = []
		if isinstance(x, slice):
			for xx in range(x.start or 0, x.stop or 26, x.step or 1):
				if isinstance(y, slice):
					for yy in range(y.start or 0, y.stop or self._ncols+1, y.step or 1):
						value.append(bitsAr[xx][yy])
				else:
					value.append(bitsAr[xx][y])
		else:
			if isinstance(y, slice):
				for yy in range(y.start or 0, y.stop or self._ncols+1, y.step or 1):
					value.append(bitsAr[x][yy])
			else:
				value = bitsAr[x][y]
		return self.readBitsFromFile()[x][y]
	def __setitem__(self, xy, value):
		# TODO: this is a mess
		x, y = xy
		x = self._letterToIndex(x)
		bitsAr = self.readBitsFromFile()
		isValueIterable = isinstance(value, Iterable)
		idx = 0
		if isinstance(x, slice):
			for xx in range(x.start or 0, x.stop or 26, x.step or 1):
				if isinstance(y, slice):
					for yy in range(y.start or 0, y.stop or self._ncols+1, y.step or 1):
						if isValueIterable:
							bitsAr[xx][yy] = value[idx]
							idx += 1
						else:
							bitsAr[xx][yy] = value
				else:
					if isValueIterable:
						bitsAr[xx][y] = value[idx]
						idx += 1
					else:
						bitsAr[xx][y] = value
		else:
			if isinstance(y, slice):
				for yy in range(y.start or 0, y.stop or self._ncols+1, y.step or 1):
					if isValueIterable:
						bitsAr[x][yy] = value[idx]
						idx += 1
					else:
						bitsAr[x][yy] = value
			else:
				bitsAr[x][y] = value
			
		self.writeBitsToFile(bitsAr)
	def __str__(self):
		values = self.readBitsFromFile()
		txt = '     ' + ''.join([f"{idx:3d}" for idx in range(self._ncols)]) + '\n'
		for mm in range(26):
			txt += '    ' + chr(mm + 97) + ' '
			for nn in range(self._ncols):
				if values[mm][nn]:
					txt += ' ✓ '
				else:
					txt += ' . '
			txt += '\n'
		return txt






		

class BinEncProp_string(BinEncProp):
	def __init__(self, parent, byteStart, byteEnd, encoding = "latin1"):
		if encoding in ("latin1", "ASCII"):
			# TODO: implement for other encoding
			byteStep = 0.5
		else:
			raise ValueError("Unkown byteStep for encoding {} please implement yourself the 'byteStep' for this encoding")
		super().__init__(parent, byteStart, byteEnd, byteStep)
		self._encoding = encoding
	def readTextFromFile(self, trim = True):
		txt = self._readBytesFromFile()
		if trim:
			txt = txt.split(b'\x00', 1)[0]
		return txt.decode(self._encoding)
	def writeTextToFile(self, txt):
		if len(txt) > self.byteWidth // self._byteStep:
			txt = txt[:self.byteWidth]
		else:
			txt = txt.ljust(self.byteWidth, '\x00')
		self._writeBytesToFile(txt.encode(self._encoding))


class BinEncProp_path(BinEncProp_string):
	def __init__(self, *args, backslashTerm = False, **kwargs):
		super().__init__(*args, **kwargs)
		self._backslashTerm = backslashTerm # whether path must finish with a '\' when written into the file
	def readTextFromFile(self, **kwargs):
		# CATT binary files only accepts "\" as file separators, however this is incredibly impractical for cross platform applications, for this reason, files are stored with "\" in CATT binary files, and converted to forward slashes when read
		# (I am writing this code on a MAC)
		path = super().readTextFromFile()
		path = path.replace('\\', '/')
		return pathlib.Path(path)
	def writeTextToFile(self, path, explicitRelPath = False):
		path = str(path) # in case path is a pathlib type
		if explicitRelPath and pathlib.Path(path).is_absolute() == False:
			# for some fields, CATT requires to explicitely indicate if a file is relative 
			if path.startswith('.') == False:
				path = '.\\' + str(path)
		path = path.replace('/', '\\')
		if self._backslashTerm:
			path = re.sub(r'\\?$', r'\\', path) # make sure path finishes with symbol '\'
		print(path)
		super().writeTextToFile(path)

		

class BinEncProp_num(BinEncProp):
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
		if format in 'fiIlL':
			return 4
		elif format in 'dqQ':
			return 8
		elif format in 'cbB?':
			return 1
		else:
			raise ValueError("Unrecognized format, maybe you could implement it?")


class BinEncProp_scalar(BinEncProp_num):
	def __init__(self, parent, byteStart, format = 'f', **kwargs):
		byteStep = super().getByteStepForFormat(format)
		super().__init__(parent, byteStart, byteStart + byteStep, format = format, **kwargs)
	def readValueFromFile(self):
		return super().readValueFromFile()[0]

		
class BinEncProp_freqValues(BinEncProp_num):
	frequencies = [125, 250, 500, 1000, 2000, 4000, 8000, 16000]
	def __init__(self, parent, byteStart, format = 'f', **kwargs):	
		step = self.getByteStepForFormat(format)
		super().__init__(parent, byteStart, byteStart + step * len(BinEncProp_freqValues.frequencies), format = format, **kwargs)
#self._frequencies = frequencies
	def __getitem__(self, freq):
		idx = BinEncProp_freqValues.frequencies.index(freq)
		values = self.readValueFromFile()
		return values[idx]
	def __setitem__(self, freq, val):
		idx = BinEncProp_freqValues.frequencies.index(freq)
		values = list(self.readValueFromFile())
		values[idx] = val
		self.writeValueToFile(*tuple(values))
	@staticmethod
	def frequencyString(spec = '10.0f'):
		spec2 = r'{0:' + spec + r'}'
		return ''.join([spec2.format(ff) for ff in BinEncProp_freqValues.frequencies])
		
	def __format__(self, spec = '10.2f'):
		txt = ""
		if 'freqs' in spec:
			spec = spec.replace('freqs', '')
			txt += BinEncProp_freqValues.frequencyString(spec) + '\n'
		spec2 = r'{0:' + spec + r'}'
		txt += ''.join([spec2.format(self[ff]) for ff in BinEncProp_freqValues.frequencies])
		return txt



class BinEncProp_3Dvec(BinEncProp_num):
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
	@staticmethod
	def axesString(spec = '>10'):
		spec2 = r'{:' + spec + r'}'
		return ''.join([spec2.format(aa) for aa in ['x', 'y', 'z']])
	def __format__(self, spec = '10.2f'):
		txt = ""
		if 'axes' in spec:
			spec = spec.replace('axes', '')
			txt += BinEncProp_3Dvec(spec)
		spec2 = r'{0:' + spec + r'}'
		txt += ''.join([spec2.format(self[idx]) for idx in (0, 1, 2)])
		return txt
	

		
class BinEncProp_planeSelection():
	def __init__(self, parent, byteStartList, bytePosNumOnlySome, bytePosNumWithoutSome, finalBytes = b'\x0A'):
		self._parent = parent
		self._byteStartList = byteStartList
		self._prop_nbrOnlySome = BinEncProp_num(parent, 0x0000064B, 0x0000064F, format = 'i')
		self._prop_nbrWithoutSome = BinEncProp_num(parent, 0x000008BF, 0x000008C3, format = 'i')
		self._prop_listOnlySome = BinEncProp_num(parent, self._byteStartOnlySome, self._byteEndOnlySome, format = 'i')
		self._prop_listWithoutSome = BinEncProp_num(parent, self._byteStartWithoutSome, self._byteEndWithoutSome, format = 'i')
		self._finalBytes = finalBytes
	@property
	def nbrOnlySome(self):
		return self._prop_nbrOnlySome.readValueFromFile()[0]
	@property
	def nbrWithoutSome(self):
		return self._prop_nbrWithoutSome.readValueFromFile()[0]
	@property
	def _nbrTotal(self):
		return self.nbrOnlySome + self.nbrWithoutSome
	@property
	def _byteStartOnlySome(self):
		return self._byteStartList
	@property
	def _byteEndOnlySome(self):
		return self._byteStartWithoutSome
	@property
	def _byteStartWithoutSome(self):
		return self._byteStartList + self.nbrOnlySome * 4
	@property
	def _byteEndWithoutSome(self):
		return self._byteStartWithoutSome + self.nbrWithoutSome * 4
	

	@property
	def listOnlySome(self):
		return self._prop_listOnlySome.readValueFromFile()
	@listOnlySome.setter
	def listOnlySome(self, values):
		# modifying len of list "only" yiels to a shift of the list "without".
		# Therefore, the list "without" is stored prior to re-writing end file part
		self._prop_nbrOnlySome.writeValueToFile(len(values))

		# get values from withoutSome
		valuesWithout = sorted(self.listWithoutSome)
		self._clear(self._nbrTotal)

		self._prop_listOnlySome = BinEncProp_num(self._parent, 
				self._byteStartOnlySome, 
				self._byteEndOnlySome, 
				format = 'i')
		self._prop_listOnlySome.writeValueToFile(*sorted(values))

		self._prop_listWithoutSome = BinEncProp_num(self._parent, 
				self._byteStartWithoutSome, 
				self._byteEndWithoutSome, 
				format = 'i')
		self._prop_listWithoutSome.writeValueToFile(*valuesWithout)


	@property
	def listWithoutSome(self):
		return self._prop_listWithoutSome.readValueFromFile()
	@listWithoutSome.setter
	def listWithoutSome(self, values):
		self._prop_nbrWithoutSome.writeValueToFile(len(values))
		self._clear(self.nbrWithoutSome, fromSec = "without")
		self._prop_listWithoutSome = BinEncProp_num(self._parent, 
				self._byteStartWithoutSome, 
				self._byteEndWithoutSome, 
				format = 'i')
		self._prop_listWithoutSome.writeValueToFile(*sorted(values))


	def _clear(self, le, fromSec = "only"):
		# clear end of binary files and adjust size to desired length
		with open(self._parent._filename, 'rb+') as f:
			if fromSec == "only":
				f.seek(self._byteStartOnlySome)
			elif fromSec == "without":
				f.seek(self._byteStartWithoutSome)
			else:
				raise ValueError("Unkown mode for 'from', must be either 'only' or 'without'.")
			# write dummy values on desired bytes slice	
			f.write(b'\00' * le * 4)
			f.write(self._finalBytes)
			f.truncate()
