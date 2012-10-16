import subprocess
import os
import sys
import shutil
##
workingDir=r"\\libgrsurya\IDEALS_ETDS\ETD_Metadata_Files\Create_Folder_Test_Folder"
dirlist=os.listdir(workingDir)
for file in dirlist:
    path=workingDir+"\\"+file
    newDir=path[:-4]
    os.mkdir(newDir)
    shutil.move(path, newDir)
##
##comment out above and uncomment this to reverse:
##workingDir="C:\Users\srobbins\Desktop\OutPut\Create_File_Test_Folder"
##os.chdir(workingDir)
##dirlist=os.listdir(workingDir)
##for somedir in dirlist:
##    path=workingDir+"\\"+somedir
##    pathtofile=workingDir+"\\"+somedir+"\\"+somedir+".PDF"
##    shutil.move(pathtofile, workingDir)
##    os.rmdir(path)
    
    
    
    
print dirlist


