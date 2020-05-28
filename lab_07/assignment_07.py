
# ####################################### LOAD REQUIRED LIBRARIES ############################################# #

import time
from osgeo import ogr
from osgeo import osr
import pandas as pd
import os
import sys
import random
import math

# ####################################### SET TIME-COUNT ###################################################### #
starttime = time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime())
print("--------------------------------------------------------")
print("Starting process, time: " + starttime)
print("")
# ####################################### FUNCTIONS ########################################################### #

# function to create random points lying on the landsat grid within a geometry
def random_points_within_PA_within_landsat_grid(geom_pa, num_points, bufferdist):
    (min_x, max_x, min_y, max_y) = geom_pa.GetEnvelope()  # Get Envelope returns a tuple (minX, maxX, minY, maxY)

    point_list = []

    while len(point_list) < num_points:
        random_point = ogr.Geometry(ogr.wkbPoint)

        random_point.AddPoint(random.uniform(min_x, max_x),
                              random.uniform(min_y, max_y))
        # try to match the location of the polygons to the landsat grid
        # couldn't make it work
        # random_point.AddPoint(387989.426864 + random.uniform(min_x, max_x)*30, 5819549.72673 + random.uniform(min_y, max_y)*30)
        poly_block = random_point.Buffer(bufferdist) # bufferdist = 63,64 (distance from center point to cornerpoint of polyblock
        intersection = geom_pa.Intersection(poly_block)
        print(len(point_list))
        if not intersection.IsEmpty():
            point_list.append(random_point)

    return point_list


# function that creates a 3x3 polygon grid (30m) based on center coordinates (UTM coordinates)
# returned is a list of rectangles, each containing a list of coordinate tuples
def create_grid_coord(x_center, y_center):
    # multiple assignment of variables
    UL_1 = ((x_center - 45), (y_center - 45))  # returns a tuple
    UR_1 = UL_2 = ((x_center - 15), (y_center - 45))
    UR_2 = UL_3 = ((x_center + 15), (y_center - 45))
    UR_3 = ((x_center + 45), (y_center - 45))
    LL_1 = UL_4 = ((x_center - 45), (y_center - 15))
    LR_1 = LL_2 = UR_4 = UL_5 = ((x_center - 15), (y_center - 15))
    LR_2 = LL_3 = UR_5 = UL_6 = ((x_center + 15), (y_center - 15))
    LR_3 = UR_6 = ((x_center + 45), (y_center - 15))
    LL_4 = UL_7 = ((x_center - 45), (y_center + 15))
    LR_4 = LL_5 = UR_7 = UL_8 = ((x_center - 15), (y_center + 15))
    LR_5 = LL_6 = UR_8 = UL_9 = ((x_center + 15), (y_center + 15))
    LR_6 = UR_9 = ((x_center + 45), (y_center + 15))
    LL_7 = ((x_center - 45), (y_center + 45))
    LR_7 = LL_8 = ((x_center - 15), (y_center + 45))
    LR_8 = LL_9 = ((x_center + 15), (y_center + 45))
    LR_9 = ((x_center + 45), (y_center + 45))

    rect1 = [UL_1, UR_1, LR_1, LL_1, UL_1]  # list of tuples # repeat last tuple to be able to close the ring
    rect2 = [UL_2, UR_2, LR_2, LL_2, UL_2]
    rect3 = [UL_3, UR_3, LR_3, LL_3, UL_3]
    rect4 = [UL_4, UR_4, LR_4, LL_4, UL_4]
    rect5 = [UL_5, UR_5, LR_5, LL_5, UL_5]
    rect6 = [UL_6, UR_6, LR_6, LL_6, UL_6]
    rect7 = [UL_7, UR_7, LR_7, LL_7, UL_7]
    rect8 = [UL_8, UR_8, LR_8, LL_8, UL_8]
    rect9 = [UL_9, UR_9, LR_9, LL_9, UL_9]

    rect_list = [rect1, rect2, rect3, rect4, rect5, rect6, rect7, rect8, rect9]  # list of lists of tuples
    return rect_list

# ####################################### FOLDER PATHS & global variables ##################################### #
# Folder containing the working data
path = "E:/STUDIUM_Global_Change_Geography/M8_Geoprocessing/Assignment07/data/"
os.chdir(path)

# ####################################### LOADING data ######################################################## #

# read germany shapefile and get layer
germany_ds = ogr.Open(path + 'gadm36_GERonly.shp', 0)  # # 0 means read-only. 1 means writeable.
if germany_ds is None:
    sys.exit('Could not open {0}.'.format(fn))
germany_lyr = germany_ds.GetLayer(0)  # contains 10 of Germany's largest PAs

# read protected area shapefile and get layer
pa_ds = ogr.Open(path + 'WDPA_May2018_polygons_GER_select10large.shp', 0)  # # 0 means read-only. 1 means writeable.
if pa_ds is None:
    sys.exit('Could not open {0}.'.format(fn))
pa_lyr = pa_ds.GetLayer('WDPA_May2018_polygons_GER_select10large')

# read point shapefile and get layer
point_ds = ogr.Open(path + 'OnePoint.shp', 0)  # # 0 means read-only. 1 means writeable.
if point_ds is None:
    sys.exit('Could not open {0}.'.format(fn))
point_lyr = point_ds.GetLayer(0)  # point-location of the center of a landsat pixel
# UTM-33N coordinates): X (easting): 387989.426864, Y (northing): 5819549.72673.
# converted to lat/long = 52.514539, 13.349345
# get feature out of the one point layer
given_point = point_lyr.GetFeature(0)
#given_point.GetGeometryRef()
# get the geometry of the feature
given_point_geom = given_point.geometry()
# accessing x and y coordinates
given_point_x_coord = given_point_geom.GetX()
given_point_y_coord = given_point_geom.GetY()

#for field in pa_lyr.schema:
#    print(field.name, field.GetTypeName())

# create a list with the names of the protected areas
pa_names_list =[]
for feat in pa_lyr:
    print(feat.GetField("NAME"))
    pa_names_list.append(feat.GetField("NAME"))
pa_lyr.ResetReading()

# ####################################### TASK############################################################## #
# generate polygon shapefile
# criteria:
# 1. For each of the ten protected areas, 50 polygon-blocks (see below) should be generated.
# The location of each polygon-block within the protected area should be random.
# 2. Each polygon-block consists of a center-polygon and overall 8 neighboring polygons
# (please refer to the session slides for a visual example).
# 3. The polygon-block should have its own identifier, and the center polygon a unique identifier
# within the polygon-block (e.g., 1.1, 1.2, … , 1.9, where 1.1 is the identifier of the center polygon).
# 4. Each polygon in each block has to have the size of one Landsat pixel (i.e., 30m x 30m).
# 5. In order to match the location of the polygons to actual Landsat pixels, you have an
# orientation-point incl. the coordinate available (see above, the point is located at the
# Siegessäule in Berlin). Please consider this in your random allocation algorithm.
# 6. Only store polygon-blocks in which all nine polygons are entirely within the protected area.
# 7. Each polygon should carry the name of the protected area it is located in as an attribute.


# #################################GENERATE RANDOM SAMPLE ################################################## #

source1 = osr.SpatialReference() # define spatial reference system from source projection
source1.ImportFromEPSG(4326) # UTM zone 33N # has decimal coordinates

target1 = osr.SpatialReference() # define spatial reference system for destination  projection
target1.ImportFromEPSG(25833) # has lat/long coordinates

transform1 = osr.CoordinateTransformation(source1, target1)
# to apply it later: geometry.Transform(transform)


# generate a random sample of points/polygons that fall within the protected areas

list_randompoints = []
for i in range(0, len(pa_lyr)):
    feat = pa_lyr.GetFeature(i)
    pa_geom = feat.geometry()  # get the geometry from the feature, returns a polygon or geom = feat.GetGeometryRef()
    pa_geom.Transform(transform1)
    # apply random_points within function:
    for item in random_points_within_PA_within_landsat_grid(pa_geom, 50, 63.64):  # num points = 50, buffdist = 63.64
        list_randompoints.append(item)  # output: list of points
        # print("created rand point", item)
    pa_lyr.ResetReading()

print(len(list_randompoints))   # 500
print(list_randompoints[1])

# accessing x and y coordinates
x_coord = list_randompoints[1].GetX()
y_coord = list_randompoints[1].GetY()

# ###############TRANSLATE X, Y COORDINATES INTO POLYGON BLOCKS ##################################################

# create list of [blocks[rectangles[corner_coord_tuple1, corner_coord_tuple2, ...]]]
list_rect = []
for point in list_randompoints:
    x_coord = point.GetX()
    y_coord = point.GetY()
    rectg = create_grid_coord(x_coord, y_coord)
    list_rect.append(rectg)

print("lenght of list_rectangles", len(list_rect)) # 500 block items

# create list of [polyblocks[polygon1, polygon2, ...]]

list_polyblocks = []
for block in list_rect:
    b = []
    for rect in block:
        ring = ogr.Geometry(ogr.wkbLinearRing)
        ring.AddPoint(rect[0][0], rect[0][1])
        ring.AddPoint(rect[1][0], rect[1][1])
        ring.AddPoint(rect[2][0], rect[2][1])
        ring.AddPoint(rect[3][0], rect[3][1])
        ring.AddPoint(rect[0][0], rect[0][1])

        # create polygon
        poly = ogr.Geometry(ogr.wkbPolygon)
        poly.AddGeometry(ring)
        b.append(poly)
    list_polyblocks.append(b)
    print("created polygonblock", block)

print("lenght of list_polyblocks", len(list_polyblocks)) # 500

#for element, counter in enumerate(list_polyblocks):
 #   print(element, counter) # 499

# #####################CREATE "TRANSFORM" FOR REPROJECTING GEOMETRIES###################################

# coordinate transformation using the osr Coordinate Transformation class (ogr & osr from osgeo needed)
source = osr.SpatialReference() # define spatial reference system from source projection
source.ImportFromEPSG(25833) # UTM zone 33N # has decimal coordinates

target = osr.SpatialReference() # define spatial reference system for destination  projection
target.ImportFromEPSG(4326) # has lat/long coordinates

transform = osr.CoordinateTransformation(source, target)
# to apply it later: geometry.Transform(transform)  # call transform method


# ################################## WRITE SHAPEFILE ##################################################

# set up the shapefile driver
driver = ogr.GetDriverByName("ESRI Shapefile")

# create an empty data source (called data.shp) by providing the data source name
# this data source is automatically open for writing
output = "pa_polygons_germany.shp"
datasource = driver.CreateDataSource(output)

if os.path.exists(path + output):
    driver.DeleteDataSource(output)
if datasource is None:
    sys.exit('Could not create {0}.'.format(output))

# create the spatial reference, WGS84
srs = osr.SpatialReference()
srs.ImportFromEPSG(4326)

# create the layer
layer = datasource.CreateLayer(output, srs, ogr.wkbPolygon)

# Add the fields we're interested in
layer.CreateField(ogr.FieldDefn("grid_ID", ogr.OFTInteger))

field_pixel_num = ogr.FieldDefn("pixel_numb", ogr.OFTReal)
field_pixel_num.SetWidth(8)
field_pixel_num.SetPrecision(1)
layer.CreateField(field_pixel_num)

field_name = ogr.FieldDefn("PA_name", ogr.OFTString)
field_name.SetWidth(24)
layer.CreateField(field_name)

# fill layer with features

gid = 1
index = 0
label_index = 0
for polyblock in list_polyblocks:
    px_extra = 0.1
    for geom in polyblock:   # collection of the generated polygons
        total_polygons = 4500
        chunk = total_polygons / len(pa_names_list)
        # create the feature
        feature = ogr.Feature(layer.GetLayerDefn())
        # Set the attributes using the values
        feature.SetField("grid_ID", gid)
        feature.SetField("pixel_numb", (gid + px_extra))

        if index >= 450 and index % 450 == 0:
            label_index += 1

        feature.SetField("PA_name", pa_names_list[label_index])
        # apply transform function
        geom.Transform(transform)  # the geometry that we get is called "geom"
        # Set the feature geometry
        feature.SetGeometry(geom)

        # Create the feature in the layer (shapefile)
        layer.CreateFeature(feature)
        print("created", feature)

        # Dereference the feature
        feature = None

        px_extra += 0.1
        index += 1
    gid += 1

# Save and close the data source
data_source = None

print("Feature <" + str(output) + "> successfully created.")
del output


#################################### WRITE KML ##################################################

driverName = "KML"
drv = ogr.GetDriverByName(driverName)
if drv is None:
    print("%s driver not available.\n" % driverName)
else:
    print("%s driver IS available.\n" % driverName)

driver = ogr.GetDriverByName('KML')
output = "kml_pa_polygons_germany.kml"
#datasource = driver.Open(output)
datasource = driver.CreateDataSource(output)

if os.path.exists(path + output):
    driver.DeleteDataSource(output)
if datasource is None:
    sys.exit('Could not create {0}.'.format(output))

# create the spatial reference, WGS84
srs = osr.SpatialReference()
srs.ImportFromEPSG(4326)

# create the layer
layer = datasource.CreateLayer(output, srs, ogr.wkbPolygon)

# Add the fields we're interested in
layer.CreateField(ogr.FieldDefn("grid_ID", ogr.OFTInteger))


field_pixel_num = ogr.FieldDefn("pixel_numb", ogr.OFTReal)
field_pixel_num.SetWidth(8)
field_pixel_num.SetPrecision(1)
layer.CreateField(field_pixel_num)
field_name = ogr.FieldDefn("PA_name", ogr.OFTString)
field_name.SetWidth(24)
layer.CreateField(field_name)


# fill layer with features

gid = 1
index = 0
label_index = 0
for polyblock in list_polyblocks:
    px_extra = 0.1
    for geom in polyblock:   # collection of the generated polygons
        total_polygons = 4500
        chunk = total_polygons / len(pa_names_list)
        # create the feature
        feature = ogr.Feature(layer.GetLayerDefn())
        # Set the attributes using the values
        feature.SetField("grid_ID", gid)
        feature.SetField("pixel_numb", (gid + px_extra))

        if index >= 450 and index % 450 == 0:
            label_index += 1

        feature.SetField("PA_name", pa_names_list[label_index])
        # apply transform function
        geom.Transform(transform)  # the geometry that we get is called "geom"
        # Set the feature geometry
        feature.SetGeometry(geom)

        # Create the feature in the layer (shapefile)
        layer.CreateFeature(feature)
        print("created", feature)

        # Dereference the feature
        feature = None

        px_extra += 0.1
        index += 1
    gid += 1

# Save and close the data source
datasource = None



# ####################################### END TIME-COUNT AND PRINT TIME STATS##################
print("")
endtime = time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime())
print("--------------------------------------------------------")
print("start: " + starttime)
print("end: " + endtime)
print("")

