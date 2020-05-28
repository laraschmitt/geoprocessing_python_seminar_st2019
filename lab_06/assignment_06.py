
# ####################################### LOAD REQUIRED LIBRARIES ############################################# #

import time
from osgeo import ogr
import numpy as np
import pandas as pd
import os
import sys

# ####################################### SET TIME-COUNT ###################################################### #
starttime = time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime())
print("--------------------------------------------------------")
print("Starting process, time: " + starttime)
print("")
# ####################################### FUNCTIONS ########################################################### #

# ####################################### FOLDER PATHS & global variables ##################################### #
# Folder containing the working data
path = "E:/STUDIUM_Global_Change_Geography/M8_Geoprocessing/Assignment06/data/"
# os.chdir(path)

#####################################PRE-PROCESSING SHAPEFILE ##############################################
'''
# read countries shapefile and get layer
countries_ds = ogr.Open(path + 'gadm36_dissolve.shp', 1)  # # 0 means read-only. 1 means writeable.
if countries_ds is None:
    sys.exit('Could not open {0}.'.format(fn))
countries_lyr = countries_ds.GetLayer(0)

# read protected areas (PA) shapefile and get layer
pa_ds = ogr.Open(path + 'WDPA_May2019-shapefile-polygons.shp', 1)
if pa_ds is None:
    sys.exit('Could not open {0}.'.format(fn))
pa_lyr = pa_ds.GetLayer(0)

# in shapefile:
# column = attribute field
# row = feature


# remove all entries with field 'MARINE' == '2'
for feat in pa_lyr:
    # print(feat.GetField('MARINE'))
    if feat.GetField('MARINE') == '2':
        print("delete")
        pa_lyr.DeleteFeature(feat.GetFID())
pa_lyr.SyncToDisk() #  close  files or call SyncToDisk to flush edits to disk
# --> reduced number of rows from 222016 to 217381

# load in reduced dataset
pa_ds_red = ogr.Open(path + 'WDPA_May2019-shapefile-polygons.shp', 1)
# get layer count of the dataset
print(pa_ds_red.GetLayerCount())  #  just one layer

# get the layer and assign it to variable
pa_lyr_red = pa_ds_red.GetLayer(0)
# get the name of the layer
print(pa_lyr_red.GetName())  # WDPA_May2019-shapefile-polygons

# get the feature count
print(pa_lyr_red.GetFeatureCount()) # 217380

# iterating over features:
#for feat in pa_lyr_red:
 # print (feat.GetField("NAME"))

# print column names and their field type

layerDef = pa_lyr.GetLayerDefn()

for i in range(layerDef.GetFieldCount()):
    fieldName = layerDef.GetFieldDefn(i).GetName()
    fieldTypeCode = layerDef.GetFieldDefn(i).GetType()
    fieldType = layerDef.GetFieldDefn(i).GetFieldTypeName(fieldTypeCode)
    print(fieldName, fieldType)


# much shorter way to do this: use the schema property on the layer object to get a list
# of FieldDefn objects. Each of these contains information such as the attribute column
# name and data type.
for field in pa_lyr_red.schema:
    print(field.name, field.GetTypeName())

# create a subset of columns 'NAME' (string), 'REP_AREA' (real = float?), 'STATUS_YR' (integer64), 'IUCN_CAT (string)'
#using SQL:

sql = 'SELECT NAME, REP_AREA, STATUS_YR, IUCN_CAT FROM "WDPA_May2019-shapefile-polygons"'
ds = pa_ds_red.ExecuteSQL(sql)

layerDef = ds.GetLayerDefn()
layerDef.GetFieldCount()  # 4 Fields

for field in ds.schema:
    print(field.name) # NAME IUCN_CAT REP_AREA STATUS_YR

'''

##############################CREATE PROTECTED AREA SUMMARY ##############################################

prot = ogr.Open(path + 'gadm36_dissolve.shp', 0)  # 0 = read-only
countries = ogr.Open(path + 'gadm36_dissolve.shp', 0)

# define final dataframe for collecting results and later export
df = pd.DataFrame(columns={'Country_ID': [],
                           'Country_Name': [],
                           'PA_Category': [],
                           '#_PAs': [],
                           'Mean_area_of_PAs': [],
                           'Area_of_largest_PA': [],
                           'Name_of_largest_PA': [],
                           'Year_of_establ._Of_largest_PA': []
                           })
# check columnn names
list(df)


i = 0
for c in countries.GetLayer(0):
    country_name = c.GetField('NAME_0')  # get attribute value for NAME_0
    print(country_name)
    pro = prot.GetLayer()  # get layer of proteced area shape
    pro.SetSpatialFilter(c.geometry())  # SetSpatialFilter(layer, geometry filter) # feat.geometry() -> grabs the geometry
    feat_count = pro.GetFeatureCount()  # GetFeatureCount for respective country

    print("done setting spatial filter: " + time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime()))

    # if no protected areas are found
    if feat_count == 0:    # if the feature count is 0
        df = df.append({'Country ID': i,
                        'Country Name': country_name,
                        'PA Category': "all",
                        '# PAs': 0,
                        'Mean area of PAs': np.nan,
                        'Area of largest PA': np.nan,
                        'Name of largest PA': np.nan,
                        'Year of establ. Of largest PA': np.nan}, ignore_index=True)
        pro.SetSpatialFilter(None)    # remove spatial filter by passing None to SetSpatialFilter.
        print("done getting features: " + time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime()))
        print("no protected areas found")
        i += 1
    else:
        PA_DEF = np.empty(feat_count, dtype='U25') # create empty numpy arrays taking the featcount as shape/size
        area = np.empty(feat_count)
        names = np.empty(feat_count, dtype='U25')
        years = np.empty(feat_count, int)
        j = 0  # new iterator
        for feat in pro:  # to loop through the layer while the spatial filter is active
            PA_DEF[j] = feat.GetField('IUCN_CAT')  # fill the arrays with the field values
            area[j] = feat.GetField('REP_AREA')
            names[j] = feat.GetField('NAME')
            years[j] = feat.GetField('STATUS_YR')
            j += 1
        pro.SetSpatialFilter(None)
        print("done getting features: " + time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime()))

        df = df.append({'Country ID': i,
                        'Country Name': country_name,
                        'PA Category': "all",
                        '# PAs': feat_count,
                        'Mean area of PAs': np.mean(area),  # calculate the mean of the area array
                        'Area of largest PA': max(area),    # get the maximum value of the area array
                        'Name of largest PA': names[np.argmax(area)], # get the indice of of maximum value, put indice in arr[i]
                        'Year of establ. Of largest PA': years[np.argmax(area)]}, ignore_index=True)

        # do sub within country
        for type in np.unique(PA_DEF):   # unique IUCN categories
            bool_sub = PA_DEF == type  # logical operation: if the values of PA_DEF and type are equal, then true
            area_tmp = area[bool_sub]

            df = df.append({'Country ID': i,
                            'Country Name': country_name,
                            'PA Category': type,
                            '# PAs': len(area_tmp),
                            'Mean area of PAs': np.mean(area_tmp),
                            'Area of largest PA': max(area_tmp),
                            'Name of largest PA': names[bool_sub][np.argmax(area_tmp)],
                            'Year of establ. Of largest PA':  years[bool_sub][np.argmax(area_tmp)]}, ignore_index=True)

        print("done calculating metrics: " + time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime()))
        print("")
        i += 1

    # for testing set number of loops
    #if i == 5:
    #    break

df.to_csv("E:/STUDIUM_Global_Change_Geography/M8_Geoprocessing/Assignment06/df_output_sig.csv", index=False, float_format='%.2f', encoding='utf-8-sig')







# ####################################### END TIME-COUNT AND PRINT TIME STATS##################
print("")
endtime = time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime())
print("--------------------------------------------------------")
print("start: " + starttime)
print("end: " + endtime)
print("")
