from bs4 import BeautifulSoup
import grequests
import json
import pandas as pd
import scrape_function as scp
from tqdm import tqdm
import random
import time


headers = {
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
}

col_names = ['listingId','unitNumber','streetNumber','street','suburb','state','postcode','bathrooms','bedrooms','parking','landArea',
            'latitude','longitude','features','agency','propertyTypes','promoLevel','soldMonth','soldYear','daysListed','inspectionsCount',
            'isRural','hasDescription','hasFloorplan','hasDisplayPrice','hasPhoto','photoCount','suburb_medianPrice',
            'suburb_medianRentPrice','suburb_entryLevelPrice','suburb_luxuryLevelPrice','primary','primaryDistance','primaryType',
            'secondary','secondaryDistance','secondaryType','listingUrl','soldPrice']

BASE = 'https://www.domain.com.au{}'
path_in = f'/Users/tristangarcia/Desktop/hp-pred_data/url/'
path_out = f'/Users/tristangarcia/Desktop/hp-pred_data/data/'


def get_urls(state):
    df = pd.read_csv(f'{path_in}{state}_urls.csv')
    slugs = df['url']
    urls = [BASE.format(slug) for slug in slugs]
    return urls


def get_data(urls, batch_size=100):
    all_responses = []
    for i in tqdm(range(0,len(urls),batch_size)):
        batch = urls[i:i+batch_size]
        requests = [grequests.get(link, headers=headers) for link in batch]
        responses  = grequests.map(requests)
        if None in responses:
            with open('url_errors.txt', 'a') as file:
                print(f'Error in batch {i//batch_size+1}')
                file.write(f'Batch {i // batch_size+1}')
                file.write('\n'.join(batch) + '\n')
        else:
                all_responses.extend(responses)
                print(f'Batch {i//batch_size+1} completed')
        time.sleep(random.randint(2,4))

    return all_responses


def parse_data(responses):
    all_rows = []
    for resp in responses:
        soup = BeautifulSoup(resp.content, "html.parser")
        script = soup.find('script', id='__NEXT_DATA__', type='application/json')
        data = json.loads(script.text.strip())
        page = data.get('props',{}).get('pageProps',{})
        if page.get('layoutProps') and page.get('componentProps'):
            row = scp.get_page_data(data)
            all_rows.append(row)
            print(row)

    return all_rows
        

def main():
    urls = get_urls('WA')
    responses = get_data(urls)
    df_rows = parse_data(responses)
    state_data = pd.DataFrame(df_rows, columns=col_names)
    state_data.to_csv(f'{path_out}WA_data.csv', index=False, header=True)


if __name__ == '__main__':
    main()

     


