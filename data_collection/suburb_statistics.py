from bs4 import BeautifulSoup
import requests
import json
import csv
import time
import pandas as pd
from tqdm import tqdm


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
                    statistics = data.get(keys[0], {}).get('statistics')
                    if statistics:  # Check if statistics is not None
                        return statistics
        except requests.exceptions.RequestException as e:
            pass        
        # No valid statistics found or request failed, wait before retrying
        time.sleep(1)  

    return None    # No info found after 5 attempts


def get_suburb_statistics(statistics):
    # Extracts statistics from statistics dict
    marriedPercentage = statistics.get('marriedPercentage',0)
    ownerOccupierPercentage = statistics.get('ownerOccupierPercentage',0)
    population = statistics.get('population',0)
    renterPercentage = statistics.get('renterPercentage',0)
    singlePercentage = statistics.get('singlePercentage',0)
    mostCommonAgeBracket = statistics.get('mostCommonAgeBracket',0)

    return [marriedPercentage,ownerOccupierPercentage,population,renterPercentage,singlePercentage,mostCommonAgeBracket]


def main():
    #'NSW','VIC','QLD','SA','ACT','NT','TAS'
    states = ['WA']
    for state in states:
        # Writing new suburb file (overwriting if it exists)
        with open(f'{path}{state.lower()}_suburb_statistics.csv', 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['suburb','state','postcode','latitude','longitude','marriedPercentage','ownerOccupierPercentage',
                             'population','renterPercentage','singlePercentage','mostCommonAgeBracket'])
        
        suburbs = get_state_suburbs(state)

        # Iterates through each suburb
        for index,row in tqdm(suburbs.iterrows(), total=suburbs.shape[0]):
            new_row = [row['locality'].lower(), row['state'].lower(),row['postcode'],row['lat'],row['long']]
            # Requesting and parsing html
            url = BASE_URL.format(row['locality'].lower().replace(' ', '-'), row['state'].lower(), row['postcode'])
            data = get_html_data(url)
            # Extracting data
            if data:
                suburb_stats = get_suburb_statistics(data)
                new_row.extend(suburb_stats)
                # Appending new row to csv if statistics exist
            with open(f'{path}{state.lower()}_suburb_statistics.csv','a') as file:
                writer = csv.writer(file)
                writer.writerow(new_row)
            
            print(new_row)   # Printing to check progress
            # Sleeping to avoid rate limiting
            time.sleep(1)

if __name__ == '__main__':
    main()