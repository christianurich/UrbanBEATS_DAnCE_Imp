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
###     SUBFUNCTIONS FOR STORAGE-BEHAVIOUR EQUATION                          ###
### ------------------------------------------------------------------------ ###

def calcDVavg(supplyvol, demandvol):
    """Calculates the dvAVG parameter to be used in the Storage Equation model"""
    dvavg = (supplyvol - demandvol)/(0.5 * (supplyvol + demandvol))
    return dvavg

def calcRMSE(inflow, demand):
    """Calculates the RMSE parameter to be used in the Storage Equation mode. A
    simple function to evaluate a statistical objective function"""
    ssd = 0
    for i in range(len(inflow)):
        ssd += pow((inflow[i]-demand[i]),2)
    rmse = np.sqrt(ssd/len(inflow))
    return rmse
    
def getModelCoefficients(city):
    """Retrieve the model coefficients for the given city in question. The order
    of coefficients is: [targetrel, dvavg, RMSE, constant]"""
    coefficients = {"Adelaide": [7.825441, -4.568164, 1.35581, -13.74432],
                    "Brisbane": [5.649993, -4.321506, 1.670372, -10.28553],
                    "Melbourne": [8.45052, -4.945666, 1.374313, -15.19023],
                    "Perth": [4.833975, -3.159505, 1.613991, -8.300912],
                    "Sydney": [5.30221, -3.771708, 1.412654, -9.512594],
                    "Global": [5.334406, -3.608082, 0.458087, -8.887966]
                    }
    if city not in ["Adelaide", "Brisbane", "Melbourne", "Perth", "Sydney"]:
        return coefficients["Global"]
    else:
        return coefficients[city]

def loglogSWHEquation(city, targetrel, supplyvol, demandvol):
    """Sizes a storage [% of average annual inflow] using the 'Universal SWH Equation'.
    Returns the size of the storage"""
    if targetrel > 95:
        targetrel = 95  #Warning, model not cut out to predict for reliabilities beyond 95%
    #print "Total Supply: ", sum(supplyvol), " TotalDemand: ", sum(demandvol)
    dvavg = calcDVavg(sum(supplyvol), sum(demandvol))
    rmse = calcRMSE(supplyvol, demandvol)
    #print dvavg
    coefficients = getModelCoefficients(city)
    
    #Apply the model
    #   Vol = Rel ^ u * (dvAvg+1) ^ v * RMSE ^ w * 10 ^ const
    storagevol = (targetrel**coefficients[0])*((dvavg+1)**coefficients[1])*(rmse**coefficients[2])*(10**coefficients[3])
    return storagevol

### ------------------------------------------------------------------------ ###    

