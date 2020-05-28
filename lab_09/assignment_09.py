### assignment_09 task 1
# ####################################### LOAD REQUIRED LIBRARIES ############################################# #

import time
from osgeo import gdal, gdalnumeric, ogr, osr
import pandas as pd
import os
import sys
import random
import math
import numpy as np
import statistics

# ####################################### SET TIME-COUNT ###################################################### #
starttime = time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime())
print("--------------------------------------------------------")
print("Starting process, time: " + starttime)
print("")
# ####################################### FUNCTIONS ########################################################### #

import osr
def CS_Transform(geom, LYRto):
    ''' Function that creates the ruling for a coordinate transformation of a geometry to the geometry of a second layer.
        Is often used when doing point-intersections or zonal summaries over vectors. To reduce the amount of calculations
        this trnasformation should be defined prior to the actual processing of the geometries.

    Parameters
    -----------
    geom : object (required)
        geometry object, retrieve through: feat.GetGeometryRef()
    LYRto : object (required)
        layer object of the layer with the coordinate system we want to transform into

    Returns
    --------
    transform : object
        transformation rule for the geo-transformation
    '''
    outPR = LYRto.GetSpatialRef()
    inPR = geom.GetSpatialReference()
    transform = osr.CoordinateTransformation(inPR, outPR)
    return transform

# ####################################### FOLDER PATHS & global variables ##################################### #
# Folder containing the working data
path = "E:/STUDIUM_Global_Change_Geography/M8_Geoprocessing/Assignment09/Assignment09_data/"
os.chdir(path)

# ####################################### LOAD DATA  ######################################################### #

#lucas shapefile
lucas_points = ogr.Open(path + 'EU28_2015_20161028_lucas2015j.gpkg')
lucas_points_layer = lucas_points.GetLayer()
print('feat count', lucas_points_layer .GetFeatureCount())


# classified map
lcImg = gdal.Open(path + 'landcover_lucas2015_15000_10000.tif').ReadAsArray()

# print(lcImg[0:10,0:25])

# landsat 8 image
l8Img = gdal.Open(path + 'landsat_median1416_15000_10000.tif').ReadAsArray()
# Raster image of 6 layers showing the median Landsat-8, EPSG 3035
# band 2 (blue), 3 (red), 4 (green), 5 (near-IR), 6 (SWIR-1), 7 (SWIR-2)

#band_value = l8Img[5, 5, 7]

# the two rasters have the same extent --> can be treated as arrays with the same size


# ##################### DEFINE FINAL DATAFRAME ############################################################# #

# define final dataframe for collecting results and later export

df = pd.DataFrame(columns={'Class': [],
                           'Band 2 (blue) mean': [],
                           'Band 3 (red) mean': [],
                           'Band 4 (green) mean': [],
                           'Band 5 (near-IR) mean': [],
                           'Band 6 (SWIR-1) mean': [],
                           'Band 7 (SWIR-2) mean': [],
                           })


# define type per column
df = df.astype(dtype={'Class': 'int64',
                           'Band 2 (blue) mean': 'int64',
                           'Band 3 (red) mean': 'int64',
                           'Band 4 (green) mean': 'int64',
                           'Band 5 (near-IR) mean': 'int64',
                           'Band 6 (SWIR-1) mean': 'int64',
                           'Band 7 (SWIR-2) mean': 'int64',
                           })

# delete existing csv file on disk
if os.path.exists('output_assignment9_task1.csv'):
    os.remove('output_assignment9_task1.csv')
    print('existing file deleted')

# ##################### RANDOM STRATIFIED SAMPLE ############################################################# #

# sample land cover map at each 17th pixel/ array slicing --> subset
# place random seed between 0 and 17
np.random.seed(42)

#x = np.random.seed(4)
#y = np.random.seed(3)

# put x and y as start point// did not work

lcImgSubset = lcImg[::17, ::17]

#i = 0
for LC_class in np.unique(lcImgSubset):   # get the represented classes/ not all 12 classes are represented
    print(LC_class) # 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11

    indices = np.transpose((np.where(lcImg == LC_class))) # get the pixel coordinates/ indices
    # np.where -> result: 2-dim arr, the first array represents the indices in first dim (row) and the second arr in second dim (col)
    # np.transpose -> permutes the dimension of the given array [[r, c], [r, c], ...]


    print('indices shape', indices.shape)
    # generate 1000 random indices from the length of the first dimension of the 2d indices array
    #np.random.seed(42)
    random_indices = np.random.choice(indices.shape[0], 1000, replace=False)
    # np.  numpy.random.choice(array, size, replace=True/False, probability=None/default uniform distr.)
    # -> generates a random sample from a given 1-D array -> get an index vector
    # shape -> returns the lenght of axis
    # print(random_indices)

    # get a list of indices
    ind_selected = indices[random_indices, :]
    ind_selected_list = ind_selected.tolist()
    # print('ind_selected:', ind_selected)

    # extract the corresponding landsat band values

    mean_0 = 0
    mean_1 = 0
    mean_2 = 0
    mean_3 = 0
    mean_4 = 0
    mean_5 = 0

    for band_numb in range(0, 6):
        band_values_list = []
        for position_pair in ind_selected_list:
            band_value = l8Img[band_numb, position_pair[0], position_pair[1]]
            band_values_list.append(band_value)
            # print(LC_class, 'all band values', band_values_list)

        print(LC_class, 'length', len(band_values_list))
        mean_list = statistics.mean(band_values_list).astype(int)

        print('class', LC_class, 'band', band_numb + 2, 'mean', mean_list)


        if band_numb == 0:
            mean_0 = mean_list
        if band_numb == 1:
            mean_1 = mean_list
        if band_numb == 2:
            mean_2 = mean_list
        if band_numb == 3:
            mean_3 = mean_list
        if band_numb == 4:
            mean_4 = mean_list
        if band_numb == 5:
            mean_5 = mean_list

            ################ FILL DATAFRAME ###########################################################

    df = df.append({'Class': LC_class,
                    'Band 2 (blue) mean': mean_0,
                    'Band 3 (red) mean': mean_1,
                    'Band 4 (green) mean': mean_2,
                    'Band 5 (near-IR) mean': mean_3,
                    'Band 6 (SWIR-1) mean': mean_4,
                    'Band 7 (SWIR-2) mean': mean_5,
                    }, ignore_index=True)

        ################ EXPORT  DATAFRAME ##########################################################

    if LC_class == 1:
        df.to_csv(path + "output_assignment9_task1.csv", header=True, mode='a', index=False,
                  encoding='utf-8')
    else:
        df.to_csv(path + "output_assignment9_task1.csv", header=False, mode='a', index=False,
                  encoding='utf-8')
    df.drop(df.index, inplace=True)

    #i += 1
    #if i == 3:
    #    break

#### PRINT DATAFRAME
    #import matplotlib.pyplot as plt
    #df = pd.DataFrame(...)
    #plt.figure()
    #df.plot()


# ####################################### END TIME-COUNT AND PRINT TIME STATS##################
print("")
endtime = time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime())
print("--------------------------------------------------------")
print("start: " + starttime)
print("end: " + endtime)
print("")


