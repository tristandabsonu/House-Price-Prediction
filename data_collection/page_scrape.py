from bs4 import BeautifulSoup
import requests
import json
import pandas as pd
import scrape_function as scp

url = 'https://domain.com.au/217-43-rochat-avenue-banyo-qld-4014-2019542334'
headers = {
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
}

result = requests.get(url, headers=headers)
soup = BeautifulSoup(result.content, "html.parser")
script = soup.find('script', id='__NEXT_DATA__', type='application/json')
data = json.loads(script.text.strip())
data = data['props']['pageProps']
row = scp.get_page_data(data)
print(row)

