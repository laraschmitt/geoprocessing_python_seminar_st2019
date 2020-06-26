import os
import gdal
import numpy as np
from shapely.geometry import box
from functools import reduce

path = '<PATH_TO_YOUR_DATA_FOLDER>'
os.chdir(path) # change directory to path

# GDAL open raster files and store in list
files=[]
for element in os.listdir(path):
    gt = gdal.Open(element)
    files.append(gt)

# projection
print(files[1].GetProjection())

# Raster size
print(files[1].RasterXSize) # height in pixels
print(files[1].RasterYSize)

################################ task 1 ############################################################

# define function for calculating the coordinates of the extent of an image
def extent_poly(file):
    gt = file.GetGeoTransform()
    UL_x = gt[0]   # upper left corner of the upper left pixel at position (padfTransform[0], padfTransform[3]
    UL_y = gt[3]
    pixel_width = gt[1]   # padfTransform[1] = pixel width
    pixel_height = gt[5]    # padfTransform[5] = pixel height
    rows = file.RasterXSize  # width/ pixelcount in row (x-direction)
    columns = file.RasterXSize  # height / pixelcount in column(y-direction)

    LR_x = UL_x + pixel_width*columns   # lower right  x-coordinate
    LR_y = UL_y + pixel_height*rows   # lower right y-coordinate

     # LR = xmax, ymin

    return box(UL_x, LR_y, LR_x, UL_y)   # shapely box; returns a polygon     return box (UL_x, UL_y, LR_x, LR_y)
#  shapely.geometry.box(minx, miny, maxx, maxy, ccw=True)
# Makes a rectangular polygon from the provided bounding box values, with counter-clockwise order by default

def common_extent(mask, file):
    if mask is None:
        return extent_poly(file)
    else:
        return extent_poly(file).intersection(mask)
        # set1.intersection(set2)), result:  largest set which contains all the elements that are common to both the sets

# functools.reduce(fun,seq):apply a particular function passed in its argument to all of the list elements
# cumulatively to the items of sequence, from left to right, so as to reduce the sequence to a single value
# functools.reduce(function, iterable[, initializer])
p = (reduce(common_extent, files, None)) # result polygon: LL - UL - UR - LR - LL (counterclockwise)
coord = list(p.exterior.coords)

# accessing upper left and lower left coordinate tuples
UL = coord[1]
LR = coord[3]

# rounding to 3 decimal numbers
UL_x = (round(UL[0],3))
UL_y = (round(UL[1],3))
LR_x = (round(LR[0],3))
LR_y = (round(LR[1],3))

print("UL_x:", UL_x, "UL_y", UL_y, "LR_x:", LR_x, "LR_y:", LR_y)

################################ task 2 ############################################################

# calculate the width and length (number of rows and cols) of the raster subset
metadata = files[1].GetGeoTransform()
pixel_width = metadata[1]
print(pixel_width)
pixel_height = (metadata[5])
print(pixel_height)

# LR_x = UL_x + rows * pixel_width  <-> rows = (LR_x - UL_x)/pixel_width *
# LR_y = UL_y + cols * pixel_height <-> cols = (LR_y - UL_x)/pixel_height

rows = round((LR_x - UL_x)/pixel_width)
print(rows)
cols = round((LR_y - UL_y)/pixel_height)
print(cols)



# numpy.empty(shape, type) Return a new array without initializing entries
arrays = np.empty([rows, cols, len(files)], int)  # [row, column] in numpy array, not [x (col) ,y (row)]


# read all raster in a 3d-array:
i = 0
for f in files:
    gt= f.GetGeoTransform()
    inv_gt = gdal.InvGeoTransform(gt)
    offsets = gdal.ApplyGeoTransform(inv_gt, UL_x, UL_y)
    off_x, off_y = map(int, offsets)
    arrays[:, :, i] = f.GetRasterBand(1).ReadAsArray(off_x, off_y, cols, rows)
    i += 1

################################ task 3 ############################################################
# calculate statistics
print("\nmean [2000, 2005, 2010, 2015, 2018]")
print(np.mean(arrays, axis=(0, 1)))
print("\nmedian [2000, 2005, 2010, 2015, 2018]")
print(np.median(arrays, axis=(0, 1)))
print("\nmin [2000, 2005, 2010, 2015, 2018]")
print(np.min(arrays, axis=(0, 1)))
print("\nmax [2000, 2005, 2010, 2015, 2018]")
print(np.max(arrays, axis=(0, 1)))
print("\nrange [2000, 2005, 2010, 2015, 2018]")
print(np.subtract(np.max(arrays, axis=(0, 1)), np.min(arrays, axis=(0, 1))))
print("\nstd [2000, 2005, 2010, 2015, 2018]")
print(np.std(arrays, axis=(0, 1)))

diff_2000_2010 = np.subtract(arrays[:, :, 0], arrays[:, :, 2])
diff_2010_2018 = np.subtract(arrays[:, :, 2], arrays[:, :, 4])

# calculate statistics
print("\nmean [2000-2010, 2010-2018]")
print(np.mean(diff_2000_2010))
print(np.mean(diff_2010_2018))

print("\nmedian [2000-2010, 2010-2018]")
print(np.median(diff_2000_2010))
print(np.median(diff_2010_2018))

print("\nmin [2000-2010, 2010-2018]")
print(np.min(diff_2000_2010))
print(np.min(diff_2010_2018))

print("\nmax [2000-2010, 2010-2018]")
print(np.max(diff_2000_2010))
print(np.max(diff_2010_2018))

print("\nrange [2000-2010, 2010-2018]")
print(np.subtract(np.max(diff_2000_2010), np.min(diff_2000_2010)))
print(np.subtract(np.max(diff_2010_2018), np.min(diff_2010_2018)))

print("\nstd [2000-2010, 2010-2018]")
print(np.std(diff_2000_2010))
print(np.std(diff_2010_2018))
