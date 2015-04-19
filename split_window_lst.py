# -*- coding: utf-8 -*-
"""
A class for the Split Window Algorithm for Land Surface Temperature estimation
@author: nik | Created on Wed Mar 18 11:28:45 2015
"""

# import average emissivities
import random
import csv_to_dictionary as coefficients


# globals
EMISSIVITIES = coefficients.get_average_emissivities()
COLUMN_WATER_VAPOUR = coefficients.get_column_water_vapour()
DUMMY_MAPCALC_STRING_T10 = 'Input_T10'
DUMMY_MAPCALC_STRING_T11 = 'Input_T11'


# helper functions
def check_t1x_range(dn):
    """
    Check if digital numbers for T10, T11, lie inside the expected range
    [1, 65535] (note, that is 16-bit though the actual data quantisation
    is 12-bit).
    """
    if dn < 1 or dn > 65535:
        raise ValueError('The input value for T10 is out of the '
                         'expected range [1,65535]')
    else:
        return True


def column_water_vapour():
    """
    Retrieving atmospheric column water vapor from Landsat8 TIRS data based on
    the modified split-window covariance and variance ratio (MSWCVR).

    With a vital assumption that the atmosphere is unchanged over the
    neighboring pixels, the MSWCVR method relates the atmospheric CWV to the ratio
    of the upward transmittances in two thermal infrared bands, whereas the
    transmittance ratio can be calculated based on the TOA brightness temperatures
    of the two bands.

    Considering N adjacent pixels, the CWV in the MSWCVR method is estimated as:

    - cwv = c0 + c1 * (tj / ti) + c2 * (tj / ti)^2
    - tj/ti ~ Rji = SUM [ ( Tik - mean(Ti) ) * (Tjk - mean(Tj) ) ] / SUM [ ( Tik - mean(Tj) )^2 ]

    In Equation (3a):

    - c0, c1 and c2 are the coefficients obtained from the
    simulated data;
    - τ is the band effective atmospheric transmittance;
    - N is the number of adjacent pixels (always excluding water and cloud pixels)
    in a spatial window size n (i.e., N = n × n);
    - Ti,k and Tj,k are the respective brightness temperatures (K) of bands
    i and j at the TOA level for the kth pixel;
    - and mean(Ti) and mean(Tj) are the mean or median brightness temperatures of
    the N pixels for the two bands.

    Using the aforementioned 946 cloud-free TIGR atmospheric profiles, we first
    used the new high accurate atmospheric radiative transfer model MODTRAN 5.2 to
    simulate the band effective atmospheric transmittance, and then we obtained the
    coefficients through regression, which resulted in:

    - c0 = −9.674
    - c1 = 0.653
    - c2 = 9.087

    The model analysis indicated that this method will obtain a CWV RMSE of about
    0.5 g/cm2. The details about the CWV retrieval can be found in [40].
    """
    equation = '{result} = {expression}'
    cwv_expression = '-9.674 + 0.653 * {Rji} + 9.087 * {Rji}^2'
    rji_expression = '{rji_numerator} / {rji_denominator}'


    """
    Adjacent pixels
    
    [-1, -1] [-1, 0] [-1, 1]
    [ 0, -1] [ 0, 0] [ 0, 1]
    [ 1, -1] [ 1, 0] [ 1, 1]

    """
    
    adjacent_pixels = [[col-1,row-1] for col in xrange(grid_width) for row in xrange(grid_height)]
    print adjacent_pixels

    Ti = '' # T10
    Tj = '' # T11

    modifiers = ["map" + str(pixel) for pixel in adjacent_pixels] 
    print modifiers

    numerator = ' + '.join(modifiers)
    denominator = len(modifiers)
    average = numerator / denominator

    equation = '{result} = {expression}'

    # (Tik - Ti_mean) * (Tjk - Tj_mean) / (Tik - Ti_mean)^2


    rji_numerator  = '({ti} - {tim}) * ({tj} - {tjm})'
    rji_denominator = '({ti} - {tim})^2'
    rji_expression = rji_numerator / rji_denominator


    rji_something = ' + '.join([numerator.format(ti=mod, tim='Ti_mean', tj='Tj', tjm='Tj_mean') for mod in modifiers])

    rji_something = ' + '.join([denominator.format(ti=mod, tim='Ti_mean') for mod in modifiers])



class SplitWindowLST():
    """
    A class implementing the split-window algorithm for Landsat8 imagery.
    The algorithm removes the atmospheric effect through differential
    atmospheric absorption in the two adjacent thermal infrared channels
    centered at about 11 and 12 μm, and the linear or nonlinear combination
    of the brightness temperatures is finally applied for LST estimation.

    LST = b0 +
        + (b1 + b2 * ((1-ae)/ae)) +
        + b3 * (de/ae) * ((t10 + t11)/2) +
        + (b4 + b5 * ((1-ae)/ae) + b6 * (de/ae^2)) * ((t10 - t11)/2) +
        + b7 * (t10 - t11)^2
    """

    def __init__(self, emissivity_b10, emissivity_b11, cwv_subrange):
        """
        Create a class object for Split Window algorithm

        Required inputs:
        - B10
        - B11 -- ToAR?
        - land cover class?
        - average emissivities for B10, B11
        - subrange for column water vapour
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
                       '{b7}*({t10} - {t11})^2]\n')

        # use inputs
        self.emissivity_t10 = float(emissivity_b10)
        self.emissivity_t11 = float(emissivity_b11)

        self.average_emissivity = 0.5 * (self.emissivity_t10 + self.emissivity_t11)
        self.delta_emissivity = self.emissivity_t10 - self.emissivity_t11

        self.cwv_subrange = random.choice(COLUMN_WATER_VAPOUR.keys())  # ***

        # set emissivities, column water vapour, RMSE
        self._set_cwv_coefficients()
        self._set_rmse()

        # model for mapcalc
        self._build_model()
        self._build_mapcalc()
        # self._build_mapcalc_direct()

    def __str__(self):
        """
        Return a string representation of the Split Window ...
        """
        equation = '   > The equation: ' + self._equation
        model = '   > The model: ' + self.model
        return equation + '\n' + model

    def _set_cwv_coefficients(self):
        """
        Set column water vapour coefficients for requested subrange
        """
        self.b0 = COLUMN_WATER_VAPOUR[self.cwv_subrange].b0
        self.b1 = COLUMN_WATER_VAPOUR[self.cwv_subrange].b1
        self.b2 = COLUMN_WATER_VAPOUR[self.cwv_subrange].b2
        self.b3 = COLUMN_WATER_VAPOUR[self.cwv_subrange].b3
        self.b4 = COLUMN_WATER_VAPOUR[self.cwv_subrange].b4
        self.b5 = COLUMN_WATER_VAPOUR[self.cwv_subrange].b5
        self.b6 = COLUMN_WATER_VAPOUR[self.cwv_subrange].b6
        self.b7 = COLUMN_WATER_VAPOUR[self.cwv_subrange].b7

        self.cwv_coefficients = (self.b0,
                                 self.b1,
                                 self.b2,
                                 self.b3,
                                 self.b4,
                                 self.b5,
                                 self.b6,
                                 self.b7)

    def get_cwv_coefficients(self):
        """
        Return the column water vapour coefficients
        """
        return self.cwv_coefficients

    def _set_rmse(self):
        """
        Retrieve and set the associated RMSE for the column water vapour
        coefficients for the subrange in question.
        """
        self.rmse = COLUMN_WATER_VAPOUR[self.cwv_subrange].rmse

    def report_rmse(self):
        """
        Report the associated R^2 value for the coefficients in question
        """
        msg = "Associated RMSE: "
        return msg + str(self.rmse)

    def compute_lst(self, t10, t11):
        """
        Compute Land Surface Temperature based on the Split-Window algorithm.
        Inputs are brightness temperatures measured in channels  i(~11.0 μm) and j (~12.0 μm).
        """
        # check validity of t10, t11
        check_t1x_range(t10)
        check_t1x_range(t11)

        # average and delta emissivity
        avg = self.average_emissivity
        delta = self.delta_emissivity

        # addends
        a = self.b0
        b = self.b1 + self.b2 * ((1-avg) / avg)
        c = self.b3*(delta / avg) * ((t10 + t11) / 2)
        d1 = self.b4 + self.b5 * ((1-avg) / avg) + self.b6 * (delta / avg**2)
        d2 = (t10 - t11) / 2
        d = d1 * d2
        e = self.b7 * (t10 - t11)**2

        # land surface temperature
        self.lst = a + b + c + d + e
        return self.lst

    def _build_model(self):
        """
        Build model for __str__
        """
        self.model = self._model.format(b0=self.b0,
                                        b1=self.b1,
                                        b2=self.b2,
                                        ae=self.average_emissivity,
                                        de=self.delta_emissivity,
                                        b3=self.b3,
                                        b4=self.b4,
                                        b5=self.b5,
                                        b6=self.b6,
                                        b7=self.b7,
                                        t10=self.emissivity_t10,
                                        t11=self.emissivity_t11)

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

        self.mapcalc = formula.format(b0=self.b0,
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
