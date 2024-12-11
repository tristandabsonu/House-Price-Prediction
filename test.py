from bs4 import BeautifulSoup
import requests
import json


HEADERS = {
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
}

BASE_URL = 'https://www.domain.com.au/suburb-profile/{}-{}-{}'
row = {
    'locality':'perth',
    'state':'WA',
    'postcode':6000
}

def get_html_data(url):
    resp = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(resp.content, "html.parser")
    script = soup.find('script', id='__NEXT_DATA__', type='application/json')
    data = json.loads(script.text.strip())
    data = data.get('props',{}).get('pageProps',{}).get('__APOLLO_STATE__')
    if data:
        keys = list(data.keys())
        propertyCategory = data.get(keys[1],{}).get('data',{}).get('propertyCategories')
        return propertyCategory
    return None


def get_suburb_statistics(category):
    # Extracts statistics from statistics dict
    bedrooms = category.get('bedrooms',0)
    propertyType = category.get('propertyCategory')
    medianSoldPrice = category.get('medianSoldPrice',0)
    medianRentPrice = category.get('medianRentPrice',0)
    entryLevelPrice = category.get('entryLevelPrice',0)
    luxuryLevelPrice = category.get('luxuryLevelPrice',0)
    avgDaysListed = category.get('daysOnMarket',0)

    return [bedrooms, propertyType, medianSoldPrice, medianRentPrice, entryLevelPrice, luxuryLevelPrice, avgDaysListed]

url = BASE_URL.format(row['locality'].lower().replace(' ', '-'), row['state'].lower(), row['postcode'])
propertyCategory = get_html_data(url)
for category in propertyCategory:
    data = get_suburb_statistics(category)
    print(data)