'''
Logic:
- Search property listings for each postcode in each state
- Each postcode search will have a total number of pages (0 if no listings found or max 50), extract total pages
- Asynchronously request all pages for the postcode
- Parse responses and extract slugs (url suffix) for each listing in each page (max 20 listings per page)
'''

# I was getting errors before doing this?? I think requests and grequests was clashing, but I need to use them both
from gevent import monkey
monkey.patch_all()  # Applying "monkey patching"

from bs4 import BeautifulSoup
import requests
import grequests
import json
from tqdm import tqdm
import time
import random
import pandas as pd


headers = {
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
}


# Adjust path depending on the state you are scraping
path_in = f'/Users/tristangarcia/Desktop/hp-pred/data/'
path_out = f'/Users/tristangarcia/Desktop/hp-pred/data/wa/'


# Parsing __NEXT_DATA__ from html to JSON format
def parse_data(response):
    # Parsing html content
    soup = BeautifulSoup(response.content, "html.parser")
    # Finding the information from the script
    script = soup.find('script', id='__NEXT_DATA__', type='application/json')
    # Loading data to JSON format
    data = json.loads(script.text.strip())

    return data


def request_data(urls):
    # Asynchronously makes requests for a list of urls
    requests = [grequests.get(url, headers=headers) for url in urls]
    responses  = grequests.map(requests)
    return responses


def get_state_suburbs(state):
    # Each state has a csv full of it's postcodes and suburbs
    df = pd.read_csv(f'{path_in}{state.lower()}_suburb_statistics.csv')
    # Extract unique suburbs and their postcodes
    unique_suburbs = df[['suburb', 'postcode']].drop_duplicates()
    
    # Format the suburb names with state and postcode
    formatted_suburbs = unique_suburbs.apply(
        lambda x: f"{x['suburb'].replace(' ', '-').lower()}-{state.lower()}-{x['postcode']}", axis=1)
    
    return formatted_suburbs.tolist()


def get_suburb_urls(suburbs, retries=3):
    # Searching through each suburb for URL's for the listings
    # Base URL is long because filters applied for property types:  'ptype=apartment-unit-flat,duplex,free-standing,pent-house,semi-detached,studio,terrace,villa'
    url = 'https://www.domain.com.au/sold-listings/{}/?page={}&ptype=apartment-unit-flat,duplex,free-standing,pent-house,semi-detached,studio,terrace,villa&excludepricewithheld=1&ssubs=0'
    attempt = 0
    
    while attempt < retries:
        try:
            # Attempt to fetch the data
            response = requests.get(url.format(suburbs, 1), headers=headers, timeout=10)
            data = parse_data(response)
            data = data.get('props', {}).get('pageProps', {}).get('componentProps')
            
            if data:
                totalPages = data.get('totalPages')  # Find total pages to determine number of URLs per suburb
                if totalPages > 0:
                    suburb_urls = [url.format(suburbs, page_num) for page_num in range(1, totalPages + 1)]
                    return suburb_urls
            return []  # Return empty list if no data or totalPages is 0
        except requests.exceptions.TooManyRedirects:
            print(f"Too many redirects encountered for {url.format(suburbs, 1)}. Attempt {attempt + 1} of {retries}.")
            attempt += 1
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            return []  # Return empty list in case of other request-related errors

    print("Failed to retrieve data after multiple attempts.")
    return []  # Return empty list if all attempts fail


def get_listings(data,suburb):
    listing_list = []
    data = data.get('props',{}).get('pageProps',{}).get('componentProps')
    if data:
        all_listings = data.get('listingsMap')
        for listing in all_listings.keys():
            # Each page has a listingsMap whose keys contain the urls for each listing 
            # Returning a tuple of (listing, postcode)
            listing_list.append((all_listings[listing].get('listingModel',{}).get('url'), suburb))
        # returning a list of urls from all listings on a page
        return listing_list


def main():
    # List of Australian states
    # 'WA','NSW','VIC','QLD','SA','TAS','ACT','NT'
    states = ['WA']
    for state in states:
        print(f'Processing: {state}')
        state_listings = []
        suburbs = get_state_suburbs(state)

        # Getting urls for each postcode
        for suburb in tqdm(suburbs):
            # Add 0's infront of postcode to make the length equal to 4
            # if len(str(suburbs)) < 4:
            #     # '0' * (4 -  len(str(postcode))) determines the number of 0's to add
            #     postcode = f'{"0"*(4 - len(str(postcode)))}{postcode}'
            # List to contain all the listings for a postcode
            suburb_listings = []
            urls = get_suburb_urls(suburb)

            if len(urls) > 0:
                responses = request_data(urls)
                data = [parse_data(r) for r in responses]
                for d in data:
                    listing_list = get_listings(d,suburb)
                    suburb_listings.extend(listing_list)
                state_listings.extend(suburb_listings)
                time.sleep(random.randint(1,3))

        # Writing to a new csv file
        state_df = pd.DataFrame(state_listings, columns=['url','suburb'])
        state_df.to_csv(f'{path_out}{state.lower()}_listing_urls.csv', index=False, header=True)
        # Printing to see progress
        print(f'Finished writing all {state} listing')


if __name__ == '__main__':
    main()