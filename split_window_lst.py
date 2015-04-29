# -*- coding: utf-8 -*-
"""
A class for the Split Window Algorithm for Land Surface Temperature estimation
@author: nik | Created on Wed Mar 18 11:28:45 2015

ToDo:
    * USE eval, it is your friend! Current mapcalc expressions are
    unnecessarily too complex to read.
"""

# import average emissivities
import random
import csv_to_dictionary as coefficients
from column_water_vapor import Column_Water_Vapor

# globals
EMISSIVITIES = coefficients.get_average_emissivities()
COLUMN_WATER_VAPOR = coefficients.get_column_water_vapor()
DUMMY_MAPCALC_STRING_T10 = 'Input_T10'
DUMMY_MAPCALC_STRING_T11 = 'Input_T11'
DUMMY_MAPCALC_STRING_CWV = 'Input_CWV'

# helper functions
def check_t1x_range(number):
    """
    Check if Brithness Temperature (Kelvin degrees) values for T10, T11, lie
    inside a reasonable range, eg [200, 330].

    Note, the Digital Number values in bands B10 and B11, are 16-bit. The
    actual data quantisation though is 12-bit.
    """
    if number < 200 or number > 330:
        raise ValueError('The input value {t1x} for T1x is out of a reasonable '
                         'range [200, 330]'.format(t1x=number))
    else:
        return True


def check_cwv(cwv):
    """
    Check whether a column water value lies within a "valid" range. Which is?
    """
    if cwv < 0.0 or cwv > 6.3:
        raise ValueError('The column water vapor estimation is out of the '
                         'expected ranfe [0.0, 6.3]')
    else:
        return True


class SplitWindowLST():
    """
    A class implementing the split-window algorithm for Landsat8 imagery

    Inputs:

    - Brightness temperatures for T10 and T11
    - An estimation of the column water vapor

    Outputs:

    -
    -

    Details

    The algorithm removes the atmospheric effect through differential
    atmospheric absorption in the two adjacent thermal infrared channels
    centered at about 11 and 12 μm.

    The linear or non-linear combination of the brightness temperatures is
    finally applied for LST estimation based on the equation:

    LST = b0 +
        + (b1 + b2 * ((1-ae)/ae)) +
        + b3 * (de/ae) * ((t10 + t11)/2) +
        + (b4 + b5 * ((1-ae)/ae) + b6 * (de/ae^2)) * ((t10 - t11)/2) +
        + b7 * (t10 - t11)^2

    To reduce the influence of the CWV error on the LST, for a CWV within the
    overlap of two adjacent CWV sub-ranges, we first use the coefficients from
    the two adjacent CWV sub-ranges to calculate the two initial temperatures
    and then use the average of the initial temperatures as the pixel LST.
    
    For example, the LST pixel with a CWV of 2.1 g/cm2 is estimated by using
    the coefficients of [0.0, 2.5] and [2.0, 3.5]. This process initially
    reduces the δLSTinc and improves the spatial continuity of the LST product.
    """

    def __init__(self, emissivity_b10, emissivity_b11):
        """
        Create a class object for Split Window algorithm

        Required inputs:
        - B10
        - B11 -- ToAR?
        - land cover class?
        - average emissivities for B10, B11
        - subrange for column water vapor
        """
        # citation
        self.citation = ('Du, Chen; Ren, Huazhong; Qin, Qiming; Meng, '
                         'Jinjie; Zhao, Shaohua. 2015. '
                         '"A Practical Split-Window Algorithm '
                         'for Estimating Land Surface Temperature from '
                         'Landsat 8 Data." '
                         'Remote Sens. 7, no. 1: 647-665.')

        # basic equation/model (for __str__)
        self._equation = ('[b0 + '
                          '(b1 + '
                          'b2*((1-ae)/ae)) + '
                          'b3*(de/ae) * ((t10 + t11)/2) + '
                          '(b4 + '
                          'b5*((1-ae)/ae) + '
                          'b6*(de/ae^2))*((t10 - t11)/2) + '
                          'b7*(t10 - t11)^2]')
        self._model = ('[{b0} + '
                       '({b1} + '
                       '{b2}*((1-{ae})/{ae})) + '
                       '{b3}*({de}/{ae}) * (({t10} + {t11})/2) + '
                       '({b4} + '
                       '{b5}*((1-{ae})/{ae}) + '
                       '{b6}*({de}/{ae}^2))*(({t10} - {t11})/2) + '
                       '{b7}*({t10} - {t11})^2]')

        # use inputs
        self.emissivity_t10 = float(emissivity_b10)
        self.emissivity_t11 = float(emissivity_b11)

        self.average_emissivity = 0.5 * (self.emissivity_t10 + self.emissivity_t11)
        self.delta_emissivity = self.emissivity_t10 - self.emissivity_t11

        # column water vapor coefficients and associated RMSE
        #self.column_water_vapor = column_water_vapor

        # self.cwv_subrange OR (self.cwv_subrange_a AND self.cwv_subrange_b)
        #self._retrieve_adjacent_cwv_subranges(column_water_vapor)

#        if self._cwv_subrange:
#
#            self._retrieve_cwv_coefficients(self._cwv_subrange)  # self.cwv_coefficients
#            self.rmse = self._retrieve_rmse(self._cwv_subrange)  # self.rmse
#
#            # model for mapcalc
#            self.model = self._build_model()
#
#        else:
#
#            self.model = False
#            self.rmse = False
#            self.cwv_coefficients_a = self._retrieve_cwv_coefficients(self._cwv_subrange_a)
#            self._model_a = self._build_model()
#            self.rmse_a = self._retrieve_rmse(self._cwv_subrange_a)  # self.rmse
#            self.cwv_coefficients_b = self._retrieve_cwv_coefficients(self._cwv_subrange_b)
#            self._model_b = self._build_model()
#            self.rmse_b = self._retrieve_rmse(self._cwv_subrange_b)  # self.rmse
            #
            # build models for each subrange
            #

#            assert self._cwv_subrange_a and self._cwv_subrange_b, "Break!"

        #
        # self.mapcalc = self._build_mapcalc()

        # all-in-one split-window lst expression for mapcalc
        self.sw_lst_mapcalc = self._build_swlst_mapcalc()

    def __str__(self):
        """
        Return a string representation of the basic Split Window LST equation
        """
        equation = ' > The algorithm\'s basic equation: ' + self._equation

        #if self.model:
        #    model = ' > The model: ' + self.model

        #else:
        #    model = ' > The models:\n ' + '  a: ' + self._model_a + '\n ' + '  b: ' + self._model_b + '\n'

        return equation #+ '\n' + model

    def _retrieve_adjacent_cwv_subranges(self, column_water_vapor):
        """
        Select and return adjacent subranges (string to be used as a dictionary
        key) based on the atmospheric column water vapor estimation (float ratio)
        ranging in (0.0, 6.3].

        Input "cwv" is an estimation of the column water vapor (float ratio).
        """
        cwv = column_water_vapor
        check_cwv(cwv)  # check if float?
 
        # a "subrange" generator
        key_subrange_generator = ((key, COLUMN_WATER_VAPOR[key].subrange)
                                  for key in COLUMN_WATER_VAPOR.keys())

        # cwv in one or two subranges?
        result = [range_x for range_x, (low, high) in key_subrange_generator
                  if low < cwv < high]

        # if one subrange, return a string
        if len(result) == 1:
            #self._cwv_subrange = result[0]
            #self._cwv_subrange_a = self._cwv_subrange_b = False
            return result[0]

        # if two subranges, return a tuple
        elif len(result) == 2:
            # self._cwv_subrange = False
            # self._cwv_subrange_a, self._cwv_subrange_b = tuple(result)
            return result[0], result[1]

    def _set_adjacent_cwv_subranges(self, column_water_vapor):
        """
        Set the retrieved cwv subranges as an attribute, though not a public
        one.
        """
        result = self._retrieve_adjacent_cwv_subranges(column_water_vapor)
        if len(result) == 1:
            self._cwv_subrange = result[0]
            self._cwv_subrange_a = self._cwv_subrange_b = False

        elif len(result) == 2:
            self._cwv_subrange = False
            self._cwv_subrange_a, self._cwv_subrange_b = tuple(result)

    def _retrieve_cwv_coefficients(self, subrange):
        """
        Retrieve column water vapor coefficients for requested subrange
        """
        b0 = COLUMN_WATER_VAPOR[subrange].b0
        b1 = COLUMN_WATER_VAPOR[subrange].b1
        b2 = COLUMN_WATER_VAPOR[subrange].b2
        b3 = COLUMN_WATER_VAPOR[subrange].b3
        b4 = COLUMN_WATER_VAPOR[subrange].b4
        b5 = COLUMN_WATER_VAPOR[subrange].b5
        b6 = COLUMN_WATER_VAPOR[subrange].b6
        b7 = COLUMN_WATER_VAPOR[subrange].b7

        cwv_coefficients = (b0,
                            b1,
                            b2,
                            b3,
                            b4,
                            b5,
                            b6,
                            b7)

        return cwv_coefficients

    def _set_cwv_coefficients(self, subrange):
        """
        Set the coefficients as an attribute.
        """
        self.cwv_coefficients = self._retrieve_cwv_coefficients(subrange)

    def get_cwv_coefficients(self):
        """
        Return the column water vapor coefficients from the object's attribute.
        """
        if self.cwv_coefficients:
            return self.cwv_coefficients
        else:
            print "* CWV coefficients have not been set!"

    def _retrieve_rmse(self, subrange):
        """
        Retrieve and set the associated RMSE for the column water vapor
        coefficients for the subrange in question.
        """
        return COLUMN_WATER_VAPOR[subrange].rmse

    def _set_rmse(self, subrange):
        """
        Set the RMSE as an attribute.
        """
        self.rmse = self._retrieve_rmse(subrange)

    def report_rmse(self):
        """
        Report the associated R^2 value for the coefficients in question
        """
        msg = "Associated RMSE: "
        return msg + str(self.rmse)

    def compute_lst(self, t10, t11, coefficients):
        """
        Compute Land Surface Temperature based on the Split-Window algorithm.
        Inputs are brightness temperatures measured in channels  i(~11.0 μm) and j (~12.0 μm).
        """

        # check validity of t10, t11
        check_t1x_range(t10)
        check_t1x_range(t11)

        # check validity of subrange (string)?

        # set cwv coefficients
        b0, b1, b2, b3, b4, b5, b6, b7 = coefficients

        # average and delta emissivity
        avg = self.average_emissivity
        delta = self.delta_emissivity

        # addends
        a = b0
        b = b1 + b2 * ((1-avg) / avg)
        c = b3*(delta / avg) * ((t10 + t11) / 2)
        d1 = b4 + b5 * ((1-avg) / avg) + b6 * (delta / avg**2)
        d2 = (t10 - t11) / 2
        d = d1 * d2
        e = b7 * (t10 - t11)**2

        # land surface temperature
        lst = a + b + c + d + e
        return lst

    def _set_lst(self):
        """
        """
        pass

    def compute_average_lst(self, t10, t11, subrange_a, subrange_b):
        """
        Compute average LST
        """

        # retrieve coefficients for first subrange and compute lst for it
        coefficients_a = self._retrieve_cwv_coefficients(subrange_a)
        lst_a = self.compute_lst(t10, t11, coefficients_a)

        # repeat for second subrange
        coefficients_b = self._retrieve_cwv_coefficients(subrange_b)
        lst_b = self.compute_lst(t10, t11, coefficients_b)

        # average land surface temperature
        return (lst_a + lst_b) / 2

    def _set_average_lst(self):
        """
        Set the average LST pixel value
        """
        pass

    def _build_model(self, coefficients):
        """
        Build model for __str__
        """
        b0, b1, b2, b3, b4, b5, b6, b7 = coefficients
        model = self._model.format(b0=b0,
                                   b1=b1,
                                   b2=b2,
                                   ae=self.average_emissivity,
                                   de=self.delta_emissivity,
                                   b3=b3,
                                   b4=b4,
                                   b5=b5,
                                   b6=b6,
                                   b7=b7,
                                   t10=self.emissivity_t10,
                                   t11=self.emissivity_t11)
        return model

    def _build_custom_mapcalc(self, subrange):
        """
        Build formula for GRASS GIS' mapcalc for the given cwv subrange
        """
        # formula = '{c0} + {c1}*{dummy} + {c2}*{dummy}^2'
        formula = ('{b0} + '
                   '({b1} + '
                   '({b2})*((1-{ae})/{ae})) + '
                   '({b3})*({de}/{ae}) * (({DUMMY_T10} + {DUMMY_T11})/2) + '
                   '({b4} + '
                   '({b5})*((1-{ae})/{ae}) + '
                   '({b6})*({de}/{ae}^2))*(({DUMMY_T10} - {DUMMY_T11})/2) + '
                   '({b7})*({DUMMY_T10} - {DUMMY_T11})^2')

        # for now, use fixed emissivities! <--------------------------------
        emissivity_t10 = float(self.emissivity_t10)
        emissivity_t11 = float(self.emissivity_t11)
        avg_emissivity = 0.5 * (emissivity_t10 + emissivity_t11)
        delta_emissivity = emissivity_t10 - emissivity_t11

        coefficients = self._retrieve_cwv_coefficients(subrange)
        b0, b1, b2, b3, b4, b5, b6, b7 = coefficients

        mapcalc = formula.format(b0=b0,
                                 b1=b1,
                                 b2=b2,
                                 ae=avg_emissivity,
                                 de=delta_emissivity,
                                 b3=b3,
                                 b4=b4,
                                 b5=b5,
                                 b6=b6,
                                 b7=b7,
                                 DUMMY_T10=DUMMY_MAPCALC_STRING_T10,
                                 DUMMY_T11=DUMMY_MAPCALC_STRING_T11)

        return mapcalc

    def _build_swlst_mapcalc(self):
        """
        """
        # subrange limits, low, high
        low_1, high_1 = COLUMN_WATER_VAPOR['Range_1'].subrange
        low_2, high_2 = COLUMN_WATER_VAPOR['Range_2'].subrange
        low_3, high_3 = COLUMN_WATER_VAPOR['Range_3'].subrange
        low_4, high_4 = COLUMN_WATER_VAPOR['Range_4'].subrange
        low_5, high_5 = COLUMN_WATER_VAPOR['Range_5'].subrange

        # build mapcalc expression for each subrange
        expression_range_1 = self._build_custom_mapcalc('Range_1')
        expression_range_2 = self._build_custom_mapcalc('Range_2')
        expression_range_3 = self._build_custom_mapcalc('Range_3')
        expression_range_4 = self._build_custom_mapcalc('Range_4')
        expression_range_5 = self._build_custom_mapcalc('Range_5')

        # build one big expression using mighty eval
        sw_lst_expression = ('eval( sw_lst_1 = {exp_1},'
                             '\ \n sw_lst_2 = {exp_2},'
                             '\ \n sw_lst_12 = (sw_lst_1 + sw_lst_2) / 2,'
                             '\ \n sw_lst_3 = {exp_3},'
                             '\ \n sw_lst_23 = (sw_lst_2 + sw_lst_3) / 2,'
                             '\ \n sw_lst_4 = {exp_4},'
                             '\ \n sw_lst_34 = (sw_lst_3 + sw_lst_4) / 2,'
                             '\ \n sw_lst_5 = {exp_5},' 
                             '\ \n sw_lst_45 = (sw_lst_5 + sw_lst_5) / 2,'
                             '\ \n in_range_1 = {low_1} < {DUMMY_CWV} < {high_1},'
                             '\ \n in_range_2 = {low_2} < {DUMMY_CWV} < {high_2},'
                             '\ \n in_range_3 = {low_3} < {DUMMY_CWV} < {high_3},'
                             '\ \n in_range_4 = {low_4} < {DUMMY_CWV} < {high_4},'
                             '\ \n in_range_5 = {low_5} < {DUMMY_CWV} < {high_5},'
                             '\ \n if( in_range_1 && in_range_2, sw_lst_12,'
                             '\ \n if( in_range_2 && in_range_3, sw_lst_23,'
                             '\ \n if( in_range_3 && in_range_4, sw_lst_34,'
                             '\ \n if( in_range_4 && in_range_5, sw_lst_45,'
                             '\ \n if( in_range_1, sw_lst_1,'
                             '\ \n if( in_range_2, sw_lst_2,'
                             '\ \n if( in_range_3, sw_lst_3,'
                             '\ \n if( in_range_4, sw_lst_4,'
                             '\ \n if( in_range_5, sw_lst_5,'
                             ' null() ))))))))))')

        # replace keywords appropriately
        swlst_expression = sw_lst_expression.format(exp_1=expression_range_1,
                                                    low_1=low_1, 
                                                    DUMMY_CWV=DUMMY_MAPCALC_STRING_CWV,
                                                    high_1=high_1,
                                                    exp_2=expression_range_2,
                                                    low_2=low_2, high_2=high_2,
                                                    exp_3=expression_range_3,
                                                    low_3=low_3, high_3=high_3,
                                                    exp_4=expression_range_4,
                                                    low_4=low_4, high_4=high_4,
                                                    exp_5=expression_range_5,
                                                    low_5=low_5, high_5=high_5)

        return swlst_expression

    def _build_mapcalc(self):
        """
        Build formula for GRASS GIS' mapcalc
        """
        # formula = '{c0} + {c1}*{dummy} + {c2}*{dummy}^2'
        formula = ('{b0} + '
                   '({b1} + '
                   '({b2})*((1-{ae})/{ae})) + '
                   '({b3})*({de}/{ae}) * (({DUMMY_T10} + {DUMMY_T11})/2) + '
                   '({b4} + '
                   '({b5})*((1-{ae})/{ae}) + '
                   '({b6})*({de}/{ae}^2))*(({DUMMY_T10} - {DUMMY_T11})/2) + '
                   '({b7})*({DUMMY_T10} - {DUMMY_T11})^2')

        mapcalc = formula.format(b0=self.b0,
                                 b1=self.b1,
                                 b2=self.b2,
                                 ae=self.average_emissivity,
                                 de=self.delta_emissivity,
                                 b3=self.b3,
                                 b4=self.b4,
                                 b5=self.b5,
                                 b6=self.b6,
                                 b7=self.b7,
                                 DUMMY_T10=DUMMY_MAPCALC_STRING_T10,
                                 DUMMY_T11=DUMMY_MAPCALC_STRING_T11)

        return mapcalc

    def _build_mapcalc_average(self):
        """
        Build formula for GRASS GIS' mapcalc -- to do!
        """
        # formula = '{c0} + {c1}*{dummy} + {c2}*{dummy}^2'
        formula = ('{b0} + '
                   '({b1} + '
                   '({b2})*((1-{ae})/{ae})) + '
                   '({b3})*({de}/{ae}) * (({DUMMY_T10} + {DUMMY_T11})/2) + '
                   '({b4} + '
                   '({b5})*((1-{ae})/{ae}) + '
                   '({b6})*({de}/{ae}^2))*(({DUMMY_T10} - {DUMMY_T11})/2) + '
                   '({b7})*({DUMMY_T10} - {DUMMY_T11})^2')

        mapcalc = formula.format(b0=self.b0,
                                      b1=self.b1,
                                      b2=self.b2,
                                      ae=self.average_emissivity,
                                      de=self.delta_emissivity,
                                      b3=self.b3,
                                      b4=self.b4,
                                      b5=self.b5,
                                      b6=self.b6,
                                      b7=self.b7,
                                      DUMMY_T10=DUMMY_MAPCALC_STRING_T10,
                                      DUMMY_T11=DUMMY_MAPCALC_STRING_T11)

        mapcalc_one = ''
        mapcalc_two = ''
        mapcalc_avg = ((mapcalc_one + mapcalc_two) / 2)
        return mapcalc

    # def _build_mapcalc_direct(self):
    #     """
    #     Build formula for GRASS GIS' mapcalc
    #     """
    #     formula = ('[{b0} + '
    #                '({b1} + '
    #                '{b2}*((1-{ae})/{ae})) + '
    #                '{b3}*({de}/{ae}) * (({t10} + {t11})/2) + '
    #                '({b4} + '
    #                '{b5}*((1-{ae})/{ae}) + '
    #                '{b6}*({de}/{ae}^2))*(({t10} - {t11})/2) + '
    #                '{b7}*({t10} - {t11})^2]')

    #     self.mapcalc_direct = formula.format(b0=self.b0,
    #                                          b1=self.b1,
    #                                          b2=self.b2,
    #                                          ae=self.average_emissivity,
    #                                          de=self.delta_emissivity,
    #                                          b3=self.b3,
    #                                          b4=self.b4,
    #                                          b5=self.b5,
    #                                          b6=self.b6,
    #                                          b7=self.b7,
    #                                          t10=self.emissivity_t10,
    #                                          t11=self.emissivity_t11)

# reusable & stand-alone
if __name__ == "__main__":
    print ('Split-Window Algorithm for Estimating Land Surface Temperature '
           'from Landsat8 OLI/TIRS imagery.'
           ' (Running as stand-alone tool?)\n')
