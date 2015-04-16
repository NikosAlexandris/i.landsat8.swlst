# -*- coding: utf-8 -*-
"""
@author: nik | Created on Wed Mar 18 11:28:45 2015
"""

# import average emissivities
#from ... import ...
import random
import csv_avg_emissivity_to_dictionary

EMISSIVITIES = csv_avg_emissivity_to_dictionary.main()

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
        self.emissivity_t10 = emissivity_b10 # t10  or  b10?
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
        'Jinjie; Zhao, Shaohua. 2015. "A Practical Split-Window Algorithm '
        'for Estimating Land Surface Temperature from Landsat 8 Data." '
        'Remote Sens. 7, no. 1: 647-665.')
            
    def __str__(self):
        """
        Return a string representation of the Split Window ...
        """
        msg = 'FixME'
        msg += '[b0 + (b1 + b2*((1-ae)/ae)) + b3*(de/ae) * ((t10 + t11)/2) + (b4 + b5*((1-ae)/ae) + b6*(de/ae^2))*((t10 - t11)/2) + b7*(t10 - t11)^2]\n'
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
        c = self.b3*(de / ae) * ( (self.t10 + self.t11) / 2)        
        d1 = self.b4 + self.b5 * ( (1-ae) / ae) + self.b6 * (de / ae**2)
        d2 = (self.t10 - self.t11) / 2
        d = d1 * d2
        e = self.b7 * (self.t10 - self.t11)**2
        
        # land surface temperature
        lst = a + b + c + d + e
        self.lst = lst


def test_split_window_lst():

    print " * Testing availability of constant data (global variables)"

    t10, t11 = random_digital_numbers(2)
    print "Random digital numbers for T10, T11:", t10, t11

    # emissivity_b10
    # emissivity_b11
    # b0
    # b1
    # b2
    # b3
    # b4
    # b5
    # b6
    # b7

    #swlst = SplitWindowLandSurfaceTemperature(t10, t11,
    #                                          emissivity_b10, emissivity_b11,
    #                                         b0, b1, b2, b3, b4, b5, b6, b7)
 
    print " * Testing '__str__' of class:\n", swlst
    print " * Testing '_citation' method:\n", swlst._citation
    print " * Testing 'compute_lst' method:\n", swlst.compute_lst()
    print " * Testing 'report_r2' method:\n", swlst.report_r2
     
    pass

test_split_window_lst()
