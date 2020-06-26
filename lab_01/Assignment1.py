# Geoprocessing in Python
# Assignment I - Basic python scripting

# ####################################### LOAD REQUIRED LIBRARIES ########################################
import os # os = operating system
## the OS module provides a way of using operating
## system dependent functionality -> allows to interface with the underlying
## operating system (Windows, Mac, Linux)
# os.getcwd() -> return current working directory
# os.uname() -> return information identifiying current os
# os.chroot(path) -> change the root directory of the current process to path
# os.listdir(path) -> return a list of the entries in the directory given by path
# os.path.isdir(path) -> return true if path is an existing directory

import re # re = regular expression operations
# a regular expression specifies a text string used for describing a search pattern
# '.' (dot) in the default mode, this matches any character except a newline
# '^' (caret.) matches the start of the string
# '$' matches the end of the string

## define path to local folder
path = '<PATH_TO_YOUR_DATA_FOLDER>'

####################################### PART 1.1  ########################################################
## The Landsat sensor family has now overall four satellites (L4, L5, L7, L8), and for each of the four 
# we have a different number of scenes available. Please assess for each footprint, how many scenes from 
# each individual sensor are located in the folders.

# Define patterns for all satellite (Pattern Matching)
string08 = '^LC08' # '^' (caret) matches the start of the string
string07 = '^LE07'
string05 = '^LT05'
string04 = '^LT04'

# for-loop
for foot in os.listdir(path): # list of the entries in the directory
    footy = os.path.join(path, foot)   #os.path.join(path, *paths) builds a path string
    if os.path.isdir(footy):  # returns true if path is an existing directory

        # Create count variables (empty)
        count01 = 0
        count08 = 0
        count07 = 0
        count05 = 0
        count04 = 0

        for scenes in os.listdir(footy):  #nested loop
            if re.match(string08, scenes):   # re.match(pattern, string)
                count08 += 1
            if re.match(string07, scenes):
                count07 += 1
            if re.match(string05, scenes):
                count05 += 1
            if re.match(string04, scenes):
                count04 += 1
        print("The",foot,"footprint has ", count08, "Landsat 8 scenes")
        print("The",foot,"footprint has ", count07, "Landsat 7 scenes")
        print("The",foot,"footpring has ", count05, "Landsat 5 scenes")
        print("The",foot,"footpring has ", count04, "Landsat 4 scenes")


####################################### PART 1.2  ########################################################
#(a) count the number of scenes that do not have the “correct” number of files in them (caution: the 
# number of files may vary between the different sensors!); and (b) generate a text-file, in which each 
# corrupt scene (i.e., the entire file path) is written as an individual line.

# Define file number for each Satellite
filenum08 = 19
filenum07 = 19
filenum05 = 21
filenum04 = 21

# Create count variables (empty)
missings = 0

# open a file with the open() function
# file_object = open("filename", "mode")
# mode tells the interpreter and developer which way the file will be used
# 'r' - read mode
# 'w' . write mode
# 'w+' - overwrites the file if it exists
# 'a' - appending mode
# 'r+' - special read and write mode
# file.write("...") -> write in file
f = open("Corrupt_Scenes.txt", "w+")

for foot in os.listdir(path):
    footy = os.path.join(path, foot)

    if os.path.isdir(footy):

        # Create count variables (empty)
        count01 = 0
        count08 = 0
        count07 = 0
        count05 = 0
        count04 = 0

        for scenes in os.listdir(footy):
            scenesy = os.path.join(footy, scenes)

            if re.match(string08, scenes):
                list = os.listdir(scenesy)
                number_files = len(list) #method len() returns the number of elements in the list
                if filenum08 != number_files:
                    missings += 1
                    a = os.path.join(path, scenes)
                    f.write(scenes + os.linesep)

            if re.match(string07, scenes):
                list = os.listdir(scenesy)
                number_files = len(list)
                if filenum07 != number_files:
                    missings += 1
                    a = os.path.join(path, scenes)
                    f.write(scenes + os.linesep)

            if re.match(string05, scenes):
                list = os.listdir(scenesy)
                number_files = len(list)
                if filenum05 != number_files:
                    missings += 1
                    a = os.path.join(path, scenes)
                    f.write(scenes + os.linesep)

            if re.match(string04, scenes):
                list = os.listdir(scenesy)
                number_files = len(list)
                if filenum04 != number_files:
                    missings += 1
                    a = os.path.join(path, scenes)
                    f.write(scenes + os.linesep)

f.close()
print("In sum",missings,"scenes are incomplete")


####################################### PART 2.1  ########################################################
# Check the number of SHP-files and the number of raster-files that are in the folder (again: for the purpose of
# data storage, these are only dummy files). Please make sure that you only count the number of layers and 
# not the number of files (e.g., a SHP-file is composed of more than one file, the same may be true for 
# raster-files). Once you have your results, please upload them for both layer types (vector and raster) 
# into moodle under question 4.

path = '<PATH_TO_YOUR_DATA_FOLDER>'

raster_len = len([file for file in os.listdir(path)
               if file.endswith('.tif') and os.path.isfile(os.path.join(path, file))])

shape_len = len([file for file in os.listdir(path)
               if file.endswith('.shp') and os.path.isfile(os.path.join(path, file))])

print("The directory includes:", raster_len, "raster layers")
print("The directory includes:", shape_len, "vector layers")


####################################### PART 2.2  ########################################################
# Some layers are incomplete, which is particularly true for the vector layers (i.e., the SHP-files). Some 
# of them are missing a dbf-file, while for others the projection information is missing. The task is to 
# identify these layers. Please submit into moodle under question 5 the number of incomplete vector and 
# raster layers. Under question 6 then provide a list of the layer names.

list_directory = os.listdir(path)
incom_vec = []

f = open("Corrupt_Shapes.txt", "w+")

for name in list_directory:

    if name.endswith('.shp'):
        dbf_files = re.sub('.shp', ".dbf", name)
        prj_files = re.sub('.shp', ".prj", name)

        if dbf_files not in list_directory:
            incom_vec.append(dbf_files)
            f.write(dbf_files  + os.linesep)

        if prj_files not in list_directory:
            incom_vec.append(prj_files)
            f.write(prj_files + os.linesep)

f.close()


print(len(incom_vec))
