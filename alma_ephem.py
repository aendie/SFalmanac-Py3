#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#   Copyright (C) 2019  Andrew Bauer
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

# This contains one function to calculate planet magnitudes...
# ... because these are not in Skyfield 1.11

import ephem        # required only for planet magnitudes

ephem_venus   = ephem.Venus()
ephem_mars    = ephem.Mars()
ephem_jupiter = ephem.Jupiter()
ephem_saturn  = ephem.Saturn()
degree_sign= u'\N{DEGREE SIGN}'

#------------------------------------------------
#   Venus, Mars, Jupiter & Saturn calculations
#------------------------------------------------

def magnitudes(date):       # used in planetstab(m)
    # returns  magitude for the navigational planets.
    # (Skyfield 1.16 does not provide this)
    
    obs = ephem.Observer()
    
    #Venus
    obs.date = date
    ephem_venus.compute(date)
    mag_venus = u"%0.1f" %(ephem_venus.mag)
    
    #Mars
    obs.date = date
    ephem_mars.compute(date)
    mag_mars = u"%0.1f" %(ephem_mars.mag)
    
    #Jupiter
    obs.date = date
    ephem_jupiter.compute(date)
    mag_jupiter = u"%0.1f" %(ephem_jupiter.mag)
    
    #Saturn
    obs.date = date
    ephem_saturn.compute(date)
    mag_saturn = u"%0.1f" %(ephem_saturn.mag)
    
    return mag_venus,mag_mars,mag_jupiter,mag_saturn
