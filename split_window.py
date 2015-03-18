# -*- coding: utf-8 -*-
"""
@author: nik | Created on Wed Mar 18 11:28:45 2015
"""

#"Emissivity Class"|"TIRS-10"|"TIRS-11"
{'Cropland': {'tirs10': 0.971}, {'tirs11': 0.968}}
#"Forest"|0.995|0.996
#"Grasslands"|0.970|0.971
#"Shrublands"|0.969|0.970
#"Wetlands"|0.992|0.998
#"Waterbodies"|0.992|0.998
#"Tundra"|0.980|0.984
#"Impervious"|0.973|0.981
#"Barren Land"|0.969|0.978                                                                                                                                                                                                               
#"Snow and ice"|0.992|0.998

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
        self.t10 = t10
        self.t11= t11
        self.emissivity_t10  = emissivity_b10# t10  or  b10?
        self.emissivity_t11 = emissivity_b11
        self.b0 = b0
        self.b1 = b1
        self.b2 = b2
        self.b3 = b3
        self.b4 = b4
        self.b5 = b5
        self.b6 = b6
        self.b7 = b7
        self._r2 = float()
        self.lst = self.compute_lst()

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

    def compute_lst(self):
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