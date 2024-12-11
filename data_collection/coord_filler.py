import certifi
import geopy.geocoders
from geopy.geocoders import Nominatim
import ssl
import pandas as pd
import time

ctx = ssl.create_default_context(cafile=certifi.where())
geopy.geocoders.options.default_ssl_context = ctx
nom = Nominatim(user_agent="tristan_scrape")

path = '/Users/tristangarcia/Desktop/hp-pred/data/wa/'


def format_address(house):
    parts = []
    # Check and append if street, suburb, and postcode are present
    if pd.notnull(house['street']):
        parts.append(house['street'])
    if pd.notnull(house['suburb']):
        parts.append(house['suburb'])
    if pd.notnull(house['postcode']):
        parts.append(f'{house["postcode"].astype(int)}')
    if parts:  # if there's at least one part present, append the state
        parts.append('Western Australia')
    # Join the parts with a comma and return the result
    print(parts)
    return ', '.join(parts) if parts else 'None'

def get_coords(address):
    location = nom.geocode(address)
    time.sleep(1)
    if location:
        return location.latitude, location.longitude
    return None, None


def main():
    data = pd.read_csv(f'{path}wa_data.csv')
    # Getting index of data to fill
    index = data.loc[(data['latitude'].isnull()) & (data['suburb'].notnull())].index
    for idx in index:
        house = data.loc[idx]
        address = format_address(house)
        latitude, longitude = get_coords(address)
        # Assigning new latitude and longitude
        data.loc[idx, 'latitude'] = latitude
        data.loc[idx, 'longitude'] = longitude

        # Printing to check progress
        print(data.loc[idx]['latitude'], data.loc[idx]['longitude'])
    
    # Writing to csv
    data.to_csv(f'{path}wa_data.csv', index=False)


main()
