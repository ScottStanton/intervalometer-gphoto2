# intervelometer
This is an intervelometer using the gphoto2 software.  It is designed to be used to take pictures on an all day or multiday basis.  It can also be used for shorter intervals that you specify.

I was unable to get the gphoto2 python library to load on my system, so I installed the software and I'm running the os command from the python program. This means you'll need to have the gphoto2 software installed on your host for this to work.


Prerequisites:
These are the python packages that you will need to have installed for this to work.
*Python3
*argparse
*astral
*datetime
*time


## Usage:
```
intervalometer.py [-h] -i ### [-s HH:MM HH:MM] [-p #] [-f filename]
                         [-g xx.yyy] [-t xx.yyy] [-d]

optional arguments:
  -h, --help            show this help message and exit
  -i ###, --interval ###
                        Time between pictures in seconds.
  -n project_name, --name project_name
                        Name of the project. This will be part of the filename
                        for the pictures.
  -s HH:MM HH:MM, --startstop HH:MM HH:MM
                        List start and stop in 24 hour format. Default is to
                        start at dawn and stop at dusk
  -p #, --prepost #     How many hours before dawn to start, and after dusk to
                        stop.
  -f filename, --filename filename
                        Base filename to be used to save the files
  -m #, --multiday #    How many days to run the program for. Default is 1.
  -t xx.yyy, --latitude xx.yyy
                        Latitude to calculate dawn and dusk. Default is 35.78
  -g xx.yyy, --longitude xx.yyy
                        Longitude to calculate dawn and dusk. Default is -78.64
  -d, --debug           Show debugging messages on the command line

```

Need to add:
*specify a base directory instead of using cwd
*daily and/or hourly transfers of files to another location (sftp, scp)
