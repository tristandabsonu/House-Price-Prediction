from bs4 import BeautifulSoup
import requests
import json
import pandas as pd



url = 'https://www.domain.com.au/10-glenton-street-abbotsbury-nsw-2176-2019465947'
headers = {
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
}

result = requests.get(url, headers=headers)
soup = BeautifulSoup(result.content, "html.parser")
script = soup.find('script', id='__NEXT_DATA__', type='application/json')
data = json.loads(script.text.strip())
data = data['props']['pageProps']
print(data['componentProps']['rootGraphQuery']['listingByIdV2']['promoLevel'])