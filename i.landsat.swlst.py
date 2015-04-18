#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
 MODULE:       i.landsat8.lst

 AUTHOR(S):    Nikos Alexandris <nik@nikosalexandris.net>
               Created on Wed Mar 18 10:00:53 2015

 PURPOSE:      Split Window Algorithm for Land Surface Temperature Estimation
               from Landsat8 OLI/TIRS imagery


               +--------+   +--------------------------+                               
               |Landsat8+--->Cloud screen & calibration|                               
               +--------+   +---+--------+-------------+                               
                                |        |                                             
                                |        |                                             
                              +-v-+   +--v-+                                           
                              |OLI|   |TIRS|                                           
                              +-+-+   +--+-+                                           
                                |        |                                             
                                |        |                                             
                             +--v-+   +--v-------------------+          +-------------+
                             |NDVI|   |Brightness temperature+---------->MSWCVM method|
              +----------+   +--+-+   +--+-------------------+          +----------+--+
              |Land cover|      |        |                                         |   
              +----------+      |        |                                         |   
                      |       +-v-+   +--v-------------------+    +----------------v--+
                      |       |FVC|   |Split Window Algorithm|    |Column Water Vapour|
+---------------------v--+    +-+-+   +-------------------+--+    +----------------+--+
|Emissivity look|up table|      |                         |                        |   
+---------------------+--+      |                         |                        |   
                      |      +--v--------------------+    |    +-------------------v--+
                      +------>Pixel emissivity ei, ej+--> | <--+Algorithm coefficients|
                             +-----------------------+    |    +----------------------+
                                                          |                            
                                                          |                            
                                          +---------------v--+                         
                                          |LST and emissivity|                         
                                          +------------------+                         

        (Figure 3)  -- FixMe


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

#%flag
#%  key: i
#%  description: Print out calibration equations
#%end

#%flag
#%  key: k
#%  description: Keep current computational region settings
#%end

#%flag
#%   key: c
#% description: Apply the Kelvin colortable to the LST map
#%end

#%option G_OPT_R_BASENAME_INPUT
#% key: input_prefix
#% key_desc: prefix string
#% type: string
#% label: Prefix of input bands
#% description: Prefix of Landsat8 brightness temperatures bands imported in GRASS' data base
#% required: no
#% answer = B
#%end

# OR

#%option G_OPT_R_INPUT
#% key: t10
#% key_desc: Temperature (10)
#% description: Brightness temperature (K) from Landsat8 band 10
#% required : yes
#%end

#%option G_OPT_R_INPUT
#% key: t11
#% key_desc: Temperature (11)
#% description: Brightness temperature (K) from Landsat 8 band 11
#% required : yes
#%end

#%option G_OPT_R_INPUT
#% key: qab
#% key_desc: QA band
#% description: Landsat 8 quality assessment band
#% required : yes
#%end

#%option G_OPT_R_INPUT
#% key: e10
#% key_desc: Emissivity B10
#% description: Emissivity for Landsat 8 band 10
#% required : no
#%end

#%option G_OPT_R_INPUT
#% key: e11
#% key_desc: Emissivity B11
#% description: Emissivity for Landsat 8 band 11
#% required : no
#%end

#%option G_OPT_R_INPUT
#% key: landcover
#% key_desc: land cover map name
#% description: Land cover map
#% required : no
#%end

#%option
#% key: emissivity_class
#% key_desc: emissivity class
#% description: Land cover class to retrieve average emissivity from a look-up table (case sensitive)
#% options: Cropland,Forest,Grasslands,Shrublands,Wetlands,Waterbodies,Tundra,Impervious,Barren,Snow
#% required: no
#%end

#%option G_OPT_R_OUTPUT
#%end

import os
import sys
sys.path.insert(1, os.path.join(os.path.dirname(sys.path[0]),
                                'etc', 'i.landsat.swlst'))

import atexit
import grass.script as grass
#from grass.exceptions import CalledModuleError
from grass.pygrass.modules.shortcuts import general as g
#from grass.pygrass.modules.shortcuts import raster as r
#from grass.pygrass.raster.abstract import Info

from split_window_lst import *


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


def random_digital_numbers(count=2):
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


def retrieve_emissivities(emissivity_class):
    """
    Get average emissivities from an emissivity look-up table.
    This helper function returns a tuple.
    """
    EMISSIVITIES = coefficients.get_average_emissivities()

    # how to select land cover class?
    if emissivity_class == 'random':
        emissivity_class = random.choice(EMISSIVITIES.keys())
        print " * Some random emissivity class (key):", emissivity_class

    fields = EMISSIVITIES[emissivity_class]._fields
    emissivity_b10 = EMISSIVITIES[emissivity_class].TIRS10
    emissivity_b11 = EMISSIVITIES[emissivity_class].TIRS11

    return (emissivity_b10, emissivity_b11)


def i_emissivity():
    pass


def retrieve_column_water_vapour():
    """
    """
    cwvkey = random.choice(COLUMN_WATER_VAPOUR.keys())
    print " * Some random key:", cwvkey
    print COLUMN_WATER_VAPOUR[cwvkey].subrange
    rmse = COLUMN_WATER_VAPOUR[cwvkey].rmse
    print " * RMSE:", rmse


def replace_dummies(string, t10, t11):
    """
    Replace DUMMY_MAPCALC_STRINGS (see SplitWindowLST class for it)
    with input maps t10, t11.

    (Idea sourced from: <http://stackoverflow.com/a/9479972/1172302>)
    """
    replacements = ('Input_T10', str(t10)), ('Input_T11', str(t11))
    return reduce(lambda alpha, omega: alpha.replace(*omega),
                  replacements, string)


def cloud_mask(qab):
        """
        Create and apply a cloud mask based on the Quality Assessment Band (BQA)

        Source: <http://landsat.usgs.gov/L8QualityAssessmentBand.php
        """
        # create cloud map
        msg = "\n|i Create a cloud mask (highest confidence) based on the Quality Assessment band."
        g.message(msg)

        equation = '{result} = {expression}'
        
        tmpfile = grass.tempfile()  # Temporary file - replace with os.getpid?
        tmp_cloudmask = "tmp." + grass.basename(tmpfile)  # use its basename
        
        qabits = 'if(qab == 49152, null(), 1)'
        cloud_masking_equation = equation.format(result=tmp_cloudmask,
                                                 expression=qabits)
        grass.mapcalc(cloud_masking_equation)

        # create cloud mask
        run('r.mask cloudmask', overwrite=True)


def main():

    t10 = options['t10']
    t11 = options['t11']
    qab = options['qab']
    #emissivity_b10 = options['emissivity_b10']
    #emissivity_b11 = options['emissivity_b11']
    landcover = options['landcover']
    emissivity_class = options['emissivity_class']

    # flags
    info = flags['i']
    keep_region = flags['k']
    #timestamps = not(flags['t'])
    #zero = flags['z']
    #null = flags['n']  ### either zero or null, not both
    #evaluation = flags['e'] -- is there a quick way?
    #shell = flags['g']
    # if kelvin = flags['c']
        #r.colors B.ToAR.11 color=kelvin

    #
    # Temporary Region and Files
    #

    if not keep_region:
        grass.use_temp_region()  # to safely modify the region

    tmpfile = grass.tempfile()  # Temporary file - replace with os.getpid?
    tmp = "tmp." + grass.basename(tmpfile)  # use its basename

    #
    # Section...
    #

    # get average emissivities from Land Cover Map  OR  Look-Up table?
    emissivity_b10, emissivity_b11 = retrieve_emissivities(emissivity_class)

    # get range for column water vapour
    cwv_subrange = retrieve_column_water_vapour()  # Random -- FixMe

    # SplitWindowLST class, feed with required input values
    split_window_lst = SplitWindowLST(emissivity_b10,
                                      emissivity_b11,
                                      cwv_subrange)
    print "Split Window LST class:", split_window_lst
    print

    # citation, report or add to history
    citation = split_window_lst.citation
    print "Citation:", citation
    print

    #
    # Match region to input image if... ?
    #

    # ToDo: check if extent-B10 == extent-B11? Uneccessay?
    if not keep_region:
        run('g.region', rast=b10)   # ## FixMe?
        msg = "\n|! Matching region extent to map {name}"
        msg = msg.format(name=b10)
        g.message(msg)

    elif keep_region:
        grass.warning(_('Operating on current region'))

    #
    # Mask clouds
    #

    # mask_clouds()


    # Temporary Map
    tmp_lst = "{prefix}.lst".format(prefix=tmp)

    # mapcalc basic equation
    equation = "{result} = {expression}"

    # mapcalc expression
    split_window_expression = split_window_lst.mapcalc

    # replace the "dummy" string...
    split_window_expression = replace_dummies(split_window_expression, t10, t11)
    print "Split-Window expression:", split_window_expression
    print

    split_window_equation = equation.format(result=tmp_lst,
                                            expression=split_window_expression)

    grass.mapcalc(split_window_equation, overwrite=True)

    #
    # Strings for metadata
    #

    # history_calibration = 'Regression model: '
    # history_calibration += mapcalc_formula
    # if ndi:
    #     history_calibration += '(NDI: {ndi})'.format(ndi=ndi)
    # title_calibration = 'Calibrated DMSP-OLS Stable Lights'
    # description_calibration = ('Inter-satellite calibrated average '
    #                            'Digital Number values')
    # units_calibration = 'Digital Numbers (Calibrated)'

    # source1_calibration = citation
    # source2_calibration = ''

    # history entry
    #run("r.support", map=tmp_lst, title=title_lst,
    #    units=units_lst, description=description_lst,
    #    source1=source1_lst, source2=source2_lst,
    #    history=history_lst)

    #
    # Add suffix to basename & rename end product
    #

    # name = "{prefix}.{suffix}"
    # name = name.format(prefix=image.split('@')[0], suffix=outputsuffix)
    # lst_name = name
    lst_name = 'LST'
    run("g.rename", rast=(tmp_lst, lst_name))

    #
    # Restore region
    #

    if not keep_region:
        grass.del_temp_region()  # restoring previous region settings
        g.message("|! Original Region restored")


if __name__ == "__main__":
    options, flags = grass.parser()
    atexit.register(cleanup)
    sys.exit(main())
