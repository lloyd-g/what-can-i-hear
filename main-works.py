
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
grondstation = wgs84.latlon(+51.5, -3.55)
elevation_m = 20.0
t = ts.now()
txurl = 'https://db.satnogs.org/api/transmitters'
headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
try:
    response = requests.get(txurl, headers=headers)
    response.raise_for_status()
    # access JSOn content
    jsonResponse = response.json()
    #print("Entire JSON response")
    #print(jsonResponse)

except HTTPError as http_err:
    print(f'HTTP error occurred: {http_err}')
except Exception as err:
    print(f'Other error occurred: {err}')
df = pd.json_normalize(jsonResponse)
#df = pd.read_json("https://db.satnogs.org/api/transmitters?format=json")
#print(df.columns)
#print(df.dtypes)
#print(df['downlink_low'].min())
#print(df['downlink_low'].max())
"""
Index(['uuid', 'description', 'alive', 'type', 'uplink_low', 'uplink_high',
       'uplink_drift', 'downlink_low', 'downlink_high', 'downlink_drift',
       'mode', 'mode_id', 'uplink_mode', 'invert', 'baud', 'sat_id',
       'norad_cat_id', 'status', 'updated', 'citation', 'service',
       'iaru_coordination', 'iaru_coordination_url', 'itu_notification',
       'frequency_violation'],
      dtype='object')
uuid                      object
description               object
alive                       bool
type                      object
uplink_low               float64
uplink_high              float64
uplink_drift             float64
downlink_low             float64
downlink_high            float64
downlink_drift           float64
mode                      object
mode_id                  float64
uplink_mode               object
invert                      bool
baud                     float64
sat_id                    object
norad_cat_id             float64
status                    object
updated                   object
citation                  object
service                   object
iaru_coordination         object
iaru_coordination_url     object
itu_notification          object
frequency_violation         bool
dtype: object
"""

dfband = df[(df['downlink_low'] >= 140000000.0) & (df['downlink_low'] <= 146000000.0)]
#print(dfband['sat_id'])
saturl = "https://db.satnogs.org/api/satellites/?format=json" 
try:
    response = requests.get(saturl, headers=headers)
    response.raise_for_status()
    # access JSOn content
    jsonRespsat = response.json()
    #print("Entire JSON response")
    #print(jsonResponse)

except HTTPError as http_err:
    print(f'HTTP error occurred: {http_err}')
except Exception as err:
    print(f'Other error occurred: {err}')
dfsat = pd.json_normalize(jsonRespsat)


#dfsat = pd.read_json("https://db.satnogs.org/api/satellites/?format=json")
#https://www.interviewqs.com/ddi-code-snippets/rows-cols-python
"""
for index, row in df.iterrows():
  print(row["description"], row["sat_id"])
  print(dfsat.loc[dfsat["sat_id"] == row["sat_id"]])
"""
ids = dfband['sat_id'].astype(str).values.tolist()
#print(ids)

satsframe = dfsat.loc[dfsat['sat_id'].isin(ids)]
#print(satsframe.columns)
"""
Index(['sat_id', 'norad_cat_id', 'name', 'names', 'image', 'status', 'decayed',
       'launched', 'deployed', 'website', 'operator', 'countries',
       'telemetries', 'updated', 'citation', 'associated_satellites'],
      dtype='object')
https://gist.github.com/wgaylord/ec4443545cdac736620b49b8e13f7475
https://celestrak.com/NORAD/documentation/gp-data-formats.php
https://celestrak.com/NORAD/elements/gp.php?{QUERY}=VALUE[&FORMAT=VALUE]
https://celestrak.com/NORAD/elements/gp.php?CATNR=25544&FORMAT=TLE
https://celestrak.com/NORAD/elements/gp.php?CATNR=47309
https://docs.poliastro.space/en/latest/examples/Loading%20OMM%20and%20TLE%20satellite%20data.html
"""

for index, row in satsframe.iterrows():
  n=str(int(row['norad_cat_id']))
  #print(n)
  #url = 'http://celestrak.com/satcat/tle.php?CATNR={}&FORMAT=TLE'.format(n)
  url = 'https://celestrak.com/NORAD/elements/gp.php?CATNR={}'.format(n)
  #print(url)
  #filename = 'tle-CATNR-{}.txt'.format(n)
  response = requests.get(url, headers=headers, allow_redirects=True)
  Resptle = response.text
  list  = Resptle.split("\r\n")
  #print(list)
  #print(name, line1, line2 )
  if len(list)>1:
    line1 = list[1]
    line2 = list[2]
    name = list[0]
    #t = ts.now()
    satellite = EarthSatellite(line1, line2, name )
    #print(satellite)
    #print(satellite.at(t).position)
    geocentric = satellite.at(t)
    #print(geocentric.position.km)
    lat, lon = wgs84.latlon_of(geocentric)
    #print( 'Latitude: {} Longitude {}   '.format(lat, lon))
    subpoint = wgs84.latlon(lat.degrees, lon.degrees, elevation_m)      
    difference = satellite - grondstation
    topocentric = difference.at(t)
    #print(topocentric.position.km)     
    alt, az, distance = topocentric.altaz()
    #print('Altitude: {} Azimuth: {} Distance:  {:.1f}'.format(alt, az, distance.km ))
    #print(name)
    if alt.degrees > 0:
      print(name)
      print( 'The sat is above the horizon')
        
    #else:
    #  print('The below is below the horizon')
        
#dfsat = pd.json_normalize(jsonRespsat)
"""
sat1 = satsframe.head(1)
print(sat1)
url = 'https://celestrak.com/NORAD/elements/gp.php?CATNR={}'.format(int(sat1['norad_cat_id']))
print(url)
response = requests.get(url, headers=headers, allow_redirects=True)
Resptle = response
print(Resptle.text)
"""