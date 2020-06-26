### assignment_10: train and evaluate a support vector machine classification to produce and asses
### a land cover map using a sample of Landsat pixels with known reference labels and extracted
### statistical features as predictors
# ####################################### LOAD REQUIRED LIBRARIES ############################################# #

import time
from osgeo import gdal
import pandas as pd
import os
import numpy as np
# %matplotlib inline
from matplotlib import pyplot as plt
from matplotlib import colors, patches
import seaborn as sns

# ####################################### SET TIME-COUNT ###################################################### #
starttime = time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime())
print("--------------------------------------------------------")
print("Starting process, time: " + starttime)
print("")
# ####################################### FUNCTIONS ########################################################### #


# ####################################### FOLDER PATHS & global variables ##################################### #
# Folder containing the working data
path = '<PATH_TO_YOUR_DATA_FOLDER>'
os.chdir(path)

# ####################################### LOAD DATA  ######################################################### #

# landsat metrics image
data = gdal.Open(path + 'landsat8_metrics1416.tif').ReadAsArray()

# reference data set
samples_df = pd.read_csv(path + "landsat8_metrics1416_samples.csv")  # read into pandas dataframe
print(samples_df.head())
# convert dataframe to ndarray
samples_arr = samples_df.as_matrix()

# ######## ARRANGE REFERENCE DATA IN RESPONSE VECTOR (y) AND PREDICTOR /FEATURE MATRIX (X)####################### #

# extract the response vector (y)
y_1 = samples_arr[:,0]    # if pd df: y1 = samples_df['class'] access first column by column name # returns a pandas series

print(y_1[5])
print(y_1.shape)  # (9494,)

# expand dimensions since the shape has to be (n_samples,1)
y = np.expand_dims(y_1, 1)
print(y.shape) # (9494,1)

# extract the predictor /feature matrix (x) by slicing the array
X= samples_arr[:, 1:32]  # in pd: X = samples_df.iloc[:, 1:31]
print(X.shape) #(9494,30) (n_samples, n_features/predictors/bands/spectral obs)

# ###########################STANDARDIZE THE FEATURE VECTOR#################################################### #

# Normalize the feature matrix to unit variance and mean zero
from sklearn.preprocessing import StandardScaler   # package name: skicit-learn
X_scaled = StandardScaler().fit(X.astype('float64')).transform(X.astype('float64'))
print(X_scaled.shape)

# ###########################SPLIT DATA INTO TRAINING AND TESTING SET########################################### #

#  split the data into a training and testing set (50/50)
from sklearn.model_selection import train_test_split
Xtrain, Xtest, ytrain, ytest = train_test_split(X_scaled, y, test_size=0.5,random_state=42)  # test_size = 0.5
# -> outputs a tuple
# need them in a 1d-array
#print(Xtrain.shape())
#Xtrain_arr = np.asarray(Xtrain)   # (np.asarray(tuple))

# ########################### TUNE HYPERPARAMETERS ############################################################# #

# use a grid search cross-validation to explore combinations of parameters.
#  adjust C (which controls the margin hardness) and gamma (which controls the size of the radial basis function kernel),
# and determine the best model
# Define the grid search for C= [1, 5, 10, 50, 100, 1000] and Gamma = [0.0001, 0.0005, 0.001, 0.005].

# Report the overall accuracy and the class-wise accuracies(recall and precision).

# create an instance of the classifier
from sklearn.svm import SVC
svc = SVC(kernel='rbf', class_weight='balanced')
print(svc.get_params())

#grid search cross validation with defined parameters
from sklearn.model_selection import GridSearchCV
param_grid = {'C': [1, 5, 10, 50, 100, 1000],
              'gamma': [0.0001, 0.0005, 0.001, 0.005]}
grid = GridSearchCV(svc, param_grid, cv=5, iid=False)

print('start with grid fit')
# model.fit(X,y):
grid.fit(Xtrain, np.ravel(ytrain))  # ravel: Return a contiguous flattened array. # %time grid.fit(Xtrain, ytrain)
print(grid.best_params_)

# predict(self, samples) -> returns array with predicted values
model = grid.best_estimator_
yfit = model.predict(Xtest)

# accuracy classification score (overall accuracy)
from sklearn.metrics import accuracy_score
acc_score = accuracy_score(ytest, yfit)
print('accuracy score', acc_score)   # accuracy score 0.8938276806404045

# generate classification report (-> lists recovery statistics label by label)
# to get a better sense of the estimator's performance
from sklearn.metrics import classification_report
print(classification_report(ytest, yfit))

from sklearn.metrics import confusion_matrix
mat = confusion_matrix(ytest, yfit)
print(sns.heatmap(mat.T, square=True, annot=True, fmt='d', cbar=False))
plt.xlabel('true label')
plt.ylabel('predicted label') #;
plt.show()




# #####################APPLY THE  MODEL TO LANDSAT DATA TO CREATE A LAND COVER MAP#####################


####### PREPROCESS THE LANDSAT DATA ##########

# when reading the array as raster with gdal: shape = (bands, rows, cols)
# can t be used like that, you have to transform it into a 2-d array: newshape(rows*cols, bands)

print(data.shape)   #(30, 1500, 1500)
bands, cols, rows = data.shape    # ndArray[row_index][col_index]
print(bands, rows, cols) # 30, 1500, 1500

data2d = np.reshape(data, (bands, rows*cols)).transpose()

print('reshaped data2d', data2d.shape) # (2250000, 30)    # bands need to be at the end, if not: np.transpose

# Normalize the data to unit variance and mean zero
data2d_scaled = StandardScaler().fit(data2d.astype('float64')).transform(data2d.astype('float64'))
print(data2d_scaled.shape)

############## PREDICTION  ###################
prediction = model.predict(data2d_scaled)
prediction = np.reshape(prediction, (rows, cols))

# ##################### MAP VISUALIZATION ####################################################
lcImg = prediction

# plot land cover map
lcColors = {1: [1.0, 0.0, 0.0, 1.0],  # Artificial
            2: [1.0, 1.0, 0.0, 1.0],  # Cropland
            3: [0.78, 0.78, 0.39, 1.0],  # Grassland
            4: [0.0, 0.78, 0.0, 1.0],  # Forest, broadleaf
            5: [0.0, 0.39, 0.39, 1.0],  # Forest, conifer
            6: [0.0, 0.0, 1.0, 1.0]}  # Water

index_colors = [lcColors[key] if key in lcColors else (1, 1, 1, 0) for key in range(1, lcImg.max()+1)]

cmap = plt.matplotlib.colors.ListedColormap(index_colors, 'Classification', lcImg.max())

# prepare labels and patches for the legend
labels = ['artificial land', 'cropland', 'grassland', 'forest broadleaved', 'forest coniferous', 'water']
patches = [patches.Patch(color=index_colors[i], label=labels[i]) for i in range(len(labels))]

# put those patched as legend-handles into the legend
plt.legend(handles=patches, bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0., ncol=1, frameon=False)

plt.imshow(lcImg, cmap=cmap, interpolation='none')
plt.show()

# ##################### EXPORT CLASSIFICATION TO GEOTIFF ####################################################

n_rows = 1500
n_cols = 1500
#ds = gdal.Open(path + 'landsat8_metrics1416.tif')

# save land cover map as geotiff

drv = gdal.GetDriverByName('GTiff')
dst_ds = drv.Create('landsat8_landcover.tif',
                    n_rows, n_cols, 1, gdal.GDT_Byte, [])


dst_band = dst_ds.GetRasterBand(1)

# write the data
dst_band.WriteArray(lcImg, 0, 0)

colors = dict((
    (1, (255, 0, 0)),  # Artificial
    (2, (255, 255, 0)),  # Cropland
    (3, (200, 200, 100)),  # Grassland
    (4, (0, 200, 0)),  # Forest broadleaf
    (5, (0, 100, 100)),  # Forest conifer
    (6, (0, 0, 255))  # Water
))

ct = gdal.ColorTable()
for key in colors:
    ct.SetColorEntry(key, colors[key])

dst_band.SetColorTable(ct)

# flush data to disk, set the NoData value and calculate stats
dst_band.FlushCache()

dst_ds.SetGeoTransform(ds.GetGeoTransform())
dst_ds.SetProjection(ds.GetProjectionRef())

dst_ds = None

# ####################################### END TIME-COUNT AND PRINT TIME STATS##################
print("")
endtime = time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime())
print("--------------------------------------------------------")
print("start: " + starttime)
print("end: " + endtime)
print("")

