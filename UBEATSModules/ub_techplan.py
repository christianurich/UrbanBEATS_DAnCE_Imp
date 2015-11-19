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
            self.addData("City", views)


      def run(self):
            print "Running techplan"





