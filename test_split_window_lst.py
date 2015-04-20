#!/usr/bin/python\<nl>\
# -*- coding: utf-8 -*-

"""
@author nik | 2015-04-18 03:48:20
"""

# required librairies
import random
import csv_to_dictionary as coefficients
from split_window_lst import * 

# globals
EMISSIVITIES = coefficients.get_average_emissivities()
COLUMN_WATER_VAPOUR = coefficients.get_column_water_vapour()

# helper function(s)
def random_digital_numbers(count=2):
    """
    Return a user-requested amount of random Digital Number values for testing
    purposes ranging in 12-bit
    """
    digital_numbers = []

    for dn in range(0, count):
        digital_numbers.append(random.randint(1, 2**12))

    if count == 1:
        return digital_numbers[0]

    return digital_numbers


def random_column_water_vapour():
    """
    Return a rational number ranging in [0.0, 6.3] to assisst in selecting
    an atmospheric column water vapour subrange, as part of testing the
    Split-WindowLST class.
    """
    return random.uniform(0.0, 6.3)


def test_split_window_lst():
    """
    Testing the SplitWindowLST class
    """

    #
    # Helpers
    #

    print
    print ">>> [Helper functions]"
    print
    t10 = random_digital_numbers(1)
    t11 = random.choice(((t10 + 500), (t10 - 500)))
    print " * Random 12-bit digital numbers for T10, T11:", t10, t11
    print
    print

    #
    # EMISSIVITIES
    #

    # get emissivities
    print ">>> [EMISSIVITIES]"
    print
    EMISSIVITIES = coefficients.get_average_emissivities()
    print " * Dictionary for average emissivities:\n\n", EMISSIVITIES
    print

    somekey = random.choice(EMISSIVITIES.keys())
    print " * Some random key from EMISSIVITIES:", somekey

    fields = EMISSIVITIES[somekey]._fields
    print " * Fields of namedtuple:", fields

    random_field = random.choice(fields)
    print " * Some random field:", random_field

    command = 'EMISSIVITIES.[{key}].{field} ='
    command = command.format(key=somekey, field=random_field)
    print " * Example of retrieving values (named tuple): " + command,
    print EMISSIVITIES[somekey].TIRS10, EMISSIVITIES[somekey].TIRS11

    emissivity_b10 = EMISSIVITIES[somekey].TIRS10
    print " * Average emissivity for B10:", emissivity_b10, "|Type:", type(emissivity_b10)
    emissivity_b11 = EMISSIVITIES[somekey].TIRS11
    print " * Average emissivity for B11:", emissivity_b11
    print
    print

    #
    # COLUMN_WATER_VAPOUR
    #

    print ">>> [COLUMN_WATER_VAPOUR]"
    COLUMN_WATER_VAPOUR = coefficients.get_column_water_vapour()
    print "\n * Dictionary for column water vapour coefficients:\n\n",
    print COLUMN_WATER_VAPOUR
    print

    print " * Retrieval of column water vapour via helper/class?"
    print
    print " * Mapcalc expression for it:\n\n", column_water_vapour(3, 'TIRS10', 'TIRS11')
    print

    cwv = random_column_water_vapour()
    print " * For the test, some random atmospheric column water vapour (g/cm^2):", cwv

    # get a column water vapour subrange
    swlst = SplitWindowLST(emissivity_b10, emissivity_b11, cwv)
    cwv_range_x = swlst.cwv_subrange
    
    cwvfields = COLUMN_WATER_VAPOUR[cwv_range_x]._fields
    print " * Fields of namedtuple:", cwvfields

    random_cwvfield = random.choice(cwvfields)
    print " * Some random field:", random_cwvfield

    command = 'COLUMN_WATER_VAPOUR.[{key}].{field} ='
    command = command.format(key=cwv_range_x, field=random_cwvfield)
    print " * Example of retrieving values (named tuple): " + command,
    print COLUMN_WATER_VAPOUR[cwv_range_x].subrange
    print
    
    
    
    #
    # class
    #

    print ">>> [class SplitWindowLST]"
    print

    # cwv_range_x = column_water_vapour_range(cwv)
    # print " * Atmospheric column water vapour range:", cwv_range_x

    swlst = SplitWindowLST(emissivity_b10, emissivity_b11, cwv)
    print "Create object and test '__str__' of SplitWindowLST() class:\n\n", swlst

    print " * Checking 'citation':", swlst.citation
    print

    b0, b1, b2, b3, b4, b5, b6, b7 = swlst.cwv_coefficients
    print " * Column Water Vapour coefficients (b0, b1, ..., b7) in <", swlst.cwv_subrange,
    print "> :", b0, b1, b2, b3, b4, b5, b6, b7

    print " * RMSE for coefficients:", swlst.rmse
    print

    print " * Checking for the 'compute_lst' method:", swlst.compute_lst
    print " * Compute the Land Surface Temperature: 'compute_lst()' >>>", swlst.compute_lst(t10, t11)
    print " * Get it from the object's lst attribute:", swlst.lst
    print

    print " * Checking the 'report_rmse' method:", swlst.report_rmse
    print " * Testing the 'report_rmse' method:", swlst.report_rmse()

    print " * Get mapcalc:", swlst.mapcalc
    # print " * Get mapcalc done all internally!?:", swlst.mapcalc_direct


# reusable & stand-alone
if __name__ == "__main__":
    print ('Testing the SplitWindowLST class')
    print
    test_split_window_lst()
