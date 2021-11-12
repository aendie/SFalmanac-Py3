#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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

# NOTE: the new format statement requires a literal '{' to be entered as '{{',
#       and a literal '}' to be entered as '}}'. The old '%' format specifier
#       will be removed from Python at some later time. See:
# https://docs.python.org/3/whatsnew/3.0.html#pep-3101-a-new-approach-to-string-formatting

# NOTE: As mentioned by Klaus Höppner in "Typesetting tables with LaTeX", 'tabular*'
#       style tables often (surprisingly) expand the space between columns.
#       Switiching to 'tabular' style has the effect that the first column 
#       varies in width, e.g. as "Wed" is wider than "Fri". 
#       Also column 'v' in the Moon table, e.g. e.g. 6.9' versus 15.3'.
#       Also column 'd' in the Moon table, e.g. e.g. -8.2' versus -13.9'.
#       'Tabular' table style normally permits column width specification only for 
#       (left-justified) paragraph column content (with the 'p' column specifier).
#       A workaround is to use 'tabularx' table style and set the custom width
#       to the maximum column width on variable column-width columns. However -
#       \multicolumn entries must not cross any X-column, so it's out of question.
#       A solution to extending the column specifiers on a 'tabular' table style
#       with left-, center- and right-justified data plus a column width specifier
#       is possible: https://de.wikibooks.org/wiki/LaTeX-W%C3%B6rterbuch:_tabular
#       This works, but again increases the overall table width unnecessarily.
#       Conclusion/Resolution:
#       The following code now uses the 'tabular' table style without any
#       column width specifiers - thus table widths vary slightly from page to page.

# Standard library imports
from datetime import datetime, timedelta
import sys			# required for .stdout.write()
from math import cos as cos
from math import copysign as copysign
from math import pi as pi

# Local application imports
from alma_ephem import magnitudes
import config
if config.MULTIpr:  # in multi-processing mode ...
    # ! DO NOT PLACE imports IN CONDITIONAL 'if'-STATEMENTS WHEN MULTI-PROCESSING !
    import multiprocessing as mp
    from functools import partial
    # ... following is still required for SINGLE-PROCESSING (in multi-processing mode):
    from alma_skyfield import ariesGHA, venusGHA, marsGHA, jupiterGHA, saturnGHA, sunGHA, moonGHA, moonVD, sunSD, moonSD, vdm_Venus, vdm_Mars, vdm_Jupiter, vdm_Saturn, ariestransit, stellar_info, planetstransit, moonage, moonphase, equation_of_time, getDUT1, find_new_moon
    # ... following is required for MULTI-PROCESSING:
    from mp_nautical import mp_twilight, mp_moonrise_set, mp_planetstransit, hor_parallax, mp_planetGHA, mp_sunmoon
else:
    # ... following is required for SINGLE-PROCESSING:
    from alma_skyfield import ariesGHA, venusGHA, marsGHA, jupiterGHA, saturnGHA, sunGHA, moonGHA, moonVD, sunSD, moonSD, vdm_Venus, vdm_Mars, vdm_Jupiter, vdm_Saturn, ariestransit, stellar_info, planetstransit, twilight, moonrise_set, moonage, moonphase, equation_of_time, getDUT1, find_new_moon


UpperLists = [[], [], []]    # moon GHA per hour for 3 days
LowerLists = [[], [], []]    # moon colong GHA per hour for 3 days

#----------------------
#   internal methods
#----------------------

def fmtdate(d):
    if config.pgsz == 'Letter': return d.strftime("%m/%d/%Y")
    return d.strftime("%d.%m.%Y")

def fmtdates(d1,d2):
    if config.pgsz == 'Letter': return d1.strftime("%m/%d/%Y") + " - " + d2.strftime("%m/%d/%Y")
    return d1.strftime("%d.%m.%Y") + " - " + d2.strftime("%d.%m.%Y")

def buildUPlists(n, ghaSoD, ghaPerHour, ghaEoD):
    # build list of hourly GHA values with modified start and end time to
    #  account for rounding times to the minute where 23:59:>30 rounds up
    #  00:00 the next day.
    UpperLists[n] = [-1.0 for x in range(25)]
    UpperLists[n][0] = ghaSoD
    for i in range(23):
        UpperLists[n][i+1] = ghaPerHour[i+1]
    UpperLists[n][24] = ghaEoD
    return

def buildLOWlists(n, ghaSoD, ghaPerHour, ghaEoD):
    # build list of hourly GHA colong values with modified start and end
    #   time to account for rounding times to the minute where 23:59:>30
    #   rounds up 00:00 the next day.
    LowerLists[n] = [-1.0 for x in range(25)]
    LowerLists[n][0] = GHAcolong(ghaSoD)
    for i in range(23):
        LowerLists[n][i+1] = GHAcolong(ghaPerHour[i+1])
    LowerLists[n][24] = GHAcolong(ghaEoD)
    return

def GHAcolong(gha):
    # return the colongitude, e.g. 270° returns 90° and 90° returns 270°
    coGHA = gha + 180
    while coGHA > 360:
        coGHA = coGHA - 360
    return coGHA

def declCompare(prev_deg, curr_deg, next_deg, hr):
    # for Declinations only...
    # decide if to print N/S; decide if to print degrees
    # note: the first three arguments are declinations in degrees (float)
    prNS = False
    prDEG = False
    psign = copysign(1.0,prev_deg)
    csign = copysign(1.0,curr_deg)
    nsign = copysign(1.0,next_deg)
    pdeg = abs(prev_deg)
    cdeg = abs(curr_deg)
    ndeg = abs(next_deg)
    pdegi = int(pdeg)
    cdegi = int(cdeg)
    ndegi = int(ndeg)
    pmin = round((pdeg-pdegi)*60, 1)	# minutes (float), rounded to 1 decimal place
    cmin = round((cdeg-cdegi)*60, 1)	# minutes (float), rounded to 1 decimal place
    nmin = round((ndeg-ndegi)*60, 1)	# minutes (float), rounded to 1 decimal place
    pmini = int(pmin)
    cmini = int(cmin)
    nmini = int(nmin)
    if pmini == 60:
        pmin -= 60
        pdegi += 1
    if cmini == 60:
        cmin -= 60
        cdegi += 1
    if nmini == 60:
        nmin -= 60
        ndegi += 1
    # now we have the values in degrees+minutes as printed

    if hr%6 == 0:
        prNS = True			# print N/S for hour = 0, 6, 12, 18
    else:
        if psign != csign:
            prNS = True		# print N/S if previous sign different
    if hr < 23:
        if csign != nsign:
            prNS = True		# print N/S if next sign different
    if prNS == False:
        if pdegi != cdegi:
            prDEG = True	# print degrees if changed since previous value
        if cdegi != ndegi:
            prDEG = True	# print degrees if next value is changed
    else:
        prDEG= True			# print degrees is N/S to be printed
    return prNS, prDEG

def NSdecl(deg, hr, printNS, printDEG, modernFMT):
    # reformat degrees latitude to Ndd°mm.m or Sdd°mm.m
    if deg[0:1] == '-':
        hemisph = 'S'
        deg = deg[1:]
    else:
        hemisph = 'N'
    if not(printDEG):
        deg = deg[10:]	# skip the degrees (always dd°mm.m) - note: the degree symbol '$^\circ$' is eight bytes long
        if (hr+3)%6 == 0:
            deg = r'''\raisebox{0.24ex}{\boldmath$\cdot$~\boldmath$\cdot$~~}''' + deg
    if modernFMT:
        if printNS or hr%6 == 0:
            sdeg = r'''\textcolor{{blue}}{{{}}}'''.format(hemisph) + deg
        else:
            sdeg = deg
    else:
        if printNS or hr%6 == 0:
            sdeg = r'''\textbf{{{}}}'''.format(hemisph) + deg
        else:
            sdeg = deg
    #print("sdeg: ", sdeg)
    return sdeg

def NSdeg(deg, modern=False, hr=0, forceNS=False):
    # reformat degrees latitude to Ndd°mm.m or Sdd°mm.m
    if deg[0:1] == '-':
        hemisph = 'S'
        deg = deg[1:]
    else:
        hemisph = 'N'
    if modern:
        if forceNS or hr%6 == 0:
            sdeg = r'''\textcolor{{blue}}{{{}}}'''.format(hemisph) + deg
        else:
            sdeg = deg
    else:
        if forceNS or hr%6 == 0:
            sdeg = r'''\textbf{{{}}}'''.format(hemisph) + deg
        else:
            sdeg = deg
    return sdeg, hemisph

def lunatikz(phase):
    # argument: moon phase (0:new to π:full to 2π:new)
    # returns the code for a moon image overlaid with a shadow (pardon the function name)
    f      = 0.01     # empirical fudge factor to position moon's shadow exactly over image
    radius = 0.375    # moon image radius (cm)
    xstart = radius + f
    diam   = 0.75     # moon image diameter (cm)
    top    = diam + f # top of moon (cm)
    bottom = 0.0 + f  # bottom of moon (cm)
    if phase < pi*0.5:    # new moon to 1st quarter
        ystart = top
        fr_angle = 90           # trace a semicircle anticlockwise from top to bottom
        to_angle = 270
        ret_angle = -90         # trace an ellipse anticlockwise from bottom to top
        end_angle = 90
        xradius = cos(phase) * radius
    elif phase < pi:      # 1st quarter to full moon
        ystart = top
        fr_angle = 90           # trace a semicircle anticlockwise from top to bottom
        to_angle = 270
        ret_angle = 270         # trace an ellipse clockwise from bottom to top
        end_angle = 90
        xradius = abs(cos(phase)) * radius
    elif phase < pi*1.5:  # full moon to 3rd quarter
        ystart = bottom
        fr_angle = -90          # trace a semicircle anticlockwise from bottom to top
        to_angle = 90
        ret_angle = 90          # trace an ellipse clockwise from top to bottom
        end_angle = -90
        xradius = abs(cos(phase)) * radius
    else:                       # 3rd quarter to new moon
        ystart = bottom
        fr_angle = -90          # trace a semicircle anticlockwise from bottom to top
        to_angle = 90
        ret_angle = 90          # trace an ellipse anticlockwise from top to bottom
        end_angle = 270
        xradius = cos(phase) * radius

    if config.dockerized:   # DOCKER ONLY
        fn = "../croppedmoon.png"
    else:
        fn = "croppedmoon.png"

    tikz = r'''\multicolumn{{1}}{{|c|}}{{\multirow{{3}}{{*}}
{{\begin{{tikzpicture}}
\node[anchor=south west,inner sep=0] at (0,0) {{\includegraphics[width=0.75cm]{{{}}}}};
\path [fill=darknight, opacity=0.75] ({:5.3f},{:5.3f}) arc [x radius=0.375, y radius=0.375, start angle={:d}, end angle={:d}]  arc [x radius={:f}, y radius=0.375, start angle={:d}, end angle={:d}];
\end{{tikzpicture}}}}}}\\
'''.format(fn, xstart, ystart, fr_angle, to_angle, xradius, ret_angle, end_angle)
    return tikz

def double_events_found(m1, m2):
    # check for two moonrise/moonset events on the same day & latitude
    dbl = False
    for i in range(len(m1)):
        if m2[i] != '--:--':
            dbl = True
    return dbl

# >>>>>>>>>>>>>>>>>>>>>>>>
def mp_planetGHA_worker(date, obj, ts):
    #print(" mp_planetGHA_worker Start  {}".format(obj))
    gha = mp_planetGHA(date, obj, ts)    # ===>>> mp_nautical.py
    #print(" mp_planetGHA_worker Finish {}".format(obj))
    return gha      # return list for four planets and Aries

def planetstab(date, ts):
    # generates a LaTeX table for the navigational plantets (traditional style)
    # OLD: \begin{tabular*}{0.74\textwidth}[t]{@{\extracolsep{\fill}}|c|r|rr|rr|rr|rr|}
    tab = r'''\noindent
\setlength{\tabcolsep}{5.8pt}  % default 6pt
\begin{tabular}[t]{|c|r|rr|rr|rr|rr|}
\multicolumn{1}{c}{\normalsize{}} & \multicolumn{1}{c}{\normalsize{Aries}} &  \multicolumn{2}{c}{\normalsize{Venus}}& \multicolumn{2}{c}{\normalsize{Mars}} & \multicolumn{2}{c}{\normalsize{Jupiter}} & \multicolumn{2}{c}{\normalsize{Saturn}}\\
'''
    # note: 74% table width above removes "Overfull \hbox (1.65279pt too wide)"
    n = 0
    while n < 3:
        tab = tab + r'''\hline
\rule{{0pt}}{{2.4ex}}\textbf{{{}}} & \multicolumn{{1}}{{c|}}{{\textbf{{GHA}}}} & \multicolumn{{1}}{{c}}{{\textbf{{GHA}}}} & \multicolumn{{1}}{{c|}}{{\textbf{{Dec}}}} & \multicolumn{{1}}{{c}}{{\textbf{{GHA}}}} & \multicolumn{{1}}{{c|}}{{\textbf{{Dec}}}} & \multicolumn{{1}}{{c}}{{\textbf{{GHA}}}} & \multicolumn{{1}}{{c|}}{{\textbf{{Dec}}}} & \multicolumn{{1}}{{c}}{{\textbf{{GHA}}}} & \multicolumn{{1}}{{c|}}{{\textbf{{Dec}}}}\\
\hline\rule{{0pt}}{{2.6ex}}\noindent
'''.format(date.strftime("%a"))

        if config.MULTIpr and config.WINpf:
            global pool
            # multiprocess 'SHA + transit times' simultaneously
            objlist = ['aries', 'venus', 'mars', 'jupiter', 'saturn']
            partial_func2 = partial(mp_planetGHA_worker, date, ts)
            listofGHA = pool.map(partial_func2, objlist, 1)     # RECOMMENDED: chunksize = 1
            aGHA = listofGHA[0][0]
            vGHA = listofGHA[1][0]
            vDEC = listofGHA[1][1]
            vDEG = listofGHA[1][2]
            mGHA = listofGHA[2][0]
            mDEC = listofGHA[2][1]
            mDEG = listofGHA[2][2]
            jGHA = listofGHA[3][0]
            jDEC = listofGHA[3][1]
            jDEG = listofGHA[3][2]
            sGHA = listofGHA[4][0]
            sDEC = listofGHA[4][1]
            sDEG = listofGHA[4][2]
        else:
            aGHA             = ariesGHA(date)
            vGHA, vDEC, vDEG = venusGHA(date)
            mGHA, mDEC, mDEG = marsGHA(date)
            jGHA, jDEC, jDEG = jupiterGHA(date)
            sGHA, sDEC, sDEG = saturnGHA(date)
        h = 0

        if config.decf != '+':	# USNO format for Declination
            while h < 24:
                if h > 0:
                    prevDECv = vDEG[h-1]
                    prevDECm = mDEG[h-1]
                    prevDECj = jDEG[h-1]
                    prevDECs = sDEG[h-1]
                else:
                    prevDECv = vDEG[0]		# hour -1 = hour 0
                    prevDECm = mDEG[0]		# hour -1 = hour 0
                    prevDECj = jDEG[0]		# hour -1 = hour 0
                    prevDECs = sDEG[0]		# hour -1 = hour 0
                if h < 23:
                    nextDECv = vDEG[h+1]
                    nextDECm = mDEG[h+1]
                    nextDECj = jDEG[h+1]
                    nextDECs = sDEG[h+1]
                else:
                    nextDECv = vDEG[23]	    # hour 24 = hour 23
                    nextDECm = mDEG[23]	    # hour 24 = hour 23
                    nextDECj = jDEG[23]	    # hour 24 = hour 23
                    nextDECs = sDEG[23]	    # hour 24 = hour 23

                # format declination checking for hemisphere change
                printNS, printDEG = declCompare(prevDECv,vDEG[h],nextDECv,h)
                vdec = NSdecl(vDEC[h],h,printNS,printDEG,False)

                printNS, printDEG = declCompare(prevDECm,mDEG[h],nextDECm,h)
                mdec = NSdecl(mDEC[h],h,printNS,printDEG,False)

                printNS, printDEG = declCompare(prevDECj,jDEG[h],nextDECj,h)
                jdec = NSdecl(jDEC[h],h,printNS,printDEG,False)

                printNS, printDEG = declCompare(prevDECs,sDEG[h],nextDECs,h)
                sdec = NSdecl(sDEC[h],h,printNS,printDEG,False)

                line = "{} & {} & {} & {} & {} & {} & {} & {} & {} & {}".format(h,aGHA[h],vGHA[h],vdec,mGHA[h],mdec,jGHA[h],jdec,sGHA[h],sdec)
                lineterminator = r'''\\
'''
                if h < 23 and (h+1)%6 == 0:
                    lineterminator = r'''\\[2Pt]
'''
                tab = tab + line + lineterminator
                h += 1

        else:			# Positive/Negative Declinations
            while h < 24:
                line = r'''{} & {} & {} & {} & {} & {} & {} & {} & {} & {}'''.format(h,aGHA[h],vGHA[h],vDEC[h],mGHA[h],mDEC[h],jGHA[h],jDEC[h],sGHA[h],sDEC[h])
                lineterminator = r'''\\
'''
                if h < 23 and (h+1)%6 == 0:
                    lineterminator = r'''\\[2Pt]
'''
                tab = tab + line + lineterminator
                h += 1

        mag_v, mag_m, mag_j, mag_s = magnitudes(date)   # magnitudes from Ephem
        RAc_v, Dc_v, mag_v = vdm_Venus(date)
        RAc_m, Dc_m = vdm_Mars(date)
        RAc_j, Dc_j, mag_j = vdm_Jupiter(date)
        RAc_s, Dc_s = vdm_Saturn(date)
        tab = tab + r'''\hline
\multicolumn{{2}}{{|c|}}{{\rule{{0pt}}{{2.4ex}}Mer.pass. {}}} & 
\multicolumn{{2}}{{c|}}{{\(\nu\) {}$'$ \emph{{d}} {}$'$ m {}}} & 
\multicolumn{{2}}{{c|}}{{\(\nu\) {}$'$ \emph{{d}} {}$'$ m {}}} & 
\multicolumn{{2}}{{c|}}{{\(\nu\) {}$'$ \emph{{d}} {}$'$ m {}}} & 
\multicolumn{{2}}{{c|}}{{\(\nu\) {}$'$ \emph{{d}} {}$'$ m {}}}\\
\hline
\multicolumn{{10}}{{c}}{{}}\\
'''.format(ariestransit(date+timedelta(days=1)),RAc_v,Dc_v,mag_v,RAc_m,Dc_m,mag_m,RAc_j,Dc_j,mag_j,RAc_s,Dc_s,mag_s)
        n += 1
        date += timedelta(days=1)
    tab = tab + r'''\end{tabular}
'''
    return tab

# >>>>>>>>>>>>>>>>>>>>>>>>
def planetstabm(date, ts):
    # generates a LaTeX table for the navigational plantets (modern style)

    tab = r'''\vspace{6Pt}\noindent
\renewcommand{\arraystretch}{1.1}
\setlength{\tabcolsep}{4pt}  % default 6pt
\begin{tabular}[t]{crcrrcrrcrrcrr}
\multicolumn{1}{c}{\normalsize{h}} & 
\multicolumn{1}{c}{\normalsize{Aries}} & & 
\multicolumn{2}{c}{\normalsize{Venus}}& & 
\multicolumn{2}{c}{\normalsize{Mars}} & & 
\multicolumn{2}{c}{\normalsize{Jupiter}} & & 
\multicolumn{2}{c}{\normalsize{Saturn}}\\
\cmidrule{2-2} \cmidrule{4-5} \cmidrule{7-8} \cmidrule{10-11} \cmidrule{13-14}'''
    n = 0
    while n < 3:
        tab = tab + r'''
\multicolumn{{1}}{{c}}{{\textbf{{{}}}}} & \multicolumn{{1}}{{c}}{{\textbf{{GHA}}}} && 
\multicolumn{{1}}{{c}}{{\textbf{{GHA}}}} & \multicolumn{{1}}{{c}}{{\textbf{{Dec}}}} &&  \multicolumn{{1}}{{c}}{{\textbf{{GHA}}}} & \multicolumn{{1}}{{c}}{{\textbf{{Dec}}}} &&  \multicolumn{{1}}{{c}}{{\textbf{{GHA}}}} & \multicolumn{{1}}{{c}}{{\textbf{{Dec}}}} &&  \multicolumn{{1}}{{c}}{{\textbf{{GHA}}}} & \multicolumn{{1}}{{c}}{{\textbf{{Dec}}}}\\
'''.format(date.strftime("%a"))
        if config.MULTIpr and config.WINpf:
            # multiprocess 'SHA + transit times' simultaneously
            objlist = ['aries', 'venus', 'mars', 'jupiter', 'saturn']
            partial_func2 = partial(mp_planetGHA_worker, date, ts)
            listofGHA = pool.map(partial_func2, objlist, 1)     # RECOMMENDED: chunksize = 1
            aGHA = listofGHA[0][0]
            vGHA = listofGHA[1][0]
            vDEC = listofGHA[1][1]
            vDEG = listofGHA[1][2]
            mGHA = listofGHA[2][0]
            mDEC = listofGHA[2][1]
            mDEG = listofGHA[2][2]
            jGHA = listofGHA[3][0]
            jDEC = listofGHA[3][1]
            jDEG = listofGHA[3][2]
            sGHA = listofGHA[4][0]
            sDEC = listofGHA[4][1]
            sDEG = listofGHA[4][2]
        else:
            aGHA             = ariesGHA(date)
            vGHA, vDEC, vDEG = venusGHA(date)
            mGHA, mDEC, mDEG = marsGHA(date)
            jGHA, jDEC, jDEG = jupiterGHA(date)
            sGHA, sDEC, sDEG = saturnGHA(date)
        h = 0

        if config.decf != '+':	# USNO format for Declination
            while h < 24:
                band = int(h/6)
                group = band % 2
                if h > 0:
                    prevDECv = vDEG[h-1]
                    prevDECm = mDEG[h-1]
                    prevDECj = jDEG[h-1]
                    prevDECs = sDEG[h-1]
                else:
                    prevDECv = vDEG[0]		# hour -1 = hour 0
                    prevDECm = mDEG[0]		# hour -1 = hour 0
                    prevDECj = jDEG[0]		# hour -1 = hour 0
                    prevDECs = sDEG[0]		# hour -1 = hour 0
                if h < 23:
                    nextDECv = vDEG[h+1]
                    nextDECm = mDEG[h+1]
                    nextDECj = jDEG[h+1]
                    nextDECs = sDEG[h+1]
                else:
                    nextDECv = vDEG[23]	    # hour 24 = hour 23
                    nextDECm = mDEG[23]	    # hour 24 = hour 23
                    nextDECj = jDEG[23]	    # hour 24 = hour 23
                    nextDECs = sDEG[23]	    # hour 24 = hour 23

                # format declination checking for hemisphere change
                printNS, printDEG = declCompare(prevDECv,vDEG[h],nextDECv,h)
                vdec = NSdecl(vDEC[h],h,printNS,printDEG,True)

                printNS, printDEG = declCompare(prevDECm,mDEG[h],nextDECm,h)
                mdec = NSdecl(mDEC[h],h,printNS,printDEG,True)

                printNS, printDEG = declCompare(prevDECj,jDEG[h],nextDECj,h)
                jdec = NSdecl(jDEC[h],h,printNS,printDEG,True)

                printNS, printDEG = declCompare(prevDECs,sDEG[h],nextDECs,h)
                sdec = NSdecl(sDEC[h],h,printNS,printDEG,True)

                line = r'''\color{{blue}}{{{}}} & '''.format(h)
                line = line + r'''{} && {} & {} && {} & {} && {} & {} && {} & {} \\
'''.format(aGHA[h],vGHA[h],vdec,mGHA[h],mdec,jGHA[h],jdec,sGHA[h],sdec)
                if group == 1:
                    tab = tab + r'''\rowcolor{LightCyan}
'''
                tab = tab + line
                h += 1

        else:			# Positive/Negative Declinations
            while h < 24:
                band = int(h/6)
                group = band % 2
                line = r'''\color{{blue}}{{{}}} & '''.format(h)
                line = line + r'''{} && {} & {} && {} & {} && {} & {} && {} & {} \\
'''.format(aGHA[h],vGHA[h],vDEC[h],mGHA[h],mDEC[h],jGHA[h],jDEC[h],sGHA[h],sDEC[h])
                if group == 1:
                    tab = tab + r'''\rowcolor{LightCyan}
'''
                tab = tab + line
                h += 1

        mag_v, mag_m, mag_j, mag_s = magnitudes(date)   # magnitudes from Ephem
        RAc_v, Dc_v, mag_v = vdm_Venus(date)
        RAc_m, Dc_m = vdm_Mars(date)
        RAc_j, Dc_j, mag_j = vdm_Jupiter(date)
        RAc_s, Dc_s = vdm_Saturn(date)
        tab = tab + r'''\cmidrule{{1-2}} \cmidrule{{4-5}} \cmidrule{{7-8}} \cmidrule{{10-11}} \cmidrule{{13-14}}
\multicolumn{{2}}{{c}}{{\footnotesize{{Mer.pass. {}}}}} && 
\multicolumn{{2}}{{c}}{{\footnotesize{{\(\nu\){}$'$ \emph{{d}}{}$'$ m{}}}}} && 
\multicolumn{{2}}{{c}}{{\footnotesize{{\(\nu\){}$'$ \emph{{d}}{}$'$ m{}}}}} && 
\multicolumn{{2}}{{c}}{{\footnotesize{{\(\nu\){}$'$ \emph{{d}}{}$'$ m{}}}}} && 
\multicolumn{{2}}{{c}}{{\footnotesize{{\(\nu\){}$'$ \emph{{d}}{}$'$ m{}}}}}\\
\cmidrule{{1-2}} \cmidrule{{4-5}} \cmidrule{{7-8}} \cmidrule{{10-11}} \cmidrule{{13-14}}
'''.format(ariestransit(date+timedelta(days=1)),RAc_v,Dc_v,mag_v,RAc_m,Dc_m,mag_m,RAc_j,Dc_j,mag_j,RAc_s,Dc_s,mag_s)
        if n < 2:
            vsep = ""
            if config.pgsz == "Letter":
                vsep = "[-2.0ex]"
            # add space between tables...
            tab = tab + r'''\multicolumn{{10}}{{c}}{{}}\\{}'''.format(vsep)
        n += 1
        date += timedelta(days=1)

    tab = tab+r'''\end{tabular}\quad
'''
    return tab

# >>>>>>>>>>>>>>>>>>>>>>>>
def mp_planets_worker(date, ts, obj):
    #print(" mp_planets_worker Start  {}".format(obj))
    sha = mp_planetstransit(date, ts, obj)    # ===>>> mp_nautical.py
    #print(" mp_planets_worker Finish {}".format(obj))
    return sha      # return list for four planets

def starstab(date, ts):
    # returns a table with ephemerides for the navigational stars
    # OLD: \begin{tabular*}{0.251\textwidth}[t]{@{\extracolsep{\fill}}|rrr|}
    # OLD: note: 0.251 instead of 0.25 (above) prevents an "Overfull \hbox (0.14297pt too wide)" message on about 5 specific pages in the full year (moonimg=True)

    if config.tbls == "m":
        out = r'''\setlength{\tabcolsep}{4pt}  % default 6pt
\begin{tabular}[t]{|rrr|}
\multicolumn{3}{c}{\normalsize{Stars}}\\
\hline
& \multicolumn{1}{c}{\multirow{2}{*}{\textbf{SHA}}} 
& \multicolumn{1}{c|}{\multirow{2}{*}{\textbf{Dec}}}\\
& & \multicolumn{1}{c|}{} \\
'''
    else:
        out = r'''\setlength{\tabcolsep}{5pt}  % default 6pt
\begin{tabular}[t]{|rrr|}
\multicolumn{3}{c}{\normalsize{Stars}}\\
\hline
\rule{0pt}{2.4ex} & \multicolumn{1}{c}{\textbf{SHA}} & \multicolumn{1}{c|}{\textbf{Dec}}\\
\hline\rule{0pt}{2.6ex}\noindent
'''
    stars = stellar_info(date + timedelta(days=1))

    for i in range(len(stars)):
        out = out + r'''{} & {} & {} \\
'''.format(stars[i][0],stars[i][1],stars[i][2])
    m = r'''\hline
'''

    # returns 3 tables with SHA & Mer.pass for Venus, Mars, Jupiter and Saturn
    for i in range(3):
        dt = date + timedelta(days=i)
        datestr = r'''{} {} {}'''.format(dt.strftime("%b"), dt.strftime("%d"), dt.strftime("%a"))
        m = m + '''\hline
'''
        if config.tbls == "m":
            m = m + r'''& & \multicolumn{{1}}{{r|}}{{}}\\[-2.0ex]
\multicolumn{{1}}{{|r}}{{\textbf{{{}}}}} 
& \multicolumn{{1}}{{c}}{{\textbf{{SHA}}}} 
& \multicolumn{{1}}{{r|}}{{\textbf{{Mer.pass}}}}\\
'''.format(datestr)
        else:
            m = m + r'''& & \multicolumn{{1}}{{r|}}{{}}\\[-2.0ex]
\textbf{{{}}} & \textbf{{SHA}} & \textbf{{Mer.pass}}\\
'''.format(datestr)
        datex = date + timedelta(days=i)

        if config.MULTIpr and config.WINpf:
            # multiprocess 'SHA + transit times' simultaneously
            objlist = ['venus', 'mars', 'jupiter', 'saturn']
            partial_func2 = partial(mp_planets_worker, datex, ts)
            listofsha = pool.map(partial_func2, objlist, 1)     # RECOMMENDED: chunksize = 1
            for k in range(len(listofsha)):
                config.stopwatch += listofsha[k][2]     # accumulate multiprocess processing time
                del listofsha[k][-1]
            p = [item for sublist in listofsha for item in sublist]
            p.extend(hor_parallax(datex, ts))
        else:
            p = planetstransit(datex)

        m = m + r'''Venus & {} & {} \\
'''.format(p[0],p[1])
        m = m + r'''Mars & {} & {} \\
'''.format(p[2],p[3])
        m = m + r'''Jupiter & {} & {} \\
'''.format(p[4],p[5])
        m = m + r'''Saturn & {} & {} \\
'''.format(p[6],p[7])
        m = m + r'''\hline
'''
    out = out + m

    # returns a table with Horizontal parallax for Venus and Mars
    hp = r'''\hline
'''
    hp = hp + r'''& & \multicolumn{1}{r|}{}\\[-2.5ex]
\multicolumn{2}{|r}{\rule{0pt}{2.6ex}\textbf{Horizontal parallax}} & \multicolumn{1}{c|}{}\\
'''
    hp = hp + r'''\multicolumn{{2}}{{|r}}{{Venus:}} & \multicolumn{{1}}{{c|}}{{{}}} \\
'''.format(p[9])
    hp = hp + r'''\multicolumn{{2}}{{|r}}{{Mars:}} & \multicolumn{{1}}{{c|}}{{{}}} \\
'''.format(p[8])
    hp = hp + r'''\hline
'''
    out = out + hp
    
    out = out + r'''\end{tabular}'''
    return out

# >>>>>>>>>>>>>>>>>>>>>>>>
def mp_sunmoon_worker(date, ts, n):
    # split the work by date into 3 separate days
    sunmoondata = mp_sunmoon(date, ts, n)      # ===>>> mp_nautical.py
    return sunmoondata

def sunmoontab(date, ts):
    # generates LaTeX table for sun and moon (traditional style)
    # OLD: \begin{tabular*}{0.54\textwidth}[t]{@{\extracolsep{\fill}}|c|rr|rrrrr|}
    # OLD note: 54% table width above removes "Overfull \hbox (1.65279pt too wide)"
    #                 and "Underfull \hbox (badness 10000)"
    # note: table may have different widths due to the 1st column (e.g. Fri versus Wed)
    # note: table may have different widths due to the 'v' column (e.g. 6.9' versus 15.3')
    # note: table may have different widths due to the 'd' column (e.g. 8.2' versus -13.9')

    if config.MULTIpr and config.WINpf:
        # multiprocess sunmoontab values per "date" simultaneously
        partial_func = partial(mp_sunmoon_worker, date, ts)
        sunmoonlist = pool.map(partial_func, [nn for nn in range(3)], 1)

    tab = r'''\noindent
\setlength{\tabcolsep}{5.8pt}  % default 6pt
\begin{tabular}[t]{|c|rr|rrrrr|}
\multicolumn{1}{c}{\normalsize{h}}& \multicolumn{2}{c}{\normalsize{Sun}} & \multicolumn{5}{c}{\normalsize{Moon}}\\
'''
    n = 0
    while n < 3:
        tab = tab + r'''\hline
\multicolumn{{1}}{{|c|}}{{\rule{{0pt}}{{2.6ex}}\textbf{{{}}}}} &\multicolumn{{1}}{{c}}{{\textbf{{GHA}}}} & \multicolumn{{1}}{{c|}}{{\textbf{{Dec}}}}  & \multicolumn{{1}}{{c}}{{\textbf{{GHA}}}} & \multicolumn{{1}}{{c}}{{\(\nu\)}} & \multicolumn{{1}}{{c}}{{\textbf{{Dec}}}} & \multicolumn{{1}}{{c}}{{\textit{{d}}}} & \multicolumn{{1}}{{c|}}{{\textbf{{HP}}}}\\
\hline\rule{{0pt}}{{2.6ex}}\noindent
'''.format(date.strftime("%a"))
        # note: inline math mode is used to typeset the greek character 'nu'

        if config.MULTIpr and config.WINpf:
            ghas = sunmoonlist[n][0]
            decs = sunmoonlist[n][1]
            degs = sunmoonlist[n][2]
            gham = sunmoonlist[n][3]
            decm = sunmoonlist[n][4]
            degm = sunmoonlist[n][5]
            HPm  = sunmoonlist[n][6]
            GHAupper = sunmoonlist[n][7]
            GHAlower = sunmoonlist[n][8]
            ghaSoD = sunmoonlist[n][9]
            ghaEoD = sunmoonlist[n][10]
            vmin = sunmoonlist[n][11]
            dmin = sunmoonlist[n][12]
        else:
            date0 = date - timedelta(days=1)
            ghas, decs, degs = sunGHA(date)
            gham, decm, degm, HPm, GHAupper, GHAlower, ghaSoD, ghaEoD = moonGHA(date)
            vmin, dmin = moonVD(date0,date)

        buildUPlists(n, ghaSoD, GHAupper, ghaEoD)
        buildLOWlists(n, ghaSoD, GHAupper, ghaEoD)

        h = 0
        if config.decf != '+':	# USNO format for Declination
            mlastNS = ''
            while h < 24:
                if h > 0:
                    prevDEC = degs[h-1]
                else:
                    prevDEC = degs[0]		# hour -1 = hour 0
                if h < 23:
                    nextDEC = degs[h+1]
                else:
                    nextDEC = degs[23]	# hour 24 = hour 23
                
                # format declination checking for hemisphere change
                printNS, printDEG = declCompare(prevDEC,degs[h],nextDEC,h)
                sdec = NSdecl(decs[h],h,printNS,printDEG,False)

                mdec, mNS = NSdeg(decm[h],False,h)
                if h < 23:
                    if mNS != mlastNS or copysign(1.0,degm[h]) != copysign(1.0,degm[h+1]):
                        mdec, mNS = NSdeg(decm[h],False,h,True)	# force N/S
                mlastNS = mNS

                line = r'''{} & {} & {} & {} & {} & {} & {} & {}'''.format(h,ghas[h],sdec,gham[h],vmin[h],mdec,dmin[h],HPm[h])
                lineterminator = r'''\\
'''
                if h < 23 and (h+1)%6 == 0:
                    lineterminator = r'''\\[2Pt]
'''
                tab = tab + line + lineterminator
                h += 1

        else:			# Positive/Negative Declinations
            while h < 24:
                line = r'''{} & {} & {} & {} & {} & {} & {} & {}'''.format(h,ghas[h],decs[h],gham[h],vmin[h],decm[h],dmin[h],HPm[h])
                lineterminator = r'''\\
'''
                if h < 23 and (h+1)%6 == 0:
                    lineterminator = r'''\\[2Pt]
'''
                tab = tab + line + lineterminator
                h += 1

        sds, dsm = sunSD(date)
        sdmm = moonSD(date)
        tab = tab + r'''\hline
\rule{{0pt}}{{2.4ex}} & \multicolumn{{1}}{{c}}{{SD = {}$'$}} & \multicolumn{{1}}{{c|}}{{\textit{{d}} = {}$'$}} & \multicolumn{{5}}{{c|}}{{SD = {}$'$}}\\
\hline
'''.format(sds,dsm,sdmm)
        if n < 2:
            # add space between tables...
            tab = tab + r'''\multicolumn{7}{c}{}\\[-1.5ex]'''
        n += 1
        date += timedelta(days=1)
    tab = tab + r'''\end{tabular}
'''
    return tab

# >>>>>>>>>>>>>>>>>>>>>>>>
def sunmoontabm(date, ts):
    # generates LaTeX table for sun and moon (modern style)

    if config.MULTIpr and config.WINpf:
        # multiprocess sunmoontab values per "date" simultaneously
        partial_func = partial(mp_sunmoon_worker, date, ts)
        sunmoonlist = pool.map(partial_func, [nn for nn in range(3)], 1)

    tab = r'''\noindent
\renewcommand{\arraystretch}{1.1}
\setlength{\tabcolsep}{4pt}  % default 6pt
\quad
\begin{tabular}[t]{crrcrrrrr}
\multicolumn{1}{c}{\normalsize{h}} & 
\multicolumn{2}{c}{\normalsize{Sun}} & &
\multicolumn{5}{c}{\normalsize{Moon}}\\
\cmidrule{2-3} \cmidrule{5-9}'''
    # note: \quad\quad above shifts all tables to the right (still within margins)
    n = 0
    while n < 3:
        tab = tab + r'''
\multicolumn{{1}}{{c}}{{\textbf{{{}}}}} & \multicolumn{{1}}{{c}}{{\textbf{{GHA}}}} & \multicolumn{{1}}{{c}}{{\textbf{{Dec}}}} & & \multicolumn{{1}}{{c}}{{\textbf{{GHA}}}} & \multicolumn{{1}}{{c}}{{\(\nu\)}} & \multicolumn{{1}}{{c}}{{\textbf{{Dec}}}} & \multicolumn{{1}}{{c}}{{\textit{{d}}}} & \multicolumn{{1}}{{c}}{{\textbf{{HP}}}}\\
'''.format(date.strftime("%a"))

        if config.MULTIpr and config.WINpf:
            ghas = sunmoonlist[n][0]
            decs = sunmoonlist[n][1]
            degs = sunmoonlist[n][2]
            gham = sunmoonlist[n][3]
            decm = sunmoonlist[n][4]
            degm = sunmoonlist[n][5]
            HPm  = sunmoonlist[n][6]
            GHAupper = sunmoonlist[n][7]
            GHAlower = sunmoonlist[n][8]
            ghaSoD = sunmoonlist[n][9]
            ghaEoD = sunmoonlist[n][10]
            vmin = sunmoonlist[n][11]
            dmin = sunmoonlist[n][12]
        else:
            date0 = date - timedelta(days=1)
            ghas, decs, degs = sunGHA(date)
            gham, decm, degm, HPm, GHAupper, GHAlower, ghaSoD, ghaEoD = moonGHA(date)
            vmin, dmin = moonVD(date0,date)

        buildUPlists(n, ghaSoD, GHAupper, ghaEoD)
        buildLOWlists(n, ghaSoD, GHAupper, ghaEoD)

        h = 0
        if config.decf != '+':	# USNO format for Declination
            mlastNS = ''
            while h < 24:
                band = int(h/6)
                group = band % 2
                if h > 0:
                    prevDEC = degs[h-1]
                else:
                    prevDEC = degs[0]		# hour -1 = hour 0
                if h < 23:
                    nextDEC = degs[h+1]
                else:
                    nextDEC = degs[23]	# hour 24 = hour 23
                
                # format declination checking for hemisphere change
                printNS, printDEG = declCompare(prevDEC,degs[h],nextDEC,h)
                sdec = NSdecl(decs[h],h,printNS,printDEG,True)

                mdec, mNS = NSdeg(decm[h],True,h)
                if h < 23:
                    if mNS != mlastNS or copysign(1.0,degm[h]) != copysign(1.0,degm[h+1]):
                        mdec, mNS = NSdeg(decm[h],True,h,True)	# force NS
                mlastNS = mNS

                line = r'''\color{{blue}}{{{}}} & '''.format(h)
                line = line + r'''{} & {} && {} & {} & {} & {} & {} \\
'''.format(ghas[h],sdec,gham[h],vmin[h],mdec,dmin[h],HPm[h])

                if group == 1:
                    tab = tab + r'''\rowcolor{LightCyan}
'''
                tab = tab + line
                h += 1

        else:			# Positive/Negative Declinations
            while h < 24:
                band = int(h/6)
                group = band % 2
                line = r'''\color{{blue}}{{{}}} & '''.format(h)
                line = line + r'''{} & {} && {} & {} & {} & {} & {} \\
'''.format(ghas[h],decs[h],gham[h],vmin[h],decm[h],dmin[h],HPm[h])
                if group == 1:
                    tab = tab + r'''\rowcolor{LightCyan}
'''
                tab = tab + line
                h += 1

        sds, dsm = sunSD(date)
        sdmm = moonSD(date)
        tab = tab + r'''\cmidrule{{2-3}} \cmidrule{{5-9}}
\multicolumn{{1}}{{c}}{{}} & \multicolumn{{1}}{{c}}{{\footnotesize{{SD = {}$'$}}}} & 
\multicolumn{{1}}{{c}}{{\footnotesize{{\textit{{d}} = {}$'$}}}} && \multicolumn{{5}}{{c}}{{\footnotesize{{SD = {}$'$}}}}\\
\cmidrule{{2-3}} \cmidrule{{5-9}}
'''.format(sds,dsm,sdmm)
        if n < 2:
            vsep = "[-1.5ex]"
            if config.pgsz == "Letter":
                vsep = "[-2.0ex]"
            # add space between tables...
            tab = tab + r'''\multicolumn{{7}}{{c}}{{}}\\{}'''.format(vsep)
        n += 1
        date += timedelta(days=1)
    tab = tab + r'''\end{tabular}\quad\quad
'''
    return tab

# >>>>>>>>>>>>>>>>>>>>>>>>
# create a list of 'moon above/below horizon' states per Latitude...
#    None = unknown; True = above horizon (visible); False = below horizon (not visible)
#    moonvisible[0] is not linked to a latitude but a manual override
# The moon above/below status is stored at 3-day intervals, i.e. when multiprocessing "1st day",
#    the previous day's status is stored here (except on the first day to be processed).
#    Multiprocessing does not confuse the states as every three days it waits for all data.
# Note: the size of moonvisible MUST equal the size of config.lat
moonvisible = [None] * 31       # moonvisible[0] up to moonvisible[30]

def mp_twilight_worker(date, ts, lat):
    #print(" mp_twilight_worker Start {}".format(lat))
    hemisph = 'N' if lat >= 0 else 'S'
    twi = mp_twilight(date, lat, hemisph, ts)       # ===>>> mp_nautical.py
    #print(" mp_twilight_worker Finish {}".format(lat))
    return twi      # return list for all latitudes

def mp_moonlight_worker(date, ts, lat, mstate):
    #print(" mp_moonlight_worker Start  {}".format(lat))
    hemisph = 'N' if lat >= 0 else 'S'
    ml = mp_moonrise_set(date, lat, mstate, hemisph, ts)    # ===>>> mp_nautical.py
    #print(" mp_moonlight_worker Finish {}".format(lat))
    return ml       # return list for all latitudes

def twilighttab(date, ts):
    # returns the twilight and moonrise tables, finally EoT data

    if config.MULTIpr:
        # multiprocess twilight values for "date+1" per latitude simultaneously
        # date+1 to calculate for the second day (three days are printed on one page)
        partial_func = partial(mp_twilight_worker, date+timedelta(days=1), ts)
        listoftwi = pool.map(partial_func, config.lat, 1)   # RECOMMENDED: chunksize = 1
        for k in range(len(listoftwi)):
            config.stopwatch += listoftwi[k][6]     # accumulate multiprocess processing time
            del listoftwi[k][-1]

        # multiprocess moonlight values for "date, date+1, date+2" per latitude simultaneously
        data = [(config.lat[ii], moonvisible[ii]) for ii in range(len(config.lat))]
        partial_func2 = partial(mp_moonlight_worker, date, ts)  # list of tuples
        listmoon = pool.starmap(partial_func2, data, 1)   # RECOMMENDED: chunksize = 1
        for k in range(len(listmoon)):
            tuple_seeks = listmoon[k][-1]
            config.moonDataSeeks    += tuple_seeks[0]   # count of moonrise ot set seeks
            config.moonHorizonSeeks += tuple_seeks[1]   # count of horizon seeks
            moonvisible[k] = tuple_seeks[2]             # updated moon state
            del listmoon[k][-1]
            tuple_times = listmoon[k][-1]
            config.stopwatch  += tuple_times[0]         # accumulate multiprocess processing time
            config.stopwatch2 += tuple_times[1]         # accumulate multiprocess processing time
            del listmoon[k][-1]
        #print("listmoon = {}".format(listmoon))

# Twilight tables ...........................................
    #lat = [72,70,68,66,64,62,60,58,56,54,52,50,45,40,35,30,20,10,0, -10,-20,-30,-35,-40,-45,-50,-52,-54,-56,-58,-60]
    latNS = [72, 70, 58, 40, 10, -10, -50, -60]
    # OLD: \begin{tabular*}{0.45\textwidth}[t]{@{\extracolsep{\fill}}|r|ccc|ccc|}

    if config.tbls == "m":
    # The header begins with a thin empty row as top padding; and the top row with
    # bold text has some padding below it. This result gives a balanced impression.
        tab = r'''\setlength{\tabcolsep}{5pt}  % default 6pt
\begin{tabular}[t]{|r|ccc|ccc|}
\multicolumn{7}{c}{\normalsize{}}\\
\hline
\multicolumn{1}{|c|}{} & & & \multicolumn{1}{|c|}{} & \multicolumn{1}{c|}{} & & \multicolumn{1}{c|}{}\\[-2.0ex]
\multicolumn{1}{|c|}{\multirow{2}{*}{\textbf{Lat.}}} & 
\multicolumn{2}{c}{\footnotesize{\textbf{Twilight}}} & 
\multicolumn{1}{|c|}{\multirow{2}{*}{\textbf{Sunrise}}} & 
\multicolumn{1}{c|}{\multirow{2}{*}{\textbf{Sunset}}} & 
\multicolumn{2}{c|}{\footnotesize{\textbf{Twilight}}}\\[0.6ex]
\multicolumn{1}{|c|}{} & 
\multicolumn{1}{c}{Naut.} & 
\multicolumn{1}{c}{Civil} & 
\multicolumn{1}{|c|}{} & 
\multicolumn{1}{c|}{} & 
\multicolumn{1}{c}{Civil} & 
\multicolumn{1}{c|}{Naut.}\\
\hline\rule{0pt}{2.6ex}\noindent
'''
    else:
        tab = r'''\setlength{\tabcolsep}{5.8pt}  % default 6pt
\begin{tabular}[t]{|r|ccc|ccc|}
\multicolumn{7}{c}{\normalsize{}}\\
\hline
\multicolumn{1}{|c|}{\rule{0pt}{2.4ex}\multirow{2}{*}{\textbf{Lat.}}} & 
\multicolumn{2}{c}{\textbf{Twilight}} & 
\multicolumn{1}{|c|}{\multirow{2}{*}{\textbf{Sunrise}}} & 
\multicolumn{1}{c|}{\multirow{2}{*}{\textbf{Sunset}}} & 
\multicolumn{2}{c|}{\textbf{Twilight}}\\
\multicolumn{1}{|c|}{} & 
\multicolumn{1}{c}{Naut.} & 
\multicolumn{1}{c}{Civil} & 
\multicolumn{1}{|c|}{} & 
\multicolumn{1}{c|}{} & 
\multicolumn{1}{c}{Civil} & 
\multicolumn{1}{c|}{Naut.}\\
\hline\rule{0pt}{2.6ex}\noindent
'''
    lasthemisph = ""
    j = 5
    for lat in config.lat:
        hemisph = 'N' if lat >= 0 else 'S'
        hs = ""
        if (lat in latNS):
            hs = hemisph
            if j%6 == 0:
                tab = tab + r'''\rule{0pt}{2.6ex}
'''
        lasthemisph = hemisph

        if config.MULTIpr:
            twi = listoftwi[j-5]
        else:
            # day+1 to calculate for the second day (three days are printed on one page)
            twi = twilight(date+timedelta(days=1), lat, hemisph)

        line = r'''\textbf{{{}}}'''.format(hs) + " " + r'''{}$^\circ$'''.format(abs(lat))
        line = line + r''' & {} & {} & {} & {} & {} & {} \\
'''.format(twi[0],twi[1],twi[2],twi[3],twi[4],twi[5])
        tab = tab + line
        j += 1
    # add space between tables...
    tab = tab + r'''\hline\multicolumn{7}{c}{}\\[-1.5ex]
'''

# Moonrise & Moonset ...........................................
    if config.tbls == "m":
        tab = tab + r'''\hline
\multicolumn{1}{|c|}{} & & & \multicolumn{1}{c|}{} & & & \multicolumn{1}{c|}{}\\[-2.0ex]
\multicolumn{1}{|c|}{\multirow{2}{*}{\textbf{Lat.}}} & 
\multicolumn{3}{c|}{\footnotesize{\textbf{Moonrise}}} & 
\multicolumn{3}{c|}{\footnotesize{\textbf{Moonset}}}\\[0.6ex]
'''
    else:
        tab = tab + r'''\hline
\multicolumn{1}{|c|}{\rule{0pt}{2.4ex}\multirow{2}{*}{\textbf{Lat.}}} & 
\multicolumn{3}{c|}{\textbf{Moonrise}} & 
\multicolumn{3}{c|}{\textbf{Moonset}}\\
'''

    weekday = [date.strftime("%a"),(date+timedelta(days=1)).strftime("%a"),(date+timedelta(days=2)).strftime("%a")]
    tab = tab + r'''\multicolumn{{1}}{{|c|}}{{}} & 
\multicolumn{{1}}{{c}}{{{}}} & 
\multicolumn{{1}}{{c}}{{{}}} & 
\multicolumn{{1}}{{c|}}{{{}}} & 
\multicolumn{{1}}{{c}}{{{}}} & 
\multicolumn{{1}}{{c}}{{{}}} & 
\multicolumn{{1}}{{c|}}{{{}}} \\
\hline\rule{{0pt}}{{2.6ex}}\noindent
'''.format(weekday[0],weekday[1],weekday[2],weekday[0],weekday[1],weekday[2])

    moon = [0,0,0,0,0,0]
    moon2 = [0,0,0,0,0,0]
    lasthemisph = ""
    j = 5
    for lat in config.lat:
        hemisph = 'N' if lat >= 0 else 'S'
        hs = ""
        if (lat in latNS):
            hs = hemisph
            if j%6 == 0:
                tab = tab + r'''\rule{0pt}{2.6ex}
'''
        lasthemisph = hemisph

        if config.MULTIpr:
            moon = listmoon[j-5][0]
            moon2 = listmoon[j-5][1]
        else:
            moon, moon2 = moonrise_set(date,lat,hemisph)

        if not(double_events_found(moon,moon2)):
            tab = tab + r'''\textbf{{{}}}'''.format(hs) + " " + r'''{}$^\circ$'''.format(abs(lat))
            tab = tab + r''' & {} & {} & {} & {} & {} & {} \\
'''.format(moon[0],moon[1],moon[2],moon[3],moon[4],moon[5])
        else:
# print a row with two moonrise/moonset events on the same day & latitude
            tab = tab + r'''\multirow{{2}}{{*}}{{\textbf{{{}}} {}$^\circ$}}'''.format(hs,abs(lat))
# top row...
            for k in range(len(moon)):
                if moon2[k] != '--:--':
                    #tab = tab + r''' & {}'''.format(moon[k])
                    tab = tab + r''' & \colorbox{{khaki!45}}{{{}}}'''.format(moon[k])
                else:
                    tab = tab + r''' & \multirow{{2}}{{*}}{{{}}}'''.format(moon[k])
            tab = tab + r'''\\
'''	# terminate top row
# bottom row...
            for k in range(len(moon)):
                if moon2[k] != '--:--':
                    #tab = tab + r''' & {}'''.format(moon2[k])
                    tab = tab + r''' & \colorbox{{khaki!45}}{{{}}}'''.format(moon2[k])
                else:
                    tab = tab + r'''&'''
            tab = tab + r'''\\
'''	# terminate bottom row
        j += 1
    # add space between tables...
    tab = tab + r'''\hline\multicolumn{7}{c}{}\\[-1.5ex]
'''

# Equation of Time section ...........................................
    #------------------  if moon image displayed... ------------------
    if config.moonimg:
        d = date
        d1 = d + timedelta(days=1)
        d2 = d + timedelta(days=2)
        d3 = d + timedelta(days=3)
        age0, pct0 = moonage(d, d1)
        phase = moonphase(d1)       # moon phase (0:new to π:full to 2π:new)
        age2, pct2 = moonage(d2, d3)
        ages = '{}-{}'.format(age0,age2)
        pcts = '{}-{}\%'.format(pct0,pct2)

        if config.tbls == "m":
            tab = tab + r'''\hline
\multicolumn{1}{|c|}{} & & & \multicolumn{1}{c|}{} & & & \multicolumn{1}{c|}{}\\[-2.0ex]
\multicolumn{1}{|c|}{\multirow{4}{*}{\footnotesize{\textbf{Day}}}} & 
\multicolumn{3}{c|}{\footnotesize{\textbf{Sun}}} & 
\multicolumn{3}{c|}{\footnotesize{\textbf{Moon}}}\\[0.6ex]
\multicolumn{1}{|c|}{} & \multicolumn{2}{c}{Eqn.of Time} & \multicolumn{1}{|c|}{Mer.} & \multicolumn{2}{c}{Mer.Pass.} & \multicolumn{1}{|c|}{Age}\\
'''

            tab = tab + r'''\multicolumn{1}{|c|}{} &\multicolumn{1}{c}{00\textsuperscript{h}} & 
\multicolumn{1}{c}{12\textsuperscript{h}} & \multicolumn{1}{|c|}{Pass} & \multicolumn{1}{c}{Upper} & \multicolumn{1}{c}{Lower} & '''
            tab = tab + r'''\multicolumn{{1}}{{|c|}}{{{}}}\\
'''.format(ages)
            
            tab = tab + r'''\multicolumn{1}{|c|}{} &\multicolumn{1}{c}{mm:ss} & 
\multicolumn{1}{c}{mm:ss} & \multicolumn{1}{|c|}{hh:mm} & \multicolumn{1}{c}{hh:mm} & \multicolumn{1}{c}{hh:mm} & '''
            tab = tab + r'''\multicolumn{{1}}{{|c|}}{{{}}}\\
\hline\rule{{0pt}}{{3.0ex}}\noindent
'''.format(pcts)

        else:
            tab = tab + r'''\hline
\multicolumn{1}{|c|}{\rule{0pt}{2.4ex}\multirow{4}{*}{\textbf{Day}}} & 
\multicolumn{3}{c|}{\textbf{Sun}} & \multicolumn{3}{c|}{\textbf{Moon}}\\
\multicolumn{1}{|c|}{} & \multicolumn{2}{c}{Eqn.of Time} & \multicolumn{1}{|c|}{Mer.} & \multicolumn{2}{c}{Mer.Pass.} & \multicolumn{1}{|c|}{Age}\\
\multicolumn{1}{|c|}{} & \multicolumn{1}{c}{00\textsuperscript{h}} & \multicolumn{1}{c}{12\textsuperscript{h}} & \multicolumn{1}{|c|}{Pass} & \multicolumn{1}{c}{Upper} & \multicolumn{1}{c}{Lower} & '''
            tab = tab + r'''\multicolumn{{1}}{{|c|}}{{{}}}\\
'''.format(ages)
            tab = tab + r'''\multicolumn{1}{|c|}{} & \multicolumn{1}{c}{mm:ss} & \multicolumn{1}{c}{mm:ss} & 
\multicolumn{1}{|c|}{hh:mm} & \multicolumn{1}{c}{hh:mm} & \multicolumn{1}{c}{hh:mm} & '''
            tab = tab + r'''\multicolumn{{1}}{{|c|}}{{{}}}\\
\hline\rule{{0pt}}{{3.0ex}}\noindent
'''.format(pcts)

        d = date
        for k in range(3):
            eq = equation_of_time(d,d + timedelta(days=1),UpperLists[k],LowerLists[k], False)
            if k == 0:
                tab = tab + r'''%s & %s & %s & %s & %s & %s & ''' %(d.strftime("%d"),eq[0],eq[1],eq[2],eq[3],eq[4])
                tab = tab + lunatikz(phase)
            elif k == 1:
                tab = tab + r'''{} & {} & {} & {} & {} & {} & \multicolumn{{1}}{{|c|}}{{}}\\
'''.format(d.strftime("%d"),eq[0],eq[1],eq[2],eq[3],eq[4])
            else:
                tab = tab + r'''{} & {} & {} & {} & {} & {} & \multicolumn{{1}}{{|c|}}{{}}\\[0.3ex]
'''.format(d.strftime("%d"),eq[0],eq[1],eq[2],eq[3],eq[4])
            d += timedelta(days=1)
        tab = tab + r'''\hline
\end{tabular}'''
    #-----------------  if no moon image displayed... -----------------
    else:
        if config.tbls == "m":
            tab = tab + r'''\hline
\multicolumn{1}{|c|}{} & & & \multicolumn{1}{c|}{} & & & \multicolumn{1}{c|}{}\\[-2.0ex]
\multicolumn{1}{|c|}{\multirow{4}{*}{\footnotesize{\textbf{Day}}}} & 
\multicolumn{3}{c|}{\footnotesize{\textbf{Sun}}} & 
\multicolumn{3}{c|}{\footnotesize{\textbf{Moon}}}\\[0.6ex]
\multicolumn{1}{|c|}{} & 
\multicolumn{2}{c}{Eqn.of Time} & 
\multicolumn{1}{|c|}{Mer.} & 
\multicolumn{2}{c}{Mer.Pass.} & 
\multicolumn{1}{|c|}{}\\
\multicolumn{1}{|c|}{} &\multicolumn{1}{c}{00\textsuperscript{h}} & \multicolumn{1}{c}{12\textsuperscript{h}} & \multicolumn{1}{|c|}{Pass} & \multicolumn{1}{c}{Upper} & \multicolumn{1}{c}{Lower} &\multicolumn{1}{|c|}{Age}\\
\multicolumn{1}{|c|}{} &\multicolumn{1}{c}{mm:ss} & \multicolumn{1}{c}{mm:ss} & \multicolumn{1}{|c|}{hh:mm} & \multicolumn{1}{c}{hh:mm} & \multicolumn{1}{c}{hh:mm} &\multicolumn{1}{|c|}{}\\
\hline\rule{0pt}{3.0ex}\noindent
'''
        else:
            tab = tab + r'''\hline
\multicolumn{1}{|c|}{\rule{0pt}{2.4ex}\multirow{4}{*}{\textbf{Day}}} & 
\multicolumn{3}{c|}{\textbf{Sun}} & \multicolumn{3}{c|}{\textbf{Moon}}\\
\multicolumn{1}{|c|}{} & \multicolumn{2}{c}{Eqn.of Time} & \multicolumn{1}{|c|}{Mer.} & \multicolumn{2}{c}{Mer.Pass.} & \multicolumn{1}{|c|}{}\\
\multicolumn{1}{|c|}{} & \multicolumn{1}{c}{00\textsuperscript{h}} & \multicolumn{1}{c}{12\textsuperscript{h}} & \multicolumn{1}{|c|}{Pass} & \multicolumn{1}{c}{Upper} & \multicolumn{1}{c}{Lower} &\multicolumn{1}{|c|}{Age}\\
\multicolumn{1}{|c|}{} & \multicolumn{1}{c}{mm:ss} & \multicolumn{1}{c}{mm:ss} & \multicolumn{1}{|c|}{hh:mm} & \multicolumn{1}{c}{hh:mm} & \multicolumn{1}{c}{hh:mm} &\multicolumn{1}{|c|}{}\\
\hline\rule{0pt}{3.0ex}\noindent
'''

        d = date
        for k in range(3):
            eq = equation_of_time(d,d + timedelta(days=1),UpperLists[k],LowerLists[k], True)
            if k == 2:
                tab = tab + r'''{} & {} & {} & {} & {} & {} & {}({}\%) \\[0.3ex]
'''.format(d.strftime("%d"),eq[0],eq[1],eq[2],eq[3],eq[4],eq[5],eq[6])
            else:
                tab = tab + r'''{} & {} & {} & {} & {} & {} & {}({}\%) \\
'''.format(d.strftime("%d"),eq[0],eq[1],eq[2],eq[3],eq[4],eq[5],eq[6])
            d += timedelta(days=1)
        tab = tab + r'''\hline
\end{tabular}'''
    return tab

#----------------------
#   page preparation
#----------------------

def doublepage(date, page1, ts):
    # creates a doublepage (3 days) of the nautical almanac

    # time delta values for the initial date&time...
    dut1, deltat = getDUT1(date)
    timeDUT1 = r"DUT1 = UT1-UTC = {:+.4f} sec\quad$\Delta$T = TT-UT1 = {:+.4f} sec".format(dut1, deltat)

    dateZ = date + timedelta(days=2)        # last day
    find_new_moon(date)     # required for 'moonage' and 'equation_of_time"
    page = ''
    if not(page1):
        page = r'''
% ------------------ N E W   P A G E ------------------
\newpage
\restoregeometry    % reset to even-page margins'''

    leftindent = ""
    rightindent = ""
    if config.tbls == "m":
        leftindent = "\quad"
        rightindent = "\hphantom{\quad}"

    page = page + r'''
\sffamily
\noindent
{}\textbf{{{}, {}, {} UT ({}.,  {}.,  {}.)}}'''.format(leftindent,date.strftime("%B %d"),(date+timedelta(days=1)).strftime("%d"),(date+timedelta(days=2)).strftime("%d"),date.strftime("%a"),(date+timedelta(days=1)).strftime("%a"),(date+timedelta(days=2)).strftime("%a"))

    if config.tbls == "m":
        page = page + r'\\[1.0ex]'  # \par leaves about 1.2ex
    else:
        page = page + r'\\[0.7ex]'

    page = page + r'''
\begin{scriptsize}
'''

    if config.tbls == "m":
        page = page + planetstabm(date,ts)
    else:
        page = page + planetstab(date,ts) + r'''\enskip
'''
    page = page + starstab(date,ts)
    str1 = r'''
\end{{scriptsize}}
% ------------------ N E W   P A G E ------------------
\newpage
\newgeometry{{nomarginpar, top={}, bottom={}, left={}, right={}}}
\begin{{flushleft}}     % required so that \par works
{{\footnotesize {}}}\hfill\textbf{{{} to {} UT}}
\end{{flushleft}}\par
\begin{{scriptsize}}
'''.format(tm, bm, oddim, oddom, timeDUT1, date.strftime("%Y %B %d"), (date+timedelta(days=2)).strftime("%b. %d"), rightindent)
    page = page + str1
    if config.tbls == "m":
        page = page + sunmoontabm(date,ts)
    else:
        page = page + sunmoontab(date,ts) + r'''\enskip
'''
    page = page + twilighttab(date,ts)
    # to avoid "Overfull \hbox" messages, leave a paragraph end before the end of a size change. (This may only apply to tabular* table style) See lines below...
    page = page + r'''

\end{scriptsize}'''
    return page


def pages(first_day, dtp, ts):
    # dtp = 0 if for entire year; = -1 if for entire month; else days to print

    if config.MULTIpr:
        # Windows & macOS defaults to "spawn"; Unix to "fork"
        #mp.set_start_method("spawn")
        n = config.CPUcores
        if n > 12: n = 12   # use 12 cores maximum
        if (config.WINpf or config.MACOSpf) and n > 8: n = 8   # 8 maximum if Windows or Mac OS
        global pool
        pool = mp.Pool(n)   # start 8 max. worker processes

    out = ''
    page1 = True
    pmth = ''
    dpp = 3         # 3 days per page
    day1 = first_day

    if dtp == 0:        # if entire year
        year = first_day.year
        yr = year
        while year == yr:
            cmth = day1.strftime("%b ")
            day3 = day1 + timedelta(days=2)
            if cmth != pmth:
                print() # progress indicator - next month
                #print(cmth, end='')
                sys.stdout.write(cmth)	# next month
                sys.stdout.flush()
                pmth = cmth
            else:
                sys.stdout.write('.')	# progress indicator
                sys.stdout.flush()
            out += doublepage(day1, page1, ts)
            page1 = False
            day1 += timedelta(days=3)
            year = day1.year
    elif dtp == -1:     # if entire month
        mth = first_day.month
        m = mth
        while mth == m:
            cmth = day1.strftime("%b ")
            day3 = day1 + timedelta(days=2)
            if cmth != pmth:
                print() # progress indicator - next month
                #print(cmth, end='')
                sys.stdout.write(cmth)	# next month
                sys.stdout.flush()
                pmth = cmth
            else:
                sys.stdout.write('.')	# progress indicator
                sys.stdout.flush()
            out += doublepage(day1, page1, ts)
            page1 = False
            day1 += timedelta(days=3)
            mth = day1.month
    else:           # print 'dtp' days beginning with first_day
        i = dtp   # don't decrement dtp
        while i > 0:
            out += doublepage(day1, page1, ts)
            page1 = False
            i -= 3
            day1 += timedelta(days=3)

    if dtp <= 0:        # if Full Almanac for a whole month/year...
        print("\n")		# 2 x newline to terminate progress indicator

    if config.MULTIpr:
        pool.close()    # close all worker processes
        pool.join()

    return out

#--------------------------
#   external entry point
#--------------------------

def almanac(first_day, dtp, ts):
    # dtp = 0 if for entire year; = -1 if for entire month; else days to print

    # make almanac starting from first_day
    global tm, bm, oddim, oddom
    year = first_day.year
    mth = first_day.month
    day = first_day.day

    # page size specific parameters
    if config.pgsz == "A4":
        # pay attention to the limited page width
        paper = "a4paper"
        vsep1 = "1.5cm"
        vsep2 = "1.0cm"
        tm1 = "21mm"    # title page...
        bm1 = "15mm"
        lm1 = "10mm"
        rm1 = "10mm"
        tm = "21mm"     # data pages...
        bm = "18mm"
        # even data pages...
        im = "10mm"     # inner margin (right side on even pages)
        om = "9mm"      # outer margin (left side on even pages)
        # odd data pages...
        oddim = "14mm"  # inner margin (left side on odd pages)
        oddom = "11mm"  # outer margin (right side on odd pages)
        if config.tbls == "m":
            tm = "10mm"
            bm = "15mm"
            im = "10mm"
            om = "10mm"
            oddim = "14mm"
            oddom = "11mm"
    else:
        # pay attention to the limited page height
        paper = "letterpaper"
        vsep1 = "0.8cm"
        vsep2 = "0.7cm"
        tm1 = "12mm"    # title page...
        bm1 = "15mm"
        lm1 = "12mm"
        rm1 = "12mm"
        tm = "12.2mm"   # data pages...
        bm = "13mm"
        # even data pages...
        im = "13mm"     # inner margin (right side on even pages)
        om = "13mm"     # outer margin (left side on even pages)
        # odd data pages...
        oddim = "14mm"  # inner margin (left side on odd pages)
        oddom = "11mm"  # outer margin (right side on odd pages)
        if config.tbls == "m":
            tm = "4mm"
            bm = "8mm"
            im = "13mm"
            om = "13mm"
            oddim = "14mm"
            oddom = "14mm"

    alm = r'''\documentclass[10pt, twoside, {}]{{report}}'''.format(paper)

    alm = alm + r'''
%\usepackage[utf8]{inputenc}
\usepackage[english]{babel}
\usepackage{fontenc}
\usepackage{enumitem} % used to customize the {description} environment'''

    # to troubleshoot add "showframe, verbose," below:
    alm = alm + r'''
\usepackage[nomarginpar, top={}, bottom={}, left={}, right={}]{{geometry}}'''.format(tm,bm,im,om)

    if config.tbls == "m":
        alm = alm + r'''
\usepackage[table]{xcolor}
% [table] option loads the colortbl package for coloring rows, columns, and cells within tables.
\definecolor{LightCyan}{rgb}{0.88,1,1}
\definecolor{darknight}{rgb}{0.18, 0.27, 0.33}
\usepackage{booktabs}'''
    else:
        alm = alm + r'''
\usepackage{xcolor}  % highlight double moon events on same day'''

    # Note: \DeclareUnicodeCharacter is not compatible with some versions of pdflatex
    alm = alm + r'''
\definecolor{darknight}{rgb}{0.18, 0.27, 0.33}
\definecolor{khaki}{rgb}{0.76, 0.69, 0.57}
\usepackage{multirow}
\newcommand{\HRule}{\rule{\linewidth}{0.5mm}}
\setlength{\footskip}{15pt}
\usepackage[pdftex]{graphicx}	% for \includegraphics
\usepackage{tikz}				% for \draw  (load after 'graphicx')
%\showboxbreadth=50  % use for logging
%\showboxdepth=50    % use for logging
%\DeclareUnicodeCharacter{00B0}{\ensuremath{{}^\circ}}
\setlength\fboxsep{1.5pt}       % ONLY used by \colorbox in alma_skyfield.py
\begin{document}'''

    alm = alm + r'''
% for the title page only...
\newgeometry{{nomarginpar, top={}, bottom={}, left={}, right={}}}'''.format(tm1,bm1,lm1,rm1)

    alm = alm + r'''
    \begin{titlepage}
    \begin{center}
    \textsc{\Large Generated using Skyfield}\\
    \large http://rhodesmill.org/skyfield/\\[0.7cm]'''
    
    if config.dockerized:   # DOCKER ONLY
        fn1 = "../A4chart0-180_P.pdf"
        fn2 = "../A4chart180-360_P.pdf"
    else:
        fn1 = "./A4chart0-180_P.pdf"
        fn2 = "./A4chart180-360_P.pdf"

    alm = alm + r'''
    % TRIM values: left bottom right top
    \includegraphics[clip, trim=12mm 20cm 12mm 21mm, width=0.92\textwidth]{{{}}}\\[0.3cm]
    \includegraphics[clip, trim=12mm 20cm 12mm 21mm, width=0.92\textwidth]{{{}}}\\'''.format(fn1,fn2)

    alm = alm + r'''[{}]
    \textsc{{\huge The Nautical Almanac}}\\[{}]'''.format(vsep1,vsep2)

    if dtp == 0:
        alm = alm + r'''
    \HRule \\[0.5cm]
    {{ \Huge \bfseries {}}}\\[0.2cm]
    \HRule \\'''.format(year)
    elif dtp == -1:
        alm = alm + r'''
    \HRule \\[0.5cm]
    {{ \Huge \bfseries {}}}\\[0.2cm]
    \HRule \\'''.format(first_day.strftime("%B %Y"))
    elif dtp > 1:
        alm = alm + r'''
    \HRule \\[0.5cm]
    {{ \Huge \bfseries {}}}\\[0.2cm]
    \HRule \\'''.format(fmtdates(first_day,first_day+timedelta(days=dtp-1)))
    else:
        alm = alm + r'''
    \HRule \\[0.5cm]
    {{ \Huge \bfseries {}}}\\[0.2cm]
    \HRule \\'''.format(fmtdate(first_day))

    alm = alm + r'''
    \begin{center}\begin{tabular}[t]{rl}
    \large\emph{Author:} & \large Andrew \textsc{Bauer}\\
    \large\emph{Original concept from:} & \large Enno \textsc{Rodegerdts}\\
    \end{tabular}\end{center}'''

    alm = alm + r'''
    {\large \today}
    \HRule \\[0.2cm]
    \end{center}
    \begin{description}[leftmargin=5.5em,style=nextline]\footnotesize
    \item[Disclaimer:] These are computer generated tables - use them at your own risk.
    The accuracy has been randomly checked with JPL HORIZONS System, but cannot be guaranteed.
    The author claims no liability for any consequences arising from use of these tables.
    Besides, this publication only contains the 'daily pages' of the Nautical Almanac: an official version of the Nautical Almanac is indispensable.
    \end{description}
\end{titlepage}
\restoregeometry    % so it does not affect the rest of the pages'''

    alm = alm + pages(first_day,dtp,ts)
    alm = alm + '''
\end{document}'''
    return alm