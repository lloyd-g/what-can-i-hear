
#https://db.satnogs.org/
#[https://db.satnogs.org/api/tle/
#https://db.satnogs.org/transmitters
import requests
from requests.exceptions import HTTPError
from pandas.io.json import json_normalize
import pandas as pd
from skyfield.api import load, wgs84
from skyfield.api import EarthSatellite
ts = load.timescale()
#location
grondstation = wgs84.latlon(+51.5, -3.55)
elevation_m = 20.0
t = ts.now()
#list of transmitters sat_id is used as key in satellites api
txurl = 'https://db.satnogs.org/api/transmitters/?format=json'
#need to look like chrome
headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
try:
    response = requests.get(txurl, headers=headers)
    response.raise_for_status()
    # access JSOn content
    jsonResponse = response.json()
  
except HTTPError as http_err:
    print(f'HTTP error occurred: {http_err}')
except Exception as err:
    print(f'Other error occurred: {err}')
df = pd.json_normalize(jsonResponse)

# filter by frequency band
dfband = df[(df['downlink_low'] >= 140000000.0) & (df['downlink_low'] <= 146000000.0)]
# list of satellites to get norad_cat_id using sat_id
saturl = "https://db.satnogs.org/api/satellites/?format=json" 
try:
    response = requests.get(saturl, headers=headers)
    response.raise_for_status()
    # access JSOn content
    jsonRespsat = response.json()

except HTTPError as http_err:
    print(f'HTTP error occurred: {http_err}')
except Exception as err:
    print(f'Other error occurred: {err}')
dfsat = pd.json_normalize(jsonRespsat)
# build list of sat_id's to build frame
ids = dfband['sat_id'].astype(str).values.tolist()
# build frame
satsframe = dfsat.loc[dfsat['sat_id'].isin(ids)]
# loop through frame to get TLE data from 
# celestrak.com/NORAD/elements
# db.satnogs.org TLE data is out of date
for index, row in satsframe.iterrows():
  #build url for query
  n=str(int(row['norad_cat_id']))
  url = 'https://celestrak.com/NORAD/elements/gp.php?CATNR={}'.format(n)
  response = requests.get(url, headers=headers, allow_redirects=True)
  Resptle = response.text
  #
  list  = Resptle.split("\r\n")
  # check responce is correct TLE
  if len(list)>1:
    name = list[0]
    line1 = list[1]
    line2 = list[2] 
    name = name.strip()
    satellite = EarthSatellite(line1, line2, name )
    #find current loaction
    geocentric = satellite.at(t)    
    lat, lon = wgs84.latlon_of(geocentric)
    subpoint = wgs84.latlon(lat.degrees, lon.degrees, elevation_m) 
    #find distance
    difference = satellite - grondstation
    topocentric = difference.at(t) 
    alt, az, distance = topocentric.altaz()
    #visablity test
    if alt.degrees > 0:
      #print(name)
      print('{} above the horizon alt {} az {} distance {:.2f}'.format(name, alt, az, distance.km))
      freqlist = dfband.loc[dfband['sat_id'] == row['sat_id']]
      #list transmitters
      for ind, txd in freqlist.iterrows():
        print('Status {} frequency {:.4f}MHz mode {}'.format(txd['status'],(txd['downlink_low']/1000000),txd['mode']))
      #print( 'The sat is above the horizon')
        
    #else:
    #  print('The below is below the horizon')
#https://skyriddles.wordpress.com/

