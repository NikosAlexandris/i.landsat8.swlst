#!/usr/bin/python\<nl>\
# -*- coding: utf-8 -*-

"""
@author nik |
"""

# required librairies
import random
from column_water_vapor import * 


def test_column_water_vapor():
    
    print
    print "Testing the Column_Water_Vapor class"
    print

    obj = Column_Water_Vapor(3, 'TIRS10', 'TIRS11')
    print " | Testing the '__str__' method:\n\n ", obj
    print
    
    print " | Adjacent pixels:", obj.adjacent_pixels
    print

    print " | Map Ti:", obj.ti
    print

    print " | Map Tj:", obj.tj
    print

    print " | Modifiers for Ti:", obj.modifiers_ti
    print
    
    print " | Modifiers for Tj:", obj.modifiers_tj
    print
    
    #print " | Zipped modifiers_tj:", obj.modifiers
    #print

    print " | Expression for Ti mean:", obj.mean_ti_expression
    print
    
    print " | Expression for Tj mean:", obj.mean_tj_expression
    print
    
    #print ' | A single "means" expression:', obj.means_tji_expression
    #print
    
    print " | Note, the following mapcalc expressions use dummy strings, meant to be replaced in the main program by the names of the maps in question"
    print

    print " | Numerator for Ratio (method):", obj._numerator_for_ratio('TestValue_TiMean', 'TestValue_TjMean')
    print
    
    print " | Denominator for Ratio (method):", obj._denominator_for_ratio('TestValue_TiMean')
    print

    print " | Ratio ji expression for mapcalc:", obj.ratio_ji_expression
    print

    print ' | Complete expression:', obj._column_water_vapor_complete_expression()
    print
    
    print ' | The "Column Water Vapor retrieval expression for mapcalc":', obj.column_water_vapor_expression
    print
    
    print " | One big mapcalc expression:\n\n  ", obj._build_cwv_mapcalc()
    print

# reusable & stand-alone
if __name__ == "__main__":
    print ('Testing the SplitWindowLST class')
    print
    test_column_water_vapor()
