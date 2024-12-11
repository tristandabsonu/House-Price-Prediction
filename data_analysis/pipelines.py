from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.neighbors import KNeighborsRegressor, BallTree
from sklearn.preprocessing import OneHotEncoder, StandardScaler, MultiLabelBinarizer

import geopandas as gpd
from shapely.geometry import Point
from geopy.distance import geodesic

import pandas as pd
import numpy as np
import ast



################  Initial preprocessing  ################

class ColumnFilter(BaseEstimator, TransformerMixin):
    def __init__(self, column, threshold, method=None):
        self.column = column
        self.threshold = threshold
        self.method = method
        
    def fit(self, X, y=None):
        return self
    
    def transform(self, X):
        if self.column in X.columns:
            # Column greater than
            if self.method=='greater': 
                X = X[X[self.column] > self.threshold]
            # Column less than
            elif self.method=='less':
                X = X[X[self.column] < self.threshold]
            # Column equal to
            elif self.method=='equal':
                X = X[X[self.column] == self.theshold]
            # Column not equal to
            elif self.method=='not_equal':
                X = X[X[self.column] != self.threshold]
        return X
        

class MissingDataRemover(BaseEstimator, TransformerMixin):
    def __init__(self, columns):
        # Columns where missing data will result in row removal
        self.columns = columns
        
    def fit(self, X, y=None):
        return self

    def transform(self, X):
        # Drop rows where any of the specified columns have missing data
        cols_to_drop = [col for col in self.columns if col in X.columns]
        return X.dropna(subset=cols_to_drop)
    
    
################  Reformatting features  ################

class PropertyTypeFormatter(BaseEstimator, TransformerMixin):
    def __init__(self):
        self.valid_types = ['house', 'apartment']
        
    def fit(self, X, y=None):
        return self

    def transform(self, X):
        X = X.copy()
        X['propertyType'] = X['propertyType'].str.split(',')
        # Apply the cleaning function
        X['propertyType'] = X['propertyType'].apply(self.reformat_propertyTypes)
        X['propertyType'] = X['propertyType'].apply(lambda x: 'unit' if x == 'apartment' else x)
        return X

    def reformat_propertyTypes(self, row):
        # Returning the first instance of a valid property type if it's in the list
        if not isinstance(row, list):
            return np.nan
        for t in row:
            if t.lower() in self.valid_types:
                return t.lower()
        return np.nan
    
    
class FeaturesFormatter(BaseEstimator, TransformerMixin):
    def __init__(self, synonym_mapping):
        self.synonym_mapping = synonym_mapping
    
    def fit(self, X, y=None):
        return self

    def transform(self, X):
        X = X.copy()
        # Creating an empty column if column doesn't exist
        if 'features' not in X.columns:
            X['features'] = np.nan
        # Apply transformations
        X['features'] = X['features'].apply(self.parse_features)
        X['features'] = X['features'].apply(self.lower_features)
        X['features'] = X['features'].apply(self.synonym_map)
        return X
    
    def parse_features(self, feature_string):
       # Use ast.literal_eval to convert string lists into lists ('[a,b,c]' -> ['a','b','c'])
        try:
            return ast.literal_eval(feature_string) if pd.notnull(feature_string) else []
        except SyntaxError:
            return [] 
    
    def lower_features(self, feature_list):
        # Convert all features to lowercase
        return [feature.lower() for feature in feature_list]
    
    def synonym_map(self, feature_list):
        # Map features to their synonyms
        return [self.synonym_mapping.get(feature, feature).replace(" ", "_") for feature in feature_list]

    
class LowercaseFormatter(BaseEstimator, TransformerMixin):        
    def fit(self, X, y=None):
        return self

    def transform(self, X):
        # Assuming X is a DataFrame with the target column
        X = X.copy()
        for col in X.columns:
            X[col] = X[col].apply(lambda x: x.lower() if isinstance(x, str) else x)
        return X

    
################  Missing value imputation  ################

class CoordinateFiller(BaseEstimator, TransformerMixin):
    def __init__(self, coord_df):
        self.coord_df = coord_df[['suburb', 'latitude', 'longitude']]
        
    def fit(self, X, y=None):
        return self

    def transform(self, X):
        # Creating an empty column if column doesn't exist
        if 'latitude' not in X.columns:
            X['latitude'] = np.nan
        if 'longitude' not in X.columns:
            X['longitude'] = np.nan
            
        # Merge the coordinate data with the main DataFrame
        X = pd.merge(X, self.coord_df, on='suburb', how='left', suffixes=('', '_from_coord'))
        # Fill missing latitude and longitude values
        X['latitude'] = X['latitude'].fillna(X['latitude_from_coord'])
        X['longitude'] = X['longitude'].fillna(X['longitude_from_coord'])
        # Drop the extra columns
        X.drop(['latitude_from_coord', 'longitude_from_coord'], axis=1, inplace=True)
        return X


class LandAreaFiller(BaseEstimator, TransformerMixin):
    def __init__(self, n_neighbors=1):
        self.n_neighbors = n_neighbors
        self.imputer = KNeighborsRegressor(n_neighbors=self.n_neighbors)
    
    def fit(self, X, y=None):
        # Filter out rows where any of these columns are null
        valid_data = X.dropna(subset=['landArea', 'latitude', 'longitude'])
        if not valid_data.empty:
            self.imputer = KNeighborsRegressor(n_neighbors=self.n_neighbors)
            self.imputer.fit(valid_data[['latitude', 'longitude']], valid_data['landArea'])
        return self

    def transform(self, X):
        # Ensure 'landArea' column exists
        if 'landArea' not in X.columns:
            X['landArea'] = np.nan

        # Only perform imputation if the imputer has been fitted
        if 'latitude' in X.columns and 'longitude' in X.columns:
            # Find rows where imputation is needed
            missing = X.loc[X['landArea'].isnull() & X['latitude'].notnull() & X['longitude'].notnull(), ['latitude', 'longitude']]
            if not missing.empty:
                X.loc[missing.index, 'landArea'] = self.imputer.predict(missing)

        return X


################  Feature Engineering  ################

class SuburbFeatureAdder(BaseEstimator, TransformerMixin):
    def __init__(self, merge_keys, add_features, df):
        self.merge_keys = merge_keys
        combined_features = merge_keys + add_features
        self.df = df[combined_features].copy().fillna(0)
        self.df.columns = [f'suburb_{col}' if col not in merge_keys else col for col in self.df.columns]
    
    def fit(self, X, y=None):
        return self
    
    def transform(self, X):
        X = pd.merge(X, self.df, on=self.merge_keys, how='left').fillna(0)
        return X


class SchoolFeatureAdder(BaseEstimator, TransformerMixin):
    def __init__(self, schools_df, school_type, state='wa'):
        self.schools_df = schools_df
        self.school_type = school_type
        self.state = state

    def fit(self, X, y=None):
        # Filter schools by state and type
        self.filtered_schools = self.schools_df[
            (self.schools_df['state'] == self.state) &
            ((self.schools_df['type'] == self.school_type) | (self.schools_df['type'] == 'combined'))
        ][['school', 'type', 'sector', 'latitude', 'longitude', 'icsea']]

        # Convert lat/lon to radians for BallTree
        schools_coords = np.radians(self.filtered_schools[['latitude', 'longitude']].values)
        self.tree = BallTree(schools_coords, metric='haversine')

        return self

    def transform(self, X):
        df_coords = np.radians(X[['latitude', 'longitude']].values)

        # Query nearest neighbors (results are in radians; multiply by Earth radius for meters)
        distances, indices = self.tree.query(df_coords, k=1)
        distances_m = distances.flatten() * 6371000  # Earth radius in meters

        # Extract details of the nearest schools
        nearest_schools = self.filtered_schools.iloc[indices.flatten()].reset_index()
        nearest_schools['distance_m'] = distances_m  # Add distances in meters

        # Map results back to df
        X[f'{self.school_type}_school'] = nearest_schools['school'].values
        X[f'{self.school_type}Distance'] = nearest_schools['distance_m'].values
        X[f'{self.school_type}Type'] = nearest_schools['type'].values
        X[f'{self.school_type}ICSEA'] = nearest_schools['icsea'].fillna(0).values

        return X


class CoastDistanceFeature(BaseEstimator, TransformerMixin):
    def __init__(self, coastline_df, crs='EPSG:3577', origin_crs='EPSG:4326', bounds={"minx": 112.0, "maxx": 154.0,
                                                                                      "miny": -44.0, "maxy": -10.0}):
        self.coastline_df = coastline_df
        self.bounds = bounds
        self.crs = crs
        self.origin_crs = origin_crs

    def fit(self, X, y=None):
        # Filter coastline for Australian bounds
        self.filtered_coastline = self.coastline_df.cx[
            self.bounds["minx"]:self.bounds["maxx"],
            self.bounds["miny"]:self.bounds["maxy"]
        ]
        
        # Reproject the filtered coastline to the specified CRS
        self.filtered_coastline = self.filtered_coastline.to_crs(self.crs)
        
        return self

    def transform(self, X):
        # Convert DataFrame to GeoDataFrame with the original CRS
        X['geometry'] = X.apply(lambda row: Point(row['longitude'], row['latitude']), axis=1)
        gdf = gpd.GeoDataFrame(X, geometry='geometry', crs=self.origin_crs)
        # Reproject GeoDataFrame to the coastline CRS
        gdf = gdf.to_crs(self.crs)
        # Calculate distances to the nearest coastline and add as a new column
        X['coastDistance'] = gdf.geometry.apply(
            lambda point: self.filtered_coastline.distance(point).min()
        )
        # Drop the helperc olumn
        X = X.drop(columns=['geometry'])
        
        return X


class CBDDistanceCalculator(BaseEstimator, TransformerMixin):
    def __init__(self, cbd_coords=(-31.9514, 115.8617)):
        self.cbd_coords = cbd_coords

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        X['cbdDistance'] = X.apply(
            lambda row: geodesic((row['latitude'], row['longitude']), self.cbd_coords).meters, axis=1
        )
        return X


################  Feature scaling  ################

class PriceScaler(BaseEstimator, TransformerMixin):
    def __init__(self, price_index_df=None):
        self.price_index_df = price_index_df[['soldYear','propertyType', 'scalingFactor']]
        
    def fit(self, X, y=None):
        return self
    
    def transform(self, X):
        # Check if both 'soldPrice' and 'soldYear' are in the DataFrame
        if 'soldPrice' in X.columns and 'soldYear' in X.columns and self.price_index_df is not None:
            X = X.merge(self.price_index_df, on=['soldYear', 'propertyType'], how='left')
            X['scalingFactor'] = X['scalingFactor'].fillna(1)  # Fill missing scaling factors with 1
            X['soldPrice'] = X['soldPrice'] * X['scalingFactor']
            X = X.drop(columns=['scalingFactor'])
        return X
       

class FeatureScaleTransform(BaseEstimator, TransformerMixin):
    def __init__(self, columns, method=None):
        self.columns = columns
        self.method = method
    
    def fit(self, X, y=None):
        return self
    
    def transform(self, X):
        # Ensure columns to be transformed is in the dataframe
        log_cols = [col for col in self.columns if col in X.columns]
        if self.method=='log':
            for col in log_cols:
                X[col] = X[col].apply(lambda x: x if x == 0 else np.log10(x))
        elif self.method=='sqrt':
            for col in log_cols:
                X[col] = X[col].apply(lambda x: x if x == 0 else np.log10(x))    
        
        return X


################  Final Preprocessing  ################

class ColumnDropper(BaseEstimator, TransformerMixin):
    def __init__(self, columns):
        self.columns = columns
        
    def fit(self, X, y=None):
        return self
    
    def transform(self, X):
        # Filter out columns that are not in dataframe
        cols_to_drop = [col for col in self.columns if col in X.columns]
        return X.drop(columns=cols_to_drop)


class CustomStandardiser(BaseEstimator, TransformerMixin):
    def __init__(self, columns):
        self.columns = columns
        self.scaler = StandardScaler() 
    
    def fit(self, X, y=None):
        X[self.columns] = X[self.columns].astype(np.float64)
        self.scaler.fit(X[self.columns])
        return self
    
    def transform(self, X):
        X = X.copy()
        X[self.columns] = self.scaler.transform(X[self.columns].astype(np.float64))
        return X


class CustomOHE(BaseEstimator, TransformerMixin):
    def __init__(self, columns):
        self.columns = columns
        self.encoder = OneHotEncoder(handle_unknown='ignore')

    def fit(self, X, y=None):
        self.encoder.fit(X[self.columns].astype(str))
        return self

    def transform(self, X):
        
        # Encoding
        transformed = self.encoder.transform(X[self.columns].astype(str))
        
        # Check if the output of transform needs to be converted to an array
        if hasattr(transformed, 'toarray'):
            transformed = transformed.toarray()  # Convert sparse matrix to a dense array
        # If it's already a numpy array, no conversion is needed

        # Reformatting OHE column names
        transformer_names = self.encoder.get_feature_names_out()
        ohe_names = [name.split('__', 1)[-1] for name in transformer_names]
    
        # Converting back to dataframe
        transformed_df = pd.DataFrame(transformed, columns=ohe_names, index=X.index)

        # Joining OHE df with other numerical features
        X = pd.concat([X.drop(columns=self.columns), transformed_df], axis=1)
        
        return X


class CustomMultiLabelBinarizer(BaseEstimator, TransformerMixin):
    def __init__(self, column):
        self.column = column
        
    def fit(self, X, y=None):
        feature_dict = {}

        for listing in X[self.column]:
            for feature in listing:
                if feature in feature_dict.keys():
                    feature_dict[feature] += 1
                else:
                    feature_dict[feature] = 1
                    
        feature_dict = {key: value for key, value in feature_dict.items() if value >= 1000}
        self.selected_features = list(feature_dict.keys())
        return self
        
    def transform(self, X):
        for feature in self.selected_features:
            X[f'feature_{feature.replace(" ", "_")}'] = X[self.column].apply(lambda x: 1 if feature in x else 0)
        
        return X.drop(columns=[self.column])


    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    