# ############################################################################################################# #
# (c) Matthias Baumann, Humboldt-Universität zu Berlin, 4/15/2019                                               #
# Assignment VI – Raster processing III                                                                          #
# Lukas Blickensdoerfer                                                                                         #
# ####################################### LOAD REQUIRED LIBRARIES ############################################# #

import time
import sys
from osgeo import ogr
import numpy as np
import pandas as pd

# ####################################### SET TIME-COUNT ###################################################### #
starttime = time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime())
print("--------------------------------------------------------")
print("Starting process, time: " + starttime)
print("")
# ####################################### FUNCTIONS ########################################################### #



# ####################################### FOLDER PATHS & global variables ##################################### #

# Folder containing the working data
path_data_folder = r'C:\Users\Lukas\Documents\_UNI\Global_Change_Geography\19_SoSe\geoscripting\ass_06'
prot_areas = "WDPA_May2019-shapefile-polygons.shp"
country_shp = "gadm36_dissolve.shp"
# ####################################### PROCESSING ########################################################## #

# subset marine areas

prot = ogr.Open(path_data_folder + "/" + prot_areas, 1)
'''
if prot is None:
    sys.exit('Could not open {0}.'.format(prot_areas))
layer = prot.GetLayer(0)

for feat in layer:
    # print(feat.GetField('MARINE'))
    if feat.GetField('MARINE') == '2':
        print("delete")
        layer.DeleteFeature(feat.GetFID())
prot.SyncToDisk()
# loop over country and set spatial filter
# calculate needed values
'''
countries = ogr.Open(path_data_folder + "/" + country_shp, 0)
i = 0
df = pd.DataFrame(columns ={'Country ID':[],
                            'Country Name':[],
                            'PA Category':[],
                            '# PAs':[],
                            'Mean area of PAs':[],
                            'Area of largest PA':[],
                            'Name of largest PA':[],
                            'Year of establ. Of largest PA':[]
                            })

for c in countries.GetLayer(0):
    country = c.geometry().Clone()
    country_name = c.GetField('NAME_0')
    print(country_name)
    pro = prot.GetLayer()
    pro.SetSpatialFilter(country)

    PA_DEF = np.empty(pro.GetFeatureCount(), dtype='U25')
    area = np.empty(pro.GetFeatureCount())
    names = np.empty(pro.GetFeatureCount(), dtype='U25')
    years = np.empty(pro.GetFeatureCount(), int)
    j = 0
    for feat in pro:

        PA_DEF[j] = feat.GetField('IUCN_CAT')
        area[j] = feat.GetField('REP_AREA')
        names[j] = feat.GetField('NAME')
        years[j] = feat.GetField('STATUS_YR')


        j += 1
    df = df.append({'Country ID': i,
                    'Country Name': c.GetField('NAME_0'),
                    'PA Category': "all",
                    '# PAs': pro.GetFeatureCount(),
                    'Mean area of PAs': np.mean(area),
                    'Area of largest PA': max(area),
                    'Name of largest PA': names[np.argmax(area)],
                    'Year of establ. Of largest PA': years[np.argmax(area)]}, ignore_index=True)


    for type in np.unique(PA_DEF):
        names_tmp[j] = names[PA_DEF == type]
        years_tmp[j] = names[years == type]

        df = df.append({'Country ID': i,
                        'Country Name': c.GetField('NAME_0'),
                        'PA Category':type ,
                        '# PAs':len(PA_DEF[PA_DEF == type]),
                        'Mean area of PAs': np.mean(area[PA_DEF == type]),
                        'Area of largest PA': max(area[PA_DEF == type]),
                        'Name of largest PA': names_tmp[np.argmax(area[PA_DEF == type])],
                        'Year of establ. Of largest PA': years_tmp[np.argmax(area[PA_DEF == type])]}, ignore_index=True)


    # print(pro.GetField('PA_DEF'))
    # data_frame = pd.DataFrame(pro.GetField('MARINE'))
    # pro.SetSpatialFilter(None)
    i+=1
    if i == 1:
        break
    pro.SetSpatialFilter(None)



# ####################################### END TIME-COUNT AND PRINT TIME STATS##################
print("")
endtime = time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime())
print("--------------------------------------------------------")
print("start: " + starttime)
print("end: " + endtime)
print("")