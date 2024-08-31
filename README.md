# OGCAPI_ODC
This repo is a Python code that implements a CGI in python that allows accessing data from a Data Cube. There is a demo instance on the development instance of the Catalan Data Cube.
https://callus.ddns.net/cgi-bin/mmdc.py

## Status
The developement started as a WCS and WMS implementation (only a simplified version of GetMap and GetCoverage operations) but has evolved to support OGC APIs. For the moment it focus on OGC API coverages. In 2024-08-30 it supported:

* Landing page: https://callus.ddns.net/cgi-bin/mmdc.py
* Conformance page: https://callus.ddns.net/cgi-bin/mmdc.py/conformance
* OpenAPI page: https://callus.ddns.net/cgi-bin/mmdc.py/api?f=json
* Collections page: https://callus.ddns.net/cgi-bin/mmdc.py/collections
* Collections page: https://callus.ddns.net/cgi-bin/mmdc.py/collections/s2_level2a_granule
* Schema page: https://callus.ddns.net/cgi-bin/mmdc.py/collections/s2_level2a_granule/schema
* Retrieving a band of a multiband (with or without scale factor: https://callus.ddns.net/cgi-bin/mmdc.py/collections/s2_level2a_granule/coverage?subset=E(422401.47:437401.47),N(4582942.45:4590742.45),time(%222018-03-29%22)&subset-crs=[EPSG:32631]&crs=[EPSG:32631]&properties=B04_10m&scale-factor=3&f=jpeg
* Generate NDVI (or other band index): https://callus.ddns.net/cgi-bin/mmdc.py/collections/s2_level2a_granule/coverage?subset=E(422401.47:437401.47),N(4582942.45:4590742.45),time(%222018-03-29%22)&subset-crs=[EPSG:32631]&crs=[EPSG:32631]&properties=(B08_10m-B04_10m)/(B08_10m%2BB04_10m)
* Generate NDVI (or other band index) filtering clouds: https://callus.ddns.net/cgi-bin/mmdc.py/collections/s2_level2a_granule/coverage?subset=E(422401.47:437401.47),N(4582942.45:4590742.45),time(%222018-04-28%22)&subset-crs=[EPSG:32631]&crs=[EPSG:32631]&properties=(B08_10m-B04_10m)/(B08_10m%2BB04_10m)&filter=(SCL_20m=4)%20or%20(SCL_20m=5)%20or%20(SCL_20m=6)
* Generate the difference between two NDVI dates (or other band index) filtering clouds: https://callus.ddns.net/cgi-bin/mmdc.py/collections/s2_level2a_granule/coverage?subset=E(422401.47:437401.47),N(4582942.45:4590742.45),time(%222018-04-28%22)&subset-crs=[EPSG:32631]&crs=[EPSG:32631]&properties=(B08_10m-B04_10m)/(B08_10m%2BB04_10m)-Slice((B08_10m-B04_10m)/(B08_10m%2BB04_10m),['time'],['2018-04-18'])&filter=(SCL_20m=4)or(SCL_20m=5)or(SCL_20m=6)
* Generate the difference between two Connectivity map dates (Catalonia): http://localhost/cgi-bin/mmdc.py/collections/TerrestrialConnectivityIndex/coverage?subset=E(260000:528000),N(4488000:4748000),time(%222017-01-01%22)&subset-crs=[EPSG:32631]&crs=[EPSG:32631]&properties=Forest-Slice(Forest,[%22time%22],[%222012-01-01%22])&scale-factor=0.5

## Acknowledgement
This activity is part of the AD4GD work. The AD4GD project is co-funded by the European Union, Switzerland and the United Kingdom.
