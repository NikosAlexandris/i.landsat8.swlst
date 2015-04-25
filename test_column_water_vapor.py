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

    obj = Column_Water_Vapor(3, 'A', 'B')
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
    
    print " | Zipped modifiers_tij (used in a function for the Ratio ji):", obj.modifiers
    print

    print " | Expression for Ti mean:", obj.mean_ti_expression
    print
    
    print " | Expression for Tj mean:", obj.mean_tj_expression
    print
    
    print " | Note, the following mapcalc expressions use dummy strings, meant to be replaced in the main program by the names of the maps in question"
    print

    print " | Expression for Numerator for Ratio (method):", obj._numerator_for_ratio('Ti_Mean', 'Tj_Mean')
    print
    
    print " | Expression for Denominator for Ratio (method):", obj._denominator_for_ratio('Ti_Mean')
    print

    print " | Ratio ji expression for mapcalc:", obj.ratio_ji_expression
    print

    print " | One big mapcalc expression:\n\n  ", obj._big_cwv_expression()
    print

# reusable & stand-alone
if __name__ == "__main__":
    print ('Testing the SplitWindowLST class')
    print
    test_column_water_vapor()
