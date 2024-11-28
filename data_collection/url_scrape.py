# I was getting errors before doing this?? I think requests and grequests was clashing
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


path_in = f'/Users/tristangarcia/Desktop/hp-pred_data/postcode/'
path_out = f'/Users/tristangarcia/Desktop/hp-pred_data/url/'


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


def get_state_postcodes(state):
    # Each state has a csv full of it's postcodes and suburbs
    s = pd.read_csv(f'{path_in}{state}_postcodes.csv')
    postcodes = s['postcode']
    return postcodes


def get_postcode_urls(postcode):
    # Searching through each postcode for URL's for the listings
    url = 'https://www.domain.com.au/sold-listings/?postcode={}&excludepricewithheld=1&ssubs=0&page={}'
    response = requests.get(url.format(postcode,1), headers=headers)
    data = parse_data(response)
    data = data.get('props',{}).get('pageProps',{}).get('componentProps')

    if data:
        totalPages = data.get('totalPages')    # totalPages to know when to know how many urls per postcode
        if totalPages > 0:
            postcode_urls = [url.format(postcode,page_num) for page_num in range(1,totalPages+1)]
            return postcode_urls
        else:
            # postcodes with no listings have totalPages == 0
            return []
    return []


def get_listings(data,postcode):
    listing_list = []
    data = data.get('props',{}).get('pageProps',{}).get('componentProps')
    if data:
        all_listings = data.get('listingsMap')
        for listing in all_listings.keys():
            # Each page has a listingsMap whose keys contain the urls for each listing 
            # Returning a tuple of (listing, postcode)
            listing_list.append((all_listings[listing].get('listingModel',{}).get('url'), postcode))
        # returning a list of urls from all listings on a page
        return listing_list


def main():
    # List of Australian states
    states = ['WA','NSW','VIC','QLD','SA','TAS','ACT','NT']
    for state in states:
        state_listings = []
        postcodes = get_state_postcodes(state)
        # Getting urls for each postcode
        for postcode in tqdm(postcodes):
            # Add 0's infront of postcode to make the length equal to 4
            if len(str(postcode)) < 4:
                # '0' * (4 -  len(str(postcode))) determines the number of 0's to add
                postcode = f'{"0"*(4 - len(str(postcode)))}{postcode}'
            # List to contain all the listings for a postcode
            postcode_listings = []
            urls = get_postcode_urls(postcode)
            if len(urls) > 0:
                responses = request_data(urls)
                data = [parse_data(r) for r in responses]
                for d in data:
                    listing_list = get_listings(d,postcode)
                    postcode_listings.extend(listing_list)
                state_listings.extend(postcode_listings)
                print(f'{postcode} completed')
                time.sleep(random.randint(1,3))
            else:
                with open('empty_postcodes.txt','a') as file:
                    file.write(f'{postcode}\n')

        # Writing to a new csv file
        state_df = pd.DataFrame(state_listings, columns=['url','postcode'])
        state_df.to_csv(f'{path_out}{state.lower()}_urls.csv', index=False, header=True)
        # Printing to see progress
        print(f'Finished writing all {state} listing')


if __name__ == '__main__':
    main()