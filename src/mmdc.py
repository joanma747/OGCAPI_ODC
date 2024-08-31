
import os
import sys
#import pkg_resources
import json
#import cgi
import urllib.parse

#os.environ['GDAL_DATA']="C:/Users/miniusu.GRUMETS-CAT/AppData/Local/conda/conda/envs/cubeenv/Library/share/gdal"
os.environ['GDAL_DATA']="C:/Users/mini/.conda/envs/odc_env/Library/share/gdal"

import datacube
import rioxarray as rio
import random

def getProtocolURL():
    if os.environ['SERVER_PORT_SECURE']=="1":
        return "https://"
    return "http://"

def getRootURL():
    url=getProtocolURL()+os.environ['SERVER_NAME']
    if (os.environ['SERVER_PORT_SECURE']=="1" and os.environ['SERVER_PORT']!="443") or (os.environ['SERVER_PORT_SECURE']=="0" and os.environ['SERVER_PORT']!="80"):
        url+=":"+os.environ['SERVER_PORT']
    url+=os.environ['SCRIPT_NAME']
    return url

def getArgumentInsensitive(query_params, k, default):
    if k.lower() in query_params:
        return query_params[k.lower()][0]
    if k.upper() in query_params:
        return query_params[k.upper()][0]
    return default

#in this cases default should be an array
def getArgumentsInsensitive(query_params, k, default):
    response=default
    if k.lower() in query_params:
        response+=query_params[k.lower()]
    if k.upper() in query_params:
        response+=query_params[k.upper()]
    return response

def getFormatToRespond(query_params, allowedFormats):
    if "f" in query_params:
        if query_params["f"][0].lower()=="html":
            mediaTypes=["text/html"]
        elif query_params["f"][0].lower()=="json":
            mediaTypes=["application/json"]
        elif query_params["f"][0].lower()=="jpeg":
            mediaTypes=["image/jpeg"]
        elif query_params["f"][0].lower()=="png":
            mediaTypes=["image/png"]
        elif query_params["f"][0].lower()=="gif":
            mediaTypes=["image/gif"]
        elif query_params["f"][0].lower()=="tiff":
            mediaTypes=["image/tiff"]
        elif query_params["f"][0].lower()=="img":
            mediaTypes=["application/x-img"]
    else:
        accept = os.environ['HTTP_ACCEPT']
        mts=accept.split(",")
        mediaTypes=[]
        for mt in mts:
            mediaTypes.append(mt.split(";")[0])
    for mt in mediaTypes:
        if mt in allowedFormats:
            return mt
    if "*/*" in mediaTypes:
        return allowedFormats[0]
    return ""

# supports &SUBSET=E(669960,729960)&SUBSET=N(4990200,5015220) NOTE the comma as a coordinate separator
def getBBoxFromSubsetWCS(subsets):
    e=""
    n=""
    for item in subsets:
        start_index = item.find("(")
        if start_index == -1:
            sys.stdout.write('Content-type: text/html\r\n\r\n<html><body>Missing \'(\' in subset='+ item +'</body></html>\r\n')
            sys.exit(0)
        end_index = item.find(")", start_index+1)
        if end_index == -1:
            sys.stdout.write('Content-type: text/html\r\n\r\n<html><body>Missing \')\' in subset='+ item +'</body></html>\r\n')
            sys.exit(0)
        k=item[0:start_index]
        v=item[start_index+1:end_index]
        if k=='E' or k=='e':  #"&SUBSET=E(669960,729960)"
            e=v.split(",", 1)
        elif k=='N' or k=='n':  #"&SUBSET=N(4990200,5015220)"
            n=v.split(",", 1)
    if e=="" or n=="":
        return []
    return [float(e[0]),float(n[0]),float(e[1]),float(n[1])]

# supports both
#   &subset=E(669960:729960)&subset=N(4990200:5015220)  NOTE the colon as coordinate separator, different from WCS.
#   &subset=E(669960:729960),N(4990200:5015220)
def getBBoxFromSubsetAPI(subsets):
    e=""
    n=""
    for subset in subsets:
        items=subset.split(",")
        for item in items:
            start_index = item.find("(")
            if start_index == -1:
                sys.stdout.write('Content-type: text/html\r\n\r\n<html><body>Missing \'(\' in subset='+ item +'</body></html>\r\n')
                sys.exit(0)
            end_index = item.find(")", start_index+1)
            if end_index == -1:
                sys.stdout.write('Content-type: text/html\r\n\r\n<html><body>Missing \')\' in subset='+ item +'</body></html>\r\n')
                sys.exit(0)
            k=item[0:start_index]
            v=item[start_index+1:end_index]
            if k=='E' or k=='e':  #"E(669960:729960)"
                e=v.split(":", 1)
            elif k=='N' or k=='n':  #"N(4990200:5015220)"
                n=v.split(":", 1)
    if e=="" or n=="":
        return []
    return [float(e[0]),float(n[0]),float(e[1]),float(n[1])]

#supports #"&SUBSET=ansi(\"2021-04-09\")"
def getTimeFromSubsetWCS(subsets):
    for item in subsets:
        start_index = item.find("(")
        if start_index == -1:
            sys.stdout.write('Content-type: text/html\r\n\r\n<html><body>Missing \'(\' in subset='+ item +'</body></html>\r\n')
            sys.exit(0)
        end_index = item.find(")", start_index+1)
        if end_index == -1:
            sys.stdout.write('Content-type: text/html\r\n\r\n<html><body>Missing \')\' in subset='+ item +'</body></html>\r\n')
            sys.exit(0)
        k=item[0:start_index]
        v=item[start_index+1:end_index]
        if k=='ansi':  #"&SUBSET=ansi(\"2021-04-09\")"
            return v.strip('\"')    
    return ""

# supports both
#   &subset=time("2021-04-09")&E(669960:729960)&subset=N(4990200:5015220)  NOTE the colon as coordinate separator, different from WCS.
#   &subset=time("2021-04-09"),E(669960:729960),N(4990200:5015220)    
def getTimeFromSubsetAPI(subsets):
    for subset in subsets:
        items=subset.split(",")
        for item in items:
            start_index = item.find("(")
            if start_index == -1:
                sys.stdout.write('Content-type: text/html\r\n\r\n<html><body>Missing \'(\' in subset='+ item +'</body></html>\r\n')
                sys.exit(0)
            end_index = item.find(")", start_index+1)
            if end_index == -1:
                sys.stdout.write('Content-type: text/html\r\n\r\n<html><body>Missing \')\' in subset='+ item +'</body></html>\r\n')
                sys.exit(0)
            k=item[0:start_index]
            v=item[start_index+1:end_index]
            if k=='time':  #"&SUBSET=ansi(\"2021-04-09\")"
                return v.strip('\"')    
    return ""

def getBBoxFromBBox(bbox):
    str_bbox = bbox.split(",")
    if len(str_bbox)<4:
        sys.stdout.write('Content-type: text/html\r\n\r\n<html><body>BBOX should have at least 4 numbers separated by coma.</body></html>\r\n')
        sys.exit(0)
    return [float(str_bbox[0]),float(str_bbox[1]),float(str_bbox[2]),float(str_bbox[3])]

# use res=0 to generate "unknown resolution".    
def getResolutionFromScaleFactor(scalefactor, res):    
    if scalefactor == "":
        return {"x": res, "y": res}
    else:
        return {"x": res*float(scalefactor), "y": res*float(scalefactor)}

def getResolutionFromWidthHeight(w, h, bbox):
    if w=="" or h=="":
        return None
    width  = int(w)
    height = int(h)
    return {"x":(bbox[2]-bbox[0])/width, "y": (bbox[3]-bbox[1])/height}
    
def getEPSGOldFormat(crs):
    c=crs.strip()
    if c[0]=="[":
        if c[-1]!="]":
            sys.stdout.write('Content-type: text/html\r\n\r\n<html><body>Missing \']\' in crs "'+ crs +'"</body></html>\r\n')
            sys.exit(0)
        return c[1:-1]
    if c.startswith("http"):
        return "EPSG:"+c.split("/")[-1]
    return c
    
def getDriverFromMediaType(mimetype):
    if mimetype=="image/jpeg":
        return 'JPEG'
    if mimetype=="image/png":
        return 'PNG'
    if mimetype=="image/gif":
        return 'GIF'
    if mimetype=="image/tiff":
        return 'GTiff'
    if mimetype=="application/x-img":
        return 'ENVI'
    return ""

#It also tranforms nodata values into the whitest color    
def scaleDataSetTo256Colors(ds_res):
    #In the future consider using the histogram to remove some extreme values that may distort the rescale.
    #import numpy as np
    #stacked = dst_cl.stack(stacked=[...])  #flatening the array https://stackoverflow.com/questions/73395873/how-to-turn-a-3-d-xarray-dataset-into-a-1d-dataset
    #stacked["Forest"]
    #counts, bin_edges = np.histogram(stacked["Forest"], bins=256)  # performing the histogram https://stackoverflow.com/questions/58974986/python-3-histogram-how-to-get-counts-and-bins-with-plt-hist-but-without-disp

    mi=ds_res.min().item()
    mx=ds_res.max().item()
        
    ds_res = ds_res.where(~ds_res.isnull(), other=mx+(mx-mi)/256)  #nodata goes above the maximum (white color)
    
    if mx==mi:
        a=1
    else:
        mx=mx+(mx-mi)*2/256  #If I do not do that, the whitest color becomes black
        a=256.0/(mx-mi)

    return ((ds_res-mi)*a).astype('uint8')  #range adapted to a maximum of 256     

def getBandFromDataCube(dc, layers, bbox, bboxCrs, crs, res, time, band, mimetype):
    #print(layers)
    #print(str(bbox[0]) +" "+ str(bbox[1]))
    #print(str(bbox[2]) +" "+ str(bbox[3]))
    #print (time)
    #print(-(bbox[2]-bbox[0])/width)
    #print((bbox[3]-bbox[1])/height)
    #print (band)
    #print (crs)
    #print (res)
    
    driver=getDriverFromMediaType(mimetype)
    if driver=="":
        sys.stdout.write('Content-type: text/html\r\n\r\n<html><body>Format not supported. Supported formats are image/jpeg, image/png, image/gif, image/tiff and application/x-img</body></html>\r\n')
        sys.exit(0)

    if (res["x"] == 0 or res["y"] == 0) and crs=="":
        ds = dc.load(product=layers,
                 x=(bbox[0],bbox[2]),
                 y=(bbox[1],bbox[3]), 
                 time=(time),
                 measurements=[band],
                 group_by='solar_day',
                 crs=bboxCrs
        )
    else:
        ds = dc.load(product=layers,
                 x=(bbox[0]+res["x"],bbox[2]),
                 y=(bbox[1],bbox[3]-res["y"]), 
                 time=(time), 
                 measurements=[band],
                 group_by='solar_day',
                 output_crs=crs, 
                 crs=bboxCrs, 
                 resolution=(-res["x"],res["y"])
        )

    #print(ds)
    if driver=='GTiff' or driver=='ENVI':
        return ds[band]
    if list(ds.data_vars)[0]=="slc":
        return ds.astype('uint8')[band]

    ds_res=ds[band]
    p=dc.index.products.get_by_name(layers)
    if p:
        for m in p.definition["measurements"]:
            if band==m["name"]:
                if "nodata" in m:
                    ds_res=ds_res.where(ds_res!=m["nodata"])
                break
    
    return scaleDataSetTo256Colors(ds_res)

evaluateSliceInDataCubeVariables={}  #The only way  have found to communicate to the Sclice function. returnResultExpressionFromDataCube() populates it and evaluateSliceInDataCube uses it

def addQuotesInInternalFunction(expression, n):
    nparenthesis=0;
    resExp="Slice("
    i=len("Slice(")
    while expression[i]==" ":
        i+=1
    if expression[i]=="'" or expression[i]=='"':
    	return {"error": True}
    else:
    	for s in range(n):
        	resExp+='\\'	
    	resExp+='"'    
    while i<len(expression):
        if expression[i:].startswith("Slice("):
            res=addQuotesInInternalFunction(expression[i:], n+1)
            if res["error"]:
                return {"error": True}
            resExp+=res["resExp"]
            i+=res["i"]
            nparenthesis+=1
        if expression[i]=="(":
            nparenthesis+=1
        elif expression[i]==")":
            nparenthesis-=1
        elif nparenthesis==0:
            if expression[i]==',':
                for s in range(n):
                    resExp+='\\'
                resExp+='"'
                return {"resExp": resExp, "i": i, "error": False}
        elif nparenthesis==-1:
            return {"resExp": resExp, "i": i, "error": False}
        resExp+=expression[i]
        i+=1
    return {"resExp": resExp, "i": i, "error": False}

def addQuotesToInternalExpressions(expression):
    resExp=""
    i=0
    while i<len(expression):
        if expression[i:].startswith("Slice("):
            res=addQuotesInInternalFunction(expression[i:], 0)
            if res["error"]:
        	    return expression
            resExp+=res["resExp"]
            i+=res["i"]
        else:
        	resExp+=expression[i]
        	i+=1
    return resExp

def returnResultExpressionFromDataCube(dc, layers, bbox, bboxCrs, crs, res, time, expression, filterWhere):
    
    if (res["x"] == 0 or res["y"] == 0) and crs=="":
        ds = dc.load(product=layers,
                 x=(bbox[0],bbox[2]),
                 y=(bbox[1],bbox[3]), 
                 time=(time),
                 group_by='solar_day',
                 crs=bboxCrs
        )
    else:
        ds = dc.load(product=layers,
                 x=(bbox[0]+res["x"],bbox[2]),
                 y=(bbox[1],bbox[3]-res["y"]), 
                 time=(time), 
                 group_by='solar_day',
                 output_crs=crs, 
                 crs=bboxCrs, 
                 resolution=(-res["x"],res["y"])
        )
                
    
    ds=ds.isel(time=0, drop=True)  #reduce the number of dimensions to 2.

    bandDict={}
    
    p=dc.index.products.get_by_name(layers)
    for m in p.definition["measurements"]:
        if "nodata" in m:
            bandDict[m["name"]]=ds[m["name"]].where(ds[m["name"]]!=m["nodata"]).astype('float')
        else:
            bandDict[m["name"]]=ds[m["name"]].astype('float')
    
    # for security reasons: https://realpython.com/python-eval-function/
    bandDict["__builtins__"]: {}
    
    if expression.find("Slice(")!=-1:
        expression=addQuotesToInternalExpressions(expression)
        bandDict["Slice"]=evaluateSliceInDataCube
        evaluateSliceInDataCubeVariables["dc"]=dc
        evaluateSliceInDataCubeVariables["layers"]=layers
        evaluateSliceInDataCubeVariables["bbox"]=bbox
        evaluateSliceInDataCubeVariables["bboxCrs"]=bboxCrs
        evaluateSliceInDataCubeVariables["crs"]=crs
        evaluateSliceInDataCubeVariables["res"]=res
        #evaluateSliceInDataCubeVariables["time"]=time
        evaluateSliceInDataCubeVariables["filterWhere"]=filterWhere

    ds_res=eval(expression, bandDict, {})
    #if time=="2018-04-28":
    #    print(ds_res)
    #    sys.exit(0)
    

    if filterWhere!="":
        bandDict["ds_res"]=ds_res
        ds_res=eval("ds_res.where("+filterWhere+")", bandDict, {})
            
    return ds_res


def evaluateSliceInDataCube(expression, dimensions, dimValues):
    if dimensions and dimValues and len(dimensions)!=len(dimValues):
        sys.stdout.write('Content-type: text/html\r\n\r\n<html><body>Slide "dimensions" and "dimValues" shuold be 2 arrays of the same length.</body></html>\r\n')
        sys.exit(0)

    if dimensions and len(dimensions)!=1 and dimensions[0]!="time":
        sys.stdout.write('Content-type: text/html\r\n\r\n<html><body>Slide "dimensions" paramenter not supported. Only suported [\'time\'].</body></html>\r\n')
        sys.exit(0)

    return returnResultExpressionFromDataCube(evaluateSliceInDataCubeVariables["dc"], evaluateSliceInDataCubeVariables["layers"], evaluateSliceInDataCubeVariables["bbox"], evaluateSliceInDataCubeVariables["bboxCrs"], evaluateSliceInDataCubeVariables["crs"], evaluateSliceInDataCubeVariables["res"], dimValues[0], expression, evaluateSliceInDataCubeVariables["filterWhere"])


def getExpressionFromDataCube(dc, layers, bbox, bboxCrs, crs, res, time, expression, filterWhere, mimetype):
    #print(layers)
    #print(str(bbox[0]) +" "+ str(bbox[1]))
    #print(str(bbox[2]) +" "+ str(bbox[3]))
    #print (time)
    #print(-(bbox[2]-bbox[0])/width)
    #print((bbox[3]-bbox[1])/height)
    #print (band)
    #print (crs)
    #print (res)
    
    driver=getDriverFromMediaType(mimetype)
    if driver=="":
        sys.stdout.write('Content-type: text/html\r\n\r\n<html><body>Format not supported. Supported formats are image/jpeg, image/png, image/gif, image/tiff and application/x-img</body></html>\r\n')
        sys.exit(0)

    ds_res=returnResultExpressionFromDataCube(dc, layers, bbox, bboxCrs, crs, res, time, expression, filterWhere)
    
    if driver=='GTiff' or driver=='ENVI':
        return ds_res

    return scaleDataSetTo256Colors(ds_res)
     

def sendImageResult(ds_band, crs, mimetype):
    driver=getDriverFromMediaType(mimetype)
    if driver=="":
        sys.stdout.write('Content-type: text/html\r\n\r\n<html><body>Format not supported. Supported formats are image/jpeg, image/png, image/gif, image/tiff and application/x-img</body></html>\r\n')
        sys.exit(0)

    random.seed()
     
    filename=os.path.join('c:\\temp','temp'+str(random.randint(0,1000000))+'.img')
    #print(filename)

    ds_band.rio.to_raster(filename, driver=driver)  #num_threads='all_cpus', tiled=True, 

    file = open(filename,"rb")
    sys.stdout.buffer.write( b"Content-type: " + bytes(mimetype, 'ascii')+ b"\r\nContent-crs: [" +  bytes(crs, 'ascii') + b"]\r\n\r\n" + file.read() )

    file.close()
    os.remove(filename)

def getCoverageAndSendResult(dc, layers, bbox, crs, res, time, band, mimetype):
    sendImageResult(getBandFromDataCube(dc, layers, bbox, crs, crs, res, time, band, mimetype), crs, mimetype)
    
def getStartHTMLPage(title):
    return '<!DOCTYPE HTML>\r\n<html>\r\n<head>\r\n<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">\r\n<title>'+title+'</title>\r\n</head>\r\n<body>\r\n'
def getEndHTMLPage():
    return '</body>\r\n</html>\r\n'
    
def startOkResponse(formatToRespond):
    sys.stdout.write("Content-type: "+formatToRespond+"\r\nAccess-Control-Allow-Origin: *\r\n\r\n")
    
def getFilterODCFormat(filterWhere):
    s=filterWhere.replace("(", " (").replace(")", ") ").replace("  ", " ").replace(" and ", " & ").replace(" AND ", " & ").replace(" or ", " | ").replace(" OR ", " | ").replace(" not ", " ~ ")
    if len(s)<3:
        return s
    s2=s[0]
    i=1
    while i < len(s)-1:
        if s[i-1]!='=' and s[i-1]!='!' and s[i]=='=' and s[i+1]!='=':  #replaces a "=" by "=="
            s2+="=="
        elif s[i]=='<' and s[i+1]=='>':  #replaces a "<>" by "!="
            s2+="!="
            i+=1
        else:
            s2+=s[i]
        i+=1
    return s2+s[i]
    
def getJSONProduct(p):
    return{
        "id": p["name"], 
        "title": p["description"], 
        "links": [
            {
                "rel" : "self",
                "type" : "application/json",
                "title" : "Information about the data (as JSON)",
                "href" : getRootURL()+"/collections/" + p["name"] + "?f=json"
            },
            {
                "rel" : "alternate",
                "type" : "text/html",
                "title" : "Information about the data (as HTML)",
                "href" : getRootURL()+"/collections/" + p["name"] + "?f=html"
            },
            {
                "rel" : "http://www.opengis.net/def/rel/ogc/1.0/schema",
                "type" : "application/json",
                "title" : "Schema (as JSON)",
                "href" : getRootURL()+"/collections/" + p["name"] + "/schema?f=json"
            },
            {
                "rel" : "http://www.opengis.net/def/rel/ogc/1.0/schema",
                "type" : "text/html",
                "title" : "Schema (as HTML)",
                "href" : getRootURL()+"/collections/" + p["name"] + "/schema?f=html"
            },
            {
                "rel" : "http://www.opengis.net/def/rel/ogc/1.0/queryables",
                "type" : "application/json",
                "title" : "Queryables (as JSON)",
                "href" : getRootURL()+"/collections/" + p["name"] + "/queryables?f=json"
            },
            {
                "rel" : "http://www.opengis.net/def/rel/ogc/1.0/queryables",
                "type" : "text/html",
                "title" : "Queryables (as HTML)",
                "href" : getRootURL()+"/collections/" + p["name"] + "/queryables?f=html"
            },
            {
                "rel" : "http://www.opengis.net/def/rel/ogc/1.0/coverage",
                "type" : "image/png",
                "title" : "Coverage (as PNG)",
                "href" : getRootURL()+"/collections/" + p["name"] + "/coverage?f=png"
            },
            {
                "rel" : "http://www.opengis.net/def/rel/ogc/1.0/coverage",
                "type" : "image/tiff; application=geotiff",
                "title" : "Coverage (as GeoTIFF)",
                "href" : getRootURL()+"/collections/" + p["name"] + "/coverage?f=tif"
            },
            {
                "rel" : "http://www.opengis.net/def/rel/ogc/1.0/map",
                "type" : "image/png",
                "title" : "Default map (as PNG)",
                "href" : getRootURL()+"/collections/" + p["name"] + "/map.png"
            },
            {
                "rel" : "http://www.opengis.net/def/rel/ogc/1.0/map",
                "type" : "image/jpeg",
                "title" : "Default map (as JPG)",
                "href" : getRootURL()+"/collections/" + p["name"] + "/map.jpg"
            }
        ]
    }

def ogcpi(path_param, query_params):
    path_params=path_param.split("/");
    if path_param=="":
        #landing page: #https://www.datacube.cat/cgi-bin/mmdc.py
        allowedFormats=["text/html", "application/json"]
        formatToRespond=getFormatToRespond(query_params, allowedFormats)
        landingPageContent={
                "title" : "Open Data Cube (ODC)",
                "links" : [
                    {
                        "href": getRootURL()+"?f=json",
                        "rel": "self",
                        "type": "application/json",
                        "title": "This document in JSON format"
                    },
                    {
                        "href": getRootURL()+"?f=html",
                        "rel": "alternate",
                        "type": "text/html",
                        "title": "This document in HTML format"
                    },
                    {
                        "href": getRootURL()+"/api?f=json",
                        "rel": "service-desc",
                        "type": "application/vnd.oai.openapi+json;version=3.0",
                        "title": "The API definition in OpenAPI 3.0 in JSON format"
                    },
                    {
                        "href": getRootURL()+"/api?f=html",
                        "rel": "service-doc",
                        "type": "text/html",
                        "title": "The API documentation in HTML format"
                    },
                    {
                        "href": getRootURL()+"/conformance?f=json",
                        "rel": "http://www.opengis.net/def/rel/ogc/1.0/conformance",
                        "type": "application/json",
                        "title": "OGC API conformance classes implemented by this service in JSON format"
                    },
                    {
                        "href": getRootURL()+"/conformance?f=html",
                        "rel": "http://www.opengis.net/def/rel/ogc/1.0/conformance",
                        "type": "text/html",
                        "title": "OGC API conformance classes implemented by this service in HTML format"
                    },
                    {
                        "href": getRootURL()+"/collections?f=json",
                        "rel": "http://www.opengis.net/def/rel/ogc/1.0/data",
                        "type": "application/json",
                        "title": "Information about the collections provided by this service in JSON format"
                    },
                    {
                        "href": getRootURL()+"/collections?f=html",
                        "rel": "http://www.opengis.net/def/rel/ogc/1.0/data",
                        "type": "text/html",
                        "title": "Information about the collections provided by this service in HTML format"
                    }
                ]
            }
        if formatToRespond=="text/html":
            startOkResponse(formatToRespond)
            sys.stdout.write(getStartHTMLPage(landingPageContent["title"]))
            sys.stdout.write('<h1>'+landingPageContent["title"]+'</h1>\r\n')
            sys.stdout.write('<b>Links to:</b>\r\n')
            sys.stdout.write('<ul>\r\n')
            for lnk in landingPageContent["links"]:
                sys.stdout.write('<li><a href="'+lnk["href"]+'">'+lnk["title"]+'</a>\r\n')
            sys.stdout.write('</ul>\r\n')
            sys.stdout.write(getEndHTMLPage())
        elif formatToRespond=="application/json":
            startOkResponse(formatToRespond)
            sys.stdout.write(json.dumps(landingPageContent))
        else:
            sys.stdout.write('Status: 404\r\nContent-type: text/html\r\nAccess-Control-Allow-Origin: *\r\n\r\n<html><body>Landing page not supported format. Only allowed"+json.dumps(allowedFormats)+"</body></html>\r\n')            
    elif path_param=="conformance":
        #conformance page: #https://www.datacube.cat/cgi-bin/mmdc.py/conformance
        allowedFormats=["text/html", "application/json"]
        formatToRespond=getFormatToRespond(query_params, allowedFormats)
        conformancePageContent={"conformsTo" : [
                "http://www.opengis.net/spec/ogcapi-common-1/1.0/conf/core",
                "http://www.opengis.net/spec/ogcapi-common-1/1.0/conf/landing-page",
                "http://www.opengis.net/spec/ogcapi-common-1/1.0/conf/html",
                "http://www.opengis.net/spec/ogcapi-common-1/1.0/conf/json",
                "http://www.opengis.net/spec/ogcapi-common-1/1.0/conf/oas30",
                "http://www.opengis.net/spec/ogcapi-common-2/1.0/conf/collections",
                "http://www.opengis.net/spec/ogcapi-common-2/1.0/conf/json",
                "http://www.opengis.net/spec/ogcapi-common-2/1.0/conf/html",
                "http://www.opengis.net/spec/ogcapi-maps-1/1.0/conf/core",
                "http://www.opengis.net/spec/ogcapi-maps-1/1.0/conf/tilesets",
                "http://www.opengis.net/spec/ogcapi-maps-1/1.0/conf/background",
                "http://www.opengis.net/spec/ogcapi-maps-1/1.0/conf/scaling",
                "http://www.opengis.net/spec/ogcapi-maps-1/1.0/conf/display-resolution",
                "http://www.opengis.net/spec/ogcapi-maps-1/1.0/conf/spatial-subsetting",
                "http://www.opengis.net/spec/ogcapi-maps-1/1.0/conf/datetime",
                "http://www.opengis.net/spec/ogcapi-maps-1/1.0/conf/general-subsetting",
                "http://www.opengis.net/spec/ogcapi-maps-1/1.0/conf/crs",
                "http://www.opengis.net/spec/ogcapi-maps-1/1.0/conf/collection-map",
                "http://www.opengis.net/spec/ogcapi-maps-1/1.0/conf/styled-map",
                "http://www.opengis.net/spec/ogcapi-maps-1/1.0/conf/png",
                "http://www.opengis.net/spec/ogcapi-maps-1/1.0/conf/jpeg",
                "http://www.opengis.net/spec/ogcapi-maps-1/1.0/conf/html",
                "http://www.opengis.net/spec/ogcapi-maps-1/1.0/conf/oas30",
                "http://www.opengis.net/spec/ogcapi-styles-1/0.0/conf/core"
            ]
        }
        if formatToRespond=="text/html":
            startOkResponse(formatToRespond)
            sys.stdout.write(getStartHTMLPage("Supported conformance classes"))
            sys.stdout.write('<h1>Supported conformance classes</h1>\r\n')
            sys.stdout.write('<ul>\r\n')
            for lnk in conformancePageContent["conformsTo"]:
                sys.stdout.write('<li><a href="'+lnk+'">'+lnk+'</a>\r\n')
            sys.stdout.write('</ul>\r\n')
            sys.stdout.write(getEndHTMLPage())
        elif formatToRespond=="application/json":
            startOkResponse(formatToRespond)
            sys.stdout.write(json.dumps(conformancePageContent))
        else:
            sys.stdout.write('Status: 404\r\nContent-type: text/html\r\nAccess-Control-Allow-Origin: *\r\n\r\n<html><body>Conformance page not supported format. Only allowed"+json.dumps(allowedFormats)+"</body></html>\r\n')
    elif path_param=="collections":
        #collections page: #https://www.datacube.cat/cgi-bin/mmdc.py/collections
        allowedFormats=["text/html", "application/json"]
        formatToRespond=getFormatToRespond(query_params, allowedFormats)
        collectionsPageContent={
            "links": [
                {
                  "rel": "self",
                  "type": "application/json",
                  "title": "The JSON representation of the list of all data collections for this dataset",
                  "href": getRootURL()+"/collections?f=json"
                },
                {
                  "rel": "alternate",
                  "type": "text/html",
                  "title": "The HTML representation of the list of all data collections for this dataset",
                  "href": getRootURL()+"/ogcapi/collections?f=html"
                }
            ],
            "collections": []
        }
        dc = datacube.Datacube(app='datacube-cgi')
        products=dc.list_products(with_pandas=False)
        for p in products:
            collectionsPageContent["collections"].append(getJSONProduct(p))
        
        if formatToRespond=="text/html":
            startOkResponse(formatToRespond)
            sys.stdout.write(getStartHTMLPage("Collections"))
            sys.stdout.write('<h1>Collections</h1>\r\n')
            sys.stdout.write('<h2>Links to:</h2>\r\n')
            sys.stdout.write('<ul>\r\n')
            for lnk in collectionsPageContent["links"]:
                sys.stdout.write('<li><a href="'+lnk["href"]+'">'+lnk["title"]+'</a>\r\n')
            sys.stdout.write('</ul>\r\n')
            sys.stdout.write('<h2>List of collections:</h2>\r\n')
            for c in collectionsPageContent["collections"]:
                sys.stdout.write('<h3>Collection \'' + c["id"] + '\'</h3>\r\n')
                sys.stdout.write(c["title"] + '\r\n')
                sys.stdout.write('<ul>\r\n')
                for lnk in c["links"]:
                    sys.stdout.write('<li><a href="'+lnk["href"]+'">'+lnk["title"]+'</a>\r\n')
                sys.stdout.write('</ul>\r\n')
            sys.stdout.write(getEndHTMLPage())
        elif formatToRespond=="application/json":
            startOkResponse(formatToRespond)
            sys.stdout.write(json.dumps(collectionsPageContent))
        else:
            sys.stdout.write('Status: 404\r\nContent-type: text/html\r\nAccess-Control-Allow-Origin: *\r\n\r\n<html><body>Collections page format not supported. Only allowed"+json.dumps(allowedFormats)+"</body></html>\r\n')
    elif len(path_params)==2 and path_params[0]=="collections":
        #collection page: https://www.datacube.cat/cgi-bin/mmdc.py/colletions/s2_level2a_utm31_10
        allowedFormats=["text/html", "application/json"]
        formatToRespond=getFormatToRespond(query_params, allowedFormats)
        dc = datacube.Datacube(app='datacube-cgi')
        p=dc.index.products.get_by_name(path_params[1])
        if p:
            collectionPageContent=getJSONProduct(p.definition)        
            if formatToRespond=="text/html":
                startOkResponse(formatToRespond)
                sys.stdout.write(getStartHTMLPage(collectionPageContent["title"]))
                sys.stdout.write('<h1>Description of collection \''+ collectionPageContent["id"]+ '\'</h1>\r\n')
                sys.stdout.write(collectionPageContent["title"] + '\r\n')
                sys.stdout.write('<ul>\r\n')
                for lnk in collectionPageContent["links"]:
                    sys.stdout.write('<li><a href="'+lnk["href"]+'">'+lnk["title"]+'</a>\r\n')
                sys.stdout.write('</ul>\r\n')
                sys.stdout.write(getEndHTMLPage())
            elif formatToRespond=="application/json":
                startOkResponse(formatToRespond)
                sys.stdout.write(json.dumps(collectionPageContent))
            else:
                sys.stdout.write('Status: 404\r\nContent-type: text/html\r\nAccess-Control-Allow-Origin: *\r\n\r\n<html><body>Collection page format not supported. Only allowed"+json.dumps(allowedFormats)+"</body></html>\r\n')
        else:
            sys.stdout.write('Status: 404\r\nContent-type: text/html\r\nAccess-Control-Allow-Origin: *\r\n\r\n<html><body>Collection not found (' + path_params[1] + ')</body></html>\r\n')
    elif len(path_params)==3 and path_params[0]=="collections" and path_params[2]=="schema":
        #schema page: https://www.datacube.cat/cgi-bin/mmdc.py/colletions/s2_level2a_utm31_10/schema
        allowedFormats=["text/html", "application/json"]
        formatToRespond=getFormatToRespond(query_params, allowedFormats)
        schemaPageContent={
           "$schema" : "https://json-schema.org/draft/2020-12/schema",
           "$id" : "https://maps.gnosis.earth/ogcapi/collections/"+path_params[1]+"/schema",
           "title" : path_params[1],
           "type" : "object",
           "properties" : { 
           }
        }
        dc = datacube.Datacube(app='datacube-cgi')
        p=dc.index.products.get_by_name(path_params[1])
        if p:
            i=1
            needNodata=False
            for m in p.definition["measurements"]:
                title=m["name"]
                if "aliases" in m:
                    for a in m["aliases"]:
                        title+=", "+a
                title+=" ("+m["dtype"]+")"
                schemaPageContent["properties"][m["name"]]={
                    "title" : title,
                    "type" : "number",
                    "x-ogc-propertySeq" : i
                }
                if "nodata" in m:
                    schemaPageContent["properties"][m["name"]]["x-ogc-nilValues"]=[m["nodata"]]
                    needNodata=True
                i=i+1
            if formatToRespond=="text/html":
                startOkResponse(formatToRespond)
                sys.stdout.write(getStartHTMLPage(schemaPageContent["title"]))
                sys.stdout.write('<h1>Schema of collection \''+ schemaPageContent["title"]+ '\'</h1>\r\n')
                sys.stdout.write('<ul><li>View <a href="?f=json"><b>JSON</b></a> representation<li>View a <a href="?f=html"><b>HTML</b></a> representation</i></ul>\r\n')
                sys.stdout.write('<table border="1"><tr><th><b>Property</b></th><th><b>Title</b></th><th><b>Type</b></th>')
                if needNodata:
                    sys.stdout.write('<th><b>Nil values</b></th>')
                sys.stdout.write('<th><b>Sequence</b></th></tr>\r\n')
                for m in schemaPageContent["properties"]:
                    v=schemaPageContent["properties"][m]
                    sys.stdout.write('<tr><td><b>'+m+'</b></td><td>'+v["title"]+'</td><td>'+v["type"]+'</td>')
                    if needNodata:
                        sys.stdout.write('<td>');
                    if "x-ogc-propertySeq" in v and len(str(v["x-ogc-propertySeq"]))>0:
                        sys.stdout.write(str(v["x-ogc-nilValues"]))
                    if needNodata:
                        sys.stdout.write('</td>');
                    sys.stdout.write('<td>'+str(v["x-ogc-propertySeq"])+'</td></tr>\r\n')

                sys.stdout.write('</table>\r\n')
                sys.stdout.write(getEndHTMLPage())
            elif formatToRespond=="application/json":
                startOkResponse(formatToRespond)
                sys.stdout.write(json.dumps(schemaPageContent))
            else:
                sys.stdout.write('Status: 404\r\nContent-type: text/html\r\nAccess-Control-Allow-Origin: *\r\n\r\n<html><body>Collection page format not supported. Only allowed"+json.dumps(allowedFormats)+"</body></html>\r\n')
        else:
            sys.stdout.write('Status: 404\r\nContent-type: text/html\r\nAccess-Control-Allow-Origin: *\r\n\r\n<html><body>Collection not found (' + path_params[1] + ')</body></html>\r\n')
    elif len(path_params)==3 and path_params[0]=="collections" and path_params[2]=="coverage":
        #coverage response: 
        #https://www.datacube.cat/cgi-bin/mmdc.py/collections/s2_level2a_utm31_10/coverage?subset=E(422401.47:437401.47)&subset=N(4582942.45:4590742.45)&properties=red&subset=time("2018-01-01")&f=jpeg
        #http://localhost/cgi-bin/mmdc.py/collections/s2_level2a_granule/coverage?subset=E(422401.47:437401.47),N(4582942.45:4590742.45),time(%222018-03-29%22)&properties=B04_10m&scale-factor=3&f=jpeg
        #http://localhost/cgi-bin/mmdc.py/collections/s2_level2a_granule/coverage?subset=E(422401.47:437401.47),N(4582942.45:4590742.45),time(%222018-03-29%22)&properties=(B08_10m-B04_10m)/(B08_10m%2BB04_10m)
        #http://localhost/cgi-bin/mmdc.py/collections/s2_level2a_granule/coverage?subset=E(422401.47:437401.47),N(4582942.45:4590742.45),time(%222018-03-29%22)&subset-crs=[EPSG:32631]&crs=[EPSG:32631]&properties=(B08_10m-B04_10m)/(B08_10m%2BB04_10m)
        #http://localhost/cgi-bin/mmdc.py/collections/s2_level2a_granule/coverage?subset=E(422401.47:437401.47),N(4582942.45:4590742.45),time(%222018-04-28%22)&subset-crs=[EPSG:32631]&crs=[EPSG:32631]&properties=(B08_10m-B04_10m)/(B08_10m%2BB04_10m)&filter=(SCL_20m=4)%20or%20(SCL_20m=5)%20or%20(SCL_20m=6)
        #http://localhost/cgi-bin/mmdc.py/collections/s2_level2a_granule/coverage?subset=E(422401.47:437401.47),N(4582942.45:4590742.45),time(%222018-04-28%22)&subset-crs=[EPSG:32631]&crs=[EPSG:32631]&properties=(B08_10m-B04_10m)/(B08_10m%2BB04_10m)-Slice((B08_10m-B04_10m)/(B08_10m%2BB04_10m),['time'],['2018-04-18'])&filter=(SCL_20m=4)or(SCL_20m=5)or(SCL_20m=6)
        #http://localhost/cgi-bin/mmdc.py/collections/TerrestrialConnectivityIndex/coverage?subset=E(390401.47:437401.47),N(4582942.45:4612942.45),time("2017-01-01")&subset-crs=[EPSG:32631]&crs=[EPSG:32631]&properties=Forest&filter=Forest<>-9999
        #http://localhost/cgi-bin/mmdc.py/collections/TerrestrialConnectivityIndex/coverage?subset=E(390401.47:437401.47),N(4582942.45:4612942.45),time("2017-01-01")&subset-crs=[EPSG:32631]&crs=[EPSG:32631]&properties=Forest
        #http://localhost/cgi-bin/mmdc.py/collections/TerrestrialConnectivityIndex/coverage?subset=E(390401.47:437401.47),N(4582942.45:4612942.45),time("2017-01-01")&subset-crs=[EPSG:32631]&crs=[EPSG:32631]&properties=Forest-Slice(Forest,['time'],['2012-01-01'])
        #http://localhost/cgi-bin/mmdc.py/collections/TerrestrialConnectivityIndex/coverage?subset=E(260000:528000),N(4488000:4748000),time(%222017-01-01%22)&subset-crs=[EPSG:32631]&crs=[EPSG:32631]&properties=Forest
        #http://localhost/cgi-bin/mmdc.py/collections/TerrestrialConnectivityIndex/coverage?subset=E(260000:528000),N(4488000:4748000),time(%222017-01-01%22)&subset-crs=[EPSG:32631]&crs=[EPSG:32631]&properties=Forest-Slice(Forest,[%22time%22],[%222012-01-01%22])

        allowedFormats=["image/jpeg", "image/png", "image/gif", "image/tiff", "application/x-img"]
        formatToRespond=getFormatToRespond(query_params, allowedFormats)
        if formatToRespond=="":
            sys.stdout.write('Status: 404\r\nContent-type: text/html\r\nAccess-Control-Allow-Origin: *\r\n\r\n<html><body>Collection page format not supported. Only allowed"+json.dumps(allowedFormats)+"</body></html>\r\n')
            sys.exit(0)
        dc = datacube.Datacube(app='datacube-cgi')
        p=dc.index.products.get_by_name(path_params[1])
        if p:
            if "storage" in p.definition and "crs" in p.definition["storage"]:
                crsDef=p.definition["storage"]["crs"]
            else:
                crsDef="EPSG:32631"
            subsets=getArgumentsInsensitive(query_params, "subset", [])
            if len(subsets)==0:
                strBBox=getArgumentInsensitive(query_params, "bbox", "")
                if strBBox=="":
                    sys.stdout.write('Status: 404\r\nContent-type: text/html\r\nAccess-Control-Allow-Origin: *\r\n\r\n<html><body>Subset or bbox parameter not found.</body></html>\r\n')
                    sys.exit(0)
                getBBoxFromBBox(strBBox)
                bboxCrs=getEPSGOldFormat(getArgumentInsensitive(query_params, "bbox-crs", crsDef))
            else:
                bbox=getBBoxFromSubsetAPI(subsets)
                bboxCrs=getEPSGOldFormat(getArgumentInsensitive(query_params, "subset-crs", crsDef))
            if len(bbox)==0:
                sys.stdout.write('Status: 404\r\nContent-type: text/html\r\nAccess-Control-Allow-Origin: *\r\n\r\n<html><body>subset=E, subset=N or bbox parameter not found.</body></html>\r\n')
                sys.exit(0)
                
            time=getTimeFromSubsetAPI(subsets)
            if time=="":
                time=getArgumentInsensitive(query_params, "time", "")
            if time=="":
                sys.stdout.write('Status: 404\r\nContent-type: text/html\r\nAccess-Control-Allow-Origin: *\r\n\r\n<html><body>Subset=time or time parameter not found.</body></html>\r\n')
                sys.exit(0)

            res=getResolutionFromWidthHeight(getArgumentInsensitive(query_params, "width", ""), getArgumentInsensitive(query_params, "height", ""), bbox)
            if res==None:
                if "storage" in p.definition and "resolution" in p.definition["storage"] and "x" in p.definition["storage"]["resolution"]:
                    res=p.definition["storage"]["resolution"]["x"]
                else:
                    res=10

                res=getResolutionFromScaleFactor(getArgumentInsensitive(query_params, "scale-factor", ""), res)
                
            crs=getEPSGOldFormat(getArgumentInsensitive(query_params, "crs", crsDef))

            band=getArgumentInsensitive(query_params, "properties", "")
            if band == "":
                sys.stdout.write('Content-type:text/html\r\n\r\n<html><body>\'properties\' parameter is required</body></html>\r\n')
                sys.exit(0)

            filterWhere=getFilterODCFormat(getArgumentInsensitive(query_params, "filter", ""))
              
            ds_band=[]
            
            if filterWhere=="":
                for m in p.definition["measurements"]:
                    if band==m["name"]:
                        #Simple situation: one band and no filter
                        ds_band=getBandFromDataCube(dc, path_params[1], bbox, bboxCrs, crs, res, time, band, formatToRespond)
                    
            
            #(ds['B08_10m']-ds['B04_10m'])/(ds['B08_10m']+ds['B04_10m'])
            #properties=(B08_10m-B04_10m)/(B08_10m+B04_10m)
            if len(ds_band)==0:
                ds_band=getExpressionFromDataCube(dc, path_params[1], bbox, bboxCrs, crs, res, time, band, filterWhere, formatToRespond)
                #sys.stdout.write('Status: 404\r\nContent-type: text/html\r\nAccess-Control-Allow-Origin: *\r\n\r\n<html><body>Property not present in this coverage.</body></html>\r\n')
                #sys.exit(0)
            sendImageResult(ds_band, crs, formatToRespond)

        else:
            sys.stdout.write('Status: 404\r\nContent-type: text/html\r\nAccess-Control-Allow-Origin: *\r\n\r\n<html><body>Collection not found (' + path_params[1] + ')</body></html>\r\n')
    elif path_param=="api":
        #api page
        allowedFormats=["text/html", "application/json"]
        formatToRespond=getFormatToRespond(query_params, allowedFormats)
        ApiPageContent={
            "openapi" : "3.0.0",
            "info" : {
                "title" : "Open Data Cube OGC API",
                "contact":{
                    "url": getRootURL()
                },
                "x-OGClimits" : {
                    "maps":{
                        "maxWidth" : 1600,
                        "maxHeight" : 1200
                    }
                },
                "version": "1.0.0"
            },
            "servers" : [
                {
                    "url" : getRootURL()
                }
            ],
            "tags" : [
                {
                    "name" : "Landing Page",
                    "description" : "Landing Page with the links to the API definition."
                },
                {
                    "name" : "Conformance",
                    "description" : "Conformance classes suported by the server."
                },
                {
                    "name" : "API",
                    "description" : "OpenAPI definition of this API."
                },
                {
                    "name" : "Data Collections",
                    "description" : "List of Data Collections resources and descriptions."
                },
                {
                    "name" : "Maps",
                    "description" : "Access to map for geospatial data resources."
                }
            ],
            "paths" : {
                "/": {
                    "get": {
                        "tags": ["Landing Page"],
                        "summary": "Retrieve the OGC API landing page for this service.",
                        "description": "The landing page provides links to the API definition, to the conformance statements and to the collections in this dataset.",
                        "operationId": "getLandingPage",
                        "parameters":[
                            {"$ref": "#/components/parameters/f-json-html"}
                        ],
                        "responses":{
                            "200":{
                                "description": "Links to the API capabilities and the TileMatrixSets shared by this service.",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "$ref": "#/components/schemas/landingPage"
                                        }
                                    },
                                    "text/html": {
                                        "schema": {
                                            "type": "string"
                                        }
                                    }
                                }
                            },
                            "406":{
                                "$ref": "#/components/responses/NotAcceptable"
                            },
                            "500":{
                                "$ref": "#/components/responses/ServerError"
                            }
                        }
                    }
                },
                "/api": {
                    "get": {
                        "tags": ["API"],
                        "summary": "Retrieve this API definition.",
                        "description": "Retrieve the OpenAPI definition of this API.",
                        "operationId": "getAPI",
                        "parameters":[
                            {"$ref": "#/components/parameters/f-json-html"}
                        ],
                        "responses":{
                            "200":{
                                "description": "Links to the API capabilities and the TileMatrixSets shared by this service.",
                                "content": {
                                    "application/vnd.oai.openapi+json;version=3.0": {
                                        "schema": {
                                            "$ref": "#/components/schemas/api"
                                        }
                                    },
                                    "text/html": {
                                        "schema": {
                                            "type": "string"
                                        }
                                    }
                                }
                            },
                            "406":{
                                "$ref": "#/components/responses/NotAcceptable"
                            },
                            "500":{
                                "$ref": "#/components/responses/ServerError"
                            }
                        }
                    }
                },
                "/conformance": {
                    "get": {
                        "tags": ["Conformance"],
                        "summary": "Retrieve the set of OGC API conformance classes that are supported by this service.",
                        "description": "A list of the URIs of all requirements classes specified in a standard that the server conforms to.",
                        "operationId": "getConformance",
                        "parameters":[
                            {"$ref": "#/components/parameters/f-json-html"}
                        ],
                        "responses":{
                            "200":{
                                "description": "The URIs of all conformance classes supported by the server.",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "$ref": "#/components/schemas/confClasses"
                                        },
                                        "example": {
                                            "conformsTo": [
                                                "http://www.opengis.net/spec/ogcapi-common-1/1.0/conf/core",
                                                "http://www.opengis.net/spec/ogcapi-common-1/1.0/conf/landing-page",
                                                "http://www.opengis.net/spec/ogcapi-common-1/1.0/conf/html",
                                                "http://www.opengis.net/spec/ogcapi-common-1/1.0/conf/json",
                                                "http://www.opengis.net/spec/ogcapi-common-1/1.0/conf/oas30",
                                                "http://www.opengis.net/spec/ogcapi-common-2/1.0/conf/collections",
                                                "http://www.opengis.net/spec/ogcapi-common-2/1.0/conf/json",
                                                "http://www.opengis.net/spec/ogcapi-common-2/1.0/conf/html",
                                                "http://www.opengis.net/spec/ogcapi-maps-1/1.0/conf/core",
                                                "http://www.opengis.net/spec/ogcapi-maps-1/1.0/conf/tilesets",
                                                "http://www.opengis.net/spec/ogcapi-maps-1/1.0/conf/background",
                                                "http://www.opengis.net/spec/ogcapi-maps-1/1.0/conf/scaling",
                                                "http://www.opengis.net/spec/ogcapi-maps-1/1.0/conf/display-resolution",
                                                "http://www.opengis.net/spec/ogcapi-maps-1/1.0/conf/spatial-subsetting",
                                                "http://www.opengis.net/spec/ogcapi-maps-1/1.0/conf/datetime",
                                                "http://www.opengis.net/spec/ogcapi-maps-1/1.0/conf/general-subsetting",
                                                "http://www.opengis.net/spec/ogcapi-maps-1/1.0/conf/crs",
                                                "http://www.opengis.net/spec/ogcapi-maps-1/1.0/conf/collection-map",
                                                "http://www.opengis.net/spec/ogcapi-maps-1/1.0/conf/styled-map",
                                                "http://www.opengis.net/spec/ogcapi-maps-1/1.0/conf/png",
                                                "http://www.opengis.net/spec/ogcapi-maps-1/1.0/conf/jpeg",
                                                "http://www.opengis.net/spec/ogcapi-maps-1/1.0/conf/html",
                                                "http://www.opengis.net/spec/ogcapi-maps-1/1.0/conf/oas30",
                                                "http://www.opengis.net/spec/ogcapi-styles-1/0.0/conf/core"
                                            ]
                                        }
                                    },
                                    "text/html": {
                                        "schema": {
                                            "type": "string"
                                        }
                                    }
                                }
                            },
                            "400":{
                                "$ref": "#/components/responses/InvalidParam"
                            },
                            "406":{
                                "$ref": "#/components/responses/NotAcceptable"
                            },
                            "500":{
                                "$ref": "#/components/responses/ServerError"
                            }
                        }
                    }
                },
                "/collections": {
                    "get": {
                        "tags": ["Data Collections"],
                        "summary": "Retrieve the list of geospatial data collections available from this service.",
                        "description": "Information which describes the set of available collections in this service.",
                        "operationId": "getCollectionsList",
                        "parameters":[
                            {"$ref": "#/components/parameters/f-json-html"}
                        ],
                        "responses":{
                            "200":{
                                "description": "The collections shared by this service. The dataset is organized as one or more collections. This resource provides information about and access to the collections. The response contains the list of collections. For each collection, a link to other resources is present as well as key information about the collection.",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "$ref": "#/components/schemas/collections"
                                        }
                                    },
                                    "text/html": {
                                        "schema": {
                                            "type": "string"
                                        }
                                    }
                                }
                            },
                            "406":{
                                "$ref": "#/components/responses/NotAcceptable"
                            },
                            "500":{
                                "$ref": "#/components/responses/ServerError"
                            }
                        }
                    }
                },
                "/collections/{collectionId}": {
                    "get": {
                        "tags": ["Data Collections"],
                        "summary": "Retrieve the description of a collection available from this service.",
                        "description": "Information about a specific collection of geospatial data with links to distribution.",
                        "operationId": "getCollection",
                        "parameters":[
                            {"$ref": "#/components/parameters/collectionId"},
                            {"$ref": "#/components/parameters/f-json-html"}
                        ],
                        "responses":{
                            "200":{
                                "description": "Metadata about the collection.",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "$ref": "#/components/schemas/collection"
                                        }
                                    },
                                    "text/html": {
                                        "schema": {
                                            "type": "string"
                                        }
                                    }
                                }
                            },
                            "404":{
                                "$ref": "#/components/responses/NotFound"
                            },
                            "406":{
                                "$ref": "#/components/responses/NotAcceptable"
                            },
                            "500":{
                                "$ref": "#/components/responses/ServerError"
                            }
                        }
                    }
                },
                "/collections/{collectionId}/map": {
                    "get": {
                        "tags": ["Maps"],
                        "summary": "Retrieve a map for the specified collection in the default style.",
                        "description": "Retrieves a map for specified collectionthein the default style, in the requested crs, on the requested bbox designed to be shown in a rendering device of a width and a height.",
                        "operationId": ".collection.getMap",
                        "parameters":[
                            {"$ref": "#/components/parameters/collectionId"},
                            {"$ref": "#/components/parameters/crs"},
                            {"$ref": "#/components/parameters/bbox"},
                            {"$ref": "#/components/parameters/bbox-crs"},
                            {"$ref": "#/components/parameters/center"},
                            {"$ref": "#/components/parameters/center-crs"},
                            {"$ref": "#/components/parameters/width"},
                            {"$ref": "#/components/parameters/height"},
                            {"$ref": "#/components/parameters/scale-denominator"},
                            {"$ref": "#/components/parameters/mm-per-pixel"},
                            {"$ref": "#/components/parameters/subset"},
                            {"$ref": "#/components/parameters/subset-crs"},
                            {"$ref": "#/components/parameters/transparent"},
                            {"$ref": "#/components/parameters/bgcolor"},
                            {"$ref": "#/components/parameters/datetime"},
                            {"$ref": "#/components/parameters/f-gif-png-jpeg"}
                        ],
                        "responses":{
                            "200":{
                                "description": "A map of the collection.",
                                "content": {
                                    "image/tiff": {
                                        "schema": {
                                            "type": "string",
                                            "format": "binary"
                                        }							
                                    },
                                    "image/png": {
                                        "schema": {
                                            "type": "string",
                                            "format": "binary"
                                        }
                                    }
                                }
                            },
                            "404":{
                                "$ref": "#/components/responses/NotFound"
                            },
                            "406":{
                                "$ref": "#/components/responses/NotAcceptable"
                            },
                            "500":{
                                "$ref": "#/components/responses/ServerError"
                            }
                        }
                    }
                }
            },
            "components" : {
                "parameters" : {
                    "f-json": {
                        "name": "f",
                        "in": "query",
                        "description": "The format of the response. If no value is provided, the standard http rules apply, i.e., the accept header is used to determine the format. Accepted values is 'json'.",
                        "required": False,
                        "schema": {
                            "type": "string",
                            "enum": [
                                "json"
                            ]
                        },
                        "example": "json",
                        "style": "form",
                        "explode": False
                    },
                    "f-json-html": {
                        "name": "f",
                        "in": "query",
                        "description": "The format of the response. If no value is provided, the standard http rules apply, i.e., the accept header is used to determine the format. Accepted value is are 'json' and 'html'.",
                        "required": False,
                        "schema": {
                            "type": "string",
                            "enum": [
                                "json", "html"
                            ]
                        },
                        "example": "json",
                        "style": "form",
                        "explode": False
                    },
                    "f-json-html-xml": {
                        "name": "f",
                        "in": "query",
                        "description": "The format of the response. If no value is provided, the standard http rules apply, i.e., the accept header is used to determine the format. Accepted values are 'json', 'html' and 'xml'.",
                        "required": False,
                        "schema": {
                            "type": "string",
                            "enum": [
                                "json", "html", "xml"
                            ]
                        },
                        "example": "json",
                        "style": "form",
                        "explode": False
                    },
                    "f-gif-png-jpeg": {
                        "name": "f",
                        "in": "query",
                        "description": "The format of the response. If no value is provided, the standard http rules apply, i.e., the accept header is used to determine the format. Accepted values 'jpeg', 'png' and 'gif' for image based tiles.",
                        "required": False,
                        "schema": {
                            "type": "string",
                            "enum": [
                                "image/png", "image/jpeg", "image/gif"
                            ]
                        },
                        "example": "image/png",
                        "style": "form",
                        "explode": False
                    },
                    "fMap": {
                        "name": "fMap",
                        "in": "query",
                        "description": "The format of the map. If no value is provided, the standard http rules apply, i.e., the accept header is used to determine the format. Accepted values 'jpeg', 'png' and 'gif' for image based maps.",
                        "required": False,
                        "schema": {
                            "type": "string",
                            "enum": [
                                "image/png", "image/jpeg", "image/gif"
                            ]
                        },
                        "example": "image/png",
                        "style": "form",
                        "explode": False
                    },
                    "collections": {
                        "name": "collections",
                        "in": "query",
                        "description": "The collections that should be included in the response. The parameter value is a comma-separated list of collection identifiers. If the parameters is missing, some or all collections will be included. The collection will be rendered in the order specified, with the last one showing on top, unless the priority is overridden by styling rules.",
                        "required": False,
                        "explode": False,
                        "schema": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        }
                    },
                    "collectionId": {
                        "name": "collectionId",
                        "in": "path",
                        "description": "Identifier of a collection.",
                        "required": True,
                        "schema": {
                            "type": "string"
                        }
                    },
                    "crs": {
                        "name": "crs",
                        "in": "query",
                        "description": "A URI or CURIE of the coordinate reference system of the map subset response. A list of all available CRS values can be found under the map description resource.",
                        "required": False,
                        "schema": {
                            "type": "string",
                            "default": "http://www.opengis.net/def/crs/OGC/1.3/CRS84"
                        },
                        "example": "http://www.opengis.net/def/crs/OGC/1.3/CRS84"
                    },
                    "bbox-crs": {
                        "name": "bbox-crs",
                        "in": "query",
                        "description": "A URI or CURIE of the coordinate reference system for the specified bounding box.",
                        "required": False,
                        "schema": {
                            "type": "string",
                            "default": "http://www.opengis.net/def/crs/OGC/1.3/CRS84"
                        },
                        "example": "http://www.opengis.net/def/crs/OGC/1.3/CRS84"
                    },
                    "center-crs": {
                        "name": "center-crs",
                        "in": "query",
                        "description": "A URI or CURIE of the coordinate reference system for the specified center point.",
                        "required": False,
                        "schema": {
                            "type": "string",
                            "default": "http://www.opengis.net/def/crs/OGC/1.3/CRS84"
                        },
                        "example": "http://www.opengis.net/def/crs/OGC/1.3/CRS84"
                    },
                    "subset-crs": {
                        "name": "subset-crs",
                        "in": "query",
                        "description": "A URI or CURIE of the coordinate reference system for the spatial subsettings.",
                        "required": False,
                        "schema": {
                            "type": "string"
                        },
                        "example": "http://www.opengis.net/def/crs/OGC/1.3/CRS84"
                    },
                    "bbox": {
                        "name": "bbox",
                        "in": "query",
                        "description": "Only elements that have a geometry that intersects the bounding box are selected. The bounding box is provided as four or six numbers, depending on whether the coordinate reference system includes a vertical axis (elevation or depth): * Lower left corner, coordinate axis 1 * Lower left corner, coordinate axis 2 * Upper right corner, coordinate axis 1 * Upper right corner, coordinate axis 2 coordinate reference system is specified by another parameter in the API ('crs'). For WGS 84 longitude/latitude (CRS84) the values are in most cases the sequence of minimum longitude, minimum latitude, maximum longitude and maximum latitude. However, in cases where the box spans the antimeridian the first value (west-most box edge) is larger than the third value (east-most box edge).",
                        "required": False,
                        "style": "form",
                        "explode": False,
                        "schema": {
                            "maxItems": 4,
                            "minItems": 4,
                            "type": "array",
                            "items": {
                                "type": "number",
                                "format": "double"
                            }
                        }
                    },
                    "center": {
                        "name": "center",
                        "in": "query",
                        "description": "Coordinates of center point for subsetting, in conjunction with the `width` and/or `height` parameters, taking into consideration the scale and display resolution of the map. The center coordinates are comma-separated and interpreted as [ogc:CRS84], unless the `center-crs` parameter specifies otherwise.",
                        "required": False,
                        "style": "form",
                        "explode": False,
                        "schema": {
                            "maxItems": 2,
                            "minItems": 2,
                            "type": "array",
                            "items": {
                                "type": "number",
                                "format": "double"
                            }
                        }
                    },
                    "subset": {
                        "name": "subset",
                        "in": "query",
                        "description": "Retrieve only part of the data by slicing or trimming along one or more axis. For trimming: {axisAbbrev}({low}:{high}) (preserves dimensionality). An asterisk (`*`) can be used instead of {low} or {high} to indicate the minimum/maximum value. For slicing: {axisAbbrev}({value}) (reduces dimensionality).",
                        "required": False,
                        "style": "form",
                        "explode": False,
                        "schema": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        }
                    },
                    "width": {
                        "name": "width",
                        "in": "query",
                        "description": "Width in pixels of map picture.",
                        "required": False,
                        "style": "form",
                        "explode": False,
                        "schema": {
                            "type": "number"
                        }
                    },
                    "height": {
                        "name": "height",
                        "in": "query",
                        "description": "Height in pixels of map picture.",
                        "required": False,
                        "style": "form",
                        "explode": False,
                        "schema": {
                            "type": "number"
                        }
                    },
                    "scale-denominator": {
                        "name": "scale-denominator",
                        "in": "query",
                        "description": "Scale denominator of the map specifying to how many units in the real world one of the same unit on the map corresponds, as printed or displayed, taking into account the display resolution (`mm-per-pixel` or 0.28 mm/pixel default). This parameter can only be used together with the `width` or `height` parameters (which provide an alternative mechanism to control the scale) if the implementation also supports subsetting, in which case those `width` and `height` parameters then control the subset of the map returned rather than the scale. If `scale-denominator` is omitted, the scale is implied from the dimensions of the returned map compared to its spatial subset area.",
                        "required": False,
                        "style": "form",
                        "explode": False,
                        "schema": {
                            "type": "number"
                        }
                    },
                    "mm-per-pixel": {
                        "name": "mm-per-pixel",
                        "in": "query",
                        "description": "Display resolution of the target rendering device in millimeters per pixel. This parameter controls the relationship between the dimensions of the resulting map in pixels and the scale of the map. The display resolution is taken into account for applying symbology rules, for the `scale-denominator` parameter, and for the spatial subsetting using a `center`, `width` and `height` parameters.",
                        "required": False,
                        "style": "form",
                        "explode": False,
                        "schema": {
                            "type": "number",
                            "format": "double",
                            "default": "0.28"
                        }
                    },
                    "transparent": {
                        "name": "transparent",
                        "in": "query",
                        "description": "Background transparency of map (default=true).",
                        "required": False,
                        "schema": {
                            "type": "boolean",
                            "default": True
                        },
                        "style": "form",
                        "explode": False
                    },
                    "bgcolor": {
                        "name": "bgcolor",
                        "in": "query",
                        "description": "Hexadecimal red-green-blue[-alpha] color value for the background color (default=0xFFFFFF). If alpha is not specified 'opaque' opacity is assumed.",
                        "required": False,
                        "schema": {
                            "type": "string",
                            "default": "0xFFFFFF"
                        },
                        "style": "form",
                        "explode": False
                    },
                    "datetime": {
                        "name": "datetime",
                        "in": "query",
                        "description": "Either a date-time or an interval, open or closed. Date and time expressions adhere to RFC 3339. Open intervals are expressed using double-dots. Examples: A date-time: '2018-02-12T23:20:50Z';  A closed interval: '2018-02-12T00:00:00Z/2018-03-18T12:31:12Z'; Open intervals: '2018-02-12T00:00:00Z/..' or '../2018-03-18T12:31:12Z'. Only elemenets that have a temporal property that intersects the value of 'datetime' are selected. If a element has multiple temporal properties, it is the decision of the server whether only a single temporal property is used to determine the extent or all relevant temporal properties.",
                        "required": False,
                        "schema": {
                            "type": "string"
                        },
                        "style": "form",
                        "explode": False
                    }
                },
                "responses" : {
                    "info": {
                        "description": "Information in an point of a map or a tiles.",
                        "content": {
                            "application/json": {
                                "example": {
                                    "properties": {
                                        "Band 1 [coast/aerosols 0.433-0.453 μm] OLI)(DN)": 23755,
                                        "Band 2 [blue 0.450-0.515 μm] (OLI)(DN)": 23938,
                                        "Band 3 [green 0.525-0.600 μm] (OLI)(DN)": 22554,
                                        "Band 4 [vermell 0.630-0.680 μm] (OLI)(DN)": 23548
                                    }
                                }
                            }
                        }
                    },
                    "InvalidParam": {
                        "description": "Invalid or unknown query parameters."
                    },
                    "NotFound": {
                        "description": "The requested URI was not found."
                    },
                    "NotAcceptable": {
                        "description": "The media types accepted by the client are not supported for this resource."
                    },
                    "ServerError": {
                        "description": "A server error occurred."
                    }
                },
                "schemas" : {
                    "landingPage": {
                        "type": "object",
                        "properties": {
                            "title": {
                                "type": "string",
                                "example": "Servidor de Mapes de MiraMon"
                            },
                            "description": {
                                "type": "string"
                            },
                            "links": {
                                "type": "array",
                                "items": {
                                    "$ref": "#/components/schemas/link"
                                }
                            }
                        }
                    },
                    "confClasses": {
                        "type": "object",
                        "required": ["conformsTo"],
                        "properties": {
                            "conformsTo": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                    "format": "uri"
                                },
                                "example": [
                                    "http://www.opengis.net/spec/ogcapi-common-1/1.0/conf/core",
                                    "http://www.opengis.net/spec/ogcapi-common-1/1.0/conf/landing-page",
                                    "http://www.opengis.net/spec/ogcapi-common-1/1.0/conf/html",
                                    "http://www.opengis.net/spec/ogcapi-common-1/1.0/conf/json",
                                    "http://www.opengis.net/spec/ogcapi-common-1/1.0/conf/oas30",
                                    "http://www.opengis.net/spec/ogcapi-common-2/1.0/conf/collections",
                                    "http://www.opengis.net/spec/ogcapi-common-2/1.0/conf/json",
                                    "http://www.opengis.net/spec/ogcapi-common-2/1.0/conf/html",
                                    "http://www.opengis.net/spec/ogcapi-maps-1/1.0/conf/core",
                                    "http://www.opengis.net/spec/ogcapi-maps-1/1.0/conf/tilesets",
                                    "http://www.opengis.net/spec/ogcapi-maps-1/1.0/conf/background",
                                    "http://www.opengis.net/spec/ogcapi-maps-1/1.0/conf/scaling",
                                    "http://www.opengis.net/spec/ogcapi-maps-1/1.0/conf/display-resolution",
                                    "http://www.opengis.net/spec/ogcapi-maps-1/1.0/conf/spatial-subsetting",
                                    "http://www.opengis.net/spec/ogcapi-maps-1/1.0/conf/datetime",
                                    "http://www.opengis.net/spec/ogcapi-maps-1/1.0/conf/general-subsetting",
                                    "http://www.opengis.net/spec/ogcapi-maps-1/1.0/conf/crs",
                                    "http://www.opengis.net/spec/ogcapi-maps-1/1.0/conf/collection-map",
                                    "http://www.opengis.net/spec/ogcapi-maps-1/1.0/conf/styled-map",
                                    "http://www.opengis.net/spec/ogcapi-maps-1/1.0/conf/png",
                                    "http://www.opengis.net/spec/ogcapi-maps-1/1.0/conf/jpeg",
                                    "http://www.opengis.net/spec/ogcapi-maps-1/1.0/conf/html",
                                    "http://www.opengis.net/spec/ogcapi-maps-1/1.0/conf/oas30",
                                    "http://www.opengis.net/spec/ogcapi-styles-1/0.0/conf/core"
                                ]
                            }
                        }
                    },
                    "collection": {
                        "type": "object",
                        "required": ["id", "links"],
                        "properties": {
                            "id": {
                                "description": "Identifier of the collection used, for example, in URIs.",
                                "type": "string",
                                "example": "buildings"
                            },
                            "title": {
                                "description": "Human readable titles of the collection.",
                                "type": "string",
                                "example": "Building in the city of Barcelona."
                            },
                            "description": {
                                "description": "A description of the collection.",
                                "type": "string",
                                "example": "This collections contains the building in the city of Barcelona."
                            },
                            "keywords": {
                                "description": "Keywords about the elements in the collection.",
                                "type": "array",
                                "items": {
                                    "$ref": "#/components/schemas/keyword"
                                }
                            },
                            "attribution": {
                                "description": "The provider of the source data for the collection. Map viewers normally show this information at the bottom of the map.",
                                "type": "string",
                                "example": "CREAF"
                            },
                            "links": {
                                "type": "array",
                                "nullable": True,
                                "items": {
                                    "$ref": "#/components/schemas/link"
                                }
                            },
                            "extent": {
                                "$ref": "#/components/schemas/extent"
                            },
                            "crs": {
                                "description": "The list of coordinate reference systems supported by the service. The first item is the default coordinate reference system.",
                                "type": "array",
                                "items": {
                                    "type": "string"
                                },
                                "default": ["http://www.opengis.net/def/crs/OGC/1.3/CRS84"],
                                "example": [
                                    "http://www.opengis.net/def/crs/OGC/1.3/CRS84",
                                    "http://www.opengis.net/def/crs/EPSG/0/4326"
                                ]
                            }
                        }
                    },
                    "crs": {
                        "description": "Coordinate reference system of the coordinates in the spatial extent (property 'bbox'). The default reference system is WGS 84 longitude/latitude.",
                        "type": "string",
                        "default": "http://www.opengis.net/def/crs/OGC/1.3/CRS84"
                    },
                    "bbox": {
                        "description": "One or more bounding boxes that describe the spatial extent of the dataset. If multiple areas are provided, the union of the bounding boxes describes the spatial extent.",
                        "type": "array",
                        "minItems": 1,
                        "items": {
                            "description": "West, south, east, north edges of the bounding box. The coordinates are in the coordinate reference system specified in 'crs' (by default this is WGS 84 longitude/latitude).",
                            "type": "array",
                            "oneOf":[
                                {
                                    "minItems": 4,
                                    "maxItems": 4
                                },
                                {
                                    "minItems": 6,
                                    "maxItems": 6
                                }
                            ],
                            "items": {
                                "type": "number"
                            },
                            "example": [
                                [7.01, 50.63, 7.22, 50.78]
                            ]
                        }
                    },
                    "extent": {
                        "description": "The extent of the collection (spatial and temporal).",
                        "type": "object",
                        "properties": {
                            "spatial": {
                            "$ref": "#/components/schemas/spatialExtent"
                            },
                            "temporal": {
                            "$ref": "#/components/schemas/temporalExtent"
                            }
                        }
                    },
                    "spatialExtent": {
                        "description": "The spatial extent of the element in the collection.",
                        "type": "object",
                        "required": "bbox",
                        "properties": {
                            "bbox": {
                                "$ref": "#/components/schemas/bbox"
                            },
                            "crs": {
                                "$ref": "#/components/schemas/crs"
                            }
                        }
                    },
                    "temporalExtent": {
                        "description": "The temporal extent of the element in the collection.",
                        "type": "object",
                        "nullable": True,
                        "properties": {
                            "interval": {
                                "$ref": "#/components/schemas/temporalInterval"
                            },
                            "trs": {
                                "$ref": "#/components/schemas/trs"
                            }
                        }
                    },
                    "temporalInterval": {
                        "description": "One or more time intervals that describe the temporal extent of the dataset.",
                        "type": "array",
                        "nullable": True,
                        "items": {
                        "description": "Begin and end times of the time interval. The timestamps are in the coordinate reference system specified in 'trs (by default this is the Gregorian calendar).",
                        "type": "array",
                        "minItems": 2,
                        "maxItems": 2,
                            "items": {
                                "type": "string",
                                "format": "date-time",
                                "nullable": True
                            },
                            "example": [
                                "2011-11-11T12:22:11Z",
                                "2012-11-24T12:32:43Z"
                            ]
                        }
                    },
                    "trs": {
                        "description": "Coordinate reference system of the coordinates in the temporal extent (property 'interval'). ",
                        "type": "string",
                        "enum": ["http://www.opengis.net/def/uom/ISO-8601/0/Gregorian"],
                        "default": "http://www.opengis.net/def/uom/ISO-8601/0/Gregorian"
                    },
                    "keyword": {
                        "type": "object",
                        "required": ["keyword"],
                        "nullable": True,
                        "properties": {
                            "keyword": {
                                "type": "string",
                                "example": "Land cover"
                            },
                            "code": {
                                "type": "string",
                                "example": "4612"
                            },
                            "codeSpace": {
                                "type": "string",
                                "example": "https://www.eionet.europa.eu/gemet/en/themes/"
                            }
                        }
                    },
                    "collections": {
                        "type": "object",
                        "required": ["links", "collections"],
                        "properties": {
                            "links": {
                                "type": "array",
                                "nullable": True,
                                "items": {
                                    "$ref": "#/components/schemas/link"
                                }
                            },
                            "collections": {
                                "type": "array",
                                "items": {
                                    "allOf": [
                                        {"$ref": "#/components/schemas/collection"}
                                    ]
                                }
                            }
                        }
                    },
                    "2DBoundingBox": {
                        "description": "Minimum bounding rectangle surrounding a 2D resource in the CRS indicated elsewhere.",
                        "type": "object",
                        "required": ["lowerLeft", "upperRight"],
                        "properties": {
                            "lowerLeft": {
                                "$ref": "#/components/schemas/2DPoint"
                            },
                            "upperRight": {
                                "$ref": "#/components/schemas/2DPoint"
                            },
                            "crs": {
                                "description": "Reference to one coordinate reference system (CRS).",
                                "type": "string",
                                "format": "uri",
                                "example": "http://www.opengis.net/def/crs/EPSG/0/3857"
                            },
                            "orderedAxes": {
                                "type": "array",
                                "minItems": 2,
                                "maxItems": 2,
                                "items": {
                                    "type": "string"
                                }
                            }
                        }
                    },
                    "2DPoint": {
                        "description": "A 2D Point in the CRS indicated elsewhere.",
                        "type": "array",
                        "minItems": 2,
                        "maxItems": 2,
                        "items": {
                            "type": "string"
                        }
                    },
                    "geodata-map": {
                        "allOf": [
                            {
                                "$ref": "#/components/schemas/geodata-map_2"
                            },
                            {
                                "$ref": "#/components/schemas/geodata-map-link"
                            }
                        ]
                    },
                    "geodata-map_2": {
                        "allOf": [
                            {
                                "$ref": "#/components/schemas/geodata-styles"
                            },
                            {
                                "$ref": "#/components/schemas/map"
                            }
                        ]
                    },
                    "geodata-styles": {
                        "type": "object",
                        "properties": {
                            "styles": {
                                "$ref": "#/components/schemas/geodata-style-set"
                            }
                        }
                    },
                    "geodata-style-set": {
                        "type": "array",
                        "nullable": True,
                        "items": [
                            {
                                "$ref": "#/components/schemas/style-set-entry",
                                "default-style": {
                                    "type": "string",
                                    "description": "The style id of a recommended default style to use for this collection."
                                }
                            }
                        ]
                    },
                    "map": {
                        "type": "object",
                        "properties": {
                            "defaultStyle": {
                                "$ref": "#/components/schemas/default-style"
                            },
                            "crs": {
                                "description": "The list of coordinate reference systems supported by the map. The first item is the default coordinate reference system.",
                                "type": "array",
                                "items": {
                                    "type": "string"
                                },
                                "default": ["http://www.opengis.net/def/crs/OGC/1.3/CRS84"],
                                "example": [
                                    "http://www.opengis.net/def/crs/OGC/1.3/CRS84",
                                    "http://www.opengis.net/def/crs/EPSG/0/4326"
                                ]
                            },
                            "crsSpatialExtents": {
                                "$ref": "#/components/schemas/crsSpatialExtents"
                            },
                            "minScaleDenominador": {
                                "type": "number",
                                "description": "Minimum scale denominator (inclusive) for which it is appropriate to generate a map of this collection. Requests outside this interval will return an HTTP 404. If it is not present we will assume there is no limit.",
                                "example": 10
                            },
                            "maxScaleDenominador": {
                                "type": "number",
                                "description": "Maximum scale denominator (inclusive) for which it is appropriate to generate a map of this collection. Requests outside this interval will return an HTTP 404. If it is not present we will assume there is no limit.",
                                "example": 10000000
                            },
                            "recomendedFormat": {
                                "type": "string",
                                "description": "Recommended output formats for a map request. Depending of the nature of the data, a format might be better than another. Categorical data looks better in a PNG but continuos data and pictures are smaller a JPEG. The map operation details all available formats for the OGC API maps. In contrast, this is the better one for this type of information. It would be one of the supported for the map operation.",
                                "example": "image/jpeg"
                            },
                            "maxWidth": {
                                "type": "number",
                                "description": "Maximum width value that a client is permitted to include in bbox subset operation.  If absent the server imposes no limit.",
                                "example": 2048
                            },
                            "maxHeight": {
                                "type": "number",
                                "description": "Maximum height value that a client is permitted to include in bbox subset operation.  If absent the server imposes no limit.",
                                "example": 2048
                            }
                        }
                    },
                    "crsSpatialExtents": {
                        "type": "array",
                        "description": "Minimum spatial extent surrounding the spatial resource for each CRS available.",
                        "items": {
                            "$ref": "#/components/schemas/spatialExtent"
                        }
                    },
                    "geodata-map-link": {
                        "type": "object",
                        "required": ["links"],
                        "properties": {
                            "links": {
                                "type": "array",
                                "items": {
                                    "$ref": "#/components/schemas/link"
                                }
                            }
                        }
                    },
                    "linkdataType": {
                        "type": "string",
                        "enum": ["map"]
                    },
                    "id-link": {
                        "type": "object",
                        "required": ["id", "links"],
                        "description": "Reusable object that contains an id to a resource and links where the object is described or a representation retrieved.",
                        "properties": {
                            "id": {
                                "type": "string"
                            },
                            "title": {
                                "type": "string"
                            },
                            "links": {
                                "type": "array",
                                "minItems": 1,
                                "items": {
                                "$ref": "#/components/schemas/link"
                                }
                            }
                        }
                    },
                    "link": {
                        "type": "object",
                        "required": ["href", "rel"],
                        "properties": {
                            "href": {
                                "type": "string",
                                "example": getRootURL()
                            },
                            "rel": {
                                "type": "string",
                                "example": "this"
                            },
                            "type": {
                                "type": "string",
                                "example": "application/json"
                            },
                            "hreflang": {
                                "type": "string",
                                "example": "en"
                            },
                            "title": {
                                "type": "string",
                                "example": "Demonstration map tiles api"
                            },
                            "length": {
                                "type": "integer",
                                "minimum": 0
                            }
                        }
                    }
                }
            }
        }
        if formatToRespond=="text/html":
            startOkResponse(formatToRespond)
            sys.stdout.write('<!DOCTYPE html>\r\n')
            sys.stdout.write('<html>\r\n')
            sys.stdout.write('    <head>\r\n')
            sys.stdout.write('    <meta charset="UTF-8">\r\n')
            sys.stdout.write('    <link rel="stylesheet" type="text/css" href="' + getProtocolURL() + 'www.ogc.grumets.cat/Swagger-UI/swagger-ui.css" >\r\n')
            sys.stdout.write('    <link rel="icon" type="image/png" href="' + getProtocolURL() + 'www.ogc.grumets.cat/Swagger-UI/favicon-32x32.png" sizes="32x32" />\r\n')
            sys.stdout.write('    <link rel="icon" type="image/png" href="' + getProtocolURL() + 'www.ogc.grumets.cat/Swagger-UI/favicon-16x16.png" sizes="16x16" />\r\n')
            sys.stdout.write('    <style>\r\n')
            sys.stdout.write('    html\r\n')
            sys.stdout.write('    {\r\n')
            sys.stdout.write('        box-sizing: border-box;\r\n')
            sys.stdout.write('        overflow: -moz-scrollbars-vertical;\r\n')
            sys.stdout.write('        overflow-y: scroll;\r\n')
            sys.stdout.write('    }\r\n')
            sys.stdout.write('\r\n')    
            sys.stdout.write('    *,\r\n')
            sys.stdout.write('    *:before,\r\n')
            sys.stdout.write('    *:after\r\n')
            sys.stdout.write('    {\r\n')
            sys.stdout.write('        box-sizing: inherit;\r\n')
            sys.stdout.write('    }\r\n')
            sys.stdout.write('\r\n')
            sys.stdout.write('    body\r\n')
            sys.stdout.write('    {\r\n')
            sys.stdout.write('        margin:0;\r\n')
            sys.stdout.write('        background: #fafafa;\r\n')
            sys.stdout.write('    }\r\n')
            sys.stdout.write('    </style>\r\n')
            sys.stdout.write('    <script src="' + getProtocolURL() + 'www.ogc.grumets.cat/Swagger-UI/swagger-ui-bundle.js"> </script>\r\n')
            sys.stdout.write('    <script src="' + getProtocolURL() + 'www.ogc.grumets.cat/Swagger-UI/swagger-ui-standalone-preset.js"> </script>\r\n')
            sys.stdout.write('    <script>\r\n')
            sys.stdout.write('        function CarregaOpenAPI(fitxer) {\r\n')
            sys.stdout.write('        const ui = SwaggerUIBundle({\r\n')
            sys.stdout.write('            url: (fitxer ? fitxer : (location.hash.length ? location.hash.substring(1) : "https://petstore.swagger.io/v2/swagger.json")),\r\n')
            sys.stdout.write('            dom_id: \'#swagger-ui\',\r\n')
            sys.stdout.write('            deepLinking: true,\r\n')
            sys.stdout.write('            presets: [\r\n')
            sys.stdout.write('                SwaggerUIBundle.presets.apis,\r\n')
            sys.stdout.write('                SwaggerUIStandalonePreset\r\n')
            sys.stdout.write('            ],\r\n')
            sys.stdout.write('            plugins: [\r\n')
            sys.stdout.write('                SwaggerUIBundle.plugins.DownloadUrl\r\n')
            sys.stdout.write('            ],\r\n')
            sys.stdout.write('            layout: "StandaloneLayout"\r\n')
            sys.stdout.write('        })\r\n')
            sys.stdout.write('\r\n')
            sys.stdout.write('        window.ui = ui\r\n')
            sys.stdout.write('    }\r\n')
            sys.stdout.write('    </script>\r\n')
            sys.stdout.write('    </head>\r\n')
            sys.stdout.write('    <body onLoad="CarregaOpenAPI(\''+ getRootURL() + '/api?f=json\')">\r\n')
            sys.stdout.write('        <div id="swagger-ui"></div>\r\n')
            sys.stdout.write('    </body>\r\n')
            sys.stdout.write('</html>\r\n')
        elif formatToRespond=="application/json":
            startOkResponse(formatToRespond)
            sys.stdout.write(json.dumps(ApiPageContent))
        else:
            sys.stdout.write('Status: 404\r\nContent-type: text/html\r\nAccess-Control-Allow-Origin: *\r\n\r\n<html><body>API page not supported format. Only allowed"+json.dumps(allowedFormats)+"</body></html>\r\n')            
    else:
        sys.stdout.write('Status: 404\r\nContent-type: text/html\r\nAccess-Control-Allow-Origin: *\r\n\r\n<html><body>'+getRootURL()+'/'+path_param+' not supported or not implemented yet</body></html>\r\n')

#arguments = cgi.FieldStorage()  # https://stackoverflow.com/questions/3582398/getting-http-get-arguments-in-python  # This is all and now you should use urllib.parse.parse_qs(query_string)
#for i in arguments.keys():
#    print ('<li>' + i + ": " + arguments[i].value)

query_string = os.environ['QUERY_STRING']

## convert the query string to a dictionary
query_params = urllib.parse.parse_qs(query_string)

## print out the values of each argument
#for name in arguments.keys():
    ## the value is always a list, watch out for that
#    print(str(name) + ' = ' + str(arguments[name]))

#s=arguments.getfirst("service", "")+arguments.getfirst("SERVICE", "")

service=getArgumentInsensitive(query_params, "service", "")

if service == "":
    #assuming ogc API
    path_info = os.environ['PATH_INFO'];
    script_name = os.environ['SCRIPT_NAME'];

    if len(path_info)>len(script_name) and path_info[len(script_name)] == "/":
        path_param=path_info[len(script_name)+1:]
    else:
        path_param=""
    ogcpi(path_param, query_params)
    sys.exit(0)
        
if service!= "WMS" and service!="WCS":
    sys.stdout.write("Content-type: text/html\r\n\r\n<html><body>Service "+ service +" not supported. WMS and WCS are the only supported</body></html>\r\n")
    sys.exit(0)
    #Status: 404 Not found\r\n  better not to use this

if service == "WMS":   #https://www.datacube.cat/cgi-bin/mmdc.py?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap&CRS=EPSG:32631&BBOX=422401.47,4582942.45,437401.47,4590742.45&WIDTH=1500&HEIGHT=780&LAYERS=s2_level2a_utm31_10&FORMAT=image/jpeg&TRANSPARENT=TRUE&STYLES=&DIM_BAND=red&TIME=2023-07-01
    s=getArgumentInsensitive(query_params, "version", "")
    if s != "1.3.0":
        sys.stdout.write('Content-type: text/html\r\n\r\n<html><body>Version not supported. 1.3.0 is the only version supported</body></html>\r\n')
        sys.exit(0)

    s=getArgumentInsensitive(query_params, "request", "")
    if s != "GetMap":
        sys.stdout.write('Content-type: text/html\r\n\r\n<html><body>Request supported. GetMap is the only request supported</body></html>\r\n')
        sys.exit(0)

    layers=getArgumentInsensitive(query_params, "layers", "")  

    bbox=getBBoxFromBBox(getArgumentInsensitive(query_params, "bbox", ""))

    res=getResolutionFromWidthHeight(getArgumentInsensitive(query_params, "width", ""), getArgumentInsensitive(query_params, "height", ""), bbox)

    time=getArgumentInsensitive(query_params, "time", "")
    crs=getEPSGOldFormat(getArgumentInsensitive(query_params, "crs", "EPSG:32631"))
    
    band=getArgumentInsensitive(query_params, "dim_band", "")
    if band == "":
        sys.stdout.write('Content-type: text/html\r\n\r\n<html><body>DIM_BAND parameter is required</body></html>\r\n')
        sys.exit(0)
    
else:  #if service == "WCS"   #https://www.datacube.cat/cgi-bin/mmdc.py?SERVICE=WCS&VERSION=2.0.1&REQUEST=GetCoverage&SUBSET=E(422401.47,437401.47)&SUBSET=N(4582942.45,4590742.45)&COVERAGEID=s2_level2a_utm31_10&FORMAT=image/jpeg&RANGESUBSET=red&SUBSET=ansi("2023-07-01")
    s=getArgumentInsensitive(query_params, "version", "")
    if s != "2.0.1":
        sys.stdout.write('Status: 404 Not found\r\nContent-type: text/html\r\n\r\n<html><body>Version not supported. 2.0.1 is the only version supported</body></html>\r\n')
        sys.exit(0)
        
    s=getArgumentInsensitive(query_params, "request", "")
    if s != "GetCoverage":
        sys.stdout.write('Content-type: text/html\r\n\r\n<html><body>Request not supported. GetCoverage is the only request supported</body></html>\r\n')
        sys.exit(0)

    layers=getArgumentInsensitive(query_params, "coverageid", "")
    
    subsets=getArgumentsInsensitive(query_params, "subset", [])
    bbox=getBBoxFromSubsetWCS(subsets)
    if len(bbox)==0:
        sys.stdout.write('Status: 404\r\nContent-type: text/html\r\nAccess-Control-Allow-Origin: *\r\n\r\n<html><body>subset=E or subset=N parameter not found.</body></html>\r\n')
        sys.exit(0)
    time=getTimeFromSubsetWCS(subsets)
    if time=="":
        sys.stdout.write('Status: 404\r\nContent-type: text/html\r\nAccess-Control-Allow-Origin: *\r\n\r\n<html><body>subset=ansi parameter not found.</body></html>\r\n')
        sys.exit(0)
        
    band=getArgumentInsensitive(query_params, "rangesubset", "")
    if band == "":
        sys.stdout.write('Content-type:text/html\r\n\r\n<html><body>rangesubset parameter is required</body></html>\r\n')
        sys.exit(0)
        
    res=getResolutionFromScaleFactor(getArgumentInsensitive(query_params, "scalefactor", ""), 10)
    
    crs=getEPSGOldFormat(getArgumentInsensitive(query_params, "outputCRS", "EPSG:32631"))
    
mimetype=getArgumentInsensitive(query_params, "format", "")

getCoverageAndSendResult(datacube.Datacube(app='datacube-cgi'), layers, bbox, crs, res, time, band, mimetype)