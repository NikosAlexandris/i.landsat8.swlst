#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
 MODULE:       i.landsat8.lst

 AUTHOR(S):    Nikos Alexandris <nik@nikosalexandris.net>
               Created on Wed Mar 18 10:00:53 2015

 PURPOSE:      Split Window Algorithm for Land Surface Temperature Estimation
               from Landsat8 OLI/TIRS imagery

               Source: Du, Chen; Ren, Huazhong; Qin, Qiming; Meng, Jinjie;
                       Zhao, Shaohua. 2015. "A Practical Split-Window Algorithm
                       for Estimating Land Surface Temperature from Landsat 8 Data."
                       Remote Sens. 7, no. 1: 647-665.

 COPYRIGHT:    (C) 2015 by the GRASS Development Team

               This program is free software under the GNU General Public
               License (>=v2). Read the file COPYING that comes with GRASS
               for details.
"""

"""
A new refinement of the generalized split-window algorithm proposed by Wan 
(2014) [19] is added with a quadratic term of the difference amongst the 
brightness temperatures (Ti, Tj) of the adjacent thermal infrared channels, 
which can be expressed as

LST = b0 + [b1 + b2 * (1−ε)/ε + b3 * (Δε/ε2)] * (Ti+T)/j2 + [b4 + b5 * (1−ε)/ε + b6 * (Δε/ε2)] * (Ti−Tj)/2 + b7 * (Ti−Tj)^2
(2)

where:

  - Ti and Tj are the TOA brightness temperatures measured in channels i 
(~11.0 μm) and j (~12.0 µm), respectively;
  - ε is the average emissivity of the two channels (i.e., ε = 0.5 [εi + εj]),
  - Δε is the channel emissivity difference (i.e., Δε = εi − εj);
  - bk (k = 0,1,...7) are the algorithm coefficients derived in the following 
  simulated dataset.

...

In the above equations,
    - dk (k = 0, 1...6) and ek (k = 1, 2, 3, 4) are the algorithm coefficients;
    - w is the CWV;
    - ε and ∆ε are the average emissivity and emissivity difference of two adjacent
      thermal channels, respectively, which are similar to Equation (2);
    - and fk (k = 0 and 1) is related to the influence of the atmospheric transmittance and emissivity,
      i.e., f k = f(εi,εj,τ i ,τj).
      
Note that the algorithm (Equation (6a)) proposed by Jiménez-Muñoz et al. added CWV
directly to estimate LST.

Rozenstein et al. used CWV to estimate the atmospheric transmittance (τi, τj) and
optimize retrieval accuracy explicitly.

Therefore, if the atmospheric CWV is unknown or cannot be obtained successfully,
neither of the two algorithms in Equations (6a) and (6b) will work. By contrast,
although our algorithm also needs CWV to determine the coefficients, this algorithm
still works for unknown CWVs because the coefficients are obtained regardless of the CWV,
as shown in Table 1.

...


  Source:
  - <http://www.mdpi.com/2072-4292/7/1/647/htm#sthash.ba1pt9hj.dpuf>

"""

"""
From <http://landsat.usgs.gov/band_designations_landsat_satellites.php>
Band 10 - Thermal Infrared (TIRS) 1 	10.60 - 11.19 	100 * (30)
Band 11 - Thermal Infrared (TIRS) 2 	11.50 - 12.51 	100 * (30)
"""

#%Module
#%  description: Practical split-window algorithm estimating Land Surface Temperature from Landsat 8 OLI/TIRS imagery (Du, Chen; Ren, Huazhong; Qin, Qiming; Meng, Jinjie; Zhao, Shaohua. 2015)
#%  keywords: imagery
#%  keywords: split window
#%  keywords: land surface temperature
#%  keywords: lst
#%  keywords: landsat8
#%End

#%option G_OPT_R_BASENAME_INPUT
#% key: input_prefix
#% key_desc: prefix string
#% type: string
#% label: Prefix of input bands
#% description: Prefix of Landsat8 brightness temperatures bands imported in GRASS' data base
#% required: yes
#% answer = B
#%end

or

#%option G_OPT_R_INPUTS
#% key: tirs
#% key_desc: tirs band name
#% type: string
#% label: QuickBird2 band
#% description: QuickBird2 acquired spectral band(s) (DN values)
#% multiple: yes
#% required: yes
#%end

#%option G_OPT_R_INPUT
#% key: landcover
#% key_desc: land cover map name
#% description: Land cover map
#% required : no
#%end

#%option G_OPT_R_OUTPUT
#%end

import atexit
import grass.script as grass
from grass.exceptions import CalledModuleError
from grass.pygrass.modules.shortcuts import general as g
#from grass.pygrass.modules.shortcuts import raster as r
#from grass.pygrass.raster.abstract import Info

import SplitWindowLandSurfaceTemperature


# helper functions
def cleanup():
    """
    Clean up temporary maps
    """
    grass.run_command('g.remove', flags='f', type="rast",
                      pattern='tmp.{pid}*'.format(pid=os.getpid()), quiet=True)
                      
def run(cmd, **kwargs):
    """
    Pass required arguments to grass commands (?)
    """
    grass.run_command(cmd, quiet=True, **kwargs)


def retrieve_emissivities():
    """
    Get average emissivities from an emissivity look-up table.
    This helper function returns a tuple.
    """
    EMISSIVITIES = coefficients.get_average_emissivities()

    # how to select land cover class?
    somekey = random.choice(EMISSIVITIES.keys())
    print " * Some random key:", somekey

    fields = EMISSIVITIES[somekey]._fields
    print " * Fields of namedtuple:", fields

    emissivity_b10 = EMISSIVITIES[somekey].TIRS10
    print "Average emissivity for B10:", emissivity_b10
    emissivity_b11 = EMISSIVITIES[somekey].TIRS11
    print "Average emissivity for B11:", emissivity_b11

    return (emissivity_b10, emissivity_b11)


def retrieve_column_water_vapour():
    """
    """
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

    # column water vapour coefficients (b0:b7), from dictionary
    b0 = COLUMN_WATER_VAPOUR[cwvkey].b0
    b1 = COLUMN_WATER_VAPOUR[cwvkey].b1
    b2 = COLUMN_WATER_VAPOUR[cwvkey].b2
    b3 = COLUMN_WATER_VAPOUR[cwvkey].b3
    b4 = COLUMN_WATER_VAPOUR[cwvkey].b4
    b5 = COLUMN_WATER_VAPOUR[cwvkey].b5
    b6 = COLUMN_WATER_VAPOUR[cwvkey].b6
    b7 = COLUMN_WATER_VAPOUR[cwvkey].b7
    
    print " * Coefficients (b0, b1, ..., b7) in", cwvkey,
    print ":", b0, b1, b2, b3, b4, b5, b6, b7

    rmse = COLUMN_WATER_VAPOUR[cwvkey].rmse
    print " * RMSE:", rmse
    print


def main():
    
    t10 = options['b10']
    t11 = options['b11']
    
    # get average emissivities

    # get column water vapour coefficients

    # get a SplitWindowLST class, feed with required input values
    split_window_lst = SplitWindowLST(t10, t11,
                                      emissivity_b10, emissivity_b11,
                                      b0, b1, b2, b3, b4, b5, b6, b7)

    # citation, report or add to history
    citation = split_window_lst._citation

    # compute Land Surface Temperature
    split_window_lst._compute_lst()
    lst = split_window_lst.lst

    # formula
    equation = "{lst} = {inputs}"
    swlst_formula = equation.format(lst=tmp_lst, inputs=)
    
    #
    grass.mapcalc(swlst_formula, overwrite=True)


if __name__ == "__main__":
    options, flags = grass.parser()
    atexit.register(cleanup)
    sys.exit(main())
