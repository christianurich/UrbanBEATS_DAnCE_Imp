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
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
"""

from pydynamind import *

#TESTFILE = "C:/Users/Peter Bach/Documents/Coding Projects/UrbanBEATS_DAnCE_Imp/Test Data/caseyclyde_500m_testdata.csv" #Mabook Path
TESTFILE = "D:/Coding Projects/UrbanBEATS_DAnCE_Imp/Test Data/caseyclyde_500m_testdata.csv" #Office Path

class UB_TranslateBlockData(Module):

        def __init__(self):
            Module.__init__(self)

            #To use the GDAL API
            self.setIsGDALModule(True)

            #Parameter Definition
            self.createParameter("fullfilepath", STRING, "Path to test .csv file")
            #self.fullfilepath = "C:/Users/Peter Bach/Dropbox/Documents RESEARCH/Current Projects/CRC Water Sensitive Cities/A4.3 DAnCE4Water/DAnCE x UrbanBEATS Module/Verification/Casey Clyde Test 1/caseyClydeTest1.csv"
            self.fullfilepath = "C:/Users/petermbach/Dropbox/Documents RESEARCH/Current Projects/CRC Water Sensitive Cities/A4.3 DAnCE4Water/DAnCE x UrbanBEATS Module/Verification/filename.csv"

            # self.attnames = ["BlockID", "BasinID", "Status", "Active", "Nhd_N", "Nhd_S",
            #         "Nhd_W", "Nhd_E", "Nhd_NE", "Nhd_NW", "Nhd_SE", "Nhd_SW", "Soil_k",
            #         "AvgElev", "pLU_RES", "pLU_COM", "pLU_LI", "pLU_CIV", "pLU_SVU",
            #         "pLU_RD", "pLU_TR", "pLU_PG", "pLU_REF", "pLU_UND", "pLU_NA", "Pop",
            #         "downID", "Outlet", "MiscAtot", "OpenSpace", "AGardens", "ASquare",
            #         "PG_av", "REF_av", "ANonW_Util", "SVU_avWS", "SVU_avWW", "SVU_avSW",
            #         "SVU_avOTH", "RoadTIA", "RD_av", "RDMedW", "DemPublicI", "HouseOccup", "ResFrontT",
            #         "avSt_RES", "WResNstrip", "ResAllots", "ResDWpLot", "ResHouses", "ResLotArea",
            #         "ResRoof", "avLt_RES", "ResLotTIA", "ResLotEIA", "ResGarden", "DemPrivI",
            #         "ResRoofCon", "HDRFlats", "HDRRoofA", "HDROccup", "HDR_TIA", "HDR_EIA",
            #         "HDRFloors", "av_HDRes", "HDRGarden", "HDRCarPark", "DemAptI", "LIjobs",
            #         "LIestates", "avSt_LI", "LIAfront", "LIAfrEIA", "LIAestate", "LIAeBldg",
            #         "LIFloors", "LIAeLoad", "LIAeCPark", "avLt_LI", "LIAeLgrey", "LIAeEIA", "LIAeTIA",
            #         "HIjobs", "HIestates", "avSt_HI", "HIAfront", "HIAfrEIA", "HIAestate", "HIAeBldg",
            #         "HIFloors", "HIAeLoad", "HIAeCPark", "avLt_HI", "HIAeLgrey", "HIAeEIA", "HIAeTIA",
            #         "ORCjobs", "ORCestates", "avSt_ORC", "ORCAfront", "ORCAfrEIA", "ORCAestate", "ORCAeBldg",
            #         "ORCFloors", "ORCAeLoad", "ORCAeCPark", "avLt_ORC", "ORCAeLgrey", "ORCAeEIA", "ORCAeTIA",
            #         "COMjobs", "COMestates", "avSt_COM", "COMAfront", "COMAfrEIA",
            #         "COMAestate", "COMAeBldg", "COMFloors", "COMAeLoad", "COMAeCPark", "avLt_COM",
            #         "COMAeLgrey", "COMAeEIA", "COMAeTIA", "Blk_TIA", "Blk_EIA", "Blk_EIF",
            #         "Blk_TIF", "Blk_RoofsA", "wd_PrivIN", "wd_PrivOUT", "wd_Nres_IN", "Apub_irr",
            #         "wd_PubOUT", "Blk_WD", "Blk_Kitch", "Blk_Shower", "Blk_Toilet", "Blk_Laund",
            #         "Blk_Garden", "Blk_Com", "Blk_Ind", "Blk_PubIrr"]

            self.attnames = ["av_HDRes","avLt_COM","avLt_HI","avLt_LI","avLt_RES",
                            "avSt_RES","BasinID","Blk_EIA","Blk_WD","BlockID",
                            "COMAeEIA","COMestates","downID","HDRFlats", "HDR_EIA",
                            "HDRRoofA","HIAeEIA","HIestates","LIAeEIA","LIestates",
                            "Outlet","PG_av","REF_av","ResAllots","ResFrontT",
                            "ResHouses","ResLotEIA","ResRoof","Soil_k","Status",
                            "SVU_avSW","SVU_avWS","SVU_avWW","wd_HDR_I","wd_HDR_K",
                            "wd_HDR_L","wd_HDR_S","wd_HDR_T","wd_Nres_IN","wd_PubOUT",
                            "wd_RES_I","wd_RES_K","wd_RES_L","wd_RES_S","wd_RES_T"]

        def init(self):

            #Data Stream Definition
            self.regiondata = ViewContainer("regiondata", COMPONENT, WRITE)
            self.regiondata.addAttribute("NumBlocks", DOUBLE, WRITE)
            self.regiondata.addAttribute("TotalBasins", DOUBLE, WRITE)

            self.blockdata = ViewContainer("blockdata", COMPONENT, WRITE)
            self.blockdata.addAttribute("BlockID", DOUBLE, WRITE)
            self.blockdata.addAttribute("BasinID", DOUBLE, WRITE)
            self.blockdata.addAttribute("Status", DOUBLE, WRITE)
            # self.blockdata.addAttribute("Active", DOUBLE, WRITE)
            # self.blockdata.addAttribute("Nhd_N", DOUBLE, WRITE)
            # self.blockdata.addAttribute("Nhd_S", DOUBLE, WRITE)
            # self.blockdata.addAttribute("Nhd_W", DOUBLE, WRITE)
            # self.blockdata.addAttribute("Nhd_E", DOUBLE, WRITE)
            # self.blockdata.addAttribute("Nhd_NE", DOUBLE, WRITE)
            # self.blockdata.addAttribute("Nhd_NW", DOUBLE, WRITE)
            # self.blockdata.addAttribute("Nhd_SE", DOUBLE, WRITE)
            # self.blockdata.addAttribute("Nhd_SW", DOUBLE, WRITE)
            self.blockdata.addAttribute("Soil_k", DOUBLE, WRITE)
            # self.blockdata.addAttribute("AvgElev", DOUBLE, WRITE)
            # self.blockdata.addAttribute("pLU_RES", DOUBLE, WRITE)
            # self.blockdata.addAttribute("pLU_COM", DOUBLE, WRITE)   #commercial & offices
            # self.blockdata.addAttribute("pLU_LI", DOUBLE, WRITE)    #light & heavy industry
            # self.blockdata.addAttribute("pLU_CIV", DOUBLE, WRITE)
            # self.blockdata.addAttribute("pLU_SVU", DOUBLE, WRITE)
            # self.blockdata.addAttribute("pLU_RD", DOUBLE, WRITE)
            # self.blockdata.addAttribute("pLU_TR", DOUBLE, WRITE)
            # self.blockdata.addAttribute("pLU_PG", DOUBLE, WRITE)
            # self.blockdata.addAttribute("pLU_REF", DOUBLE, WRITE)
            # self.blockdata.addAttribute("pLU_UND", DOUBLE, WRITE)
            # self.blockdata.addAttribute("pLU_NA", DOUBLE, WRITE)
            # self.blockdata.addAttribute("Pop", DOUBLE, WRITE)
            self.blockdata.addAttribute("downID", DOUBLE, WRITE)
            self.blockdata.addAttribute("Outlet", DOUBLE, WRITE)
            # self.blockdata.addAttribute("MiscAtot", DOUBLE, WRITE)
            # self.blockdata.addAttribute("OpenSpace", DOUBLE, WRITE)
            # self.blockdata.addAttribute("AGardens", DOUBLE, WRITE)
            # self.blockdata.addAttribute("ASquare", DOUBLE, WRITE)
            self.blockdata.addAttribute("PG_av", DOUBLE, WRITE)
            self.blockdata.addAttribute("REF_av", DOUBLE, WRITE)
            # self.blockdata.addAttribute("ANonW_Util", DOUBLE, WRITE)
            self.blockdata.addAttribute("SVU_avWS", DOUBLE, WRITE)
            self.blockdata.addAttribute("SVU_avWW", DOUBLE, WRITE)
            self.blockdata.addAttribute("SVU_avSW", DOUBLE, WRITE)
            self.blockdata.addAttribute("SVU_avOTH", DOUBLE, WRITE)
            # self.blockdata.addAttribute("RoadTIA", DOUBLE, WRITE)
            # self.blockdata.addAttribute("RD_av", DOUBLE, WRITE)
            # self.blockdata.addAttribute("RDMedW", DOUBLE, WRITE)
            # self.blockdata.addAttribute("DemPublicI", DOUBLE, WRITE)
            self.blockdata.addAttribute("HasRes", DOUBLE, WRITE)
            self.blockdata.addAttribute("HasHouses", DOUBLE, WRITE)
            # self.blockdata.addAttribute("HouseOccup", DOUBLE, WRITE)
            self.blockdata.addAttribute("ResFrontT", DOUBLE, WRITE)
            self.blockdata.addAttribute("avSt_RES", DOUBLE, WRITE)
            # self.blockdata.addAttribute("WResNstrip", DOUBLE, WRITE)
            self.blockdata.addAttribute("ResAllots", DOUBLE, WRITE)
            # self.blockdata.addAttribute("ResDWpLot", DOUBLE, WRITE)
            self.blockdata.addAttribute("ResHouses", DOUBLE, WRITE)
            # self.blockdata.addAttribute("ResLotArea", DOUBLE, WRITE)
            # self.blockdata.addAttribute("ResRoof", DOUBLE, WRITE)
            self.blockdata.addAttribute("avLt_RES", DOUBLE, WRITE)
            # self.blockdata.addAttribute("ResLotTIA", DOUBLE, WRITE)
            self.blockdata.addAttribute("ResLotEIA", DOUBLE, WRITE)
            # self.blockdata.addAttribute("ResGarden", DOUBLE, WRITE)
            # self.blockdata.addAttribute("DemPrivI", DOUBLE, WRITE)
            # self.blockdata.addAttribute("ResRoofCon", DOUBLE, WRITE)
            self.blockdata.addAttribute("HasFlats", DOUBLE, WRITE)
            self.blockdata.addAttribute("HDRFlats", DOUBLE, WRITE)
            self.blockdata.addAttribute("HDRRoofA", DOUBLE, WRITE)
            # self.blockdata.addAttribute("HDROccup", DOUBLE, WRITE)
            # self.blockdata.addAttribute("HDR_TIA", DOUBLE, WRITE)
            self.blockdata.addAttribute("HDR_EIA", DOUBLE, WRITE)
            # self.blockdata.addAttribute("HDRFloors", DOUBLE, WRITE)
            self.blockdata.addAttribute("av_HDRes", DOUBLE, WRITE)
            # self.blockdata.addAttribute("HDRGarden", DOUBLE, WRITE)
            # self.blockdata.addAttribute("HDRCarPark", DOUBLE, WRITE)
            # self.blockdata.addAttribute("DemAptI", DOUBLE, WRITE)
            self.blockdata.addAttribute("Has_LI", DOUBLE, WRITE)
            # self.blockdata.addAttribute("LIjobs", DOUBLE, WRITE)
            self.blockdata.addAttribute("LIestates", DOUBLE, WRITE)
            # self.blockdata.addAttribute("avSt_LI", DOUBLE, WRITE)
            # self.blockdata.addAttribute("LIAfront", DOUBLE, WRITE)
            # self.blockdata.addAttribute("LIAfrEIA", DOUBLE, WRITE)
            # self.blockdata.addAttribute("LIAestate", DOUBLE, WRITE)
            # self.blockdata.addAttribute("LIAeBldg", DOUBLE, WRITE)
            # self.blockdata.addAttribute("LIFloors", DOUBLE, WRITE)
            # self.blockdata.addAttribute("LIAeLoad", DOUBLE, WRITE)
            # self.blockdata.addAttribute("LIAeCPark", DOUBLE, WRITE)
            self.blockdata.addAttribute("avLt_LI", DOUBLE, WRITE)
            # self.blockdata.addAttribute("LIAeLgrey", DOUBLE, WRITE)
            self.blockdata.addAttribute("LIAeEIA", DOUBLE, WRITE)
            # self.blockdata.addAttribute("LIAeTIA", DOUBLE, WRITE)
            self.blockdata.addAttribute("Has_HI", DOUBLE, WRITE)
            # self.blockdata.addAttribute("HIjobs", DOUBLE, WRITE)
            self.blockdata.addAttribute("HIestates", DOUBLE, WRITE)
            # self.blockdata.addAttribute("avSt_HI", DOUBLE, WRITE)
            # self.blockdata.addAttribute("HIAfront", DOUBLE, WRITE)
            # self.blockdata.addAttribute("HIAfrEIA", DOUBLE, WRITE)
            # self.blockdata.addAttribute("HIAestate", DOUBLE, WRITE)
            # self.blockdata.addAttribute("HIAeBldg", DOUBLE, WRITE)
            # self.blockdata.addAttribute("HIFloors", DOUBLE, WRITE)
            # self.blockdata.addAttribute("HIAeLoad", DOUBLE, WRITE)
            # self.blockdata.addAttribute("HIAeCPark", DOUBLE, WRITE)
            self.blockdata.addAttribute("avLt_HI", DOUBLE, WRITE)
            # self.blockdata.addAttribute("HIAeLgrey", DOUBLE, WRITE)
            self.blockdata.addAttribute("HIAeEIA", DOUBLE, WRITE)
            # self.blockdata.addAttribute("HIAeTIA", DOUBLE, WRITE)
            self.blockdata.addAttribute("Has_Com", DOUBLE, WRITE)
            # self.blockdata.addAttribute("COMjobs", DOUBLE, WRITE)
            self.blockdata.addAttribute("COMestates", DOUBLE, WRITE)
            # self.blockdata.addAttribute("avSt_COM", DOUBLE, WRITE)
            # self.blockdata.addAttribute("COMAfront", DOUBLE, WRITE)
            # self.blockdata.addAttribute("COMAfrEIA", DOUBLE, WRITE)
            # self.blockdata.addAttribute("COMAestate", DOUBLE, WRITE)
            # self.blockdata.addAttribute("COMAeBldg", DOUBLE, WRITE)
            # self.blockdata.addAttribute("COMFloors", DOUBLE, WRITE)
            # self.blockdata.addAttribute("COMAeLoad", DOUBLE, WRITE)
            # self.blockdata.addAttribute("COMAeCPark", DOUBLE, WRITE)
            self.blockdata.addAttribute("avLt_COM", DOUBLE, WRITE)
            # self.blockdata.addAttribute("COMAeLgrey", DOUBLE, WRITE)
            self.blockdata.addAttribute("COMAeEIA", DOUBLE, WRITE)
            # self.blockdata.addAttribute("COMAeTIA", DOUBLE, WRITE)
            # self.blockdata.addAttribute("Has_ORC", DOUBLE, WRITE)
            # self.blockdata.addAttribute("ORCjobs", DOUBLE, WRITE)
            # self.blockdata.addAttribute("ORCestates", DOUBLE, WRITE)
            # self.blockdata.addAttribute("avSt_ORC", DOUBLE, WRITE)
            # self.blockdata.addAttribute("ORCAfront", DOUBLE, WRITE)
            # self.blockdata.addAttribute("ORCAfrEIA", DOUBLE, WRITE)
            # self.blockdata.addAttribute("ORCAestate", DOUBLE, WRITE)
            # self.blockdata.addAttribute("ORCAeBldg", DOUBLE, WRITE)
            # self.blockdata.addAttribute("ORCFloors", DOUBLE, WRITE)
            # self.blockdata.addAttribute("ORCAeLoad", DOUBLE, WRITE)
            # self.blockdata.addAttribute("ORCAeCPark", DOUBLE, WRITE)
            # self.blockdata.addAttribute("avLt_ORC", DOUBLE, WRITE)
            # self.blockdata.addAttribute("ORCAeLgrey", DOUBLE, WRITE)
            # self.blockdata.addAttribute("ORCAeEIA", DOUBLE, WRITE)
            # self.blockdata.addAttribute("ORCAeTIA", DOUBLE, WRITE)
            # self.blockdata.addAttribute("Blk_TIA", DOUBLE, WRITE)
            self.blockdata.addAttribute("Blk_EIA", DOUBLE, WRITE)
            # self.blockdata.addAttribute("Blk_EIF", DOUBLE, WRITE)
            # self.blockdata.addAttribute("Blk_TIF", DOUBLE, WRITE)
            # self.blockdata.addAttribute("Blk_RoofsA", DOUBLE, WRITE)
            # self.blockdata.addAttribute("wd_PrivIN", DOUBLE, WRITE)
            # self.blockdata.addAttribute("wd_PrivOUT", DOUBLE, WRITE)
            self.blockdata.addAttribute("wd_Nres_IN", DOUBLE, WRITE)
            # self.blockdata.addAttribute("Apub_irr", DOUBLE, WRITE)
            self.blockdata.addAttribute("wd_PubOUT", DOUBLE, WRITE)
            self.blockdata.addAttribute("wd_RES_K", DOUBLE, WRITE)
            self.blockdata.addAttribute("wd_RES_S", DOUBLE, WRITE)
            self.blockdata.addAttribute("wd_RES_T", DOUBLE, WRITE)
            self.blockdata.addAttribute("wd_RES_L", DOUBLE, WRITE)
            self.blockdata.addAttribute("wd_RES_I", DOUBLE, WRITE)
            self.blockdata.addAttribute("wd_HDR_K", DOUBLE, WRITE)
            self.blockdata.addAttribute("wd_HDR_S", DOUBLE, WRITE)
            self.blockdata.addAttribute("wd_HDR_T", DOUBLE, WRITE)
            self.blockdata.addAttribute("wd_HDR_L", DOUBLE, WRITE)
            self.blockdata.addAttribute("wd_HDR_I", DOUBLE, WRITE)
            self.blockdata.addAttribute("Blk_WD", DOUBLE, WRITE)
            # self.blockdata.addAttribute("Blk_Kitch", DOUBLE, WRITE)
            # self.blockdata.addAttribute("Blk_Shower", DOUBLE, WRITE)
            # self.blockdata.addAttribute("Blk_Toilet", DOUBLE, WRITE)
            # self.blockdata.addAttribute("Blk_Laund", DOUBLE, WRITE)
            # self.blockdata.addAttribute("Blk_Garden", DOUBLE, WRITE)
            # self.blockdata.addAttribute("Blk_Com", DOUBLE, WRITE)
            # self.blockdata.addAttribute("Blk_Ind", DOUBLE, WRITE)
            # self.blockdata.addAttribute("Blk_PubIrr", DOUBLE, WRITE)
            self.blockdata.addAttribute("HasL_RESSys", DOUBLE, WRITE)
            self.blockdata.addAttribute("HasL_HDRSys", DOUBLE, WRITE)
            self.blockdata.addAttribute("HasL_LISys", DOUBLE, WRITE)
            self.blockdata.addAttribute("HasL_HISys", DOUBLE, WRITE)
            self.blockdata.addAttribute("HasL_COMSys", DOUBLE, WRITE)
            self.blockdata.addAttribute("HasSSys", DOUBLE, WRITE)
            self.blockdata.addAttribute("HasNSys", DOUBLE, WRITE)
            self.blockdata.addAttribute("HasBSys", DOUBLE, WRITE)

            self.registerViewContainers([self.blockdata, self.regiondata])


        def run(self):
            #Data Stream Manipulation
            datadict = self.loadFileTESTFILE()
            numblocks = len(datadict["BlockID"])
            numbasins = max(datadict["BasinID"])

            print numblocks
            print numbasins

            mapregion = self.regiondata.create_feature()
            mapregion.SetField("NumBlocks", numblocks)
            mapregion.SetField("TotalBasins", numbasins)

            #Transfer datadict into BlockComponents
            for i in range(numblocks):
                blockcomp = self.blockdata.create_feature()
                for att in self.attnames:
                    # print att
                    blockcomp.SetField(att, datadict[att][i])
                    if att=="BlockID":
                        print datadict[att][i]
                    if att=="ResHouses":
                        blockcomp.SetField("HasHouses", int(datadict[att][i]!=0))
                        blockcomp.SetField("HasRes", int(datadict[att][i]!=0))
                    if att=="HDRFlats":
                        blockcomp.SetField("HasFlats", int(datadict[att][i]!=0))
                        blockcomp.SetField("HasRes", int(datadict[att][i]!=0))
                    if att=="LIestates":
                        blockcomp.SetField("Has_LI", int(datadict[att][i]!=0))
                    if att=="HIestates":
                        blockcomp.SetField("Has_HI", int(datadict[att][i]!=0))
                    if att=="COMestates":
                        blockcomp.SetField("Has_Com", int(datadict[att][i]!=0))
                    if att=="ORCestates":
                        blockcomp.SetField("Has_ORC", int(datadict[att][i]!=0))
                    if att=="downID":
                        if int(datadict[att][i]) != -1:
                            blockcomp.SetField("downID", int(datadict[att][i]))
                        else:
                            blockcomp.SetField("downID", int(datadict["drainID"][i]))

                blockcomp.SetField("HasL_RESSys", 0)
                blockcomp.SetField("HasL_HDRSys", 0)
                blockcomp.SetField("HasL_LISys", 0)
                blockcomp.SetField("HasL_HISys", 0)
                blockcomp.SetField("HasL_COMSys", 0)
                blockcomp.SetField("HasSSys", 0)
                blockcomp.SetField("HasNSys", 0)
                blockcomp.SetField("HasBSys", 0)

            self.regiondata.finalise()
            self.blockdata.finalise()

            return True


        def loadFileTESTFILE(self):
            """Retrieves the testfile and writes the information into dictionary
                - uses either input from TESTFILE or the fullfilepath parameter
                - returns the variable datadict, which contains all attributes
            """
            if self.fullfilepath == "":
                f = open(TESTFILE, 'r')
            else:
                f = open(self.fullfilepath, 'r')
            filedata = []
            for lines in f:
                filedata.append(lines.split(','))
            f.close()
            attlist = filedata[0]

            for i in range(len(attlist)):
                if "\n" in attlist[i]:
                    attlist[i] = attlist[i].rstrip("\n")

            #Create dictionary to store data
            datadict = {}
            for attribute in attlist:
                datadict[attribute] = []

            for i in range(len(filedata)):
                if i == 0:
                    continue
                dataline = filedata[i]
                for j in range(len(dataline)):
                    try:
                        datadict[attlist[j]].append(float(dataline[j]))
                    except:
                        datadict[attlist[j]].append(dataline[j])

            return datadict
