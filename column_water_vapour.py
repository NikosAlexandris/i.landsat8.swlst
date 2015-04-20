#!/usr/bin/python\<nl>\
# -*- coding: utf-8 -*-

"""
Determinatin of atmospheric column water vapour based on
Huazhong Ren, Chen Du, Qiming Qin, Rongyuan Liu, Jinjie Meng, Jing Li

@author nik | 2015-04-18 03:48:20
"""

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

    """
    Adjacent pixels

    [-1, -1] [-1, 0] [-1, 1]
    [ 0, -1] [ 0, 0] [ 0, 1]
    [ 1, -1] [ 1, 0] [ 1, 1]

    """
    def __init__(self, window_size, ti, tj):
        """
        """
        # brightness temperature maps
        #ti = t10
        #tj = t11

        # constants
        self.c0 = -9.674
        self.c1 = 0.653
        self.c2 = 9.087

        # window of N pixels
        self.window_size = window_size
        self.window_height = self.window_size
        self.window_width = self.window_size
    
        # size of window, adjacent pixels
        self.adjacent_pixels = self._derive_adjacent_pixels()
        
        # maps for transmittance
        self.ti = ti
        self.tj = tj

        # mapcalc modifiers to access neighborhood pixels
        self.modifiers_ti = self.derive_modifiers(self.ti)
        self.modifiers_tj = self.derive_modifiers(self.tj)
        self.modifiers = zip(self.modifiers_ti, self.modifiers_tj)
        print "Zipped:\n", self.modifiers
        print

     
        # required terms
        self.ti_mean = self.mean_tirs_expression(self.modifiers_ti)
        print "Expression for Ti mean:", self.ti_mean
        print
        
        self.tj_mean = self.mean_tirs_expression(self.modifiers_tj)
        print "Expression for Ti mean:", self.tj_mean
        print

        self.ratio_expression()
        self.column_water_vapour = 0.99
        
    def _citation(self):
        pass
    
    def __str__(self):
        return str(self.column_water_vapour)
    
    def _derive_adjacent_pixels(self):
        """
        Adjacent pixels
        """
        return [[col-1, row-1] for col in xrange(self.window_width) for row in xrange(self.window_height)]

    def derive_modifiers(self, tx):
        """
        Return mapcalc map modifiers for adjacent pixels for the input map tx
        """
        return [tx + str(pixel) for pixel in self.adjacent_pixels]

    def mean_tirs_expression(self, modifiers):
        """
        Means of...
        """
        tx_mean_expression = '{Tx_sum} / {Tx_length}'
        tx_sum = ' + '.join(modifiers)
        tx_length = len(modifiers)
        return tx_mean_expression.format(Tx_sum=tx_sum, Tx_length=tx_length)

    def numerator_for_ratio(self):
        """
        Numerator for Ratio ji
        """
        rji_numerator = '({Ti} - {Tim}) * ({Tj} - {Tjm})'
        return ' + '.join([rji_numerator.format(Ti=mod_ti,
                                                Tim=self.ti_mean,
                                                Tj=mod_tj,
                                                Tjm=self.tj_mean) for mod_ti, mod_tj in self.modifiers])

    def denominator_for_ratio(self):
        """
        Denominator for Ratio ji
        """
        rji_denominator = '({Ti} - {Tim})^2'
        return ' + '.join([rji_denominator.format(Ti=mod,
                                                  Tim=self.ti_mean) for mod in self.modifiers_ti])

    def ratio_expression(self):
        """
        ratio expression
        """
        rji_numerator = self.numerator_for_ratio()
        print "Numerator:\n", rji_numerator
        print

        rji_denominator = self.denominator_for_ratio()
        print "Denominator:\n", rji_denominator
        print

        rji = '( {numerator} ) / ( {denominator} )'
        rji = rji.format(numerator=rji_numerator, denominator=rji_denominator)
        print
        #print "Expression for Rji:\n", rji
        print

        self.ratio_ji = rji

    def column_water_vapour_expression(self):
        """
        """
        cwv_expression = '({c0}) + ({c1}) * ({Rji}) + ({c2}) * ({Rji})^2'
        return cwv_expression.format(c0=self.c0, c1=self.c1, Rji=self.ratio_ji, c2=self.c2)

def test_class():

    obj = Column_Water_Vapour(3, 'TIRS10', 'TIRS11')
    print obj

    print obj.column_water_vapour_expression()

test_class()

# reusable & stand-alone
if __name__ == "__main__":
    print ('Atmpspheric column water vapour retrieval '
           'from Landsat 8 TIRS data.'
           ' (Running as stand-alone tool?)\n')
