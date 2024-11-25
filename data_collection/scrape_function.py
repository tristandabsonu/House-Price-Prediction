'''
This code contains all of the code to extract required variables from json format
'''
from datetime import datetime


def get_variable_data(data, keys, variable, default=None):
    for key in keys:
        if isinstance(data, dict):
            data = data.get(key)
        else:
            return default
    return data[variable]


def school_data(data):
    primary, primaryDistance, primaryType = None, None, None
    secondary, secondaryDistance, secondaryType = None, None, None

    for item in data:
        # Check for primary school
        if primary is None and item.get('educationLevel', '').lower() == 'primary':
            primary = item.get('name')
            primaryDistance = item.get('distance')
            primaryType = item.get('type')

        # Check for secondary school
        if secondary is None and item.get('educationLevel', '').lower() == 'secondary':
            secondary = item.get('name')
            secondaryDistance = item.get('distance')
            secondaryType = item.get('type')

        # Stop early if both are found
        if primary and secondary:
            break

    return primary, primaryDistance, primaryType, secondary, secondaryDistance, secondaryType



def get_page_data(data):
    # listing id and url
    listingId = get_variable_data(data, ['componentProps'],'listingId')
    listingUrl = get_variable_data(data, ['componentProps'],'listingUrl')
    # variables from traversing to 'property'
    property_keys = ['layoutProps','digitalData','page','pageInfo','property']
    agency = get_variable_data(data, property_keys,'agency')
    bathrooms = get_variable_data(data, property_keys,'bathrooms')
    bedrooms = get_variable_data(data, property_keys,'bedrooms')
    daysListed = get_variable_data(data, property_keys,'daysListed')
    inspectionsCount = get_variable_data(data, property_keys,'inspectionsCount')
    hasPhoto = get_variable_data(data, property_keys,'hasPhoto')
    hasFloorplan = get_variable_data(data, property_keys,'hasFloorplan')
    hasDisplayPrice = get_variable_data(data, property_keys,'hasDisplayPrice')
    hasDescription = get_variable_data(data, property_keys,'hasDescription')
    parking = get_variable_data(data, property_keys,'parking')
    photoCount = get_variable_data(data, property_keys,'photoCount')
    # variables from traversing to 'listingByIdV2'
    listingByIdV2_keys = ['componentProps','rootGraphQuery','listingByIdV2']
    features = get_variable_data(data, listingByIdV2_keys,'features')
    promoLevel = get_variable_data(data, listingByIdV2_keys,'promoLevel')
    propertyTypes = get_variable_data(data, listingByIdV2_keys,'propertyTypes')
    isRural = get_variable_data(data, listingByIdV2_keys,'isRural')
    landAreaSqm = get_variable_data(data, listingByIdV2_keys,'landAreaSqm')
    # variables from traversing to 'displayableAddress'
    displayableAddress_keys = ['componentProps','rootGraphQuery','listingByIdV2', 'displayableAddress']
    unitNumber = get_variable_data(data, displayableAddress_keys, 'unitNumber')
    streetNumber = get_variable_data(data, displayableAddress_keys, 'streetNumber')
    street = get_variable_data(data, displayableAddress_keys, 'street')
    suburbName = get_variable_data(data, displayableAddress_keys, 'suburbName')
    state = get_variable_data(data, displayableAddress_keys, 'state')
    postcode = get_variable_data(data, displayableAddress_keys, 'postcode')
    # variables from traversing to 'geolocation'
    geolocation_keys = ['componentProps','rootGraphQuery','listingByIdV2','displayableAddress','geolocation']
    latitude = get_variable_data(data, geolocation_keys, 'latitude')
    longitude = get_variable_data(data, geolocation_keys, 'longitude')
    # variables from traversing to 'schoolCatchment'
    school_keys = ['componentProps', 'schoolCatchment']
    schools = get_variable_data(data, school_keys, 'schools')
    primary, primaryDistance, primaryType, secondary, secondaryDistance, secondaryType = school_data(schools)
    # variables from traversing to 'suburbInsights'
    suburbInsights_keys = ['componentProps', 'suburbInsights']
    suburb_medianPrice = get_variable_data(data, suburbInsights_keys, 'medianPrice')
    suburb_medianRentPrice = get_variable_data(data, suburbInsights_keys, 'medianRentPrice')
    suburb_entryLevelPrice = get_variable_data(data, suburbInsights_keys, 'entryLevelPrice')
    suburb_luxuryLevelPrice = get_variable_data(data, suburbInsights_keys, 'luxuryLevelPrice')
    # sold date
    soldDate_keys = ['componentProps','rootGraphQuery','listingByIdV2','soldDetails','soldDate']
    isoDate = get_variable_data(data, soldDate_keys, 'isoDate')
    dt = datetime.strptime(isoDate, "%Y-%m-%dT%H:%M:%S")
    soldYear = dt.year
    soldMonth = dt.month
    # target variable
    target_keys = ['componentProps','rootGraphQuery','listingByIdV2','soldDetails','soldPrice','rawValues']
    soldPrice = get_variable_data(data, target_keys, 'exactPrice')

    return [listingId,unitNumber,streetNumber,street,suburbName,state,postcode,bathrooms,bedrooms,parking,landAreaSqm,
            latitude,longitude,features,agency,propertyTypes,promoLevel,soldMonth,soldYear,daysListed,inspectionsCount,
            isRural,hasDescription,hasFloorplan,hasDisplayPrice,hasPhoto,photoCount,suburb_medianPrice,
            suburb_medianRentPrice,suburb_entryLevelPrice,suburb_luxuryLevelPrice,primary,primaryDistance,primaryType,
            secondary,secondaryDistance,secondaryType,listingUrl,soldPrice]