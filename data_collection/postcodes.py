'''
Uses austrlian_postcodes.csv dataset found on the internet to get postcodes for each state
Source: https://www.matthewproctor.com/australian_postcodes
'''
import pandas as pd


path = '/Users/tristangarcia/Desktop/hp-pred_data/'
postcodes = pd.read_csv(f'{path}australian_postcodes.csv')

def get_postcodes(state):
    
    s = postcodes.loc[postcodes['state'] == state, ['postcode','locality','state']].drop_duplicates(subset='postcode',keep='first')
    s.to_csv(f'{path}{state}_postcodes.csv', index=False, header=True)

for state in ['WA','NSW','VIC','QLD','TAS','ACT','SA','NT']:
    get_postcodes(state)

