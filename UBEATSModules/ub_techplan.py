# -*- coding: utf-8 -*- 
"""
@file
@author  Peter M Bach <peterbach@gmail.com>
@version 1.0
@section LICENSE

This file is part of UrbanBEATS - Dynamind Implementation
Copyright (C) 2015  Peter M Bach

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, READ to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
"""
from pydynamind import *

#URBANBEATS IMPORTS
import tech_templates as tt
import tech_design as td
import tech_designbydcv as dcv          #sub-functions that design based on design curves
import tech_designbyeq as deq           #sub-functions that design based on design equations
import tech_designbysim as dsim         #sub-functions that design based on miniature simulations
import ubseriesread as ubseries         #sub-functions responsible for processing climate data

#OTHER IMPORTS
import os, gc, random
import numpy as np


#Path to the ancillary folder external files that UrbanBEATS uses to undertake the WSUD assessment
#Includes: Design curves, rainfall data, stormwater harvesting benefits empirical relationships
ANCILLARY_PATH = "D:/Coding Projects/UrbanBEATS_DAnCE_Imp/ancillary"   #Change this path to suit


class UB_Techplan(Module):

      def __init__(self):
            Module.__init__(self)

            #To use the GDAL API
            self.setIsGDALModule(True)
            #Parameter Definition

            ##########################################################################
            #---DESIGN CRITERIA INPUTS                                               
            ##########################################################################

            #DESIGN RATIONALE SETTINGS
            self.createParameter("ration_runoff", BOOL,"")
            self.createParameter("ration_pollute", BOOL,"")
            self.createParameter("ration_harvest",BOOL,"")
            self.createParameter("runoff_pri", DOUBLE,"")
            self.createParameter("pollute_pri", DOUBLE,"")
            self.createParameter("harvest_pri",DOUBLE,"")
            self.ration_runoff = 0                     #Design for runoff volume reduction
            self.ration_pollute = 1                    #Design for pollution management
            self.ration_harvest = 0                    #Design for harvesting & reuse? Adds storage-sizing to certain systems
            self.runoff_pri = 0.0                      #Priority of flood mitigation?
            self.pollute_pri = 1.0                     #Priority of pollution management?
            self.harvest_pri = 0.0                     #Priority for harvesting & reuse

            self.priorities = []            #ADVANCED PARAMETER, holds the final weights for MCA

            #WATER MANAGEMENT TARGETS
            self.createParameter("targets_runoff", DOUBLE,"")
            self.createParameter("targets_TSS", DOUBLE,"")
            self.createParameter("targets_TP", DOUBLE,"")
            self.createParameter("targets_TN", DOUBLE,"")
            self.createParameter("targets_reliability", DOUBLE, "")
            self.targets_runoff = 30.0            #Runoff reduction target [%]
            self.targets_TSS = 80.0               #TSS Load reduction target [%]
            self.targets_TP = 45.0                #TP Load reduction target [%]
            self.targets_TN = 45.0                #TN Load reduction target [%]
            self.targets_reliability = 80.0       #required reliability of harvesting systems

            self.system_tarQ = 0            #INITIALIZE THESE VARIABLES
            self.system_tarTSS = 0
            self.system_tarTP = 0
            self.system_tarTN = 0
            self.system_tarREL = 0
            self.targetsvector = []         #---CALCULATED IN THE FIRST SECTION OF RUN()

            #WATER MANAGEMENT SERVICE LEVELS
            self.createParameter("service_swmQty", DOUBLE, "")
            self.createParameter("service_swmWQ", DOUBLE, "")
            self.createParameter("service_rec", DOUBLE, "")
            self.createParameter("service_res", BOOL, "")
            self.createParameter("service_hdr", BOOL, "")
            self.createParameter("service_com", BOOL, "")
            self.createParameter("service_li", BOOL, "")
            self.createParameter("service_hi", BOOL, "")
            self.createParameter("service_redundancy", DOUBLE, "")
            self.service_swmQty = 50.0                #required service level for stormwater management
            self.service_swmWQ = 80.0                 #required service level for stormwater management
            self.service_rec = 50.0                   #required service level for substituting potable water demand through recycling
            self.service_res = 1
            self.service_hdr = 1
            self.service_com = 1
            self.service_li = 1
            self.service_hi = 1
            self.service_redundancy = 25.0
            self.servicevector = []

            #STRATEGY CUSTOMIZE
            self.createParameter("strategy_lot_check", BOOL, "")
            self.createParameter("strategy_street_check", BOOL, "")
            self.createParameter("strategy_neigh_check", BOOL, "")
            self.createParameter("strategy_subbas_check", BOOL, "")
            self.createParameter("lot_rigour", DOUBLE, "")
            self.createParameter("street_rigour", DOUBLE, "")
            self.createParameter("neigh_rigour", DOUBLE, "")
            self.createParameter("subbas_rigour", DOUBLE, "")
            self.strategy_lot_check = 1         #Plan technologies at Lot scale?
            self.strategy_street_check = 1      #Plan technologies at Street scale?
            self.strategy_neigh_check = 1       #Plan technologies at Neighbourhood scale?
            self.strategy_subbas_check = 1      #Plan technologies at Sub-basin scale?
            self.lot_rigour = 4.0               #How many increments at lot scale? (4 = 0, 0.25, 0.5, 0.75, 1.0) 
            self.street_rigour = 4.0            #How many increments at street scale? (4 = 0, 0.25, 0.5, 0.75, 1.0)
            self.neigh_rigour = 4.0             #How many increments at neighbourhood scale? (4 = 0, 0.25, 0.5, 0.75, 1.0)
            self.subbas_rigour = 4.0            #How many increments at sub-basin scale? (4 = 0, 0.25, 0.5, 0.75, 1.0)

            #REGIONAL RECYCLING-SUPPLY ZONES
            self.createParameter("rec_demrange_min", DOUBLE, "")
            self.createParameter("rec_demrange_max", DOUBLE, "")
            self.createParameter("ww_kitchen", BOOL, "")
            self.createParameter("ww_shower", BOOL, "")
            self.createParameter("ww_toilet", BOOL, "")
            self.createParameter("ww_laundry", BOOL, "")
            self.createParameter("hs_strategy", STRING, "")
            self.rec_demrange_min = 10.0
            self.rec_demrange_max = 100.0
            self.ww_kitchen = 0         #Kitchen WQ default = GW
            self.ww_shower = 0          #Shower WQ default = GW
            self.ww_toilet = 0          #Toilet WQ default = BW --> MUST BE RECYCLED
            self.ww_laundry = 0         #Laundry WQ default = GW
            self.hs_strategy = "ud"         #ud = upstream-downstream, uu = upstream-upstream, ua = upstream-around

            #ADDITIONAL INPUTS
            self.createParameter("sb_method", STRING, "")
            self.createParameter("rain_length", DOUBLE, "")
            self.createParameter("swh_benefits", BOOL, "")
            self.createParameter("swh_unitrunoff", DOUBLE, "")
            self.createParameter("swh_unitrunoff_auto", BOOL, "")
            self.sb_method = "Sim"  #Sim = simulation, Eqn = equation
            self.rain_length = 2.0   #number of years.
            self.swh_benefits = 1   #execute function to calculate SWH benefits? (1 by default, but perhaps treat as mutually exclusive)
            self.swh_unitrunoff = 0.545  #Unit runoff rate [kL/sqm impervious]
            self.swh_unitrunoff_auto = 0

            ##########################################################################
            #---RETROFIT CONDITIONS INPUTS                                           
            ##########################################################################

            #SCENARIO DESCRIPTION
            self.createParameter("retrofit_scenario", STRING,"")
            self.createParameter("renewal_cycle_def", BOOL,"")
            self.createParameter("renewal_lot_years", DOUBLE,"")
            self.createParameter("renewal_street_years", DOUBLE,"")
            self.createParameter("renewal_neigh_years", DOUBLE,"")
            self.createParameter("renewal_lot_perc", DOUBLE,"")
            self.createParameter("force_street", BOOL,"")
            self.createParameter("force_neigh", BOOL,"")
            self.createParameter("force_prec", BOOL,"")
            self.retrofit_scenario = "N"    #N = Do Nothing, R = With Renewal, F = Forced
            self.renewal_cycle_def = 1      #Defined renewal cycle?
            self.renewal_lot_years = 10.0         #number of years to apply renewal rate
            self.renewal_street_years = 20.0      #cycle of years for street-scale renewal
            self.renewal_neigh_years = 40.0       #cycle of years for neighbourhood-precinct renewal
            self.renewal_lot_perc = 5.0           #renewal percentage
            self.force_street = 0              #forced renewal on lot?
            self.force_neigh = 0           #forced renewal on street?
            self.force_prec = 0            #forced renewal on neighbourhood and precinct?

            #LIFE CYCLE OF EXISTING SYSTEMS
            self.createParameter("lot_renew", BOOL,"")
            self.createParameter("lot_decom", BOOL,"")
            self.createParameter("street_renew", BOOL,"")
            self.createParameter("street_decom", BOOL,"")
            self.createParameter("neigh_renew", BOOL,"")
            self.createParameter("neigh_decom", BOOL,"")
            self.createParameter("prec_renew", BOOL,"")
            self.createParameter("prec_decom", BOOL,"")
            self.createParameter("decom_thresh", DOUBLE,"")
            self.createParameter("renewal_thresh", DOUBLE,"")
            self.createParameter("renewal_alternative", STRING,"")
            self.lot_renew = 0      #NOT USED UNLESS LOT RENEWAL ALGORITHM EXISTS
            self.lot_decom = 0
            self.street_renew = 0
            self.street_decom = 0
            self.neigh_renew = 0
            self.neigh_decom = 0
            self.prec_renew = 0
            self.prec_decom = 0
            self.decom_thresh = 40.0
            self.renewal_thresh = 30.0
            self.renewal_alternative = "K"          #if renewal cannot be done, what to do then? K=Keep, D=Decommission

            ##########################################################################
            #---TECHNOLOGIES LIST AND CUSTOMIZATION                                  
            ##########################################################################

            #---BIOFILTRATION SYSTEM/RAINGARDEN [BF]--------------------------------
            self.createParameter("BFstatus", BOOL,"")
            self.BFstatus = 1

            #Available Scales
            self.createParameter("BFlot", BOOL,"")
            self.createParameter("BFstreet", BOOL,"")
            self.createParameter("BFneigh", BOOL,"")
            self.createParameter("BFprec", BOOL,"")
            self.BFlot = 1
            self.BFstreet = 1
            self.BFneigh = 1
            self.BFprec = 1

            #Available Applications
            self.createParameter("BFflow", BOOL, "")
            self.createParameter("BFpollute", BOOL,"")
            self.createParameter("BFrecycle", BOOL, "")
            self.BFflow = 1
            self.BFpollute = 1
            self.BFrecycle = 1

            #Design Curves
            self.createParameter("BFdesignUB", BOOL,"")
            self.createParameter("BFdescur_path", STRING,"")
            self.BFdesignUB = 1          #use DAnCE4Water's default curves to design system?
            self.BFdescur_path = "no file"  #path for design curve

            #Design Information
            self.createParameter("BFspec_EDD", DOUBLE,"")
            self.createParameter("BFspec_FD", DOUBLE,"")
            self.createParameter("BFminsize", DOUBLE, "")
            self.createParameter("BFmaxsize", DOUBLE,"")
            self.createParameter("BFavglife", DOUBLE,"")
            self.createParameter("BFexfil", DOUBLE,"")
            self.BFspec_EDD = 0.4
            self.BFspec_FD = 0.6
            self.BFminsize = 5.0              #minimum surface area of the system in sqm
            self.BFmaxsize = 999999.0         #maximum surface area of system in sqm
            self.BFavglife = 20.0             #average life span of a biofilter
            self.BFexfil = 0.0

            #---INFILTRATION SYSTEM [IS]--------------------------------------------
            self.createParameter("ISstatus", BOOL,"")
            self.ISstatus = 1

            #Available Scales
            self.createParameter("ISlot", BOOL,"")
            self.createParameter("ISstreet", BOOL,"")
            self.createParameter("ISneigh", BOOL,"")
            self.createParameter("ISprec", BOOL, "")
            self.ISlot = 1
            self.ISstreet = 1
            self.ISneigh = 1
            self.ISprec = 1

            #Available Applications
            self.createParameter("ISflow", BOOL,"")
            self.createParameter("ISpollute", BOOL,"")
            self.ISflow = 1
            self.ISpollute = 1
            self.ISrecycle = 0      #Permanently zero

            #Design Curves
            self.createParameter("ISdesignUB", BOOL,"")
            self.createParameter("ISdescur_path", STRING,"")
            self.ISdesignUB = 1          #use DAnCE4Water's default curves to design system?
            self.ISdescur_path = "no file"  #path for design curve

            #Design Information        self.createParameter("ISspec_EDD", DOUBLE,"")
            self.createParameter("ISspec_FD", DOUBLE,"")
            self.createParameter("ISspec_EDD", DOUBLE,"")
            self.createParameter("ISminsize", DOUBLE, "")
            self.createParameter("ISmaxsize", DOUBLE,"")
            self.createParameter("ISavglife", DOUBLE,"")
            self.createParameter("ISexfil", DOUBLE, "")
            self.ISspec_EDD = 0.2
            self.ISspec_FD = 0.8
            self.ISminsize = 5.0
            self.ISmaxsize = 99999.0          #maximum surface area of system in sqm
            self.ISavglife = 20.0             #average life span of an infiltration system
            self.ISexfil = 3.6

            #---PONDS & SEDIMENTATION BASIN [PB]------------------------------------
            self.createParameter("PBstatus", BOOL,"")
            self.PBstatus = 1

            #Available Scales
            self.createParameter("PBneigh", BOOL,"")
            self.createParameter("PBprec", BOOL,"")
            self.PBneigh = 1
            self.PBprec = 1

            #Available Applications
            self.createParameter("PBflow", BOOL,"")
            self.createParameter("PBpollute", BOOL,"")
            self.createParameter("PBrecycle", BOOL, "")
            self.PBflow = 1
            self.PBpollute = 1
            self.PBrecycle = 0

            #Design Curves
            self.createParameter("PBdesignUB", BOOL,"")
            self.createParameter("PBdescur_path", STRING,"")
            self.PBdesignUB = 1          #use DAnCE4Water's default curves to design system?
            self.PBdescur_path = "no file"  #path for design curve

            #Design Information
            self.createParameter("PBspec_MD", STRING,"")
            self.createParameter("PBminsize", DOUBLE, "")
            self.createParameter("PBmaxsize", DOUBLE,"")
            self.createParameter("PBavglife", DOUBLE,"")
            self.createParameter("PBexfil", DOUBLE, "")
            self.PBspec_MD = "0.75"     #need a string for the combo box
            self.PBminsize = 100.0
            self.PBmaxsize = 9999999.0           #maximum surface area of system in sqm
            self.PBavglife = 20.0             #average life span of a pond/basin
            self.PBexfil = 0.36

            #---RAINWATER TANK [RT]-------------------------------------------------
            self.createParameter("RTstatus", BOOL,"")
            self.RTstatus = 0

            self.createParameter("RTlot", BOOL,"")
            self.createParameter("RTneigh", BOOL,"")
            self.createParameter("RTflow", BOOL,"")
            self.createParameter("RTrecycle", BOOL,"")
            self.RTlot = 1
            self.RTneigh = 0
            self.RTflow = 0
            self.RTpollute = 0      #permanently zero
            self.RTrecycle = 1

            self.createParameter("RT_maxdepth", DOUBLE,"")
            self.createParameter("RT_mindead", DOUBLE,"")
            self.createParameter("RTdesignUB", BOOL,"")
            self.createParameter("RTdescur_path", STRING,"")
            self.createParameter("RTavglife", DOUBLE,"")
            self.RT_maxdepth = 2.0            #max tank depth [m]
            self.RT_mindead = 0.1           #minimum dead storage level [m]
            self.RTdesignUB = 1         #use DAnCE4Water's default curves to design system?
            self.RTdescur_path = "no file"  #path for design curve
            self.RTavglife = 20.0             #average life span of a raintank

            self.RTminsize = 0.0             #placeholders, do not actually matter
            self.RTmaxsize = 9999.0

            #---SURFACE WETLAND [WSUR]----------------------------------------------
            self.createParameter("WSURstatus", BOOL,"")
            self.WSURstatus = 1

            #Available Scales
            self.createParameter("WSURneigh", BOOL,"")
            self.createParameter("WSURprec", BOOL,"")
            self.WSURneigh = 1
            self.WSURprec = 1

            #Available Applications
            self.createParameter("WSURflow", BOOL,"")
            self.createParameter("WSURpollute", BOOL,"")
            self.createParameter("WSURrecycle", BOOL, "")
            self.WSURflow = 1
            self.WSURpollute = 1
            self.WSURrecycle = 0

            #Design Curves
            self.createParameter("WSURdesignUB", BOOL,"")
            self.createParameter("WSURdescur_path", STRING,"")
            self.WSURdesignUB = 1          #use DAnCE4Water's default curves to design system?
            self.WSURdescur_path = "no file"  #path for design curve

            #Design Information
            self.createParameter("WSURspec_EDD", STRING,"")
            self.createParameter("WSURminsize", DOUBLE, "")
            self.createParameter("WSURmaxsize", DOUBLE,"")
            self.createParameter("WSURavglife", DOUBLE,"")
            self.createParameter("WSURexfil", DOUBLE, "") 
            self.WSURspec_EDD = "0.75"
            self.WSURminsize = 200.0
            self.WSURmaxsize = 9999999.0           #maximum surface area of system in sqm
            self.WSURavglife = 20.0             #average life span of a wetland
            self.WSURexfil = 0.36

            #---SWALES & BUFFER STRIPS [SW]-----------------------------------------
            self.createParameter("SWstatus", BOOL,"")
            self.SWstatus = 0

            #Available Scales
            self.createParameter("SWstreet", BOOL,"")
            self.createParameter("SWneigh", BOOL,"")
            self.SWstreet = 1
            self.SWneigh = 1

            #Available Applications
            self.createParameter("SWflow", BOOL,"")
            self.createParameter("SWpollute", BOOL,"")
            self.createParameter("SWrecycle", BOOL, "")
            self.SWflow = 1
            self.SWpollute = 1
            self.SWrecycle = 0

            #Design Curves
            self.createParameter("SWdesignUB", BOOL,"")
            self.createParameter("SWdescur_path", STRING,"")
            self.SWdesignUB = 1          #use DAnCE4Water's default curves to design system?
            self.SWdescur_path = "no file"  #path for design curve

            #Design Information
            self.createParameter("SWspec", DOUBLE,"")
            self.createParameter("SWminsize", DOUBLE, "")
            self.createParameter("SWmaxsize", DOUBLE,"")
            self.createParameter("SWavglife", DOUBLE,"")
            self.createParameter("SWexfil", DOUBLE, "")
            self.SWspec = 0.0
            self.SWminsize = 20.0
            self.SWmaxsize = 9999.0           #maximum surface area of system in sqm
            self.SWavglife = 20.0             #average life span of a swale
            self.SWexfil = 3.6              

            #---REGIONAL INFORMATION -----------------------------------------------
            self.createParameter("regioncity", STRING,"")
            self.regioncity = "Melbourne"

            #---MULTI-CRITERIA INPUTS-----------------------------------------------
            #SELECT EVALUATION METRICS
            self.createParameter("scoringmatrix_path", STRING,"")
            self.createParameter("scoringmatrix_default", BOOL,"")
            self.scoringmatrix_path = ""
            self.scoringmatrix_default = 1

            #CUSTOMIZE EVALUATION CRITERIA
            self.createParameter("bottomlines_tech", BOOL,"")
            self.createParameter("bottomlines_env", BOOL,"")
            self.createParameter("bottomlines_ecn",BOOL,"")
            self.createParameter("bottomlines_soc", BOOL,"")
            self.createParameter("bottomlines_tech_n", DOUBLE,"")
            self.createParameter("bottomlines_env_n", DOUBLE,"")
            self.createParameter("bottomlines_ecn_n", DOUBLE,"")
            self.createParameter("bottomlines_soc_n", DOUBLE,"")
            self.createParameter("bottomlines_tech_w", DOUBLE,"")
            self.createParameter("bottomlines_env_w", DOUBLE,"")
            self.createParameter("bottomlines_ecn_w", DOUBLE,"")
            self.createParameter("bottomlines_soc_w", DOUBLE,"")
            self.bottomlines_tech = 1   #Include criteria? Yes/No
            self.bottomlines_env = 1
            self.bottomlines_ecn = 1
            self.bottomlines_soc = 1
            self.bottomlines_tech_n = 4.0     #Metric numbers
            self.bottomlines_env_n = 5.0
            self.bottomlines_ecn_n = 2.0
            self.bottomlines_soc_n = 4.0
            self.bottomlines_tech_w = 1.0     #Criteria Weights
            self.bottomlines_env_w = 1.0
            self.bottomlines_ecn_w = 1.0
            self.bottomlines_soc_w = 1.0
            self.mca_techlist, self.mca_tech, self.mca_env, self.mca_ecn, self.mca_soc = [], [], [], [], [] #initialize as globals

            #SCORING OF STRATEGIES
            self.createParameter("score_strat", STRING, "")
            self.createParameter("scope_stoch", BOOL,"")
            self.createParameter("score_method", STRING,"")
            self.createParameter("ingroup_scoring", STRING,"")
            self.createParameter("iao_influence", DOUBLE, "")
            self.scope_stoch = 0
            self.score_strat = "SNP"        #SNP = service-no-penalty, SLP = service-linear-penalty, SPP = service-nonlinear-penalty
            self.score_method = "WSM"       #MCA scoring method
            self.ingroup_scoring = "Avg"
            self.iao_influence = 10.0

            #RANKING OF STRATEGIES
            self.createParameter("ranktype", STRING,"")
            self.createParameter("topranklimit", DOUBLE,"")
            self.createParameter("conf_int", DOUBLE,"")
            self.createParameter("pickingmethod", STRING, "")
            self.ranktype = "RK"            #CI = Confidence Interval, RK = ranking
            self.topranklimit = 10.0
            self.conf_int = 95.0
            self.pickingmethod = "TOP"  #TOP = score-based, RND = random sampling

            ########################################################################
            #---ADVANCED PARAMETERS & VARIABLES
            ########################################################################
            self.technames = ["ASHP", "AQ", "ASR", "BF", "GR", "GT", 
                          "GPT", "IS", "PPL", "PB", "PP", "RT", 
                          "SF", "IRR", "WSUB", "WSUR", "SW", 
                          "TPS", "UT", "WWRR", "WT"]

            self.scaleabbr = ["lot", "street", "neigh", "prec"]
            self.ffplevels = {"PO":1, "NP":2, "RW":3, "SW":4, "GW":5}  #Used to determine when a system is cleaner than the other
            self.sqlDB = 0  #Global variable to hold the sqlite database
            self.dbcurs = 0 #cursor to execute sqlcommands for the sqlite database
            self.lot_incr = []
            self.street_incr = []
            self.neigh_incr = []
            self.subbas_incr = []

            self.createParameter("num_output_strats", DOUBLE, "")
            self.num_output_strats = 5      #number of output strategies

            self.createParameter("startyear", DOUBLE, "")
            self.createParameter("prevyear", DOUBLE, "")
            self.createParameter("currentyear", DOUBLE, "")
            self.startyear = 1960  #Retrofit Advanced Parameters - Set by Model Core
            self.prevyear = 1960
            self.currentyear = 1980

            #SWH Harvesting algorithms
            self.createParameter("rainfile", STRING, "")    #Rainfall file for SWH
            self.rainfile = "MelbourneRain1998-2007-6min.csv"
            self.createParameter("rain_dt", DOUBLE, "")
            self.rain_dt = 6        #[mins]
            self.createParameter("evapfile", STRING, "")
            self.evapfile = "MelbourneEvap1998-2007-Day.csv"
            self.createParameter("evap_dt", DOUBLE, "")
            self.evap_dt = 1440     #[mins]
            self.lot_raintanksizes = [1,2,3,4,5,7.5,10,15,20]       #[kL]
            self.raindata = []      #Globals to contain the data time series
            self.evapdata = []
            self.evapscale = []
            self.sysdepths = {}     #Holds all calculated system depths

            self.swhbenefitstable = []

            self.createParameter("relTolerance", DOUBLE, "")
            self.createParameter("maxSBiterations", DOUBLE, "")
            self.relTolerance = 1
            self.maxSBiterations = 100

            self.createParameter("maxMCiterations", DOUBLE, "")
            self.createParameter("defaultdecision", STRING, "")
            self.maxMCiterations = 1000
            self.defaultdecision = "H"

            #MCA Penalties
            self.createParameter("penaltyQty", BOOL, "")
            self.createParameter("penaltyWQ", BOOL, "")
            self.createParameter("penaltyRec", BOOL, "")
            self.createParameter("penaltyFa", DOUBLE, "")
            self.createParameter("penaltyFb", DOUBLE, "")
            self.penaltyQty = 1
            self.penaltyWQ = 1
            self.penaltyRec = 1
            self.penaltyFa = 2.0
            self.penaltyFb = 1.2


            self.attnames = ["BlockID", "BasinID", "Status", "Active", "Nhd_N", "Nhd_S", 
                    "Nhd_W", "Nhd_E", "Nhd_NE", "Nhd_NW", "Nhd_SE", "Nhd_SW", "Soil_k", 
                    "AvgElev", "pLU_RES", "pLU_COM", "pLU_LI", "pLU_CIV", "pLU_SVU", 
                    "pLU_RD", "pLU_TR", "pLU_PG", "pLU_REF", "pLU_UND", "pLU_NA", "Pop", 
                    "downID", "Outlet", "MiscAtot", "OpenSpace", "AGardens", "ASquare", 
                    "PG_av", "REF_av", "ANonW_Util", "SVU_avWS", "SVU_avWW", "SVU_avSW", 
                    "SVU_avOTH", "RoadTIA", "RD_av", "RDMedW", "DemPublicI", "HouseOccup", "ResFrontT",
                    "avSt_RES", "WResNstrip", "ResAllots", "ResDWpLot", "ResHouses", "ResLotArea", 
                    "ResRoof", "avLt_RES", "ResLotTIA", "ResLotEIA", "ResGarden", "DemPrivI", 
                    "ResRoofCon", "HDRFlats", "HDRRoofA", "HDROccup", "HDR_TIA", "HDR_EIA", 
                    "HDRFloors", "av_HDRes", "HDRGarden", "HDRCarPark", "DemAptI", 
                    "LIjobs", "LIestates", "avSt_LI", "LIAfront", "LIAfrEIA", "LIAestate", "LIAeBldg", 
                    "LIFloors", "LIAeLoad", "LIAeCPark", "avLt_LI", "LIAeLgrey", "LIAeEIA", "LIAeTIA", 
                    "HIjobs", "HIestates", "avSt_HI", "HIAfront", "HIAfrEIA", "HIAestate", "HIAeBldg", 
                    "HIFloors", "HIAeLoad", "HIAeCPark", "avLt_HI", "HIAeLgrey", "HIAeEIA", "HIAeTIA", 
                    "ORCjobs", "ORCestates", "avSt_ORC", "ORCAfront", "ORCAfrEIA", "ORCAestate", "ORCAeBldg", 
                    "ORCFloors", "ORCAeLoad", "ORCAeCPark", "avLt_ORC", "ORCAeLgrey", "ORCAeEIA", "ORCAeTIA", 
                    "COMjobs", "COMestates", "avSt_COM", "COMAfront", "COMAfrEIA", 
                    "COMAestate", "COMAeBldg", "COMFloors", "COMAeLoad", "COMAeCPark", "avLt_COM", 
                    "COMAeLgrey", "COMAeEIA", "COMAeTIA", "Blk_TIA", "Blk_EIA", "Blk_EIF", 
                    "Blk_TIF", "Blk_RoofsA", "wd_PrivIN", "wd_PrivOUT", "wd_Nres_IN", "Apub_irr", 
                    "wd_PubOUT", "Blk_WD", "Blk_Kitch", "Blk_Shower", "Blk_Toilet", "Blk_Laund", 
                    "Blk_Garden", "Blk_Com", "Blk_Ind", "Blk_PubIrr", "HasHouses", "HasFlats", 
                    "Has_LI", "Has_Com", "Has_HI", "Has_ORC", "HasL_RESSys", "HasL_HDRSys", "HasL_LISys",
                    "HasL_HISys", "HasL_COMSys", "HasSSys", "HasNSys", "HasBSys"]

            self.blockDict = {}
            self.blockIDlist = []
            self.downIDlist = []

            self.curscalepref = {"L":0.25, "S":0.25, "N":0.25, "B":0.25}


      def init(self):

            #Data Stream Definition
            self.regiondata = ViewContainer("regiondata", COMPONENT, READ)
            self.regiondata.addAttribute("NumBlocks", DOUBLE, READ)
            self.regiondata.addAttribute("BlockSize", DOUBLE, READ)
            self.regiondata.addAttribute("TotalBasins", DOUBLE, READ)

            self.blockdata = ViewContainer("blockdata", COMPONENT, READ)
            self.blockdata.addAttribute("BlockID", DOUBLE, READ)
            self.blockdata.addAttribute("BasinID", DOUBLE, READ)
            self.blockdata.addAttribute("Status", DOUBLE, READ)
            self.blockdata.addAttribute("Active", DOUBLE, READ)
            self.blockdata.addAttribute("Nhd_N", DOUBLE, READ)
            self.blockdata.addAttribute("Nhd_S", DOUBLE, READ)
            self.blockdata.addAttribute("Nhd_W", DOUBLE, READ)
            self.blockdata.addAttribute("Nhd_E", DOUBLE, READ)
            self.blockdata.addAttribute("Nhd_NE", DOUBLE, READ)
            self.blockdata.addAttribute("Nhd_NW", DOUBLE, READ)
            self.blockdata.addAttribute("Nhd_SE", DOUBLE, READ)
            self.blockdata.addAttribute("Nhd_SW", DOUBLE, READ)
            self.blockdata.addAttribute("Soil_k", DOUBLE, READ)
            self.blockdata.addAttribute("AvgElev", DOUBLE, READ)
            self.blockdata.addAttribute("pLU_RES", DOUBLE, READ)
            self.blockdata.addAttribute("pLU_COM", DOUBLE, READ)   #commercial & offices
            self.blockdata.addAttribute("pLU_LI", DOUBLE, READ)    #light & heavy industry
            self.blockdata.addAttribute("pLU_CIV", DOUBLE, READ)
            self.blockdata.addAttribute("pLU_SVU", DOUBLE, READ)
            self.blockdata.addAttribute("pLU_RD", DOUBLE, READ)
            self.blockdata.addAttribute("pLU_TR", DOUBLE, READ)
            self.blockdata.addAttribute("pLU_PG", DOUBLE, READ)
            self.blockdata.addAttribute("pLU_REF", DOUBLE, READ)
            self.blockdata.addAttribute("pLU_UND", DOUBLE, READ)
            self.blockdata.addAttribute("pLU_NA", DOUBLE, READ)
            self.blockdata.addAttribute("Pop", DOUBLE, READ)
            self.blockdata.addAttribute("downID", DOUBLE, READ)
            self.blockdata.addAttribute("Outlet", DOUBLE, READ)
            self.blockdata.addAttribute("MiscAtot", DOUBLE, READ)
            self.blockdata.addAttribute("OpenSpace", DOUBLE, READ)
            self.blockdata.addAttribute("AGardens", DOUBLE, READ)
            self.blockdata.addAttribute("ASquare", DOUBLE, READ)
            self.blockdata.addAttribute("PG_av", DOUBLE, READ)
            self.blockdata.addAttribute("REF_av", DOUBLE, READ)
            self.blockdata.addAttribute("ANonW_Util", DOUBLE, READ)
            self.blockdata.addAttribute("SVU_avWS", DOUBLE, READ)
            self.blockdata.addAttribute("SVU_avWW", DOUBLE, READ)
            self.blockdata.addAttribute("SVU_avSW", DOUBLE, READ)
            self.blockdata.addAttribute("SVU_avOTH", DOUBLE, READ)
            self.blockdata.addAttribute("RoadTIA", DOUBLE, READ)
            self.blockdata.addAttribute("RD_av", DOUBLE, READ)
            self.blockdata.addAttribute("RDMedW", DOUBLE, READ)
            self.blockdata.addAttribute("DemPublicI", DOUBLE, READ)
            self.blockdata.addAttribute("HasHouses", DOUBLE, READ)
            self.blockdata.addAttribute("HouseOccup", DOUBLE, READ)
            self.blockdata.addAttribute("ResFrontT", DOUBLE, READ)
            self.blockdata.addAttribute("avSt_RES", DOUBLE, READ)
            self.blockdata.addAttribute("WResNstrip", DOUBLE, READ)
            self.blockdata.addAttribute("ResAllots", DOUBLE, READ)
            self.blockdata.addAttribute("ResDWpLot", DOUBLE, READ)
            self.blockdata.addAttribute("ResHouses", DOUBLE, READ)
            self.blockdata.addAttribute("ResLotArea", DOUBLE, READ)
            self.blockdata.addAttribute("ResRoof", DOUBLE, READ)
            self.blockdata.addAttribute("avLt_RES", DOUBLE, READ)
            self.blockdata.addAttribute("ResLotTIA", DOUBLE, READ)
            self.blockdata.addAttribute("ResLotEIA", DOUBLE, READ)
            self.blockdata.addAttribute("ResGarden", DOUBLE, READ)
            self.blockdata.addAttribute("DemPrivI", DOUBLE, READ)
            self.blockdata.addAttribute("ResRoofCon", DOUBLE, READ)
            self.blockdata.addAttribute("HasFlats", DOUBLE, READ)
            self.blockdata.addAttribute("HDRFlats", DOUBLE, READ)
            self.blockdata.addAttribute("HDRRoofA", DOUBLE, READ)
            self.blockdata.addAttribute("HDROccup", DOUBLE, READ)
            self.blockdata.addAttribute("HDR_TIA", DOUBLE, READ)
            self.blockdata.addAttribute("HDR_EIA", DOUBLE, READ)
            self.blockdata.addAttribute("HDRFloors", DOUBLE, READ)
            self.blockdata.addAttribute("av_HDRes", DOUBLE, READ)
            self.blockdata.addAttribute("HDRGarden", DOUBLE, READ)
            self.blockdata.addAttribute("HDRCarPark", DOUBLE, READ)
            self.blockdata.addAttribute("DemAptI", DOUBLE, READ)
            self.blockdata.addAttribute("Has_LI", DOUBLE, READ)
            self.blockdata.addAttribute("LIjobs", DOUBLE, READ)
            self.blockdata.addAttribute("LIestates", DOUBLE, READ)
            self.blockdata.addAttribute("avSt_LI", DOUBLE, READ)
            self.blockdata.addAttribute("LIAfront", DOUBLE, READ)
            self.blockdata.addAttribute("LIAfrEIA", DOUBLE, READ)
            self.blockdata.addAttribute("LIAestate", DOUBLE, READ)
            self.blockdata.addAttribute("LIAeBldg", DOUBLE, READ)
            self.blockdata.addAttribute("LIFloors", DOUBLE, READ)
            self.blockdata.addAttribute("LIAeLoad", DOUBLE, READ)
            self.blockdata.addAttribute("LIAeCPark", DOUBLE, READ)
            self.blockdata.addAttribute("avLt_LI", DOUBLE, READ)
            self.blockdata.addAttribute("LIAeLgrey", DOUBLE, READ)
            self.blockdata.addAttribute("LIAeEIA", DOUBLE, READ)
            self.blockdata.addAttribute("LIAeTIA", DOUBLE, READ)
            self.blockdata.addAttribute("Has_HI", DOUBLE, READ)
            self.blockdata.addAttribute("HIjobs", DOUBLE, READ)
            self.blockdata.addAttribute("HIestates", DOUBLE, READ)
            self.blockdata.addAttribute("avSt_HI", DOUBLE, READ)
            self.blockdata.addAttribute("HIAfront", DOUBLE, READ)
            self.blockdata.addAttribute("HIAfrEIA", DOUBLE, READ)
            self.blockdata.addAttribute("HIAestate", DOUBLE, READ)
            self.blockdata.addAttribute("HIAeBldg", DOUBLE, READ)
            self.blockdata.addAttribute("HIFloors", DOUBLE, READ)
            self.blockdata.addAttribute("HIAeLoad", DOUBLE, READ)
            self.blockdata.addAttribute("HIAeCPark", DOUBLE, READ)
            self.blockdata.addAttribute("avLt_HI", DOUBLE, READ)
            self.blockdata.addAttribute("HIAeLgrey", DOUBLE, READ)
            self.blockdata.addAttribute("HIAeEIA", DOUBLE, READ)
            self.blockdata.addAttribute("HIAeTIA", DOUBLE, READ)
            self.blockdata.addAttribute("Has_Com", DOUBLE, READ)
            self.blockdata.addAttribute("COMjobs", DOUBLE, READ)
            self.blockdata.addAttribute("COMestates", DOUBLE, READ)
            self.blockdata.addAttribute("avSt_COM", DOUBLE, READ)
            self.blockdata.addAttribute("COMAfront", DOUBLE, READ)
            self.blockdata.addAttribute("COMAfrEIA", DOUBLE, READ)
            self.blockdata.addAttribute("COMAestate", DOUBLE, READ)
            self.blockdata.addAttribute("COMAeBldg", DOUBLE, READ)
            self.blockdata.addAttribute("COMFloors", DOUBLE, READ)
            self.blockdata.addAttribute("COMAeLoad", DOUBLE, READ)
            self.blockdata.addAttribute("COMAeCPark", DOUBLE, READ)
            self.blockdata.addAttribute("avLt_COM", DOUBLE, READ)
            self.blockdata.addAttribute("COMAeLgrey", DOUBLE, READ)
            self.blockdata.addAttribute("COMAeEIA", DOUBLE, READ)
            self.blockdata.addAttribute("COMAeTIA", DOUBLE, READ)
            self.blockdata.addAttribute("Has_ORC", DOUBLE, READ)
            self.blockdata.addAttribute("ORCjobs", DOUBLE, READ)
            self.blockdata.addAttribute("ORCestates", DOUBLE, READ)
            self.blockdata.addAttribute("avSt_ORC", DOUBLE, READ)
            self.blockdata.addAttribute("ORCAfront", DOUBLE, READ)
            self.blockdata.addAttribute("ORCAfrEIA", DOUBLE, READ)
            self.blockdata.addAttribute("ORCAestate", DOUBLE, READ)
            self.blockdata.addAttribute("ORCAeBldg", DOUBLE, READ)
            self.blockdata.addAttribute("ORCFloors", DOUBLE, READ)
            self.blockdata.addAttribute("ORCAeLoad", DOUBLE, READ)
            self.blockdata.addAttribute("ORCAeCPark", DOUBLE, READ)
            self.blockdata.addAttribute("avLt_ORC", DOUBLE, READ)
            self.blockdata.addAttribute("ORCAeLgrey", DOUBLE, READ)
            self.blockdata.addAttribute("ORCAeEIA", DOUBLE, READ)
            self.blockdata.addAttribute("ORCAeTIA", DOUBLE, READ)
            self.blockdata.addAttribute("Blk_TIA", DOUBLE, READ)
            self.blockdata.addAttribute("Blk_EIA", DOUBLE, READ)
            self.blockdata.addAttribute("Blk_EIF", DOUBLE, READ)
            self.blockdata.addAttribute("Blk_TIF", DOUBLE, READ)
            self.blockdata.addAttribute("Blk_RoofsA", DOUBLE, READ)
            self.blockdata.addAttribute("wd_PrivIN", DOUBLE, READ)
            self.blockdata.addAttribute("wd_PrivOUT", DOUBLE, READ)
            self.blockdata.addAttribute("wd_Nres_IN", DOUBLE, READ)
            self.blockdata.addAttribute("Apub_irr", DOUBLE, READ)
            self.blockdata.addAttribute("wd_PubOUT", DOUBLE, READ)
            self.blockdata.addAttribute("Blk_WD", DOUBLE, READ)
            self.blockdata.addAttribute("Blk_Kitch", DOUBLE, READ)
            self.blockdata.addAttribute("Blk_Shower", DOUBLE, READ)
            self.blockdata.addAttribute("Blk_Toilet", DOUBLE, READ)
            self.blockdata.addAttribute("Blk_Laund", DOUBLE, READ)
            self.blockdata.addAttribute("Blk_Garden", DOUBLE, READ)
            self.blockdata.addAttribute("Blk_Com", DOUBLE, READ)
            self.blockdata.addAttribute("Blk_Ind", DOUBLE, READ)
            self.blockdata.addAttribute("Blk_PubIrr", DOUBLE, READ)
            self.blockdata.addAttribute("HasL_RESSys", DOUBLE, READ)
            self.blockdata.addAttribute("HasL_HDRSys", DOUBLE, READ)
            self.blockdata.addAttribute("HasL_LISys", DOUBLE, READ)
            self.blockdata.addAttribute("HasL_HISys", DOUBLE, READ)
            self.blockdata.addAttribute("HasL_COMSys", DOUBLE, READ)
            self.blockdata.addAttribute("HasSSys", DOUBLE, READ)
            self.blockdata.addAttribute("HasNSys", DOUBLE, READ)
            self.blockdata.addAttribute("HasBSys", DOUBLE, READ)

            views = []
            views.append(self.regiondata)
            views.append(self.blockdata)
            self.registerViewContainers(views)


      def run(self):
            ###-------------------------------------------------------------------###
            #--- DYNAMIND PRE-PROCESSING
            ###-------------------------------------------------------------------###
            #-------------------------------------------------------------------------------------------------------
            #Retrieve data to work with - NOTE THIS NEEDS TO BE REPLACED WITH WHATEVER DAnCE wants to implement
            self.regiondata.reset_reading()
            
            for r in self.regiondata:
                  mapdata = r

            self.blockdata.reset_reading()
            for block in self.blockdata:
                  curID = block.GetFieldAsInteger("BlockID")
                  print curID
                  self.blockDict[curID] = {}
                  for key in self.attnames:
                        self.blockDict[curID][key] = block.GetFieldAsDouble(key)
            #End Result is a dictionary of dictionaries. Each key in the outer dictionary represents a BlocKID, each 
            #key in the inner dictionary represents the attributes of that block
            #---------------------------------------------------------------------------------------------------------


            ################################################################################
            ## UrbanBEATS WSUD Planning Module CODE STRUCTURE
            ## ----------------------------------------------
            ##    - Section ! - Pre-processing
            ##    - Section A - Recalculate Impervious Area to Service
            ##    - Seciton B - Retrofit Algorithm
            ##    - Section C - Opportunities Mapping of Individual Techs
            ##          > C.1 - Initialise Increment Variables
            ##          > C.2 - Load climate data if harvesting
            ##          > C.3 - Block Opportunities Assessment
            ##                ' C.3.1 - Assess Lot Opportunities
            ##                ' C.3.2 - Assess Street Opportunities
            ##                ' C.3.3 - Assess Neighbourhood Opportunities
            ##                ' C.3.4 - Assess Sub-basin Opportunities
            ##          >C.4 - Construct In-block Options
            ##
            ################################################################################
            

            ###-------------------------------------------------------------------###
            #--- SECTION ! - Pre-Processing
            ###-------------------------------------------------------------------###        

            #CALCULATE SOME GLOBAL VARIABLES RELATING TO TARGETS
            self.system_tarQ = self.ration_runoff * self.targets_runoff     #Runoff reduction target
            self.system_tarTSS = self.ration_pollute * self.targets_TSS     #TSS reduction target
            self.system_tarTP = self.ration_pollute * self.targets_TP       #TP reduction target
            self.system_tarTN = self.ration_pollute * self.targets_TN       #TN reduction target
            self.system_tarREL = self.ration_harvest * self.targets_reliability     #Reliability  of recycling

            self.targetsvector = [self.system_tarQ, self.system_tarTSS, self.system_tarTP, self.system_tarTN, self.system_tarREL]
            print self.targetsvector      #-> targetsvector TO BE USED TO ASSESS OPPORTUNITIES
            
            self.servicevector = [self.service_swmQty, self.service_swmWQ, self.service_rec]
            print self.servicevector
            
            #CALCULATE SYSTEM DEPTHS
            self.sysdepths = {"RT": self.RT_maxdepth - self.RT_mindead, "WSUR": self.WSURspec_EDD, "PB": self.PBspec_MD}

            #SET DESIGN CURVES DIRECTORY - ALL CURVES NEED TO BE LOCATED IN THIS DIRECTORY
            #To be done later.

            #GET NECESSARY GLOBAL DATA TO DO ANALYSIS
            blocks_num = mapdata.GetFieldAsInteger("NumBlocks")     #number of blocks to loop through
            self.block_size = mapdata.GetFieldAsDouble("BlockSize")    #size of block
            basins = mapdata.GetFieldAsInteger("TotalBasins")
            
            #CREATE TECHNOLOGIES SHORTLIST - THIS IS THE USER'S CUSTOMISED SHORTLIST
            userTechList = self.compileUserTechList()               #holds the active technologies selected by user for simulation
            print userTechList

            #CREATE TECHNOLOGY LISTS FOR DIFFERENT SCALES
            techListLot = self.fillScaleTechList("lot", userTechList)
            techListStreet = self.fillScaleTechList("street", userTechList)
            techListNeigh = self.fillScaleTechList("neigh", userTechList)
            techListSubbas = self.fillScaleTechList("subbas", userTechList)
            print "Lot"+str(techListLot)
            print "Street"+str(techListStreet)
            print "Neighbourhood"+str(techListNeigh)
            print "Sub-basin"+str(techListSubbas)

            #INITIALIZE STORMWATER HARVESTING BENEFITS DATA
            if self.swh_benefits:
                  self.swhbenefitstable = dcv.initializeSWHbenefitsTable(ANCILLARY_PATH)

            #PROCESS MCA PARAMETERS AND SCORING DETAILS
            self.mca_techlist, self.mca_tech, self.mca_env, self.mca_ecn, self.mca_soc = self.retrieveMCAscoringmatrix()
            print self.mca_techlist
            print self.mca_tech
            print self.mca_env
            print self.mca_ecn
            print self.mca_soc

            #Calculate MCA weightings for different PURPOSES - used to penalize MCA score if tech does not meet particular purpose
            self.priorities = [int(self.ration_runoff)*float(self.runoff_pri), 
                           int(self.ration_pollute)*float(self.pollute_pri),
                           int(self.ration_harvest)*float(self.harvest_pri)]
            prioritiessum = sum(self.priorities)
            for i in range(len(self.priorities)):       #e.g. ALL and priorities 3,2,1 --> [3/6, 2/6, 1/6]
                  if prioritiessum == 0:
                        self.priorities[i] = 1
                  else:
                        self.priorities[i] = self.priorities[i]/prioritiessum               #1, 2 and priorities 3,2,1 --> [3/5, 2/5, 0]
            print self.priorities
            print "Now planning technologies"


            ###-------------------------------------------------------------------###
            #---  SECTION A1 - RECALCULATE IMP AREA TO SERVE                     ---#
            ###-------------------------------------------------------------------###
            #DETERMINE IMPERVIOUS AREAS TO MANAGE BASED ON LAND USES
            for currentID in self.blockDict.keys():
                  currentAttList = self.blockDict[currentID]
                  if currentAttList["Status"] == 0:
                        continue
                  block_EIA = currentAttList["Blk_EIA"]

                  if self.service_res == False:
                        AimpRes = currentAttList["ResLotEIA"] * currentAttList["ResAllots"]
                        AimpstRes = currentAttList["ResFrontT"] - currentAttList["avSt_RES"]
                        block_EIA -= AimpRes - AimpstRes
                  if self.service_hdr == False:
                        block_EIA -= currentAttList["HDR_EIA"]
                  if self.service_com == False:
                        block_EIA -= currentAttList["COMAeEIA"]
                  if self.service_li == False:
                        block_EIA -= currentAttList["LIAeEIA"]
                  if self.service_hi == False:
                        block_EIA -= currentAttList["HIAeEIA"]

                  currentAttList["Manage_EIA"] = block_EIA  #Add the "Manage_EIA" Attribute

            ###-------------------------------------------------------------------###
            #---  SECTION A2 - HASH TABLE OF UPSTREAM/DOWNSTREAM                 ---#
            ###-------------------------------------------------------------------###
            #SET UP A HASH TABLE FOR QUICKLY FINDING THE UPSTREAM STRING
            for currentID in self.blockDict.keys():
                  self.blockIDlist.append(int(self.blockDict[currentID]["BlockID"]))
                  self.downIDlist.append(int(self.blockDict[currentID]["downID"]))
                  
            ###-------------------------------------------------------------------###
            #---  SECTION B - RETROFIT ALGORITHM
            ###-------------------------------------------------------------------###

            #totsystems = self.activesim.getAssetWithName("SysPrevGlobal").getAttribute("TotalSystems")
            totsystems = 0

            print "Total Systems in Map: "+str(totsystems)

            #sysIDs = self.activesim.getAssetsWithIdentifier("SysPrevID")
            sysIDs = []

            #Grab the list of systems and sort them based on location into a dictionary
            system_list = {}        #Dictionary
            for i in self.blockDict.keys():
                  system_list[i] = []
            for i in range(len(sysIDs)):
                  curSys = sysIDs[i]
                  locate = int(curSys["Location"])
                  system_list[locate].append(curSys)  #Block ID [5], [curSys, curSys, curSys]
            
            print system_list
            
            #Do the retrofitting
            for currentID in self.blockDict.keys():
                  currentAttList = self.blockDict[currentID]
                  if currentAttList["Status"] == 0:
                        continue

                  sys_implement = system_list[currentID]
                  if len(sys_implement) == 0:
                        currentAttList["ServWQ"] = 0        #These indicate the amount of service already provided
                        currentAttList["ServQTY"] = 0
                        currentAttList["ServREC"] = 0
                        currentAttList["ServUpQTY"] = 0
                        currentAttList["ServUpWQ"] = 0
                        currentAttList["ServUpREC"] = 0
                        continue

                  if self.retrofit_scenario == "N":
                        self.retrofit_DoNothing(currentID, sys_implement)
                  elif self.retrofit_scenario == "R":
                        self.retrofit_WithRenewal(currentID, sys_implement)
                  elif self.retrofit_scenario == "F":
                        self.retrofit_Forced(currentID, sys_implement)

            ###-------------------------------------------------------------------###
            #--- SECTION C - OPPORTUNITIES MAPPING OF INDIVIDUAL TECHS
            ###-------------------------------------------------------------------###

            inblock_options = {}
            subbas_options = {}

                  #---- C.1 - INITIALISE INCREMENT VARIABLES ------------------------
            print "Debug", str(self.lot_rigour)+" "+str(self.street_rigour)+" "+str(self.neigh_rigour)+" "+str(self.subbas_rigour)
            self.lot_incr = self.setupIncrementVector(self.lot_rigour)
            self.street_incr = self.setupIncrementVector(self.street_rigour)
            self.neigh_incr = self.setupIncrementVector(self.neigh_rigour)
            self.subbas_incr = self.setupIncrementVector(self.subbas_rigour)
            print "Debug", str(self.lot_incr)+" "+str(self.street_incr)+" "+str(self.neigh_incr)+" "+str(self.subbas_incr)


                  #---- C.2 - LOAD CLIMATE DATA IF HARVESTING -----------------------

            if bool(self.ration_harvest):   #if harvest is a management objective
                  #Initialize meteorological data vectors: Load rainfile and evaporation files,
                  #create the scaling factors for evap data
                  print "Loading Climate Data... "
                  self.raindata = ubseries.loadClimateFile(self.rainfile, "csv", self.rain_dt, 1440, self.rain_length)
                  self.evapdata = ubseries.loadClimateFile(self.evapfile, "csv", self.evap_dt, 1440, self.rain_length)
                  self.evapscale = ubseries.convertVectorToScalingFactors(self.evapdata)
                  self.raindata = ubseries.removeDateStampFromSeries(self.raindata)             #Remove the date stamps

                  #---- C.3 - BLOCK OPPORTUNITIES ASSESSMENT -------------------------

            for i in self.blockDict.keys():
                  currentID = i
                  print "Currently on Block "+str(currentID)
                  currentAttList = self.blockDict[i]
                  if currentAttList["Status"] == 0:
                        print "Block not active in simulation"
                        continue

                  #INITIALIZE VECTORS
                  lot_techRES = [0]
                  lot_techHDR = [0]
                  lot_techLI = [0]
                  lot_techHI = [0]
                  lot_techCOM = [0]
                  street_tech = [0]
                  neigh_tech = [0]
                  subbas_tech = [0]

                  
                        #---- C.3.1 -- Assess Lot Opportunities -----------------------------

                  if len(techListLot) != 0:
                        lot_techRES, lot_techHDR, lot_techLI, lot_techHI, lot_techCOM = self.assessLotOpportunities(techListLot, currentAttList)
                        #print lot_techRES
                        #print lot_techHDR
                        #print lot_techLI
                        #print lot_techHI 
                        #print lot_techCOM

                        #---- C.3.2 -- Assess Street Opportunities --------------------------

                  if len(techListStreet) != 0:
                        street_tech = self.assessStreetOpportunities(techListStreet, currentAttList)
                        #print street_tech

                        #---- C.3.3 -- Assess Neighbourhood Opportunities -------------------

                  if len(techListNeigh) != 0:
                        neigh_tech = self.assessNeighbourhoodOpportunities(techListNeigh, currentAttList)
                        #print neigh_tech

                        #---- C.3.4 -- Assess Sub-basin Opportunities -------------------

                  if len(techListSubbas) != 0:
                        subbas_tech = self.assessSubbasinOpportunities(techListSubbas, currentAttList)
                        #print subbas_tech

                        subbas_options["BlockID"+str(currentID)] = subbas_tech

                  #---- C.4 - CONSTRUCT IN-BLOCK OPTIONS ------------------------------------

                  inblock_options["BlockID"+str(currentID)] = self.constructInBlockOptions(currentAttList, lot_techRES, lot_techHDR, lot_techLI, lot_techHI, lot_techCOM, street_tech, neigh_tech)

            ###-------------------------------------------------------------------###
            #---  SECTION D - MONTE CARLO (ACROSS BASINS)                        ---#
            ###-------------------------------------------------------------------###
            gc.collect()

            for i in range(int(basins)):
                  currentBasinID = i+1
                  print "Currently on Basin ID"+str(currentBasinID)

                  basinBlockIDs, outletID = self.getBasinBlockIDs(currentBasinID)
                  print "basinBlockIDs "+str(basinBlockIDs)+" "+str(outletID)

                  dP_QTY, basinRemainQTY, basinTreatedQTY, basinEIA = self.calculateRemainingService("QTY", basinBlockIDs)
                  dP_WQ, basinRemainWQ, basinTreatedWQ, basinEIA = self.calculateRemainingService("WQ", basinBlockIDs)
                  dP_REC, basinRemainREC, basinTreatedREC, basinDem = self.calculateRemainingService("REC", basinBlockIDs)

                  print "Basin Totals: "+str([basinRemainQTY, basinRemainWQ, basinRemainREC])
                  print "Must choose a strategy now that treats: "+str([dP_QTY*100.0, dP_WQ*100.0, dP_REC*100.0])+"% of basin"

                  subbasPartakeIDs = self.findSubbasinPartakeIDs(basinBlockIDs, subbas_options) #Find locations of possible WSUD

                  updatedService = [dP_QTY, dP_WQ, dP_REC]

                  #SKIP CONDITIONS
                  if basinRemainQTY == 0.0 and basinRemainWQ == 0.0 and basinRemainREC == 0.0:
                        #print "Basin ID: ", currentBasinID, " has no remaining service requirements, skipping!"
                        continue
                  if sum(updatedService) == 0:
                        continue

                  iterations = self.maxMCiterations   #MONTE CARLO ITERATIONS - CAN SET TO SENSITIVITY VALUE IN FUTURE RELATIVE TO BASIN SIZE

                  if len(basinBlockIDs) == 1: #if we are dealing with a single-block basin, reduce the number of iterations
                        iterations = self.maxMCiterations/10        #If only one block in basin, do different/smaller number of iterations
                  
                  #Begin Monte Carlo
                  basin_strategies = []
                  for iteration in range(int(iterations)):   #1000 monte carlo simulations
                        print "Current Iteration No. "+str(iteration+1)
                        #Draw Samples
                        subbas_chosenIDs, inblocks_chosenIDs = self.selectTechLocationsByRandom(subbasPartakeIDs, basinBlockIDs)
                        #print "Selected Locations: Subbasins ", subbas_chosenIDs, " In Blocks ", inblocks_chosenIDs

                        #Create the Basin Management Strategy Object
                        current_bstrategy = tt.BasinManagementStrategy(iteration+1, currentBasinID,
                                 basinBlockIDs, subbasPartakeIDs,
                                 [basinRemainQTY, basinRemainWQ, basinRemainREC])

                        #Populate Basin Management Strategy Object based on the current sampled values
                        self.populateBasinWithTech(current_bstrategy, subbas_chosenIDs, inblocks_chosenIDs,
                        inblock_options, subbas_options, basinBlockIDs)

                        tt.updateBasinService(current_bstrategy)
                        #print current_bstrategy.getSubbasinArray()
                        #print (current_bstrategy.getInBlocksArray()

                        tt.calculateBasinStrategyMCAScores(current_bstrategy,self.curscalepref, self.priorities, self.mca_techlist, self.mca_tech, \
                        self.mca_env, self.mca_ecn, self.mca_soc, \
                        [self.bottomlines_tech_w, self.bottomlines_env_w, \
                                 self.bottomlines_ecn_w, self.bottomlines_soc_w], self.iao_influence/100.0)

                        #Add basin strategy to list of possibilities
                        service_objfunc = self.evaluateServiceObjectiveFunction(current_bstrategy, updatedService)        #Calculates how well it meets the total service

                        self.penalizeMCAscore(current_bstrategy, self.score_strat, updatedService)

                        basin_strategies.append([service_objfunc,current_bstrategy.getServicePvalues(), current_bstrategy.getTotalMCAscore(), current_bstrategy])

                  #Pick the final option by narrowing down the list and choosing (based on how many
                  #need to be chosen), sort and grab the top ranking options
                  basin_strategies.sort()
                  print basin_strategies
                  acceptable_options = []
                  for j in range(len(basin_strategies)):
                        if basin_strategies[j][0] < 0:  
                              continue    #if the OF is <0 i.e. -1, skip
                        else:
                              acceptable_options.append(basin_strategies[j])
                  print acceptable_options
                  
                  if self.ranktype == "RK":
                        acceptable_options = acceptable_options[0:int(self.topranklimit)]
                  elif self.ranktype == "CI":
                        acceptableN = int(len(acceptable_options)*(1.0-float(self.conf_int)/100.0))
                        acceptable_options = acceptable_options[0:acceptableN]

                  topcount = len(acceptable_options)
                  acceptable_options.sort(key=lambda score: score[2], reverse=True)
                  print acceptable_options

                  #Choose final option
                  numselect = min(topcount, self.num_output_strats)   #Determines how many options out of the matrix it should select
                  final_selection = []
                  if self.pickingmethod == "TOP":
                        checkvar = []
                        for j in range(int(numselect)):
                              checkvar.append(acceptable_options[j])
                              final_selection.append([acceptable_options[j][3],acceptable_options[j][2]]) #[strategy object, score]
                        print checkvar
                  elif self.pickingmethod == "RND":
                        for j in range(int(numselect)):
                              score_matrix = []       #Create the score matrix
                              for opt in acceptable_options:
                                    score_matrix.append(opt[2])
                              selection_cdf = self.createCDF(score_matrix)    #Creat the CDF
                              choice = self.samplefromCDF(selection_cdf)
                              final_selection.append([acceptable_options[choice][3],acceptable_options[j][2]])   #[strategy object , score]
                              acceptable_options.pop(choice)  #Pop the option at the selected index from the matrix
                              #Repeat for as many options as requested

                  #Write WSUD strategy attributes to output vector for that block
                  print final_selection
                  if len(final_selection) == 0:
                        self.transferExistingSystemsToOutput(1, 0)
                        #If there are no additional plans, just tranfer systems across, only one output as StrategyID1

                  for j in range(len(final_selection)):       #Otherwise it'll loop
                        cur_strat = final_selection[j]
                        stratID = j+1
                        self.writeStrategyView(stratID, currentBasinID, basinBlockIDs, cur_strat)
                        self.transferExistingSystemsToOutput(stratID, cur_strat[1])

                  #Clear the array and garbage collect
                  basin_strategies = []
                  acceptable_options = []
                  final_selection = []
                  gc.collect()
                  #END OF BASIN LOOP, continues to next basin

            #END OF MODULE


      ######################################
      #--- FUNCTIONS FOR PRE-PROCESSING ---#
      ######################################
      def compileUserTechList(self):
            """Compiles a dictionary of the technologies the user should use and at
            what scales these different technologies should be used. Results are 
            presented as a dictionary:
            userTechList = { "TechAbbreviation" : [boolean, boolean, boolean, boolean], }
                            each boolean corresponds to one of the four scales in the order
                            lot, street, neighbourhood, sub-basin
            """
            userTechList = {}
            for j in self.technames:
                  if eval("self."+j+"status == 1"):
                        userTechList[j] = [0,0,0,0]
                        for k in range(len(self.scaleabbr)):
                              k_scale = self.scaleabbr[k]
                              try:
                                    if eval("self."+str(j)+str(k_scale)+"==1"):
                                          userTechList[j][k] = 1
                              except NameError:
                                    pass
                              except AttributeError:
                                    pass
            return userTechList
    

      def fillScaleTechList(self, scale, userTechList):
            """Returns a vector of tech abbreviations for a given scale of application
            by scanning the userTechList dictionary. Used to fill out the relevant variables
            that will be called when assessing opportunities
            - Inputs: scale (the desired scale to work with, note that subbas and prec are interchangable)
            userTechList (the created dictionary output from self.compileUserTechList()
            """
            techlist = []
            if eval("self.strategy_"+scale+"_check == 1"):
                  if scale == "subbas":
                        scalelookup = "prec"
                  else:
                        scalelookup = scale
                  scaleindex = self.scaleabbr.index(scalelookup)
                  for key in userTechList.keys():
                        if userTechList[key][scaleindex] == 1:
                              techlist.append(key)
                        else:
                              pass
                  return techlist
            else:
                  return techlist

      ######################################
      #--- MCA-RELATED SUB-FUNCTIONS    ---#
      ######################################

      def retrieveMCAscoringmatrix(self):
            """Retrieves the Multi-Criteria Assessment Scoring Matrix from either the file
            or the default UrbanBEATS values. Returns the vector data containing all scores.
            """
            mca_scoringmatrix, mca_tech, mca_env, mca_ecn, mca_soc = [], [], [] ,[] ,[]
            if self.scoringmatrix_default:
                  mca_fname = ANCILLARY_PATH+"/mcadefault.csv"  #uses UBEATS default matrix           
            else:
                  mca_fname = self.scoringmatrix_path #loads file

            f = open(str(mca_fname), 'r')
            for lines in f:
                  readingline = lines.split(',')
                  readingline[len(readingline)-1] = readingline[len(readingline)-1].rstrip()
                  mca_scoringmatrix.append(readingline)
            f.close()
            total_metrics = len(mca_scoringmatrix[0])-1    #total number of metrics
            total_tech = len(mca_scoringmatrix)-1          #for total number of technologies

            #Grab index of technologies to relate to scores
            mca_techlist = []
            for i in range(len(mca_scoringmatrix)):
                  if i == 0:
                        continue        #Skip the header line
                  mca_techlist.append(mca_scoringmatrix[i][0])

            metrics = [self.bottomlines_tech_n, self.bottomlines_env_n, self.bottomlines_ecn_n, self.bottomlines_soc_n]
            if total_metrics != sum(metrics):
                  print "Warning, user-defined number of metrics does not match that of loaded file! Attempting to identify metrics!"
                  metrics, positions = self.identifyMCAmetriccount(mca_scoringmatrix[0])
            else:
                  print "User-defined number of metrics matches that of loaded file!"
                  metrics = [self.bottomlines_tech_n, self.bottomlines_env_n, self.bottomlines_ecn_n, self.bottomlines_soc_n, 0]
                  techpos, envpos, ecnpos, socpos = [], [], [], []
                  poscounter = 1
                  for i in range(int(self.bottomlines_tech_n)):
                        techpos.append(int(poscounter))
                        poscounter += 1
                  for i in range(int(self.bottomlines_env_n)):
                        envpos.append(int(poscounter))
                        poscounter += 1
                  for i in range(int(self.bottomlines_ecn_n)):
                        ecnpos.append(int(poscounter))
                        poscounter += 1
                  for i in range(int(self.bottomlines_soc_n)):
                        socpos.append(int(poscounter))
                        poscounter += 1
                  positions = [techpos, envpos, ecnpos, socpos, []]

            for lines in range(len(mca_scoringmatrix)):
                  if lines == 0:
                        continue
                  mca_tech.append(self.filloutMCAscorearray(mca_scoringmatrix[lines], metrics[0], positions[0]))
                  mca_env.append(self.filloutMCAscorearray(mca_scoringmatrix[lines], metrics[1], positions[1]))
                  mca_ecn.append(self.filloutMCAscorearray(mca_scoringmatrix[lines], metrics[2], positions[2]))
                  mca_soc.append(self.filloutMCAscorearray(mca_scoringmatrix[lines], metrics[3], positions[3]))

            for i in ["tech", "env", "ecn", "soc"]:                     #Runs the check if the criteria was selected
                  if eval("self.bottomlines_"+str(i)) == False:           #if not, creates a zero-length empty array
                        exec("mca_"+str(i)+" = []")

            mca_tech = self.rescaleMCAscorelists(mca_tech)
            mca_env = self.rescaleMCAscorelists(mca_env)
            mca_ecn = self.rescaleMCAscorelists(mca_ecn)
            mca_soc = self.rescaleMCAscorelists(mca_soc)
            return mca_techlist, mca_tech, mca_env, mca_ecn, mca_soc

      def penalizeMCAscore(self, bstrategy, method, services):
            """Penalty function that modifies the MCA score of the total basin strategy based on the required service
            level. There are three possible methods:
            (1) SNP - no penalty, nothing happens,
            (2) SLP - linear penalty function: revised score = current_score - (a*diff._service)*current_score
            (3) SPP - non-linear penalty as a power function: revised score = current_score - (a*diff._service^b)*current_score
            The coefficients a and b are set in UrbanBEATS' advanced options.
            """
            if method == "SNP":
                  return True

            bSvalues = bstrategy.getServicePvalues()
            dSQty = max(0, (bSvalues[0] - services[0])*int(self.penaltyQty))   #only applies to overtreatment
            dSWQ = max(0, (bSvalues[1] - services[1])*int(self.penaltyWQ))
            dSRec = max(0, (bSvalues[2] - services[2])*int(self.penaltyRec))

            if method == "SLP":
                  a = 1.0
                  bstrategy.setTotalMCAscore(max(0, bstrategy.getTotalMCAscore() - a* sum(dSQty, dSWQ, dSRec) * bstrategy.getTotalMCAscore()))
            elif method == "SPP":
                  a = self.penaltyFa
                  b = self.penaltyFb
                  bstrategy.setTotalMCAscore(max(0, bstrategy.getTotalMCAscore() - a* pow(sum(dSQty, dSWQ, dSRec),b)))
            return True


      def identifyMCAmetriccount(self, metriclist):
            """A function to read the MCA file and identify how many technical, environmental
            economics and social metrics have been entered into the list. Returns a vector of
            the suggested correct metric count based on the four different criteria. Note that
            identification of metrics can only be done if the user-defined file has entered
            the criteria titles correctly, i.e. acceptable strings include
            Technical Criteria: "Te#", "Tec#", "Tech#", "Technical#", "Technology#"
            or "Technological#"
            Environmental Criteria: "En#", "Env#", "Enviro#", Environ#", Environment#" or
            "Environmental#"
            Economics Criteria: "Ec#", "Ecn#", "Econ#", "Economic#", "Economics#" or
            "Economical#"
            Social Criteria: "So#", "Soc#", "Social#", "Society#", "Socio#", "Societal#" or
            "People#" or "Person#"
            These acceptable strings can either be 'first-letter capitalized', 'all uppsercase'
            or 'all lowercase' format.
            """
            tec, env, ecn, soc, unid = 0,0,0,0,0
            tecpos, envpos, ecnpos, socpos, unidpos = [], [], [], [], []

            #List of acceptable strings
            tecstrings = ["Te", "TE", "te", "Tec", "TEC", "tec", "Tech", "TECH", "tech",
                  "Technical", "TECHNICAL", "technical", "Technology", "TECHNOLOGY",
                  "technology", "Technological", "TECHNOLOGICAL", "technological"]
            envstrings = ["En", "EN", "en", "Env", "ENV", "env", "Enviro", "ENVIRO", "enviro",
                  "Environ", "ENVIRON", "environ", "Environment", "ENVIRONMENT",
                  "environment", "Environmental", "ENVIRONMENTAL", "environmental"]
            ecnstrings = ["Ec", "EC", "ec", "Ecn", "ECN", "ecn", "Econ", "ECON", "econ",
                  "Economic", "ECONOMIC", "economic", "Economics", "ECONOMICS", 
                  "economics", "Economical", "ECONOMICAL", "economical"]
            socstrings = ["So", "SO", "so", "Soc", "SOC", "soc", "Social", "SOCIAL", "social",
                  "Society", "SOCIETY", "society", "Socio", "SOCIO", "socio", "Societal",
                  "SOCIETAL", "societal", "People", "PEOPLE", "people", "Person",
                  "PERSON", "person"]

            for i in range(len(metriclist)):
                  if i == 0:
                        continue
                  if str(metriclist[i][0:len(metriclist[i])-1]) in tecstrings:
                        tec += 1
                        tecpos.append(i)
                  elif str(metriclist[i][0:len(metriclist[i])-1]) in envstrings:
                        env += 1
                        envpos.append(i)
                  elif str(metriclist[i][0:len(metriclist[i])-1]) in ecnstrings:
                        ecn += 1
                        ecnpos.append(i)
                  elif str(metriclist[i][0:len(metriclist[i])-1]) in socstrings:
                        soc += 1
                        socpos.append(i)
                  else:
                        unid += 1
                        unidpos.append(i)

            criteriametrics = [tec, env, ecn, soc, unid]
            criteriapos = [tecpos, envpos, ecnpos, socpos, unidpos]
            return criteriametrics, criteriapos


      def filloutMCAscorearray(self, line, techcount, techpos):
            """Extracts scores for a particular criteria from a line in the loaded scoring matrix
            and transfers them to the respective array, also converts the value to a float"""
            line_index = []
            for i in range(int(techcount)):
                  line_index.append(float(line[techpos[i]]))
            return line_index


      def rescaleMCAscorelists(self, list):
            """Rescales the MCA scores based on the number of metrics in each criteria. This gives
            each criteria an equal weighting to start with and can then influence the evaluation
            later on with user-defined final criteria weights.
            """
            for i in range(len(list)):
                  for j in range(len(list[i])):
                        list[i][j] = list[i][j]/len(list[i])
            return list


      ################################
      #--- RETROFIT SUB-FUNCTIONS ---#
      ################################

      def retrofit_DoNothing(self, ID, sys_implement):
            """Implements the "DO NOTHING" Retrofit Scenario across the entire map Do Nothing:
            Technologies already in place will be left as is
            - The impervious area they already treat will be removed from the outstanding impervious 
            area to be treated
            - The Block will be marked at the corresponding scale as "occupied" so that techopp 
            functions cannot place anything there ('no space case')
            """
            print "Block: "+str(ID)
            print sys_implement     #[curSys, curSys, curSys, ...]

            #currentAttList = self.getBlockUUID(ID,city)
            currentAttList = self.blockDict[ID]
            inblock_imp_treated = 0 #Initialize to keep track of treated in-block imperviousness

            #LOT, STREET, NEIGH Systems
            for luc_code in ["L_RES", "L_HDR", "L_LI", "L_HI", "L_COM", "S", "N"]:
                  sys_descr = self.locatePlannedSystems(sys_implement, luc_code)
                  if sys_descr == None:       #None found for that particular land use
                        inblock_imp_treated += 0
                        currentAttList["Has"+str(luc_code)+"Sys"] = 0
                  else:
                        currentAttList["Has"+str(luc_code)+"Sys"] = 1  #mark the system as having been taken
                        print luc_code+" Location: "+str(sys_descr["Location"])
                        Aimplot = currentAttList["ResLotEIA"]
                        if luc_code == "L_RES":
                              imptreated = min(self.retrieveNewAimpTreated(ID, luc_code, sys_descr), Aimplot)
                        else:
                              imptreated = self.retrieveNewAimpTreated(ID, luc_code, sys_descr)
                        inblock_imp_treated += imptreated * sys_descr["GoalQty"]
                        sys_descr["ImpT"] = imptreated   #UNIT IMPERVIOUSNESS TREATED
                        sys_descr["CurImpT"] = imptreated * sys_descr["Qty"]
                        #Do Nothing Scenario: ImpT changes and CurImpT changes, but Status remains 1

            print "DEBUG: Assignign VAriables"
            currentAttList["ServWQ"] = inblock_imp_treated
            currentAttList["ServQTY"] = 0
            currentAttList["ServREC"] = 0

            inblock_impdeficit = max(currentAttList["Manage_EIA"] - inblock_imp_treated, 0)
            currentAttList["DeficitWQ"] = inblock_impdeficit
            print "Deficit Area still to treat inblock: "+str(inblock_impdeficit)

            #Calculate the maximum degree of lot implementation allowed (no. of houses)
            allotments = currentAttList["ResAllots"]
            Aimplot = currentAttList["ResLotEIA"]
            print "Allotments = "+str(allotments)+" of each "+str(Aimplot)+" sqm impervious"
            max_houses = min((inblock_impdeficit/Aimplot)/allotments, 1)
            print "A Lot Strategy in this Block would permit a maximum implementation in: "+str(max_houses*100)+"% of houses"
            currentAttList["MaxLotDeg"] = max_houses

            #PRECINCT SYSTEMS
            sys_descr = self.locatePlannedSystems(sys_implement, "B")
            if sys_descr == None:
                  print "no Systems"
                  currentAttList["HasBSys"] = 0
                  currentAttList["ServUpWQ"] = 0
                  currentAttList["ServUpQTY"] = 0
                  currentAttList["ServUpREC"] = 0
            else:
                  currentAttList["HasBSys"] = 1
                  subbasimptreated = self.retrieveNewAimpTreated(ID, "B", sys_descr)
                  print "Subbasin Location: "+str(sys_descr["Location"])
                  currentAttList["ServUpWQ"] = subbasimptreated
                  sys_descr["ImpT"] = subbasimptreated
                  sys_descr["CurImpT"] = subbasimptreated * sys_descr["Qty"]
            return True
          
    
      def retrofit_Forced(self, ID, sys_implement):
            """Implements the "FORCED" Retrofit Scenario across the entire map
            Forced: Technologies at the checked scales are retrofitted depending on the three
            options available: keep, upgrade, decommission
            - See comments under "With Renewal" scenario for further details
            """
            print "Block: "+str(ID)
            print sys_implement

            #currentAttList = self.getBlockUUID(ID,city)
            currentAttList = self.blockDict[ID]
            inblock_imp_treated = 0 #Initialize to keep track of treated in-block imperviousness

            #LOT, STREET & NEIGH
            for luc_code in ["L_RES", "L_HDR", "L_LI", "L_HI", "L_COM", "S", "N"]:
                  sys_descr = self.locatePlannedSystems(sys_implement, luc_code)

                  if sys_descr == None: #Skip condition, no system at the particular scale/luc-code
                        inblock_imp_treated += 0
                        currentAttList["Has"+str(luc_code)+"Sys"] = 0
                        continue

                  oldImp = sys_descr["ImpT"]
                  decision, newImpT = self.dealWithSystem(currentAttList, sys_descr, luc_code,)

                  #CONDITIONS THAT WILL FORCE A DECISION == 1
                  if luc_code in ["L_RES", "L_HDR", "L_LI", "L_HI", "L_COM"]:
                        decision = 1 #YOU CANNOT FORCE RETROFIT ON LOT, SO KEEP THE SYSTEMS
                  if luc_code == "S" and self.force_street == 0: #if we do not force retrofit on neighbourhood, just keep the system
                        decision = 1
                  if luc_code == "N" and self.force_neigh == 0: #if we do not force retrofit on neighbourhood, just keep the system
                        decision = 1

                  if decision == 1:   #KEEP SYSTEM
                        currentAttList["Has"+str(luc_code)+"Sys"] = 1
                        Aimplot = currentAttList["ResLotEIA"]
                        if luc_code == "L_RES":
                              imptreated = min(newImpT, Aimplot)
                        else:
                              imptreated = newImpT
                        inblock_imp_treated += imptreated
                        sys_descr["ImpT"] = imptreated
                        sys_descr["CurImpT"] = imptreated * sys_descr["Qty"]

                  elif decision == 2: #RENEWAL
                        print "Renewing the System - Redesigning and Assessing Space Requirements"
                        newAsys, newEAFact = self.redesignSystem(currentAttList, sys_descr, luc_code, oldImp) #get new system size & EA

                        #Get available space - depends on scale/luc-code
                        if luc_code == "S":
                              avlSpace = currentAttList["avSt_RES"]
                        elif luc_code == "N":
                              if sys_descr["Type"] in ["BF", "WSUR", "PB","RT", "SW", "IS"]: #CHECK WHAT SVU Land use area is available
                                    svu_space = currentAttList["SVU_avSW"] + currentAttList["SVU_avWS"]
                              elif sys_descr["Type"] in ["GT"]:
                                    svu_space = currentAttList["SVU_avWW"]
                              else:
                                    svu_space = 0
                              avlSpace = currentAttList["PG_av"] + currentAttList["REF_av"] + svu_space

                        if newAsys > avlSpace and self.renewal_alternative == "K": #if system does not fit and alternative is 'Keep'
                              print "Cannot fit new system design, keeping old design instead"
                              currentAttList["Has"+str(luc_code)+"Sys"] = 1
                              inblock_imp_treated += newImpT
                              sys_descr["ImpT"] = newImpT
                              sys_descr["CurImpT"] = newImpT * sys_descr["Qty"]
                        elif newAsys > avlSpace and self.renewal_alternative == "D": #if system does not fit and alternative is 'Decommission'
                              print "Cannot fit new system design, decommissioning instead"
                              inblock_imp_treated += 0 #quite self-explanatory but is added here for clarity
                              currentAttList["Has"+str(luc_code)+"Sys"] = 1
                              sys_implement.remove(sys_descr)
                              #>>>>>>>>>>>>>>>>>>self.activesim.removeAssetByName("SysPrevID"+str(sys_descr["SysID"]))
                        else: #otherwise it'll fit, transfer new information
                              print "New System Upgrades fit, transferring this information to output"
                              currentAttList["Has"+str(luc_code)+"Sys"] = 1
                              self.defineUpgradedSystemAttributes(sys_descr, newAsys, newEAFact, oldImp)
                              inblock_imp_treated += oldImp

                  elif decision == 3: #DECOMMISSIONING
                        print "Decommissioning the system"
                        inblock_imp_treated += 0 #quite self-explanatory but is added here for clarity
                        #remove all attributes, wipe the attributes entry in techconfigout with a blank attribute object
                        currentAttList["Has"+str(luc_code)+"Sys"] = 0 #Remove system placeholder
                        sys_implement.remove(sys_descr)
                        #city.removeComponent(sys_descr.getUUID())
                        self.activesim.removeAssetByName("SysPrevID"+str(sys_descr.getAttribute("SysID")))

            currentAttList["ServWQ"] = inblock_imp_treated
            currentAttList["ServQTY"] = 0
            currentAttList["ServREC"] = 0

            inblock_impdeficit = max(currentAttList["Manage_EIA"] - inblock_imp_treated, 0)
            currentAttList["DeficitIA"] = inblock_impdeficit

            allotments = currentAttList["ResAllots"]
            Aimplot = currentAttList["ResLotEIA"]
            print "Allotments = "+str(allotments)+" of each "+str(Aimplot)+" sqm impervious"
            max_houses = min((inblock_impdeficit/Aimplot)/allotments, 1)
            print "A Lot Strategy in this Block would permit a maximum implementation in: "+str(max_houses*100)+"% of houses"
            currentAttList["MaxLotDeg"] = max_houses

            #SUBBASIN
            sys_descr = self.locatePlannedSystems(sys_implement, "B")
            if sys_descr == None:
                  currentAttList["HasBSys"] = 0
            else:
                  oldImp = sys_descr["ImpT"]
                  decision, newImpT = self.dealWithSystem(currentAttList, sys_descr, "B")
                  if self.force_prec == 0: #if we do not force retrofit on precinct, just keep the system
                        decision = 1

                  if decision == 1: #KEEP
                        print "Keeping the System"
                        currentAttList["HasBSys"] = 1
                        currentAttList["ServUpWQ"] = newImpT
                        sys_descr["ImpT"] = newImpT
                        sys_descr["CurImpT"] = newImpT * sys_descr["Qty"]

                  elif decision == 2: #RENEWAL
                        print "Renewing the System - Redesigning and Assessing Space Requirements"
                        newAsys, newEAFact = self.redesignSystem(currentAttList, sys_descr, "B", oldImp) #get new system size & EA
                        if sys_descr["Type"] in ["BF", "WSUR", "PB","RT", "SW", "IS"]: #CHECK WHAT SVU Land use area is available
                              svu_space = currentAttList["SVU_avSW"] + currentAttList["SVU_avWS"]
                        elif sys_descr["Type"] in ["GT"]:
                              svu_space = currentAttList["SVU_avWW"]
                        else:
                              svu_space = 0
                        avlSpace = currentAttList["PG_av"] + currentAttList["REF_av"] + svu_space
                        if newAsys > avlSpace and self.renewal_alternative == "K": #if system does not fit and alternative is 'Keep'
                              print "Cannot fit new system design, keeping old design instead"
                              currentAttList["HasBSys"] = 1
                              currentAttList["ServUpWQ"] = newImpT
                              sys_descr["ImpT"] = newImpT
                              sys_descr["CurImpT"] = newImpT * sys_descr["Qty"]
                        elif newAsys > avlSpace and self.renewal_alternative == "D": #if system does not fit and alternative is 'Decommission'
                              print "Cannot fit new system design, decommissioning instead"
                              currentAttList["ServUpWQ"] = 0
                              currentAttList["HasBSys"] = 0       #Remove system placeholder
                              sys_implement.remove(sys_descr)
                              #city.removeComponent(sys_descr.getUUID())
                              self.activesim.removeAssetByName("SysPrevID"+str(sys_descr["SysID"]))
                        else: #otherwise it'll fit, transfer new information
                              print "New System Upgrades fit, transferring this information to output"
                              currentAttList["HasBSys"] = 1
                              self.defineUpgradedSystemAttributes(sys_descr, newAsys, newEAFact, oldImp)
                              currentAttList["ServUpWQ"] = oldImp        #OLD IMP BECAUSE THE REDESIGNED SYSTEM IS NOW LARGER
                                                                                    #AND BETTER TO HANDLE SAME IMP AREA AS BEFORE!
                  elif decision == 3: #DECOMMISSIONING
                        print "Decommissioning the system"
                        currentAttList["ServUpWQ"] = 0
                        #remove all attributes, wipe the attributes entry in techconfigout with a blank attribute object
                        currentAttList["HasSubbasS"] = 0
                        sys_implement.remove(sys_descr)
                        #city.removeComponent(sys_descr.getUUID())
                        #>>>>self.activesim.removeAssetByName("SysPrevID"+str(sys_descr["SysID"]))
            return True


      def retrofit_WithRenewal(self, ID, sys_implement):
            """Implements the "WITH RENEWAL" Retrofit Scenario across the entire map
            With Renewal: Technologies at different scales are selected for retrofitting
            depending on the block's age and renewal cycles configured by the user
            - Technologies are first considered for keeping, upgrading or decommissioning
            - Keep: impervious area they already treat will be removed from the outstanding
            impervious area to be treated and that scale in said Block marked as 'taken'
            - Upgrade: technology targets will be looked at and compared, the upgraded technology
            is assessed and then implemented. Same procedures as for Keep are subsequently
            carried out with the new design
            - Decommission: technology is removed from the area, impervious area is freed up
            scale in said block is marked as 'available'"""

            time_passed = self.currentyear - self.prevyear

            print "Block: "+str(ID)
            print sys_implement

            #currentAttList = self.getBlockUUID(ID,city)
            currentAttList = self.activesim.getAssetWithName("BlockID"+str(ID))
            inblock_imp_treated = 0

            if self.renewal_cycle_def == 0:
                  self.retrofit_DoNothing(ID, sys_implement) #if no renewal cycle was defined
                  return True #go through the Do Nothing Loop instead

            #LOT, STREET, NEIGH
            for luc_code in ["L_RES", "L_HDR", "L_LI", "L_HI", "L_COM", "S", "N"]:
                  sys_descr = self.locatePlannedSystems(sys_implement, luc_code)
                  if sys_descr == None:
                        inblock_imp_treated += 0
                        currentAttList["Has"+str(luc_code)+"Sys"] = 0
                        continue

                  #Get Renewal Cycle Variable
                  if luc_code in ["L_RES", "L_HDR", "L_LI", "L_HI", "L_COM"]:
                        renewalyears = self.renewal_lot_years
                  elif luc_code == "S":
                        renewalyears = self.renewal_street_years
                  elif luc_code == "N":
                        renewalyears = self.renewal_neigh_years

                  #DO SOMETHING TO DETERMINE IF YES/NO RETROFIT, then check the decision
                  if time_passed - (time_passed // renewalyears)*renewalyears == 0:
                        go_retrofit = 1 #then it's time for renewal
                        print "Before: "+str(sys_descr["GoalQty"])
                        #modify the current sys_descr attribute to take into account lot systems that have disappeared.
                        #If systems have disappeared the final quantity of lot implementation (i.e. goalqty) will drop
                        if luc_code == "L_RES":
                              sys_descr = self.updateForBuildingStockRenewal(currentAttList, sys_descr)
                        print "After: "+str(sys_descr["GoalQty"])
                  else:
                        go_retrofit = 0

                  #NOW DETERMINE IF ARE RETROFITTING OR NOT: IF NOT READY FOR RETROFIT, KEEP, ELSE GO INTO CYCLE
                  oldImp = sys_descr["ImpT"] #Old ImpT using the old GoalQty value
                  decision, newImpT = self.dealWithSystem(currentAttList, sys_descr, luc_code) #gets the new ImpT using new GoalQty value (if it changed)
                  if go_retrofit == 0:        #If the decision is to NOT retrofit yet, then KEEP the system
                        decision = 1

                  if decision == 1: #KEEP
                        print "Keeping the System"
                        currentAttList["Has"+str(luc_code)+"Sys"] = 1
                        Aimplot = currentAttList["ResLotEIA"]
                        if luc_code == "L_RES":
                              imptreated = min(newImpT, Aimplot)
                        else:
                              imptreated = newImpT
                        inblock_imp_treated += imptreated
                        sys_descr["ImpT"] = imptreated
                        sys_descr["CurImpT"] = imptreated * sys_descr["Qty"]

                  elif decision == 2: #RENEWAL
                        if luc_code in ["L_RES", "L_HDR", "L_COM", "L_LI", "L_HI"]:
                              print "Lot-scale systems will not allow renewal, instead the systems will be kept as is until plan is abandoned"
                              currentAttList["Has"+str(luc_code)+"Sys"] = 1
                              Aimplot = currentAttList["ResLotEIA"]
                              if luc_code == "L_RES":
                                    imptreated = min(newImpT, Aimplot)
                              else:
                                    imptreated = newImpT
                              inblock_imp_treated += imptreated
                              sys_descr["ImpT"] = imptreated
                              sys_descr["CurImpT"] = imptreated * sys_descr["Qty"]
                              #FUTURE DYNAMICS TO BE INTRODUCED
                        else:
                              print "Renewing the System - Redesigning and Assessing Space Requirements"
                              newAsys, newEAFact = self.redesignSystem(currentAttList, sys_descr, luc_code, oldImp) #get new system size & EA

                              #Get available space - depends on scale/luc-code
                              if luc_code == "S":
                                    avlSpace = currentAttList["avSt_RES"]
                              elif luc_code == "N":
                                    if sys_descr["Type"] in ["BF", "WSUR", "PB","RT", "SW", "IS"]: #CHECK WHAT SVU Land use area is available
                                          svu_space = currentAttList["SVU_avSW"] + currentAttList["SVU_avWS"]
                                    elif sys_descr["Type"] in ["GT"]:
                                          svu_space = currentAttList["SVU_avWW"]
                                    else:
                                          svu_space = 0
                                    avlSpace = currentAttList["PG_av"] + currentAttList["REF_av"] + svu_space

                              if newAsys > avlSpace and self.renewal_alternative == "K": #if system does not fit and alternative is 'Keep'
                                    print "Cannot fit new system design, keeping old design instead"
                                    currentAttList["Has"+str(luc_code)+"Sys"] = 1
                                    inblock_imp_treated += newImpT
                                    sys_descr["ImpT"] = newImpT
                                    sys_descr["CurImpT"] = newImpT * sys_descr["Qty"]
                              elif newAsys > avlSpace and self.renewal_alternative == "D": #if system does not fit and alternative is 'Decommission'
                                    print "Cannot fit new system design, decommissioning instead"
                                    inblock_imp_treated += 0 #quite self-explanatory but is added here for clarity
                                    currentAttList["Has"+str(luc_code)+"Sys"] = 1
                                    sys_implement.remove(sys_descr)
                                    #city.removeComponent(sys_descr.getUUID())
                                    self.activesim.removeAssetByName("SysPrevID"+str(sys_descr["SysID"]))
                              else: #otherwise it'll fit, transfer new information
                                    print "New System Upgrades fit, transferring this information to output"
                                    currentAttList["Has"+str(luc_code)+"Sys"] = 1
                                    self.defineUpgradedSystemAttributes(sys_descr, newAsys, newEAFact, oldImp)
                                    inblock_imp_treated += oldImp

                  elif decision == 3: #DECOMMISSIONING
                        print "Decommissioning the system"
                        inblock_imp_treated += 0 #quite self-explanatory but is added here for clarity
                        #remove all attributes, wipe the attributes entry in techconfigout with a blank attribute object
                        currentAttList["Has"+str(luc_code)+"Sys"] = 0 #Remove system placeholder
                        sys_implement.remove(sys_descr)
                        #city.removeComponent(sys_descr.getUUID())
                        self.activesim.removeAssetByName("SysPrevID"+str(sys_descr["SysID"]))

            currentAttList["ServWQ"] = inblock_imp_treated
            currentAttList["ServQTY"] = 0
            currentAttList["ServREC"] = 0

            inblock_impdeficit = max(currentAttList["Manage_EIA"] - inblock_imp_treated, 0)
            currentAttList["DeficitIA"] = inblock_impdeficit

            allotments = currentAttList["ResAllots"]
            Aimplot = currentAttList["ResLotEIA"]
            print "Allotments = "+str(allotments)+" of each "+str(Aimplot)+" sqm impervious"
            if allotments == 0:
                  max_houses = 0
            else:
                  max_houses = min((inblock_impdeficit/Aimplot)/allotments, 1)
            print "A Lot Strategy in this Block would permit a maximum implementation in: "+str(max_houses*100)+"% of houses"
            currentAttList["MaxLotDeg"] = max_houses

            #SUBBASIN
            sys_descr = self.locatePlannedSystems(sys_implement, "B")
            if sys_descr == None:
                  currentAttList["HasBSys"] = 0
            else:
                  #DO SOMETHING TO DETERMINE IF YES/NO RETROFIT, then check the decision
                  if time_passed - (time_passed // self.renewal_neigh_years)*self.renewal_neigh_years == 0:
                        go_retrofit = 1 #then it's time for renewal
                  else:
                        go_retrofit = 0 #otherwise do not do anything

                  #NOW DETERMINE IF ARE RETROFITTING OR NOT: IF NOT READY FOR RETROFIT, KEEP, ELSE GO INTO CYCLE
                  oldImp = sys_descr["ImpT"]
                  decision, newImpT = self.dealWithSystem(currentAttList, sys_descr, "B")
                  if go_retrofit == 0:
                        decision = 1

                  if decision == 1: #keep
                        print "Keeping the System"
                        currentAttList["HasBSys"] = 1
                        currentAttList["ServUpWQ"] = newImpT
                        sys_descr["ImpT"] = newImpT
                        sys_descr["CurImpT"] = newImpT * sys_descr["Qty"]

                  elif decision == 2: #renewal
                        print "Renewing the System - Redesigning and Assessing Space Requirements"
                        newAsys, newEAFact = self.redesignSystem(currentAttList, sys_descr, "B", oldImp) #get new system size & EA
                        if sys_descr["Type"] in ["BF", "WSUR", "PB","RT", "SW", "IS"]: #CHECK WHAT SVU Land use area is available
                              svu_space = currentAttList["SVU_avSW"] + currentAttList["SVU_avWS"]
                        elif sys_descr["Type"] in ["GT"]:
                              svu_space = currentAttList["SVU_avWW"]
                        else:
                              svu_space = 0
                        
                        avlSpace = currentAttList["PG_av"] + currentAttList["REF_av"] + svu_space
                        if newAsys > avlSpace and self.renewal_alternative == "K": #if system does not fit and alternative is 'Keep'
                              print "Cannot fit new system design, keeping old design instead"
                              currentAttList["HasBSys"] = 1
                              currentAttList["ServUpWQ"] = newImpT
                              sys_descr["ImpT"] = newImpT
                              sys_descr["CurImpT"] = newImpT * sys_descr["Qty"]
                        elif newAsys > avlSpace and self.renewal_alternative == "D": #if system does not fit and alternative is 'Decommission'
                              print "Cannot fit new system design, decommissioning instead"
                              currentAttList["ServUpWQ"] = 0
                              currentAttList["HasBSys"] = 0 #Remove system placeholder
                              sys_implement.remove(sys_descr)
                              #city.removeComponent(sys_descr.getUUID())
                              #>>>> self.activesim.removeAssetByName("SysPrevID"+str(sys_descr["SysID"]))
                        else: #otherwise it'll fit, transfer new information
                              print "New System Upgrades fit, transferring this information to output"
                              currentAttList["HasBSys"] = 1
                              self.defineUpgradedSystemAttributes(sys_descr, newAsys, newEAFact, oldImp)
                              currentAttList["ServUpWQ"] = oldImp        #OLD IMP BECAUSE THE REDESIGNED SYSTEM IS NOW LARGER
                                            #AND BETTER TO HANDLE SAME IMP AREA AS BEFORE!
                  elif decision == 3: #DECOMMISSIONING
                        print "Decommissioning the system"
                        currentAttList["ServUpWQ"] = 0
                        #remove all attributes, wipe the attributes entry in techconfigout with a blank attribute object
                        currentAttList["HasSubbasS"] = 0
                        sys_implement.remove(sys_descr)
                        #city.removeComponent(sys_descr.getUUID())
                        #>>>> self.activesim.removeAssetByName("SysPrevID"+str(sys_descr["SysID"]))
            return True


      def locatePlannedSystems(self, system_list, scale):
            """Searches the input planned technologies list for a system that fits the scale in the block
            Returns the system attribute list. System_list is a vector of Components [curSys, curSys, curSys]
            """
            for curSys in system_list:
                  if curSys["Scale"] == scale:
                        return curSys
            return None


      def retrieveNewAimpTreated(self, ID, scale, sys_descr):
            """Retrieves the system information for the given scale from the city datastream and
            assesses how well the current system's design can meet the current targets by comparing its
            performance on the design curves.
            """
            #Determine impervious area to deal with depending on scale
            currentAttList = self.blockDict[ID]
            ksat = currentAttList["Soil_k"]
            sysexfil = sys_descr["Exfil"]
            Asyseff = sys_descr["SysArea"]/sys_descr["EAFact"]
            wtype = sys_descr["Type"]
            #need to be using the effective area, not the planning area

            #print "Type: "+str(type)+" AsysEffective: "+str(Asyseff)+"ksat: "+str(ksat)

            ### EXCEPTION FOR SWALES AT THE MOMENT WHILE THERE ARE NO DESIGN CURVE FILES ###
            if wtype == "SW":
                  return 0
            ### END OF EXCEPTION - CHANGE WHEN DESIGN CURVES ARE AVAILABLE ###

            #Grab targets and adjust for particular system type
            #print "Targets: "+str(self.targetsvector)

            #Piece together the pathname from current system information: FUTURE
            #NOTE: CURRENT TECH DESIGNS WILL NOT BE CHANGED! THEREFORE PATHNAME WE RETRIEVE FROM
            #DESIGN DETAILS VECTOR LIST

            #Depending on the type of system and classification, will need to retrieve design in different
            #ways
            if wtype in ["BF", "SW", "WSUR", "PB", "IS"]:    #DESIGN by DCV Systems
                  sys_perc = dcv.retrieveDesign(self.getDCVPath(wtype), wtype, min(ksat, sysexfil), self.targetsvector)
            #print "Sys Percentage: "+str(sys_perc)
            elif wtype in ["RT", "PP", "ASHP", "GW"]:        #DESIGN by EQN or SIM Systems
                  #Other system types
                  sys_perc = np.inf #deq.retrieveDesign(...)

            if sys_perc == np.inf:
                  #Results - new targets cannot be met, system will not be considered
                  #release the imp area, but mark the space as taken!
                  imptreatedbysystem = 0
            else:
                  #Calculate the system's current Atreated
                  imptreatedbysystem = Asyseff/sys_perc

            #            #Account for Lot Scale as exception
            #            if scale in ["L_RES", "L_HDR", "L_LI", "L_HI", "L_COM"]:
            #                imptreatedbysystem *= goalqty #imp treated by ONE lot system * the desired qty that can be implemented
            #            else:
            #                imptreated += imptreatedbysystem
            #print "impervious area treated by system: "+str(imptreatedbysystem)
            return imptreatedbysystem


      def findDCVpath(self, wtype, sys_descr):
            #Finds the correct pathname of the design curve file based on system type and specs
            if wtype in ["IS", "BF"]: #then file = BF-EDDx.xm-FDx.xm.dcv
                  pathname = 0
            elif wtype in ["WSUR"]: #then file = WSUR-EDDx.xm.dcv
                  pathname = 0
            elif wtype in ["PB"]: #then file = PB-MDx.xm.dcv
                  pathname = 0
            return pathname


      def dealWithSystem(self, currentAttList, sys_descr, scale):
            """Checks the system's feasibility on a number of categories and sets up a decision matrix
            to determine what should be done with the system (i.e. keep, upgrade, decommission). Returns
            a final decision and the newly treated impervious area.
            """

            currentID = int(currentAttList["BlockID"])
            scalecheck = [[self.lot_renew, self.lot_decom], 
                        [self.street_renew, self.street_decom], 
                        [self.neigh_renew, self.neigh_decom], 
                        [self.prec_renew, self.prec_decom]]

            if scale in ["L_RES", "L_HDR", "L_LI", "L_HI", "L_COM"]:
                  scaleconditions = scalecheck[0]
            else:
                  scalematrix = ["L", "S", "N", "B"]
                  scaleconditions = scalecheck[scalematrix.index(scale)]

            decision_matrix = [] #contains numbers of each decision 1=Keep, 2=Renew, 3=Decom
            #1st pass: decision based on the maximum i.e. if [1, 3], decommission

            ###-------------------------------------------------------
            ### DECISION FACTOR 1: SYSTEM AGE
            ### Determine where the system age lies
            ###-------------------------------------------------------
            sys_yearbuilt = sys_descr["Year"]
            sys_type = sys_descr["Type"]
            avglife = eval("self."+str(sys_type)+"avglife")
            age = self.currentyear - sys_yearbuilt
            #print "System Age: "+str(age)

            if scaleconditions[1] == 1 and age > avglife: #decom
                  #print "System too old, decommission"
                  decision_matrix.append(3)
            elif scaleconditions[0] == 1 and age > avglife/float(2.0): #renew
                  #print "System needs renewal because of age"
                  decision_matrix.append(2)
            else: #keep
                  decision_matrix.append(1)

            ###-------------------------------------------------------
            ### DECISION FACTOR 2: DROP IN PERFORMANCE
            ### Determine where the system performance lies
            ###-------------------------------------------------------
            old_imp = sys_descr["ImpT"]
            if old_imp == 0: #This can happen if for example it was found previously that
                  perfdeficit = 1.0 #the system can no longer meet new targets, but is not retrofitted because of renewal cycles.
                  new_imp = 0
            else:           #Need to catch this happening or else there will be a float division error!
                  new_imp = self.retrieveNewAimpTreated(currentID, scale, sys_descr)
                  perfdeficit = (old_imp - new_imp)/old_imp

            #print "Old Imp: "+str(old_imp)
            #print "New Imp: "+str(new_imp)
            #print "Performance Deficit of System: "+str(perfdeficit)

            if scaleconditions[1] == 1 and perfdeficit >= (float(self.decom_thresh)/100.0): #Decom = Checked, threshold exceeded
                  #print "System's performance not up to scratch, decommission"
                  decision_matrix.append(3)
            elif scaleconditions[0] == 1 and perfdeficit >= (float(self.renewal_thresh)/100.0): #Renew = checked, threshold exceeded
                  #print "System's performance ok, needs renewal"
                  decision_matrix.append(2)
            else:
                  decision_matrix.append(1)

            ### MAKE FINAL DECISION ###
            #print decision_matrix
            final_decision = max(decision_matrix)           #worst-case chosen, i.e. maximum
            
            return final_decision, new_imp


      def redesignSystem(self, currentAttList, sys_descr, scale, originalAimpTreated):
            """Redesigns the system for BlockID at the given 'scale' for the original Impervious
            Area that it was supposed to treat, but now according to new targets.
            - ID: BlockID, i.e. the system's location
            - sys_descr: the original vector of the system
            - scale: the letter denoting system scale
            - originalAimpTreated: the old impervious area the system was meant to treat
            """
            wtype = sys_descr["Type"]

            #TO BE CHANGED LATER ON, BUT FOR NOW WE ASSUME THIS IS THE SAME PATH
            dcvpath = self.getDCVPath(wtype)
            #GET THE DCV FILENAME
            #dcvpath = self.findDCVpath(type, sys_descr)

            #Some additional arguments for the design function
            maxsize = eval("self."+str(wtype)+"maxsize")                     #FUTURE >>>>>> MULTI-oBJECTIVE DESIGN
            minsize = eval("self."+str(wtype)+"minsize")
            soilK = currentAttList["Soil_k"]
            systemK = sys_descr["Exfil"]

            #Current targets
            targets = self.targetsvector
            tech_applications = self.getTechnologyApplications(wtype)
            purpose = [0, tech_applications[1], 0]

            #Call the design function using eval, due to different system Types
            newdesign = eval('td.design_'+str(wtype)+'('+str(originalAimpTreated)+',"'+str(dcvpath)+'",'+str(self.targetsvector)+','+str(purpose)+','+str(soilK)+','+str(systemK)+','+str(minsize)+','+str(maxsize)+')')    

            Anewsystem = newdesign[0]
            newEAFactor = newdesign[1]

            return Anewsystem, newEAFactor


      def defineUpgradedSystemAttributes(self, sys_descr, newAsys, newEAFact, impT):
            """Updates the current component with new attributes based on the newly designed/upgraded
            system at a particular location.
            """
            sys_descr["SysArea"] = newAsys
            sys_descr["EAFact"] = newEAFact
            sys_descr["ImpT"] = impT
            sys_descr["CurImpT"] = impT*sys_descr["GoalQty"]

            #System was upgraded, add one to the upgrade count
            sys_descr["Upgrades"] = sys_descr["Upgrades"] + 1
            return True


      def updateForBuildingStockRenewal(self, currentAttList, sys_descr):
            """Number of houses removed from area = total currently there * lot_perc
            evenly distribute this across those that have lot system and those that don't
            we therefore end up calculate how many systems lost as lot-perc * how many in place
            """
            print "YEARS"
            print str(self.currentyear)+" "+str(self.prevyear)+" "+str(self.renewal_lot_years)
            cycles = (float(self.currentyear) - float(self.prevyear)) // float(self.renewal_lot_years)
            print "Cycles"+str( cycles )
            currentQty = float(sys_descr["Qty"])
            num_lots_lost = currentQty*self.renewal_lot_perc/100*cycles
            newQty = currentQty - num_lots_lost
            goalquantity = sys_descr["GoalQty"]

            adjustedgoalQty = goalquantity - num_lots_lost
            #Update goal quantity: This is how many we can only reach now because we lost some
            sys_descr["GoalQty"] = int(adjustedgoalQty)

            #Update current quantity: This is how many current exist in the map
            sys_descr["Qty"] = int(newQty)
            return sys_descr


      ###########################################
      #--- OPPORTUNITY MAPPING SUB-FUNCTIONS ---#
      ###########################################

      def setupIncrementVector(self, increment):
            """A global function for creating an increment list from the user input 'rigour levels'.
            For example:
            - If Rigour = 4
            - Then Increment List will be:  [0, 0.25, 0.5, 0.75, 1.0]
            Returns the increment list
            """
            incr_matrix = [0.0]
            for i in range(int(increment)):
                  incr_matrix.append(round(float(1.0/float(increment))*(float(i)+1.0),3))
            return incr_matrix

      def getDCVPath(self, techType):
            """Retrieves the string for the path to the design curve file, whether it is a custom loaded
            design curve or the UB default curves.
            """
            if eval("self."+techType+"designUB"):
                  if techType in ["BF", "IS"]:
                        return ANCILLARY_PATH+"/wsudcurves/Melbourne/"+techType+"-EDD"+str(eval("self."+techType+"spec_EDD"))+"m-FD"+str(eval("self."+techType+"spec_FD"))+"m-DC.dcv"
                  elif techType in ["PB"]:
                        return ANCILLARY_PATH+"/wsudcurves/Melbourne/"+techType+"-MD"+str(eval("self."+techType+"spec_MD"))+"m-DC.dcv"
                  elif techType in ["WSUR"]:
                        return ANCILLARY_PATH+"/wsudcurves/Melbourne/"+techType+"-EDD"+str(eval("self."+techType+"spec_EDD"))+"m-DC.dcv"
                  else:
                        return "No DC Located"
            else:
                  return eval("self."+techType+"descur_path")


      def getTechnologyApplications(self, j):
            """Simply creates a boolean list of whether a particular technology was chosen for flow management
            water quality control and/or water recycling, this list will inform the sizing of the system.
            """
            try:
                  purposeQ = eval("self."+j+"flow")
                  if purposeQ == None:
                        purposeQ = 0
            except NameError:
                  purposeQ = 0
            except AttributeError:
                  purposeQ = 0
            #------------------------------------------------
            try:
                  purposeWQ = eval("self."+j+"pollute")
                  if purposeWQ == None:
                        purposeWQ = 0
            except NameError:
                  purposeWQ = 0
            except AttributeError:
                  purposeWQ = 0
            #------------------------------------------------
            try:
                  purposeREC = eval("self."+j+"recycle")
                  if purposeREC == None:
                        purposeREC = 0
            except NameError:
                  purposeREC = 0
            except AttributeError:
                  purposeREC = 0
            #------------------------------------------------
            purposes = [purposeQ, purposeWQ, purposeREC]
            purposebooleans = [int(self.ration_runoff), int(self.ration_pollute), int(self.ration_harvest)]
            for i in range(len(purposes)):
                  purposes[i] *= purposebooleans[i]
            return purposes


      def assessLotOpportunities(self, techList, currentAttList):
            """Assesses if the shortlist of lot-scale technologies can be put into the lot scale
            Does this for one block at a time, depending on the currentAttributesList and the techlist
            """
            currentID = int(currentAttList["BlockID"])

            tdRES = [0]     #initialize with one option = no technology = 0
            tdHDR = [0]     #because when piecing together options, we want options where there are
            tdLI = [0]      #no lot technologies at all.
            tdHI = [0]
            tdCOM = [0]

            #Check first if there are lot-stuff to work with
            hasHouses = int(currentAttList["HasHouses"]) * int(self.service_res)
            lot_avail_sp = currentAttList["avLt_RES"] * int(self.service_res)        
            Aimplot = currentAttList["ResLotEIA"]          #effective impervious area of one residential allotment

            hasApts = int(currentAttList["HasFlats"]) * int(self.service_hdr)
            hdr_avail_sp = currentAttList["av_HDRes"] * int(self.service_hdr)        
            Aimphdr = currentAttList["HDR_EIA"]

            hasLI = int(currentAttList["Has_LI"]) * int(self.service_li)
            LI_avail_sp = currentAttList["avLt_LI"] * int(self.service_li)
            AimpLI = currentAttList["LIAeEIA"]

            hasHI = int(currentAttList["Has_HI"]) * int(self.service_hi)
            HI_avail_sp = currentAttList["avLt_HI"] * int(self.service_hi)
            AimpHI = currentAttList["HIAeEIA"]

            hasCOM = int(currentAttList["Has_Com"]) * int(self.service_com)
            com_avail_sp = currentAttList["avLt_COM"] * int(self.service_com)
            AimpCOM = currentAttList["COMAeEIA"]

            #Check SKIP CONDITIONS - return zero matrix if either is true.
            if hasHouses + hasApts + hasLI + hasHI + hasCOM == 0:   #SKIP CONDITION #1 - No Units to build on
                  #print "No lot units to build on"
                  return tdRES, tdHDR, tdLI, tdHI, tdCOM

            if lot_avail_sp + hdr_avail_sp + LI_avail_sp + HI_avail_sp + com_avail_sp < 0.0001:    #SKIP CONDITION #2 - no space
                  #print "No lot space to build on"
                  return tdRES, tdHDR, tdLI, tdHI, tdCOM

            #GET INFORMATION FROM VECTOR DATA
            soilK = currentAttList["Soil_k"]               #soil infiltration rate on area

            #print "Impervious Area on Lot: "+str(Aimplot)
            #print "Impervious Area on HDR: "+str(Aimphdr)
            #print "Impervious Area on LI: "+str(AimpLI)
            #print "Impervious Area on HI: "+str(AimpHI)
            #print "Impervious Area on COM: "+str(AimpCOM)

            #Size the required store to achieve the required potable supply substitution.
            storeVols = []
            if bool(int(self.ration_harvest)):
                  store_volRES = self.determineStorageVolForLot(currentAttList, self.raindata, self.evapscale, "RW", "RES")
                  store_volHDR = self.determineStorageVolForLot(currentAttList, self.raindata, self.evapscale, "RW", "HDR")
                  storeVols = [store_volRES, store_volHDR]  #IF 100% service is to occur
                  #print storeVols
            else:
                  storeVols = [np.inf, np.inf]        #By default it is "not possible"

            for j in techList:
                  tech_applications = self.getTechnologyApplications(j)
                  #print "Current Tech: "+str(j)+" applications: "+str(tech_applications)

                  minsize = eval("self."+j+"minsize")         #gets the specific system's minimum allowable size
                  maxsize = eval("self."+j+"maxsize")          #gets the specific system's maximum size

                  #Design curve path
                  dcvpath = self.getDCVPath(j)            #design curve file as a string
                  #print dcvpath

                  #RES Systems
                  hasRESsystems = int(currentAttList["HasL_RESSys"])
                  if hasRESsystems == 0 and hasHouses != 0 and Aimplot > 0.0001 and j not in ["banned","list","of","tech"]:    #Do lot-scale house system
                        sys_objects = self.designTechnology(1.0, Aimplot, j, dcvpath, tech_applications, soilK, minsize, maxsize, lot_avail_sp, "RES", currentID, storeVols[0])
                        for sys_object in sys_objects:
                              tdRES.append(sys_object)

                  #HDR Systems
                  hasHDRsystems = int(currentAttList["HasL_HDRSys"])
                  if hasHDRsystems == 0 and hasApts != 0 and Aimphdr > 0.0001 and j not in ["banned","list","of","tech"]:    #Do apartment lot-scale system
                        for i in self.lot_incr:
                              if i == 0:
                                    continue
                              sys_objects = self.designTechnology(i, Aimphdr, j, dcvpath, tech_applications, soilK, minsize, maxsize, hdr_avail_sp, "HDR", currentID, np.inf)
                              for sys_object in sys_objects:
                                    tdHDR.append(sys_object)

                  #LI Systems
                  hasLIsystems = int(currentAttList["HasL_LISys"])  
                  if hasLIsystems == 0 and hasLI != 0 and AimpLI > 0.0001 and j not in ["banned","list","of","tech"]:
                        for i in self.lot_incr:
                              if i == 0:
                                    continue
                              sys_objects = self.designTechnology(i, AimpLI, j, dcvpath, tech_applications, soilK, minsize, maxsize, LI_avail_sp, "LI", currentID, np.inf)
                              for sys_object in sys_objects:
                                    tdLI.append(sys_object)

                  #HI Systems                        
                  hasHIsystems = int(currentAttList["HasL_HISys"])
                  if hasHIsystems == 0 and hasHI != 0 and AimpHI > 0.0001 and j not in ["banned","list","of","tech"]:
                        for i in self.lot_incr:
                              if i == 0:
                                    continue
                              sys_objects = self.designTechnology(i, AimpHI, j, dcvpath, tech_applications, soilK, minsize, maxsize, HI_avail_sp, "HI", currentID, np.inf)
                              for sys_object in sys_objects:
                                    tdHI.append(sys_object)

                  #COM Systems
                  hasCOMsystems = int(currentAttList["HasL_COMSys"])
                  if hasCOMsystems == 0 and hasCOM != 0 and AimpCOM > 0.0001 and j not in ["banned","list","of","tech"]:
                        for i in self.lot_incr:
                              if i == 0:
                                    continue
                              sys_objects = self.designTechnology(i, AimpCOM, j, dcvpath, tech_applications, soilK, minsize, maxsize, com_avail_sp, "COM", currentID, np.inf)
                              for sys_object in sys_objects:
                                    tdCOM.append(sys_object)

            return tdRES, tdHDR, tdLI, tdHI, tdCOM    

      def designTechnology(self, incr, Aimp, techabbr, dcvpath, tech_applications, soilK, minsize, maxsize, avail_sp, landuse, currentID, storeObj):
            """Carries out the design for a given system type on a given land use and scale. This function is
            used for the different land uses that can accommodate various technologies in the model.
            Input Arguments:            
            -incr = design increment                             -minsize = minimum system size
            -Aimp = effective imp. area                          -maxsize = maximum system size
            -techabbr = technology's abbreviation                -avail_sp = available space
            -dcvpath = design curve path                         -landuse = current land use being designed for
            -tech_applications = types of uses for technology    -currentID = currentBlockID
            -soilK = soil exfiltration rates                     -storeObj = object containing storage info in case of recycling objective
            Output Argument:
            - a WSUD object instance
            """            
            scalematrix = {"RES":'L', "HDR":'L', "LI":'L', "HI":'L', "COM":'L', "Street":'S', "Neigh":'N', "Subbas":'B'}

            try:
                  curscale = scalematrix[landuse]
            except KeyError:
                  curscale = 'NA'

            Adesign_imp = Aimp * incr       #Target impervious area depends on the increment/i.e. level of treatment service

            if storeObj != np.inf:
                  design_Dem = storeObj.getSupply()
                  #print "Size of Tank: "+str(storeObj.getSize())
            else:
                  design_Dem = 0
            #print "Design Demand :"+str(design_Dem)

            #Get Soil K to use for theoretical system design
            if techabbr in ["BF", "SW", "IS", "WSUR", "PB"]:
                  systemK = eval("self."+str(techabbr)+"exfil")
            else:
                  systemK = 0

            Asystem = {"Qty":[None, 1], "WQ":[None,1], "Rec":[None,1], "Size":[None, 1]}  #Template for system design, holds designs

            #OBJECTIVE 1 - Design for Runoff Control
            if tech_applications[0] == 1:
                  purpose = [tech_applications[0], 0, 0]
                  Asystem["Qty"] = eval('td.design_'+str(techabbr)+'('+str(Adesign_imp)+',"'+str(dcvpath)+'",'+str(self.targetsvector)+','+str(purpose)+','+str(soilK)+','+str(systemK)+','+str(minsize)+','+str(maxsize)+')')
                  #print Asystem["Qty"]
            else:
                  Asystem["Qty"] = [None, 1]
            
            Asystem["Size"] = Asystem["Qty"]    #First target, set as default system size, even if zero

            #OBJECTIVE 2 - Design for WQ Control
            if tech_applications[1] == 1:
                  purpose = [0, tech_applications[1], 0]
                  Asystem["WQ"] = eval('td.design_'+str(techabbr)+'('+str(Adesign_imp)+',"'+str(dcvpath)+'",'+str(self.targetsvector)+','+str(purpose)+','+str(soilK)+','+str(systemK)+','+str(minsize)+','+str(maxsize)+')')
                  #print Asystem["WQ"]
            else:
                  Asystem["WQ"] = [None, 1]
            if Asystem["WQ"][0] > Asystem["Size"][0]:
                  Asystem["Size"] = Asystem["WQ"] #if area for water quality is greater, choose the governing one as the final system size

            sys_objects_array = []  #Initialise the array that will hold the tech designs

            #Add the WQ - Qty system combo first to the array. Assume no harvesting
            if Asystem["Size"][0] < avail_sp and Asystem["Size"][0] != None:        #if it fits and is NOT a NoneType:
                  #IF THERE IS NO STORAGE, JUST CREATE THE TECH OBJECT WITHOUT THE STORE
                  servicematrix = [0,0,0]
                  if Asystem["Qty"][0] != None:
                        servicematrix[0] = Adesign_imp
                  if Asystem["WQ"][0] != None:
                        servicematrix[1] = Adesign_imp
                  if Asystem["Rec"][0] != None:
                        servicematrix[2] = design_Dem

                  sys_object = tt.WaterTech(techabbr, Asystem["Size"][0], curscale, servicematrix, Asystem["Size"][1], landuse, currentID)
                  sys_object.setDesignIncrement(incr)
                  sys_objects_array.append(sys_object)

            #OBJECTIVE 3 - If system type permits storage, design for Recycling - this includes WQ control first, then adding storage!
            #   Only works if:
            #       #1 - the harvesting application is checked
            #       #2 - there is a store object that is not infinity
            #       #3 - the system is one of those that supports harvesting
            addstore = []   #Has several arguments [store object, WQsize, QTYsize, type of store, integrated?]
            if tech_applications[2] == 1 and storeObj != np.inf:
                  #First design for WQ control (assume raintanks don't use natural treatment)
                  purpose = [0, 1, 0]
                  if techabbr in ["RT", "GW"]:        #If a raintank or greywater system, then no area required. Assume treatment is through some
                        AsystemRecWQ = [0, 1]           #   non-green-infrastructure means
                  else:   #Design for a fully lined system!
                        AsystemRecWQ = eval('td.design_'+str(techabbr)+'('+str(Adesign_imp)+',"'+str(dcvpath)+'",'+str(self.targetsvector)+','+str(purpose)+','+str(soilK)+','+str(0)+','+str(minsize)+','+str(maxsize)+')')
                        #Required surface are of a system that only does water quality management...

                  vol = storeObj.getSize()
                  #print vol
                  if vol == np.inf:       #Strange error where volume return is inf, yet the name 'inf' is not defined
                        vol = np.inf

                  design_harvest = True
                  if AsystemRecWQ[0] in [np.inf, None] or vol == np.inf:
                        #Skip harvesting design! Cannot fulfill treatment + storage
                        design_harvest = False

                  #Harvesting System Design: Part 1 - INTEGRATED Design extra storage space as integrated storage
                  #   WSUR = open water body as extra area
                  #   PB = part of the storage area
                  #   RT = standard storage volume
                  #   GW = standard storage volume
                  if techabbr in ["RT", "GW", "PB", "WSUR"] and design_harvest:        #Turn the WQ system into a SWH system based on hybrid combos
                        sysdepth = float(self.sysdepths[techabbr])     #obtain the system depth
                        AsystemRecQty = eval('td.sizeStoreArea_'+str(techabbr)+'('+str(vol)+','+str(sysdepth)+','+str(0)+','+str(9999)+')')
                        if AsystemRecQty[0] != None:
                              addstore.append([storeObj, AsystemRecWQ, AsystemRecQty, techabbr, 1])     #Input arguments to addstore function

                  #Harvesting System Design: Part 2 - HYBRID A Design extra storage space as closed auxillary storage
                  #   WSUR = into tank
                  #   BF = into tank
                  #   SW = into tank
                  if techabbr in ["WSUR", "BF", "SW"] and design_harvest:
                        sysdepth = float(self.sysdepths["RT"])
                        AsystemRecQty = td.sizeStoreArea_RT(vol, sysdepth, 0, 9999)
                        if AsystemRecQty[0] != None:
                              addstore.append([storeObj, AsystemRecWQ, AsystemRecQty, "RT", 0])

                  #Harvesting System Design: Part 3 - HYBRID B Design extra storage space as open auxillary storage
                  #   BF = into pond
                  #   SW = into pond
                  if techabbr in ["BF", "SW"] and curscale in ["N", "B"] and design_harvest:
                        sysdepth = float(self.sysdepths["PB"])
                        AsystemRecQty = td.sizeStoreArea_PB(vol, sysdepth, 0.0, 9999.0)
                        if AsystemRecQty[0] != None:
                              addstore.append([storeObj, AsystemRecWQ, AsystemRecQty, "PB", 0])

            if len(addstore) == 0:
                  return sys_objects_array

            for i in range(len(addstore)):
                  curstore = addstore[i]
                  if len(curstore) == 0:
                        #print "No Addstore Data, continuing"
                        continue
            
                  #CHECK WHAT THE TOTAL SYSTEM SIZE IS FIRST BY COMPARING LARGEST SYSTEM TO DATE VS. HARVESTING SYSTEM
                  recsize = curstore[1][0] + curstore[2][0]   #AsystemRecWQ + AsystemRecQTY
                  eafact = recsize/(curstore[1][0]/curstore[1][1] + curstore[2][0]/curstore[2][1])    #area factor, does not indicate relative factors for different systems!
                  #eafact is the same as WQfact and QtyFact if the system is integrated (e.g. Wetland buffer is ALWAYS 1.3)

                  Asystem["Rec"] = [recsize, eafact]  #This is the total recycling storage size
                  if curstore[4] == 1:                #Check if the system integrated? Differentiate between integrated and non-integrated systems!
                        Asystem["Size"] = Asystem["Rec"]    #Because the integrated system has same planning rules so EAFACT is the same
                  else:
                        Asystem["Size"] = curstore[1]   #if non-integrated, then base system is defined ONLY as WQ area/treatment...

                  #NOW CHECK AVAILABLE SPACE - CREATE OBJECT AND PASS TO FUNCTION RETURN
                  if recsize < avail_sp and recsize != None:        #if it fits and is NOT a NoneType
                        #print "Fits"
                        servicematrix = [0,0,0]     #Skip water quantity, this is assumed negligible since the treatment system is lined and will not reduce flow
                        if AsystemRecWQ[0] != None:             #Harvesting system cannot do runoff reduction through normal means!
                              servicematrix[1] = Adesign_imp
                        if AsystemRecQty[0] != None:
                              servicematrix[2] = design_Dem
                        servicematrixstring = tt.convertArrayToDBString(servicematrix)
                        sys_object = tt.WaterTech(techabbr, Asystem["Size"][0], curscale, servicematrix, Asystem["Size"][1], landuse, currentID)
                        sys_object.addRecycledStoreToTech(curstore[0], curstore[2], curstore[3], curstore[4])     #If analysis showed that system can accommodate store, add the store object
                        sys_object.setDesignIncrement(incr)

                        #Work out SWH Benefits for Quantity and Quality
                        if self.swh_benefits:
                              if self.ration_runoff:      #NOW HAVE TO DETERMINE WHETHER TO DO THIS BASED ON UNIT RUNOFF RATE OR SOMETHING ELSE
                                    dcv.treatQTYbenefits(sys_object, self.swh_unitrunoff, Adesign_imp)
                              if self.ration_pollute:
                                    dcv.treatWQbenefits(sys_object, self.swh_unitrunoff, self.targetsvector[1:4], Adesign_imp, self.swhbenefitstable)   #only the three pollution targets
                              # print sys_object.getIAO("all")

                        sys_objects_array.append(sys_object)
            return sys_objects_array    #if no systems are design, returns an empty array


      def assessStreetOpportunities(self, techList, currentAttList):
            """Assesses if the shortlist of street-scale technologies can be put into the streetscape
            Does this for one block at a time, depending on the currentAttributesList and the techlist
            """
            currentID = int(currentAttList["BlockID"])
            technologydesigns = [0]

            #Check first if there is residential lot to manage
            hasHouses = int(currentAttList["HasHouses"]) * int(self.service_res)
            hasSsystems = int(currentAttList["HasSSys"])
            if hasHouses == 0 or hasSsystems == 1:  #SKIP CONDITION 2 - no houses to design for
                  return technologydesigns

            street_avail_Res = currentAttList["avSt_RES"]
            if street_avail_Res < 0.0001:
                  #print "No space on street"
                  return technologydesigns

            #GET INFORMATION FROM VECTOR DATA
            allotments = currentAttList["ResAllots"]
            soilK = currentAttList["Soil_k"]

            Aimplot = currentAttList["ResLotEIA"]
            AimpRes = Aimplot * allotments
            AimpstRes = currentAttList["ResFrontT"] - currentAttList["avSt_RES"]

            Aimphdr = currentAttList["HDR_EIA"]

            storeObj = np.inf       #No storage recycling for this scale

            for j in techList:
                  tech_applications = self.getTechnologyApplications(j)
                  #print "Assessing street techs for "+str(j)+" applications: "+str(tech_applications)

                  minsize = eval("self."+j+"minsize")
                  maxsize = eval("self."+j+"maxsize")          #gets the specific system's maximum size

                  #Design curve path
                  dcvpath = self.getDCVPath(j)

                  for lot_deg in self.lot_incr:
                        AimpremainRes = AimpstRes + (AimpRes *(1-lot_deg))      #street + remaining lot
                        AimpremainHdr = Aimphdr*(1.0-lot_deg)

                        for street_deg in self.street_incr:
                              #print "CurrentStreet Deg: "+str(street_deg)+" for lot-deg "+str(lot_deg)
                              if street_deg == 0:
                                    continue
                              AimptotreatRes = AimpremainRes * street_deg
                              AimptotreatHdr = AimpremainHdr * street_deg
                              #print "Aimp to treat: "+str(AimptotreatRes)

                              if hasHouses != 0 and AimptotreatRes > 0.0001:
                                    sys_objects = self.designTechnology(street_deg, AimptotreatRes, j, dcvpath,
                                          tech_applications, soilK, minsize, maxsize, 
                                          street_avail_Res, "Street", currentID, storeObj)
                                    for sys_object in sys_objects:
                                          sys_object.setDesignIncrement([lot_deg, street_deg])
                                          technologydesigns.append(sys_object)
            return technologydesigns


      def assessNeighbourhoodOpportunities(self, techList, currentAttList):
            """Assesses if the shortlist of neighbourhood-scale technologies can be put in local parks 
            & other areas. Does this for one block at a time, depending on the currentAttributesList 
            and the techlist
            """
            currentID = int(currentAttList["BlockID"])
            technologydesigns = [0]

            #Grab total impervious area and available space
            AblockEIA = currentAttList["Manage_EIA"]
            hasNsystems = int(currentAttList["HasNSys"])
            hasBsystems = int(currentAttList["HasBSys"])
            if AblockEIA <= 0.0001 or hasNsystems == 1 or hasBsystems == 1:
                  return technologydesigns    #SKIP CONDITION 1 - already systems in place or no impervious area to treat

            av_PG = currentAttList["PG_av"]
            av_REF = currentAttList["REF_av"]
            av_SVU_sw = currentAttList["SVU_avSW"]
            av_SVU_ws = currentAttList["SVU_avWS"]
            totalavailable = av_PG + av_REF + av_SVU_sw + av_SVU_ws
            if totalavailable < 0.0001:
                  return technologydesigns    #SKIP CONDITION 2 - NO SPACE AVAILABLE

            #GET INFORMATION FROM VECTOR DATA
            soilK = currentAttList["Soil_k"]

            #Size a combination of stormwater harvesting stores
            if bool(int(self.ration_harvest)):
                  neighSWstores = self.determineStorageVolNeigh(currentAttList, self.raindata, self.evapscale, "SW")
                  #print neighSWstores

            for j in techList:
                  tech_applications = self.getTechnologyApplications(j)
                  #print "Currently designing tech: "+str(j)+" available applications: "+str(tech_applications)

                  minsize = eval("self."+j+"minsize")
                  maxsize = eval("self."+j+"maxsize")         #Gets the specific system's maximum size
                  #Design curve path
                  dcvpath = self.getDCVPath(j)
                  for neigh_deg in self.neigh_incr:
                        #print "Current Neigh Deg: "+str(neigh_deg)
                        if neigh_deg == 0: 
                              continue

                        Aimptotreat = neigh_deg * AblockEIA

                        if bool(int(self.ration_harvest)) and neighSWstores != np.inf:
                              curStoreObjs = neighSWstores[neigh_deg]
                              for supplyincr in self.neigh_incr:
                                    if supplyincr == 0: 
                                          continue
                                    storeObj = curStoreObjs[supplyincr]
                                    sys_objects = self.designTechnology(neigh_deg, Aimptotreat, j, dcvpath, tech_applications,
                                                      soilK, minsize, maxsize, totalavailable, "Neigh", currentID, storeObj)
                                    for sys_object in sys_objects:
                                          sys_object.setDesignIncrement(neigh_deg)
                                          technologydesigns.append(sys_object)
                        else:
                              storeObj = np.inf
                              sys_objects = self.designTechnology(neigh_deg, Aimptotreat, j, dcvpath, tech_applications,
                                                                  soilK, minsize, maxsize, totalavailable, "Neigh", currentID, storeObj)
                              for sys_object in sys_objects:
                                    sys_object.setDesignIncrement(neigh_deg)
                                    technologydesigns.append(sys_object)

            return technologydesigns


      def assessSubbasinOpportunities(self, techList, currentAttList):
            """Assesses if the shortlist of sub-basin-scale technologies can be put in local parks 
            & other areas. Does this for one block at a time, depending on the currentAttributesList 
            and the techlist
            """
            currentID = int(currentAttList["BlockID"])

            technologydesigns = {}  #Three Conditions: 1) there must be upstream blocks
                                                     # 2) there must be space available, 
                                                     # 3) there must be impervious to treat

            soilK = currentAttList["Soil_k"]

            #SKIP CONDITION 1: Grab Block's Upstream Area
            upstreamIDs = self.retrieveStreamBlockIDs(currentAttList, "upstream")
            hasBsystems = int(currentAttList["HasBSys"])
            hasNsystems = int(currentAttList["HasBSys"])
            if len(upstreamIDs) == 0 or hasBsystems == 1 or hasNsystems == 1:
                  #print "Current Block has no upstream areas, skipping"
                  return technologydesigns

            #SKIP CONDITION 2: Grab Total available space, if there is none, no point continuing
            av_PG = currentAttList["PG_av"]
            av_REF = currentAttList["REF_av"]
            av_SVU_sw = currentAttList["SVU_avSW"]
            av_SVU_ws = currentAttList["SVU_avWS"]
            totalavailable = av_PG + av_REF + av_SVU_sw + av_SVU_ws
            if totalavailable < 0.0001:
                  #print "Total Available Space in Block to do STUFF: "+str(totalavailable)+" less than threshold"
                  return technologydesigns

            #SKIP CONDITION 3: Get Block's upstream Impervious area
            upstreamImp = self.retrieveAttributeFromIDs(upstreamIDs, "Manage_EIA", "sum")
            if upstreamImp < 0.0001:
                  #print "Total Upstream Impervious Area: "+str(upstreamImp)+" less than threshold"
                  return technologydesigns

            #Initialize techdesignvector's dictionary keys
            for j in self.subbas_incr:
                  technologydesigns[j] = [0]

            if bool(int(self.ration_harvest)):
                  subbasSWstores = self.determineStorageVolSubbasin(currentAttList, self.raindata, self.evapscale, "SW")
                  #print "Subbasin: "+str(subbasSWstores)

            for j in techList:
                  tech_applications = self.getTechnologyApplications(j)
                  #print "Now designing for "+str(j)+" for applications: "+str(tech_applications)

                  minsize = eval("self."+j+"minsize")
                  maxsize = eval("self."+j+"maxsize")     #Gets the specific system's maximum allowable size

                  #Design curve path
                  dcvpath = self.getDCVPath(j)
                  for bas_deg in self.subbas_incr:
                        #print Current Basin Deg: "+str(bas_deg)
                        if bas_deg == 0:
                              continue
                        Aimptotreat = upstreamImp * bas_deg
                        #print "Aimp to treat: "+str(Aimptotreat)

                        #Loop across all options in curStoreObj
                        if bool(int(self.ration_harvest)) and subbasSWstores != np.inf:
                              curStoreObjs = subbasSWstores[bas_deg]  #current dict of possible stores based on harvestable area (bas_Deg)
                              for supplyincr in self.subbas_incr:
                                    if supplyincr == 0 or Aimptotreat < 0.0001: 
                                          continue
                                    storeObj = curStoreObjs[supplyincr]
                                    sys_objects = self.designTechnology(bas_deg, Aimptotreat, j, dcvpath, tech_applications,
                                                      soilK, minsize, maxsize, totalavailable, "Subbas", currentID, storeObj)
                              for sys_object in sys_objects:
                                    sys_object.setDesignIncrement(bas_deg)
                                    technologydesigns[bas_deg].append(sys_object)
                        else:
                              storeObj = np.inf
                              sys_objects = self.designTechnology(bas_deg, Aimptotreat, j, dcvpath, tech_applications,
                                                soilK, minsize, maxsize, totalavailable, "Subbas", currentID, storeObj)
                              for sys_object in sys_objects:
                                    sys_object.setDesignIncrement(bas_deg)
                                    technologydesigns[bas_deg].append(sys_object)
            return technologydesigns


      def retrieveStreamBlockIDs(self, currentAttList, direction):
            """Returns a vector containing all upstream block IDs, allows quick collation of 
            details.
            """
            blockID = int(currentAttList["BlockID"])
            streamIDs = []
            curID = blockID
            if direction == "upstream":
                  #Read downIDlist, grab BlockID, continue
                  
                  #First group of IDs
                  indices = [id_index for id_index, x in enumerate(self.downIDlist) if x == curID]
                  for id_index in indices:
                        if id_index == -1:
                              continue
                        streamIDs.append(self.blockIDlist[id_index])
            
                  #Begin scanning the next IDs
                  curindex = 0
                  while curindex != len(streamIDs):
                        indices = [id_index for id_index, x in enumerate(self.downIDlist) if x == streamIDs[curindex]]
                        for id_index in indices:
                              streamIDs.append(self.blockIDlist[id_index])
                        curindex += 1

            elif direction == "downstream":
                  while curID != -1:
                        try: 
                              downID = self.downIDlist[self.blockIDlist.index(curID)]
                              if downID == -1:
                                    curID = -1
                                    continue
                              else:
                                    streamIDs.append(downID)
                              curID = self.downIDlist[self.blockIDlist.index(curID)]
                        except:
                              curID = -1
            if len(streamIDs) == 0:
                  return []
            else:
                  return streamIDs

      def retrieveAttributeFromIDs(self, listIDs, attribute, calc):
            """Retrieves all values from the list of upstreamIDs with the attribute name
            <attribute> and calculates whatever <calc> specifies
                  Input:
                        - listIDs: the vector list of upstream IDs e.g. [3, 5, 7, 8, 10, 15, 22]
                        - attribute: an exact string that matches the attribute as saved by other
                              modules
                  - calc: the means of calculation, options include
                              'sum' - calculates total sum
                              'average' - calculates average
                              'max' - retrieves the maximum
                              'min' - retrieves the minimum
                              'minNotzero' - retrieves the minimum among non-zero numbers
                              'list' - returns the list itself
            """
            output = 0
            datavector = []

            for i in listIDs:
                  curAttList = self.blockDict[int(i)]
                  #blockFace = self.getBlockUUID(i, city)
                  if curAttList["Status"] == 0:
                        continue
                  datavector.append(curAttList[attribute])

            if calc == 'sum':
                  output = sum(datavector)
            elif calc == 'average':
                  pass
            elif calc == 'max':
                  pass
            elif calc == 'min':
                  pass
            elif calc == 'minNotzero':
                  pass
            elif calc == 'list':
                  output = datavector
            else:
                  print "Error, calc not specified, returning sum"
                  output = sum(datavector)
            return output

      def determineStorageVolForLot(self, currentAttList, rain, evapscale, wqtype, lottype):
            """Uses information of the Block's lot-scale to determine what the required
            storage size of a water recycling system is to meet the required end uses
            and achieve the user-defined potable water reduction
            - currentAttList:  current Attribute list of the block in question
            - rain: rainfall data for determining inflows if planning SW harvesting
            - evapscale: scaling factors for outdoor irrigation demand scaling
            - wqtype: the water quality being harvested (determines the type of end
            uses acceptable)

            Function returns a storage volume based on the module's predefined variables
            of potable water supply reduction, reliability, etc."""

            if int(currentAttList["HasRes"]) == 0:
                  return np.inf       #Return infinity if there is no res land use
            #First exit
            if lottype == "RES" and int(currentAttList["HasHouses"]) == 0:
                  return np.inf
            if lottype == "HDR" and int(currentAttList["HasFlats"]) == 0:
                  return np.inf

            #WORKING IN [kL/yr] for single values and [kL/day] for timeseries

            #Use the FFP matrix to determine total demands and suitable end uses

            wqlevel = self.ffplevels[wqtype]    #get the level and determine the suitable end uses
            if lottype == "RES":    #Demands based on a single house
                  reshouses = float(currentAttList["ResHouses"])
                  resallots = float(currentAttList["ResAllots"])
                  lotdemands = {"Kitchen":currentAttList["wd_RES_K"]*365.0/reshouses,
                        "Shower":currentAttList["wd_RES_S"]*365.0/reshouses,
                        "Toilet":currentAttList["wd_RES_T"]*365.0/reshouses,
                        "Laundry":currentAttList["wd_RES_L"]*365.0/reshouses,
                        "Irrigation":currentAttList["wd_RES_I"]*365.0/resallots }
            elif lottype == "HDR": #Demands based on entire apartment sharing a single roof
                  hdrflats = float(currentAttList["HDRFlats"])
                  lotdemands = {"Kitchen":currentAttList["wd_HDR_K"]*365.0/hdrflats,
                        "Shower":currentAttList["wd_HDR_S"]*365.0/hdrflats,
                        "Toilet":currentAttList["wd_HDR_T"]*365.0/hdrflats,
                        "Laundry":currentAttList["wd_HDR_L"]*365.0/hdrflats,
                        "Irrigation":currentAttList["wd_HDR_I"]*365.0 }
            totalhhdemand = sum(lotdemands.values())    #Total House demand, [kL/yr]

            enduses = {}        #Tracks all the different types of end uses
            objenduses = []
            if self.ffplevels[self.ffp_kitchen] >= wqlevel:
                  enduses["Kitchen"] = lotdemands["Kitchen"]
                  objenduses.append('K')
            if self.ffplevels[self.ffp_shower] >= wqlevel:
                  enduses["Shower"] = lotdemands["Shower"]
                  objenduses.append('S')
            if self.ffplevels[self.ffp_toilet] >= wqlevel:
                  enduses["Toilet"] = lotdemands["Toilet"]
                  objenduses.append('T')
            if self.ffplevels[self.ffp_laundry] >= wqlevel:
                  enduses["Laundry"] = lotdemands["Laundry"]
                  objenduses.append('L')
            if self.ffplevels[self.ffp_garden] >= wqlevel:
                  enduses["Irrigation"] = lotdemands["Irrigation"]
                  objenduses.append('I')
            totalsubdemand = sum(enduses.values())

            if totalsubdemand == 0:
                  return np.inf

            #Determine what the maximum substitution can be, supply the smaller of total substitutable demand
            #or the desired target.
            recdemand = min(totalsubdemand, self.service_rec/100*totalhhdemand)     #the lower of the two
            #print "Recycled Demand Lot: "+str(recdemand)
            #Determine inflow/demand time series
            if lottype == "RES":
                  Aroof = currentAttList["ResRoof"]
            elif lottype == "HDR":
                  Aroof = currentAttList["HDRRoofA"]

            #Determine demand time series
            if "Irrigation" in enduses.keys():
                  #Scale to evap pattern
                  demandseries = ubseries.createScaledDataSeries(recdemand, evapscale, False)
            else:
                  #Scale to constant pattern
                  demandseries = ubseries.createConstantDataSeries(recdemand/365, len(rain))

            #Generate the inflow series based on the kind of water being harvested
            if wqtype in ["RW", "SW"]:      #Use rainwater to generate inflow
                  inflow = ubseries.convertDataToInflowSeries(rain, Aroof, False)     #Convert rainfall to inflow
                  maxinflow = sum(rain)/1000 * Aroof / self.rain_length         #average annual inflow using whole roof
                  tank_templates = self.lot_raintanksizes     #Use the possible raintank sizes
            elif wqtype in ["GW"]:  #Use greywater to generate inflow
                  inflow = 0
                  maxinflow = 0
                  tank_templates = [] #use the possible greywater tank sizes

            if (self.rec_demrange_max/100.0)*maxinflow < recdemand or (self.rec_demrange_min/100.0)*maxinflow > recdemand:
                  #If Vdem not within the bounds of total inflow
                  return np.inf       #cannot size a store that is supplying more than it is getting or not economical to size

            #Depending on Method, size the store
            if self.sb_method == "Sim":
                  mintank_found = 0
                  storageVol = np.inf      #Assume infinite storage for now
                  for i in tank_templates:        #Run through loop
                        if mintank_found == 1:
                              continue
                  rel = dsim.calculateTankReliability(inflow, demandseries, i)
                  if rel > self.targets_reliability:
                        mintank_found = 1
                        storageVol = i

            elif self.sb_method == "Eqn":
                  vdemvsupp = recdemand / maxinflow
                  storagePerc = deq.loglogSWHEquation(self.regioncity, self.targets_reliability, inflow, demandseries)
                  reqVol = storagePerc/100*maxinflow  #storagePerc is the percentage of the avg. annual inflow

                  #Determine where this volume ranks in reliability
                  storageVol = np.inf     #Assume infinite storage for now, readjust later
                  tank_templates.reverse()        #Reverse the series for the loop
                  for i in range(len(tank_templates)):
                        if reqVol < tank_templates[i]: #Begins with largest tank
                              storageVol = tank_templates[i] #Begins with largest tank    #if the volume is below the current tank size, use the 'next largest'
                  tank_templates.reverse()        #Reverse the series back in case it needs to be used again
            storeObj = tt.RecycledStorage(wqtype, storageVol,  objenduses, Aroof, self.targets_reliability, recdemand, "L")
            #End of function: returns storageVol as either [1kL, 2kL, 5kL, 10kL, 15kL, 20kL] or np.inf
            return storeObj

      def determineEndUses(self, wqtype):
            """Returns an array of the allowable water end uses for the given water
            quality type 'wqtype'. Array is dependent on user inputs and is subsequently
            used to determine water demands substitutable by that water source. This 
            function is only for neighbourhood and sub-basin scales"""
            wqlevel = self.ffplevels[wqtype]
            enduses = []
            if self.ffplevels[self.ffp_kitchen] >= wqlevel: enduses.append("K")
            if self.ffplevels[self.ffp_shower] >= wqlevel: enduses.append("S")
            if self.ffplevels[self.ffp_toilet] >= wqlevel: enduses.append("T")
            if self.ffplevels[self.ffp_laundry] >= wqlevel: enduses.append("L")
            if self.ffplevels[self.ffp_garden] >= wqlevel: enduses.append("I")
            if self.ffplevels[self.public_irr_wq] >= wqlevel: enduses.append("PI")
            return enduses

      def determineStorageVolNeigh(self, currentAttList, rain, evapscale, wqtype):
            """Uses information of the Block to determine the required storage size of
            a water recycling system to meet required end uses and achieve the user-defined
            potable water reduction and reliability targets
            - currentAttList:  current Attribute list of the block in question
            - rain: rainfall data for determining inflows if planning SW harvesting
            - evapscale: scaling factors for outdoor irrigation demand scaling
            - wqtype: water quality being harvested (determines the type of end
            uses acceptable)

            Function returns an array of storage volumes in dictionary format identified
            by the planning increment."""

            #WORKING IN [kL/yr] for single values and [kL/day] for time series
            if currentAttList["Blk_EIA"] == 0:
                  return np.inf

            enduses = self.determineEndUses(wqtype)
            houses = currentAttList["ResHouses"]

            #Total water demand (excluding non-residential areas)
            storageVol = {}

            #Get the entire Block's Water Demand
            blk_demands = self.getTotalWaterDemandEndUse(currentAttList, ["K","S","T", "L", "I", "PI"])
            #print "Block demands: "+str(blk_demands)

            #Get the entire Block's substitutable water demand
            totalsubdemand = self.getTotalWaterDemandEndUse(currentAttList, enduses)
            #print "Total Demand Substitutable: "+str(totalsubdemand)

            if totalsubdemand == 0: #If nothing can be substituted, return infinity
                  return np.inf    

            #Loop across increments: Storage that harvests all area/WW to supply [0.25, 0.5, 0.75, 1.0] of demand
            for i in range(len(self.neigh_incr)):   #Loop across harvestable area
                  if self.neigh_incr[i] == 0:
                        continue
                  harvestincr = self.neigh_incr[i]
                  storageVol[harvestincr] = {} #Initialize container dictionary

                  for j in range(len(self.neigh_incr)):   #Loop across substitutable demands
                        if self.neigh_incr[j] == 0:
                              continue

                        supplyincr = self.neigh_incr[j]
                        recdemand = supplyincr*blk_demands  #x% of total block demand
                        if recdemand > totalsubdemand:      #if that demand is greater than what can be substituted, then
                              storageVol[harvestincr][supplyincr] = np.inf         
                              #make it impossible to size a system for that combo
                              continue
                        #print "Recycled Demand: "+str(recdemand)

                        if recdemand == 0:
                              #If there is no demand to substitute, then storageVol is np.inf
                              storageVol[harvestincr][supplyincr] = np.inf
                              continue

                        #Harvestable area
                        Aharvest = currentAttList["Blk_EIA"]*harvestincr   #Start with this
                        #print "Harvestable Area :"+str(Aharvest)

                        if "I" in enduses:      #If irrigation is part of end uses
                              #Scale to evap pattern
                              demandseries = ubseries.createScaledDataSeries(recdemand, evapscale, False)
                        else:
                              #Scale to constant pattern
                              demandseries = ubseries.createScaledDataSeries(recdemand/365, len(rain))

                        #Generate the inflow series based on kind of water being harvested
                        if wqtype in ["RW", "SW"]:
                              inflow = ubseries.convertDataToInflowSeries(rain, Aharvest, False)
                              maxinflow = sum(rain)/1000*Aharvest / self.rain_length
                              #print "Average annual inflow: "+str(maxinflow)
                        elif wqtype in ["GW"]:
                              inflow = 0
                              maxinflow = 0

                        if (self.rec_demrange_max/100.0)*maxinflow < recdemand or (self.rec_demrange_min/100.0)*maxinflow > recdemand:
                              storageVol[harvestincr][supplyincr] = np.inf 
                              #Cannot size a store that is not within the demand range specified
                              continue

                        #Size the store depending on method
                        if self.sb_method == "Sim":
                              reqVol = dsim.estimateStoreVolume(inflow, demandseries, self.targets_reliability, self.relTolerance, self.maxSBiterations)
                              #print "reqVol: "+str(reqVol)
                        elif self.sb_method == "Eqn":
                              vdemvsupp = recdemand / maxinflow
                              storagePerc = deq.loglogSWHEquation(self.regioncity, self.targets_reliability, inflow, demandseries)
                              reqVol = storagePerc/100*maxinflow  #storagePerc is the percentage of the avg. annual inflow
                        storeObj = tt.RecycledStorage(wqtype, reqVol, enduses, Aharvest, self.targets_reliability, recdemand, "N")
                        storageVol[harvestincr][supplyincr] = storeObj       #at each lot incr: [ x options ]
            #print storageVol[harvestincr]
            return storageVol

      def getTotalWaterDemandEndUse(self, currentAttList, enduse):
            """Retrieves all end uses for the current Block based on the end use matrix
            and the lot-increment. 
            """
            demand = 0
            #End use in houses and apartments - indoors + garden irrigation
            for i in enduse:    #Get Indoor demands first
                  if i == "PI" or i == "I":
                        continue    #Skip the public irrigation
                  demand += currentAttList["wd_RES_"+str(i)]*365.0
                  demand += currentAttList["wd_HDR_"+str(i)]*365.0
            #Add irrigation of public open space
            if "I" in enduse:
                  demand += currentAttList["wd_RES_I"]*365.0
                  demand += currentAttList["wd_HDR_I"]*365.0 #Add all HDR irrigation
            if "PI" in enduse:
                  demand += currentAttList["wd_PubOUT"]
            return demand


      def determineStorageVolSubbasin(self, currentAttList, rain, evapscale, wqtype):
            """Uses information of the current Block and the broader sub-basin to determine
            the required storage size of a water recycling system to meet required end uses
            and achieve user-defined potable water reduction and reliability targets. It does
            this for a number of combinations, but finds the worst case first e.g.

            4 increments: [0.25, 0.5, 0.75, 1.00] of the catchment harvested to treat
            [0.25, 0.5, 0.75, 1.00] portion of population and public space
            worst case scenario: 0.25 harvest to supply 1.00 of area

            Input parameters:
            - currentAttList: current Attribute list of the block in question
            - rain: rainfall data for determining inflows if planning SW harvesting
            - evapscale: scaling factors for outdoor irrigation demand scaling
            - wqtype: water quality being harvested (determines the type of end uses
            accepable)

            Model also considers the self.hs_strategy at this scale, i.e. harvest upstream
            to supply downstream? harvest upstream to supply upstream? harvest upstream to
            supply basin?

            Function returns an array of storage volumes in dictionary format identified by
            planning increment."""

            #WORKING IN [kL/yr] for single values and [kL/day] for time series
            #(1) Get all Blocks based on the strategy
            harvestblockIDs = self.retrieveStreamBlockIDs(currentAttList, "upstream")
            harvestblockIDs.append(currentAttList["BlockID"])
            if self.hs_strategy == "ud":
                  supplytoblockIDs = self.retrieveStreamBlockIDs(currentAttList, "downstream")
                  supplytoblockIDs.append(currentAttList["BlockID"])
            elif self.hs_strategy == "uu":
                  supplytoblockIDs = harvestblockIDs        #Try ref copy first
                  #        supplytoblockIDs = []
                  #        for i in range(len(harvestblockIDs)):
                  #            supplytoblockIDs.append(harvestblockIDs[i])   #make a direct copy
            elif self.hs_strategy == "ua":
                  supplytoblockIDs = self.retrieveStreamBlockIDs(currentAttList, "downstream")
                  for i in range(len(harvestblockIDs)):   #To get all basin IDs, simply concatenate the strings
                        supplytoblockIDs.append(harvestblockIDs[i])   

            #print "HarvestBlocKIDs: "+str(harvestblockIDs)
            #print "SupplyBlockIDs:" +str(supplytoblockIDs)

            #(2) Prepare end uses and obtain full demands
            enduses = self.determineEndUses(wqtype)
            bas_totdemand = 0
            bas_subdemand = 0
            for i in supplytoblockIDs:
                  #block_attr = self.getBlockUUID(i, city)
                  block_attr = self.blockDict[int(i)]
                  bas_totdemand += self.getTotalWaterDemandEndUse(block_attr, ["K","S","T", "L", "I", "PI"])
                  bas_subdemand += self.getTotalWaterDemandEndUse(block_attr, enduses)

            #print "Total basin demands/substitutable "+str(bas_totdemand_+" "+str(bas_subdemand)

            #(3) Grab total harvestable area
            AharvestTot = self.retrieveAttributeFromIDs(harvestblockIDs, "Blk_EIA", "sum")
            #print "AharvestTotal: "+str(AharvestTot)
            if AharvestTot == 0:    #no area to harvest
                  return np.inf
                  #Future - add something to deal with retrofit

            storageVol = {}
            #(4) Generate Demand Time Series
            for i in range(len(self.subbas_incr)):          #HARVEST x% LOOP
                  if self.subbas_incr[i] == 0:
                        continue        #Skip 0 increment

                  harvestincr = self.subbas_incr[i]
                  storageVol[harvestincr] = {}    #initialize container
                  for j in range(len(self.subbas_incr)):      #SUPPLY y% LOOP
                        if self.subbas_incr[j] == 0:
                              continue    #Skip 0 increment

                        supplyincr = self.subbas_incr[j]
                        recdemand = bas_totdemand * supplyincr
                        if recdemand > bas_subdemand:      #if that demand is greater than what can be substituted, then
                              storageVol[harvestincr][supplyincr] = np.inf         
                              #make it impossible to size a system for that combo
                              continue

                        Aharvest = AharvestTot * harvestincr
                        #print "Required demand: "+str(recdemand)
                        if "I" in enduses:
                              demandseries = ubseries.createScaledDataSeries(recdemand, evapscale, False)
                        else:
                              demandseries = ubseries.createScaledDataSeries(recdemand/365, len(rain))

                        if wqtype in ["RW", "SW"]:
                              inflow = ubseries.convertDataToInflowSeries(rain, Aharvest, False)
                              maxinflow = sum(rain)/1000*Aharvest / self.rain_length
                              #print "Average annual inflow: "+str(maxinflow)
                        elif wqtype in ["GW"]:
                              inflow = 0
                              maxinflow = 0

                        if (self.rec_demrange_max/100.0)*maxinflow < recdemand or (self.rec_demrange_min/100.0)*maxinflow > recdemand:
                              #Cannot design a storage for a demand that is not within the user-defined range of total annual inflow
                              storageVol[harvestincr][supplyincr] = np.inf
                              continue

                        #(5) Size the store for the current combo
                        if self.sb_method == "Sim":
                              reqVol = dsim.estimateStoreVolume(inflow, demandseries, self.targets_reliability, self.relTolerance, self.maxSBiterations)
                              #print "reqVol: "+str(reqVol)
                        elif self.sb_method == "Eqn":
                              vdemvsupp = recdemand / maxinflow
                              storagePerc = deq.loglogSWHEquation(self.regioncity, self.targets_reliability, inflow, demandseries)
                              reqVol = storagePerc/100*maxinflow  #storagePerc is the percentage of the avg. annual inflow

                        storeObj = tt.RecycledStorage(wqtype, reqVol, enduses, Aharvest, self.targets_reliability, recdemand, "B")
                        storageVol[harvestincr][supplyincr] = storeObj
            return storageVol

      ###################################
      #--- IN-BLOCK OPTIONS CREATION ---#
      ###################################
      def constructInBlockOptions(self, currentAttList, lot_techRES, lot_techHDR, lot_techLI, 
                                    lot_techHI, lot_techCOM, street_tech, neigh_tech):
            """Tries every combination of technology and narrows down the list of in-block
            options based on MCA scoring and the Top Ranking Configuration selected by the
            user. Returns an array of the top In-Block Options for piecing together with
            sub-basin scale systems
            Input Arguments:
                  - currentAttList - current Block's Attribute list
                  - lot_techRES - list of lot-scale technologies for residential land use
                  - lot_techHDR - list of lot-scale technologies for HDR land use
                  - lot_techLI - list of lot-scale technologies for LI land use
                  - lot_techHI - list of lot-scale technologies for HI land use
                  - lot_techCOM - list of lot-scale technologies for COM land use
                  - street_tech - list of street scale technologies limited to RES land use
                  - neigh_tech - list of neighbourhood scale technologies for block
            """
            allInBlockOptions = {}      #Initialize dictionary to hold all in-block options
            currentID = int(currentAttList["BlockID"])
            blockarea = pow(self.block_size, 2) * currentAttList["Active"]

            for i in range(len(self.subbas_incr)):                #e.g. for [0, 0.25, 0.5, 0.75, 1.0]
                  allInBlockOptions[self.subbas_incr[i]] = []       #Bins are: 0 to 25%, >25% to 50%, >50% to 75%, >75% to 100% of block treatment

            #Obtain all variables needed to do area balance for Impervious Area Service
            allotments = currentAttList["ResAllots"]
            estatesLI = currentAttList["LIestates"]
            estatesHI = currentAttList["HIestates"]
            estatesCOM = currentAttList["COMestates"]
            Aimplot = currentAttList["ResLotEIA"]
            AimpRes = allotments * Aimplot
            AimpstRes = currentAttList["ResFrontT"] - currentAttList["avSt_RES"]
            Aimphdr = currentAttList["HDR_EIA"]    
            AimpAeLI = currentAttList["LIAeEIA"]
            AimpLI = AimpAeLI * estatesLI
            AimpAeHI = currentAttList["HIAeEIA"]
            AimpHI = AimpAeHI * estatesHI
            AimpAeCOM = currentAttList["COMAeEIA"]
            AimpCOM = AimpAeCOM * estatesCOM

            AblockEIA = currentAttList["Manage_EIA"]          #Total block imp area to manage
            blockDem = currentAttList["Blk_WD"] - currentAttList["wd_Nres_IN"]

            if AblockEIA == 0 and blockDem == 0:
                  return {}

            #CREATE COMBINATIONS MATRIX FOR ALL LOT SCALE TECHNOLOGIES FIRST
            #   for lot-scale technologies, these are pieced together based on the same increment
            #   combinations are either 0 or the technologies that fit at that increment
            lot_tech = []
            for a in range(len(self.lot_incr)):     #lot_incr = [0, ....., 1.0]
                  lot_deg = self.lot_incr[a]          #currently working on all lot-scale systems of increment lot_deg
                  if lot_deg == 0:
                        lot_tech.append([lot_deg,0,0,0,0,0])      #([deg, res, hdr, li, hi, com])
                        continue
                  for b in lot_techRES:
                        for c in lot_techHDR:
                              if c != 0 and c.getDesignIncrement() != lot_deg:
                                    continue
                              for d in lot_techLI:
                                    if d != 0 and d.getDesignIncrement() != lot_deg:
                                          continue
                                    for e in lot_techHI:
                                          if e != 0 and e.getDesignIncrement() != lot_deg:
                                                continue
                                          for f in lot_techCOM:
                                                if f != 0 and f.getDesignIncrement() != lot_deg:
                                                      continue
                                                lot_tech.append([lot_deg, b, c, d, e, f])
            if len(street_tech) == 0:
                  street_tech.append(0)
            if len(neigh_tech) == 0:
                  neigh_tech.append(0)

            #Combine all three scales together
            combocheck =[]
            for a in lot_tech:
                  for b in street_tech:
                        for c in neigh_tech:
                              lot_deg = a[0]
                              combo = [a[1], a[2], a[3], a[4], a[5], b, c]
                              #if combo in combocheck:
                              #    continue
                              combocheck.append(combo)
                              #print "Combo: "+str(combo)+ " at lot deg: "+str(lot_deg)
                              lotcounts = [int(lot_deg * allotments), int(1), int(estatesLI), int(estatesHI), int(estatesCOM),int(1),int(1)]

                              if allotments != 0 and int(lot_deg*allotments) == 0:
                                    continue        #the case of minimal allotments on-site where multiplying by lot-deg and truncation returns zero
                                                      #this results in totalimpserved = 0, therefore model crashes on ZeroDivisionError

                              #Check if street + lot systems exceed the requirements
                              if a[1] != 0 and b != 0 and (a[1].getService("Qty")*allotments + b.getService("Qty")) > (AimpRes+AimpstRes):
                                    continue    #Overtreatment occurring in residential district at the lot scale for "Qty"
                              if a[1] != 0 and b != 0 and (a[1].getService("WQ")*allotments + b.getService("WQ")) > (AimpRes+AimpstRes):
                                    continue    #Overtreatment occurring in residential district at the lot scale for "WQ"
                              if combo.count(0) == 7: 
                                    continue    #all options in the combo are zero, then we have no technologies, skip this as well

                              servicematrix = self.getTotalComboService(combo, lotcounts)
                              offsetmatrix = self.getTotalIAOofCombo(combo, lotcounts)
                              #print servicematrix

                              if servicematrix[0] > AblockEIA or servicematrix[1] > AblockEIA:
                                    #print "Overtreatment on Qty or WQ side"
                                    continue
                              elif servicematrix[2] > blockDem: #CHANGE TO DEMAND!
                                    #print "Oversupply of demand"
                                    continue
                              else:
                                    #print "Strategy is fine"
                                    #Create Block Strategy and put it into one of the subbas bins of allInBlockOptions
                                    servicebin = self.identifyBin(servicematrix, AblockEIA, blockDem)
                                    blockstrat = tt.BlockStrategy(combo, servicematrix, lotcounts, currentID, servicebin)
                                    blockstrat.setIAO("Qty", offsetmatrix[0])
                                    blockstrat.setIAO("WQ", offsetmatrix[1])
                                    #print blockstrat
                                    tt.CalculateMCATechScores(blockstrat,[AblockEIA, AblockEIA, blockDem],self.curscalepref, self.priorities, 
                                          self.mca_techlist, self.mca_tech, self.mca_env, self.mca_ecn, self.mca_soc, self.iao_influence/100.0)

                                    tt.CalculateMCAStratScore(blockstrat, [self.bottomlines_tech_w, self.bottomlines_env_w, 
                                          self.bottomlines_ecn_w, self.bottomlines_soc_w])
                                    
                              if len(allInBlockOptions[servicebin]) < 10:         #If there are less than ten options in each bin...
                                    allInBlockOptions[servicebin].append(blockstrat)        #append the current strategy to the list of that bin
                              else:               #Otherwise get bin's lowest score, compare and replace if necessary
                                    lowestscore, lowestscoreindex = self.getServiceBinLowestScore(allInBlockOptions[servicebin])
                                    if blockstrat.getTotalMCAscore() > lowestscore:
                                          allInBlockOptions[servicebin].pop(lowestscoreindex)      #Pop the lowest score and replace
                                          allInBlockOptions[servicebin].append(blockstrat)
                                          #dbs = tt.createDataBaseString(blockstrat)
                                    elif blockstrat.getTotalMCAscore() == lowestscore:
                                          if random.random() > 0.5:   #if the scores are equal: fifty-fifty chance
                                                allInBlockOptions[servicebin].pop(lowestscoreindex)      #Pop the lowest score and replace
                                                allInBlockOptions[servicebin].append(blockstrat)
                                    else:
                                          blockstrat = 0      #set null reference

            return allInBlockOptions

      def getServiceBinLowestScore(self, binlist):
            """Scans none list of BlockStrategies for the lowest MCA total score and returns
            its value as well as the position in the list.
            """
            scorelist = []
            for i in range(len(binlist)):
                  scorelist.append(binlist[i].getTotalMCAscore())
            lowscore = min(scorelist)
            lowscoreindex = scorelist.index(lowscore)
            return lowscore, lowscoreindex

      def getTotalIAOofCombo(self, techarray, lotcounts):
            """Tallies up the total impervious area offset for quantity and quality based on the WSUD objects' individual
            offsets.
            """
            service_abbr = ["Qty", "WQ"]
            offsetmatrix = [0, 0]
            for j in range(len(service_abbr)):
                  abbr = service_abbr[j]
                  for tech in techarray:
                        if tech == 0:
                              continue
                        if tech.getScale() == "L" and tech.getLandUse() == "RES":
                              offsetmatrix[j] += tech.getIAO(abbr) * lotcounts[0]
                        elif tech.getScale() == "L" and tech.getLandUse() == "LI":
                              offsetmatrix[j] += tech.getIAO(abbr) * lotcounts[2]
                        elif tech.getScale() == "L" and tech.getLandUse() == "HI":
                              offsetmatrix[j] += tech.getIAO(abbr) * lotcounts[3]
                        elif tech.getScale() == "L" and tech.getLandUse() == "COM":
                              offsetmatrix[j] += tech.getIAO(abbr) * lotcounts[4]
                        else:
                              offsetmatrix[j] += tech.getIAO(abbr)
            return offsetmatrix

      def getTotalComboService(self, techarray, lotcounts):
            """Retrieves all the impervious area served by an array of systems and returns
            the value"""
            service_abbr = ["Qty", "WQ", "Rec"]
            service_booleans = [int(self.ration_runoff), int(self.ration_pollute), int(self.ration_harvest)]
            servicematrix = [0,0,0]
            for j in range(len(servicematrix)):
                  if service_booleans[j] == 0:        #If not interested in that particular part
                        servicematrix[j] = 0    #Set that service matrix entry to zero and continue
                        continue
                  abbr = service_abbr[j]
                  for tech in techarray:
                        if tech == 0:
                              continue
                        if tech.getScale() == "L" and tech.getLandUse() == "RES":
                              servicematrix[j] += tech.getService(abbr) * lotcounts[0]
                        elif tech.getScale() == "L" and tech.getLandUse() == "LI":
                              servicematrix[j] += tech.getService(abbr) * lotcounts[2]
                        elif tech.getScale() == "L" and tech.getLandUse() == "HI":
                              servicematrix[j] += tech.getService(abbr) * lotcounts[3]
                        elif tech.getScale() == "L" and tech.getLandUse() == "COM":
                              servicematrix[j] += tech.getService(abbr) * lotcounts[4]
                        else:
                              servicematrix[j] += tech.getService(abbr)
            return servicematrix

      def identifyBin(self, servicematrix, AblockEIA, totdemand):
            """Determines what bin to sort a particular service into, used when determining
            which bin a BlockStrategy should go into"""
            if AblockEIA == 0: AblockEIA = 0.0001    #Make infinitesimally small because the only case
            if totdemand == 0: totdemand = 0.0001    #that results from this would be where service == 0

            servicelevels = [servicematrix[0]/AblockEIA, servicematrix[1]/AblockEIA, servicematrix[2]/totdemand]
            #print servicelevels
            bracketwidth = 1.0/float(self.subbas_rigour)   #Used to bin the score within the bracket and penalise MCA score
            blockstratservice = max(servicelevels)
            #print "Maximum service achieved is: "+str(blockstratservice)+" "+str(servicelevels)
            for i in self.subbas_incr:      #[0(skip), 0.25, 0.5, 0.75, 1.0]
                  #Identify Bin using 'less than' rule. Will skip the zero increment bin!
                  #            if blockstratservice < i:   #bins will go from 0 to 0.25, 0.25, to 0.5 etc. (similar for other incr)
                  #                return i
                  #            else:
                  #                continue

                  #Identify Bin using Bracket
                  if blockstratservice >= max((i-(bracketwidth/2)),0) and blockstratservice <= min((i+(bracketwidth/2)),1):
                        #print "Bin: "+str(i)
                        return i
                  else:
                        continue
                  #print "Bin: "+str(max(self.subbas_incr))
            return max(self.subbas_incr)

      ######################################
      #--- GENERATING BASIN REALISATION ---#
      ######################################
      def getBasinBlockIDs(self, currentBasinID):
            """Retrieves all blockIDs within the single basin and returns them in the order
            of upstream to downstream based on the length of the upstream strings."""
            basinblocksortarray = []
            basinblockIDs = []
            outletID = 0
            for currentID in self.blockDict.keys():
                  currentAttList = self.blockDict[currentID]
                  if currentAttList["BasinID"] != currentBasinID:
                        continue
                  else:
                        upstreamIDs = self.retrieveStreamBlockIDs(currentAttList, "upstream")
                        basinblocksortarray.append([len(upstreamIDs),currentID])
                  if currentAttList["Outlet"] == 1:
                        outletID = currentID
            basinblocksortarray.sort()                      #sort ascending based on length of upstream string
            for i in range(len(basinblocksortarray)):
                  basinblockIDs.append(basinblocksortarray[i][1])     #append just the ID of block

            return basinblockIDs, outletID


      def findSubbasinPartakeIDs(self, basinBlockIDs, subbas_options):
            """Searches the blocks within the basin for locations of possible sub-basin scale
            technologies and returns a list of IDs"""
            partake_IDs = []
            for i in range(len(basinBlockIDs)):
                  currentID = int(basinBlockIDs[i])
                  try:
                        if len(subbas_options["BlockID"+str(currentID)]) != 0:
                              partake_IDs.append(currentID)
                        else:
                              continue
                  except KeyError:
                        continue
            return partake_IDs


      def selectTechLocationsByRandom(self, partakeIDs, basinblockIDs):
            """Samples by random a number of sub-basin scale technologies and in-block locations
            for the model to place technologies in, returns two arrays: one of the chosen
            sub-basin IDs and one of the chosen in-block locations"""
            partakeIDsTEMP = []     #Make copies of the arrays to prevent reference-modification
            for i in partakeIDs:
                  partakeIDsTEMP.append(i)
            basinblockIDsTEMP = []
            for i in basinblockIDs:
                  basinblockIDsTEMP.append(i)

            techs_subbas = random.randint(0,len(partakeIDsTEMP))
            subbas_chosenIDs = []
            for j in range(techs_subbas):
                  sample_index = random.randint(0,len(partakeIDsTEMP)-1)
                  subbas_chosenIDs.append(partakeIDsTEMP[sample_index])
                  basinblockIDsTEMP.remove(partakeIDsTEMP[sample_index]) #remove from blocks possibilities
                  partakeIDsTEMP.pop(sample_index)    #pop the value from the partake list

            techs_blocks = random.randint(0, len(basinblockIDsTEMP))
            inblocks_chosenIDs = []
            for j in range(techs_blocks):
                  sample_index = random.randint(0,len(basinblockIDsTEMP)-1)       #If sampling an index, must subtract 1 from len()
                  inblocks_chosenIDs.append(basinblockIDsTEMP[sample_index])
                  basinblockIDsTEMP.pop(sample_index)

            #Reset arrays
            basinblockIDsTEMP = []
            partakeIDsTEMP = []
            return subbas_chosenIDs, inblocks_chosenIDs


      def calculateRemainingService(self, servtype, basinBlockIDs):
            """Assesses the alread treated area/demand for the current basin and returns
            the remaining area/demand to be treated with a strategy.
            - Type: refers to the type of objective "QTY" = quantity, WQ = quality, 
            REC = recycling
            - basinBlockIDs: array containing all IDs within the current basin
            """
            #print basinBlockIDs
            # print "Basin Blocks", basinBlockIDs
            # print servtype
            if servtype in ["WQ", "QTY"]:       #for basin EIA
                  total = self.retrieveAttributeFromIDs(basinBlockIDs, "Manage_EIA", "sum")
            elif servtype in ["REC"]:           #for basin total Demand minus indoor non-res demand
                  total = self.retrieveAttributeFromIDs(basinBlockIDs, "Blk_WD", "sum") - self.retrieveAttributeFromIDs(basinBlockIDs, "wd_Nres_IN", "sum")

            # print "total", total
            # print "Total Imp Area: "+str(total)
            basinTreated = self.retrieveAttributeFromIDs(basinBlockIDs, "Serv"+str(servtype), "sum")
            basinTreated += self.retrieveAttributeFromIDs(basinBlockIDs, "ServUp"+str(servtype), "sum")
            if int(basinTreated) == 0:
                  basinTreated = 0.0

            # print "Treated: ", basinTreated
            # print "Treated ImpArea: "+str(basinTreated)
            rationales = {"QTY": bool(int(self.ration_runoff)), "WQ": bool(int(self.ration_pollute)),
                              "REC": bool(int(self.ration_harvest)) }
            services = {"QTY": float(self.servicevector[0]), "WQ": float(self.servicevector[1]), "REC": float(self.servicevector[2])}

            if rationales[servtype]:
                  basinRemain = max(total - basinTreated, 0)
            else:
                  basinRemain = 0
            # print "Total remaining: ", basinRemain

            if total == 0:
                  prevService = 1
            else:
                  prevService = float(basinTreated)/float(total)

            if max(1- prevService, 0) == 0:
                  delta_percent = 0.0
            else:
                  delta_percent = max(services[servtype]/100.0*rationales[servtype] - prevService,0.0) / (1.0 - prevService)
            return delta_percent, basinRemain, basinTreated, total


      def populateBasinWithTech(self, current_bstrategy, subbas_chosenIDs, inblocks_chosenIDs, 
                              inblock_options, subbas_options, basinBlockIDs):
            """Scans through all blocks within a basin from upstream to downstream end and populates the
            various areas selected in chosenIDs arrays with possible technologies available from the 
            options arrays. Returns an updated current_bstrategy object completed with all details.
            """
            partakeIDs = current_bstrategy.getSubbasPartakeIDs()    #returned in order upstream-->downstream

            #Make a copy of partakeIDs to track blocks
            partakeIDsTracker = []
            for id in partakeIDs:
                  partakeIDsTracker.append(id)

            #Initialize variables to track objective fulfillment
            subbasID_treatedQTY = {}
            subbasID_treatedWQ = {}
            subbasID_treatedREC = {}
            for i in range(len(partakeIDs)):
                  subbasID_treatedQTY[partakeIDs[i]] = 0
                  subbasID_treatedWQ[partakeIDs[i]] = 0
                  subbasID_treatedREC[partakeIDs[i]] = 0

            #Loop across partakeID blocks (i.e. all blocks, which have a precinct tech)
            for i in range(len(partakeIDs)):
                  currentBlockID = partakeIDs[i]      #DENOTES CURRENT POSITION IN THE MAP
                  currentAttList = self.blockDict[currentBlockID]
                  #print "Currently on BlockID: "+str(currentBlockID)

                  upstreamIDs = self.retrieveStreamBlockIDs(currentAttList, "upstream")
                  downstreamIDs = self.retrieveStreamBlockIDs(currentAttList, "downstream")
                  #print "Upstream Blocks: "+str(upstreamIDs)+" downstream Blocks: "+str(downstreamIDs)

                  remainIDs = []    #All blocks upstream of current location that are unique to that location in the sub-basin
                  for b_id in upstreamIDs:
                        remainIDs.append(b_id)

                  #(1) See if there are existing sub-basins inside the current sub-basin
                  subbasinIDs = []            #All blocks that are sub-basins within the subbasin denoted by the current location
                  for b_id in partakeIDsTracker:
                        if b_id in upstreamIDs:
                              subbasinIDs.append(b_id)
                  #print "Subbasins upstream of current location "+str(subbasinIDs)
                  
                  for sbID in subbasinIDs:                  #then loop over the locations found and
                        partakeIDsTracker.remove(sbID)      #remove these from the tracker list so
                                                            #that they are not doubled up
                  
                  for b_id in subbasinIDs:
                        remainIDs.remove(b_id)            #remove the sub-basin ID's ID from remainIDs
                        #upstrIDs = self.retrieveStreamBlockIDs(self.getBlockUUID(id, city), "upstream")
                        upstrIDs = self.retrieveStreamBlockIDs(self.blockDict[b_id], "upstream")
                        for upID in upstrIDs:   #Also remove all sub-basinID's upstream block IDs from
                              remainIDs.remove(upID)   #remain IDs, leaving ONLY Blocks local to currentBlockID
                  #print "Blocks local to current location: "+str(remainIDs)

                  #(2) Obtain highest allowable degree of treatment (Max_Degree)
                  #------- 2.1 Get Total Imp/Dem needing to be treated at the current position
                  upstreamIDs.append(currentBlockID)
                  downstreamIDs.append(currentBlockID)        #Add currentBlockID to the array

                  dp, totalAimpQTY, sv, cp = self.calculateRemainingService("QTY", upstreamIDs)

                  dp, totalAimpWQ, sv, cp = self.calculateRemainingService("WQ", upstreamIDs)

                  #print "Total Quantity Aimp: "+str(totalAimpQTY)
                  #print "Total Water Quality Aimp: "+str(totalAimpWQ)

                  if self.hs_strategy == "ud":
                        dP, totalDemREC, sv,cp = self.calculateRemainingService("REC", downstreamIDs)
                  elif self.hs_strategy == "uu":
                        dP, totalDemREC, sv, cp = self.calculateRemainingService("REC", upstreamIDs)
                  elif self.hs_strategy == "ua":
                        dP, totalDemREC, sv, cp = self.calculateRemainingService("REC", basinBlockIDs)

                  #------- 2.2 Subtract the already serviced parts from upstream sub-basin blocks
                  max_deg_matrix = []
                  subbas_treatedAimpQTY = 0  #Sum of already treated imp area in upstream sub-basins and the now planned treatment
                  subbas_treatedAimpWQ = 0
                  subbas_treatedDemREC = 0

                  for sbID in subbasinIDs:
                        subbas_treatedAimpQTY += subbasID_treatedQTY[sbID]  #Check all upstream sub-basins for their treated Aimp            
                        subbas_treatedAimpWQ += subbasID_treatedWQ[sbID]    #Check all upstream sub-basins for their treated Aimp            

                  #print subbas_treatedAimpQTY
                  #print subbas_treatedAimpWQ

                  remainAimp_subbasinQTY = max(totalAimpQTY - subbas_treatedAimpQTY, 0)
                  if bool(int(self.ration_runoff)) and totalAimpQTY != 0:
                        max_deg_matrix.append(remainAimp_subbasinQTY / totalAimpQTY)
                  #else:
                        #max_deg_matrix.append(0)

                  remainAimp_subbasinWQ = max(totalAimpWQ - subbas_treatedAimpWQ, 0)
                  if bool(int(self.ration_pollute)) and totalAimpWQ != 0:
                        max_deg_matrix.append(remainAimp_subbasinWQ / totalAimpWQ)
                  #else:
                        #max_deg_matrix.append(0)

                  if self.hs_strategy == 'ud':
                        totSupply = 0
                        downstreamIDs = []      #the complete matrix of all downstream IDs from all upstream sbIDs
                        for sbID in subbasinIDs:
                              totSupply += subbasID_treatedREC[sbID]      #Get total supply of all combined upstream systems
                              #downIDs = self.retrieveStreamBlockIDs(self.getBlockUUID(sbID, city), "downstream")
                              downIDs = self.retrieveStreamBlockIDs(self.blockDict[sbID], "downstream")
                              downIDs.append(sbID)
                              for dID in downIDs:
                                    if dID not in downstreamIDs: downstreamIDs.append(dID)
                        #Get all blocks between currentID's upstream and sbIDs downstream blocks
                        shareIDs = []
                        for dID in downstreamIDs:
                              if dID in upstreamIDs and dID not in shareIDs:
                                    shareIDs.append(dID)
                        #Calculate Total Water Demand of Blocks in between the current point and highest upstream point
                        totBetweenDem = self.retrieveAttributeFromIDs(shareIDs, "Blk_WD", "sum") - \
                                    self.retrieveAttributeFromIDs(shareIDs, "wd_Nres_IN", "sum")
                        #Remaining demand is total downstream demand minus the higher of (total upstream supply excess and zero)
                        remainDem_subbasinRec = totalDemREC - max(totSupply - totBetweenDem, 0)
                  elif self.hs_strategy in ['uu', 'ua']:
                        for sbID in subbasinIDs:
                              subbas_treatedDemREC += subbasID_treatedREC[sbID]
                        remainDem_subbasinRec = max(totalDemREC - subbas_treatedDemREC, 0)

                  if bool(int(self.ration_harvest)) and totalDemREC != 0:
                        max_deg_matrix.append(remainDem_subbasinRec / totalDemREC)
                  #else:
                        #max_deg_matrix.append(0)

                  # print "Max_deg_matrix", max_deg_matrix
                  # print "Max Degre matrix: "+str(max_deg_matrix)
                  max_degree = min(max_deg_matrix)+float(self.service_redundancy/100.0)  #choose the minimum, bring in allowance using redundancy parameter

                  current_bstrategy.addSubBasinInfo(currentBlockID, upstreamIDs, subbasinIDs, [totalAimpQTY,totalAimpWQ,totalDemREC])
                  #print [totalAimpQTY,totalAimpWQ,totalDemREC]
                  #print "Current State of Treatment: "+str([subbas_treatedAimpQTY, subbas_treatedAimpWQ, subbas_treatedDemREC])

                  #(3) PICK A SUB-BASIN TECHNOLOGY
                  if currentBlockID in subbas_chosenIDs:
                        deg, obj, treatedQTY, treatedWQ, treatedREC, iaoqty, iaowq = self.pickOption(currentBlockID, max_degree, subbas_options, [totalAimpQTY, totalAimpWQ, totalDemREC], "SB")
                        #print "Option Treats: "+str([treatedQTY, treatedWQ, treatedREC])
                        #print obj

                        subbas_treatedAimpQTY += treatedQTY + iaoqty
                        subbas_treatedAimpWQ += treatedWQ + iaowq
                        subbas_treatedDemREC += treatedREC
                        remainAimp_subbasinQTY = max(remainAimp_subbasinQTY - treatedQTY, 0)
                        remainAimp_subbasinWQ = max(remainAimp_subbasinWQ - treatedWQ, 0)
                        remainDem_subbasinRec = max(remainDem_subbasinRec - treatedREC, 0)
                        #print "Remaining: "+str([remainAimp_subbasinQTY, remainAimp_subbasinWQ, remainDem_subbasinRec])
                        if deg != 0 and obj != 0:
                              current_bstrategy.appendTechnology(currentBlockID, deg, obj, "s")

                  #(4) PICK AN IN-BLOCK STRATEGY IF IT IS HAS BEEN CHOSEN
                  for rbID in remainIDs:
                        if rbID not in inblocks_chosenIDs:        #If the Block ID hasn't been chosen,
                              #print "rbID not in inblocks_chosenIDs"
                              continue                            #then skip to next one, no point otherwise

                        max_deg_matrix = [1]
                        block_Aimp = self.blockDict[rbID]["Manage_EIA"]
                        block_Dem = self.blockDict[rbID]["Blk_WD"] - self.blockDict[rbID]["wd_Nres_IN"]
                        #print "Block details: "+str(block_Aimp)+" "+str(block_Dem)
                        if block_Aimp == 0:     #Impervious governs pretty much everything, if it is zero, don't even bother
                              continue
                        if block_Dem == 0 and bool(int(self.ration_harvest)):   #If demand is zero and we are planning for recycling, skip
                              continue
                        #print "Can select a block option for current Block"

                        if bool(int(self.ration_runoff)):
                              max_deg_matrix.append(remainAimp_subbasinQTY/block_Aimp)
                        if bool(int(self.ration_pollute)):
                              max_deg_matrix.append(remainAimp_subbasinWQ/block_Aimp)
                        if bool(int(self.ration_harvest)):
                              max_deg_matrix.append(remainDem_subbasinRec/block_Dem)
                        #print "Block Degrees: "+str(max_deg_matrix)
                        max_degree = min(max_deg_matrix) + float(self.service_redundancy/100)
                        #print str([block_Aimp*int(self.ration_runoff))+" "+str(block_Aimp*int(self.ration_pollute))+" "+str(block_Dem*int(self.ration_harvest)])

                        #print "In Block Maximum Degree: "+str(max_degree)
                        deg, obj, treatedQTY, treatedWQ, treatedREC, iaoqty, iaowq = self.pickOption(rbID,max_degree,inblock_options, [block_Aimp*bool(int(self.ration_runoff)), block_Aimp*bool(int(self.ration_pollute)), block_Dem*bool(int(self.ration_harvest))], "BS")
                        #print "Option Treats: "+str([treatedQTY, treatedWQ, treatedREC])
                        #print obj

                        subbas_treatedAimpQTY += treatedQTY + iaoqty
                        subbas_treatedAimpWQ += treatedWQ + iaowq
                        subbas_treatedDemREC += treatedREC
                        remainAimp_subbasinQTY = max(remainAimp_subbasinQTY - treatedQTY, 0)
                        remainAimp_subbasinWQ = max(remainAimp_subbasinWQ - treatedWQ, 0)
                        remainDem_subbasinRec = max(remainDem_subbasinRec - treatedREC, 0)
                        #print "Remaining: "+str([remainAimp_subbasinQTY, remainAimp_subbasinWQ, remainDem_subbasinRec])
                        if deg != 0 and obj != 0:
                              current_bstrategy.appendTechnology(rbID, deg, obj, "b")

                  #(5) FINALIZE THE SERVICE VALUES FOR QTY, WQ, REC BEFORE NEXT LOOP
                  #Impervious area offset will result in options going over treatment threshold.
                  subbasID_treatedQTY[currentBlockID] = subbas_treatedAimpQTY #min(subbas_treatedAimpQTY, totalAimpQTY)
                  subbasID_treatedWQ[currentBlockID] = subbas_treatedAimpWQ #min(subbas_treatedAimpWQ, totalAimpWQ)
                  subbasID_treatedREC[currentBlockID] = min(subbas_treatedDemREC, totalDemREC)
                  #print subbasID_treatedQTY
                  #print subbasID_treatedWQ
            return True

      #################################################
      #--- RANKING AND CHOOSING BASIN REALISATIONS ---#
      #################################################
      def evaluateServiceObjectiveFunction(self, basinstrategy, updatedservice):
            """Calculates how close the basinstrategy meets the required service
            levels set by the user. A performance metric is returned. If one of the
            service levels has not been met, performance is automatically assigned
            a value of -1. It will then be removed in the main program.
            The objective function used to find the optimum strategies is calculated
            as:
            choice = min { sum(serviceProvided - serviceRequired) }, OF >0
            updatedservice = [serviceQty, serviceWQ, serviceREC] based on delta_percent
            """
            serviceQty = float(int(self.ration_runoff))*float(updatedservice[0])
            serviceWQ = float(int(self.ration_pollute))*float(updatedservice[1])
            serviceRec = float(int(self.ration_harvest))*float(updatedservice[2])
            serviceRequired = [serviceQty, serviceWQ, serviceRec]
            serviceBooleans = [int(self.ration_runoff), int(self.ration_pollute), int(self.ration_harvest)]

            serviceProvided = basinstrategy.getServicePvalues() #[0,0,0] P values for service
            for i in range(len(serviceProvided)):
                  serviceProvided[i] *= float(serviceBooleans[i])     #Rescale to ensure no service items are zero
            #print "Service Req "+str(serviceProvided)
            #print "Service Provided "+str(serviceRequired)
            
            #Objective Criterion: A strategy is most suitable to the user's input
            #requirements if the sum(service-provided - service-required) is a minimum
            #and >0
            negative = False
            performance = 0
            for i in range(len(serviceProvided)):
                  performance += (serviceProvided[i] - serviceRequired[i])
                  if (serviceProvided[i] - serviceRequired[i]) < 0:
                        negative = True
            if negative:
                  performance = -1       #One objective at least, not fulfilled
            return performance

      def pickOption(self, blockID, max_degree, options_collection, totals, strattype):
            """Picks and returns a random option based on the input impervious area and maximum
            treatment degree. Can be used on either the in-block strategies or larger precinct 
            strategies. If it cannot pick anything, it will return zeros all around."""
            bracketwidth = 1.0/float(self.subbas_rigour)    #Use bracket to determine optimum bin

            #print options_collection["BlockID"+str(blockID)]
            if strattype == "BS":   #in-block strategy
                  options = []

                  #Continuous-based picking
                  for i in options_collection["BlockID"+str(blockID)].keys():
                        if (i-bracketwidth/2) >= max_degree:                
                              continue
                        for j in options_collection["BlockID"+str(blockID)][i]:
                              options.append(j)

                  #Bin-based picking
                  #            degs = []   #holds all the possible increments within max_degree
                  #            for i in options_collection["BlockID"+str(blockID)].keys():
                  #                if (i-bracketwidth/2) <= max_degree:                
                  #                    degs.append(i)  #add as a possible increment
                  #            if len(degs) != 0:
                  #                chosen_deg = degs[random.randint(0, len(degs)-1)]
                  #                for j in options_collection["BlockID"+str(blockID)][chosen_deg]:
                  #                    options.append(j)

                  if len(options) == 0:
                        return 0, 0, 0, 0, 0, 0, 0
                  scores = []
                  for i in options:
                        scores.append(i.getTotalMCAscore())

                  #print "Scores: "+str(scores)

                  #Pick Option
                  scores = self.createCDF(scores)
                  #print "Scores CDF: "+str(scores)
                  choice = self.samplefromCDF(scores)
                  #print choice
                  chosen_obj = options[choice]

                  #            AimpQTY = totals[0]
                  #            AimpWQ = totals[1]
                  #            DemREC = totals[2]
                  #            treatedAimpQTY = chosen_deg * AimpQTY
                  #            treatedAimpWQ = chosen_deg * AimpWQ
                  #            treatedDemREC = chosen_deg * DemREC            
                  treatedAimpQTY = chosen_obj.getService("Qty")
                  iaoqty = chosen_obj.getIAO("Qty")
                  treatedAimpWQ = chosen_obj.getService("WQ")
                  iaowq = chosen_obj.getIAO("WQ")
                  treatedDemREC = chosen_obj.getService("Rec")
                  return chosen_obj.getBlockBin(), chosen_obj, treatedAimpQTY, treatedAimpWQ, treatedDemREC, iaoqty, iaowq

            elif strattype == "SB":  #sub-basin strategy
                  #Continuous-based picking
                  options = []
                  for deg in self.subbas_incr:
                        if(deg-bracketwidth/2) >= max_degree:
                              continue
                        for j in options_collection["BlockID"+str(blockID)][deg]:
                              options.append(j)

                  if len(options) != 0:
                        chosen_obj = options[random.randint(0, len(options)-1)]

                  #Bin-based picking
                  #            AimpQTY = totals[0]
                  #            AimpWQ = totals[1]
                  #            DemREC = totals[2]
                  #            indices = []
                  #            for deg in self.subbas_incr:
                  #                if (deg-bracketwidth/2) <= max_degree:
                  #                    indices.append(deg)
                  #            if len(indices) != 0:
                  #                choice = random.randint(0, len(indices)-1)
                  #                chosen_deg = self.subbas_incr[choice]
                  #            else:
                  #                return 0, 0, 0, 0, 0
                  #            
                  #            Nopt = len(options_collection["BlockID"+str(blockID)][chosen_deg])
                  #            
                  #            if Nopt != 0:
                  #            #if chosen_deg != 0 and Nopt != 0:
                  ##                treatedAimpQTY = chosen_deg * AimpQTY
                  ##                treatedAimpWQ = chosen_deg * AimpWQ
                  ##                treatedDemREC = chosen_deg * DemREC
                  #                choice = random.randint(0, Nopt-1)
                  #                chosen_obj = options_collection["BlockID"+str(blockID)][chosen_deg][choice]
                  #                
                  if chosen_obj == 0:
                        return 0, 0, 0, 0, 0, 0, 0
                  chosen_deg = chosen_obj.getDesignIncrement()
                  treatedAimpQTY = chosen_obj.getService("Qty")
                  iaoqty = chosen_obj.getIAO("Qty")
                  treatedAimpWQ = chosen_obj.getService("WQ")
                  iaowq = chosen_obj.getIAO("WQ")
                  treatedDemREC = chosen_obj.getService("Rec")

                  return chosen_deg, chosen_obj, treatedAimpQTY, treatedAimpWQ, treatedDemREC, iaoqty, iaowq
            else:
                  return 0, 0, 0, 0, 0, 0, 0

      def createCDF(self, score_matrix):
            """Creates a cumulative distribution for an input list of values by normalizing
            these first and subsequently summing probabilities.
            """
            pdf = []
            cdf = []
            for i in range(len(score_matrix)):
                  if sum(score_matrix) == 0:
                        pdf.append(1.0/float(len(score_matrix)))
                  else:
                        pdf.append(score_matrix[i]/sum(score_matrix))
            cumu_p = 0
            for i in range(len(pdf)):
                  cumu_p += pdf[i]
                  cdf.append(cumu_p)
            cdf[len(cdf)-1] = 1.0   #Adjust for rounding errors
            return cdf

      def samplefromCDF(self, selection_cdf):
            """Samples one sample from a cumulative distribution function and returns
            the index. Sampling is uniform, probabilities are determined by the CDF"""
            p_sample = random.random()
            for i in range(len(selection_cdf)):
                  if p_sample <= selection_cdf[i]:
                        return i
            return (len(selection_cdf)-1)