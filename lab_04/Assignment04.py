import numpy as np
import rasterio as rio
import gdal
import os

path = "E:/STUDIUM_Global_Change_Geography/M8_Geoprocessing/Assignment04/landsat8_2015"

os.chdir(path)  # change directory to path

# using os.walk
files = []
for dir_path, dir_name, file in os.walk(path):
    for f_name in file:
        if f_name.endswith(".tif"):
            files.append(os.path.join(dir_path, f_name))


# 1) build mask: create a function that reads a single QA file and returns a Boolean numpy array
# (true = 1 : good observations, false = 0 : invalid observations).
# pixel codes QA raster:
# 0: clear land pixel -> good
# 1: clear water pixel -> good
# 2: cloud shadow
# 3: snow -> good
# 4: cloud
# 255: fill value

# loops take too long on array, use vectorize operations!

def build_mask(qa_arr):
    # logical operation to find out which pixel is valid:
    bool_arr = ((qa_arr == 0) | (qa_arr == 1) | (qa_arr == 3)).astype(int)
    return bool_arr


# SR_arr = gdal.Open(files[1]).ReadAsArray()
# QA_arr = gdal.Open(files[0]).ReadAsArray()  ## this has to go in the build mask function!!

# npditer = multidim iterator object, short for "for row in QA_arr: for column in QA_arr:


# function: cloudmask for a single file
def mask_image(sr_filename):   # input:# filename
    # open SR file with gdal and read it as numpy array
    sr_arr = gdal.Open(sr_filename).ReadAsArray()
    # identify corresponding QA file with replace(pattern, replacement)
    qa_arr = gdal.Open(sr_filename.replace("sr", "qa")).ReadAsArray()
    # use build_mask() function to retrieve the correct mask array
    mask_arr = build_mask(qa_arr)
    # apply broadcasting to apply the mask_arr(1 dim) to SR(6 dim) // multiplication of the two arrays
    # sr dim (6, 1000,1000); qa dim (1000,1000) -> add a dimension
    masked_arr = sr_arr * mask_arr
    # convert sr array (int) to floating point array (integer arrays must not have NAs!)
    masked_arr = masked_arr.astype(float)
    # convert 0 in the array to no data value(NA)
    masked_arr[masked_arr == 0] = 'nan'  #  other way round: arr(np.isnan(arr) = 0

    return masked_arr # ouput: array

# check for masked_arr.shape: has to be (6, 1000, 1000)
    # add fourth dimension (time)
    x1_ext = np.expand_dims(x1, axis=0)
# input=data.transpose(2,0,1) for changing the order of the axis


# 3) function to calculate a mean composite
def mean_compos(sr_filenames): # input list of filenames
    # find sr_files and apply mask_image with map function and put them in list
    def find_sr(element):
        if 'sr' in element:
            return True
    list_3darrays = list(map(mask_image, filter(find_sr, sr_filenames)))
    # join the 3d arrays to a 4d array with np.stack
    arr_stack = np.stack(list_3darrays, axis=0)  #  join a sequence of arrays along a new axis, if axis = 0, it will be the first dim.
    # apply np.nanmean(array, axis)
    arr_stack_mean = np.nanmean(arr_stack, axis=0)  # multi-dimensional aggregations, axis specifies the axid along which the aggregate is computed

    return arr_stack_mean # ouput: 6-band image where each band and pixel represent the mean across time


arr_stack_mean = mean_compos(files)


# export numpy array to raster geotif using rasterio module:
# Create a new raster object with all of the metadata needed to define it. This metadata includes:
# the shape (rows and columns) of the object
# the coordinate reference system (crs)
# the type of file (you will export a geotiff (.tif) in this lesson
# and the type of data being stored (integer, float, etc).


with rio.open(files[1]) as ras:
    data_ras = ras.read()
    ras_meta = ras.profile

ras_transform = ras_meta["transform"]
ras_crs = ras_meta["crs"]

# change datatype from int to float
ras_meta['dtype'] = "float64"

# ras_meta = {'driver': 'GTiff', 'dtype': 'float64', 'nodata': -9999.0, 'width': 1000, 'height': 1000, 'count': 6,
# 'crs': CRS.from_dict(init='epsg:32633'),
# 'transform': Affine(30.0, 0.0, 364335.0, 0.0, -30.0, 5830485.0), 'tiled': False, 'interleave': 'pixel'}

with rio.open('E:/STUDIUM_Global_Change_Geography/M8_Geoprocessing/Assignment04/mean_output.tif', 'w', **ras_meta) as dst:
    dst.write(arr_stack_mean)


# 4) function to calculate Max NDVI composite

# arr_layer [0] - blue; [1] - green, [2] - red, [3] - NIR, [4] - SWIR 1, [5] - SWIR 2
# NDVI formula: (NIR - Red)/(NIR + Red)
# in a maximum NDVI composite each pixel contains the band values that correspond with the date of maximum NDVI
# hence, each pixel will represent the original band values that were recorded at the date of maximum
# vegetation greenness

# find sr_files and apply ndvi function with map function and put them in list

def ndvi(sr_filename):
    sr_arr = gdal.Open(sr_filename).ReadAsArray()
    ndvi_arr = np.subtract(sr_arr[3], sr_arr[2]) / np.add(sr_arr[3], sr_arr[2])
    return ndvi_arr


def max_NDVI_compos(sr_filenames):# input: filename # NDVI function:
    def find_sr(element):
        if 'sr' in element:
            return True

    list_NDVI_arrays = list(map(ndvi, filter(find_sr, sr_filenames))) # list of 2d arrays

    # join the 2d arrays to a 3d array with np.stack
    ndvi_stack = np.stack(list_NDVI_arrays, axis=0)   # shape = (17, 1000, 1000)


    # apply np.nanmean(array, axis)
    arr_stack_ndvi = np.nanmax(ndvi_stack, axis=0)  # multi-dimensional aggregations, axis specifies the axid along which the aggregate is computed

    return arr_stack_ndvi


# export numpy array as tif:



# ras_meta = {'driver': 'GTiff', 'dtype': 'float64', 'nodata': -9999.0, 'width': 1000, 'height': 1000, 'count': 6,
# 'crs': CRS.from_dict(init='epsg:32633'),
# 'transform': Affine(30.0, 0.0, 364335.0, 0.0, -30.0, 5830485.0), 'tiled': False, 'interleave': 'pixel'}


# change count to 1
ras_meta['count'] = 1
# add dimension to output
arr_stack_ndvi_3d = np.expand_dims(arr_stack_ndvi, axis=0)

with rio.open('E:/STUDIUM_Global_Change_Geography/M8_Geoprocessing/Assignment04/ndvi_output.tif', 'w', **ras_meta) as dst:
    dst.write(arr_stack_ndvi_3d)