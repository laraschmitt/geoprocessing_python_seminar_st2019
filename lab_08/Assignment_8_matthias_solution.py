
# Functions to copy vector and raster layers to memory for faster processing
# For vector layers
import ogr
def CopyToMem(path):
    drvMemV = ogr.GetDriverByName('Memory')
    f_open = drvMemV.CopyDataSource(ogr.Open(path),'')
    return f_open
# For raster layers
import gdal
def OpenRasterToMemory(path):
    drvMemR = gdal.GetDriverByName('MEM')
    ds = gdal.Open(path)
    dsMem = drvMemR.CreateCopy('', ds)
    return dsMem


# Do the grow information
    # Clone the geometry to not mess with the original
    geom_cl = geom.Clone()
    geom_cl.Transform(CS_Transform(geom_cl, grow_lyr))
    grow_lyr.SetSpatialFilter(geom_cl)
    # If there are no grows, then set the first three variables to zero
    if grow_lyr.GetFeatureCount() == 0:
        vals.extend([0, 0, 0])
    else:
    # Iterate through selected grows
        grow_feat = grow_lyr.GetNextFeature()
        g_plants = 0
        o_plants = 0
        while grow_feat:
        # Get number of plants in greenhouses
            p_gh = grow_feat.GetField("g_plants")
            g_plants = g_plants + p_gh
        # Get number of plants in open space
            g_open = grow_feat.GetField("o_plants")
            o_plants = o_plants + g_open
            grow_feat = grow_lyr.GetNextFeature()
    # Reset the reading of the layer so that we start from zero again, remove the spatial filter
        grow_lyr.ResetReading()
        grow_lyr.SetSpatialFilter(None)
    # Append values to output
        vals.append(g_plants)
        vals.append(o_plants)


# Set a flag to zero, which changes to one if SetSpatialFilter() returns  more than 0
flag = 0
buff = 10
while flag == 0:
    geomBuff = geom_cl.Buffer(buff)
    buffOnly = geomBuff.Difference(geom_cl)
    grow_lyr.SetSpatialFilter(buffOnly)
    neighGrow = growsLYR.GetFeatureCount()
    if neighGrow > 0:
        flag = 1
    else:
        buff += 10
vals.append(buff)



# Calculate the number of private roads
    geom_cl = geom.Clone() #new clone of the geometry, geotansform
    geom_cl.Transform(CS_Transform(geom_cl, roads_lyr))
    # Set Attribute filter to 'private'
    roads_lyr.SetAttributeFilter("FUNCTIONAL = 'Private'")
    roads_feat = roads_lyr.GetNextFeature()
    roads_geom = roads_feat.GetGeometryRef()
    intersect = geom_cl.Intersection(roads_geom)
    kms = intersect.Length()
    if kms > 0:
        vals.append(kms / 1000)
    else:
        vals.append(0)
    roads_lyr.ResetReading()
# Calculate number of local roads
    roads_lyr.SetAttributeFilter("FUNCTIONAL = 'Local Roads'")
    roads_feat = roads_lyr.GetNextFeature()
    roads_geom = roads_feat.GetGeometryRef()
    intersect = geom_cl.Intersection(roads_geom)
    kms = intersect.Length()
    if kms > 0:
        vals.append(kms / 1000)
    else:
        vals.append(0)
    roads_lyr.ResetReading()

import ogr, osr, gdal
import numpy as np
import math


def Geom_Raster_to_np(geom, raster):
    '''
    Function that takes a geometry from a polygon shapefile and a rasterfile, and returns both features as 2d-arryas in the size of the geom --> can be later used
    for masking. Function does a coordinate transformation implicitely!

    PARAMETERS
    -----------
    geom : geom object (required); geometry of the feature
    raster: gdal object (required); raster as a gdal-object (through gdal.Open())

   RETURNS
    -------
    Two numpy-arrays
    (1) np-array of the geometry as binary feature --> values inside the geometry have value '1', values outside '0'
    (2) np-array of the raster in the same size (i.e., as a subset of the raster) of the geometry
    '''
    # Make a coordinate transformation of the geom-srs to the raster-srs
    pol_srs = geom.GetSpatialReference()
    ras_srs = raster.GetProjection()
    target_SR = osr.SpatialReference()
    target_SR.ImportFromWkt(ras_srs)
    srs_trans = osr.CoordinateTransformation(pol_srs, target_SR)
    geom.Transform(srs_trans)
    # Create a memory shp/lyr to rasterize in
    geom_shp = ogr.GetDriverByName('Memory').CreateDataSource('')
    geom_lyr = geom_shp.CreateLayer('geom_shp', srs=geom.GetSpatialReference())
    geom_feat = ogr.Feature(geom_lyr.GetLayerDefn())
    geom_feat.SetGeometryDirectly(ogr.Geometry(wkt=str(geom)))
    geom_lyr.CreateFeature(geom_feat)
    # Rasterize the layer, open in numpy
    x_min, x_max, y_min, y_max = geom.GetEnvelope()
    gt = raster.GetGeoTransform()
    pr = raster.GetProjection()
    x_res = math.ceil((abs(x_max - x_min)) / gt[1])
    y_res = math.ceil((abs(y_max - y_min)) / gt[1])
    new_gt = (x_min, gt[1], 0, y_max, 0, -gt[1])
    lyr_ras = gdal.GetDriverByName('MEM').Create('', x_res, y_res, 1, gdal.GDT_Byte)
    lyr_ras.GetRasterBand(1).SetNoDataValue(0)
    lyr_ras.SetProjection(pr)
    lyr_ras.SetGeoTransform(new_gt)
    gdal.RasterizeLayer(lyr_ras, [1], geom_lyr, burn_values=[1], options=['ALL_TOUCHED=TRUE'])
    geom_np = np.array(lyr_ras.GetRasterBand(1).ReadAsArray())
    # Now load the raster into the array --> only take the area that is 1:1 the geom-layer (see Garrard p.195)
    inv_gt = gdal.InvGeoTransform(gt)
    offsets_ul = gdal.ApplyGeoTransform(inv_gt, x_min, y_max)
    off_ul_x, off_ul_y = map(int, offsets_ul)
    raster_np = np.array(raster.GetRasterBand(1).ReadAsArray(off_ul_x, off_ul_y, x_res, y_res))
    return geom_np, raster_np




# Calculate mean elevation
    geom_np, elev_np = Geom_Raster_to_np(geom, dem)
    mean = elev_np[geom_np == 1].mean()
    vals.append(mean)

# Add the values to the output
outDS.append(vals)
outDS.extend([0, 0])
# Take next feature
feat = parcels_lyr.GetNextFeature()



import csv
def WriteListToCSV(outname, list, delim):
    '''
    Function to write a list of lists into a csv-file. Each entry in the list is thereby a new line
    --> the function is designed towards the standard output of may of my analyses.
    PARAMETERS
    ----------
    outname : string (required)
        Path to the output-file. make sure it ends with ".csv"
    list : list object (required)
        List with the data to write. Each sublist is an own line in the csv file. [[line 1], [line 2],...,[line n]]
    delim : string (required)
        Deliminter for the csv-File
    RETURNS
    -------
    theFile : output-file. Directly written to disc
    '''
    with open(outname, "w") as theFile:
        csv.register_dialect("custom", delimiter = delim, skipinitialspace = True, lineterminator = '\n')
        writer = csv.writer(theFile, dialect = "custom")
        for element in list:
            writer.writerow(element)



outFile = workFolder + "summaryDataset.csv"
WriteListToCSV(outFile, outDS, ",")




