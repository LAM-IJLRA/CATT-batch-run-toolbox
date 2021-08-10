# This script contains functions and objects relative to CATT and TUCT projects configurations
# zagala - 04.03.2021

import re
import pathlib
import warnings
import autocatt.materials
from autocatt.binWrapping import *



class MD9Wrapper:
# Wrapper for MD9 file (CATT-acoustics)
# 
# To instantiate from an existing MD9.file:

# ```
#   A = MD9Wrapper("project.MD9")
# ```
# 
#
# Project name and files:
# The following property are getable / setable:
# - projName                string
# - inputFolder             string
# - outputFolder            string
# - masterGeoFile           string
# - receverLocFile          string
# - sourceLocFile           string
#
# Diffuse relfections:
# - diffReflMode            among "off", "surface", "surface + edge" 
# - diffRelfUseDefault      True or False
# - diffReflDefaultValues   individual frequency can be set/get as follows: 
#   ```
#   A.diffReflDefaultValues[125] = 0.2
#   ```
#
# Head direction:
# - headDirectionMode
# - headDirection           individual component can be set/get as follows:
#   ```
#   A.headDirection[1:3] = [1, 0, 0]
#   xyz = A.headDirection[:]
#   A.headDirection = [7, 8, 9]
#   ```
#
# Air properties:
# - airTemperature          air temperature in degree celsius
# - airHumidity             relative hmidity, in %
# - airDensity              in kg/m^3
#
# Air absorption:
# - airAbsorptionMode       among 'estimated', 'user defined', 'off', 'estimated + edge'
# - airAbsorptionUserValues individual frequency values can be set/get as follows (in dB/m):
#   ```
#   A.airAbsorptionUserValues[16000] = -12.0
#   ```
# 
# Background noise:
# - backgroundNoiseLevelTotal   (used for receivers for which noise level has not be individually defined) defined for each frequency band
# - backgroundNoiseLevelresidual (added to all sources for which background noise has been individually defined) defined for ech frequency band
# 
# Sources and receivers used:
# - sourcesUsed             can be activated using a alphanumeric coordinates, e.g.
#   ```
#   A.sourcesUsed['A', 0] = True
#   A.sourcesUsed['B':'E', 0] = True # activate the first source of each group from B to D
#   A.sourcesUsed[::2, -1] = True # activate the last source of group A, C, E, G, ...
#   ```
# - receiversUsed           can be activated using a numerci index, e.g.
#   ```
#   A.receiversUsed[0:10] = True # activate the first 10 receivers
#   A.receiversUsed[2:-2] = False # deactivate all receivers excepts the first and last 2
#   ``` 
#
# Planes selection
# - planeSelectionMode      among 'only', or 'without'
# - planeSelection          object used to manage list of planes for modes 'only', and 'without'
#   ```
#   A.planeSelection.listOnlyWithSome = [0, 1, 2] # only planes 0, 1, and 2
#   a = A.planeSelection.listOnlyWithoutSome # get indices of planes omitted when 'without' mode is activated
#   ```
# 
# zagala - 04.2021
    def __init__(self, filename, createFile = False):
        self._filename = pathlib.Path(filename)
        assert self._filename.suffix in ['.MD9', '']
        
        if self._filename.exists() is False and createFile is True:
            import shutil
            templateFile = pathlib.Path(autocatt.__file__).parent / "templates" / "template.MD9"
            shutil.copy(templateFile, self._filename)
            print(f"new project file '{self._filename}' created")

        with open(self._filename, 'rb') as f:
            f.seek(0x0000)
            if f.read(2) != b'\x59\x4a':
                raise RuntimeError("file is not in MD9 format or is corrupted")

        self._prop_projName = BinEncProp_string(self, 0x00000008, 0x00000010D)
        self._prop_inputFolder = BinEncProp_path(self, 0x0000010D, 0x00000212, backslashTerm = True)
        self._prop_outputFolder = BinEncProp_path(self, 0x00000212, 0x00000317, backslashTerm = True)
        self._prop_masterGeoFile = BinEncProp_path(self, 0x00000317, 0x00000417)
        self._prop_receiverLocFile = BinEncProp_path(self, 0x00000417, 0x00000517)
        self._prop_sourceLocFile = BinEncProp_path(self, 0x00000517, 0x00000617)

        self._prop_diffReflMode = BinEncProp_num(self, 0x00000B34, 0x00000B36, format = '?')    
        self._prop_diffReflUseDefault = BinEncProp_scalar(self, 0x00000B36, format = '?')   
        self._prop_diffReflDefaultValues = BinEncProp_freqValues(self, 0x00000B37, format = 'f')

        self._prop_headDirectionMode = BinEncProp_scalar(self, 0x00000B57, format = 'b')
        self._prop_headDirection = BinEncProp_3Dvec(self, 0x00000B58, format = 'f')

        self._prop_airTemperature = BinEncProp_scalar(self, 0x0000B85, format = 'f', min = -20.0, max = 50)
        self._prop_airHumidity = BinEncProp_scalar(self, 0x0000B89, format = 'f', min = 0.0, max = 100.0)
        self._prop_airDensity = BinEncProp_scalar(self, 0x0000B8D, format = 'f', min = 1.0, max = 2.0)

        self._prop_airAbsorptionMode = BinEncProp_scalar(self, 0x00000B64, format = 'b')
        self._prop_airAbsorptionUserValues = BinEncProp_freqValues(self, 0x00000B65, format = 'f')

        self._prop_backgroundNoiseLevelTotal = BinEncProp_freqValues(self, 0x00000B91, format = 'f')
        self._prop_backgroundNoiseLevelResidual = BinEncProp_freqValues(self, 0x00000BB1, format = 'f')

        self._prop_sourcesUsed = BinEncProp_bitsMatrix(self, 0x00000627, ncols = 10)
        self._prop_receiversUsed = BinEncProp_bitsArray(self, 0x00000617, 100)

        self._prop_planeSelectionMode = BinEncProp_scalar(self, 0x00000B33, format = 'b')
        self._prop_planeSelection = BinEncProp_planeSelection(self, 0x00001108, 0x00000064B, 0x0000008BF)
        
    def __str__(self):
        txt = (
                f"{'=' * 80}\n"
                f"Project\n"
                f"{'-' * 20}\n"
                f"{'project name' : <20}: {self.projName}\n"
                f"{'input folder' : <20}: {self.inputFolder!s:<40} "
                f"{'✓' if self.inputFolder.is_dir() else 'not found'}\n"
                f"{'output folder' : <20}: {self.outputFolder!s:<40} "
                f"{'✓' if self.outputFolder.is_dir() else 'not found'}\n"
                f"{'master geo file' : <20}: {self.masterGeoFile!s:<40} "
                f"{'✓' if (self.inputFolder / self.masterGeoFile).is_file() else 'not found'}\n"
                f"{'receiver loc file' : <20}: {self.receiverLocFile!s:<40} "
                f"{'✓' if (self.inputFolder / self.receiverLocFile).is_file() else 'not found'}\n"
                f"{'source loc file' : <20}: {self.sourceLocFile!s:<40} "
                f"{'✓' if (self.inputFolder / self.sourceLocFile).is_file() else 'not found'}\n"
                f"\n"
                f"Diffuse reflections\n"
                f"{'-' * 20}\n"
                f"  {'mode' : <18}: {self.diffReflMode}\n"
                f"  {'use default' : <18}: {self.diffReflUseDefault}\n"
                f"  {'' : >18}  {BinEncProp_freqValues.frequencyString()}\n"
                f"  {'default values' : <18}: {self.diffReflDefaultValues: 10.2f}\n"
                f"\n"
                f"Head direction\n"
                f"{'-' * 20}\n"
                f"  {'mode' : <18}: {self.headDirectionMode}\n"
                f"  {'' : >18}  {BinEncProp_3Dvec.axesString()}\n"
                f"\n"
                f"  {'direction' : <18}: {self.headDirection : 10.2f}\n"
                f"Athmospheric conditions\n"
                f"{'-' * 20}\n"
                f"  {'air absorption mode' : <18}: {self.airAbsorptionMode}\n"
                f"  {'air temperature' : <18}: {self.airTemperature : 10.2f} °C\n"
                f"  {'air humidity' : <18}: {self.airHumidity : 10.2f} %\n"
                f"  {'air density' : <18}: {self.airDensity : 10.2f} kg/m³\n"
                f"  {'' : >18}  {BinEncProp_freqValues.frequencyString()}\n"
                f"  {'air abs (user)': <18}: {self.airAbsorptionUserValues : 10.2e} /m\n"
                f"\n"
                f"Background noise\n"
                f"{'-' * 20}\n"
                f"  {'' : >18}  {BinEncProp_freqValues.frequencyString()}\n"
                f"  {'total level': <18}: {self.backgroundNoiseLevelTotal : 10.2f} dB_SPL\n"
                f"  {'residual level': <18}: {self.backgroundNoiseLevelResidual : 10.2f} dB_SPL\n"
                f"\n"
                f"Sources and receivers:\n"
                f"{'-' * 20}\n"
        )
        srcStr = str(self.sourcesUsed).splitlines()
        recStr = str(self.receiversUsed).splitlines()
        for idx in range(max(len(srcStr), len(recStr))):
            if idx < len(srcStr):
                txt += srcStr[idx]
            else:
                txt += ' ' * len(srcStr[idx-1])
            if idx < len(recStr):
                txt += recStr[idx]
            txt += '\n'
        txt += '=' * 80
        return txt

    @property
    def projName(self):
        return self._prop_projName.readTextFromFile()
    @projName.setter
    def projName(self, name):
        if name != '':
            self._prop_projName.writeTextToFile(name)
        else:
            raise ValueError('project name cannot be empty')

    @property
    def inputFolder(self):
        return pathlib.Path(self._prop_inputFolder.readTextFromFile())
    @inputFolder.setter
    def inputFolder(self, folder):
        self._prop_inputFolder.writeTextToFile(folder, explicitRelPath = True)

    @property
    def outputFolder(self):
        return self._prop_outputFolder.readTextFromFile()
    @outputFolder.setter
    def outputFolder(self, folder):
        self._prop_outputFolder.writeTextToFile(folder, explicitRelPath = True)

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
    def receiverLocFile(self, file):
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
        return self._prop_diffReflUseDefault.readValueFromFile()
    @diffReflUseDefault.setter
    def diffReflUseDefault(self, value):
        self._prop_diffReflUseDefault.writeValueToFile(bool(value))

    @property
    def diffReflDefaultValues(self):
        # to call it 
        #  - index it with the frequency 
        #       e.g. A.diffReflDefautValues[2000]
        #       to get or set the value at 2000Hz
        return self._prop_diffReflDefaultValues

    @property
    def headDirectionMode(self):
        code = self._prop_headDirectionMode.readValueFromFile()
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
    def airTemperature(self):
        return self._prop_airTemperature.readValueFromFile()
    @airTemperature.setter
    def airTemperature(self, temp):
        if (temp < -20.0) or (temp > 50):
            raise ValueError("CATT does not accept airTemperatures outside the range [-20, 50] deg. Celsius")
        self._prop_airTemperature.writeValueToFile(temp)
    
    @property
    def airHumidity(self):
        return self._prop_airHumidity.readValueFromFile()
    @airHumidity.setter
    def airHumidity(self, x):
        if (x < 0.0) or (x > 100):
            raise ValueError("CATT does not accept relative airHumidity outside the range [0, 100] %")
        self._prop_airHumidity.writeValueToFile(x)
        
    @property
    def airDensity(self):
        return self._prop_airDensity.readValueFromFile()
    @airDensity.setter
    def airDensity(self, x):
        if (x < 1.0) or (x > 2.0):
            raise ValueError("CATT does not accept air density outside the range [1.0, 2.0] kg/m^3")
        self._prop_airDensity.writeValueToFile(x)
    
    @property
    def airAbsorptionMode(self):
        code = self._prop_airAbsorptionMode.readValueFromFile()
        if code == 0:
            return "estimated"
        elif code == 1:
            return "user defined"
        elif code == 2:
            return "off"
        elif code == 3:
            return "estimated + edge"
        else:
            print(code)
            raise ValueError("Unkown airAbsorptionMode code")
    @airAbsorptionMode.setter
    def airAbsorptionMode(self, mode):
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
        #       e.g. A.airAbsorptionValues[2000]
        #       to get or set the value at 2000Hz
        return self._prop_airAbsorptionUserValues


    @property
    def backgroundNoiseLevelTotal(self):
        # to call it, 
        #  - index it with the frequency 
        #       e.g. A.backgroundNoiseLevelTotal[2000]
        #       to get or set the value at 2000Hz
        return self._prop_backgroundNoiseLevelTotal
        
    @property
    def backgroundNoiseLevelResidual(self):
        # to call it, 
        #  - index it with the frequency 
        #       e.g. A.backgroundNoiseLevelResidual[2000]
        #       to get or set the value at 2000Hz
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
        code = self._prop_planeSelectionMode.readValueFromFile()
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
    def planeSelectionMode(self, mode):
        if mode == "all":
            code = 0
        elif mode == "only some":
            code = 1
        elif mode == "without some":
            code = 2
        else:
            raise ValueError("Unknown plane selection mode, must be either 'all', 'only some', or 'without some'.")
        self._prop_planeSelectionMode.writeValueToFile(code)

    @property
    def planeSelection(self):
        return self._prop_planeSelection





class CounterFileWrapper:
    def __init__(self, filename):
        self._filename = pathlib.Path(filename)

        self._propCount = BinEncProp_scalar(self, 0x0000, format = "i")

        if self._filename.exists() is False:
            with open(self._filename, 'wb') as f:
                f.seek(0x0000)
                f.write(0x000)
            self.count = 0


    def __str__(self):
        return f"{'count' : <20}: {self.count:10d}\n"

    @property
    def count(self):
        return self._propCount.readValueFromFile()
    @count.setter
    def count(self, x):
        self._propCount.writeValueToFile(x)






class PredictionSettingWrapper:
# Wrapper for prediction setting .DAT file (CATT-acoustics)

    def __init__(self, filename):
        self._filename = pathlib.Path(filename)
#       assert self._filename.suffix in ['.DAT', '']
#       
#       if self._filename.exists() is False and createFile is True:
#           import shutil
#           templateFile = pathlib.Path(autocatt.__file__).parent / "templates" / "template.MD9"
#           shutil.copy(templateFile, self._filename)
#           print(f"new project file '{self._filename}' created")

        self._prop_algo = BinEncProp_scalar(self, 0x00000008, format = 'b')

        self._prop_length = BinEncProp_scalar(self, 0x00000009, format = 'f', min = 0.05, max = 20.0)

        self._prop_nbrRays = BinEncProp_scalar(self, 0x0000000D, format = 'L')

        self._prop_eAverages = BinEncProp_scalar(self, 0x00000012, format = 'b', min = 1, max = 50)
        self._prop_splitOrder = BinEncProp_scalar(self, 0x00000018, format = 'b', min = 0, max = 2)

        # misc binary array (spread on 4 Bytes), list of param (not ordered):
        #   shut-down after processing
        #   suggestNRays, suggest length
        #   3o HOA 2o HOA
        #   create 5 channels
        #   air absorption
        #   diffraction
        #   2nd order diff only for  double planes, oversample, 2nd Order Diff, diff to spec, spec to diff]
        self._prop_miscBitsArray = BinEncProp_bitsArray(self, 0x00000016, 32, endian = "big")

    def __str__(self):
        txt = (
            f"{'=' * 80}\n"
            f"Algorithm\n"
            f"{'-' * 20}\n"
            f"{'algorithm' : <20}: {self.algorithm:10d}\n"
            f"{'length' : <20}: {self.length:10.2f} s\n"
            f"{'suggest length' : <20}: {self.suggestLength}\n"
            f"{'nbr rays' : <20}: {self.nbrRays:10d}\n"
            f"{'suggest nbr rays' : <20}: {self.suggestNbrRays}\n"
            f"{'E averages' : <20}: {self.eAverages:10d}\n" # ONLY for algo 1
            f"{'max split order' : <20}: {self.splitOrder:10d}\n"   # ONLY for algo 1
            f"{'air absorption' : <20}: {self.airAbsorption}\n"


            f"\nDiffraction\n"
            f"{'-' * 20}\n"
            f"{'diffraction' : <20}: {self.diffraction}\n"
            f"{'diff to spec' : <20}: {self.diffraction_diffToSpec}\n"
            f"{'spec to diff' : <20}: {self.diffraction_specToDiff}\n"
            f"{'2nd order diff' : <20}: {self.diffraction_order2}\n"
            f"{'2nd o. only dbl planes' : <20}: {self.diffraction_order2_onlyDoublePlanes}\n"
            f"{'oversampling' : <20}: {self.diffraction_oversampling}\n"

            f"\nOutput\n"
            f"{'-' * 20}\n"
            f"{'B-format order' : <20}: {self.orderBFormat}\n"
            f"{'5 channels' : <20}: {self.fiveChannelsOutput}\n"

            f"\nMisc\n"
            f"{'-' * 20}\n"
            f"{'shut down when done' : <20}: {self.shutDownAfterProc}\n"
            f"{'single thread' : <20}: {self.singleThread}\n"

            f"{'=' * 80}\n"
        )
        return txt

    @property
    def algorithm(self):
        return self._prop_algo.readValueFromFile() + 1
    @algorithm.setter
    def algorithm(self, x):
        if x not in [1, 2, 3]:
            raise ValueError("algorithm must be either 1, 2, or 3")
        self._prop_algo.writeValueToFile(x - 1)

    @property
    def length(self):
        return self._prop_length.readValueFromFile()
    @length.setter
    def length(self, x):
        self._prop_length.writeValueToFile(x)
    

    @property
    def nbrRays(self):
        return self._prop_nbrRays.readValueFromFile()
    @nbrRays.setter
    def nbrRays(self, x):
        if x == "diffraction only" or x == 0:
            if self.diffraction == False:
                raise ValueError("Setting nbrRays to 'diffraction only' requires to activate diffraction first")
            x = 0
        elif x == "direct only" or x == 1:
            x = 1
        elif x == "first order specular only" or x == 2:
            x = 2
        elif x == "direct and first order specular only" or x == 3:
            x = 3
        elif x < 100:
            raise ValueError("Number of rays must be greater or equal to 100 or have the special values 0, 1, 2, or 3.")
        self._prop_nbrRays.writeValueToFile(x)

    @property
    def eAverages(self):
        return self._prop_eAverages.readValueFromFile()
    @eAverages.setter
    def eAverages(self, x):
        self._prop_eAverages.writeValueToFile(x)

    @property
    def splitOrder(self):
        return self._prop_splitOrder.readValueFromFile()
    @splitOrder.setter
    def splitOrder(self, x):
        self._prop_splitOrder.writeValueToFile(x)

    @property
    def shutDownAfterProc(self):
        return self._prop_miscBitsArray[7]
    @shutDownAfterProc.setter
    def shutDownAfterProc(self, x):
        self._prop_miscBitsArray[7] = x

    @property
    def suggestLength(self):
        return self._prop_miscBitsArray[0]
    @suggestLength.setter
    def suggestLength(self, x):
        self._prop_miscBitsArray[0] = x

    @property
    def suggestNbrRays(self):
        return self._prop_miscBitsArray[1]
    @suggestNbrRays.setter
    def suggestNbrRays(self, x):
        warnings.warn("initial estimation of number of rays is not yet implemented, you might want to set the initial number of rays by yourself. After estimation and analysis of the echogram, the number of rays will be adjusted.")
        self._prop_miscBitsArray[1] = x
    
    @property
    def airAbsorption(self):
        return self._prop_miscBitsArray[8]  
    @airAbsorption.setter
    def airAbsorption(self, x):
        self._prop_miscBitsArray[8] = x

    @property
    def singleThread(self):
        return self._prop_miscBitsArray[9]
    @singleThread.setter
    def singleThread(self, x):
        self._prop_miscBitsArray[9] = x

    @property
    def diffraction(self):
        return self._prop_miscBitsArray[14]
    @diffraction.setter
    def diffraction(self, x):
        if x is False and self.nbrRays == 0:
            raise ValueError("You cannot deactivate diffracton while 'diffractionOnly' mode is activated. Please set ")
        self._prop_miscBitsArray[14] = x

    @property
    def orderBFormat(self):
        codeOrder2 = self._prop_miscBitsArray[11]
        codeOrder3 = self._prop_miscBitsArray[12]
        if codeOrder2 is True:
            if codeOrder3 is False:
                return 2
            else:
                raise ValueError("inconsistency in predicition settings DAT file. B-format order cannot be set to 2nd order and 3rd order at the same time.")
        else:
            if codeOrder3 is True:
                return 3
            else:
                return 1
    @orderBFormat.setter
    def orderBFormat(self, x):
        if x == 1:
            codeOrder2 = False
            codeOrder3 = False
        elif x == 2:
            codeOrder2 = True
            codeOrder3 = False
        elif x == 3:
            codeOrder2 = False
            codeOrder3 = True
        else:
            raise ValueError("B-Format order must be either 1, 2, or 3")
        self._prop_miscBitsArray[11] = codeOrder2
        self._prop_miscBitsArray[12] = codeOrder3

    @property
    def fiveChannelsOutput(self):
        return self._prop_miscBitsArray[13]
    @fiveChannelsOutput.setter
    def fiveChannelsOutput(self, x):
        warnings.warn("setting of geometry of the microphone tree is not implemented yet.")
        self._prop_miscBitsArray[13] = x

    @property
    def diffraction_specToDiff(self):
        return self._prop_miscBitsArray[24]
    @diffraction_specToDiff.setter
    def diffraction_specToDiff(self, x):
        self._prop_miscBitsArray[24] = x

    @property
    def diffraction_diffToSpec(self):
        return self._prop_miscBitsArray[25]
    @diffraction_diffToSpec.setter
    def diffraction_diffToSpec(self, x):
        self._prop_miscBitsArray[25] = x

    @property
    def diffraction_order2(self):
        return self._prop_miscBitsArray[26]
    @diffraction_order2.setter
    def diffraction_order2(self, x):
        self._prop_miscBitsArray[26] = x

    @property
    def diffraction_oversampling(self):
        return self._prop_miscBitsArray[27]
    @diffraction_oversampling.setter
    def diffraction_oversampling(self, x):
        self._promiscBitsArray[27] = x

    @property
    def diffraction_order2_onlyDoublePlanes(self):
        return self._prop_miscBitsArray[28]
    @diffraction_order2_onlyDoublePlanes.setter
    def diffraction_order2_onlyDoublePlanes(self, x):
        self._prop_miscBitsArray[28] = x

    








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

        
            


    
