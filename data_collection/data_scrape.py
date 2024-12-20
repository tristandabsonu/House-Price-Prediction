from bs4 import BeautifulSoup
import grequests
import json
import pandas as pd
import scrape_function as scp
from tqdm import tqdm
import random
import time
import os


headers = {
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
}

col_names = ['listingId','unitNumber','streetNumber','street','suburb','state','postcode','bathrooms','bedrooms','parking','landArea',
            'latitude','longitude','features','agency','propertyTypes','promoLevel','soldMonth','soldYear','daysListed','inspectionsCount',
            'isRural','hasDescription','hasFloorplan','hasDisplayPrice','hasPhoto','photoCount','suburb_medianPrice',
            'suburb_medianRentPrice','suburb_entryLevelPrice','suburb_luxuryLevelPrice','primary','primaryDistance','primaryType',
            'secondary','secondaryDistance','secondaryType','listingUrl','soldPrice']

# Base URL
BASE = 'https://www.domain.com.au{}'
# File paths
path = f'/Users/tristangarcia/Desktop/hp-pred/data/wa/'


def remove_file(state):
    output_path = f'{path}{state.lower()}_data.csv'
    # Remove file if it exists
    if os.path.exists(output_path):
        os.remove(output_path)
        print(f'Existing file {output_path} removed.')


def get_urls(state):
    # Open state csv as a pandas df
    df = pd.read_csv(f'{path}{state.lower()}_listing_urls.csv')
    # Accessing the url column (containing the slugs (suffix of a url) of each listing)
    slugs = df['url'].unique()
    # Converts slugs into full urls
    urls = [BASE.format(slug) for slug in slugs]
    return urls


def get_data(urls, resp_batch_size=100):
    '''
    Sending requests for a batch of links 
    Pausing program between each batch to avoid rate limiting
    '''
    # List to contain all responses for listings in a state
    all_responses = []
    # Goes through all urls from a state in batches
    for i in tqdm(range(0,len(urls),resp_batch_size)):
        batch = urls[i:i+resp_batch_size]
        # Asynchronous requests for faster processing
        requests = [grequests.get(link, headers=headers) for link in batch]
        responses  = grequests.map(requests)
        # If any errors with requests, None response will be returned
        if any(resp and resp.status_code == 430 for resp in responses):
            # Save all errors in a log
            with open('url_errors.txt', 'a') as file:
                file.write(f'Batch {i // resp_batch_size+1}\n')
                file.write('\n'.join(batch) + '\n')
        else:
                # If successful, batch of responses is added to all_responses
                all_responses.extend(responses)
        # Sleeping at random # of seconds between 1-3 to imitate human behaviour
        time.sleep(random.randint(1,3))

    return all_responses


def parse_data(responses):
    # List to contain all rows for a df for house data for a state
    all_rows = []
    # Parses every responses synchronously
    for resp in tqdm(responses):
        soup = BeautifulSoup(resp.content, "html.parser")
        script = soup.find('script', id='__NEXT_DATA__', type='application/json')
        data = json.loads(script.text.strip())
        # First two key traversal should always be available 
        page = data.get('props',{}).get('pageProps',{})
        # Ensures there is data to be scraped
        if page.get('layoutProps') and page.get('componentProps'):
            # Function from scrape_function.py to find all data relevant to a listing
            row = scp.get_page_data(page)
            all_rows.append(row)

    return all_rows
        

def main():
    # 'WA', 'NSW', 'VIC', 'SA','TAS','ACT','NT'
    states = ['WA']
    for state in states:
        # Removing file if it exists
        remove_file(state)
        
        print(f'\nWebscraping {state}...')
        # Reading url data
        urls = get_urls(state)
        print(f'Number of urls: {len(urls)}')
        # Process data in chunks (avoids memory overload on a single list)
        url_batch_size = 10000    # Adjust batch size for memory efficiency
        print(f'Number of batches: {len(urls)//url_batch_size + 1}\n')
        for i in range(0, len(urls), url_batch_size):
            start_time = time.time()
            print(f'Requesting batch {i // url_batch_size + 1} urls...')
            batch_urls = urls[i:i + url_batch_size]
            # Sending requests for the batch
            responses = get_data(batch_urls)
            # Parsing all responses
            print('Parsing responses...')
            df_rows = parse_data(responses)
            # Converting list of rows to a DataFrame
            batch_data = pd.DataFrame(df_rows, columns=col_names)
            # Writing data to CSV incrementally
            write_mode = 'a' if i > 0 else 'w'
            header = i == 0    # Only include header for the first batch
            batch_data.to_csv(f'{path}{state.lower()}_data.csv', mode=write_mode, index=False, header=header)
            print(f'Batch {i // url_batch_size + 1} saved.')
            print(f'---- {round(time.time() - start_time, 2)} seconds ----\n')

        print(f'{state} data collected successfully!\n')


if __name__ == '__main__':
    main()

     


