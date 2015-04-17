# -*- coding: utf-8 -*-
"""
@author: nik | Created on Wed Mar 18 11:28:45 2015
"""

# import average emissivities
import random
import csv_to_dictionary as coefficients

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
    purposes
    """
    digital_numbers = []

    for dn in range(0, count):
        digital_numbers.append(random.randint(1, 65535))

    return digital_numbers


def random_digital_number():
    """
    Return one random of Digital Number values for testing purposes
    """
    return random.randint(1, 65535)


class SplitWindowLandSurfaceTemperature():
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
    def __init__(self, t10, t11, emissivity_b10, emissivity_b11, b0, b1, b2, b3, b4, b5, b6, b7):
        """
        Create a class object for Split Window algorithm ... LST ...
        """
        if check_t1x_range(t10):
            self.t10 = t10
        if check_t1x_range(t11):
            self.t11 = t11
        self.emissivity_t10 = emissivity_b10  # t10  or  b10?
        self.emissivity_t11 = emissivity_b11
        self._ae = float()
        self._de = float()
        self.b0 = b0
        self.b1 = b1
        self.b2 = b2
        self.b3 = b3
        self.b4 = b4
        self.b5 = b5
        self.b6 = b6
        self.b7 = b7
        self.r2 = float()
        self.lst = self._compute_lst()

    def _citation(self):
        """
        Citation
        """
        self._citation = ('Du, Chen; Ren, Huazhong; Qin, Qiming; Meng, '
                          'Jinjie; Zhao, Shaohua. 2015. '
                          '"A Practical Split-Window Algorithm '
                          'for Estimating Land Surface Temperature from '
                          'Landsat 8 Data." '
                          'Remote Sens. 7, no. 1: 647-665.')

    def __str__(self):
        """
        Return a string representation of the Split Window ...
        """
        msg = 'FixMe <<<'
        msg += ('[b0 + '
                '(b1 + '
                'b2*((1-ae)/ae)) + '
                'b3*(de/ae) * ((t10 + t11)/2) + '
                '(b4 + '
                'b5*((1-ae)/ae) + '
                'b6*(de/ae^2))*((t10 - t11)/2) + '
                'b7*(t10 - t11)^2]\n')
        return msg + '  ' + self._model + '\n'

    def report_r2(self):
        """
        Report the associated R^2 value for the coefficients in question
        """
        msg = "Asociated R^2: "
        return msg + str(self._r2)

    def _compute_lst(self):
        """
        Compute Land Surface Temperature
        """

        # average emissivity
        ae = 0.5 * (self.emissivity_b10 + self.emissivity_b11)

        # delta emissivity
        de = self.emissivity_b10 - self.emissivity_b11

        # addends
        a = self.b0
        b = self.b1 + self.b2 * ((1-ae) / ae)
        c = self.b3*(de / ae) * ((self.t10 + self.t11) / 2)
        d1 = self.b4 + self.b5 * ((1-ae) / ae) + self.b6 * (de / ae**2)
        d2 = (self.t10 - self.t11) / 2
        d = d1 * d2
        e = self.b7 * (self.t10 - self.t11)**2

        # land surface temperature
        lst = a + b + c + d + e
        self.lst = lst


def test_split_window_lst():

    print " * Testing availability of constant data (global variables)"
    print

    t10, t11 = random_digital_numbers(2)
    print " * Random digital numbers for T10, T11:", t10, t11
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
    emissivity_b11 = EMISSIVITIES[somekey].TIRS11
    
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

    b0 = COLUMN_WATER_VAPOUR[cwvkey].b0
    b1 = COLUMN_WATER_VAPOUR[cwvkey].b1
    b2 = COLUMN_WATER_VAPOUR[cwvkey].b2
    b3 = COLUMN_WATER_VAPOUR[cwvkey].b3
    b4 = COLUMN_WATER_VAPOUR[cwvkey].b4
    b5 = COLUMN_WATER_VAPOUR[cwvkey].b5
    b6 = COLUMN_WATER_VAPOUR[cwvkey].b6
    b7 = COLUMN_WATER_VAPOUR[cwvkey].b7
    print " * Coefficients b0, b1, ..., b7:", b0, b1, b2, b3, b4, b5, b6, b7

    rmse = COLUMN_WATER_VAPOUR[cwvkey].rmse
    print " * RMSE:", rmse
    print


    swlst = SplitWindowLandSurfaceTemperature(t10, t11,
                                              emissivity_b10, emissivity_b11,
                                              b0, b1, b2, b3, b4, b5, b6, b7)

    print " * Testing '__str__' of class:\n", swlst
    print " * Testing '_citation' method:\n", swlst._citation
    print " * Testing 'compute_lst' method:\n", swlst.compute_lst()
    print " * Testing 'report_r2' method:\n", swlst.report_r2

    pass

test_split_window_lst()
