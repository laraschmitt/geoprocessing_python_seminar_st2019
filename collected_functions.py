
########## collected functions


#################### copy vector and raster layers to memory for faster processing ##########################
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


#################### COORDINATE TRANSFORMATION ##########################
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


#################### WRITE LIST TO CSV TO DISK ##########################

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

import ogr, osr, gdal
import numpy as np
import math


#################### GEOMETRY FROM RASTER TO NUMPY ARRAY  ##########################


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