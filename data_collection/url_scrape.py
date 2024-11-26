import pandas as pd
from bs4 import BeautifulSoup
import requests
import json
import time
import random


headers = {
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
}


path1 = f'/Users/tristangarcia/Desktop/hp-pred_data/postcode/'
path2 = f'/Users/tristangarcia/Desktop/hp-pred_data/url/'


# Parsing __NEXT_DATA__ from html to JSON format
def parse_data(url):
    result = requests.get(url, headers=headers)
    # Parsing html content
    soup = BeautifulSoup(result.content, "html.parser")
    # Finding the information from the script
    script = soup.find('script', id='__NEXT_DATA__', type='application/json')
    # Loading data to JSON format
    data = json.loads(script.text.strip())

    return data


def get_urls_for_postcode(postcode):
    rows = []
    page_num = 1    # Always starting with 1
    while True:
        # Searching through each postcode for URL's for the listings
        url = f'https://www.domain.com.au/sold-listings/?postcode={postcode}&excludepricewithheld=1&ssubs=0&page={page_num}'
        data = parse_data(url)
        data = data.get('props',{}).get('pageProps',{}).get('componentProps')

        if not data:
            break

        totalPages = data.get('totalPages')    # totalPages to know when to stop the search
        all_listings = data.get('listingsMap')
        for listing in all_listings.keys():
            # Each page has a listingsMap whose keys contain the urls for each listing 
            rows.append((all_listings[listing].get('listingModel',{}).get('url'), postcode))

        # Checks that we haven't gone past the total pages
        if page_num >= totalPages:
            break
        page_num += 1

        # Pausing the program every 2 requests
        if (page_num%2) == 0:
            # Sleeping for a random interval between each page search to imitate human behaviour
            time.sleep(random.randint(2,4))
        
    return rows


def main():
    # List of Australian states
    states = ['WA','NSW','VIC','QLD','SA','TAS','ACT','NT']

    for state in states:
        rows = []
        # Each state has a csv full of it's postcodes and suburbs
        s = pd.read_csv(f'{path1}{state}_postcodes.csv')
        postcodes = s['postcode']

        # Getting urls for each postcode
        for postcode in postcodes:
            # Add 0's infront of postcode to make the length equal to 4
            if len(str(postcode)) < 4:
                # '0' * (4 -  len(str(postcode))) determines the number of 0's to add
                postcode = f'{"0"*(4 - len(str(postcode)))}{postcode}'
            listings = get_urls_for_postcode(postcode)
            # Recording postcodes with empty listings
            if len(listings) == 0:
                print(f'Empty Postcode: {postcode}')
                with open('empty_postcodes.txt', 'a') as file:
                    file.write(f'{postcode}\n')
            # Adding to the rows or urls
            rows.extend(listings)
            # Printing to see progress
            print(len(rows), postcode)
            
        # Writing to a new csv file
        rows_df = pd.DataFrame(rows, columns=['url','postcode'])
        rows_df.to_csv(f'{path2}{state}_urls.csv', index=False, header=True)
        # Printing to see progress
        print(f'Finished writing all {state} urls')


if __name__ == '__main__':
    main()