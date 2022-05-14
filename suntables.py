#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#   Copyright (C) 2022  Andrew Bauer
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

###### Standard library imports ######
from datetime import datetime, timedelta
from math import copysign as copysign

###### Local application imports ######
import config
import alma_skyfield as alma_skyfield

#------------------------
#   internal functions
#------------------------

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

def fmtdate(d):
    if config.pgsz == 'Letter': return d.strftime("%m/%d/%Y")
    return d.strftime("%d.%m.%Y")

def fmtdates(d1,d2):
    if config.pgsz == 'Letter': return d1.strftime("%m/%d/%Y") + " - " + d2.strftime("%m/%d/%Y")
    return d1.strftime("%d.%m.%Y") + " - " + d2.strftime("%d.%m.%Y")

# >>>>>>>>>>>>>>>>>>>>>>>>
def suntab(date, n):
    # generates LaTeX table for sun only (traditional styla)
    tab = r'''\noindent
\begin{tabular*}{0.2\textwidth}[t]{@{\extracolsep{\fill}}|c|rr|}
'''
    while n > 0:
        tab = tab + r'''\hline
\multicolumn{{1}}{{|c|}}{{\rule{{0pt}}{{2.6ex}}\textbf{{{}}}}} & \multicolumn{{1}}{{c}}{{\textbf{{GHA}}}} & \multicolumn{{1}}{{c|}}{{\textbf{{Dec}}}}\\
\hline\rule{{0pt}}{{2.6ex}}\noindent
'''.format(date.strftime("%d"))

        ghas, decs, degs = alma_skyfield.sunGHA(date)
        h = 0

        if config.decf != '+':  # USNO format for Declination
            while h < 24:
                if h > 0:
                    prevDEC = degs[h-1]
                else:
                    prevDEC = degs[0]       # hour -1 = hour 0
                if h < 23:
                    nextDEC = degs[h+1]
                else:
                    nextDEC = degs[23]      # hour 24 = hour 23
                
                # format declination checking for hemisphere change
                printNS, printDEG = declCompare(prevDEC,degs[h],nextDEC,h)
                sdec = NSdecl(decs[h],h,printNS,printDEG,False)

                line = "{} & {} & {}".format(h,ghas[h],sdec)
                lineterminator = r'''\\
'''
                if h < 23 and (h+1)%6 == 0:
                    lineterminator = r'''\\[2Pt]
'''
                tab = tab + line + lineterminator
                h += 1

        else:			# Positive/Negative Declinations
            while h < 24:
                line = "{} & {} & {}".format(h,ghas[h],decs[h])
                lineterminator = r'''\\
'''
                if h < 23 and (h+1)%6 == 0:
                    lineterminator = r'''\\[2Pt]
'''
                tab = tab + line + lineterminator
                h += 1

        sds, dsm = alma_skyfield.sunSD(date)
        tab = tab + r'''\hline
\rule{{0pt}}{{2.4ex}} & 
\multicolumn{{1}}{{c}}{{SD={}$'$}} & 
\multicolumn{{1}}{{c|}}{{\textit{{d}}\,=\,{}$'$}}\\
\hline
'''.format(sds,dsm)
        if n > 1:
            # add space between tables...
            tab = tab + r'''\multicolumn{1}{c}{}\\[-0.5ex]'''
        n -= 1
        date += timedelta(days=1)

    tab = tab + r'''\end{tabular*}'''
    return tab

# >>>>>>>>>>>>>>>>>>>>>>>>
def suntabm(date, n):
    # generates LaTeX table for sun only (modern style)
    if config.decf != '+':	# USNO format for Declination
        colsep = "4pt"
    else:
        colsep = "3.8pt"
    
    tab = r'''\noindent
\renewcommand{{\arraystretch}}{{1.1}}
\setlength{{\tabcolsep}}{{{}}}
\begin{{tabular}}[t]{{crr}}'''.format(colsep)

    while n > 0:
##        print("n = {}".format(n))
        tab = tab + r'''
\multicolumn{{1}}{{c}}{{\footnotesize{{\textbf{{{}}}}}}} & \multicolumn{{1}}{{c}}{{\footnotesize{{\textbf{{GHA}}}}}} & \multicolumn{{1}}{{c}}{{\footnotesize{{\textbf{{Dec}}}}}}\\
\cmidrule{{1-3}}
'''.format(date.strftime("%d"))

        ghas, decs, degs = alma_skyfield.sunGHA(date)
        h = 0

        if config.decf != '+':  # USNO format for Declination
            while h < 24:
                band = int(h/6)
                group = band % 2
                if h > 0:
                    prevDEC = degs[h-1]
                else:
                    prevDEC = degs[0]       # hour -1 = hour 0
                if h < 23:
                    nextDEC = degs[h+1]
                else:
                    nextDEC = degs[23]      # hour 24 = hour 23
                
                # format declination checking for hemisphere change
                printNS, printDEG = declCompare(prevDEC,degs[h],nextDEC,h)
                sdec = NSdecl(decs[h],h,printNS,printDEG,True)

                line = r'''\color{{blue}}{{{}}} & '''.format(h)
                line = line + "{} & {}".format(ghas[h],sdec)
                if group == 1:
                    tab = tab + r'''\rowcolor{LightCyan}'''
                lineterminator = r'''\\
'''
                if config.pgsz == "A4" and h < 23 and (h+1)%6 == 0:
                    lineterminator = r'''\\[2Pt]
'''
                tab = tab + line + lineterminator
                h += 1

        else:			# Positive/Negative Declinations
            while h < 24:
                band = int(h/6)
                group = band % 2
                line = r'''\color{{blue}}{{{}}} & '''.format(h)
                line = line + "{} & {}".format(ghas[h],decs[h])
                if group == 1:
                    tab = tab + r'''\rowcolor{LightCyan}'''
                lineterminator = r'''\\
'''
                if config.pgsz == "A4" and h < 23 and (h+1)%6 == 0:
                    lineterminator = r'''\\[2Pt]
'''
                tab = tab + line + lineterminator
                h += 1

        sds, dsm = alma_skyfield.sunSD(date)
        tab = tab + r'''\cmidrule{{2-3}} & 
\multicolumn{{1}}{{c}}{{\scriptsize{{SD\,=\,{}$'$}}}} & \multicolumn{{1}}{{c}}{{\footnotesize{{\textit{{d}}\,=\,{}$'$}}}}\\
\cmidrule{{2-3}}'''.format(sds,dsm)
        # note: '\,' inserts a .166667em space in text mode 
        if n > 1:
            # add space between tables...
            tab = tab + r'''
\multicolumn{3}{c}{}\\[-1.5ex]'''
        n -= 1
        date += timedelta(days=1)
    tab = tab + r'''
\end{tabular}'''
    return tab

#----------------------
#   page preparation
#----------------------

def page(date, dpp=15):
    # time delta values for the initial date&time...
    dut1, deltat = alma_skyfield.getDUT1(date)
    timeDUT1 = r"DUT1 = UT1-UTC = {:+.4f} sec\quad$\Delta$T = TT-UT1 = {:+.4f} sec".format(dut1, deltat)

    if dpp > 1:
        str2 = r'''\textbf{{{} to {} UT}}'''.format(date.strftime("%Y %B %d"),(date+timedelta(days=dpp-1)).strftime("%b. %d"))
    else:
        str2 = r'''\textbf{{{} UT}}'''.format(date.strftime("%Y %B %d"))

    # creates a page(15 days) of the Sun almanac
    page = r'''
% ------------------ N E W   P A G E ------------------
\newpage
\sffamily
\noindent
\begin{{flushleft}}     % required so that \par works
{{\footnotesize {}}}\hfill{}
\end{{flushleft}}\par
\begin{{scriptsize}}
'''.format(timeDUT1, str2)

    if config.tbls == "m":
        while dpp > 0:
            page += suntabm(date,min(3,dpp))
            date += timedelta(days=3)
            dpp -= 3
            if dpp > 0: page = page + r'''\quad
'''
    else:
        while dpp > 0:
            page += suntab(date,min(3,dpp))
            date += timedelta(days=3)
            dpp -= 3

    # to avoid "Overfull \hbox" messages, leave a paragraph end before the end of a size change. (This may only apply to tabular* table style) See lines below...
    page = page + r'''

\end{scriptsize}'''
    return page

def pages(first_day, dtp):
    # dtp = 0 if for entire year; = -1 if for entire month; else days to print

    out = ''

    if dtp == 0:       # if entire year
        year = first_day.year
        yr = year
        dpp = 15      # 15 days per page maximum
        day1 = first_day
        while year == yr:
            day15 = day1 + timedelta(days=14)
            if day15.year != yr:
                dpp -= day15.day
                if dpp <= 0: return out
            out += page(day1, dpp)
            day1 += timedelta(days=15)
            year = day1.year
    elif dtp == -1:    # if entire month
        mth = first_day.month
        m = mth
        dpp = 15      # 15 days per page maximum
        day1 = first_day
        while mth == m:
            day15 = day1 + timedelta(days=14)
            if day15.month != m:
                dpp -= day15.day
                if dpp <= 0: return out
            out += page(day1, dpp)
            day1 += timedelta(days=15)
            mth = day1.month
    else:               # print 'dtp' days beginning with first_day
        day1 = first_day
        dpp = 15      # 15 days per page maximum
        while dtp > 0:
            if dtp <= 15: dpp = dtp
            out += page(day1, dpp)
            dtp -= 15
            day1 += timedelta(days=15)

    return out

#--------------------------
#   external entry point
#--------------------------

def sunalmanac(first_day, dtp):
    # dtp = 0 if for entire year; = -1 if for entire month; else days to print

    # make almanac starting from first_day
    year = first_day.year
    mth = first_day.month
    day = first_day.day

    # page size specific parameters
    if config.pgsz == "A4":
        # pay attention to the limited page width
        paper = "a4paper"
        tm = "21mm"
        bm = "18mm"
        lm = "12mm"     # 13mm
        rm = "12mm"     # 13mm
        if config.tbls == "m" and config.decf != '+':	# USNO format for Declination
            tm = "8mm"
            bm = "13mm"
            lm = "11mm"
            rm = "10mm"
        if config.tbls == "m" and config.decf == '+':	# Positive/Negative Declinations
            tm = "8mm"
            bm = "13mm"
            lm = "12mm"
            rm = "12mm"
    else:
        # pay attention to the limited page height
        paper = "letterpaper"
        tm = "12.2mm"
        bm = "13mm"
        lm = "15mm"     # 16mm
        rm = "15mm"     # 16mm
        if config.tbls == "m" and config.decf != '+':	# USNO format for Declination
            tm = "5mm"
            bm = "8mm"
            lm = "14mm"
            rm = "13mm"
        if config.tbls == "m" and config.decf == '+':	# Positive/Negative Declinations
            tm = "5mm"
            bm = "8mm"
            lm = "15mm"
            rm = "15mm"

    # default is 'oneside'...
    alm = r'''\documentclass[10pt, {}]{{report}}'''.format(paper)

    alm = alm + r'''
%\usepackage[utf8]{inputenc}
\usepackage[english]{babel}
\usepackage{fontenc}
\usepackage{enumitem} % used to customize the {description} environment'''

    if config.tbls == "m":
        alm = alm + r'''
\usepackage[table]{xcolor}
\definecolor{LightCyan}{rgb}{0.88,1,1}
\usepackage{booktabs}'''

    # to troubleshoot add "showframe, verbose," below:
    alm = alm + r'''
\usepackage[nomarginpar, top={}, bottom={}, left={}, right={}]{{geometry}}'''.format(tm,bm,lm,rm)

    # Note: \DeclareUnicodeCharacter is not compatible with some versions of pdflatex
    alm = alm + r'''
\newcommand{\HRule}{\rule{\linewidth}{0.5mm}}
\setlength{\footskip}{15pt}
\usepackage[pdftex]{graphicx}
%\showboxbreadth=50  % use for logging
%\showboxdepth=50    % use for logging
%\DeclareUnicodeCharacter{00B0}{\ensuremath{{}^\circ}}
\begin{document}
% for the title page and page 2 only...
\newgeometry{nomarginpar, top=5mm, bottom=13mm, left=20mm, right=14mm}'''

    alm = alm + r'''
    \begin{titlepage}\vspace*{1.5cm}
    \begin{center}
    \textsc{\Large Generated using Skyfield}\\
    \large http://rhodesmill.org/skyfield/\\[1.5cm]'''

    if config.dockerized:   # DOCKER ONLY
        fn = "../Ra"
    else:
        fn = "./Ra"

    alm = alm + r'''
    \includegraphics[width=0.4\textwidth]{{{}}}\\[1cm]
    \textsc{{\huge The Nautical Almanac for the Sun}}\\[0.7cm]'''.format(fn)

    if dtp == 0:
        alm = alm + r'''
    \HRule \\[0.6cm]
    {{ \Huge \bfseries {}}}\\[0.4cm]
    \HRule \\[1.5cm]'''.format(year)
    elif dtp == -1:
        alm = alm + r'''
    \HRule \\[0.6cm]
    {{ \Huge \bfseries {}}}\\[0.4cm]
    \HRule \\[1.5cm]'''.format(first_day.strftime("%B %Y"))
    elif dtp > 1:
        alm = alm + r'''
    \HRule \\[0.6cm]
    {{ \Huge \bfseries {}}}\\[0.4cm]
    \HRule \\[1.5cm]'''.format(fmtdates(first_day,first_day+timedelta(days=dtp-1)))
    else:
        alm = alm + r'''
    \HRule \\[0.6cm]
    {{ \Huge \bfseries {}}}\\[0.4cm]
    \HRule \\[1.5cm]'''.format(fmtdate(first_day))

    alm = alm + r'''
    \begin{center} \large
    \emph{Author:}\\
    Andrew \textsc{Bauer}\\[6Pt]
    \emph{Original concept from:}\\
    Enno \textsc{Rodegerdts}
    \end{center}'''

    alm = alm + r'''
    \vfill
    {\large \today}
    \HRule \\[0.6cm]
    \end{center}
    \begin{description}[leftmargin=5.5em,style=nextline]\footnotesize
    \item[Disclaimer:] These are computer generated tables - use them at your own risk.
    The accuracy has been randomly checked with JPL HORIZONS System, but cannot be guaranteed.
    The author claims no liability for any consequences arising from use of these tables.
    Besides, this publication only contains sun tables: an official version of the Nautical Almanac is indispensable.
    \end{description}
\end{titlepage}
'''

    alm = alm + r'''
    \setcounter{page}{2}    % otherwise it's 1
    \vspace*{2cm}
    \noindent
    DIP corrects for height of eye over the surface. This value has to be subtracted from the sextant altitude ($H_s$). The  correction in degrees for height of eye in meters is given by the following formula: 
    \[d=0.0293\sqrt{m}\]
    This is the first correction (apart from index error) that has to be applied to the measured altitude.\\[12pt]
    \noindent
    The next correction is for refraction in the earth's atmosphere. As usual this table is correct for 10$^\circ$C and a pressure of 1010 hPa. This correction has to be applied to apparent altitude ($H_a$). The exact values can be calculated by the following formula.
    \[R_0=\cot \left( H_a + \frac{7.31}{H_a+4.4}\right)\]
    For other than standard conditions, calculate a correction factor for $R_0$ by: \[f=\frac{0.28P}{T+273}\] where $P$ is the pressure in hectopascal and $T$ is the temperature in $^\circ$C.\\[12pt]
    \noindent
    Semidiameter has to be added for lower limb sights and subtracted for upper limb sights. The value for semidiameter is tabulated in the daily pages.\\[12pt]
    \noindent
    To correct your sextant altitude $H_s$ do the following:
    Calculate $H_a$ by
     \[H_a= H_s+I-d\] 
    where $I$ is the sextant's index error and $d$ is DIP. Then calculate the observed altitude $H_o$ by
    \[H_o= H_a-R+P\pm SD\]
    where $R$ is refraction, $P$ is parallax and $SD$ is the semidiameter.\\[12pt]
    \noindent
    Sight reduction tables can be downloaded for the US government's internet pages. Search for HO-229 or HO-249.  These values can also be calculated with two, relatively simple, formulas:
    \[ \sin H_c= \sin L \sin d + \cos L \cos d \cos LHA\]
    and
    \[\cos A = \frac{\sin d - \sin L \sin H_c}{\cos L \cos H_c}\]
    where $A$ is the azimuth angle, $L$ is the latitude, $d$ is the declination and $LHA$ is the local hour angle. The azimuth ($Z_n$) is given by the following rule:
    \begin{itemize}
    \item if the $LHA$ is greater than $180^\circ$,\quad$Z_n=A$
    \item if the $LHA$ is less than $180^\circ$,\quad$Z_n = 360^\circ - A$
    \end{itemize}
\restoregeometry    % so it does not affect the rest of the pages'''

    alm = alm + pages(first_day,dtp)
    alm = alm + '''
\end{document}'''
    return alm