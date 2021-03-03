# -*- coding: utf-8 -*-
#!/usr/bin/python

# Franck Zagala - 02.03.2021

import click
import os, glob
from matToWav import matToWav
#import sys, getopt, os, struct, glob, scipy.io, re, subprocess, shlex
#from scipy.io import wavfile
#import numpy as np

@click.command()
@click.option("-i", "--input-file", "inputFile", 
		prompt="input file", 
		help="full path to the .md9 file", 
		type=click.Path(exists=True, file_okay=True, dir_okay=False, resolve_path=True))
@click.option("-o", "--output-folder", "outputFolder", 
		prompt="output directory",
		help="output directory path",
		type=click.Path(exists=True, file_okay=False, dir_okay=True, resolve_path=True))
@click.option("-r", "--room", "room",
		prompt="room",
		help="project name like in CATT General Settings",
		type=click.STRING)
@click.option("-N", "--nbr-runs", "nbrRuns",
		default=1, 
		help="number of runs", 
		type=click.INT)
@click.option("-f", "--ir-format", "irFormat",
		multiple=True,
		default=["omni", "bf", "bin"], 
		type=click.Choice(["omni", "bf", "bin"], case_sensitive=False))
@click.option("-m/-M", "--meas/--no-meas", 
		default=True,
		help="whether measure files should be created")
@click.option("-e", "--executable", "CATTexe",
		prompt=True,
		default=lambda: os.environ.get("AUTOCATT_CATT_EXE", ""),
		type=click.Path(exists=True, file_okay=True))
@click.option("-t", "--tuct-executable", "TUCTexe",
		prompt=True,
		default=lambda: os.environ.get("AUTOCATT_TUCT_EXE", ""),
		type=click.Path(exists=True, file_okay=True))
def main(inputFile, outputFolder, room, nbrRuns, irFormat, meas, CATTexe, TUCTexe):

	print("----------------")
	print("input File :     ", inputFile)
	print("output folder :  ", outputFolder)
	print("room : 		    ", room)
	print("number of runs : ", nbrRuns)
	print("irFormat :       ", irFormat)
	print("export meas :	", meas)
	print("CATT exe :       ", CATTexe)
	print("TUCT exe :       ", TUCTexe)


	CAGBaseName = outputFolder + '/' + room

	commandCATT = f"{CATTexe!s} {inputFile!s} /AUTO"

	for ii in range(nbrRuns):

		os.system(commandCATT)
		print("\n")

		CAGFile = CAGBaseName + "_" + str(ii + 1) + ".CAG"
		commandTUCT = f"{TUCTexe!s} {CAGFile!s} /AUTO /SAVE:{','.join(irFormat)}"
		os.system(commandTUCT)
		print("\n")


# convert omni mat file to wav
	matToWav("trucBidule_AdummyIR_OMNI.mat")





	# find CATT results files (.MAT)
#	resultsFiles = glob.glob(CAGBaseName + "*.MAT")

#for res in resultsFiles:
		
#	if bool(re.search("_OMNI", res):

		

#   #Default parameter values
#   input_file = ''
#   room = ''
#   nof_runs = 1
#   ft = "OMNI"
#   output_folder = None
#   
#   try:
#      opts, args = getopt.getopt(argv,"hi:r:",["N=","fmt=","o="])
#   except getopt.GetoptError:
#      print('CATT_batch_processing.py -i <input_file> -r <room>')
#      sys.exit(2)
#   for opt, arg in opts:
#      if opt == '-h':
#         print('\n\n\nCATT_batch_processing.py -i <input_file> -r <room> [--N <nof_runs> --fmt <IR_format> --o <output_folder>]')
#         print('\nRuns multiple simulations of TUCT2 and saves the IRs in .WAV and the measures in .MAT')
#         print('\n<output_folder> must be the same as that defined in General Settings/Output folder in your CATT project = <input_file>')
#         print('\nTUCT2 reads the simulation settings from <room>_predictionsettings.DAT stored in the <output_folder>')
#         print('\nExample: python CATT_batch_processing.py -i C:\\Users\\Julien\\Documents\\CATTDATA\\Amphi55a\\#X\\CATT.MD9 -r Amphi55a --N 2 --fmt ["OMNI","BIN"]'
#               ' --o C:\\Users\\Julien\\Documents\\CATTDATA\\Amphi55a\\#X\\OUTPUT_ALGO2')
#         print('\n<input_file>: full path of the .MD9 file')
#         print('<room>: project name like in CATT General Settings')
#         print('<nof_runs>: number of consecutive runs of TUCT predictions (default: 1)')
#         print('<IR_format>: list of comma-separated strings among MEAS(measures), OMNI(omni IR), BF(B-format IR) and BIN(binaural IR)' 
#               '\nExample: <IR_format> = ["BF","OMNI","MEAS"] (default: ["OMNI"])')
#         print('<output_folder>: output folder name (default: "<input_file>/OUTPUT")')
#         print('\nThe channels ordering of the B-Format IRs is ACN (see https://www.wikiwand.com/en/Ambisonic_data_exchange_formats)')
#
#         sys.exit()
#      elif opt == ("-i"):
#         input_file = str(arg)
#      elif opt == ("-r"):
#         room = arg
#      elif opt == ("--N"):
#         nof_runs = int(arg)
#      elif opt == ("--fmt"):
#         ft = arg
#      elif opt == ("--o"):
#         output_folder = str(arg)
#         
#   print('Input file is ', input_file)
#   print('Room is ', room)
#   print('Number of runs is ', nof_runs)
#   print('IR format is ', ft)
#
#   inputfolder = os.path.split(input_file.replace(os.sep,'/'))[0]
#   if output_folder == None:  
#       output_folder = inputfolder + "/OUTPUT"
#
#   print('Output folder is ', output_folder)
#
#   #Here put your own path to the CATT folder
#   CATTfolder = """C:\\Program Files (x86)\\CATT\\"""
#   CATT9cmd = CATTfolder + "CATT9.exe"   
#   TUCTcmd = CATTfolder + "TUCT2.exe"
#
#   CAGBaseName = output_folder + '/' + room
#   
#   #Scan of the xxx_count.DAT file to get the run numbering offset
#   Cntfile = CAGBaseName + '_count.DAT'
#   if os.path.exists(Cntfile):
#       fid = open(Cntfile,'rb')
#       cnt = struct.unpack('i', fid.read(4))[0]
#       fid.close()
#   else:
#       cnt = 0
#
#   #Creation of the string concatenating the desired output formats
#   IR_format_str = ''
#   for IR_format in [ft]:
#       IR_format_str += IR_format + ','
#   
#   #Executing the runs
#   for index in range(nof_runs):
#       
#       os.system('"' + '"' + CATT9cmd + '"' + ' ' + input_file.replace('/','\\') + ' /AUTO' + '"')
#       
#       CAGfile = CAGBaseName + '_' + str(cnt + index + 1) + '.CAG'
#       TUCTcmd_full = " '"'%s'"' '"'%s'"' ' /AUTO /SAVE:%s'" % (TUCTcmd, CAGfile.replace('/','\\'),IR_format_str[:-1])
#       subprocess.run(shlex.split(TUCTcmd_full))
#
#
#   # .MAT TO .WAV files conversion 
#   mat_list = glob.glob(CAGBaseName + "*.MAT")  
#
#   for i in range(len(mat_list)):
#      
#       #Look for pattern '_A' in the MAT filename to obtain the variable name
#       if bool(re.search('_OMNI',mat_list[i])):
#           
#           mat = scipy.io.loadmat(mat_list[i])
#           wavfilename = mat_list[i][:-4] + '.WAV'
#           fs = int(mat['TUCT_fs'])
#           varname = 'h_A' + (mat_list[i].split('_A')[1])[:-4]
#           wavfile.write(wavfilename, fs, np.array(mat[varname][0]))
#           mat.clear()
#           os.remove(mat_list[i])
#           
#       elif bool(re.search('_BF',mat_list[i])):
#           
#           mat = scipy.io.loadmat(mat_list[i])
#           wavfilename = mat_list[i][:-4] + '.WAV'
#           fs = int(mat['TUCT_fs'])         
#           varname_W = 'h_A' + (mat_list[i].split('_A')[1])[:-4] + '_W'
#           varname_X = 'h_A' + (mat_list[i].split('_A')[1])[:-4] + '_X'
#           varname_Y = 'h_A' + (mat_list[i].split('_A')[1])[:-4] + '_Y'
#           varname_Z = 'h_A' + (mat_list[i].split('_A')[1])[:-4] + '_Z'
#           W = np.array(mat[varname_W][0])
#           Y = np.array(mat[varname_Y][0])
#           Z = np.array(mat[varname_Z][0])
#           X = np.array(mat[varname_X][0])
#           output = np.vstack([W,Y,Z,X])
#           
#           if len(mat)-1 >= 9: #2nd order BFormat
#               varname_R = 'h_A' + (mat_list[i].split('_A')[1])[:-4] + '_R'
#               varname_S = 'h_A' + (mat_list[i].split('_A')[1])[:-4] + '_S'
#               varname_T = 'h_A' + (mat_list[i].split('_A')[1])[:-4] + '_T'
#               varname_U = 'h_A' + (mat_list[i].split('_A')[1])[:-4] + '_U'
#               varname_V = 'h_A' + (mat_list[i].split('_A')[1])[:-4] + '_V'
#               R = np.array(mat[varname_R][0])
#               S = np.array(mat[varname_S][0])
#               T = np.array(mat[varname_T][0])
#               U = np.array(mat[varname_U][0])
#               V = np.array(mat[varname_V][0])
#               output = np.vstack([W,Y,Z,X,V,T,R,S,U])
#               
#               if len(mat)-1 == 16: #3rd order BFormat:
#                   varname_K = 'h_A' + (mat_list[i].split('_A')[1])[:-4] + '_K'
#                   varname_L = 'h_A' + (mat_list[i].split('_A')[1])[:-4] + '_L'
#                   varname_M = 'h_A' + (mat_list[i].split('_A')[1])[:-4] + '_M'
#                   varname_N = 'h_A' + (mat_list[i].split('_A')[1])[:-4] + '_N'
#                   varname_O = 'h_A' + (mat_list[i].split('_A')[1])[:-4] + '_O'
#                   varname_P = 'h_A' + (mat_list[i].split('_A')[1])[:-4] + '_P'
#                   varname_Q = 'h_A' + (mat_list[i].split('_A')[1])[:-4] + '_Q'
#                   K = np.array(mat[varname_K][0])
#                   L = np.array(mat[varname_L][0])
#                   M = np.array(mat[varname_M][0])
#                   N = np.array(mat[varname_N][0])
#                   O = np.array(mat[varname_O][0])
#                   P = np.array(mat[varname_P][0])
#                   Q = np.array(mat[varname_Q][0])
#                   output = np.vstack([W,Y,Z,X,V,T,R,S,U,Q,O,M,K,L,N,P])          
#
#           wavfile.write(wavfilename, fs, output.transpose())
#           mat.clear()
#           os.remove(mat_list[i])
#           
#       elif bool(re.search('_BIN',mat_list[i])):
#           
#           mat = scipy.io.loadmat(mat_list[i])
#           wavfilename = mat_list[i][:-4] + '.WAV'
#           fs = int(mat['TUCT_fs'])
#           varname_L = 'h_A' + (mat_list[i].split('_A')[1])[:-4] + '_L'
#           varname_R = 'h_A' + (mat_list[i].split('_A')[1])[:-4] + '_R'
#           L = np.array(mat[varname_L][0])
#           R = np.array(mat[varname_R][0])
#           output = np.vstack([L,R])
#           wavfile.write(wavfilename, fs, output.transpose())
#           mat.clear()
#           os.remove(mat_list[i])     

if __name__ == "__main__":
   main()
