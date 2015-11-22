# -*- coding: utf-8 -*-
"""
@file
@author  Peter M Bach <peterbach@gmail.com>
@version 1.0
@section LICENSE

This file is part of UrbanBEATS
Copyright (C) 2012-2015  Peter M Bach

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
"""
import math as m
import numpy as np
import tech_designbydcv as ddcv
import tech_templates as tt

########################################################
#DESIGN FUNCTIONS FOR DIFFERENT TECHNOLOGIES           #
########################################################

#---BIOFILTRATION SYSTEM/RAINGARDEN [BF]----------------------------------------
def design_BF(Aimp, dcv, targets, tech_apps, soilK, systemK, minsize, maxsize):
    #Design of Biofiltration systems
    #   input: Imparea = Impervious Area to treat
    #          tarQ = Runoff reduction target
    #          tarTSS = TSS reduction target
    #          tarTP = TP reduction target
    #          tarTN = TN reduction target
    #          soilK = soil hydraulic conductivity
    #          maxsize = maximum allowable system size
    tarQ, tarTSS, tarTP, tarTN = targets[0:4]
    tarQ *= tech_apps[0]
    tarTSS *= tech_apps[1]
    tarTP *= tech_apps[1]
    tarTN *= tech_apps[1]
    
    exfil = min(soilK, systemK)
    #print Aimp, tarTSS, tarTP, tarTN, exfil
    if Aimp == 0:   #if there is no impervious area to design for, why bother?
        return [None, 1]
    #size the system for runoff reduction and pollution reduction independently
    if soilK != 0:
        psystem = ddcv.retrieveDesign(dcv, "BF", exfil, [tarQ, tarTSS, tarTP, tarTN, 100])
    else:
        psystem = np.inf
        
    if psystem == np.inf or psystem == 0:
        return [None, 1]
    
    system_area = max(Aimp * psystem, minsize)  #the larger of the two
    
    #if the system design has passed to this point: i.e. not impossible and there is impervious to treat, then add planning constraints
    
    if system_area > maxsize:          #if the final design exceeds the maximum allowable size, forget it!
        #print "Warning, Maximum System Size Exceeded"
        return [None, 1]
        
    #an infiltrating system (extra space around it required), determine the setback required
    if soilK > 180:
        setback = 1.0   #metres
    elif soilK > 36:
        setback = 2.0   #metres
    elif soilK > 3.6:
        setback = 4.0   #metres
    else:
        setback = 5.0   #metres
    
    Areq = m.pow((m.sqrt(system_area)+2*setback),2)
    #print "Arequired", Areq
    diff = Areq/system_area
    #final check, if the system has exceeded maximum size, return 'impossible' = inf
    return [Areq, diff]

#---INFILTRATION SYSTEMS [IS]---------------------------------------------------
def design_IS(Aimp, dcv, targets, tech_apps, soilK, systemK, minsize, maxsize):
    #Design of Infiltration systems
    #   input: Imparea = Impervious Area to treat
    #          tarQ = Runoff reduction target
    #          tarTSS = TSS reduction target
    #          tarTP = TP reduction target
    #          tarTN = TN reduction target
    #          soilK = soil hydraulic conductivity
    #          maxsize = maximum allowable system size
    tarQ, tarTSS, tarTP, tarTN = targets[0:4]
    tarQ *= tech_apps[0]
    tarTSS *= tech_apps[1]
    tarTP *= tech_apps[1]
    tarTN *= tech_apps[1]
    
    exfil = min(soilK, systemK)
    
    if Aimp == 0:   #if there is no impervious area to design for, why bother?
        return [None, 1]
    
    #size the system
    if soilK != 0:
        psystem = ddcv.retrieveDesign(dcv, "IS", exfil, [tarQ, tarTSS, tarTP, tarTN, 100])
        #print psystem
    else:
        psystem = np.inf
        
    if psystem == np.inf or psystem == 0:       #if the system cannot be designed, it will return infinity
        return [None, 1]
    
    system_area = max(Aimp * psystem, minsize)  #the larger of the two
    
    if system_area > maxsize:          #if the final design exceeds the maximum allowable size, forget it!
        #print "Warning, Maximum System Size Exceeded"
        return [None, 1]
    
    #if the system design has passed to this point: i.e. not impossible and there is impervious to treat, then add planning constraints
    #find setback requirement based on soilK
    if soilK >= 3600:
        setback = 1.0
    elif soilK >= 1800:
        setback = 1.0
    elif soilK >= 360:
        setback = 1.0
    elif soilK >= 180:
        setback = 1.0
    elif soilK > 36:
        setback = 2
    elif soilK > 3.6:
        setback = 4.0   #metres
    else:
        #print "Soil is unsuitable for infiltration"
        return [None, 1]

    Areq = m.pow((m.sqrt(system_area)+2*setback),2)
#    print "Required Area: ", Areq
    diff = Areq/system_area
    return [Areq, diff]

#---PONDS & BASINS [PB]---------------------------------------------------------
def design_PB(Aimp, dcv, targets, tech_apps, soilK, systemK, minsize, maxsize ):
    #Design of Ponds & Lakes
    #   input: Imparea = Impervious Area to treat
    #          tarQ = Runoff reduction target
    #          tarTSS = TSS reduction target
    #          tarTP = TP reduction target
    #          tarTN = TN reduction target
    #          soilK = soil hydraulic conductivity
    #          maxsize = maximum allowable system size
    tarQ, tarTSS, tarTP, tarTN = targets[0:4]
    tarQ *= tech_apps[0]
    tarTSS *= tech_apps[1]
    tarTP *= tech_apps[1]
    tarTN *= tech_apps[1]
    
    exfil = min(soilK, systemK)
    
    if Aimp == 0:   #if there is no impervious area to design for, why bother?
        return [None, 1]
    #size the system
    if soilK != 0:
        psystem = ddcv.retrieveDesign(dcv, "PB", exfil, [tarQ, tarTSS, tarTP, tarTN, 100])
    else:
        psystem = np.inf
        
    if psystem == np.inf or psystem == 0:       #if the system cannot be designed, it will return infinity
        return [None, 1]
    
    system_area = max(Aimp * psystem, minsize)  #the larger of the two
    
    if system_area > maxsize:          #if the final design exceeds the maximum allowable size, forget it!
        #print "Warning, Maximum System Size Exceeded"
        return [None, 1]
    
    #add extra area to the system (multipliers for batters)
    batter_multiplier = 1.3
    
    Areq = system_area * batter_multiplier
    diff = Areq/system_area
    return [Areq, diff]

def sizeStoreArea_PB(vol, sysdepth, minsize, maxsize):
    surfarea = vol / sysdepth       #[sqm]
    Asystem = surfarea
    if surfarea < minsize:
        Asystem = minsize
    if surfarea > maxsize:
        return [None, 1]
    
    Areq = Asystem * 1.3   #batter multiplier
    diff = Areq/Asystem

    return [Areq, diff]    #No buffer for raintanks

#---SURFACE WETLANDS [WSUR]-----------------------------------------------------
def design_WSUR(Aimp, dcv, targets, tech_apps, soilK, systemK, minsize, maxsize ):
    #Design of Ponds & Lakes
    #   input: Imparea = Impervious Area to treat
    #          tarQ = Runoff reduction target
    #          tarTSS = TSS reduction target
    #          tarTP = TP reduction target
    #          tarTN = TN reduction target
    #          soilK = soil hydraulic conductivity
    #          maxsize = maximum allowable system size
    tarQ, tarTSS, tarTP, tarTN = targets[0:4]
    tarQ *= tech_apps[0]
    tarTSS *= tech_apps[1]
    tarTP *= tech_apps[1]
    tarTN *= tech_apps[1]
    
    exfil = min(soilK, systemK)
    
    if Aimp == 0:   #if there is no impervious area to design for, why bother?
        return [None, 1]
    #size the system
    if soilK != 0:
        psystem = ddcv.retrieveDesign(dcv, "WSUR", exfil, [tarQ, tarTSS, tarTP, tarTN, 100])
    else:
        psystem = np.inf    
    
    if psystem == np.inf or psystem == 0:       #if the system cannot be designed, it will return infinity
        return [None, 1]
    
    system_area = max(Aimp * psystem, minsize)  #the larger of the two
       
    if system_area > maxsize:   #if the final design exceeds the maximum allowable size, forget it!
        #print "Warning, Maximum System Size Exceeded"
        return [None, 1]
    
    #add extra area to the system (multipliers for batters)
    batter_multiplier = 1.3
    
    Areq = system_area * batter_multiplier
    diff = Areq/system_area
    
    return [Areq, diff]

def sizeStoreArea_WSUR(vol, sysdepth, minsize, maxsize):
    surfarea = vol / sysdepth       #[sqm]
    Asystem = surfarea
    if surfarea < minsize:
        Asystem = minsize
    if surfarea > maxsize:
        return [None, 1]
    
    Areq = Asystem * 1.3   #batter multiplier
    diff = Areq/Asystem

    return [Areq, diff]    #No buffer for raintanks

#---SWALES & BUFFER STRIPS [SW]-------------------------------------------------
def design_SW(Aimp, dcv, targets, tech_apps, soilK, systemK, minsize, maxsize ):
    #Design of Ponds & Lakes
    #   input: Imparea = Impervious Area to treat
    #          tarQ = Runoff reduction target
    #          tarTSS = TSS reduction target
    #          tarTP = TP reduction target
    #          tarTN = TN reduction target
    #          soilK = soil hydraulic conductivity
    #          maxsize = maximum allowable system size
    tarQ, tarTSS, tarTP, tarTN = targets[0:4]
    tarQ *= tech_apps[0]
    tarTSS *= tech_apps[1]
    tarTP *= tech_apps[1]
    tarTN *= tech_apps[1]
    
    exfil = min(soilK, systemK)
    
    dcSW = [[0,0.1,0.2,0.5,1.0,1.5,2,2.5,3], \
            [0,50,70,81,89,90,91,91.5,92], \
            [0,30,45,55,60,62,64,65,65], \
            [0,7,11,19,24,28,30,32.5,35]]
            #design curve for swales & buffer strips
            #column 0 = area of system (as % of imp. area)
            #columns 1 to 3 = TSS, TP, TN reduction achieved (%)
    
    sizes = []         #initialize variables
    targets = [tarTSS, tarTP, tarTN]
    pollutant = ["TSS", "TP", "TN"]
    cannot_meet = 0
    for pol_index in [1, 2, 3]:
        #find size for TSS
        lower_bound = None
        upper_bound = dcSW[pol_index][0]
        up_row = 0
        for i in dcSW[pol_index][1:]:
            if max(dcSW[pol_index]) < targets[pol_index-1]:
                #print "Warning, cannot meet "+str(pollutant[pol_index-1])+" Target with current design standards!"
                cannot_meet = 1
                sizes.append(max(dcSW[0]))
                break
            up_row = up_row + 1
            lower_bound = upper_bound
            upper_bound = i
            if targets[pol_index-1] <= upper_bound:
                slope = (dcSW[0][up_row] - dcSW[0][up_row-1])/(upper_bound - lower_bound)
                sizes.append(dcSW[0][up_row-1]+(slope*(targets[pol_index-1] - lower_bound)))    
                break
    
    #calculate surface area of system required
    if cannot_meet == 1:
        return [None, 1]
    else:
        size_req = max(sizes)
        Asystem = max(Aimp * size_req/100, minsize)
    
    if Asystem > maxsize:          #if the final design exceeds the maximum allowable size, forget it!
        #print "Warning, Maximum System Size Exceeded"
        Areq = None
    
    #add extra area to the system
    
    if Aimp == 0:
        Areq = None
        #print "no area - no system"
    else:
        Areq = Asystem      #swales drain into a pipe, so no additional area required, just need to check what minimum allowable width is

    diff = 1.0
    
    return [Areq, diff]

#---RAINWATER/STORMWATAER TANK [RT]-------------------------------------------------
def sizeStoreArea_RT(vol, sysdepth, minsize, maxsize):
    
    surfarea = vol / sysdepth       #[sqm]
    Areq = surfarea
    #print "Area required: ", Areq
    if surfarea < minsize:
        Areq = minsize
    if surfarea > maxsize:
        # print "raintank no fit"
        return [None, 1]
    
    return [Areq, 1]    #No buffer for raintanks
        
    