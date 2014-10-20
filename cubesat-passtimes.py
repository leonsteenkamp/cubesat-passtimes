#!/usr/bin/env python
# Author: Leon Steenkamp - https://github.com/leonsteenkamp
# 20 October 2014
# Based on http://http://rhodesmill.org/pyephem/tutorial.html 
# and http://rhodesmill.org/pyephem/quick
import sys
import string
import time
import os
import ephem
import math
import urllib2
import argparse
import httplib2
import MySQLdb

if sys.platform in ['linux','linux2']:
    os.system('clear')
elif sys.platform in ['win32']:
    os.system('cls')

# One of "passes" or "hours" should be 0. Use "passes" to calculate 
# for the next n passes or "hours" for the passes during the next n hours
# "satName" should be a something that can be used to find the TLE by its name
# "addDateToDB" can be used to control writing to the DB, for testing, currently False
satName = "ZACUBE" # or "UKUBE"
addDateToDB = True
passes = 1
hours = 0
PassLocationLon = "18.64279"
PassLocationLat = "-33.932343"
PassLocationEle = 80

# Your database details
# Create your table with :
# create table userYourTableNameHere (ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP, aos TIMESTAMP, los TIMESTAMP, ele INT);
DBhost="hostname.co.za" # your DB host, usually localhost
DBuser="username"       # your DB username
DBpasswd="password"     # your DB password
DBdb="database"         # name of the database
DBtable="table"         # name of the database table

print "Platform: %s" % sys.platform

def GetTLE():
    '''GetTLEs(): returns a list of tuples of keps for each satellite.
    This function currently relies on a url from amsat.org.'''

    # grab the latest keps
    tles = urllib2.urlopen('http://www.celestrak.com/NORAD/elements/cubesat.txt').readlines()

    # strip off the header tokens and newlines
    tles = [item.strip() for item in tles]

    # clean up the lines
    tles = [(tles[i],tles[i+1],tles[i+2]) for i in xrange(0,len(tles)-2,3)]

    return tles

def addDBentry(aosRaw,losRaw,ele):
    aos = aosRaw
    los = losRaw
    db = MySQLdb.connect(host=DBhost,       # your host, usually localhost
                         user=DBuser,       # your username
                         passwd=DBpasswd,   # your password
                         db=DBdb)           # name of the data base
    cur = db.cursor() 
    cur.execute("""INSERT INTO """ + DBtable + """ VALUES (null,%s,%s,%s)""",(aos,los,ele))
    db.commit()
    cur.close()
    db.close()


print("Retrieving TLE")
str = GetTLE()
print("Done\nCalculating\n")

for s in str:
    for a in s:
        if satName in a:
            print "TLE found for : %s" % satName
            print("%s") % s[0]
            print("%s") % s[1]
            print("%s\n") % s[2]
            meanmotion = s[2][52:63]
            zacube = ephem.readtle(s[0],s[1],s[2])

#tleLine1 = "2013-066B"
#tleLine2 = "1 39417U 13066B   13349.05334596  .00003010  00000-0  41766-3 0   762"
#tleLine3 = "2 39417  97.7974  60.9212 0064739 119.6848 241.0835 14.77205056  3503"
#zacube = ephem.readtle(tleLine1, tleLine2, tleLine3)

# city = ephem.city('Cape Town')
# print city.lat, city.lon

#lotime = ephem.localtime(info[0])
orbitalperiod = (24*60)/float(meanmotion)
print "Orbital Period: %.1f minutes\n" % orbitalperiod
location = ephem.Observer()
location.lon = PassLocationLon
location.lat = PassLocationLat
location.elevation = PassLocationEle
location.date = ephem.now()

startDate = ephem.now()
count=0

if hours!=0 and passes==0:
    print ("Passes for next %d hours\n" % hours)
    while location.date <= ephem.Date(startDate+(hours*ephem.hour)):
        rt,ra,tt,ta,st,sa = location.next_pass(zacube)

        if ephem.Date(rt) >= ephem.Date(startDate+(hours*ephem.hour)):
            break

        print("Rise time:   %s UTC" % rt)
        print("Transit time: %s UTC" % tt)
        print("Set time:     %s UTC" % st)
        print("Rise azimuth: %.1f" % math.degrees(ra))
        print("Set azimuth:  %.1f" % math.degrees(sa))
        print("Transit alt:  %.1f" % math.degrees(ta))
        print "\n"

        location.date = ephem.Date(st + (orbitalperiod/2) * ephem.minute) #set the new date to start calc from well outside the current pass time
        
        if addDateToDB == True:
            __start = rt
            __end = st
            __start = __start.timetuple()
            __end = __end.timetuple()
            addDBentry(__start, __end, math.degrees(ta))

elif passes!=0 and hours==0:
    print ("Next %d passes\n" % passes)
    for x in range(passes):
        rt,ra,tt,ta,st,sa = location.next_pass(zacube)
        print("Rise time:   %s UTC" % rt)
        print("Transit time: %s UTC" % tt)
        print("Set time:     %s UTC" % st)
        print("Rise azimuth: %.1f" % math.degrees(ra))
        print("Set azimuth:  %.1f" % math.degrees(sa))
        print("Transit alt:  %.1f" % math.degrees(ta))
        print "\n"

        location.date = ephem.Date(st + (orbitalperiod/2) * ephem.minute) #set the new date to start calc from well outside the current pass time
        
        if addDateToDB == True:
            __start = rt
            __end = st
            addDBentry(__start, __end, math.degrees(ta))

else:
    print("huh?\n")


exit()
