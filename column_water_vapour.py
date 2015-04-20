#!/usr/bin/python\<nl>\
# -*- coding: utf-8 -*-

"""
Determinatin of atmospheric column water vapour based on
Huazhong Ren, Chen Du, Qiming Qin, Rongyuan Liu, Jinjie Meng, Jing Li

@author nik | 2015-04-18 03:48:20
"""

# globals
DUMMY_Ti_MEAN = 'Mean_Ti'
DUMMY_Tj_MEAN = 'Mean_Tj'
DUMMY_Rji = 'Ratio_ji'

class Column_Water_Vapour():
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
    - tj/ti ~ Rji = SUM [ ( Tik - mean(Ti) ) * (Tjk - mean(Tj) ) ] /
                  / SUM [ ( Tik - mean(Tj) )^2 ]

    In Equation (3a):

    - c0, c1 and c2 are coefficients obtained from simulated data;
    - τ is the band effective atmospheric transmittance;
    - N is the number of adjacent pixels (excluding water and cloud pixels)
    in a spatial window of size n (i.e., N = n × n);
    - Ti,k and Tj,k are Top of Atmosphere brightness temperatures (K) of
    bands i and j for the kth pixel;
    - mean(Ti) and mean(Tj) are the mean or median brightness temperatures of
    the N pixels for the two bands.

    The regression coefficients:

    - c0 = −9.674
    - c1 = 0.653
    - c2 = 9.087

    where obtained by:

    - 946 cloud-free TIGR atmospheric profiles,
    - the new high accurate atmospheric radiative transfer model MODTRAN 5.2
    - simulating the band effective atmospheric transmittance

    Model analysis indicated that this method will obtain a CWV RMSE of about
    0.5 g/cm2. Details about the CWV retrieval can be found in:

    Ren, H.; Du, C.; Qin, Q.; Liu, R.; Meng, J.; Li, J. Atmospheric water vapor
    retrieval from landsat 8 and its validation. In Proceedings of the IEEE
    International Geosciene and Remote Sensing Symposium (IGARSS), Quebec, QC,
    Canada, July 2014; pp. 3045–3048.
    """

    def __init__(self, window_size, ti, tj):
        """
        """
        # model constants
        self.c0 = -9.674
        self.c1 = 0.653
        self.c2 = 9.087

        # window of N (= n by n) pixels
        self.window_size = window_size
        self.window_height = self.window_size
        self.window_width = self.window_size

        # size of window, adjacent pixels
        self.adjacent_pixels = self._derive_adjacent_pixels()

        # maps for transmittance
        self.ti = ti
        self.tj = tj

        # mapcalc modifiers to access neighborhood pixels
        self.modifiers_ti = self._derive_modifiers(self.ti)
        self.modifiers_tj = self._derive_modifiers(self.tj)
        self.modifiers = zip(self.modifiers_ti, self.modifiers_tj)

        # mapcalc expression for means
        self.mean_ti_expression = self._mean_tirs_expression(self.modifiers_ti)
        self.mean_tj_expression = self._mean_tirs_expression(self.modifiers_tj)

        # ratio ji
        self.ratio_ji_expression = self._ratio_ji_expression()

        # column water vapour
        self.column_water_vapour_expression = self._column_water_vapour_expression()

    def _citation(self):
        pass

    def __str__(self):
        """
        """
        msg = 'Expression for r.mapcalc to determine column water vapour: '
        return msg + str(self.column_water_vapour_expression)

    def _derive_adjacent_pixels(self):
        """
        Adjacent pixels:

        [-1, -1] [-1, 0] [-1, 1]
        [ 0, -1] [ 0, 0] [ 0, 1]
        [ 1, -1] [ 1, 0] [ 1, 1]
        """
        return [[col-1, row-1] for col in xrange(self.window_width) for row in xrange(self.window_height)]

    def _derive_modifiers(self, tx):
        """
        Return mapcalc map modifiers for adjacent pixels for the input map tx
        """
        return [tx + str(pixel) for pixel in self.adjacent_pixels]

    def _mean_tirs_expression(self, modifiers):
        """
        Means of...
        """
        tx_mean_expression = '({Tx_sum} / {Tx_length})'
        tx_sum = ' + '.join(modifiers)
        tx_length = len(modifiers)
        return tx_mean_expression.format(Tx_sum=tx_sum, Tx_length=tx_length)


    def _numerator_for_ratio(self, mean_ti, mean_tj):
        """
        Numerator for Ratio ji. Requires mean values for...
        """
        if not mean_ti:
            mean_ti = 'Ti_mean'
        if not mean_tj:
            mean_tj = 'Tj_mean'

        rji_numerator = '({Ti} - {Tim}) * ({Tj} - {Tjm})'
        return ' + '.join([rji_numerator.format(Ti=mod_ti,
                                                Tim=mean_ti,
                                                Tj=mod_tj,
                                                Tjm=mean_tj) for mod_ti, mod_tj in self.modifiers])

    def _denominator_for_ratio(self, mean_ti):
        """
        Denominator for Ratio ji
        """
        if not mean_ti:
            mean_ti = 'Ti_mean'

        rji_denominator = '({Ti} - {Tim})^2'
        return ' + '.join([rji_denominator.format(Ti=mod,
                                                  Tim=mean_ti) for mod in self.modifiers_ti])

    def _ratio_ji_expression(self):
        """
        ratio expression
        """
        rji_numerator = self._numerator_for_ratio(mean_ti=DUMMY_Ti_MEAN, mean_tj=DUMMY_Tj_MEAN)
        rji_denominator = self._denominator_for_ratio(mean_ti=DUMMY_Ti_MEAN)
        rji = '( {numerator} ) / ( {denominator} )'
        return rji.format(numerator=rji_numerator, denominator=rji_denominator)

    def _column_water_vapour_complete_expression(self):
        """
        """
        cwv_expression = '({c0}) + ({c1}) * ({Rji}) + ({c2}) * ({Rji})^2'
        return cwv_expression.format(c0=self.c0,
                                     c1=self.c1,
                                     Rji=self.ratio_ji_expression,
                                     c2=self.c2)

    def _column_water_vapour_expression(self):
        """
        """
        cwv_expression = '({c0}) + ({c1}) * ({Rji}) + ({c2}) * ({Rji})^2'
        return cwv_expression.format(c0=self.c0,
                                     c1=self.c1,
                                     Rji=DUMMY_Rji,
                                     c2=self.c2)


def test_class():
    
    print
    print "Testing the Column_Water_Vapour class"
    print

    obj = Column_Water_Vapour(3, 'TIRS10', 'TIRS11')
    print " | Testing the '__str__' method:\n\n ", obj
    print
    
    print " | Adjacent pixels:", obj.adjacent_pixels
    print

    print " | Map Ti:", obj.ti
    print " | Map Tj:", obj.tj
    print

    print " | Modifiers for Ti:", obj.modifiers_ti
    print " | Modifiers for Tj:", obj.modifiers_tj
    print " | Zipped modifiers_tj:", obj.modifiers
    print

    print " | Expression for Ti mean:", obj.mean_ti_expression
    print " | Expression for Tj mean:", obj.mean_tj_expression
    print

    print " | Numerator for Ratio (method):", obj._numerator_for_ratio('TestValue_TiMean', 'TestValue_TjMean')
    print " | Denominator for Ratio (method):", obj._denominator_for_ratio('TestValue_TiMean')

    print " | Ratio ji expression for mapcalc:", obj.ratio_ji_expression
    print

    print ' | The "Column water vapour retrieval expression for mapcalc":\n\n', obj.column_water_vapour_expression
    print

# reusable & stand-alone
if __name__ == "__main__":
    print ('Atmpspheric column water vapour retrieval '
           'from Landsat 8 TIRS data.'
           ' (Running as stand-alone tool?)\n')

    test_class()

