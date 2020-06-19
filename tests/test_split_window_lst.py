#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
@author nik | 2015-04-18 03:48:20 | Updated June 2020
"""

import random
import csv_to_dictionary as coefficients
from split_window_lst import *
from column_water_vapor import Column_Water_Vapor
from randomness import random_digital_numbers
from randomness import random_window_size
from randomness import random_column_water_vapor
from randomness import random_brightness_temperature_values

EMISSIVITIES = coefficients.get_average_emissivities()
COLUMN_WATER_VAPOR = coefficients.get_column_water_vapor()
MapName_for_T10 = 'TiRS10'
MapName_for_T11 = 'TiRS11'

def test_helper_functions(t10, t11):
    """
    """
    fstring = """[ Helper functions ]
  * Random brightness temperature values for T10, T11: {t10}, {t11}
  * NOTE that some out of a reasonable range T10, T11 values, which cause the
    current test to fail, are tolerated on-purpose in order to test the range
    checking function `check_t1x_range()`."""
    print(fstring)


def test_emissivity_functions(landcover_class):
    """
    """
    fields = EMISSIVITIES[landcover_class]._fields
    random_field = random.choice(fields)
    command = f'EMISSIVITIES.[{landcover_class}].{random_field} ='
    emissivity_b10 = EMISSIVITIES[landcover_class].TIRS10
    type_emissivity_b10 = type(emissivity_b10)
    emissivity_b11 = EMISSIVITIES[landcover_class].TIRS11
    type_emissivity_b11 = type(emissivity_b11)

    fstring = f"""[ EMISSIVITIES
    * Dictionary for average emissivities:
      {EMISSIVITIES}
    * Some random key from EMISSIVITIES: {landcover_class}
    * Fields of namedtuple: {fields}
    * Some random field: {random_field}
    * Example of retrieving values (named tuple): {command}
      {EMISSIVITIES[landcover_class].TIRS10}, {EMISSIVITIES[landcover_class].TIRS11}
    * Average emissivity for B10: {emissivity_b10}, |Type: {type_emissivity_b10}
    * Average emissivity for B11: {emissivity_b11}, |Type: {type_emissivity_b11}"""
    print(fstring)


def test_column_water_vapor_functions(cwv_range_x):
    """
    """
    window_size = random_window_size()
    cwvobj = Column_Water_Vapor(window_size, MapName_for_T10, MapName_for_T11)
    cwvobj_expression = cwvobj.column_water_vapor_expression
    cwvfields = COLUMN_WATER_VAPOR[cwv_range_x]._fields
    random_cwvfield = random.choice(cwvfields)
    command = f'COLUMN_WATER_VAPOR.[{cwv_range_x}].{random_cwvfield}'

    fstring = f"""[ COLUMN_WATER_VAPOR ]
    * NOTE: Some out of range values which cause the current test to fail, are
      tolerated on-purpose in order to check for the CWV range checking function.
      Check for the range of the random_column_water_vapor() function.
    * Dictionary for column water vapor coefficients:
      {COLUMN_WATER_VAPOR}
    * Retrieval of column water vapor via class, example:
      `cwvobj = Column_Water_Vapour({window_size}, {MapName_for_T10}, {MapName_for_T11})`
      returns:
      {cwvobj}
    * Mapcalc expression for it: {cwvobj_expression}
    * Fields of namedtuple (same for all subranges): {cwvfields}
    * Some random field: {random_cwvfield}
    * Example of retrieving values (named tuple): {command}"""
    print(fstring)


def test_split_window_class(swlst_object, cwv, landcover_class):
    """
    """
    cwv_range_x = swlst_object._retrieve_adjacent_cwv_subranges(cwv)
    type_cwv_range_x = type(cwv_range_x)

    # special case for Subrange 6
    if cwv_range_x == 'Range_6':
        msg = f"""The CWV value {cwv} falls outside of one of the subranges. Using the complete CWV range [0.0, 6.3] described as"""
    else:
        msg = f"""The CWV value {cwv} falls inside: {cwv_range_x}
    * Type: {type_cwv_range_x}"""

    fstring = f"""[ class SplitWindowLST ]
    * Create object and test '__str__' of SplitWindowLST() class:
      {swlst_object}
    * The 'citation' attribute:
      {swlst_object.citation}
    * Test using the atmospheric column water vapor value (g/cm^2): {cwv}
    * {msg}, {cwv_range_x}"""
    print(fstring)


def test_split_window_lst():
    """
    Testing the SplitWindowLST class
    """

    t10 = random_brightness_temperature_values(1)
    t11 = random.choice(((t10 + 50), (t10 - 50)))  # check some failures as well
    test_helper_functions(t10, t11)
    print()

    some_landcover_class = random.choice(list(EMISSIVITIES.keys()))
    test_emissivity_functions(some_landcover_class)
    print()

    cwv_range_x = random.choice([key for key in COLUMN_WATER_VAPOR.keys()])
    # print " * Atmospheric column water vapor range:", cwv_range_x
    test_column_water_vapor_functions(cwv_range_x)
    print()

    cwv = random_column_water_vapor()
    swlst = SplitWindowLST(some_landcover_class)
    test_split_window_class(swlst, cwv, some_landcover_class)
    print()


### First, test all _retrieve functions ###

    print()
    print("( Testing unpacking of values )")
    print()

    if type(cwv_range_x) == str:

        cwv_coefficients_x = swlst._retrieve_cwv_coefficients(cwv_range_x)
        b0, b1, b2, b3, b4, b5, b6, b7 = cwv_coefficients_x
        swlst._set_rmse(cwv_range_x)
        report_rmse = swlst.report_rmse()
        swlst_build_model = swlst._build_model(cwv_coefficients_x)
        swlst_retrieve_rmse = swlst._retrieve_rmse(cwv_range_x)
        fstring_cwv_range_x_string = f""" * Column Water Vapor coefficients (b0, b1, ..., b7) in < {cwv_range_x}:
        {b0}, {b1}, {b2}, {b3}, {b4}, {b5}, {b6}, {b7}
         * Model: {swlst_build_model}
         * '_retrieve_rmse' method: swlst_retrieve_rmse
         * '_set_rmse' and 'report_rmse' methods: {report_rmse}
         * Testing the 'compute_lst' method:", swlst.compute_lst(t10, t11, cwv_coefficients_x)"""
        print(fstring_cwv_range_x_string)


    elif type(cwv_range_x) == tuple and len(cwv_range_x) == 2:

        print(" * Two subranges returned:",)

        cwv_subrange_a, cwv_subrange_b = tuple(cwv_range_x)[0], tuple(cwv_range_x)[1]
        print(" Subrange a:", cwv_subrange_a, "| Subrange b:", cwv_subrange_b)

        #
        # Subrange A
        #

        print()
        print(" > Tests for subrange a")
        print()
        coefficients_a = swlst._retrieve_cwv_coefficients(cwv_subrange_a)
        b0, b1, b2, b3, b4, b5, b6, b7 = coefficients_a
        print("   * Column Water Vapor coefficients for", cwv_subrange_a,)
        print("> ", b0, b1, b2, b3, b4, b5, b6, b7)
        print("   * Testing the '_set' and 'get' methods:",)
        swlst._set_cwv_coefficients(cwv_subrange_a)  # does not return anything
        print(swlst.get_cwv_coefficients())
        print("   * Model:", swlst._build_model(coefficients_a))
        print("   * Checking the '_retrieve_rmse' method:", swlst._retrieve_rmse(cwv_subrange_a))
        print("   * Testing the '_set_rmse' and 'report_rmse' methods:",)
        swlst._set_rmse(cwv_subrange_a)
        print(swlst.report_rmse())

        #
        # Subrange B
        #

        print()
        print(" > Tests for subrange b")
        print()
        coefficients_b = swlst._retrieve_cwv_coefficients(cwv_subrange_b)
        b0, b1, b2, b3, b4, b5, b6, b7 = coefficients_b
        print("   * Column Water Vapor coefficients for", cwv_subrange_b,)
        print("> ", b0, b1, b2, b3, b4, b5, b6, b7)
        print("   * Testing the 'get' and '_set' methods:",)
        swlst._set_cwv_coefficients(cwv_subrange_b)
        print(swlst.get_cwv_coefficients())
        print("   * Model:", swlst._build_model(coefficients_b))
        print("   * Checking the '_retrieve_rmse' method:", swlst._retrieve_rmse(cwv_subrange_a))
        print("   * Testing the '_set_rmse' and 'report_rmse' methods:",)
        swlst._set_rmse(cwv_subrange_a)
        print(swlst.report_rmse())

        #
        # Average LST
        #

        print()
        print("( Computing average LST )")
        print()
        print(" * Compute the average LST: 'compute_average_lst()' >>>",)
        print(swlst.compute_average_lst(t10, t11, cwv_subrange_a, cwv_subrange_b))
        print()

    print()
    print("[ Subranges ]")
    print()

    key_subrange_generator = ((key, COLUMN_WATER_VAPOR[key].subrange) for key in COLUMN_WATER_VAPOR.keys())
    sw_lst_expression = swlst.sw_lst_mapcalc
    print("Big expression:\n\n", sw_lst_expression)


# reusable & stand-alone
if __name__ == "__main__":
    print('Testing the SplitWindowLST class')
    print()
    test_split_window_lst()
