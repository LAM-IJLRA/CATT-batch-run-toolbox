%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%
%   CATT_batch_processing.m
%
%   Runs multiple simulations of TUCT2 and saves the IRs in .WAV and the 
%   measures in .MAT
%
%   If output files already exist in the output folder, the index of the 
%   will be automatically incremented so that preexisting files are not
%   overwritten.
%
%   The prediction settings (algorithm, number of rays, IR length, B-format
%   order etc.) must be defined in TUCT2 prior to running the script. If it
%   is desired to run the same geometric model with different prediction
%   settings, it is recommended to create one output folder for each set of
%   prediction settings, and save the .MD9 file with the desired output
%   folder before running the script (or alternatively, make copies of the 
%   entire project).
%
%   Before anything else:  
%       - enable auto-run-save hidden options. Copy the following code in
%       the hidden options  .txt files (same code for both):
%       CATT-A in CATTDATA\hidddenoptions_v9.txt:
%       C2009-05641-49C61-6B041 ;AutoRunSaveCAG
%       TUCT In CATTDATA\hidddenoptions_TUCT.txt:
%       C2009-05641-49C61-6B041 ;AutoRunSave
%       - define the path of CATT application in the GLOBAL VARIABLES 
%       section below
%
%   Input parameters must be defined in the INPUT PARAMETERS section below:
%
%   - nof_runs: number of consecutive runs
%
%   - output_format: a list of strings among 'MEAS' (metrics stored in a 
%   .MAT file), 'BIN' (binaural IR) in .WAV, 'BF' (B-format, order 
%   depending on the predefined prediction settings, following the ACN
%   ordering convention) in .WAV, and 'OMNI' (omnidirectional IR) in .WAV
%
%   - InputFolder and MDLfile: the CATT project file
%
%   - OutputFolder: the output folder where the IRs will be stored. MUST BE
%   THE SAME AS THAT DEFINED IN THE GENERAL SETTINGS OF CATT
%
%   - Project: the name of your project/room
%
%   Julien De Muynke
%   23-02-2021
%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

%% GLOBAL VARIABLES

%the CATT folder
CATTfolder = 'C:\Program Files (x86)\CATT';  %FILL IN!
%the full path of catt9.exe
CATT9 = fullfile(CATTfolder, 'catt9.exe'); 
%the full path of tuct.exe
TUCT = fullfile(CATTfolder,'tuct2.exe');

%% INPUT PARAMETERS

% Number of consecutive runs
nof_runs = 1;

% Desired IR formats
output_format = {'MEAS','BIN','BF','OMNI'};

%Project input folder from General settings
InputFolder = 'C:\Users\Julien\Documents\CATTDATA\Amphi55a\#X';  %FILL IN!
%the CATT-A Modeling project file
MDLfile = fullfile(InputFolder,'CATT.MD9'); %FILL IN!

%Project output folder from General settings
OutputFolder = 'C:\Users\Julien\Documents\CATTDATA\Amphi55a\#X\OUTPUT'; %FILL IN!

% %the CATT-A Modeling source-file name, i.e. the file to 
% %be rewitten each loop iteration:
% SRCfile = fullfile(InputFolder,'SRC.LOC'); %FILL IN!

%Project name from General settings, CAG-file name is based on it:
Project = 'Amphi55a'; %FILL IN!

%% COUNT.DAT file

%the basename of the CAG to which _2.CAG,_3.CAG etc. 
%will be added each iteration, the latest count will
%be read from Cntfile
CAGBase = [fullfile(OutputFolder,Project) '_'];%count.DAT'); 
Cntfile = [ CAGBase 'count.DAT' ];

%% -- processing loop --

%create the string containing all the output formats
format_str = '';
for i = 1:length(output_format)
    format_str = [format_str ',' char(output_format(i))];
end
format_str = format_str(2:end);

%get the appended CAG-file cnt (a single 32-bit integer)
if exist(Cntfile,'file')
    fid = fopen(Cntfile,'rb');
    cnt = fread(fid,1,'int32');
    fclose(fid);
else
    cnt = 0;
end

%loop count, or use while
for k = cnt+1:cnt+nof_runs

    %-- run CATT-A to create a new CAG -- 
    ret = system( ['"' CATT9 '" "' MDLfile '"' ' /AUTO'] );
    if ret ~= 0
        disp('script failed for CATT9'); return
    end
       
    %-- run TUCT with the new CAG --
    CAGfile = [CAGBase num2str(k) '.CAG'];
    
    ret = dos( ['"' TUCT '" "' CAGfile '"' ' /AUTO /SAVE:' format_str] );

    if ret ~= 0
        %type error file
        disp('script failed for  TUCT:'); 
        %eval(['type ' num2str(k) '_autorun_error.TXT' ]);
        %return
    end
    
    k = k + 1;

end 

%% Convert .MAT into .WAV

list = dir([OutputFolder '\*.mat']);
ACN = {'W','Y','Z','X','V','T','R','S','U','Q','O','M','K','L','N','P'};

for i = 1:length(list)
    
    fname = list(i).name;
    suffix_idx = strfind(fname,'_A');
    ir_name = ['h_' fname(suffix_idx+1:end-4)];
    mat_struct = load(fullfile(OutputFolder,fname));
    
    if contains(fname,'OMNI')
        audiowrite(fullfile(OutputFolder,[fname(1:end-4) '.WAV']),eval(['mat_struct.' ir_name]),mat_struct.TUCT_fs,'BitsPerSample',32);
        delete(fullfile(OutputFolder,fname));
        clear mat_struct;
    elseif contains(fname,'BIN')
        audiowrite(fullfile(OutputFolder,[fname(1:end-4) '.WAV']),transpose(eval(['[mat_struct.' ir_name '_L;mat_struct.' ir_name '_R]'])),mat_struct.TUCT_fs,'BitsPerSample',32);
        delete(fullfile(OutputFolder,fname));
        clear mat_struct;
    elseif contains(fname,'BF')
        nof_channels = numel(fieldnames(mat_struct))-1;
        str = '';
        for j = 1:nof_channels
            str = [str ['mat_struct.' ir_name '_' char(ACN(j))] ';'];
        end
        output_file = ['[' str(1:end-1) ']'];
        audiowrite(fullfile(OutputFolder,[fname(1:end-4) '.WAV']),transpose(eval(output_file)),mat_struct.TUCT_fs,'BitsPerSample',32);
        delete(fullfile(OutputFolder,fname));
        clear mat_struct;
    end
    
end