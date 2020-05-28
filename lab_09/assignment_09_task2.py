
## assignment_09 task2

import gdal
import os
import ogr
import osr
import pandas as pd


path = "E:/STUDIUM_Global_Change_Geography/M8_Geoprocessing/Assignment09/Assignment09_data/"
os.chdir(path)

# ####################################### LOAD DATA  ######################################################### #

#lucas shapefile
lucas_points = ogr.Open(path + 'EU28_2015_20161028_lucas2015j.gpkg')
lucas_points_layer = lucas_points.GetLayer()
print('feat count', lucas_points_layer .GetFeatureCount())

# subset of lucas shapefile (from Dirk)
lucas_points_subset = ogr.Open(path + 'EU28_2015_20161028_lucas2015j_subset.gpkg')
lucas_points_subset_layer = lucas_points_subset.GetLayer()
print('feat count_subset', lucas_points_subset_layer.GetFeatureCount())

# Load the raster
landsat = gdal.Open(path + "landsat_median1416_15000_10000.tif")


landclasses_img = gdal.Open(path + 'landcover_lucas2015_15000_10000.tif')

############# DEFINE OUTPUT DATAFRAME ############################

# define output dataframe
df_2 = pd.DataFrame(columns={'class': [],
                           'x': [],
                           'y': [],
                           'band2': [],
                           'band3': [],
                           'band4': [],
                           'band5': [],
                           'band6': [],
                           'band7': []

                           })

############# COORDINATE TRANSFORMATION ############################

# get the coordinate system of the raster
landsat_srs = osr.SpatialReference(wkt=landsat.GetProjection())  # since not an ogr object
#print(landsat_srs)

# get the coordinate system of the point layer
lucas_srs = lucas_points_layer.GetSpatialRef()
#print(lucas_srs)

# create transformation
trans_point2img = osr.CoordinateTransformation(lucas_srs, landsat_srs)
trans_img2point = osr.CoordinateTransformation(landsat_srs, lucas_srs)

############# BOUNDING BOX RASTER EXTENT & SET IT AS SPATIAL FILTER ON POINTS LAYER ############################

geotransform_landsat = landsat.GetGeoTransform()

ulx, xres, xskew, uly, yskew, yres  = landsat.GetGeoTransform()
lrx = ulx + (landsat.RasterXSize * xres)
lry = uly + (landsat.RasterYSize * yres)

# build a polygon/bounding box out of the landsat coordinates
ring = ogr.Geometry(ogr.wkbLinearRing)
ring.AddPoint(ulx, uly)
ring.AddPoint(lrx, uly)
ring.AddPoint(lrx, lry)
ring.AddPoint(ulx, lry)
ring.AddPoint(ulx, uly)

poly = ogr.Geometry(ogr.wkbPolygon)
poly.AddGeometry(ring)
poly.Transform(trans_img2point)

# set the polygon as spatial filter for the lucas point layer
#lucas_points_layer.SetSpatialFilter(poly) -> ERROR 1: failed to prepare SQL
#print('feat count_filtered', lucas_points_layer.GetFeatureCount())

# delete file if exists
if os.path.exists('output_assignment9_task2.csv'):
    os.remove('output_assignment9_task2.csv')
    print('existing file deleted')

#### loop through point layer and extract classes from landclasses img + band values from landsat image

i = 0
for points in lucas_points_subset_layer:  # use the subset because could not fix error
    geom = points.GetGeometryRef()
    geom.Transform(trans_point2img)


    # get x and y coordinates
    x_coord, y_coord = geom.GetX(), geom.GetY()
    #print(px, py)

    # Convert from map to pixel coordinates.
    # Only works for geotransforms with no rotation.
    pixel_x = int((x_coord - geotransform_landsat[0]) / geotransform_landsat[1])  # x pixel
    pixel_y = int((y_coord - geotransform_landsat[3]) / geotransform_landsat[5])  # y pixel

    # extract classes
    class_extracted = 0
    for x in range(landclasses_img.RasterCount):  # function RasterCount = raster band count
        x += 1
        landclasses_rb = landclasses_img.GetRasterBand(x)
        class_extracted = landclasses_rb.ReadAsArray(pixel_x, pixel_y, 1, 1) # read as array at pixel position

    # extract band values
    band_values = []   # create an empty list

    for i in range(landsat.RasterCount):  # loop through all raster bands  # range starts at 0
        i += 1  # increase i by 1, since raster band indices start at 1 not 0
        landsat_rb = landsat.GetRasterBand(i)  # get the raster band
        value_at_pos = landsat_rb.ReadAsArray(pixel_x, pixel_y, 1, 1)  # read raster band as array at pixel position
        band_values.append(int(value_at_pos[0]))  # append band value to list

################ FILL DATAFRAME ###########################################################

    df_2 = df_2.append({'class': int(class_extracted[0]),  # access array at 0 (only) position
                    'x': x_coord,
                    'y': y_coord,
                    'band2': band_values[0],  # access band value list at position []
                    'band3': band_values[1],
                    'band4': band_values[2],
                    'band5': band_values[3],
                    'band6': band_values[4],
                    'band7': band_values[5]},
                   ignore_index=True)

    ################ PRINT  DATAFRAME ##########################################################

    if i == 0:
        df_2.to_csv(path + "output_assignment9_task2.csv", header=True, mode='a', index=False, float_format='%2d',
                  encoding='utf-8')
    else:
        df_2.to_csv(path + "output_assignment9_task2.csv", header=False, mode='a', index=False, float_format='%2d',
                  encoding='utf-8')

    i += 1

    df_2.drop(df_2.index, inplace=True)


lucas_points_layer.SetSpatialFilter(None)
lucas_points_layer.ResetReading()

'''
# ####################################### END TIME-COUNT AND PRINT TIME STATS##################
print("")
endtime = time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime())
print("--------------------------------------------------------")
print("start: " + starttime)
print("end: " + endtime)
print("")

'''