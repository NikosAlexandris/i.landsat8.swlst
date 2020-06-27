#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Determining atmospheric column water vapor based on
Huazhong Ren, Chen Du, Qiming Qin, Rongyuan Liu, Jinjie Meng, Jing Li

@author nik | Created on 2015-04-18 03:48:20 | Updated on June 2020
"""

from citations import CITATION_COLUMN_WATER_VAPOR
from constants import DUMMY_Ti_MEAN
from constants import DUMMY_Tj_MEAN
from constants import DUMMY_Rji
from constants import EQUATION
from randomness import random_adjacent_pixel_values
from grass.pygrass.modules.shortcuts import general as g
from dummy_mapcalc_strings import replace_dummies
import grass.script as grass
from helpers import run

class Column_Water_Vapor():
    """
    Retrieving atmospheric column water vapor from Landsat8 TIRS data based on
    the modified split-window covariance and variance ratio (MSWCVR).

    -------------------------------------------------------------------------
    *Note,* this class produces valid expressions for GRASS GIS' mapcalc raster
    processing module and does not directly compute column water vapor
    estimations.
    -------------------------------------------------------------------------

    With a vital assumption that the atmosphere is unchanged over the
    neighboring pixels, the MSWCVR method relates the atmospheric CWV to the
    ratio of the upward transmittances in two thermal infrared bands, whereas
    the transmittance ratio can be calculated based on the TOA brightness
    temperatures of the two bands.

    Considering N adjacent pixels, the CWV in the MSWCVR method is estimated
    as:

    - cwv  =  c0  +  c1  *  (tj / ti)  +  c2  *  (tj / ti)^2

    - tj/ti ~ Rji = SUM [ ( Tik - Ti_mean ) * ( Tjk - Tj_mean ) ] /
                    SUM [ ( Tik - Ti_mean )^2 ]

    In Equation (3a):

    - c0, c1 and c2 are coefficients obtained from simulated data;

    - τ is the band effective atmospheric transmittance;

    - N is the number of adjacent pixels (excluding water and cloud pixels)
    in a spatial window of size n (i.e., N = n × n);

    - Ti,k and Tj,k are Top of Atmosphere brightness temperatures (K) of
    bands i and j for the kth pixel;

    - mean(Ti) and mean(Tj) or median(Ti) and median(Tj) are the mean or median
      brightness temperatures of the N pixels for the two bands


    The regression coefficients:

    ==================================================================

    * NOTE, there is a typo in the paper!

    [0] Du, Chen; Ren, Huazhong; Qin, Qiming; Meng, Jinjie; Zhao,
    Shaohua. 2015. "A Practical Split-Window Algorithm for Estimating
    Land Surface Temperature from Landsat 8 Data." Remote Sens. 7, no.
    1: 647-665.
    http://www.mdpi.com/2072-4292/7/1/647/htm\#sthash.ba1pt9hj.dpuf

    from which the equation's coefficients are (also) published.

    The correct order of constants is as below, source from the
    referenced paper below.

    ==================================================================

    - c2 = -9.674
    - c1 = 0.653
    - c0 = 9.087

    where obtained by:

    - 946 cloud-free TIGR atmospheric profiles,
    - the new high accurate atmospheric radiative transfer model MODTRAN 5.2
    - simulating the band effective atmospheric transmittance

    Model analysis indicated that this method will obtain a CWV RMSE of about
    0.5 g/cm2. Details about the CWV retrieval can be found in:

    Ren, H., Du, C., Liu, R., Qin, Q., Yan, G., Li, Z. L., & Meng, J. (2015).
    Atmospheric water vapor retrieval from Landsat 8 thermal infrared images.
    Journal of Geophysical Research: Atmospheres, 120(5), 1723-1738.


    Old reference:

    Ren, H.; Du, C.; Qin, Q.; Liu, R.; Meng, J.; Li, J. Atmospheric water vapor
    retrieval from landsat 8 and its validation. In Proceedings of the IEEE
    International Geosciene and Remote Sensing Symposium (IGARSS), Quebec, QC,
    Canada, July 2014; pp. 3045–3048.
    """

    def __init__(self, window_size, ti, tj):
        """
        """

        # citation
        self.citation = CITATION_COLUMN_WATER_VAPOR

        # model constants
        self.c2 = -9.674
        self.c1 = 0.653
        self.c0 = 9.087

        self._equation = ('c0  + '
                          'c1 * (tj / ti)  + '
                          'c2 * (tj / ti)^2')

        self._model = ('{c0} + '
                       '{c1} * ({tj} / {ti}) + '
                       '{c2} * ({tj} / {ti})^2')

        # window of N (= n by n) pixels, adjacent pixels
        assert window_size % 2 != 0, "Window size should be an even number!"
        assert window_size >= 7, "Window size should be equal to/larger than 7."
        self.window_size = window_size

        self.window_height = self.window_size
        self.window_width = self.window_size
        self.adjacent_pixels = self._derive_adjacent_pixels()

        # maps for transmittance
        self.ti = ti
        self.tj = tj

        # mapcalc modifiers to access neighborhood pixels
        self.modifiers_ti = self._derive_modifiers(self.ti)
        self.modifiers_tj = self._derive_modifiers(self.tj)
        self.modifiers = list(zip(self.modifiers_ti, self.modifiers_tj))

        # mapcalc expression for means; medians
        self.mean_ti_expression = self._mean_tirs_expression(self.modifiers_ti)
        self.mean_tj_expression = self._mean_tirs_expression(self.modifiers_tj)
        self.median_ti_expression = self._median_tirs_expression(self.modifiers_ti)
        self.median_tj_expression = self._median_tirs_expression(self.modifiers_tj)

        # mapcalc expression for ratio ji
        self.ratio_ji_expression = self._ratio_ji_expression()


    def __str__(self):
        """
        The object's self string
        """
        msg = (f'- Window size: {self.window_size} by + {self.window_size}'
        '- Expression for r.mapcalc to determine column water vapor: ')
        return msg + str(self.column_water_vapor_expression)

    # def compute_column_water_vapor(self, tik, tjk):
    #     """
    #     Compute the column water vapor based on lists of input Ti and Tj
    #     values.

    #     This is a single value production function. It does not read or return
    #     a map.
    #     """
    #     # feed with N pixels
    #     ti_mean = sum(tik) / len(tik)
    #     tj_mean = sum(tjk) / len(tjk)

    #     # numerator: sum of all (Tik - Ti_mean) * (Tjk - Tj_mean)
    #     numerator_ji_terms = []
    #     for ti, tj in zip(tik, tjk):
    #         numerator_ji_terms.append((ti - ti_mean) * (tj - tj_mean))
    #     numerator_ji = sum(numerator_ji_terms) * 1.0

    #     # denominator:  sum of all (Tik - Ti_mean)^2
    #     denominator_ji_terms = []
    #     for ti in tik:
    #         term = (ti - ti_mean)**2
    #         denominator_ji_terms.append(term)
    #     denominator_ji = sum(denominator_ji_terms) * 1.0

    #     ratio_ji = numerator_ji / denominator_ji
    #     cwv = self.c0 + self.c1 * (ratio_ji) + self.c2 * ((ratio_ji) ** 2)
    #     return cwv

    def _derive_adjacent_pixels(self):
        """
        Derive a window/grid of "adjacent" pixels:

        [-1, -1] [-1, 0] [-1, 1]
        [ 0, -1] [ 0, 0] [ 0, 1]
        [ 1, -1] [ 1, 0] [ 1, 1]
        """
        # center row indexing
        half_height = (self.window_height - 1) // 2

        # center col indexing
        half_width = (self.window_width - 1) // 2

        return [[col, row]
                for col in range(-half_width + 1, half_width)
                for row in range(-half_height + 1, half_height)]

    def _derive_modifiers(self, tx):
        """
        Return mapcalc map modifiers for adjacent pixels for the input map tx
        """
        return [tx + str(pixel)
                for pixel
                in self.adjacent_pixels]

    def _mean_tirs_expression(self, modifiers):
        """
        Return mapcalc expression for window means based on the given mapcalc
        pixel modifiers.
        """
        tx_sum = '(' + ' + '.join(modifiers) + ')'
        tx_length = len(modifiers)
        tx_mean_expression = f'{tx_sum} / {tx_length}'
        return tx_mean_expression

    def _median_tirs_expression(self, modifiers):
        """
        Parameters
        ----------
        modifiers
            Pixel modifiers to access adjacent pixels using GRASS GIS' mapcalc
            syntax

        Returns
        -------
        tx_mean_expression
            A mapcalc expression for window medians based on the given mapcalc
            pixel modifiers.
        """
        modifiers = ', '.join(modifiers)
        tx_median_expression = f'median({modifiers})'
        return tx_median_expression

    def _numerator_for_ratio(self, mean_ti, mean_tj):
        """
        Numerator for Ratio ji. Use this function for the step-by-step approach
        to estimate the column water vapor from within the main code (main
        function) of the module i.landsat8.swlst
        """
        if not mean_ti:
            mean_ti = 'Ti_mean'

        if not mean_tj:
            mean_tj = 'Tj_mean'

        rji_numerator = '(' + '({Ti} - {Tim}) * ({Tj} - {Tjm})' + ')'

        return ' + '.join([rji_numerator.format(Ti=mod_ti,
                                                Tim=mean_ti,
                                                Tj=mod_tj,
                                                Tjm=mean_tj)
                          for mod_ti, mod_tj in self.modifiers])

    def _numerator_for_ratio_big(self, **kwargs):
        """
        Numerator for Ratio ji. Requires two strings, one to represent the mean
        of 'Ti's ('mean_ti') and one for the mean of 'Tj's ('mean_tj'). Use
        this function for the big mapcalc expression.

        Example:
                _numerator_for_ratio_big(mean_ti='Some_String',
                                        mean_tj='Another_String')
        """
        mean_ti = kwargs.get('mean_ti', 'ti_mean')
        mean_tj = kwargs.get('mean_tj', 'tj_mean')
        if mean_ti and mean_tj:
            terms = '({Ti} - {Tim}) * ({Tj} - {Tjm})'
            terms = ' + '.join([terms.format(Ti=mod_ti,
                                         Tim=mean_ti,
                                         Tj=mod_tj,
                                         Tjm=mean_tj)
                           for mod_ti, mod_tj in self.modifiers])

        median_ti = kwargs.get('median_ti', 'ti_median')
        median_tj = kwargs.get('median_tj', 'tj_median')
        if median_ti and median_tj:
            terms = '({Ti} - {Tim}) * ({Tj} - {Tjm})'
            terms = ' + '.join([terms.format(Ti=mod_ti,
                                         Tim=median_ti,
                                         Tj=mod_tj,
                                         Tjm=median_tj)
                           for mod_ti, mod_tj in self.modifiers])
        return terms

    def _denominator_for_ratio(self, mean_ti):
        """
        Denominator for Ratio ji. Use this function for the step-by-step
        approach to estimate the column water vapor from within the main code
        (main function) of the module i.landsat8.swlst
        """
        if not mean_ti:
            mean_ti = 'Ti_mean'

        rji_denominator = '({Ti} - {Tim})^2'

        return ' + '.join([rji_denominator.format(Ti=mod,
                                                  Tim=mean_ti)
                          for mod in self.modifiers_ti])

    def _denominator_for_ratio_big(self, **kwargs):
        """
        Denominator for Ratio ji. Use this function for the big mapcalc
        expression.

        Example:
                _denominator_for_ratio_big(mean_ti='Some_String')
        """
        mean_ti = kwargs.get('mean_ti', 'ti_mean')
        terms = '({Ti} - {Tim})^2'
        terms = ' + '.join([terms.format(Ti=mod,
                                         Tim=mean_ti)
                           for mod in self.modifiers_ti])

        return terms

    def _ratio_ji_expression(self):
        """
        Returns a mapcalc expression for the Ratio ji, part of the column water
        vapor retrieval model.
        """
        rji_numerator = self._numerator_for_ratio(mean_ti=DUMMY_Ti_MEAN,
                                                  mean_tj=DUMMY_Tj_MEAN)
        rji_denominator = self._denominator_for_ratio(mean_ti=DUMMY_Ti_MEAN)
        rji = f'( {rji_numerator} ) / ( {rji_denominator} )'
        return rji

    def _column_water_vapor_expression(self):
        """
        Use this function for the step-by-step approach to estimate the column
        water vapor from within the main code (main function) of the module
        i.landsat8.swlst
        """
        Rji = DUMMY_Rji
        cwv_expression = f'({self.c0}) + ({self.c1}) * ({Rji}) + ({self.c2}) * ({Rji})^2'
        return cwv_expression

    def _big_cwv_expression(self):
        """
        Build and return a valid mapcalc expression for deriving a Column
        Water Vapor map from Landsat8's brightness temperature channels
        B10, B11 based on the MSWCVM method (see citation).
        """
        modifiers_ti = self._derive_modifiers(self.ti)
        ti_mean = self._mean_tirs_expression(modifiers_ti)
        string_for_mean_ti = 'ti_mean'

        modifiers_tj = self._derive_modifiers(self.tj)
        tj_mean = self._mean_tirs_expression(modifiers_tj)
        string_for_mean_tj = 'tj_mean'

        numerator = self._numerator_for_ratio_big(
                        mean_ti=string_for_mean_ti,
                        mean_tj=string_for_mean_tj,
                    )
        denominator = self._denominator_for_ratio_big(mean_ti=string_for_mean_ti)

        cwv_expression = ('eval('
               f'\ \n  ti_mean = {ti_mean},'
               f'\ \n  tj_mean = {tj_mean},'
               f'\ \n  numerator = {numerator},'
               f'\ \n  denominator = {denominator},'
               '\ \n  rji = numerator / denominator,'
               f'\ \n  {self.c0} + {self.c1} * (rji) + {self.c2} * (rji)^2)')
        return cwv_expression

    def _big_cwv_expression_median(self):
        """
        Build and return a valid mapcalc expression for deriving a Column
        Water Vapor map from Landsat8's brightness temperature channels
        B10, B11 based on the MSWCVM method (see citation).
        """
        modifiers_ti = self._derive_modifiers(self.ti)
        ti_median = self._median_tirs_expression(modifiers_ti)
        string_for_median_ti = 'ti_median'

        modifiers_tj = self._derive_modifiers(self.tj)
        tj_median = self._median_tirs_expression(modifiers_tj)
        string_for_median_tj = 'tj_median'

        numerator = self._numerator_for_ratio_big(
                        median_ti=string_for_median_ti,
                        median_tj=string_for_median_tj,
                    )
        denominator = self._denominator_for_ratio_big(median_ti=string_for_median_ti)

        cwv_expression = ('eval('
               f'\ \n  ti_median = {ti_median},'
               f'\ \n  tj_median = {tj_median},'
               f'\ \n  numerator = {numerator},'
               f'\ \n  denominator = {denominator},'
               '\ \n  rji = numerator / denominator,'
               f'\ \n  {self.c0} + {self.c1} * (rji) + {self.c2} * (rji)^2)')
        return cwv_expression


def estimate_cwv_big_expression(
        outname,
        cwv_output,
        t10,
        t11,
        cwv_expression,
        quiet=True,
    ):
    """
    Derive a column water vapor map using a single mapcalc expression based on
    eval.

            *** To Do: evaluate -- does it work correctly? *** !
    """
    msg = "\n|i Estimating atmospheric column water vapor "
    if quiet:
        msg += '| Expression:\n'
    g.message(msg)

    if quiet:
        msg = replace_dummies(cwv_expression,
                              in_ti=t10, out_ti='T10',
                              in_tj=t11, out_tj='T11')
        msg += '\n'
        g.message(msg)

    cwv_equation = EQUATION.format(result=outname, expression=cwv_expression)
    grass.mapcalc(cwv_equation, overwrite=True)

    if quiet:
        run('r.info', map=outname, flags='r')

    if cwv_output:

        history_cwv = 'FixMe -- Column Water Vapor model: '
        history_cwv += 'FixMe -- Add equation?'
        title_cwv = 'Column Water Vapor'
        description_cwv = 'Column Water Vapor'
        units_cwv = 'g/cm^2'
        source1_cwv = cwv.citation
        source2_cwv = 'FixMe'
        run("r.support",
            map=outname,
            title=title_cwv,
            units=units_cwv,
            description=description_cwv,
            source1=source1_cwv,
            source2=source2_cwv,
            history=history_cwv,
        )
        run('g.rename', raster=(outname, cwv_output))


# reusable & stand-alone
if __name__ == "__main__":
    print ('Atmpspheric column water vapor retrieval '
           'from Landsat 8 TIRS data.'
           ' (Running as stand-alone tool?)')
