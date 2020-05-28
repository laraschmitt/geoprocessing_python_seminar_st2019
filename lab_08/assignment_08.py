
# ####################################### LOAD REQUIRED LIBRARIES ############################################# #

import time
from osgeo import gdal, gdalnumeric, ogr, osr
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


# function to reproject shapefile layers
def reproject_layers (EPSG_in, EPSG_out, in_shapefile_name, output_name, layer_name, ogr_geom_type):
    # pass in attributes like: (3310, 26741, 'name.shp', 'output.shp', 'layer', ogr.wkbPoint)
    driver = ogr.GetDriverByName('ESRI Shapefile')

    # input SpatialReference
    inSpatialRef = osr.SpatialReference()
    inSpatialRef.ImportFromEPSG(EPSG_in)

    # output SpatialReference
    outSpatialRef = osr.SpatialReference()
    outSpatialRef.ImportFromEPSG(EPSG_out)

    # create the CoordinateTransformation
    coordTrans = osr.CoordinateTransformation(inSpatialRef, outSpatialRef)

    # get the input layer
    inDataSet = driver.Open(path + in_shapefile_name)
    inLayer = inDataSet.GetLayer()

    # create the spatial reference
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(EPSG_out)

    # create the output layer
    outputShapefile = output_name
    if os.path.exists(outputShapefile):
        driver.DeleteDataSource(outputShapefile)
    outDataSet = driver.CreateDataSource(outputShapefile)
    outLayer = outDataSet.CreateLayer(layer_name, srs, geom_type=ogr_geom_type)

    # add fields
    inLayerDefn = inLayer.GetLayerDefn()
    for i in range(0, inLayerDefn.GetFieldCount()):
        fieldDefn = inLayerDefn.GetFieldDefn(i)
        outLayer.CreateField(fieldDefn)

    # get the output layer's feature definition
    outLayerDefn = outLayer.GetLayerDefn()

    # loop through the input features
    inFeature = inLayer.GetNextFeature()
    while inFeature:
        # get the input geometry
        geom = inFeature.GetGeometryRef()
        # reproject the geometry
        geom.Transform(coordTrans)
        # create a new feature
        outFeature = ogr.Feature(outLayerDefn)
        # set the geometry and attribute
        outFeature.SetGeometry(geom)
        for i in range(0, outLayerDefn.GetFieldCount()):
            outFeature.SetField(outLayerDefn.GetFieldDefn(i).GetNameRef(), inFeature.GetField(i))
        # add the feature to the shapefile
        outLayer.CreateFeature(outFeature)
        # dereference the features and get the next input feature
        outFeature = None
        inFeature = inLayer.GetNextFeature()

    # Save and close the shapefiles
    inDataSet = None
    outDataSet = None


# world to pixel
def world2Pixel(geoMatrix, x, y):
  """
  Uses a gdal geomatrix (gdal.GetGeoTransform()) to calculate
  the pixel location of a geospatial coordinate
  """
  ulX = geoMatrix[0]
  ulY = geoMatrix[3]
  xDist = geoMatrix[1]
  yDist = geoMatrix[5]
  rtnX = geoMatrix[2]
  rtnY = geoMatrix[4]
  pixel = int((x - ulX) / xDist)
  line = int((ulY - y) / xDist)
  return (pixel, line)

# function to clip a GeoTiff with a Shapefile
def clip_geotiff(shapefile_path, raster_path):
    # Load the source data as a gdalnumeric array
    srcArray = gdalnumeric.LoadFile(raster_path)

    # Also load as a gdal image to get geotransform
    # (world file) info
    srcImage = gdal.Open(raster_path)
    geoTrans = srcImage.GetGeoTransform()

    # Create an OGR layer from a boundary shapefile
    shapef = ogr.Open(shapefile_path)
    lyr = shapef.GetLayer( os.path.split( os.path.splitext( shapefile_path )[0] )[1] )
    poly = lyr.GetNextFeature()

    # Convert the layer extent to image pixel coordinates
    minX, maxX, minY, maxY = lyr.GetExtent()
    ulX, ulY = world2Pixel(geoTrans, minX, maxY)
    lrX, lrY = world2Pixel(geoTrans, maxX, minY)

    # Calculate the pixel size of the new image
    pxWidth = int(lrX - ulX)
    pxHeight = int(lrY - ulY)

    clip = srcArray[:, ulY:lrY, ulX:lrX]


# ####################################### FOLDER PATHS & global variables ##################################### #
# Folder containing the working data
path = "E:/STUDIUM_Global_Change_Geography/M8_Geoprocessing/Assignment08/Assignment08_data2/"
os.chdir(path)

# ##################### REPROJECT LAYERS ###################################################################### #

# parcels shapefile
reproject_layers(26741, 3310, 'Parcels.shp', 'Parcels_3310.shp', 'Parcels_3310', ogr.wkbMultiPolygon)

# roads shapefile
reproject_layers(26741, 3310, 'Roads.shp', 'Roads_3310.shp', 'Roads', ogr.wkbMultiLineString)

# public lands shapefile
reproject_layers(26741, 3310, 'PublicLands.shp', 'PublicLands_3310.shp', 'PublicLands_3310', ogr.wkbMultiPolygon)

# timber harvest plan shapefile
reproject_layers(26741, 3310, 'TimberHarvestPlan.shp', 'TimberHarvestPlan_3310.shp', 'TimberHarvestPlan_3310', ogr.wkbMultiPolygon)


# ####################################### LOADING data ######################################################## #

# read parcels shapefile and get layer
parcels_ds = ogr.Open(path + 'Parcels_3310.shp', 0)  # # 0 means read-only. 1 means writeable.
if parcels_ds is None:
    sys.exit('Could not open {0}.'.format(fn))
parcels_lyr = parcels_ds.GetLayer(0)

# read marihuana grows shapefile and get layer
mariuhana_grows_ds = ogr.Open(path + 'Marihuana_Grows.shp', 0)  # # 0 means read-only. 1 means writeable.
if mariuhana_grows_ds is None:
    sys.exit('Could not open {0}.'.format(fn))
marihuana_grows_lyr = mariuhana_grows_ds.GetLayer(0)

# read roads shapefile and get layer
roads_ds = ogr.Open(path + 'Roads_3310.shp', 0)  # # 0 means read-only. 1 means writeable.
if roads_ds is None:
    sys.exit('Could not open {0}.'.format(fn))
roads_lyr = roads_ds.GetLayer(0)

# read public lands shapefile and get layer
public_lands_ds = ogr.Open(path + 'PublicLands_3310.shp', 0)  # # 0 means read-only. 1 means writeable.
if public_lands_ds is None:
    sys.exit('Could not open {0}.'.format(fn))
public_lands_lyr = public_lands_ds.GetLayer(0)


# read timber harvest shapefile and get layer
timber_harvest_ds = ogr.Open(path + 'TimberHarvestPlan_3310.shp', 0)  # # 0 means read-only. 1 means writeable.
if timber_harvest_ds is None:
    sys.exit('Could not open {0}.'.format(fn))
timber_harvest_lyr = timber_harvest_ds.GetLayer(0)

dem_raster = gdal.Open(path + 'DEM_Humboldt.tif')
# Raster size


# ##################### DEFINE EMPTY DATAFRAME FOR COLLECTING RESULTS ###################################

# define final dataframe for collecting results and later export
df = pd.DataFrame(columns={'Parcel_APN': [],
                           'Nr_GH-Plants': [],
                           'Nr_OD-Plants': [],
                           'Dist_to_grow_m': [],
                           'Km_Priv_Road': [],
                           'Km_local_Road': [],
                           'Mean_elevation': [],
                           'PublicLand-YN': [],
                           'Prop_in_THP': []

                           })

# define type per column
df = df.astype(dtype={'Parcel_APN': "int64",
                        'Nr_GH-Plants': "int64",
                       'Nr_OD-Plants': "int64",
                       'Dist_to_grow_m': "string",
                       'Km_Priv_Road': "float64",
                       'Km_local_Road': "float64",
                       'Mean_elevation': "float64",
                       'PublicLand-YN': "int64",
                       'Prop_in_THP': "float64"})

# #################################### FILL DATAFRAME  ###################################################
if os.path.exists('output_assignment8.csv'):
    os.remove('output_assignment8.csv')
    print('existing file deleted')


i = 0
for parcel in parcels_lyr:

    ########### GET APN NUMBER #############################################################

    # get field value fpr parcel_apn
    parcel_apn = parcel.GetField('APN')
    print('parcel apn', parcel_apn)

    # get parcel geometry
    parcel_geom = parcel.geometry().Clone()

    ########### GET VALUES FOR NUMBER OF GREENHOUSE AND OUTDOOR PLANTS PER PARCEL ##########

    # set spatial filter (parcel geometry) for marihuana layer
    marihuana_grows_lyr.SetSpatialFilter(parcel_geom)

    g_count_list = []  # create empty lists for greenhouse and outdoor plant count
    o_count_list = []

    for feat in marihuana_grows_lyr:
        # print('g_house', feat.GetField('g_plants'))
        no_g_plants = feat.GetField('g_plants')
        g_count_list.append(no_g_plants)  # append values for greenhouse plant numbers

        # print('outdoor', feat.GetField('o_plants'))
        no_o_plants = feat.GetField('o_plants')
        o_count_list.append(no_o_plants)

    greenhouse_count = sum(g_count_list)  # sum the values of the list
    outdoor_count = sum(o_count_list)

    # set spatial filter (parcel geometry) to none
    marihuana_grows_lyr.SetSpatialFilter(None)
    marihuana_grows_lyr.ResetReading()

    ################# GET DISTANCE TO NEXT GROW ############################################
    bufferDist = 10
    sum_dist = 0

    # get the total feature count per parcel of the marihuana layer
    marihuana_grows_lyr.SetSpatialFilter(parcel_geom)
    total_feat_count = marihuana_grows_lyr.GetFeatureCount()

    # create buffer around parcel geometry (start value = 10)
    buffer = parcel_geom.Buffer(bufferDist)
    # set spatial filter on the marihuana layer with the buffered parcel
    marihuana_grows_lyr.SetSpatialFilter(buffer)

    # count the marijuana features within the buffered parcel
    feat_count_buff = marihuana_grows_lyr.GetFeatureCount()
    if greenhouse_count > 0 or outdoor_count > 0:
        print('parcel with grows in it')
        while feat_count_buff == total_feat_count:
            buffer_geom = parcel_geom.Buffer(bufferDist)
            marihuana_grows_lyr.SetSpatialFilter(buffer_geom)
            feat_count_buff = marihuana_grows_lyr.GetFeatureCount()

            bufferDist += 10
            marihuana_grows_lyr.SetSpatialFilter(None)

        distance_from = bufferDist-10
        distance_to = bufferDist
        sum_dist = '{0}-{1}'.format(distance_from, distance_to)

    # set spatial filter to None
    marihuana_grows_lyr.SetSpatialFilter(None)
    marihuana_grows_lyr.ResetReading()

    ############# GET VALUES FOR KM PRIVATE ROADS AND LOCAL ROADS PER PARCEL ################

    # set attribute filters for value private and get feature and the geometry
    roads_lyr.SetAttributeFilter("FUNCTIONAL = 'Private'")
    road_feat = roads_lyr.GetNextFeature()  # layer.GetNextFeature()
    road_geom = road_feat.geometry()

    # get the intersection of the road geometry and the parcel geometry
    intersect_parcel_private_r = road_geom.Intersection(parcel_geom)   # output: new geometry representing the intersection or NULL
    intersection_private_r_length_km = round((intersect_parcel_private_r.Length() / 1000), 3) #geom.Length() returns in meters
    # print('intersection with private road', intersection_private_r_length_km)

    # Set Attribute Filter to None
    roads_lyr.ResetReading()
    roads_lyr.SetAttributeFilter(None)

    # set attribute filters for value private and get feature and the geometry
    roads_lyr.SetAttributeFilter("FUNCTIONAL = 'Local Roads'")
    road_feat = roads_lyr.GetNextFeature()  # layer.GetNextFeature()
    road_geom = road_feat.geometry()

    # get the intersection of the road geometry and the parcel geometry
    intersect_parcel_private_r = road_geom.Intersection(parcel_geom)
    intersection_local_r_length_km = round((intersect_parcel_private_r.Length() / 1000), 3)
    #print('intersection with local road', intersection_local_r_length_km)

    # Set Attribute Filter to None
    roads_lyr.ResetReading()
    roads_lyr.SetAttributeFilter(None)

    ################ GET MEAN ELEVATION FROM RASTER #########################################

    #dem_raster
    # ReadAsArray()

    #clip_geotiff(path + 'Parcels_3310.shp', path + 'DEM_Humboldt.tif')
    #np.mean()


    ################ GET PUBLIC LANDS BINARIES ##############################################
    binary = 0
    for shape in public_lands_lyr:
        public_land_geom = shape.geometry()
        if public_land_geom.Intersects(parcel_geom):
            binary = 1

    public_lands_lyr.ResetReading()
    public_lands_lyr.SetAttributeFilter(None)

    ################ GET TIMBER HARVEST PLAN PERCENTAGES ######################################
    proportion = None
    parcel_area = parcel_geom.GetArea()
    for area in timber_harvest_lyr:
        timber_area_geom = area.geometry()
        if timber_area_geom.Intersects(parcel_geom):
            intersect_area = parcel_geom.Intersection(timber_area_geom)
            area_calc = intersect_area.GetArea()
            proportion = round((area_calc / parcel_area), 5)
            #print(proportion)


    timber_harvest_lyr.ResetReading()
    timber_harvest_lyr.SetAttributeFilter(None)

    ################ FILL DATAFRAME ###########################################################

    df = df.append({'Parcel_APN': parcel_apn,
                    'Nr_GH-Plants': greenhouse_count,
                    'Nr_OD-Plants': outdoor_count,
                    'Dist_to_grow_m': sum_dist,
                    'Km_Priv_Road': intersection_private_r_length_km,
                    'Km_local_Road': intersection_local_r_length_km,
                    'Mean_elevation': [],  # np.mean(array),
                    'PublicLand-YN': binary,
                    'Prop_in_THP': proportion
                           }, ignore_index=True)

    ################ PRINT  DATAFRAME ##########################################################

    if i == 0:
        df.to_csv(path + "output_assignment8.csv", header=True, mode='a', index=False,
                  encoding='utf-8')
    else:
        df.to_csv(path + "output_assignment8.csv", header=False, mode='a', index=False,
                  encoding='utf-8')
    df.drop(df.index, inplace=True)

    i += 1
    #if i == 100:
    #    break


# reset reading parcels layer
parcels_lyr.ResetReading()


# ####################################### END TIME-COUNT AND PRINT TIME STATS##################
print("")
endtime = time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime())
print("--------------------------------------------------------")
print("start: " + starttime)
print("end: " + endtime)
print("")

