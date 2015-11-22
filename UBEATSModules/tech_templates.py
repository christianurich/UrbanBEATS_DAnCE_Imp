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
import random as rand
import numpy as np

### EXTERNAL FUNCTIONS THAT CAN MANIPULATE THE CLASSES OF THIS MODULE ###
def CalculateMCATechScores(strategyobject, totalvalues, spref, priorities, techarray, tech, env, ecn, soc, iaoinf):
    """Calculates the individual multicriteria scores for the given strategy object
    and saves it into its attributes, takes the techarray and four other vectors
    containing MCA scores as input.
        - strategyobject = the strategy object containing the information about the technologies
        - totalvalues[0] = total impervious area to work with for Qty
        - totalvalues[1] = total impervious area to work with for WQ
        - totalvalues[2] = total demand to work with
        - spref = scale preference (weightings based on scale)
    """
    techs = strategyobject.getTechnologies()    #grab the array of technologies in the block
    mca_tech = 0.0        #Initialize trackers
    mca_env = 0.0
    mca_ecn = 0.0
    mca_soc = 0.0

    service_abbr = ["Qty", "WQ", "Rec"]       #these are the four main services for the objectives
    for j in range(len(totalvalues)):
        if totalvalues[j] == 0:
            continue    #Skip or else there will be a zero division, it doesn't add to the score anyway
        abbr = service_abbr[j]  #current service abbr to find value from object
        mca_techsub, mca_envsub, mca_ecnsub, mca_socsub = 0.0,0.0,0.0,0.0       #Initialize sub-trackers
        for i in techs: #loop across techs
            if i == 0:  #no score
                continue
            lotcount = float(strategyobject.getQuantity(i.getLandUse()))        #get lot-count based on land use

            systype = i.getType()
            sysscale = i.getScale()
            hybrid = False
            if i.getRecycledStorage() != None:
                recycletype = i.getRecycledStorageType()
                hybrid = not(systype == recycletype)
                # print systype, recycletype

            iao = i.getIAO(abbr)*iaoinf     #iaoinf = influence of IAO  - zero for "Rec"
            if hybrid:
                #Sub-Score = (individual Tech score) x (imp served by tech / imp served by strategy) X number of techs implemented
                if len(tech) != 0: mca_techsub += (sum(tech[techarray.index(systype)]) +
                                                   sum(tech[techarray.index(recycletype)])) / 2.0 * \
                                                  (i.getService(abbr)+iao)/float(totalvalues[j]) * \
                                                  float(lotcount) * float(spref[sysscale]) * 1000
                if len(env) != 0: mca_envsub += (sum(env[techarray.index(systype)]) +
                                                 sum(env[techarray.index(recycletype)])) / 2.0 * \
                                                (i.getService(abbr)+iao)/float(totalvalues[j]) * \
                                                float(lotcount) * float(spref[sysscale]) * 1000
                if len(ecn) != 0: mca_ecnsub += (sum(ecn[techarray.index(systype)]) +
                                                 sum(ecn[techarray.index(recycletype)])) / 2.0 * \
                                                (i.getService(abbr)+iao)/float(totalvalues[j]) * \
                                                float(lotcount) * float(spref[sysscale]) * 1000
                if len(soc) != 0: mca_socsub += (sum(soc[techarray.index(systype)]) +
                                                 sum(soc[techarray.index(recycletype)])) / 2.0 * \
                                                (i.getService(abbr)+iao)/float(totalvalues[j]) * \
                                                float(lotcount) * float(spref[sysscale]) * 1000
            else:
                if len(tech) != 0: mca_techsub += sum(tech[techarray.index(systype)]) * \
                                                  (i.getService(abbr)+iao)/float(totalvalues[j]) * \
                                                  float(lotcount) * float(spref[sysscale]) * 1000
                if len(env) != 0: mca_envsub += sum(env[techarray.index(systype)]) * \
                                                (i.getService(abbr)+iao)/float(totalvalues[j]) * \
                                                float(lotcount) * float(spref[sysscale]) * 1000
                if len(ecn) != 0: mca_ecnsub += sum(ecn[techarray.index(systype)]) * \
                                                (i.getService(abbr)+iao)/float(totalvalues[j]) * \
                                                float(lotcount) * float(spref[sysscale]) * 1000
                if len(soc) != 0: mca_socsub += sum(soc[techarray.index(systype)]) * \
                                                (i.getService(abbr)+iao)/float(totalvalues[j]) * \
                                                float(lotcount) * float(spref[sysscale]) * 1000

        mca_tech += mca_techsub * priorities[j]   #Before next loop, add the sub-scores, scaled by their priorities
        mca_env += mca_envsub * priorities[j]     #to the total criteria scores
        mca_ecn += mca_ecnsub * priorities[j]     #Score = (sub-score) x (priority weighting for current objective)
        mca_soc += mca_socsub * priorities[j]     #If current objective not selected, priority = 0
        
    strategyobject.setMCAscore("tec", mca_tech)
    strategyobject.setMCAscore("env", mca_env)
    strategyobject.setMCAscore("ecn", mca_ecn)
    strategyobject.setMCAscore("soc", mca_soc)
    return True

def CalculateMCAStratScore(strategyobject, weightings):
    """Calculates the final MCA score of the strategy for the given strategy object
    and input weightings for the four criteria [tech, env, ecn, soc]. Saves the final
    score into the object's attributes
    """
    #Normalize the weightings
    weightings = rescaleList(weightings, 'normalize')
    
    #Calculate final score and set it
    mca_total = 0
    mca_total += strategyobject.getMCAscore("tec") * weightings[0]
    mca_total += strategyobject.getMCAscore("env") * weightings[1]
    mca_total += strategyobject.getMCAscore("ecn") * weightings[2]
    mca_total += strategyobject.getMCAscore("soc") * weightings[3]
    strategyobject.setTotalMCAscore(mca_total)
    return True

def rescaleList(list, method):
    """Simple rescaling of a single-dimensional array based on the either the number of entries
    (method='length') or the sum of its values (method='normalize')."""
    if method == 'length':
        for i in range(len(list)):
            list[i] = float(list[i])/float(len(list))
    elif method == 'normalize':
        j = float(sum(list))
        for i in range(len(list)):
            list[i] = list[i]/j
    return list

def createDataBaseString(blockstrategy, Aimp):
    """Prepare's the blockstrategy object's properties into a string that can be inserted
    into the database table corresponding to top-inblock strategies
    """
    dbstring = ""
    dbstring += str(blockstrategy.getLocation())+","+str(blockstrategy.getBlockBin())+","
    #grab all technologies
    techlist = blockstrategy.getTechnologies()
    for i in techlist:
        if i == 0:
            dbstring += "'0',0,0,"
        else:
            dbstring += "'"+str(i.getType())+"',"+str(blockstrategy.getQuantity(i.getLandUse()))+",'"+str(convertArrayToDBString(i.getService("all")))+"',"
          
    dbstring += "'"+str(convertArrayToDBString(blockstrategy.getService("all")))+"',"+str(blockstrategy.getMCAscore("tec"))+","+str(blockstrategy.getMCAscore("env"))+","
    dbstring += str(blockstrategy.getMCAscore("ecn"))+","+str(blockstrategy.getMCAscore("soc"))+","+str(blockstrategy.getTotalMCAscore())+","
    dbstring += str(Aimp)
    return dbstring

def convertArrayToDBString(arrayinput):
    dbstring = ""
    for i in range(len(arrayinput)):
        dbstring += str(arrayinput[i])
        if i != (len(arrayinput)-1):
            dbstring += " | "
    return dbstring

def updateBasinService(basinstrategyobject):
    """Goes through the basin strategy object and tallies up the total impervious area
    serviced. This allows the strategy object to be sorted and scored.
    """
    subbasin = basinstrategyobject.getSubbasinArray()
    inblocks = basinstrategyobject.getInBlocksArray()

    #Loop across four different objectives
    abbr_matrix = ["Qty", "WQ", "Rec"]
    for j in range(len(abbr_matrix)):
        total_service = 0       #initialize tracker
        abbr = abbr_matrix[j]
        for i in subbasin:
            if subbasin[i] == 0:
                continue
            total_service += subbasin[i].getService(abbr) + subbasin[i].getIAO(abbr) #get the service for that particular tech and purpose
        for i in inblocks:
            if inblocks[i] == 0:
                continue
            total_service += inblocks[i].getService(abbr) + inblocks[i].getIAO(abbr)
    
        basinstrategyobject.setService(abbr, total_service)
    
    basinstrategyobject.setServicePvalues()
    return True

def calculateBasinStrategyMCAScores(basinstrategyobject, spref, priorities, techarray, tech, env, ecn, soc, weightings, iaoinf):
    """Scores the provided strategy object by accessing its information and ranking technologies
    using the provided MCA scoring matrix
    """
    techcumu = 0
    envcumu = 0
    ecncumu = 0
    soccumu = 0
    mcatotal = 0
    
    totalvalues = basinstrategyobject.getBasinTotalValues()     #returns [x, x, x] containing totals
    subbasin = basinstrategyobject.getSubbasinArray()
    inblocks = basinstrategyobject.getInBlocksArray()
    
    for i in inblocks:
        if inblocks[i] == 0:
            continue
        techcumu += inblocks[i].getMCAscore("tec")      #Have already been scaled to priorities and based on
        envcumu += inblocks[i].getMCAscore("env")       #services, therefore no need to do again.
        ecncumu += inblocks[i].getMCAscore("ecn")
        soccumu += inblocks[i].getMCAscore("soc")
    
    service_abbr = ["Qty", "WQ", "Rec"]       #these are the four main services for the objectives
    for j in range(len(totalvalues)):   #loop across three service objectives
        abbr = service_abbr[j]          #Current abbreviation used to retrieve service values
        mca_techsub, mca_envsub, mca_ecnsub, mca_socsub = 0.0,0.0,0.0,0.0       #initialize sub-trackers
                       
        for i in subbasin:
            if subbasin[i] == 0.0:
                continue
            systype = subbasin[i].getType()
            sysscale = "B"
            if subbasin[i].getRecycledStorage() != None:
                recycletype = subbasin[i].getRecycledStorageType()
                hybrid = not(systype == recycletype)
            else:
                hybrid = False

            iao = subbasin[i].getIAO(abbr)*iaoinf     #iaoinf = influence of IAO - zero for Rec or non-harvest
            if hybrid:


                if len(tech) != 0: mca_techsub += (sum(tech[techarray.index(systype)]) +
                                                   sum(tech[techarray.index(recycletype)])) / 2.0 * \
                                                  (subbasin[i].getService(abbr)+iao)/float(totalvalues[j]) * float(spref[sysscale]) * 1000
                if len(env) != 0: mca_envsub += (sum(env[techarray.index(systype)]) +
                                                 sum(env[techarray.index(recycletype)])) / 2.0 * \
                                                (subbasin[i].getService(abbr)+iao)/float(totalvalues[j]) * float(spref[sysscale]) * 1000
                if len(ecn) != 0: mca_ecnsub += (sum(ecn[techarray.index(systype)]) +
                                                 sum(ecn[techarray.index(recycletype)])) / 2.0 * \
                                                (subbasin[i].getService(abbr)+iao)/float(totalvalues[j]) * float(spref[sysscale]) * 1000
                if len(soc) != 0: mca_socsub += (sum(soc[techarray.index(systype)]) +
                                                 sum(soc[techarray.index(recycletype)])) / 2.0 * \
                                                (subbasin[i].getService(abbr)+iao)/float(totalvalues[j]) * float(spref[sysscale]) * 1000
            else:
                if len(tech) != 0: mca_techsub += sum(tech[techarray.index(systype)]) * \
                                                  (subbasin[i].getService(abbr)+iao)/float(totalvalues[j]) * float(spref[sysscale]) * 1000
                if len(env) != 0: mca_envsub += sum(env[techarray.index(systype)]) * \
                                                (subbasin[i].getService(abbr)+iao)/float(totalvalues[j]) * float(spref[sysscale]) * 1000
                if len(ecn) != 0: mca_ecnsub += sum(ecn[techarray.index(systype)]) * \
                                                (subbasin[i].getService(abbr)+iao)/float(totalvalues[j]) * float(spref[sysscale]) * 1000
                if len(soc) != 0: mca_socsub += sum(soc[techarray.index(systype)]) * \
                                                (subbasin[i].getService(abbr)+iao)/float(totalvalues[j]) * float(spref[sysscale]) * 1000

        techcumu += mca_techsub * float(priorities[j])  #add to the cumulative MCA scores, scaled by their relative priorities
        envcumu += mca_envsub * float(priorities[j])
        ecncumu += mca_ecnsub * float(priorities[j])
        soccumu += mca_socsub * float(priorities[j])

    #Normalize the weightings
    weightings = rescaleList(weightings, 'normalize')

    mca_total = techcumu * weightings[0] + envcumu * weightings[1] + ecncumu * weightings[2] + soccumu * weightings[3]
    basinstrategyobject.setMCAscore("tec", techcumu)
    basinstrategyobject.setMCAscore("env", envcumu)
    basinstrategyobject.setMCAscore("ecn", ecncumu)
    basinstrategyobject.setMCAscore("soc", soccumu)
    basinstrategyobject.setTotalMCAscore(mca_total)
    return True

def writeReportFile(basinstrategyobject, filename):
    """Writes an output CSV file of the basin strategy object passed to the function
    and saves it to the file with the given <filename>.csv. The file can be opened in
    Excel for convenient viewing"""
    
    return True

def reportStrategy(strategyobject):
    """Prints details of the strategy into the console window for quick viewing, use
    this function for debugging"""
    
    return True

### CLASSES IN THIS MODULE ###
class RecycledStorage(object):
    def __init__(self, type, volume, enduses, Aharvest, rel, supply, scale):
        """An object to hold data on recycled storage"""
        
        self.__type = type
        self.__volume = volume          #[kL]
        self.__Aharvest = Aharvest      #[sqm]
        self.__rel = rel                #[%]
        self.__supply = supply          #Total demand supplied [kL/yr]
        self.__enduses = enduses        #Contains 'K, L, T, S, I, PI'
        self.__scale = scale            #L=lot N=Neighbourhood B=subbasin

    def getSize(self):
        return self.__volume
    
    def getSupply(self):
        return self.__supply
    
    def getReliability(self):
        return self.__rel
    
    def getAreaOfHarvest(self):
        return self.__Aharvest
    
class WaterTech(object):
    def __init__(self, type, size, scale, service, areafactor, landuse, blockID):
        """Technology type = initials of the tech e.g. BF = biofilter
                type = system type  in terms of abbreviation
                size = surface area/volume/specification number depending on system type
                scale = a letter signifiying scale of application, L-lot, S-street, N-neighbourhood, R-regional (sub-basin)
                service = imp area, population, public open space servied by the system. An array of length 4.
                areafactor = a factor for multiplying the system footprint to get planning-allocated area
                landuse = the type of land use the system was designed for
                blockID = the location of the system (i.e. block ID)
            For individual water techs, the design increment represents the service level they can provide.
            The serviced imp.area/pop/public space divided by its total value is either equal to this increment
            or zero because the service cannot be met at all. i.e. [1, 1, 1, 1] or [1, 1, 0, 1]. This is binary.
        """
        self.__type = type
        self.__size = size              #Area of system or volume if tank
        self.__scale = scale
        self.__service = {}
        self.__service["Qty"] = float(service[0])       #impervious area treated for runoff reduction
        self.__service["WQ"] = float(service[1])        #impervious area treated for pollution control
        self.__service["Rec"] = float(service[2])     #total population serviced by recycling
        self.__areafactor = areafactor
        self.__landuse = landuse
        self.__designincrement = 1.0    #If design increment = 1.0, then service matrix will be either all imp area or zero
        self.__blockID = blockID
        self.__rec_store = None
        self.__rec_store_type = ""
        self.__rec_integrated = 0
        self.__rec_store_surfaceArea = 0.0
        self.__rec_store_areafactor = 0.0
        self.__quantityIAO = 0.0    #Impervious Area offset for stormwater quantity water management
        self.__qualityIAO = 0.0     #Impervious Area offset for stormwater quality water management
        
        #Assign some descriptive variables to the object
        if self.__type in ['BF', 'IS']:
            self.hasFilter = True
        else:
            self.hasFilter = False
        if self.__type in ['WSUR', 'PB', 'RT', 'GW']:
            self.hasStorage = True
        else:
            self.hasStorage = False
        if self.__type in ['RT', 'GW', 'PPL']:
            self.isGreyTech = True
            self.isGreenTech = False
        else:
            self.isGreyTech = False
            self.isGreenTech = True

    def addRecycledStoreToTech(self, storeObj, recsurfarea, type, integrated):
        self.__rec_store = storeObj
        self.__service["Rec"] = storeObj.getSupply()
        self.__rec_integrated = integrated
        self.__rec_store_type = type
        self.__rec_store_surfaceArea = recsurfarea[0]
        self.__rec_store_areafactor = recsurfarea[1]
        return True

    def getRecycledStorage(self):
        return self.__rec_store

    def getRecycledStorageType(self):
        return self.__rec_store_type

    def getStoreSurfArea(self):
        if bool(self.__rec_Integrated):
            return 0
        else:
            return self.__rec_store_surfaceArea
    
    def setDesignIncrement(self, increment):
        self.__designincrement = increment
        return True
    
    def getDesignIncrement(self):
        return self.__designincrement
    
    def getType(self):
        return self.__type
    
    def getAreaFactor(self):
        return self.__areafactor
    
    def getSize(self):
        return self.__size
    
    def getScale(self):
        return self.__scale
    
    def getService(self, category):
        if category == "all":
            return [self.__service["Qty"], self.__service["WQ"], self.__service["Rec"]]
        else:
            return self.__service[category]
        
    def getLandUse(self):
        return self.__landuse
    
    def getLocation(self):
        return self.__blockID

    def setIAO(self, purpose, value):
        if purpose == "Qty":
            self.__quantityIAO = value
        elif purpose == "WQ":
            self.__qualityIAO = value
        else:
            pass
        return True

    def getIAO(self, purpose):
        if purpose == "Qty":
            return self.__quantityIAO
        elif purpose == "WQ":
            return self.__qualityIAO
        elif purpose == "Rec":
            return 0
        else:
            return [self.__quantityIAO, self.__qualityIAO]

    
class BlockStrategy(object):
    """Object, which contains all the WSUD technologies at the lot, street and neighbourhood
    scales to make up the 'In-Block' Strategy. It applies to one block only and contains a
    maximum of 7 possible technologies (5lot, 1street, 1neighbourhood).
    
    The combo is passed to the object as a vector, totalserviceabsolute specifies the total
    service provided by the entire object, allotments tells us the number of allotments in
    residential housing serviced, currentID pinpoints the location and the bin gives us an
    indication of what bin-group this strategy should be in (when evaluating top 10 in-block
    systems).
    """
    def __init__(self, combo, totalserviceabsolute, allotments, currentID, bin):
        self.__lotRES_tech = combo[0]
        self.__lotHDR_tech = combo[1]
        self.__lotLI_tech = combo[2]
        self.__lotHI_tech = combo[3]
        self.__lotCOM_tech = combo[4]
        self.__street_tech = combo[5]
        self.__neigh_tech = combo[6]
        self.__blockservice = {} #e.g. total imp served, total pop served
        self.__blockservice["Qty"] = totalserviceabsolute[0]            #Impervious area [sqm]
        self.__blockservice["WQ"] = totalserviceabsolute[1]             #Impervious area [sqm]
        self.__blockservice["Rec"] = totalserviceabsolute[2]          #Demand substituted [kL]
        self.__blockbin = bin   #Maximum of the blockservice matrix e.g. [0.5, 0.5, 0.5, 0.5] --> 0.5 service
                                                                        #[0.76, 0.2, 0.1, 0] --> 0.76 service
        self.__location = currentID
        
        self.__allotments = allotments  #a list of lotcounts [RES Lots, HDR Lots, LI estates, HI estates, COM estates]
        self.lucmatrix = ["RES", "HDR", "LI", "HI", "COM", "Street", "Neigh"]
        self.__MCA_scores = [0.0,0.0,0.0,0.0]
        self.__MCA_totscore = 0.0
        self.criteriamatrix = ["tec", "env", "ecn", "soc"]
        self.__quantityIAO = 0.0
        self.__qualityIAO = 0.0
    
    def getBlockBin(self):
        return self.__blockbin
    
    def getQuantity(self, luc):
        if luc == "all":
            return self.__allotments
        elif luc not in self.lucmatrix:
            return 1
        else:
            return self.__allotments[self.lucmatrix.index(luc)]
    
    def setMCAscore(self, criteria, score):
        self.__MCA_scores[self.criteriamatrix.index(criteria)] = score
    
    def getMCAscore(self, criteria):
        return self.__MCA_scores[self.criteriamatrix.index(criteria)]
    
    def setTotalMCAscore(self, score):
        self.__MCA_totscore = float(score)
    
    def getTotalMCAscore(self):
        return self.__MCA_totscore
    
    def getTechnologies(self):
        return [self.__lotRES_tech, self.__lotHDR_tech, self.__lotLI_tech, self.__lotHI_tech, self.__lotCOM_tech, self.__street_tech, self.__neigh_tech]
        
    def getService(self, category):
        if category == "all":
            return [self.__blockservice["Qty"], self.__blockservice["WQ"], self.__blockservice["Rec"]]
        else:
            return self.__blockservice[category]
    
    def getLocation(self):
        return self.__location
    
    def getTotalBasinContribution(self, category, totalvalue):
        """Returns the total contribution of a particular service within the basin
        e.g. water quantity managment across the total impervious area or recycling
        across the whole population."""
        return self.__service[category]/totalvalue

    def setIAO(self, purpose, value):
        if purpose == "Qty":
            self.__quantityIAO = value
        elif purpose == "WQ":
            self.__qualityIAO = value
        return True

    def getIAO(self, purpose):
        if purpose == "Qty":
            return self.__quantityIAO
        elif purpose == "WQ":
            return self.__qualityIAO
        elif purpose == "Rec":
            return 0
        else:
            return [self.__quantityIAO, self.__qualityIAO]
    
class BasinManagementStrategy(object):
    """Class for the complete water management strategy within a basin of the case study.
    Contains all the information about the basin as well as location of different technologies
    in place within this basin, their service levels and scoring.
    """
    def __init__(self, strategyID, basinID, basinblockIDs, partakeIDs, basin_info):
        #basin_info = [cumulative_Aimp, cumulative_population, cumulative_public_area]
        
        self.__basinID = basinID                #IDs for strategy basin and blocks
        self.__strategyID = strategyID
        self.__blocks = len(basinblockIDs)
        self.__basinblockIDs = (basinblockIDs)
        self.__subbas_partake_IDs = partakeIDs

        self.__redundancyQty = 0.0     #The amount of redundancy in the strategy
        self.__redundancyWQ = 0.0
        self.__redundancyRec = 0.0

        self.__basinAimpQty = basin_info[0]    #Impervious Area to be managed for QTY
        self.__basinAimpWQ = basin_info[1]     #Impervious area to be managed for WQ
        self.__basinDemRec = basin_info[2]         #Basin demand to be managed
        
        #Service Metrics
        self.__basin_services = {"Qty":0.0, "WQ":0.0, "Rec":0.0}
                                        #Qty: effective impervious area served
                                        #WQ: effective impervious area served
                                        #Rec: total potable supply substituted
        self.__basin_serviceP = [0.0,0.0,0.0]
        
        self.criteriamatrix = ["tec", "env", "ecn", "soc"]
        self.__MCA_scores = [0.0,0.0,0.0,0.0]
        self.__MCA_totscore = 0.0
        
        #Create Arrays to hold the strategy information
        self.__basindetails = {}        #Holds the information on all upstream IDs
        self.__subbasinarray = {}
        for i in partakeIDs:
            self.__subbasinarray[i] = 0.0
            self.__basindetails[i] = 0.0
        
        self.__degreesarray = {}    
        self.__inblockarray = {}
        for i in basinblockIDs:
            self.__inblockarray[i] = 0.0
            self.__degreesarray[i] = [0.0,0.0]

        self.__quantityIAO = 0.0
        self.__qualityIAO = 0.0
    
    def getBasinEIA(self):
        return self.__basinAimp
    
    def getBasinTotalValues(self):
        """Used in the MCA function to get the scores and totals to loop across for different
        objectives"""
        if self.__basinAimpQty == 0:
            returnimpQty = np.inf  #Adjusts to avoid division by zero
        else:
            returnimpQty = self.__basinAimpQty
        
        if self.__basinAimpWQ == 0:
            returnimpWQ = np.inf
        else:
            returnimpWQ = self.__basinAimpWQ
        
        if self.__basinDemRec == 0:
            returndemRec = np.inf
        else:
            returndemRec = self.__basinDemRec
        
        return [returnimpQty, returnimpWQ, returndemRec]
    
    def setService(self, category, value):
        self.__basin_services[category] = value
        return True
    
    def getService(self, category):
        return self.__basin_services[category]
    
    def setServicePvalues(self):
        totalvalues = self.getBasinTotalValues()
        self.__basin_serviceP[0] = self.getService("Qty")/totalvalues[0]
        self.__basin_serviceP[1] = self.getService("WQ")/totalvalues[1]
        self.__basin_serviceP[2] = self.getService("Rec")/totalvalues[2]
        return True
    
    def getServicePvalues(self):
        return self.__basin_serviceP
    
    def getBasinBlockIDs(self):
        return self.__basinblockIDs
    
    def getSubbasPartakeIDs(self):
        return self.__subbas_partake_IDs
    
    def setMCAscore(self, criteria, score):
        self.__MCA_scores[self.criteriamatrix.index(criteria)] = score
    
    def getMCAscore(self, criteria):
        return self.__MCA_scores[self.criteriamatrix.index(criteria)]
    
    def setTotalMCAscore(self, score):
        self.__MCA_totscore = score
    
    def getTotalMCAscore(self):
        return self.__MCA_totscore
    
    def getSubbasinArray(self):
        return self.__subbasinarray
    
    def getInBlocksArray(self):
        return self.__inblockarray
    
    def addSubBasinInfo(self, currentID, upstreamIDs, subbasinIDs, totals_subbas):
        """Adds information about the basin and sub-basin to the strategy to allow quick retrieval
        of catchment details for computation.
            totalvalues_subbas = [imp-area, population, public-space]
        """
        try:
            self.__basindetails[currentID] = [currentID, upstreamIDs, subbasinIDs, totals_subbas]
        except KeyError:
            return True
        
    def appendTechnology(self, currentID, deg, chosen_object, scaletype):
        """Appends a given technology object to either the in-block list of systems or 
        the subbasin list of systems at the location currentID. Additionally saves the
        degree of service implementation as well.
            - deg used later for sampling from the appropriate bin
            - scaletype = "s" for subbasin, "b" for in-block
        """
        try:
            if scaletype == "s":
                self.__subbasinarray[currentID] = chosen_object
                self.__degreesarray[currentID][1] = deg
            elif scaletype == "b":
                self.__inblockarray[currentID] = chosen_object
                self.__degreesarray[currentID][0] = deg
            return True
        except KeyError:
            return True
        
    def getIndividualTechStrat(self, currentID, scaletype):
        """Retrieves the object for a particular in-block or subbasin strategy/system
        that is located in the block with the ID currentID. If none exists in that location,
        model returns None.
            - scaletype = "s" for subbasin, "b" for in-block
        """
        try:
            if scaletype == "s":
                strat = self.__subbasinarray[currentID]
            elif scaletype == "b":
                strat = self.__inblockarray[currentID]
            if strat == 0:
                return None
            else:
                return strat
        except KeyError:
            return None
    
 
#    def reportBasinStrategy(self):
#        print "-----------------------------------------"
#        print "Basin ID", self.__basinID
#        print "-----------------------------------------"
#        print "Total Blocks in basin: ", self.__blocks
#        print "Total Impervious Area: ", self.__basinAimp/10000, " ha"
#        print "Block IDs"
#        print self.__basinblockIDs
#        print "Blocks that can fit a precinct-scale system:"
#        print self.__precpartakeIDs 
#        print ""
#        print "Chosen Objects for precinct"
#        print self.__precarray
#        print "Chosen Objects for in-block"
#        print self.__blockarray
#        return True
    
#    def writeReportFile(self):
#        f = open("UB_BasinStrategy No "+str(self.__basinID)+"-"+str(self.__strategyID)+".csv", 'w')
#        f.write("UrbanBEATS Basin Strategy File for Strategy No. "+str(self.__strategyID)+"\n\n")
#        f.write("Basin ID:,"+str(self.__basinID)+"\n")
#        f.write("Total Service:,"+str(self.getPropImpServed())+"%\n")
#        f.write("Blocks within basin:,"+str(len(self.__basinblockIDs))+"\n")
#        f.write("Blocks containing precinct-scale opportunities:,"+str(len(self.__precpartakeIDs))+"\n\n")
#        f.write("Tech Score, Env Score, Ecn Score, Soc Score, Total Score\n")
#        scorestring = ""
#        for i in self.getMCAsubscores():
#            scorestring += str(i)+","
#        scorestring += str(self.getMCAtotscore())+","
#        f.write(scorestring+"\n\n")
        
#        f.write("Block ID, Lot System, Size, Service, Houses [%], Allotments, Street System, Size, Service, Neigh System, Size, Service, Prec System, Size, Service,\n")
        
#        for i in range(len(self.__basinblockIDs)):
#            #get strategy list
#            outputstring1 = ""
#            if len(self.__blockarray[i]) == 0:
#                outputstring1 = "0,0,0,0,0,0,0,0,0,0,0,"
#            else:
#                stratlist = self.__blockarray[i][0].getSystemList()
#                for j in range(len(stratlist)):
#                    if stratlist[j] == 0:
#                        outputstring1 += "0,0,0,"
#                    else:
#                        outputstring1 += str(stratlist[j].getType())+","+str(stratlist[j].getSize())+","+str(stratlist[j].getBasinContribution(self.__basinAimp))+","
#                    if j == 0 and stratlist[j] != 0:
#                        outputstring1 += str(self.__blockarray[i][0].getLotImplementation())+","+str(self.__blockarray[i][0].getAllotments())+","
#                    elif j == 0 and stratlist[j] == 0:
#                        outputstring1 += "0,0,"
            
#            #get precinct-scale stuff
#            outputstring2 = ""
#            if self.__basinblockIDs[i] in self.__precpartakeIDs:                   #if the ID is also a precinct ID check if there's a tech
#                ix = self.__precpartakeIDs.index(self.__basinblockIDs[i])          #get index to reference
#                if len(self.__precarray[ix]) == 0:                                   #check if there's a tech object or not
#                    outputstring2 = "0,0,0,"
#                else:
#                    outputstring2 = str(self.__precarray[ix][0].getType())+","+str(self.__precarray[ix][0].getSize())+","+str(self.__precarray[ix][0].getBasinContribution(self.__basinAimp))+","
#            else:
#                outputstring2 = "0,0,0,"
#            #combine option strings
#            f.write(str(self.__basinblockIDs[i])+","+outputstring1+outputstring2+"\n")
#        f.close()
#        return True
    