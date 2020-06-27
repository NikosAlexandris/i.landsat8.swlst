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
from constants import NUMERATOR
from constants import DENOMINATOR_Ti
from constants import DENOMINATOR_Tj
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
        self.ratio_ji_expression = str()
        self.ratio_ij_expression = str()

        self.retrieval_accuracy = float()

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

    def _numerator_for_ratio(self, ti_m, tj_m):
        """
        Build the numerator for Ratio ji or ij which is:
            Sum( (Tik - Ti_mean) * (Tjk - Tj_mean) )

        Note that 'Ratio_ji' =~ 'Ratio_ij'.
        Use this function for building GRASS GIS mapcalc expression.

        Parameters
        ----------
        modifiers
            Not explicitly needed as an input since it is sourced from the
            objects attribute self.modifiers

        ti_m
            Either of mean(Ti) or median(Ti)

        tj_m
            Either of mean(Tj) or median(Tj)

        Returns
        -------
        numerator
            The numerator expression for Ratio ji or ij

        Examples
        --------
        >>> numerator = self._numerator_for_ratio(
                ti_m = mean_ti,
                tj_m = mean_tj,
            )

        >>> numerator = self._numerator_for_ratio(
                ti_m = median_ti,
                tj_m = median_tj,
            )
        """
        numerator = ' + '.join([NUMERATOR.format(Ti=modifier_ti,
                                        Tim=ti_m,
                                        Tj=modifier_tj,
                                        Tjm=tj_m)
                            for modifier_ti, modifier_tj
                            in self.modifiers])
        return numerator

    def _denominator_for_ratio_ji(self, ti_m):
        """
        Denominator for Ratio ji which is:
        Sum ( (Tik - Ti_mean)^2 )
        """
        denominator_ji = ' + '.join([DENOMINATOR_Ti.format(Ti=modifier_ti,
                                        Tim=ti_m)
                            for modifier_ti
                            in self.modifiers_ti])
        return denominator_ji

    def _denominator_for_ratio_ij(self, tj_m):
        """
        Denominator for Ratio ij. Note that Use this function for the step-by-step
        approach to estimate the column water vapor from within the main code
        (main function) of the module i.landsat8.swlst
        """
        denominator_ij = ' + '.join([DENOMINATOR_Tj.format(Tj=modifier_tj,
                                        Tjm=tj_m)
                            for modifier_tj
                            in self.modifiers_tj])
        return denominator_ij

    def _ratio_ji_expression(self, statistic):
        """
        Returns a mapcalc expression for the Ratio ji, part of the column water
        vapor retrieval model.
        """
        if 'mean' in statistic:
            rji_numerator = self._numerator_for_ratio(
                    ti_m=DUMMY_Ti_MEAN,
                    tj_m=DUMMY_Tj_MEAN,
            )
            rji_denominator = self._denominator_for_ratio_ji(ti_m=DUMMY_Ti_MEAN)
        if 'median' in statistic:
            rji_numerator = self._numerator_for_ratio(
                    ti_m=DUMMY_Ti_MEDIAN,
                    tj_m=DUMMY_Tj_MEDIAN,
            )
            rji_denominator = self._denominator_for_ratio_ji(ti_m=DUMMY_Ti_MEDIAN)

        rji = f'( {rji_numerator} ) / ( {rji_denominator} )'
        self.ratio_ji_expression = rji
        return rji

    def _ratio_ij_expression(self, statistic):
        """
        Returns a mapcalc expression for the Ratio ij, part of the column water
        vapor retrieval model.
        """
        if 'mean' in statistic:
            rij_numerator = self._numerator_for_ratio(
                    ti_m=DUMMY_Ti_MEAN,
                    tj_m=DUMMY_Tj_MEAN,
            )
            rij_denominator = self._denominator_for_ratio_ij(tj_m=DUMMY_Tj_MEAN)

        if 'median' in statistic:
            rij_numerator = self._numerator_for_ratio(
                    ti_m=DUMMY_Ti_MEDIAN,
                    tj_m=DUMMY_Tj_MEDIAN,
            )
            rij_denominator = self._denominator_for_ratio_ij(tj_m=DUMMY_Tj_MEDIAN)

        rij = f'( {rij_numerator} ) / ( {rij_denominator} )'
        self.ratio_ij_expression = rij
        return rij

    def _big_cwv_expression_mean(self):
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

        numerator = self._numerator_for_ratio(
                        mean_ti=string_for_mean_ti,
                        mean_tj=string_for_mean_tj,
                    )
        denominator = self._denominator_for_ratio_ji(ti_m=DUMMY_Ti_MEAN)

        cwv_expression = ('eval('
               f'\ \n  ti_mean = {ti_mean},'
               f'\ \n  tj_mean = {tj_mean},'
               f'\ \n  numerator = {numerator},'
               f'\ \n  denominator = {denominator},'
               '\ \n  rji = numerator / denominator,'
               f'\ \n  {self.c0} + {self.c1} * (rji) + {self.c2} * (rji)^2)')
        return cwv_expression

    def _big_cwv_expression_mean_ij(self):
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

        numerator = self._numerator_for_ratio(
                        mean_ti=string_for_mean_ti,
                        mean_tj=string_for_mean_tj,
                    )
        denominator = self._denominator_for_ratio_ij(tj_m=DUMMY_Tj_MEAN)

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

        numerator = self._numerator_for_ratio(
                        median_ti=string_for_median_ti,
                        median_tj=string_for_median_tj,
                    )
        denominator = self._denominator_for_ratio_ji(ti_m=DUMMY_Ti_MEDIAN)

        cwv_expression = ('eval('
               f'\ \n  ti_median = {ti_median},'
               f'\ \n  tj_median = {tj_median},'
               f'\ \n  numerator = {numerator},'
               f'\ \n  denominator = {denominator},'
               '\ \n  rji = numerator / denominator,'
               f'\ \n  {self.c0} + {self.c1} * (rji) + {self.c2} * (rji)^2)')
        return cwv_expression

    def _big_cwv_expression_median_ij(self):
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

        numerator = self._numerator_for_ratio(
                        median_ti=string_for_median_ti,
                        median_tj=string_for_median_tj,
                    )
        denominator = self._denominator_for_ratio_ij(tj_m=DUMMY_Tj_MEDIAN)

        cwv_expression = ('eval('
               f'\ \n  ti_median = {ti_median},'
               f'\ \n  tj_median = {tj_median},'
               f'\ \n  numerator = {numerator},'
               f'\ \n  denominator = {denominator},'
               '\ \n  rji = numerator / denominator,'
               f'\ \n  {self.c0} + {self.c1} * (rji) + {self.c2} * (rji)^2)')
        return cwv_expression

    def _compute_retrieval_accuracy(self, **kwargs):
        """
        """
        if 'mean' in kwargs:
            numerator_ji = self._numerator_for_ratio(
                            mean_ti=string_for_mean_ti,
                            mean_tj=string_for_mean_tj,
                        )
            numerator_ij = numerator_ji
            denominator_ji = self._denominator_for_ratio_ji(ti_m=string_for_mean_ti)
            denominator_ij = self._denominator_for_ratio_ij(tj_m=string_for_mean_tj)

        if 'median' in kwargs:
            numerator_ji = self._numerator_for_ratio(
                            median_ti=string_for_median_ti,
                            median_tj=string_for_median_tj,
                        )
            numerator_ij = numerator_ji
            denominator_ji = self._denominator_for_ratio_ji(ti_m=string_for_median_ti)
            denominator_ij = self._denominator_for_ratio_ij(tj_m=string_for_median_tj)

        ratio_ji = numerator_ji / denominator_ji
        ratio_ij = numerator_ij / denominator_ij
        x2 = ratio_ji * ratio_ij
        self.retrieval_accuracy = x2

        return ratio_ji * ratio_ij

    def _big_retrieval_accuracy_expression_mean():
        """
        """
        ratio_ji = self._big_cwv_expression_mean()
        ratio_ij = self._big_cwv_expression_mean_ij
        return ratio_ji * ratio_ij

    def _big_retrieval_accuracy_expression_median():
        """
        """
        ratio_ji = self._big_cwv_expression_median()
        ratio_ij = self._big_cwv_expression_median_ij
        return ratio_ji * ratio_ij

def estimate_cwv(
        temporary_map,
        cwv_map,
        t10,
        t11,
        window_size,
        median=False,
        info=False,
    ):
    """
    Derive a column water vapor map using a single mapcalc expression based on
    eval.

            *** To Do: evaluate -- does it work correctly? *** !
    """
    cwv = Column_Water_Vapor(window_size, t10, t11)

    if median:
        cwv_expression = cwv._big_cwv_expression_median()
    else:
        cwv_expression = cwv._big_cwv_expression_mean()

    # if accuracy:
    #     if median:
    #         accuracy_expression = cwv._big_accuracy_expression_median()
    #     else:
    #         accuracy_expression = cwv._big_accuracy_expression_mean()
    # else:
    #     accuracy_expression = str()

    msg = "\n|i Estimating atmospheric column water vapor"
    if info:
        msg += '\n   Expression:\n'
        msg = replace_dummies(
                cwv_expression,
                in_ti=t10, out_ti='T10',
                in_tj=t11, out_tj='T11',
        )
    g.message(msg)

    cwv_equation = EQUATION.format(
            result=temporary_map,
            expression=cwv_expression,
    )
    grass.mapcalc(cwv_equation, overwrite=True)

    # accuracy_equation = EQUATION.format(result=outname, expression=accuracy_expression)
    # grass.mapcalc(accuracy_equation, overwrite=True)

    if info:
        run('r.info', map=temporary_map, flags='r')

    if cwv_map:
        history_cwv = f'\nColumn Water Vapor model: {cwv._equation}'
        history_cwv += f'\nSpatial window of size: {cwv.window_size}'
        title_cwv = 'Column Water Vapor'
        description_cwv = 'Column Water Vapor based on MSWVCM'
        units_cwv = 'g/cm^2'
        source1_cwv = cwv.citation
        source2_cwv = 'FixMe'
        run("r.support",
            map=temporary_map,
            title=title_cwv,
            units=units_cwv,
            description=description_cwv,
            source1=source1_cwv,
            source2=source2_cwv,
            history=history_cwv,
        )
        run('g.rename', raster=(temporary_map, cwv_map))


# reusable & stand-alone
if __name__ == "__main__":
    print ('Atmpspheric column water vapor retrieval '
           'from Landsat 8 TIRS data.'
           ' (Running as stand-alone tool?)')
