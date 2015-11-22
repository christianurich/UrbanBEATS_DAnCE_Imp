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

def loadClimateFile(filename, filetype, dt_in, dt_out, numyears):
    """Retrieves climate file based on the input filename and format specified. Format
    can take different styles, e.g. .ixx, .csv, etc.
        - filename: the full path to the file, so that the program can find it
        - format: the filetype extension that also defines how the raindata is delimited
        - dt_in: input timestep of the file [mins]
        - dt_out: desired output timestep of the file [mins]
        - numyears: extracts data from startyear + numyears and returns it

    Current support rainfile formats are: .csv, .ixx, .mse
    """
    #New timestep, determine how many lines of old time-step data need to be summed
    if dt_out % dt_in == 0:
        datalines = int(dt_out / dt_in)
    else:
        print "Error: cannot convert climate file timestep from dt-in to dt-out"
        datalines = 1
    
    #Grab the data from the file based on the format, returns [Year, Month, Data]
    if filetype == "csv":
        #Input Data format: "DD/MM/YYYY HH:MM, rain[mm]\n", skip first line of file
        data = readFileCSV(filename, datalines)
    elif filetype == "ixx":
        #Input Data format: "DD.MM.YYYY.hh.mm.ss rain[mm/dt]\n", skip first line of file
        data = readFileIXX(filename, datalines)
    elif filetype == "mse":
        #Input Data format: "YY MM DD hh mm ss rain[10E-3mm/dt]\n", skip first line of file
        data = readFileMSE(filename, datalines)
    
    #Narrow down the data to only what the user wants
    datacut = extractDataSubSet(data, numyears)
    return datacut

def readFileCSV(filename, rescalelines):
    """Read a .csv format data file containing climate data at a given time step.
    Function also calls rescaling function to rescale the data to the desired d_out
    timestep"""
    f = open(filename, 'r')         #Open the file containin raindata
    datavec = []                      #initialize the vector that contains the data [[Date][rain]]
    f.readline()                        #skip the first line of the file
    for lines in f:
        datavec.append(lines)         #Add the subsequent lines to the rain file
    f.close()
    for i in range(len(datavec)):
        datavec[i] = datavec[i].split(",")    #split the line based on the s
        datavec[i][0] = datavec[i][0].split(" ")
        datavec[i][1] = datavec[i][1].rstrip("\n")
        if datavec[i][1] in ['', "0", ""]:
            datavec[i][1] = "0"
        datavec[i][1] = float(datavec[i][1])
    #Transfer rain data into rain[] matrix, pay attention to month and year
    for i in range(len(datavec)):
        year, month = convertToYearMonth(datavec[i][0][0], "/", 2)
        datavec[i] = [year, month, datavec[i][1]]
    data = rescaleData(datavec, rescalelines)
    return data

def rescaleData(datavec, rescalelines):
    """Rescale data to current dt_out timestep (using rescalelines). Sum up in groups of
    #x lines where x = rescalelines"""
    timecounter = 0
    datasum = 0
    data = []
    for i in range(len(datavec)):
        curyear = datavec[i][0]
        curmonth = datavec[i][1]
        timecounter += 1
        datasum += datavec[i][2]
        if timecounter == rescalelines:
            data.append([curyear, curmonth, datasum])
            timecounter = 0
            datasum = 0
    if timecounter != 0:
        data.append([curyear, curmonth, datasum])
    datavec = []        #Clear memory
    #Now we have rescaled data in the matrix data[] stored in the form of [year, month, data]
    return data

def convertToYearMonth(datestring, delimiter, yearpos):
    """Input date string 'DD/MM/YYYY' is converted into two output integers: year and month"""
    date = datestring.split(delimiter)
    year = int(date[yearpos])
    if yearpos == 0:
        month = int(date[yearpos + 1])
    else:
        month = int(date[yearpos - 1])
    return year, month

def getYearCount(inputvec):
    """Scans the data vector for unique years to return the total number of years in 
        the time-series """
    yearitems = []
    for i in range(len(inputvec)):
        if inputvec[i][0] not in yearitems:
            yearitems.append(inputvec[i][0])
    return len(yearitems)

def extractDataSubSet(data, numyears):
    """Scans the data file and returns a time series of length 'numyears' = number of
    years the user wants of the data, if numyears = 0, returns one year only"""
    years = getYearCount(data)
    if numyears < 1:
        numyears = 1    #cannot be less than 1
    if numyears >= years:        #if time series shorter than what user wants, returns time-series
        return data
    startyear = data[0][0]       #get the start year
    endyear = startyear + numyears   #the year to stop tracking
    currentyear = startyear     #initialize current year variable
    datacut = []
    rowcounter = 0
    while currentyear != endyear:        
        datacut.append(data[rowcounter])        #append the data
        rowcounter += 1                         #increment row counter by one        
        currentyear = data[rowcounter][0]     #stops once the last line of the end year has been written
    return datacut

def convertVectorToScalingFactors(inputvec):
    """Converts an input series to a set of scaling factors based on the annual data.
    Used for evaporation factors for example."""
    annualdata = convertDataToAnnual(inputvec)
    yeartrack = inputvec[0][0]
    anndataindex = 0
    scalefactors = []
    for i in range(len(inputvec)):
        curyear = inputvec[i][0]
        if curyear == yeartrack:
            scalefactors.append([inputvec[i][0], inputvec[i][1], inputvec[i][2]/annualdata[anndataindex][1]])
        else:
            yeartrack = curyear
            anndataindex += 1
            scalefactors.append([inputvec[i][0], inputvec[i][1], inputvec[i][2]/annualdata[anndataindex][1]])
    #scalefactors.append([inputvec[i][0], inputvec[i][1], inputvec[i][2]/annualdata[anndataindex][1]])
    return scalefactors

def convertDataToMonthly(data):
    """Converts an input data set to monthly time step"""
    mdata = []
    datasum = 0
    curmonth = data[0][1]
    for i in range(len(data)):
        if data[i][1] == curmonth:
            datasum += data[i][2]
        else:
            mdata.append([data[i-1][0], curmonth, datasum])
            datasum = data[i][2]
            curmonth = data[i][1]
    mdata.append([data[i-1][0], curmonth, datasum])
    return mdata
    
def convertDataToAnnual(data):
    """Converts an input data set to annual time step"""
    anndata = []
    yeartrack = data[0][0]      #initialize to start year
    datasum = 0
    for i in range(len(data)):
        curyear = data[i][0]
        if curyear == yeartrack:
            datasum += data[i][2]
        elif curyear != yeartrack:
            anndata.append([yeartrack, datasum])
            datasum = data[i][2] #reinitialize datasum, but set to value of current year
            yeartrack = curyear
    anndata.append([yeartrack, datasum])
    return anndata

def convertDataToInflowSeries(data, catchment, includedatestamp):
    """Converts an input rain-data series to an inflow time series [kL/dt] based on
    a specified catchment area
        - data: the data vector [year, month, data[mm]] 
        - catchment: catchment area [sqm]
        - includedatestamp: if false, just returns a single-dimensional vector
        """
    inflowseries = []
    #Check for DateStamp
    if type(data[0]) != type([]):       #NO has no date stamp
        for i in range(len(data)):
            inflowseries.append(data[i]/1000*catchment)
    else:       #Has a date stamp
        for i in range(len(data)):
            if includedatestamp:
                inflowseries.append([data[i][0], data[i][1], data[i][2]/1000 * catchment])
            else:
                inflowseries.append(data[i][2]/1000 * catchment)
    return inflowseries

def createScaledDataSeries(annualvalue, scalingfactors, includedatestamp):
    """Converts single annual water usage value [kL] to a time series based on
    the scalingfactors array.
        - annualvalue: total annual water demand [kL]
        - scalingfactors: time series of scaling factors obtained from 
                        convertVectorToScalingFactors()
        - includedatestamp: if false, just returns a single-dimensional vector"""
    dataseries = []
    for i in range(len(scalingfactors)):
        if includedatestamp:
            dataseries.append([scalingfactors[i][0], scalingfactors[i][1], scalingfactors[i][2]*annualvalue])
        else:
            dataseries.append(scalingfactors[i][2]*annualvalue)
    return dataseries

def createConstantDataSeries(dailyvalue, timesteps):
    """Converts a daily water usage value [kL/day] into a time series of length "timesteps"
    and returns this as a vector that does not include a datestamp
        - Dailyvalue: of water demand [kL/day]
        - timesteps: total length of time period [days]
    """
    dataseries = []
    for i in range(timesteps):
        dataseries.append(dailyvalue)
    return dataseries

def mergeTimeSeries(timeseries1, timeseries2, includedatestamp):
    """Merges two time series of the same time step into a single continuous time series.
    If time steps differ, it will return the longer one
        - timeseries1, 2: respective time series matrices either in the form [value] or [date, value]
        - datestamp: removes the datestamp if False"""
    merger = []
    #Check the length of both time series to make sure they can be merged
    length1 = len(timeseries1)
    length2 = len(timeseries2)
    if length1 != length2:      #return the longer one
        print "Error, time series are not of same length"
        if length1 > length2:
            return timeseries1
        else:
            return timeseries2
        
    #Check format of time series (i.e. whether simply [data] or [[date, data]] format
    if type(timeseries1[0]) == type([]):    #if of type list    
        format1 = len(timeseries1[0])
    else:
        format1 = 1
    if type(timeseries2[0]) == type([]):
        format2 = len(timeseries2[0])       #can be done by checking the first row
    else:
        format2 = 1
    #Possibilities: 1 - [data], 2 - [year, data], 3 - [year, month, data]
    if format1 > 1 or format2 > 1:      #then there is date data
        if format1 == format2:
            controltseries = timeseries1        #If they are the same length, assume they have same data structure
        elif format1 > format2:
            controltseries = timeseries1
        else:
            controltseries = timeseries2
    else:
        includedatestamp = False
        
    for i in range(length1):
        timestepsum = 0
        if format1 > 1: 
            timestepsum += timeseries1[i][len(timeseries1[i])-1]
        else: 
            timestepsum += timeseries1[i]
        if format2 > 1: 
            timestepsum += timeseries2[i][len(timeseries2[i])-1]
        else: 
            timestepsum += timeseries2[i]
                
        if includedatestamp:
            merger.append(controltseries[i][0:(len(controltseries[0])-1)])
            merger[i].append(timestepsum)
        else:
            merger.append(timestepsum)
    return merger

def removeDateStampFromSeries(data):
    """Removes the datestamp from the dataseries 'data' and returns a single-dimensional
    vector containing only data values."""
    dataseries = []
    for i in range(len(data)):
        dataseries.append(data[i][2])
    return dataseries