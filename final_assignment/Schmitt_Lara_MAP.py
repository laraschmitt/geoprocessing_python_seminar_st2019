
# Geoprocessing with Python
# MAP ST 2019
# Schmitt, Lara

# ########################### LOAD REQUIRED LIBRARIES ########################################################## #
from osgeo import gdal, gdalconst
import time
import numpy as np
import pandas as pd
import random
import os
import ogr
import osr
import numpy as np
import os
import gdal
import sys
import warnings
import matplotlib.pyplot as plt
from sklearn.preprocessing import RobustScaler
from sklearn.model_selection import GridSearchCV
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import train_test_split


# ####################################### SET TIME-COUNT ###################################################### #
starttime = time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime())
print("--------------------------------------------------------")
print("Starting process, time: " + starttime)

# Suppress invalid numpy warning
warnings.filterwarnings('ignore')

# ########################### DEFINE INPUT DATA FOLDER PATH ##################################################### #

path = "E:/STUDIUM_Global_Change_Geography/M8_Geoprocessing/MAP/MAP_data/"
os.chdir(path)

# ########################### DEFINE OUTPUT FOLDER ############################################################# #

# create a new subfolder called "output"

newpath = "E:/STUDIUM_Global_Change_Geography/M8_Geoprocessing/MAP/MAP_data/output"
if not os.path.exists(newpath):
    os.makedirs(newpath)

os.chdir(newpath)

# ###########################  FUNCTIONS ######################################################################## #


# function to transform array position into x,y - coordinates
def pixel2coord(raster, x, y):
    xoff, a, b, yoff, d, e = raster.GetGeoTransform()

    xp = a * x + b * y + a * 0.5 + b * 0.5 + xoff
    yp = d * x + e * y + d * 0.5 + e * 0.5 + yoff
    return(xp, yp)

# function to create six step mean from array
def time_step_arr(array_to_step):
    # calculate the 6 time-step (8 bands) average to deal with the no data values: (6x8)
    step_1 = array_to_step[0:7, :, :]
    step_2 = array_to_step[8:15, :, :]
    step_3 = array_to_step[16:23, :, :]
    step_4 = array_to_step[24:31, :, :]
    step_5 = array_to_step[32:39, :, :]
    step_6 = array_to_step[40:48, :, :]

    steps = [step_1, step_2, step_3, step_4, step_5, step_6]
    # calculate average value
    seq = []

    for step in steps:
        average = np.nanmean(step, 0)
        seq.append(average)

    return np.stack(seq, axis=0)


# function to export array to geotiff
def export_array_to_geotiff(input_file_path, output_file_path, array):
    # open file
    in_ds = gdal.Open(input_file_path)

    if in_ds is None:
        print ('Could not open image file')
        sys.exit(1)

    #band1 = in_ds.GetRasterBand(1)
    rows = in_ds.RasterYSize
    cols = in_ds.RasterXSize

    # create the output image
    driver = gdal.GetDriverByName('GTiff')

    # print driver
    out_ds = driver.Create(output_file_path, cols, rows, 1, gdal.GDT_Float64, [])
    if out_ds is None:
        print ('Could not create tif')
        sys.exit(1)
    out_band = out_ds.GetRasterBand(1)

    # write the array
    out_band.WriteArray(array, 0, 0)

    # flush data to disk
    out_band.FlushCache()

    # georeference the image and set the projection
    out_ds.SetGeoTransform(in_ds.GetGeoTransform())
    out_ds.SetProjection(in_ds.GetProjectionRef())

    print("Writing file",output_file_path, " done", time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime()))

# ############################# REPROJECT LANDSAT FILE ######################################################## #

# open the input file
input = gdal.Open(path + 'landsat_TC/CHACO_TreeCover2015.bsq')
# get projection & geoTransform from landsat file
inputProj = input.GetProjection()
inputTrans = input.GetGeoTransform()

reference = gdal.Open(path + 'MODIS_EVI/MODIS_EVI_h0_v0.tif')
# get projection & geoTransform from modis  file
referenceProj = reference.GetProjection()
referenceTrans = reference.GetGeoTransform()
bandreference = reference.GetRasterBand(1)
#x = reference.RasterXSize

# one MODIS tile is 1000 x 1000
# 3 x 5 matrix of giles = 15 tiles
x = 3 * reference.RasterXSize
y = 4 * reference.RasterYSize + 800  # last row of tiles is shorter
# the export will have the size of the modis tiles extent

# create output file
outputfile = path + 'landsat_reprojected.tif'
driver= gdal.GetDriverByName('GTiff')
output = driver.Create(outputfile,x,y,1,bandreference.DataType)
output.SetGeoTransform(referenceTrans)
output.SetProjection(referenceProj)

# reproject image
gdal.ReprojectImage(input,output,inputProj,referenceProj,gdalconst.GRA_Bilinear)

del output

# import the resampled landsat tree cover dataset
resampled = path + 'landsat_reprojected.tif'

print("Reprojecting Landsat file done", time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime()))

# ################## GENERATE STRATIFIED RANDOM SAMPLE ACROSS MODIS EXTENT ###################################### #

# load one modis tile
modis = gdal.Open(path + 'MODIS_EVI/MODIS_EVI_h0_v0.tif')

# load resampled landsat image and read as array
landsat_res_img = gdal.Open(path + 'landsat_reprojected.tif')
landsat_res_arr = landsat_res_img.ReadAsArray()
treecover_arr = np.array(landsat_res_img.GetRasterBand(1).ReadAsArray()).astype(float)

# create a binary no data/ invalid data-mask
mask = np.logical_and(treecover_arr > 0, treecover_arr < 8905)
mask_reversed = np.logical_not(mask)

# apply mask
treecover_arr[mask_reversed] = -9999

# define min and max
min = 0
max = np.amax(treecover_arr)

# define classes for sampling in 20% steps
# class 1
class_0_20 = np.where(treecover_arr <= (0.2*max))
# class 2
class_20_40 = np.where(np.logical_and(treecover_arr >= (0.2*max), treecover_arr <= (0.4*max)))
# class 3
class_40_60 = np.where(np.logical_and(treecover_arr >= (0.4*max), treecover_arr <= (0.6*max)))
# class 4
class_60_80 = np.where(np.logical_and(treecover_arr >= (0.6*max), treecover_arr <= (0.8*max)))
# class 6
class_80_100 = np.where(np.logical_and(treecover_arr >= (0.8*max), treecover_arr <= (1*max)))

# store class-arrays in a list
list_classes = [class_0_20, class_20_40, class_40_60, class_60_80, class_80_100]

# define results array to store random point indices
result = np.zeros((10000, 3), dtype=np.int)


# fill array with 2000 random points per class:
# (because of later occuring no data value problem)
v1 = 0
v2 = 2000

for i in range(1,6):
    # generate 2000 random points (array indices) per class
    inds = np.transpose(list_classes[i-1])
    n_pixel = inds.shape[0]
    random.seed(42)
    indsel = inds[np.random.choice(n_pixel, 2000, replace=False), :]

    result[v1:v2, 0] = i   # = classvalue (from 1 to 5)
    result[v1:v2, 1:] = indsel
    v1 += 2000
    v2 += 2000

# put array in dataframe
df = pd.DataFrame(result)

print("Generating Random Points (pixel locations) done", time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime()))

# apply pixel2coord-function to transform array position into x,y - coordinates
rand_point_coords = []
for pixel in result:
    coord = pixel2coord(modis, pixel[2], pixel[1])  # tuple
    rand_point_coords.append((pixel[0], coord[0], coord[1]))  # list of tuples

# put list in dataframe
df2 = pd.DataFrame(rand_point_coords)
# concat the two dataframes
df_rand = pd.concat([df, df2],axis=1)

print("Generating Random Points (coordinates) done", time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime()))


# ######################## CALCULATE NEW MODIS BANDS AND JOIN TILES ###################################### #

# calculate the 6 time-step (8 bands) average to deal with the no data values: (6 x8)
modis_arr = []
for modis_file in os.listdir(path + 'MODIS_EVI'): # list of the entries in the directory
    tile = os.path.join(path + 'MODIS_EVI/' + modis_file) #os.path.join(path, *paths) builds a path string
    modis_tile = gdal.Open(tile)
    arr = modis_tile.ReadAsArray().astype(float) # (46, 1000, 1000)    # arr[1, 1:10, 1:10]

    # nodatavalues = -9999; replace with 0 to be able to calculate the mean
    arr[arr == -9999] = np.nan

    modis_arr.append(time_step_arr(arr))  # list of 15 6-d arrays

print("Calculating 6 time-step average arrays done ", time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime()))

# join the modis arrays to one big array
x = np.hstack([modis_arr[0], modis_arr[1], modis_arr[2]])

row_1 = np.concatenate([modis_arr[0], modis_arr[1], modis_arr[2]], axis = 2)
row_2 = np.concatenate([modis_arr[3], modis_arr[4], modis_arr[5]], axis = 2)
row_3 = np.concatenate([modis_arr[6], modis_arr[7], modis_arr[8]], axis = 2)
row_4 = np.concatenate([modis_arr[9], modis_arr[10], modis_arr[11]], axis = 2)
row_5 = np.concatenate([modis_arr[12], modis_arr[13], modis_arr[14]], axis = 2)

stacked = np.concatenate([row_1, row_2, row_3, row_4, row_5], axis = 1) # shape 46, 4800, 3000

print("Stacking MODIS arrays done", time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime()))

# transform rand points df to list
rand_points = df_rand.values.tolist() # list of lists

# extract values of the landsat treecover array and the modis mosaic array
for i in range(len(rand_points)):
    row = int(rand_points[i][1])
    col = int(rand_points[i][2])
    treecover_value = landsat_res_arr[row, col]
    rand_points[i].append(treecover_value)
    for band in range(6):
        row = int(rand_points[i][1])
        col = int(rand_points[i][2])
        evi_value = stacked[band, row, col]
        rand_points[i].append(evi_value)

print("Extracting Landsat treecover and MODIS EVI values done", time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime()))

# put list in dataframe
df_randpoints = pd.DataFrame(rand_points)

# drop rows with nan values
df_rand_cleaned = df_randpoints.dropna()

# split up the datasets into classes
df_1 = df_rand_cleaned[df_rand_cleaned[0] == 1]
df_2 = df_rand_cleaned[df_rand_cleaned[0] == 2]
df_3 = df_rand_cleaned[df_rand_cleaned[0] == 3]
df_4 = df_rand_cleaned[df_rand_cleaned[0] == 4]
df_5 = df_rand_cleaned[df_rand_cleaned[0] == 5]

# generate training dataset
# taking 125 points from class 1 and 2, 100 points from class 3 and 5 and 50 points from class 5
df_500 = pd.concat([df_1.sample(125), df_2.sample(125), df_3.sample(100),  df_4.sample(100), df_5.sample(50)])
list_500 = df_500.values.tolist()  # list of lists
print("Generating training dataset done", time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime()))

# ########################### EXPORT POINT SHAPEFILE  ######################################################### #

# set up the shapefile driver
driver = ogr.GetDriverByName("ESRI Shapefile")

# create an empty data source (called data.shp) by providing the data source name
# this data source is automatically open for writing
output = "random_points.shp"
datasource = driver.CreateDataSource(output)

if os.path.exists(newpath + output):
    driver.DeleteDataSource(output)
if datasource is None:
    sys.exit('Could not create {0}.'.format(output))

# create the spatial reference
wkt = modis.GetProjection()

srs = osr.SpatialReference()
srs.ImportFromWkt(wkt)

# create the layer
layer = datasource.CreateLayer(output, srs, ogr.wkbPoint)

# Add the field
layer.CreateField(ogr.FieldDefn("point_ID", ogr.OFTInteger))
layer.CreateField(ogr.FieldDefn("x_coord", ogr.OFTReal))
layer.CreateField(ogr.FieldDefn("y_coord", ogr.OFTReal))

# fill layer with features
point_id = 1
for pointCoord in list_500:
    # create point geometry
    point = ogr.Geometry(ogr.wkbPoint)
    point.AddPoint(pointCoord[4], pointCoord[5])

    # create the feature
    feature = ogr.Feature(layer.GetLayerDefn())
    # Set the attributes
    feature.SetField("point_ID", point_id)
    feature.SetField("x_coord", pointCoord[4])
    feature.SetField("y_coord", pointCoord[5])

    # Set the feature geometry
    feature.SetGeometry(point)

    # Create the feature in the layer (shapefile)
    layer.CreateFeature(feature)

    # Dereference the feature
    feature = None

    point_id += 1

# Save and close the data source
data_source = None

print("Feature <" + str(output) + "> successfully created.")
del output

print("Exporting point shapefile done", time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime()))

##########  PARAMETRIZE A GRADIENT BOOSTING REGRESSION USING THE SKICIT-LEARN PACKAGE  ######################## #

# ######## ARRANGE REFERENCE DATA IN RESPONSE VECTOR (y) AND PREDICTOR /FEATURE MATRIX (X)####################### #
# convert dataframe to ndarray
samples_arr = df_500.as_matrix()

# extract the response vector (y)
y_1 = samples_arr[:,6]

# expand dimensions since the shape has to be (n_samples,1)
y = np.expand_dims(y_1, 1)

# extract the predictor /feature matrix (x) by slicing the array
X= samples_arr[:, 7:13]

# ###########################STANDARDIZE THE DATA ############################################################## #

rbX = RobustScaler()
X = rbX.fit_transform(X)
rbY = RobustScaler()
y = rbY.fit_transform(y)

# ###########################SPLIT DATA INTO TRAINING AND TESTING SET########################################### #

#  split the data into a training and testing set (50/50)
x_train, x_test, y_train, y_test = train_test_split(X, y, test_size=0.5, random_state=42)

# ###########################GRID SEARCH CROSS VALIDATION ###################################################### #

# hyper parameter selection (grid search)
est = GradientBoostingRegressor(n_estimators=100)

# grid search cross-validation
param_grid = {'learning_rate': [0.1, 0.05, 0.02, 0.01],
              'max_depth': [4, 6],
              'min_samples_leaf': [1, 3, 9, 5, 17],
              'max_features': [1.0, 0.3, 0.1]}

grid = GridSearchCV(est, param_grid, cv=5, iid=False, n_jobs=3).fit(x_train, y_train.ravel())
grid.get_params()

model = grid.best_estimator_
y_fit = model.predict(x_test)

mse = mean_squared_error(y_test, y_fit)
print("Model Perfomance - mean squared error (MSE): %.4f" % mse)
print("Fitting best model done", time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime()))


# ######################## APPLY THE  MODEL TO MODIS DATA TO CREATE A TREECOVER MAP ############################### #

# did not succeed in implementing the parallel processing
# alternative: loop through each MODIS tile

current_file_path = None
for modis_file in os.listdir(path + 'MODIS_EVI'): # list of the entries in the directory
    print(modis_file)
    current_file_path = path + 'MODIS_EVI/' + modis_file
    tile = os.path.join(path + 'MODIS_EVI/' + modis_file) #os.path.join(path, *paths) builds a path string
    modis_tile =  gdal.Open(tile)
    arr = modis_tile.ReadAsArray().astype(float) # (46, 1000, 1000)    # arr[1, 1:10, 1:10]

    # nodatavalues = -9999; replace with nan to be able to calculate the mean
    arr[arr == -9999] = np.nan

    data = time_step_arr(arr)
    print("for", modis_file, "created array", time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime()))

    # preprocess data for prediction
    #  get first band & create binary mask for later masking
    band1 = data[0,:,:]
    # create nan_mask
    nan_mask =  np.isnan(band1)
    # set nan value to a high negative number
    data[np.isnan(data)] = -999999999999

    # transform shape of data to required shape: 2-d array: newshape(rows*cols, bands)
    bands, cols, rows = data.shape  # ndArray[row_index][col_index]
    data2d = np.reshape(data, (bands, rows*cols)).transpose()

    # prediction
    prediction = model.predict(rbX.transform(data2d))
    prediction = np.reshape(prediction, (cols, rows))
    prediction = rbY.inverse_transform(prediction)

    # mask out all nan values & non-valid values
    prediction[nan_mask] = np.nan   #-9999
    prediction[prediction < 0] = np.nan

    # calling export function
    output_file_name = current_file_path.replace('.tif', '') + '_processed.tif'
    output_file_p = output_file_name.replace('MODIS_EVI', 'output')
    export_array_to_geotiff(current_file_path, output_file_p, prediction)

out_ds = None

# ####################################### END TIME-COUNT AND PRINT TIME STATS ############################### #
endtime = time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime())
print("--------------------------------------------------------")
print("start: " + starttime)
print("end: " + endtime)
