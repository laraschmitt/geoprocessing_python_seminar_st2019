import numpy as np
from osgeo import gdal
import os
from matplotlib import pyplot as plt # import pyplot module from matplot library
import rasterio as rio


path = "E:/STUDIUM_Global_Change_Geography/M8_Geoprocessing/Assignment05/data"
os.chdir(path)

files = []
for dir_path, dir_name, file in os.walk(path):
    for f_name in file:
        if f_name.endswith(".tif"):
            files.append(os.path.join(dir_path, f_name))

# read forest mask
forest_mask = gdal.Open(files[0])
forest_mask_arr = forest_mask.ReadAsArray()  # 1: forest, 0: non-forest
forest_mask_arr.shape  # (461, 514)
# add dimension to forest mask
forest_mask_arr = np.expand_dims(forest_mask_arr, axis=0)   #shape (1, 461, 514)

# read vertex file
src_ds = gdal.Open(files[1])
src_arr = src_ds.ReadAsArray()
arc_ds = None
src_arr.shape   # (22, 461, 514)


vertex_year = src_arr[0:6, 370, 291]
# -> we have only 6 years (last was 0)  --> where is the 7th year?

vertex_fit = src_arr[14:20, 370, 291]

plt.plot(vertex_year, vertex_fit) # plt.show
# type %matplotlib in console to active inline plotting

%matplotlib

# create a subset of the array with only the fitted values
vertex_fit_arr = src_arr[14:21, :, :]  # shape (7, 461, 514)

# create a subset of the array with only the years
vertex_year_arr = src_arr[0:6, :, :]  # shape (6, 461, 514)

unique_val = np.unique(vertex_year_arr)

# calculate the change magnitude for every pixel with numpy.diff
# numpy.diff(arr, n=1, axis=-1)
# n = number of times values are differenced
# axis = the axis along which the difference is taken, default is the last axis
# The first difference is given by out[n] = a[n+1] - a[n] along the given axis, higher differences are calculated by using diff recursively

mag_arr = np.diff(vertex_fit_arr, n=1, axis=0)  # shape (6, 461, 514)

# identify the indices with the maximum magnitude using argmax
# numpy.argmax(a, axis=None, out=None) -> returns the indices of the maximum values along an axis

max_mag_arr = np.argmax(mag_arr, axis=0)  # shape (561,524), pixel values = range from 0-5
#np.amax(arr, axis) --> returns the maximum of an array or maximum along an axis

# add dimensions to max_mag_arr
max_mag_arr = np.expand_dims(max_mag_arr, axis=0)  # shape (1, 461, 514)

# linking the max_mag indices raster to the year raster using np.take_along_axis
# np.take_along_axis(source arr, indices: ndarray, axis)
max_mag_year_arr = np.take_along_axis(vertex_year_arr, max_mag_arr, axis=0)  # shape (1, 461, 514)

# mask out non- forest areas and magnitude values < 500
# (only magnitude values that are greater than 500 should be considered as change/ as disturbed)

# create array with maximum magnitude values
max_value_mag_arr = mag_arr.max(axis=0)

# create boolean array with maximum magnitude value >= 500 = 1 and <500 = 0
bool_valid_mag_arr = (max_value_mag_arr >= 500).astype(int)

# mask out respective values in the year array with array multiplication
masked_valid_mag_arr = max_mag_year_arr * bool_valid_mag_arr

# mask out non-forest pixels
masked_valid_mag_valid_forest_arr = masked_valid_mag_arr * forest_mask_arr   # shape (1, 461, 514)

# remove single-dimensional entry from the shape of the array
masked_valid_mag_valid_forest_arr = np.squeeze(masked_valid_mag_valid_forest_arr)  # shape (461, 514)


# export as GeoTiff
with rio.open(files[1]) as ras:
    data_ras = ras.read()
    ras_meta = ras.profile

# ras_meta:
# {'driver': 'GTiff', 'dtype': 'int16', 'nodata': None, 'width': 514, 'height': 461, 'count': 22,
# 'crs': CRS.from_dict(init='epsg:32633'),
# 'transform': Affine(30.0, 0.0, 487905.0, 0.0, -30.0, 5762925.0), 'tiled': False, 'interleave': 'pixel'}

# change count to 1
ras_meta['count'] = 1
# change datatype to 'int32'
ras_meta['dtype'] = 'int32'

# ras_meta = {'driver': 'GTiff', 'dtype': 'int32', 'nodata': None, 'width': 514, 'height': 461, 'count': 1,
# 'crs': CRS.from_dict(init='epsg:32633'),
# 'transform': Affine(30.0, 0.0, 487905.0, 0.0, -30.0, 5762925.0), 'tiled': False, 'interleave': 'pixel'}

with rio.open('E:/STUDIUM_Global_Change_Geography/M8_Geoprocessing/Assignment05/disturbance_years_output.tif', 'w', **ras_meta) as dst:
    dst.write(masked_valid_mag_valid_forest_arr)


# helper function plot disturbance year map
from matplotlib import pyplot as plt
from matplotlib import patches as mpatches
from matplotlib import colors

def plotDisturbanceYearMap(img):


    values = np.unique(img.ravel())
    values = values[values > 0]

    cmap = plt.get_cmap('jet', values.size)
    cmap.set_under('grey')
    norm = colors.BoundaryNorm(list(values), cmap.N)

    plt.figure(figsize=(8, 4))
    im = plt.imshow(img, interpolation='none', cmap=cmap, norm=norm)

    dist_colors = [im.cmap(im.norm(value)) for value in values]
    # create a patch (proxy artist) for every color
    patches = [mpatches.Patch(color=dist_colors[i], label=values[i]) for i in range(len(values))]
    # put those patched as legend-handles into the legend
    plt.legend(handles=patches, bbox_to_anchor=(1.05, 1), loc=2,
               borderaxespad=0., ncol=2, frameon=False)

    plt.grid(True)
    plt.show()

plotDisturbanceYearMap(masked_valid_mag_valid_forest_arr)


# histogram # reval your result to get the right image

a = masked_valid_mag_valid_forest_arr
histogram = np.histogram(a,bins = list(range(1987, 2019)))
hist,bins = np.histogram(a,bins = list(range(1987, 2019)))

plt.hist(a[a != 0], bins = list(range(1987, 2019)), alpha=0.5, histtype='bar', color = 'g',  ec='black')
plt.grid(axis='y', alpha=0.75)
plt.xlabel('Year')
plt.ylabel('Disturbance Frequency')
plt.title('Annual forest disturbance frequency between 1987 and 2018')
plt.xticks(np.arange(1987, 2019, 1), rotation='vertical')
plt.yticks(np.arange(0, 2700, 500))
