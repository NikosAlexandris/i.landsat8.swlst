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


# helper functions
def check_t1x_range(dn):
    """
    Check if digital numbers for T10, T11, lie inside
    the expected range [1, 65535]
    """
    if dn < 1 or dn > 65535:
        raise ValueError('The input value for T10 is out of '
                         'expected range [1,65535]')
    else:
        return True


def random_digital_numbers(count=3):
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


def random_digital_number():
    """
    Return one random of Digital Number values for testing purposes
    """
    return random.randint(1, 65535)


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

    def __init__(self, t10, t11, emissivity_b10, emissivity_b11, cwv_subrange):
        """
        Create a class object for Split Window algorithm

        Required inputs:
        - B10
        - B11 -- ToAR?
        - land cover class?
        - average emissivities for B10, B11
        - subrange for column water vapour
        """
        self.citation = ('Du, Chen; Ren, Huazhong; Qin, Qiming; Meng, '
                         'Jinjie; Zhao, Shaohua. 2015. '
                         '"A Practical Split-Window Algorithm '
                         'for Estimating Land Surface Temperature from '
                         'Landsat 8 Data." '
                         'Remote Sens. 7, no. 1: 647-665.')

        if check_t1x_range(t10):
            self.t10 = t10

        if check_t1x_range(t11):
            self.t11 = t11

        # emissivities
        self.emissivity_t10 = float(emissivity_b10)  # t10  or  b10?
        self.emissivity_t11 = float(emissivity_b11)
        self.average_emissivity = 0.5 * (self.emissivity_t10 + self.emissivity_t11)
        self.delta_emissivity = self.emissivity_t10 - self.emissivity_t11

        # column water vapour
        self.cwv_subrange = random.choice(COLUMN_WATER_VAPOUR.keys())  # ***
        self._set_cwv_coefficients()

        # Root Mean Square Error for coefficients
        self._set_rmse()

        self._model = 'Add model here...'
        self._mapcalc = 'formula'
        self.lst = self._compute_lst()

    def __str__(self):
        """
        Return a string representation of the Split Window ...
        """
        equation = '   > The equation: '
        equation += ('[b0 + '
                     '(b1 + '
                     'b2*((1-ae)/ae)) + '
                     'b3*(de/ae) * ((t10 + t11)/2) + '
                     '(b4 + '
                     'b5*((1-ae)/ae) + '
                     'b6*(de/ae^2))*((t10 - t11)/2) + '
                     'b7*(t10 - t11)^2]')
        model_msg = '   > The model: '
        model = ('[{b0} + '
                 '({b1} + '
                 '{b2}*((1-{ae})/{ae})) + '
                 '{b3}*({de}/{ae}) * (({t10} + {t11})/2) + '
                 '({b4} + '
                 '{b5}*((1-{ae})/{ae}) + '
                 '{b6}*({de}/{ae}^2))*(({t10} - {t11})/2) + '
                 '{b7}*({t10} - {t11})^2]\n')
        model = model.format(b0=self.b0,
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

        return equation + '\n' + model_msg + model

    def _set_cwv_coefficients(self):
        """
        Set the model's coefficients for the requested satellite and year
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
        """
        return self.cwv_coefficients

    def _set_rmse(self):
        self.rmse = COLUMN_WATER_VAPOUR[self.cwv_subrange].rmse

    def report_rmse(self):
        """
        Report the associated R^2 value for the coefficients in question
        """
        msg = "Asociated RMSE: "
        return msg + str(self.rmse)


    def _compute_lst(self):
        """
        Compute Land Surface Temperature
        """

        # average emissivity
        avg = self.average_emissivity

        # delta emissivity
        delta = self.delta_emissivity

        # addends
        a = self.b0
        b = self.b1 + self.b2 * ((1-avg) / avg)
        c = self.b3*(delta / avg) * ((self.t10 + self.t11) / 2)
        d1 = self.b4 + self.b5 * ((1-avg) / avg) + self.b6 * (delta / avg**2)
        d2 = (self.t10 - self.t11) / 2
        d = d1 * d2
        e = self.b7 * (self.t10 - self.t11)**2

        # land surface temperature
        self.lst = a + b + c + d + e
        return self.lst

    def _mapcalc(self):
        """
        Return equation for GRASS GIS' mapcalc
        """
        # formula = '{c0} + {c1}*{dummy} + {c2}*{dummy}^2'
        #formula = EQUATIONS[self.author].formula  # look in equations.py
        #self.mapcalc = formula.format(c0=self.c0, c1=self.c1,
        #                              dummy=DUMMY_MAPCALC_STRING, c2=self.c2)
        pass

def test_split_window_lst():

    print " * Testing availability of constant data (global variables)"
    print

    t10 = random_digital_numbers(1)
    t11 = random.choice(((t10 + 500), (t10 - 500)))
    print " * Random 12-bit digital numbers for T10, T11:", t10, t11
    print

    # get emissivities
    EMISSIVITIES = coefficients.get_average_emissivities()
    print "\n * Dictionary for average emissivities:\n", EMISSIVITIES
    print

    somekey = random.choice(EMISSIVITIES.keys())
    print " * Some random key:", somekey

    fields = EMISSIVITIES[somekey]._fields
    print " * Fields of namedtuple:", fields

    random_field = random.choice(fields)
    print " * Some random field:", random_field

    command = 'EMISSIVITIES.[{key}].{field} ='
    command = command.format(key=somekey, field=random_field)
    print " * Example of retrieving values (named tuple): " + command,
    print EMISSIVITIES[somekey].TIRS10, EMISSIVITIES[somekey].TIRS11
    print "\n >>> FIXME -- how to call a named tuple non-interactively?\n"

    emissivity_b10 = EMISSIVITIES[somekey].TIRS10
    print "Average emissivity for B10:", emissivity_b10, "|Type:", type(emissivity_b10)
    emissivity_b11 = EMISSIVITIES[somekey].TIRS11
    print "Average emissivity for B11:", emissivity_b11

    # ---------------------------------------------------------
    COLUMN_WATER_VAPOUR = coefficients.get_column_water_vapour()
    print "\n * Dictionary for column water vapour coefficients:\n",
    print COLUMN_WATER_VAPOUR
    print

    cwvkey = random.choice(COLUMN_WATER_VAPOUR.keys())
    print " * Some random key:", cwvkey

    cwvfields = COLUMN_WATER_VAPOUR[cwvkey]._fields
    print " * Fields of namedtuple:", cwvfields

    random_cwvfield = random.choice(cwvfields)
    print " * Some random field:", random_cwvfield

    command = 'COLUMN_WATER_VAPOUR.[{key}].{field} ='
    command = command.format(key=cwvkey, field=random_cwvfield)
    print " * Example of retrieving values (named tuple): " + command,
    print COLUMN_WATER_VAPOUR[cwvkey].subrange

    print "\n >>> FIXME -- how to call a named tuple non-interactively?\n"

    swlst = SplitWindowLST(t10, t11, emissivity_b10, emissivity_b11, cwvkey)
    print "Create object and test '__str__' of SplitWindowLST() class:\n", swlst
    print

    b0, b1, b2, b3, b4, b5, b6, b7 = swlst.cwv_coefficients
    print " * Coefficients (b0, b1, ..., b7) in <", cwvkey,
    print "> :", b0, b1, b2, b3, b4, b5, b6, b7

    print " * RMSE:", swlst.rmse
    print

    print " * Checking 'citation':", swlst.citation
    print

    print " * Checking the '_compute_lst' method:", swlst._compute_lst
    swlst._compute_lst()  # compute it first!
    print " * Return the LST value:", swlst.lst
    print

    print " * Checking the 'report_rmse' method:", swlst.report_rmse
    print " * Testing the 'report_rmse' method:", swlst.report_rmse()
test_split_window_lst()
