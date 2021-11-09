#!/usr/bin/python3
#
# Written by ScottStanton
# https://github.com/ScottStanton/
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
from paramiko import SSHClient
from scp import SCPClient


##### Setting up the command line arguments  #####

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
parser.add_argument('-b','--backup', nargs=2, type=str,
       metavar=('hostname','destination_directory'), help="Hostname and  Destination directory to backup to.  Must have passwordless scp setup to the host.")
parser.add_argument('-v','--verbose', action='store_true',
       help="Show debugging messages on the command line")

args = parser.parse_args()

##### Checking for conflicting arguments  #####

if args.longitude and not args.latitude:
    parser.error("--longitude requires --latitude")
if args.latitude and not args.longitude:
    parser.error("--latitude requires --longitude")
if args.startstop and args.offset:
    parser.error("--offset cannot be used with --startstop. Do your own math.")
    
######  Subroutines   #####

def current_time():
    now = time.localtime()
    now_hour = int(time.strftime("%H", now))
    now_min = int(time.strftime("%M", now))
    now_sec = int(time.strftime("%S", now))
    return now_hour, now_min, now_sec

def debug_print(string):
    # Add print statement here is -v is set.  Still have to figure out how to set it.
    if args.verbose:
        now = time.localtime()
        debug_time = str(time.strftime("%H:%M:%S ", now))
        print(f'DEBUG: {debug_time} - {string}')
## End of function

def take_picture():
    global picture_number
    debug_print(f'*click* {picture_number:0>4d}')
    if args.faux:
        result = subprocess.run(['/home/pi/bin/gfauxto2', '--capture-image-and-download'], stdout=subprocess.PIPE).stdout.decode('utf-8')
    else:
        result = subprocess.run(['gphoto2', '--capture-image-and-download'], stdout=subprocess.PIPE).stdout.decode('utf-8')
    debug_print(f'gphoto output: {result}')
    for line in result.split('\n'):
        if line.startswith('Saving file as'):
            capture_filename = line.split()
    os.rename(capture_filename[3], dir + '/' + args.project[0] + '/' + filename + str(picture_number).zfill(4) + '.jpg')
    debug_print(f'Move file to {dir}/{args.project[0]}/{filename}{picture_number:0>4d}.jpg')
    picture_number += 1
## End of function

def backup_picture():
    debug_print('Backing up picture')
    before_hour, before_min, before_sec = current_time()

    ssh = SSHClient()
    ssh.load_system_host_keys()
    if '@' in args.backup[0]:
       dest_user,dest_host = args.backup[0].split('@')
       debug_print(f'INIT: Destination user is {dest_user}')
       ssh.connect(dest_host, username=dest_user)
    else:
       dest_host = args.backup[0]
       dest_user = ''
       ssh.connect(dest_host)

        
    debug_print(f'SSH connection to {dest_host} is open.')

    scp = SCPClient(ssh.get_transport())
    file_name = filename + str(picture_number - 1).zfill(4) + '.jpg'
    full_source = dir + '/' + args.project[0] + '/' + file_name
    dest_path = args.backup[1].replace('\\','/')
    full_dest = '/'.join([dest_path,file_name])
    debug_print(f'Copy {full_source} to {full_dest}')
    scp.put(full_source, full_dest)

    scp.close()
    ssh.close()
    after_hour, after_min, after_sec = current_time()

    if after_min < before_min:
        after_min += 60
    if after_sec < before_sec:
        after_sec += 60
    change_min = after_min - before_min
    change_sec = after_sec - before_sec
    change = change_sec + (60 * change_min)
    debug_print(f'Copy process took {change!s} seconds')
    return change
## End of function


def waitforrighttime():
    #####   This loop will check the time and wait until we get to the correct time to exit the loop.  #####
    debug_print('Waiting for the correct time to take pictures')
    while True:
        current_hour, current_min, current_sec = current_time()
        debug_print(f'Current time: {current_hour:0>2d}:{current_min:0>2d}')
        debug_print(f'Start time: {start_hour:0>2d}:{start_min:0>2d}')

        if current_hour < start_hour:
            debug_print('We have a while to wait, sleeping until the next hour checkpoint')
            seconds_to_sleep = 60 * (60 - int(time.strftime("%M", now)))
            debug_print(f'Sleeping for {seconds_to_sleep!s} seconds.')
            time.sleep(seconds_to_sleep)
        elif current_hour == start_hour:
            debug_print('Hours are the same')
            if current_min < start_min:
                 debug_print('We have minutes to wait...')
                 seconds_to_sleep = (60 * (start_min - current_min)) + 5
                 debug_print(f'Sleeping for {seconds_to_sleep!s} seconds.')
                 time.sleep(seconds_to_sleep)
            else:
                # if current_min >= start_min
                debug_print('Start minute is greater or equal to current minute')
                debug_print('Ending loop 1')
                break
    ## End of while loop
## End of function


def takepicturesandstop():
    #This loop will take pictures every *interval* seconds and watch for the stop time
    debug_print('Time to start looping through taking pictures and checking stop times.')
    while True:
        current_hour, current_min, current_sec = current_time()
        debug_print(f'Current time: {current_hour:0>2d}:{current_min:0>2d}')
        debug_print(f'Stop time: {stop_hour:0>2d}:{stop_min:0>2d}')

        if current_hour == stop_hour:
            debug_print('The hour to stop has arrived... but has the minute arrived?')
            if current_min >= stop_min:
                debug_print('The minute to stop has arrived. ')
                break
        elif current_hour > stop_hour:
            debug_print('This should never happen, but typos do occur and math is hard')
            break

        debug_print('Time to take a picture')
        take_picture()

        sleep_time = args.interval

        if args.backup:
            backup_seconds = backup_picture()
            sleep_time = args.interval - backup_seconds
        if sleep_time < 0:
            sleep_time = 0

        debug_print(f'Sleep for {sleep_time!s} seconds')
        time.sleep(sleep_time)
    ## End of while loop
## End of function

def wait_for_end_of_day():
    debug_print('Enter wait_for_end_of_day')
    current_hour, current_min, current_sec = current_time()
    seconds_to_sleep = 60 * (60 - current_min)
    debug_print(f'Sleeping until the top of the hour.  About {seconds_to_sleep!s} seconds away')
    time.sleep(seconds_to_sleep)

    current_hour, current_min, current_sec = current_time()

    while current_hour > 0:
        debug_print('It is not tomorrow yet, sleeping another hour.')
        time.sleep(3600) #hour
        current_hour, current_min, current_sec = current_time()
## End of function

def start_stop_time_set():
    global start_hour
    global start_min
    global stop_hour
    global stop_min  
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


##### Set default arguments  #####

picture_number = 0     # You have to start counting pictures with some number

last_picture_transfered = 0

last_hour = 0

this_day = 1     # Start on day 1 in case of multi-day events.

total_days = args.multiday
debug_print(f'INIT: multiday value is {total_days}')

if not args.offset:
    offset = 0
else:
    offset = args.offset[0]
debug_print(f'INIT: offset value is {offset!s}')

if not args.dir:
    dir = '/data'
else:
    dir = args.dir[0]

if args.longitude and args.latitude:
    loc = LocationInfo(name='Custom',latitude=args.latitude[0], longitude=args.longitude[0])
else:
    loc = LocationInfo(name='Raleigh', region='NC, USA', timezone='America/New_York',
                       latitude=35.78, longitude=-78.64)

proc1 = subprocess.Popen(['gphoto2', '--auto-detect'], stdout=subprocess.PIPE)
proc2 = subprocess.Popen(['wc', '-l'], stdin=proc1.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
proc1.stdout.close() # Allow proc1 to receive a SIGPIPE if proc2 exits.
out, err = proc2.communicate()
if int(out.strip()) <= 2:
    args.faux = True
    debug_print('INIT: No camera found - using gfauxto2 to simulate pictures')
else:
    debug_print('INIT: Camera found - using gphoto2 to take pictures')
proc2.stdout.close()
proc2.stderr.close()

path = '/'.join([dir,args.project[0],''])
os.makedirs(path, mode=0o775, exist_ok=True)
os.chdir(path)
debug_print(f'INIT: path is {path}')


##### Setting up the start and stop times for the day                      #####
##### These either come from the command paramters or from dusk and dawn.  #####

start_stop_time_set()

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
debug_print(f'Start Time: {start_hour:0>2d}:{start_min:0>2d} Stop time: {stop_hour:0>2d}:{stop_min:0>2d}')


current_hour, current_min, current_sec = current_time()
if start_hour < current_hour:
    debug_print('We need to wait until tomorrow')
    wait_for_end_of_day()


time.sleep(60)        # Sleep for another minute to make sure we are past midnight
now = time.localtime()
if not args.project:
    filename = str(time.strftime("%Y-%m-%d-", now))
else:
    filename = args.project[0] + '-' + str(time.strftime("%Y-%m-%d-", now))
debug_print(f'INIT: filename is {filename}####')

##### We should have sane values, so it time to get to work.   #####
##### Loop in case there is a multi-day parameter.  If there   #####
##### is not multi-day we'll break from the loop after getting #####
##### most of the way through it.  No matter what we need to   #####
##### at least take one days worth of pictures.                #####

while True:

    waitforrighttime()      # This loop is a matter of sleeping until the correct time.
    takepicturesandstop()   # This loop takes pictures and looks for the stopping time.

    debug_print(f'This is {this_day!s} of {total_days!s} days')
    if this_day == total_days:
        debug_print(f'{this_day!s} is the same as {total_days!s}. Ending the loop.')
        break

    wait_for_end_of_day()

    debug_print('Reset the picture_number to 0000')
    last_picture_transfered = 0
    picture_number = 0     # At the end of the day we rest the picture number back to 0
    time.sleep(60)         # Sleep for another minute to make sure we are past midnight
    start_stop_time_set()  # In case of using location and running into DST changes

    now = time.localtime()
    debug_print('Set the filename to the next day')
    if not args.project:
        filename = str(time.strftime("%Y-%m-%d-", now))
    else:
        filename = args.project[0] + '-' + str(time.strftime("%Y-%m-%d-", now))
    debug_print(f'New filename: {filename}')

    this_day += 1

    ## End of while loop

debug_print('End of Program.')
