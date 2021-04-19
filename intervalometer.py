#!/usr/bin/python3
#
# This software is covered by The Unlicense license
#

import argparse
import datetime
import os
import pathlib
import subprocess
import sys
import time
from astral.sun import sun
from astral import LocationInfo

# Setting up the command line arguments  #####
#
parser = argparse.ArgumentParser()

parser.add_argument('-i','--interval', required=True, type=int,
       metavar='###', help="Time between pictures in seconds.")
parser.add_argument('-s','--startstop', nargs=2,
       metavar='HH:MM', help="List start and stop in 24 hour format. Default is to start at dawn and stop at dusk")
parser.add_argument('-o','--offset', nargs=1, type=int, default=0,
       metavar='#', help="How many hours before dawn to start, and after dusk to stop.")
parser.add_argument('-m','--multiday', nargs=1, type=int, default=1,
       metavar='#', help="How many days to run the program for.  Default is 1.")
parser.add_argument('-d','--dir', nargs=1, type=str,
       metavar='directory', help="Full directory path to save the project to.  Defaults to /data.")
parser.add_argument('-p','--project', nargs=1, type=str, required=True,
       metavar='project', help="Name of the project you are taking pictures for.  This directory will be created if it doesn't exist.")
parser.add_argument('-f','--faux', action='store_true',
       help="Use the gfauxto2 command to simulate taking pictures.  Will create empty files instead of taking pictures.")
parser.add_argument('-t','--latitude', nargs=1, type=float,
       metavar='xx.yyy', help="Latitude to calculate dawn and dusk. Default is 35.78")
parser.add_argument('-g','--longitude', nargs=1, type=float,
       metavar='xx.yyy', help="Longitude to calculate dawn and dusk. Default is -78.64")
parser.add_argument('-b','--backup', nargs=1, type=str,
       metavar='backup target', help="I don't know what this looks like yet.  Not implemented.")
parser.add_argument('-v','--verbose', action='store_true',
       help="Show debugging messages on the command line")

args = parser.parse_args()

# Checking for conflicting arguments  #####
#
if args.longitude and not args.latitude:
    parser.error("--longitude requires --latitude")
if args.latitude and not args.longitude:
    parser.error("--latitude requires --longitude")
if args.startstop and args.offset:
    parser.error("--offset cannot be used with --startstop. Do your own math.")
    

##### Set default arguments  #####

picture_number = 0     # You have to start counting pictures with some number

this_day = 1     # Start on day 1 in case of multi-day events.

if not args.multiday:
    total_days = 1
else:
    total_days = args.multiday
debug_print('INIT: multiday value is ' + total_days)

if not args.offset:
    offset = 0
else:
    offset = args.offset[0]

if not args.dir:
    dir = '/data'
else:
    dir = args.dir[0]

now = time.localtime()
if not args.project:
    filename = str(time.strftime("%Y-%m-%d-", now))
else:
    filename = args.project[0] + '-' + str(time.strftime("%Y-%m-%d-", now))
debug_print('INIT: filename is ' + filename)

if args.longitude and args.latitude:
    loc = LocationInfo(name='Custom',latitude=args.latitude[0], longitude=args.longitude[0])
else:
    loc = LocationInfo(name='Raleigh', region='NC, USA', timezone='America/New_York',
                       latitude=35.78, longitude=-78.64)

proc1 = subprocess.Popen(['gphoto2', '--auto-detect'], stdout=subprocess.PIPE)
proc2 = subprocess.Popen(['wc', '-l'], stdin=proc1.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
proc1.stdout.close() # Allow proc1 to receive a SIGPIPE if proc2 exits.
out, err = proc2.communicate()
print(out.strip())
if int(out.strip()) <= 2:
    args.faux = True
    debug_print('No camera found - using gfauxto2 to simulate pictures')
else:
    debug_print('Camera found - using gphoto2 to take pictures')
proc2.stdout.close()
proc2.stderr.close()

path = '/'.join([dir,args.project[0],''])
os.makedirs(path, mode=0o775, exist_ok=True)
os.chdir(path)
debug_print('INIT: path is ' + path)

######  Subroutines   #####

def debug_print(string):
    # Add print statement here is -v is set.  Still have to figure out how to set it.
    if args.verbose:
        now = time.localtime()
        debug_time = str(time.strftime("%H:%M:%S ", now))
        print('DEBUG: ' + debug_time + string)

def take_picture(basename):
    global picture_number
    debug_print('*click* ' + str(picture_number).zfill(4))
    if args.faux:
        result = subprocess.run(['/home/pi/bin/gfauxto2', '--capture-image-and-download'], stdout=subprocess.PIPE).stdout.decode('utf-8')
    else:
        result = subprocess.run(['gphoto2', '--capture-image-and-download'], stdout=subprocess.PIPE).stdout.decode('utf-8')
    debug_print('gphoto output: ' + result)
    for line in result.split('\n'):
        if line.startswith('Saving file as'):
            capture_filename = line.split()
    os.rename(capture_filename[3], dir + '/' + args.project + '/' + filename + str(picture_number).zfill(4) + '.jpg')
    picture_number += 1 

def waitforrighttime():
    #####   This loop will check the time and wait until we get to the correct time to exit the loop.  #####
    debug_print('Waiting for the correct time to take pictures')
    while True:
        now = time.localtime()
        current_hour = int(time.strftime("%H", now))
        current_min = int(time.strftime("%M", now))
        debug_print('Current time: ' + str(current_hour) + ':' + str(current_min))
        debug_print('Start time: ' + str(start_hour) + ':' + str(start_min))

        if current_hour < start_hour:
            debug_print('We have a while to wait, sleeping until the next hour checkpoint')
            seconds_to_sleep = 60 * (60 - int(time.strftime("%M", now)))
            debug_print('Sleeping for ' + str(seconds_to_sleep) + ' seconds.')
            time.sleep(seconds_to_sleep)
        elif current_hour == start_hour:
            debug_print('Hours are the same')
            if current_min < start_min:
                 debug_print('We have minutes to wait...')
                 seconds_to_sleep = (60 * (start_min - current_min)) + 5
                 debug_print('Sleeping for ' + str(seconds_to_sleep) + ' seconds.')
                 time.sleep(seconds_to_sleep)
            else:
                # if current_min >= start_min
                debug_print('Start minute is greater or equal to current minute')
                debug_print('Ending loop 1')
                break

def takepicturesandstop():
    #This loop will take pictures every *interval* seconds and watch for the stop time
    debug_print('Time to start looping through taking pictures and checking stop times.')
    while True:
        now = time.localtime()
        current_hour = int(time.strftime("%H", now))
        current_min = int(time.strftime("%M", now))
        debug_print('Current time: ' + str(current_hour) + ':' + str(current_min))
        debug_print('Stop time: ' + str(stop_hour) + ':' + str(stop_min))

        if current_hour == stop_hour:
            debug_print('The hour to stop has arrived... but has the minute arrived?')
            if current_min >= stop_min:
                debug_print('The minute to stop has arrived. ')
                break
        elif current_hour > stop_hour:
            debug_print('This should never happen, but typos do occur and math is hard')
            break
    
        debug_print('Time to take a picture')
        take_picture(filename)
        time.sleep(args.interval)


##### Setting up the start and stop times for the day                      #####
##### These either come from the command paramters or from dusk and dawn.  #####

if args.startstop:
    start_hour = int(args.startstop[0].split(':')[0])
    start_min = int(args.startstop[0].split(':')[1])
    stop_hour = int(args.startstop[1].split(':')[0])
    stop_min = int(args.startstop[1].split(':')[1])
else:
    s = sun(loc.observer, date=datetime.date.today(), tzinfo=loc.timezone)

    start_hour = int(str(s['dawn'])[11:13]) - offset
    start_min = int(str(s['dawn'])[14:16])
    stop_hour = int(str(s['dusk'])[11:13]) + offset
    stop_min = int(str(s['dusk'])[14:16])

#####  Now that we have subtracted and added to time, we need to make sure that the  ######
#####  numbers for minute and hour are still within what we expect for time.  If we  ######
#####  mess this up then we will end up in a loop forever later in the program.      ######

if start_min > 59:
    start_min = start_min - 60
    start_hour = start_hour + 1
if stop_min > 59:
    stop_min = stop_min - 60
    stop_hour - stop_hour + 1
if start_hour < 0:
    start_hour = 24 + start_hour
if stop_hour > 23:
    stop_hour = stop_hour - 24
debug_print('Start Time: ' + str(start_hour) + ':' + str(start_min) + ' Stop time: ' + str(stop_hour) + ':' + str(stop_min))


##### We should have sane values, so it time to get to work.   #####
##### Loop in case there is a multi-day parameter.  If there   #####
##### is not multi-day we'll break from the loop after getting #####
##### most of the way through it.  No matter what we need to   #####
##### at least take one days worth of pictures.                #####

while True:

    waitforrighttime()      # This loop is a matter of sleeping until the correct time.
    takepicturesandstop()   # This loop takes pictures and looks for the stopping time.

    debug_print('This is ' + str(this_day) + ' of total days ' + str(total_days))
    if this_day == total_days:
        break

    now = time.localtime()
    current_hour = int(time.strftime("%H", now))
    current_min = int(time.strftime("%M", now))
    seconds_to_sleep = 60 * (60 - current_min)
    debug_print('Sleeping until the top of the hour.  About ' + str(seconds_to_sleep) + ' seconds away')
    time.sleep(seconds_to_sleep)

    while current_hour > 0:
        debug_print('It is not tomorrow yet, sleeping another hour.')
        time.sleep(3600) #hour
        now = time.localtime()
        current_hour = int(time.strftime("%H", now))

    debug_print('Reset the picture_number to 0000')
    picture_number = 0     # At the end of the day we rest the picture number back to 0
    time.sleep(60)        # Sleep for another minute to make sure we are past midnight

    now = time.localtime()
    debug_print('Set the filename to the next day')
    if not args.project:
        filename = str(time.strftime("%Y-%m-%d-", now))
    else:
        filename = args.filename[0] + '-' + str(time.strftime("%Y-%m-%d-", now))

    this_day += 1

debug_print('End of Program.')
