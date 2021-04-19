# Intervelometer-gphoto2
This is an intervelometer using the gphoto2 software.  It is designed to be used to take pictures on an all day or multiday basis.  It can also be used for shorter intervals that you specify.

I was unable to get the gphoto2 python library to load on my system, so I installed the software and I'm running the os command from the python program. This means you'll need to have the gphoto2 software installed on your host for this to work.


## Prerequisites:
* Python 3.x is required to use this program.
* The astral python package is required. 


## Usage:
```
usage: intervalometer.py [-h] -i ### -p project [-s HH:MM HH:MM] [-o #] [-m #] [-d directory] [-t xx.yyy -g xx.yyy] [-f] [-v]

optional arguments:
  -h, --help                       show this help message and exit
  -i ###, --interval ###           REQUIRED:  Time between pictures in seconds.
  -p project, --project project    REQUIRED: Name of the project you are taking pictures for. This directory will be created if it doesn't exist.
  -s HH:MM HH:MM, --startstop HH:MM HH:MM
                                   List start and stop time in 24 hour format. If not used, the default is to start at dawn and stop at dusk.
  -o #, --offset #                 How many hours before dawn to start, and after dusk to stop.  Cannot be used with --startstop.
  -m #, --multiday #               How many days to run the program for. Default is 1.
  -d directory, --dir directory    Full directory path to save the project to. Defaults to /data.
  -t xx.yyy, --latitude xx.yyy     Latitude to calculate dawn and dusk. Default is 35.78
  -g xx.yyy, --longitude xx.yyy    Longitude to calculate dawn and dusk. Default is -78.64
  -f, --faux                       Use the gfauxto2 command to simulate taking pictures. Will create empty files instead of taking pictures.
  -v, --verbose                    Show debugging messages on the command line

```

## Need to add:
* daily and/or hourly transfers of files to another location (sftp, scp)
