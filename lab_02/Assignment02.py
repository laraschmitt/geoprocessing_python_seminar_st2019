
import pandas as pd
import numpy as np
import rasterio as rio
import os
from shapely.geometry import Point, Polygon # datatypes used from shapely package: polygon and points
from geopandas import GeoDataFrame # needed to create a geopandas dataframe
import geopandas

# import table with the land cover and land use data
LC_path = "E:/STUDIUM_Global_Change_Geography/M8_Geoprocessing/Assignment02/DE_2015_20180724.csv"
# import the grid table containing the sampling locations
grid_path = "E:/STUDIUM_Global_Change_Geography/M8_Geoprocessing/Assignment02/GRID_CSVEXP_20171113.csv"
# fname = os.path.join(path, *path)

# read cs
df = pd.read_csv(LC_path)  # df = pd.read_csv(filename)
# print(df.head)
print(len(df.index))
# print(len(df.column))

grid = pd.read_csv(grid_path)
# print(grid.head)

############################## task 1.1
# Filter out potentially unsuitable observations. Save the observations that meet the criteria below
# into a new data frame and answer the following questions: (see below)
# Filter criteria:
# • OBS_TYPE = 1
# • OBS_DIRECT = 1
# • OBS_RADIUS <= 2
# • AREA_SIZE >= 2
# • FEATURE_WIDTH > 1
# • LC1_PCT >= 5
# hints: slicing, grouping by, aggregating function

# check if all columns exist --> change OBS_DIRECT to OBS_DIR
if 'OBS_DIR' in df.columns:
    print("Yes")
else:
    print("No")

# filter data
df_filtered = df[(df.OBS_TYPE == 1) & (df.OBS_DIR == 1) & (df.OBS_RADIUS <= 2)
            & (df.AREA_SIZE >= 2) & (df.FEATURE_WIDTH > 1) & (df.LC1_PCT >= 5)]

df_fil = pd.DataFrame(df_filtered)

# Questions
# 1) How many observations are left?
count_row = (len(df_fil.index))
print(count_row, "observations are left")

# 2) How many land cover classes (column LC1) were recorded?
## f1st solution with unique() and len()
count_classes = len(df_fil.LC1.unique())
print(count_classes, "land cover classes were recorded")

## 2nd solution with value_counts()
value_count = df_fil.LC1.value_counts()
print(len(value_count))

# 3) What is the average observer distance (meters) (OBS_DIST)?
avg_obs_dist = df_fil.OBS_DIST.mean()
print(avg_obs_dist, "is the average observer distance (meters)")

# 4) What is the average observer distance of class A21?

means = df_fil.groupby('LC1').mean()      # df.groupby('key')  # mean()
avg_obs_dist_A21 = means.loc['A21', 'OBS_DIST']
print(avg_obs_dist_A21, "is the average observer distance of class A21")

# 5) How many samples are in the land cover class (LC1) with the most samples?
# find the land cover class (LC1) with the most samples
sizes = df_fil.groupby('LC1').size()
LC_most_frequent = sizes.idxmax()
count_max_samples = sizes.max()

print(count_max_samples, "are in the most frequent land cover class", LC_most_frequent)

## 2nd solution with function and value_counts
def top_value_count (x, n=5):
    return x.value_counts().head(n)

x = top_value_count(df_fil.LC1, n = 1)
print(x)


###################### task 1.2
# Create a GeoDataFrame of the filtered LUCAS samples and save it as an ESRI shapefile.

# check datatypes of the grid dataframe
print(grid.dtypes)  # ASSOC18 is bool -> not allowed when writing geodataframe to file
# change the datatype to int
grid.ASSOC18 = grid.ASSOC18.astype(int)   # dataframe.astype(type)


# merge the grid file with the table and transform it to dataframe
merged = pd.merge(grid, df_fil)
df_merged = pd.DataFrame(merged)


# creating a tuple of Longitude and Latitude and transfer it to Point
geometry = [Point(xy) for xy in zip(df_merged.GPS_LONG, df_merged.GPS_LAT)]

# geometry = geopandas.points_from_xy(merged_df.GPS_LONG, merged_df.GPS_LAT)

# specify the coordinate reference system
crs = "+init=epsg:4326" #http://www.spatialreference.org/ref/epsg/4326/

# create the GeoDataFrame
geo_df = GeoDataFrame(df_merged, crs=crs, geometry=geometry)

geo_df.to_file(driver='ESRI Shapefile', filename='lucas_de.shp')


##### task 2. 1
# Assume you used EarthExplorer (https://earthexplorer.usgs.gov) to select all Landsat-8 Collection 1
# scenes acquired over Germany and downloaded their metadata (LANDSAT_8_C1_313804.csv). Your
# task is to explore and filter the metadata of the available Landsat scenes and to build a shapefile
# from selected scene boundaries.

# load metadata
metadata_path = "E:/STUDIUM_Global_Change_Geography/M8_Geoprocessing/Assignment02/LANDSAT_8_C1_313804.csv"
metadata = pd.read_csv(metadata_path)
# print(metadata)

# replaces spaces with underscore in column names
metadata.columns = [c.replace(' ', '_') for c in metadata.columns]

# rename columns
metadata.rename(columns={'Day/Night_Indicator':'Day_Night_Indicator',
                          'Data_Type_Level-1':'Data_Type_Level_1'},
                 inplace=True)

# 1. Filter out potential scenes using the filter criteria below. Save the scenes that meet the criteria
# below into a new data frame and answer the questions below.
# Filter criteria:
# • Day/Night Indicator = DAY
# • Data Type Level-1 = OLI_TIRS_L1TP
# • Land Cloud Cover < 70

metadata_fil = metadata[(metadata.Day_Night_Indicator == "DAY") &
                        (metadata.Data_Type_Level_1 == "OLI_TIRS_L1TP") & (metadata.Land_Cloud_Cover < 70)]

# questions:
# 1) What is the average geometric accuracy in the X and Y direction: 'Geometric RMSE Model X' and
# 'Geometric RMSE Model Y'?

avg_geom_acc_x = metadata_fil.Geometric_RMSE_Model_X.mean()
avg_geom_acc_y = metadata_fil.Geometric_RMSE_Model_Y.mean()

print(avg_geom_acc_x, " : average geometric accuracy in X-direction", os.linesep,
      avg_geom_acc_y, " : average geometric accuracy in x-direction")

# 2) What is the average land cloud cover?

avg_land_cc = metadata_fil.Land_Cloud_Cover.mean()
print(avg_land_cc, ": average land cloud cover")

# # 3) How many Landsat footprints (unique Path/Row combination) are there?
# Landsat_Product_Identifier:
#     LXSS_LLLL_PPPRRR_YYYYMMDD_yyyymmdd_CC_TX

#     L = Landsat
#     X = Sensor (E = Enhanced Thematic Mapper Plus)
#     SS = Satellite (07 = Landsat 7)
#     LLLL = Processing Correction Level (L1TP = precision and terrain, L1GT = systematic terrain, L1GS = systematic)
#     PPP = WRS Path
#     RRR = WRS Row
#     YYYYMMDD = Acquisition Date expressed in Year, Month, Day
#     yyyymmdd = Processing Date expressed in Year, Month, Day
#     CC = Collection Number (01)
#     TX = Collection Category (RT = Real Time, T1 = Tier 1, T2 = Tier 2)

# slice Landsat_Product_Identifier_string, so that only PathRow remains
# Series.str.slice(start=int, stop=int, step=int)
metadata_sliced = metadata_fil.Landsat_Product_Identifier.str.slice(start=10, stop=16)

# count unique values:
PR_value_count = metadata_sliced.value_counts()
print(len(PR_value_count), "Landsat footprints (unique Path/Row combinations)")


##################### task 2.2 ##########################
# Create a GeoDataFrame of the filtered Landsat scenes and save it as an ESRI shapefile
# (Hint: “UseUR Corner Lat dec”, etc.)

# construct polygons out of the Corner attributes

# creating tuples/points of Longitude and Latitude for the 4 corner points
UL_Corner = [Point(xy) for xy in zip(metadata_fil.UL_Corner_Long_dec, metadata_fil.UL_Corner_Lat_dec)]
UR_Corner = [Point(xy) for xy in zip(metadata_fil.UR_Corner_Long_dec, metadata_fil.UR_Corner_Lat_dec)]
LL_Corner = [Point(xy) for xy in zip(metadata_fil.LL_Corner_Long_dec, metadata_fil.LL_Corner_Lat_dec)]
LR_Corner = [Point(xy) for xy in zip(metadata_fil.LR_Corner_Long_dec, metadata_fil.LR_Corner_Lat_dec)]

geometry2 = []

for i in range(0, len(UR_Corner)):
    geometry2.append(Polygon([p.x, p.y] for p in [UL_Corner[i], UR_Corner[i], LR_Corner[i], LL_Corner[i]]))

# specify the coordinate reference system
crs = "+init=epsg:4326" #http://www.spatialreference.org/ref/epsg/4326/

# create the GeoDataFrame
geo_df2 = GeoDataFrame(metadata_fil, crs=crs, geometry=geometry2)

geo_df2.to_file(driver='ESRI Shapefile', filename='lucas_de2.shp')