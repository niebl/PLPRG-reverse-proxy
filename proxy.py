#!/usr/bin/python3

import requests
import asyncio
import time
import os
import argparse, sys
import re

from sanic import Sanic
from sanic.response import text
from cors import add_cors_headers
from options import setup_options


### APP DEFINITION

app = Sanic("mapExcerptServer")
app.register_listener(setup_options, "before_server_start")
app.register_middleware(add_cors_headers, "response")

reverseServer = "127.0.0.1:8088/reverse.php"
cacheAreaServer = "127.0.0.1:8080/cacheArea"
mobileClientServer = "127.0.0.1:8081/reverse"

@app.get("/status")
def status(request):
    return text("map-excerpt-server running")

#usual nominatim
@app.get("/reverse")
async def reverseHandler(request):
    outbound = f"http://{reverseServer}?{request.query_string}&format=json"

    #TODO: log this stuff
    st = time.time()    
    res = requests.get(outbound)
    et = time.time()
    elapsed = et - st

    a = nominatimLogger.extractArgs(request.query_string)
    st = a["time"] if a["time"] else st
    log = [str(st), outbound, a["lat"], a["lon"], elapsed, str(len(res.content))]

    nominatimLogger.append(log)
    return text(res.text)

#requests to mobileClient
@app.get("/mobileClient")
async def mobileClientHandler(request):
    outbound = f"http://{mobileClientServer}?{request.query_string}"
    #TODO: log this stuff

    st = time.time()
    res = requests.get(outbound)
    et = time.time()
    elapsed = et - st

    a = mcLogger.extractArgs(request.query_string)
    print(a)
    st = a["time"] if a["time"] else st
    print(st)
    log = [str(st), outbound, a["lat"], a["lon"], elapsed, str(len(res.content))]

    mcLogger.append(log)
    return text(res.text)

#requests to mapExcerptServer
#TODO: log responses
@app.get("/cacheArea")
async def cacheAreaHandler(request):
    outbound = f"http://{cacheAreaServer}?{request.query_string}"
    #TODO: log this stuff
    st = time.time()
    res = requests.get(outbound)
    et = time.time()
    elapsed = et - st

    a = mesLogger.extractArgs(request.query_string)
    st = a["time"] if a["time"] else st
    log = [str(st), outbound, a["lat"], a["lon"], elapsed, str(len(res.content))]

    mesLogger.append(log)
    return text(res.text)


#class that will write logs to a CSV file
#headers is an array of strings
class CSVLogger:
    #construct empty
    def __init__(self, filename=None, headers=None, separator = ",", verbose=False):
        self.filename = filename
        self.file = None
        self.v = verbose
        self.sep = separator
        self.headers = headers

    '''
    def __init__(self, filename, headers, separator = ",", verbose = False):
        self.filename = filename
        self.v = verbose
        self.sep = separator
        self.headers = headers
        
        if not self.fileExists():
            self.createFile(headers)
        self.file = open(self.filename, "a")
        return
    '''        
    
    def initialize(self, filename, headers):
        self.headers = headers
        self.filename = filename
        
        if not self.fileExists():
            self.createFile(headers)
        return
    
    def fileExists(self):
        return os.path.isfile(self.filename)

    def createFile(self, headers):
        file = open(self.filename, "w")
        header = self.sep.join(headers) + "\n"
        file.write(header)
        file.close

    def append(self, values):
        self.file = open(self.filename, "a+")
        values = map(str, values) 
        line = self.sep.join(values) + "\n"
        print(self.file)
        try:
            self.file.write(line)
        except:
            print("append went wrong")
        self.file.close()
    
    def extractArgs(self, url):
        lat = re.search(r"(?<=lat=)(.*?)(?=&|$)", url)
        lon = re.search(r"(?<=lon=)(.*?)(?=&|$)", url)
        time = re.search(r"(?<=time=)(.*?)(?=&|$)", url)

        lat = lat.group() if lat else ""
        lon = lon.group() if lon else ""
        time = time.group() if time else ""

        return {"lat": lat, "lon": lon, "time": time}



def stringSize(input):
    return len(input.encode('utf-8'))

nominatimLogger = CSVLogger(separator=";")
mcLogger = CSVLogger(separator=";")
mesLogger = CSVLogger(separator=";")



#handle arguments
parser = argparse.ArgumentParser()

parser.add_argument("--nomURI", help="address of the nominatim server-endpoint")
parser.add_argument("--mcURI", help="address of the mobile client endpoint")
parser.add_argument("--mesURI", help="address of the map excerpt server endpoint")

parser.add_argument("--logfilePath", help="filepath of the logfiles")

parser.add_argument("--nomFile", help="name of nominatim logfile")
parser.add_argument("--mcFile", help="name of mobile client logfile")
parser.add_argument("--mesFile", help="name of map excerpt server logfile")

parser.add_argument("--port", help="port on which to listen")

args=parser.parse_args()
args = vars(args)

if __name__ == "__main__":
    port = int(args["port"]) if args["port"] else 8082
    app.run(host='127.0.0.1', port=port, access_log=True)

### ARGUMENTS
if args["nomURI"]:
    reverseServer = args["nomURI"]
if args["mcURI"]:
    mobileClientServer = args["mcURI"] 
if args["mesURI"]:
    cacheAreaServer = args["mesURI"]

nomFile = args["nomFile"] if args["nomFile"] else "nominatim_log.csv"
mcFile = args["mcFile"] if args["mcFile"] else "mobileClient_log.csv"
mesFile = args["mesFile"] if args["mesFile"] else "mapExcerptServer_log.csv"

nominatimLogger.initialize(nomFile, ["timestamp", "request", "lat", "lon", "elapsed", "responseSize"])
mcLogger.initialize(mcFile, ["timestamp", "request", "lat", "lon", "elapsed", "responseSize"])
mesLogger.initialize(mesFile, ["timestamp", "request", "lat", "lon", "elapsed", "responseSize"])