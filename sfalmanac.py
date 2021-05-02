#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

#   Copyright (C) 2021  Andrew Bauer
#   Copyright (C) 2014  Enno Rodegerdts

#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 3 of the License, or
#   (at your option) any later version.
# 
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
# 
#   You should have received a copy of the GNU General Public License along
#   with this program.  If not, see <https://www.gnu.org/licenses/>.

# Standard library imports
import os
import sys
import time
import datetime

# Local application imports
import tables
import suntables
import eventtables
import config
import increments
from alma_skyfield import init_sf


def makePDF(fn, msg = ""):
    command = 'pdflatex {}'.format(fn + ".tex")
    os.system(command)
    print("finished" + msg)
    return

def tidy_up(fn):
    os.remove(fn + ".tex")
    if os.path.isfile(fn + ".log"):
        os.remove(fn + ".log")
    if os.path.isfile(fn + ".aux"):
        os.remove(fn + ".aux")
    return


##Main##
if sys.version_info[0] < 3:
    raise Exception("Must be using Python 3")

if config.ephndx not in set([0, 1, 2]):
    print("Error - Please choose a valid ephemeris in config.py")
    sys.exit(0)

ts = init_sf()     # in alma_skyfield
d = datetime.datetime.utcnow().date()
first_day = datetime.date(d.year, d.month, d.day)

#first_day = datetime.date(2023, 6, 24)	# for testing a specific date
#d = first_day							# for testing a specific date

sday = "{:02d}".format(d.day)       # sday = "%02d" % d.day
smth = "{:02d}".format(d.month)     # smth = "%02d" % d.month
syr  = "{}".format(d.year)          # syr  = "%s" % d.year
symd = syr + smth + sday
sdmy = sday + "." + smth + "." + syr
yrmin = config.ephemeris[config.ephndx][1]
yrmax = config.ephemeris[config.ephndx][2]

if config.pgsz not in set(['A4', 'Letter']):
    print("Please choose a valid paper size in config.py")
    sys.exit(0)

s = input("""\nWhat do you want to create?:\n
    1   Nautical Almanac   (for a year)
    2   Sun tables only    (for a year)
    3   Event Time tables  (for a year)
    4   Nautical almanac   -  6 days from today
    5   Sun tables only    - 30 days from today
    6   Event Time tables  -  6 days from today
    7   "Increments and Corrections" tables (static data)
""")

if s in set(['1', '2', '3', '4', '5', '6', '7']):
    if int(s) < 4:
        print("Please enter the desired year")
        years = input("  as yyyy ... or the FIRST and LAST year as yyyy-yyyy\n")
        if len(years)== 4:
            yearfr = years
            yearto = years
        elif len(years) == 9 and years[4] == '-':
            yearfr = years[0:4]
            yearto = years[5:9]
        else:
            print("Error! Invalid format")
            sys.exit(0)
        
        if str(yearfr).isnumeric():
            if yrmin <= int(yearfr) <= yrmax:
                first_day = datetime.date(int(yearfr), 1, 1)
            else:
                print("!! Please pick a year between {} and {} !!".format(yrmin,yrmax))
                sys.exit(0)
        else:
            print("Error! First year is not numeric")
            sys.exit(0)

        if str(yearto).isnumeric():
            if yrmin <= int(yearto) <= yrmax:
                first_day_to = datetime.date(int(yearto), 1, 1)
            else:
                print("!! Please pick a year between {} and {} !!".format(yrmin,yrmax))
                sys.exit(0)
            if int(yearto) < int(yearfr):
                print("Error! The LAST year must be later than the FIRST year")
                sys.exit(0)
        else:
            print("Error! Last year is not numeric")
            sys.exit(0)

    if s != '3' and int(s) <= 5:
        tsin = input("""What table style is required?:\n
        t   Traditional
        m   Modern
""")
        ff = '_'
        DecFmt = ''
        config.tbls = tsin[0:1]	# table style
        config.decf = tsin[1:2]	# Declination format
        if config.tbls != 'm':
            config.tbls = ''		# anything other than 'm' is traditional
            ff = ''
        if config.decf != '+':		# Positive/Negative Declinations
            config.decf = ''		# USNO format for Declination
        else:
            DecFmt = '[old]'

    if s == '1':        # Nautical Almanac (for a year)
        print("Take a break - this computer needs some time for cosmic meditation.")
##        config.initLOG()		# initialize log file
        for yearint in range(int(yearfr),int(yearto)+1):
            start = time.time()
            config.stopwatch = 0.0      # 00000
            config.moonDataSeeks = 0
            config.moonDataFound = 0
            config.moonHorizonSeeks = 0
            config.moonHorizonFound = 0
            year = "{:4d}".format(yearint)  # year = "%4d" %yearint
            msg = "\nCreating the nautical almanac for the year {}".format(year)
            print(msg)
##            config.writeLOG(msg)
            first_day = datetime.date(yearint, 1, 1)
            fn = "almanac{}{}".format(ff,year+DecFmt)
            outfile = open(fn + ".tex", mode="w", encoding="utf8")
            outfile.write(tables.almanac(first_day,122))
            outfile.close()
            stop = time.time()
            msg = "execution time = {:0.2f} seconds".format(stop-start) # msg = "execution time = %0.2f seconds" %(stop-start)
            print(msg)
##            config.writeLOG("\n\n" + msg + "\n")
            msg2 = "stopwatch      = {:0.2f} seconds".format(config.stopwatch)
            print(msg2)                 # 00000
            msg3 = "(stopwatch shows the time spent in the 'almanac.find_discrete' function)"
            print(msg3)
            msg4 = "Moon daily data found in transient store = {} of {}".format(config.moonDataFound, config.moonDataSeeks)
            print(msg4)
            msg5 = "Moon continuously above/below horizon state found in transient store = {} of {}".format(config.moonHorizonFound, config.moonHorizonSeeks)
            print(msg5)
            print()
            makePDF(fn, " creating nautical almanac for {}".format(year))
            tidy_up(fn)
##        config.closeLOG()     # close log after the for-loop

    elif s == '2':      # Sun Tables (for a year)
        for yearint in range(int(yearfr),int(yearto)+1):
            year = "{:4d}".format(yearint)  # year = "%4d" %yearint
            msg = "\nCreating the sun tables for the year {}\n".format(year)
            print(msg)
            first_day = datetime.date(yearint, 1, 1)
            fn = "sunalmanac{}{}".format(ff,year+DecFmt)
            outfile = open(fn + ".tex", mode="w", encoding="utf8")
            outfile.write(suntables.almanac(first_day,25))
            outfile.close()
            makePDF(fn, " creating sun tables for {}".format(year))
            tidy_up(fn)

    elif s == '3':      # Event Time tables  (for a year)
        print("Take a break - this computer needs some time for cosmic meditation.")
        for yearint in range(int(yearfr),int(yearto)+1):
            start = time.time()
            config.stopwatch = 0.0      # 00000
            year = "{:4d}".format(yearint)  # year = "%4d" %yearint
            msg = "\nCreating the event time tables for the year {}".format(year)
            print(msg)
            first_day = datetime.date(yearint, 1, 1)
            fn = "event-times{}".format(year)
            outfile = open(fn + ".tex", mode="w", encoding="utf8")
            outfile.write(eventtables.maketables(first_day,183))
            outfile.close()
            stop = time.time()
            msg = "execution time = {:0.2f} seconds".format(stop-start) # msg = "execution time = %0.2f seconds" %(stop-start)
            print(msg)
            print()
            makePDF(fn, " creating event time tables for {}".format(year))
            tidy_up(fn)

    elif s == '4':      # Nautical almanac   -  6 days from today
##        config.initLOG()		# initialize log file
        start = time.time()
        config.stopwatch = 0.0      # 00000
        msg = "\nCreating nautical almanac tables - from {}\n".format(sdmy)
        print(msg)
        fn = "almanac{}{}".format(ff,symd+DecFmt)
        outfile = open(fn + ".tex", mode="w", encoding="utf8")
        outfile.write(tables.almanac(first_day,2))
        outfile.close()
        stop = time.time()
        msg1 = "execution time = {:0.2f} seconds".format(stop-start)
        print(msg1)
        msg2 = "stopwatch      = {:0.2f} seconds".format(config.stopwatch)
        print(msg2)                 # 00000
        msg3 = "(stopwatch shows the time spent in the 'almanac.find_discrete' function)"
        print(msg3)
        msg4 = "Moon daily data found in transient store = {} of {}".format(config.moonDataFound, config.moonDataSeeks)
        print(msg4)
        msg5 = "Moon continuously above/below horizon state found in transient store = {} of {}".format(config.moonHorizonFound, config.moonHorizonSeeks)
        print(msg5)
        print()
##        config.writeLOG('\n\n' + msg1 + '\n' + msg2 + '\n' + msg3)
##        config.closeLOG()
        makePDF(fn)
        tidy_up(fn)

    elif s == '5':      # Sun tables only    - 30 days from today
        msg = "\nCreating the sun tables - from {}\n".format(sdmy)
        print(msg)
        fn = "sunalmanac{}{}".format(ff,symd+DecFmt)
        outfile = open(fn + ".tex", mode="w", encoding="utf8")
        outfile.write(suntables.almanac(first_day,2))
        outfile.close()
        makePDF(fn)
        tidy_up(fn)

    elif s == '6':      # Event Time tables  -  6 days from today
        msg = "\nCreating event time tables - from {}\n".format(sdmy)
        print(msg)
        fn = "event-times{}".format(symd)
        outfile = open(fn + ".tex", mode="w", encoding="utf8")
        outfile.write(eventtables.maketables(first_day,3))
        outfile.close()
        makePDF(fn)
        tidy_up(fn)

    elif s == '7':
        msg = "\nCreating the Increments and Corrections tables\n"
        print(msg)
        fn = "inc"
        outfile = open(fn + ".tex", mode="w", encoding="utf8")
        outfile.write(increments.makelatex())
        outfile.close()
        makePDF(fn)
        tidy_up(fn)

else:
    print("Error! Choose 1, 2, 3, 4, 5, 6 or 7")
