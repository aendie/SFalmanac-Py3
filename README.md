# SFalmanac-Py3

SFalmanac-Py3 is a Python 3.7 script that creates the daily pages of the Nautical Almanac. These are tables that are needed for celestial navigation with a sextant. Although you are strongly advised to purchase the official Nautical Almanac, this program will reproduce the tables with no warranty or guarantee of accuracy.

As opposed to the older PyEphem astronomy library, this uses the newer Skyfield astronomy package: https://rhodesmill.org/skyfield/

NOTE: two scripts are included (both can be run): 'sfalmanac.py' and 'increments.py'  
NOTE: a Python 2.7 script with identical functionality can be found at:  https://github.com/aendie/SFalmanac-Py2  
NOTE: a [PyEphem](https://rhodesmill.org/pyephem/) version of SFalmanac is available here:
https://github.com/aendie/Py3almanac

An aim of this development was to maintain:

* **identical PDF output formatting with a similar control program**
	 It is then possible to display both generated tables (from PyEphem and Skyfield)
	 and compare what has changed by flipping between the two tabs in the PDF reader.
	 Anything that has changed flashes, thereby drawing your attention to it.
	 This crude and simple method is quite effective in highlihgting data that
	 might need further attention.

The results have been crosschecked with USNO data to some extent.  
(However, constructive feedback is always appreciated.)

## Requirements

&nbsp;&nbsp;&nbsp;&nbsp;Most of the computation is done by the free Pyephem library.  
&nbsp;&nbsp;&nbsp;&nbsp;Typesetting is done by TeX/LaTeX so you first need to install:

* Python v3.4 or higher (3.7 is recommended)
* PyEphem
* TeX/LaTeX&nbsp;&nbsp;or&nbsp;&nbsp;MiKTeX
  

### INSTALLATION GUIDELINES on Windows 10:

&nbsp;&nbsp;&nbsp;&nbsp;Install Python 3.7 and MiKTeX from https://miktex.org/  
&nbsp;&nbsp;&nbsp;&nbsp;Using Command Prompt, go to your Python folder and run, e.g.:

&nbsp;&nbsp;&nbsp;&nbsp;**cd C:\\Python37-64**  
&nbsp;&nbsp;&nbsp;&nbsp;**python -m pip install --upgrade pip**  
&nbsp;&nbsp;&nbsp;&nbsp;... for a first install:  
&nbsp;&nbsp;&nbsp;&nbsp;**python -m pip install pyephem**  
&nbsp;&nbsp;&nbsp;&nbsp;... if already installed, check for upgrade explicitly:  
&nbsp;&nbsp;&nbsp;&nbsp;**python -m pip install --upgrade pyephem**

&nbsp;&nbsp;&nbsp;&nbsp;Put the Pyalmanac files in a new folder, go there and start with:  
&nbsp;&nbsp;&nbsp;&nbsp;**py -3 pyalmanac.py**


### INSTALLATION GUIDELINES on Linux:

&nbsp;&nbsp;&nbsp;&nbsp;Install your platform#'s Python- and LaTeX distribution.  
&nbsp;&nbsp;&nbsp;&nbsp;Remember to choose python 3.4 or higher and install all develpment header files.  
&nbsp;&nbsp;&nbsp;&nbsp;Run at the command line:

&nbsp;&nbsp;&nbsp;&nbsp;**pip install pyephem**

&nbsp;&nbsp;&nbsp;&nbsp;Put the Pyalmanac files in any directory and start with:  
&nbsp;&nbsp;&nbsp;&nbsp;**python pyalmanac**  
&nbsp;&nbsp;&nbsp;&nbsp;or  
&nbsp;&nbsp;&nbsp;&nbsp;**./pyalmanac**


### INSTALLATION GUIDELINES on MAC:

&nbsp;&nbsp;&nbsp;&nbsp;Every Mac comes with python preinstalled.  
&nbsp;&nbsp;&nbsp;&nbsp;(Please choose this version of Pyalmanac if Python 3.* is installed.)  
&nbsp;&nbsp;&nbsp;&nbsp;You need to install the PyEphem library to use Pyalmanac.  
&nbsp;&nbsp;&nbsp;&nbsp;Type the following commands at the commandline (terminal app):

&nbsp;&nbsp;&nbsp;&nbsp;**sudo easy_install pip**  
&nbsp;&nbsp;&nbsp;&nbsp;**pip install pyephem**

&nbsp;&nbsp;&nbsp;&nbsp;If this command fails, your Mac asks you if you would like to install the header files.  
&nbsp;&nbsp;&nbsp;&nbsp;Do so - you do not need to install the full IDE - and try again.

&nbsp;&nbsp;&nbsp;&nbsp;Install TeX/LaTeX from http://www.tug.org/mactex/

&nbsp;&nbsp;&nbsp;&nbsp;Now you are almost ready. Put the Pyalmanac files in any directory and start with:  
&nbsp;&nbsp;&nbsp;&nbsp;**python pyalmanac**  
&nbsp;&nbsp;&nbsp;&nbsp;or  
&nbsp;&nbsp;&nbsp;&nbsp;**./pyalmanac**
