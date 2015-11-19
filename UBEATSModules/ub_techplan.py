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
            self.ration_runoff = 0                #Design for flood mitigation?
            self.ration_pollute = 1               #Design for pollution management?
            self.ration_harvest = 0              #Design for harvesting & reuse? Adds storage-sizing to certain systems
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
            self.targets_runoff = 80.0            #Runoff reduction target [%]
            self.targets_TSS = 70.0               #TSS Load reduction target [%]
            self.targets_TP = 30.0                #TP Load reduction target [%]
            self.targets_TN = 30.0                #TN Load reduction target [%]
            self.targets_reliability = 80.0       #required reliability of harvesting systems

            self.system_tarQ = 0            #INITIALIZE THESE VARIABLES
            self.system_tarTSS = 0
            self.system_tarTP = 0
            self.system_tarTN = 0
            self.system_tarREL = 0
            self.targetsvector = []         #---CALCULATED IN THE FIRST LINE OF RUN()

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
            self.strategy_lot_check = 1
            self.strategy_street_check = 1
            self.strategy_neigh_check = 1
            self.strategy_subbas_check = 1
            self.lot_rigour = 4.0
            self.street_rigour = 4.0
            self.neigh_rigour = 4.0
            self.subbas_rigour = 4.0

            #ADDITIONAL STRATEGIES
            self.createParameter("scalepref", DOUBLE,"")
            self.scalepref = 3  #Ranges from 1 (high priority on at-source) to 5 (high priority on end-of-pipe)

            self.scalingprefmatrix = [{"L":0.40, "S":0.30, "N":0.20, "B":0.10},
                                  {"L":0.25, "S":0.35, "N":0.25, "B":0.15},
                                  {"L":0.25, "S":0.25, "N":0.25, "B":0.25},
                                  {"L":0.15, "S":0.25, "N":0.35, "B":0.25},
                                  {"L":0.10, "S":0.20, "N":0.30, "B":0.40},]
            self.curscalepref = {"L":0.25, "S":0.25, "N":0.25, "B":0.25}

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
            self.scoringmatrix_default = 0

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
            self.rainfile = ""
            self.createParameter("rain_dt", DOUBLE, "")
            self.rain_dt = 6        #[mins]
            self.createParameter("evapfile", STRING, "")
            self.evapfile = ""
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
                    "SVU_avOTH", "RoadTIA", "RD_av", "RDMedW", "DemPublicI", "HouseOccup", 
                    "avSt_RES", "WResNstrip", "ResAllots", "ResDWpLot", "ResHouses", "ResLotArea", 
                    "ResRoof", "avLt_RES", "ResLotTIA", "ResLotEIA", "ResGarden", "DemPrivI", 
                    "ResRoofCon", "HDRFlats", "HDRRoofA", "HDROccup", "HDR_TIA", "HDR_EIA", 
                    "HDRFloors", "av_HDRes", "HDRGarden", "HDRCarPark", "DemAptI", "LIjobs", 
                    "LIestates", "avSt_LI", "LIAfront", "LIAfrEIA", "LIAestate", "LIAeBldg", 
                    "LIFloors", "LIAeLoad", "LIAeCPark", "avLt_LI", "LIAeLgrey", "LIAeEIA", 
                    "LIAeTIA", "COMjobs", "COMestates", "avSt_COM", "COMAfront", "COMAfrEIA", 
                    "COMAestate", "COMAeBldg", "COMFloors", "COMAeLoad", "COMAeCPark", "avLt_COM", 
                    "COMAeLgrey", "COMAeEIA", "COMAeTIA", "Blk_TIA", "Blk_EIA", "Blk_EIF", 
                    "Blk_TIF", "Blk_RoofsA", "wd_PrivIN", "wd_PrivOUT", "wd_Nres_IN", "Apub_irr", 
                    "wd_PubOUT", "Blk_WD", "Blk_Kitch", "Blk_Shower", "Blk_Toilet", "Blk_Laund", 
                    "Blk_Garden", "Blk_Com", "Blk_Ind", "Blk_PubIrr"]

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
            self.blockdata.addAttribute("HouseOccup", DOUBLE, READ)
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

            views = []
            views.append(self.regiondata)
            views.append(self.blockdata)
            self.registerViewContainers(views)


      def run(self):
            #-------------------------------------------------------------------------------------------------------
            #Retrieve data to work with - NOTE THIS NEEDS TO BE REPLACED WITH WHATEVER DAnCE wants to implement
            self.regiondata.reset_reading()
            
            for r in self.regiondata:
                  mapdata = r

            numblocks = mapdata.GetFieldAsInteger("NumBlocks")

            blockDict = {}

            self.blockdata.reset_reading()
            for block in self.blockdata:
                  curID = block.GetFieldAsInteger("BlockID")
                  print curID
                  blockDict[curID] = {}
                  for key in self.attnames:
                        blockDict[curID][key] = block.GetFieldAsDouble(key)
            #End Result is a dictionary of dictionaries. Each key in the outer dictionary represents a BlocKID, each 
            #key in the inner dictionary represents the attributes of that block
            #---------------------------------------------------------------------------------------------------------


            



