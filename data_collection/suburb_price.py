'''
Scrapes 'medianSoldPrice','medianRentPrice','entryLevelPrice','luxuryLevelPrice','avgDaysListed' for australian suburbs
with differing bedrooms counts and property types
'''

from bs4 import BeautifulSoup
import requests
import json
import csv
import time
import pandas as pd


HEADERS = {
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
}

BASE_URL = 'https://www.domain.com.au/suburb-profile/{}-{}-{}'

# Adjust path depending on the state you are scraping
path = '/Users/tristangarcia/Desktop/hp-pred/data/'


def get_state_suburbs(state):
    # Loads australian postcodes data 
    # https://www.matthewproctor.com/australian_postcodes
    df = pd.read_csv(f'{path}australian_postcodes.csv')
    # Filters by state
    df = df.loc[df['state']==state]
    # Removes duplicates
    df = df.drop_duplicates(subset=['locality'])
    return df


def get_html_data(url):
    max_retries = 5 
    # Retries the request if None was found
    for _ in range(max_retries):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=10)
            soup = BeautifulSoup(resp.content, "html.parser")
            script = soup.find('script', id='__NEXT_DATA__', type='application/json')
            if script:
                data = json.loads(script.text.strip())
                data = data.get('props', {}).get('pageProps', {}).get('__APOLLO_STATE__')
                if data:
                    keys = list(data.keys())
                    propertyCategories = data.get(keys[1], {}).get('data',{}).get('propertyCategories')
                    return propertyCategories
        except requests.exceptions.RequestException as e:
            pass        
        # No valid propertyCategories found or request failed, wait before retrying
        time.sleep(1)  

    return None    # No info found after 5 attempts


def get_suburb_statistics(category):
    # Extracts statistics from statistics dict
    bedrooms = category.get('bedrooms',0)
    propertyType = category.get('propertyCategory')
    if propertyType is not None:
        propertyType = propertyType.lower()
    medianSoldPrice = category.get('medianSoldPrice',0)
    medianRentPrice = category.get('medianRentPrice',0)
    entryLevelPrice = category.get('entryLevelPrice',0)
    luxuryLevelPrice = category.get('luxuryLevelPrice',0)
    avgDaysListed = category.get('daysOnMarket',0)

    return [bedrooms, propertyType, medianSoldPrice, medianRentPrice, entryLevelPrice, luxuryLevelPrice, avgDaysListed]


def main():
    #'WA' finished
    states = ['NSW','VIC','QLD','SA','ACT','NT','TAS']
    for state in states:
        suburbs = get_state_suburbs(state)
        # Writing new suburb file (overwriting if it exists)
        with open(f'{path}{state.lower()}_suburb_prices.csv', 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['suburb','state','postcode','bedrooms','propertyType','medianSoldPrice',
                             'medianRentPrice','entryLevelPrice','luxuryLevelPrice','avgDaysListed'])

        # Iterates through each suburb
        for index,row in suburbs.iterrows():
            suburb = [row['locality'].lower(), row['state'].lower(),row['postcode']]
            # Requesting and parsing html
            url = BASE_URL.format(row['locality'].lower().replace(' ', '-'), row['state'].lower(), row['postcode'])
            propertyCategory = get_html_data(url)
            # Extracting data
            if propertyCategory:
                # Each propertyCategory is a list, ie: [{2bedroom house,...}, {3 bedroom house,...}, {1 bedroom unit,...}]
                for category in propertyCategory:
                    category_stats = get_suburb_statistics(category)
                    new_row = suburb + category_stats
                    print(new_row)   # Printing to check progress
                    # Appending new row to csv if statistics exist
                    with open(f'{path}{state.lower()}_suburb_prices.csv','a') as file:
                        writer = csv.writer(file)
                        writer.writerow(new_row)
            
            # Sleeping to avoid rate limiting
            time.sleep(1)

if __name__ == '__main__':
    main()