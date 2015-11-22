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

### ------------------------------------------------------------------------ ###
###     SUBFUNCTIONS FOR STORAGE-BEHAVIOUR SIMULATION                        ###
### ------------------------------------------------------------------------ ###

def estimateStoreVolume(inflowseries, demandseries, targetrel, estTol, maxiter):
    """Storage-behaviour model to size an optimum system size based on the inflow
    and outflow timeseries input to the model.
    Note that inflow and outflow timeseries must be of the same length!
        - inflowseries: single-dimensional list of inflow into tanke
        - demandseries: a single-dimensional list of demand values
        - targetrel: the target reliability to be achieved
        - estTol: the tolerance level acceptable
        - maxiter: maximum number of iterations permissible before an 
                    interpolation is done, prevent computational explosion
    """
    if len(inflowseries) != len(demandseries):
        #print "Error, inflow/demand time series must be of the same time step"
        return False
    
    if targetrel > 95:
        targetrel = 95  #cannot be greater than 95% for convergence reasons
    
    #Estimate an initial storage volume to begin
    days = len(inflowseries)
    years = days/365
    volest = (sum(inflowseries)/years) / 2      #Begin at 50% of average annual inflow
    #Initialize bounding volumes and reliabilities
    lowervol, lowerrel = 0,0
    uppervol, upperrel = sum(inflowseries), 100
    
    #Iterate to find optimum storage volume (Bisection)
    relTol = upperrel - lowerrel        #reliability range tolerance
    iterationcount = 0
    while estTol < relTol and iterationcount < maxiter: # or volestdiff > 0.0001:   #keep looping until the relTol is less than estTol
        iterationcount += 1
        currel = calculateTankReliability(inflowseries, demandseries, volest)
        if currel > targetrel:
            uppervol = volest
            upperrel = currel
        elif currel < targetrel:
            lowervol = volest
            lowerrel = currel
        volest = (uppervol + lowervol)/2     #if est. Rel is larger than target, halve volume
        relTol = upperrel - lowerrel    #recalculate reliability difference to check against tolerance
        
    #print "Total Iterations Needed: ", iterationcount
    #End of loop, we have bounding volumes and reliability, linearly interpolate
    storageVol = linearInterpolate(lowervol, uppervol, lowerrel, upperrel, targetrel)
    #print "Final Volume: ", storageVol    
    storageREL = calculateTankReliability(inflowseries, demandseries, storageVol)
    #print "Final Reliability: ", storageREL, "%"
    
    if abs(targetrel - storageREL) > 1: #within +/- 2% reliability accuracy
        return np.inf   #Cannot find a store with that reliability, return infinity
    return storageVol
    
def calculateTankReliability(inflowseries, demandseries, volume):
    """Runs a storage-behaviour simulation (Yield after spill order) and returns
    the reliability of the input volume
        - inflowseries: a single-dimensional list of all inflows
        - demandseries: a single-dimensional list of all demands for that timestep
        - volume: the store volume
    """
    cV = 0      #current Volume in store set to zero at start
    cumuspill = 0
    cumudemand = sum(demandseries)
    cumusupply = 0
    for i in range(len(inflowseries)):
        cV += inflowseries[i]   #add inflow
        
        #YIELD AFTER SPILL (YAS)
        if cV > volume:
            cumuspill += cV - volume
            cV = volume
        
        todaydemand = demandseries[i]
        supplyfromtank = min(todaydemand, cV)
        cV = cV - supplyfromtank
        cumusupply += supplyfromtank
    return cumusupply/cumudemand * 100

### ------------------------------------------------------------------------ ###     

def linearInterpolate(y0, y1, x0, x1, x):
        """Linear interpolation formula, returns y for x given bounds y, bounds x"""
        y = y0 + (y1-y0)*((x - x0)/(x1 - x0))
        return y

