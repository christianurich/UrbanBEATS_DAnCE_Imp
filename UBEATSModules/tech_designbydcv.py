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

import numpy as np
import tech_templates as tt

def retrieveDesign(pathname, systemtype, ksat, targets):
    #Step 1: Read DCV file
    dcv = readDCVFile(pathname, systemtype)
    #print "Designing for : ", ksat
    #Step 2: Get Brackets
    k0, k1, lowbrack, upbrack = bracketDCVFile(dcv, ksat)
    
    #Step 3: Get both sets of areas
    areaslower = findTargetSize(lowbrack, targets)
    areasupper = findTargetSize(upbrack, targets)
    
    #Step 4: Get final design area
    finalarea = getFinalSizeRequirement(k0, k1, areaslower, areasupper, ksat)
    
    return finalarea


def readDCVFile(pathfname, systemtype):
    f = open(pathfname, 'r')    #Note: must do conversion to raw string or else will not work on some PCs
    designcurve = []
    for lines in f:
        designcurve.append(lines.split(','))          
    f.close()
    finaldcv = [[],[],[],[],[],[],[]]
    for i in range(len(designcurve)):
        if i == 0:
            #print designcurve[i]
            continue
        for j in range(len(designcurve[i])):
            # print designcurve[i][j]
            finaldcv[j].append(float(designcurve[i][j]))
    return finaldcv

def bracketDCVFile(array, ksat):
    #function to retrieve the arrays from the DCV file from which design can be undertaken
    #   array = dcv array
    #   ksat = exfiltration rate for which to find the bracket
    #   match = indicates whether it's an close match (0) or a double bracket (1)
    #           if exact, function returns one array, if double bracket, function returns two arrays

    #Step 1: obtain unique kvalue
    kuniques = []
    for i in array[1]:
        if i in kuniques:
            continue
        kuniques.append(i)
    #print kuniques
    
    #Step 2a: check if ksat falls within the k-values of the dcv, if not, only work with one bracket
    kmin = min(array[1])
    #print "Kmin ", kmin
    kmax = max(array[1])
    if ksat <= kmin or ksat >= kmax:
        #print "Warning, ksat is not within bounds of dcv file, using single value"
        if ksat <= kmin:
            klow = kmin
            kup = kmin
        else:
            klow = kmax
            kup = kmax
    else:
        #Step 2b: if there are two brackets because ksat falls within range of kmin, kmax, find the values
        klow = kmin    #initialize lower and upper k brackets
        kup = klow
        for i in range(len(kuniques)):
            if kup > ksat:
                continue
            klow = kuniques[i]
            kup = kuniques[i+1]
        #print klow, kup
    
    #Step 3: Retrieve brackets        
    lowerbracket = [[],[],[],[],[],[],[]]
    upperbracket = [[],[],[],[],[],[],[]]
    if klow == kup:     #one bracket
        index = array[1].index(klow)
        while array[1][index] == klow:
            for i in range(7):
                lowerbracket[i].append(array[i][index])
                upperbracket[i].append(array[i][index])                
            if index == len(array[1])-1:    #if kup is the last bracket in the file, need to terminate while loop in a different way
                break
            else:
                index += 1
        #print lowerbracket
        #print upperbracket
    
    if klow != kup: #two brackets
        index = array[1].index(klow)
        while array[1][index] == klow:
            for i in range(7):
                lowerbracket[i].append(array[i][index])
            if index == len(array[1])-1:    #if kup is the last bracket in the file, need to terminate while loop in a different way
                break
            else:
                index += 1
            index += 1
        index = array[1].index(kup)
        while array[1][index] == kup:
            for i in range(7):
                upperbracket[i].append(array[i][index])
            if index == len(array[1])-1:    #if kup is the last bracket in the file, need to terminate while loop in a different way
                break
            else:
                index += 1
        #print lowerbracket
        #print upperbracket
    
    return klow, kup, lowerbracket, upperbracket
    
def findTargetSize(bracket, targetvalues):
    #retrieves the required system size for given targetvalues
    Apercent = []   #holds five values: Q, TSS, TP, TN, GP 
    #loop through the five different targets    
    for i in range(len(targetvalues)):
        #find the value in the bracket
        targetmax = max(bracket[i+2])   #offset the index by 2
        #print targetmax        
        target = targetvalues[i]
        #print target
        if target > targetmax:      #if required target exceeds that of max, cannot design
            #print ".dcv designs cannot meet current target"
            Apercent.append(np.inf)
            continue
        elif target == 0:
            Apercent.append(0)
            continue    #if target is zero, just return zero
        lower = 0                   #initialize lower and upper variables
        upper = min(bracket[i+2])
        for j in range(len(bracket[i+2])):
            if target <= upper:
                continue
            lower = upper
            upper = bracket[i+2][j]
        #grab indices for Asystem in bracket[0]
        if lower == 0:       #but if the lower bound is zero, which isn't in the .dcv, go straight to interpolation
            Apercent.append(linearInterpolate(lower, upper, 0, bracket[0][0], target))
            continue
        mindex = bracket[i+2].index(lower)
        maxdex = mindex + 1
        Apercent.append(linearInterpolate(lower, upper, bracket[0][mindex], bracket[0][maxdex], target))
    #final Apercent has sizes for [Qreduction, TSSreduction, TPreduction, TNreduction, GPreduction]
    return Apercent

def getFinalSizeRequirement(klow, kup, minsizes, maxsizes, ksat):        
    #retrieves the final system size required based on two sets of sizes for the lower and upper kbracket
    if klow == kup:       #if there was only one bracket, no interpolation needed
#        print max(minsizes) #min and max sizes are identical        
        return float(max(minsizes))/100    #the maximum size among the brackets
        
    Apercent = []   #initialize possible areas
    for i in range(len(minsizes)):
        if minsizes[i] == np.inf or maxsizes[i] == np.inf:
            Apercent.append(np.inf)
        else:
            Apercent.append(linearInterpolate(klow, kup, minsizes[i], maxsizes[i], ksat))
#    print Apercent
    Afinal = max(Apercent)
#    print "Final Ap: "+str(Afinal)
    return float(Afinal)/100

def linearInterpolate(x0, x1, y0, y1, x):
    # print x0, x1, y0, y1, x
    y = y0+(x - x0)*((y1 - y0)/(x1 - x0))
    return y

### ------------------------------------------------------------------------ ###
###     SUBFUNCTIONS FOR STORMWATER HARVESTING BENEFITS                      ###
### ------------------------------------------------------------------------ ###

def treatQTYbenefits(wsudobj, runoffrate, designAimp):
    """Determines the SWH benefits for runoff volume reduction, expressed as an impervious area offset (IAO). The IAO
    data is written to the object's attribute self.__quantityIAO. It is calculated based on the runoff rate and the
    size of the treatment store, which in turn determines how much runoff is removed from the system.
    - WSUDobj - the tech object representing the WSUD system in place (with harvesting capabilities)
    - runoffrate - the runoff rate in the catchment, based on user input or based on rainfall runoff modelling
            (consider only the impervious portion)
    - designAimp - the impervious area that the harvesting system's treatment was designed for
    """
    storagedata = wsudobj.getRecycledStorage()
    if storagedata == None:
        return True

    reliability = float(storagedata.getReliability()) / 100.0   #Needed to work our actual extraction
    systype = wsudobj.getType()
    Aimp = designAimp                       #[sqm]
    supply = storagedata.getSupply()        #[kL]
    vextracted = supply * reliability       # supply x [kL] at 80% reliability = amount extracted

    # print "Reliability", reliability, "Aimp", Aimp, "supply", supply, "extracted", vextracted

    quantityIAO = (vextracted / runoffrate)    #[kL] / [kL/sqm/yr] = sqm impervious catchment offset
    wsudobj.setIAO("Qty", quantityIAO)
    return True

def initializeSWHbenefitsTable(filepath):
    """Initialises the SWH benefits dictionary from the swhbenefits.cfg file, which contains the lookup table of
    empirical m-values and bthresh values for calculating impervious area offset (IAO) for water quality control.
    """
    f = open(filepath+"/swhbenefits.cfg", 'r')
    swhbenefitstable = []
    f.readline()
    for lines in f:
        data = lines.split(',')
        data[2] = float(data[2])    #Convert target to float
        data[3] = float(data[3])    #Convert m-value to float
        data[4] = float(data[4])    #Convert bthresh to float
        swhbenefitstable.append(data)

    return swhbenefitstable


def treatWQbenefits(wsudobj, runoffrate, targets, designAimp, swhbenefitstable):
    """Determines the SWH benefits for pollution reduction, expressed as an impervious area offset (IAO). The IAO
    data is written to the object's attribute self.__quantityIAO. It is calculated based on the empirical relationships
    developed from numerous MUSIC simulations and the size of the treatment store, which in turn determines how much
    water is removed from the system.
    - WSUDobj - the tech object representing the WSUD system in place (with harvesting capabilities)
    - runoffrate - the runoff rate in the catchment, based on user input or based on rainfall runoff modelling
            (consider only the impervious portion)
    - targets - an array of TSS, TP, TN targets that the treatment system has been designed for
    - designAimp - the impervious area that the harvesting system's treatment was designed for
    - swhbenefitstable - the lookup table for stormwater harvesting benefits, which is initialised in techplacement and passed
            to this function.
    """
    storagedata = wsudobj.getRecycledStorage()

    if storagedata == None:
        return True

    systype = wsudobj.getType()
    reliability = float(storagedata.getReliability()) / 100.0

    Aimp = designAimp
    if Aimp == 0:
        return True

    supply = storagedata.getSupply()
    vextracted = supply * reliability   # supply x [kL] at 80% reliability = amount extracted
    totalrunoff = runoffrate * Aimp     #Total runoff volume that treatment system is targeting
    pext = min(vextracted / totalrunoff, 1.0)

    # print "Reliability", reliability, "Aimp", Aimp, "supply", supply, "extracted", pext

    m, bthresh = lookupSWHbenefit(systype, targets, swhbenefitstable)

    #Apply the SWH Benefits equation for water quality
    qualityIAOs = []    #will have IAOs based on TSS, TP, TN, the final is the minimum of all three or zero

    for i in range(len(m)):
        qualityIAOs.append(m[i] * max((pext - bthresh[0]),0) * Aimp)  #Additional impervious area that can be left untreated for water quality
                                                                      #based on the stormwater harvesting benefits perceived [sqm].
    if len(m) == 0:
        qualityIAO = 0.0                    #just to avoid the ValueError if an empty array is tested for its minimum.
    else:
        qualityIAO = min(qualityIAOs)         #minimum of the three
        qualityIAO = max(qualityIAO, 0.0)     #if the benefits is less than zero, adjust to zero

    wsudobj.setIAO("WQ", qualityIAO)
    return True


def lookupSWHbenefit(systype, targets, swhbenefitstable):
    """Lookup function for the empirical SWH benefits equation for pollution management. The lookup is driven by
    system type and the treatment targets.
    """
    m = []           #The slope of the empirical benefits equation, i.e. rate of IAO increase per unit extraction
    bthresh = []     #The extraction threshold at which benefits begin

    #Lookup m and bthresh for the different targets and pick the worst case scenario.
    sysTSS = []
    sysTP = []
    sysTN = []
    # print swhbenefitstable
    for i in range(len(swhbenefitstable)):
        if swhbenefitstable[i][0] != systype:
            continue
        # print "sys"+str(swhbenefitstable[i][1])+".append("+(str(swhbenefitstable[i]))+")"
        eval("sys"+str(swhbenefitstable[i][1])+".append("+(str(swhbenefitstable[i]))+")")

    pollmatrix = [sysTSS, sysTP, sysTN]

    # print sysTSS, sysTP, sysTN

    #Interpolate for given targets to get m and bthresh values
    for i in range(len(targets)):
        curpoll = pollmatrix[i]
        curpollT = [[row[j] for row in curpoll] for j in range(len(curpoll[0]))]    #List comprehension to transport the matrix
        # print "DEBUG", curpollT
        curtarget = targets[i]

        #Work out the m and b values by interpolation
        # print "CURTARGET", curtarget
        if curtarget in curpollT[2]:        #If the target is identical to the target for which m and b values exist then simply select
            m.append(curpollT[3][curpollT[2].index(curtarget)])
            bthresh.append(curpollT[4][curpollT[2].index(curtarget)])
        elif curtarget < min(curpollT[2]):  #if the target is less than the minimum in the table, use the minimum benefits
            m.append(curpoll[3][curpollT.index(min(curpollT[2]))])
            bthresh.append(curpoll[4][curpollT.index(min(curpollT[2]))])
        elif curtarget > max(curpollT[2]):   #If the target is greater than the maximum in the table, assume no benefit
            m.append(0)
            bthresh.append(0)
        else:       #finally, if none of the above apply, then the target is between the bounds
            j_index, found = 0, 0
            while found == 0:
                if curtarget < curpollT[2][j_index] and curtarget > curpollT[2][j_index + 1]: #if less than
                    tupper, tlower = curpollT[2][j_index], curpollT[2][j_index + 1]   #X
                    mupper, mlower = curpollT[3][j_index], curpollT[3][j_index + 1]   #Y1
                    bupper, blower = curpollT[4][j_index], curpollT[4][j_index + 1]   #Y2
                    found = 1
                else: j_index += 1
            m.append(linearInterpolate(tlower,tupper,mlower,mupper,curtarget))  #Interpolate for m
            if bupper == 0 and blower == 0:
                bthresh.append(0)
            else:
                bthresh.append(linearInterpolate(tlower,tupper,blower,bupper,curtarget))  #Interpolate for bthresh
    # print "Debug", m, bthresh
    return m, bthresh

