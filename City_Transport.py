import requests
from datetime import datetime
import time
from math import ceil, floor


def get_car_route_length(carParams):

    url = 'https://router.hereapi.com/v8/routes?return=summary'
    response = requests.get(url, params=carParams)
    data = response.json()
    # Return distance from 'origin' to 'destination' in meteres
    return (data['routes'][0]['sections'][0]['summary']['length'])


def get_public_transit_time(commonParams):
    url = 'https://transit.router.hereapi.com/v8/routes'
    response = requests.get(url, params=commonParams)
    data = response.json()
    # colleting necessary public transit data in list
    publicTransitStepsList = []
    for travelStep in (data['routes'][0]['sections']):
        travelStepDict = {}
        travelStepDict.update({'arrival': (travelStep['arrival']['time'])})
        travelStepDict.update({'departure': (travelStep['departure']['time'])})
        travelStepDict.update({'type': (travelStep['type'])})
        publicTransitStepsList.append(travelStepDict)

    # looking for first and last 'transit' type transport
    firstAndLastBus = []
    for travelStep in publicTransitStepsList:
        if (travelStep['type'] == 'transit'):
            firstAndLastBus.append(travelStep)
            break
    publicTransitStepsList.reverse()
    for travelStep in publicTransitStepsList:
        if (travelStep['type'] == 'transit'):
            firstAndLastBus.append(travelStep)
            break
    # calculate and  return time (in minutes) travel in public transport
    dateFormat = '%Y-%m-%dT%H:%M:%S'

    rawStartTime = firstAndLastBus[0]['departure']
    rawStartTime = rawStartTime[0:-6]
    startTime = datetime.strptime(rawStartTime, dateFormat)
    startTime_timeStamp = time.mktime(startTime.timetuple())

    rawEndTime = firstAndLastBus[1]['arrival']
    rawEndTime = rawEndTime[0:-6]
    endTime = datetime.strptime(rawEndTime, dateFormat)
    endTime_timeStamp = time.mktime(endTime.timetuple())

    travelTime = (endTime_timeStamp - startTime_timeStamp)/60
    return travelTime


def get_geocoordinates_from_location(userDefinedLocation):

    locationParams = {'apiKey': 'hKtKIZVYfsLbNqwCdOplJNC5sP94aGg4fhC746yGadw',
                      'q': userDefinedLocation,
                      'limit': '1'}
    url = 'https://geocode.search.hereapi.com/v1/geocode?'
    response = requests.get(url, params=locationParams)
    data = response.json()
    rawGeoData = data['items'][0]['access']
    preparedGeoData = str(
        str(rawGeoData[0]['lat']) + str(',') + str(rawGeoData[0]['lng']))
    return preparedGeoData


def calculate_cost_of_travel(get_car_route_length, carParams, get_public_transit_time, commonParams, ticketAndFuelPrices):
    carTravelCost = round((get_car_route_length(carParams) * 0.001 * 0.01 *
                          ticketAndFuelPrices['litersPer100Kilometers'] * ticketAndFuelPrices['1LiterPrice']), 2)
    # find the cheapest ticket variant
    travelTime = get_public_transit_time(commonParams)
    if travelTime <= 20:
        transitTravelCost = ticketAndFuelPrices['20min']
    elif travelTime > 20 and travelTime <= 75:
        transitTravelCost = ticketAndFuelPrices['75min']
    elif travelTime > 75 and (travelTime % 75) > 20:
        transitTravelCost = ceil(travelTime / 75) * \
            ticketAndFuelPrices['75min']
    elif travelTime > 75 and (travelTime % 75) < 20:
        transitTravelCost = round(
            (floor(travelTime/75) * 4.4) + ticketAndFuelPrices['20min'], 2)

    travelList = [carTravelCost, transitTravelCost]
    return travelList


# reapeat asking for data, until it's correct
geoCoordinatesFromOriginPoint = None
geoCoordinatesFromDestinationPoint = None
while (geoCoordinatesFromOriginPoint or geoCoordinatesFromDestinationPoint) == None:
    try:
        originPoint = input("Start point: ")
        destinationPoint = input("End point: ")
        ticketAndFuelPrices = {'1LiterPrice': float(input("Fuel price [zl/L]: ")),
                               'litersPer100Kilometers': float(input("Fuel consuption [L/100km]: ")),
                               '75min': 4.40, '20min': 3.40}

        geoCoordinatesFromOriginPoint = get_geocoordinates_from_location(
            originPoint)
        geoCoordinatesFromDestinationPoint = get_geocoordinates_from_location(
            destinationPoint)
    except (KeyError, IndexError):
        print("Place doesn't exist")
    except (ValueError):
        print("This value is not the number")

commonParams = {'apiKey': 'hKtKIZVYfsLbNqwCdOplJNC5sP94aGg4fhC746yGadw',
                'origin': geoCoordinatesFromOriginPoint,
                'destination': geoCoordinatesFromDestinationPoint}
carParams = {'transportMode': 'car'}
carParams.update(commonParams)


print(calculate_cost_of_travel(get_car_route_length, carParams,
                               get_public_transit_time, commonParams, ticketAndFuelPrices))
