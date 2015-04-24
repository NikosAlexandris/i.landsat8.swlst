#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
 MODULE:       i.landsat8.swlst

 AUTHOR(S):    Nikos Alexandris <nik@nikosalexandris.net>
               Created on Wed Mar 18 10:00:53 2015

 PURPOSE:      A robust and practical Slit-Window (SW) algorithm estimating
               land surface temperature, from the Thermal Infra-Red Sensor
               (TIRS) aboard Landsat 8 with an accuracy of better than 1.0 K.

               The input parameters include:

               - the brightness temperatures (Ti and Tj) of the two adjacent
                 TIRS channels,

               - FROM-GLC land cover products and emissivity lookup table, which are
                 a fraction of the FVC that can be estimated from the red and
                 near-infrared reflectance of the Operational Land Imager (OLI).

               - The FVC is estimated from the NDVI, calculated from the red and
                 near-infrared reflectance of Operational Land Imager, another payload
                 on Landsat8, by using the method proposed by Carlson (1997) and Sobrino
                 (2001) [34,35].

                The algorithm's flowchart (Figure 3 in the paper [0]) is:

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

               Sources:

               [0] Du, Chen; Ren, Huazhong; Qin, Qiming; Meng, Jinjie;
               Zhao, Shaohua. 2015. "A Practical Split-Window Algorithm
               for Estimating Land Surface Temperature from Landsat 8 Data."
               Remote Sens. 7, no. 1: 647-665.
               <http://www.mdpi.com/2072-4292/7/1/647/htm#sthash.ba1pt9hj.dpuf>

               [1] Huazhong Ren, Chen Du, Qiming Qin, Rongyuan Liu,
               Jinjie Meng, and Jing Li. "Atmospheric Water Vapor Retrieval
               from Landsat 8 and Its Validation." 3045–3048. IEEE, 2014.


               Details

               A new refinement of the generalized split-window algorithm
               proposed by Wan (2014) [19] is added with a quadratic term of
               the difference amongst the brightness temperatures (Ti, Tj) of
               the adjacent thermal infrared channels, which can be expressed
               as (equation 2 in the paper [0])

               LST = b0 +
                    [b1 + b2 * (1−ε)/ε + b3 * (Δε/ε2)] * (Ti+T)/j2 +
                    [b4 + b5 * (1−ε)/ε + b6 * (Δε/ε2)] * (Ti−Tj)/2 +
                     b7 * (Ti−Tj)^2

               where:

               - Ti and Tj are Top of Atmosphere brightness temperatures
               measured in channels i (~11.0 μm) and j (~12.0 µm),
               respectively;
                 - from
            <http://landsat.usgs.gov/band_designations_landsat_satellites.php>:
                   - Band 10, Thermal Infrared (TIRS) 1, 10.60-11.19, 100*(30)
                   - Band 11, Thermal Infrared (TIRS) 2, 11.50-12.51, 100*(30)

               - ε is the average emissivity of the two channels (i.e., ε = 0.5
               [εi + εj]),
               
               - Δε is the channel emissivity difference (i.e., Δε = εi − εj);
               
               - bk (k = 0,1,...7) are the algorithm coefficients derived in
               the following simulated dataset.

               [...]

               In the above equations,
                   
                   - dk (k = 0, 1...6) and ek (k = 1, 2, 3, 4) are the
                   algorithm coefficients;
                   
                   - w is the CWV;
                   
                   - ε and ∆ε are the average emissivity and emissivity
                   difference of two adjacent thermal channels, respectively,
                   which are similar to Equation (2);
                   
                   - and fk (k = 0 and 1) is related to the influence of the
                   atmospheric transmittance and emissivity, i.e., f k =
                   f(εi,εj,τ i ,τj).
                
                Note that the algorithm (Equation (6a)) proposed by
                Jiménez-Muñoz et al. added CWV directly to estimate LST.

                Rozenstein et al. used CWV to estimate the atmospheric
                transmittance (τi, τj) and optimize retrieval accuracy
                explicitly.

                Therefore, if the atmospheric CWV is unknown or cannot be
                obtained successfully, neither of the two algorithms in
                Equations (6a) and (6b) will work. By contrast, although our
                algorithm also needs CWV to determine the coefficients, this
                algorithm still works for unknown CWVs because the coefficients
                are obtained regardless of the CWV, as shown in Table 1.

 COPYRIGHT:    (C) 2015 by the GRASS Development Team

               This program is free software under the GNU General Public
               License (>=v2). Read the file COPYING that comes with GRASS
               for details.

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
#%  description: Print out model equations
#%end

#%flag
#%  key: k
#%  description: Keep current computational region settings
#%end

#%flag
#% key: c
#% description: Apply Celsius colortable to output LST map
#%end

#%option G_OPT_R_BASENAME_INPUT
#% key: prefix
#% key_desc: prefix string
#% type: string
#% label: OLI band names prefix
#% description: Prefix of Landsat8 OLI band names
#% required: no
#% answer: B
#%end

#%option G_OPT_R_INPUT
#% key: b4
#% key_desc: Band 4
#% description: Band 4 - Red (0.64 - 0.67 microns)
#% required : yes
#%end

#%option G_OPT_R_INPUT
#% key: b5
#% key_desc: Band 5
#% description: Band 5 - Near Infra-Red (0.85 - 0.88 microns)
#% required : yes
#%end

#%option G_OPT_R_INPUT
#% key: b10
#% key_desc: Band 10
#% description: Band 10 - TIRS (10.60 - 11.19 microns)
#% required : no
#%end

#%option G_OPT_R_INPUT
#% key: b11
#% key_desc: Band 11
#% description: Band 11 - TIRS (11.50 - 12.51 microns)
#% required : no
#%end

#%option G_OPT_R_INPUT
#% key: t10
#% key_desc: Temperature (10)
#% description: Brightness temperature (K) from band 10 
#% required : yes
#%end

#%option G_OPT_R_INPUT
#% key: t11
#% key_desc: Temperature (11)
#% description: Brightness temperature (K) from band 11 
#% required : yes
#%end

#%rules
#% excludes: b10, t10
#%end

#%rules
#% excludes: b11, t11
#%end

#%option G_OPT_R_INPUT
#% key: qab
#% key_desc: QA band
#% description: Landsat 8 quality assessment band
#% required : yes
#%end

#%option
#% key: clouds
#% key_desc: cloud masking
#% description: Confidence level for cloud masking (see...) -- ToDo!
#% options: clouds,cirrus,both
#% answer: high
#% required: no
#%end

#%rules
#% excludes: prefix, b4, b5, b10, b11, qab
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
#% description: Manual selection of land cover class to retrieve average emissivity from a look-up table (case sensitive)
#% options: Cropland, Forest, Grasslands, Shrublands, Wetlands, Waterbodies, Tundra, Impervious, Barren, Snow
#% required : yes
#%end

#%option G_OPT_R_OUTPUT
#% key: lst
#% key_desc: lst output
#% description: Name for output Land Surface Temperature map
#% required: yes
#% answer: lst
#%end

#%option G_OPT_R_OUTPUT
#% key: cwv
#% key_desc: cwv output
#% description: Name for output Column Water Vapor map [optional]
#% required: no
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


def save_map(mapname):
    """
    Helper function to save some in-between maps, assisting in debugging
    """
    run('r.info', map=mapname, flags='r')
    run('g.copy', raster=(mapname, 'DebuggingMap'))


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


def mask_clouds(qa_band):
        """
        Create and apply a cloud mask based on the Quality Assessment Band
        (BQA.) Source: <http://landsat.usgs.gov/L8QualityAssessmentBand.php

        See also: http://courses.neteler.org/processing-landsat8-data-in-grass-gis-7/#Applying_the_Landsat_8_Quality_Assessment_%28QA%29_Band
        """
        # create cloud map
        msg = ('\n|i Create a cloud mask (highest confidence) '
               'based on the Quality Assessment band.')
        g.message(msg)

        tmp_cloudmask = tmp + '.cloudmask'

        qabits_expression = 'if({qab} == 49152, null(), 1)'.format(qab=qa_band)

        cloud_masking_equation = equation.format(result=tmp_cloudmask,
                                                 expression=qabits_expression)

        grass.mapcalc(cloud_masking_equation)

        # create cloud mask
        run('r.mask', raster=tmp_cloudmask, overwrite=True)


def ndvi(b4, b5):
    """
    Derive NDVI
    """
    # temporary map
    global tmp_ndvi
    tmp_ndvi = tmp + '.ndvi'

    # use i.vi or r.mapcalc?
    run('i.vi', red=b4, nir=b5, viname="ndvi", output=tmp_ndvi, storage_bit=16)


def fvc(ndvi):
    """
    Derive the Fraction of Vegetation Cover from the NDVI
    based on a simple radiative transfer model (Carlson and Ripley, 1997)

    f = ((NDVI - NDVI_s) / (NDVI_inf - NSVI_s))^2

    where:

    - NDVI_inf for vegetation with infinite LAI
    - NDVI_s for bare soil
    """
    # name for themporary fvc map
    tmp_fvc = tmp + '.fvc'

    # equation for r.mapcalc
    ndvi_inf = 2
    ndvi_bare_soil = 0

    fvc_expression = ('(({ndvi} - {ndvi_bare_soil}) / '
                      '({ndvi_inf} - {ndvi_bare_soil}))^ 2')
    fvc_expression = fvc_expression.format(ndvi=ndvi,
                                           ndvi_bare_soil=ndvi_bare_soil,
                                           ndvi_inf=ndvi_inf)
    fvc_equation = equation.format(result=tmp_fvc, expression=fvc_expression)

    # compute fvc
    grass.mapcalc(fvc_equation, overwrite=True)

    # remove temporary ndvi map
    run('g.remove', type='raster', name=tmp_ndvi, flags='f')


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

    # fields = EMISSIVITIES[emissivity_class]._fields
    emissivity_b10 = EMISSIVITIES[emissivity_class].TIRS10
    emissivity_b11 = EMISSIVITIES[emissivity_class].TIRS11

    return (emissivity_b10, emissivity_b11)


def random_column_water_vapor_subrange():
    """
    Helper function returning a random column water vapour key
    to assist in testing the module.
    """
    cwvkey = random.choice(COLUMN_WATER_VAPOUR.keys())
    # COLUMN_WATER_VAPOUR[cwvkey].subrange
    # COLUMN_WATER_VAPOUR[cwvkey].rmse
    return cwvkey

def random_column_water_vapor_value():
    """
    Helper function returning a random value for column water vapor.
    """
    return random.uniform(0.0, 6.3)


def replace_dummies(string, *args, **kwargs):
    """
    Replace DUMMY_MAPCALC_STRINGS (see SplitWindowLST class for it)
    with input maps ti, tj (here: t10, t11).

    - in_ti and in_tj are the "input" strings, for example:
    in_ti = 'Input_T10'  and  in_tj = 'Input_T11'

    - out_ti and out_tj are the output strings which correspond to map
    names, user-fed or in-between temporary maps, for example:
    out_ti = t10  and  out_tj = t11

    or

    out_ti = tmp_ti_mean  and  out_tj = tmp_ti_mean

    (Idea sourced from: <http://stackoverflow.com/a/9479972/1172302>)
    """
    inout = set(['instring', 'outstring'])
    # if inout.issubset(set(kwargs)):  # alternative
    if inout == set(kwargs):
        instring = kwargs.get('instring', 'None')
        outstring = kwargs.get('outstring', 'None')

        # end comma important!
        replacements = (str(instring), str(outstring)),

    in_tij_out = set(['in_ti', 'out_ti', 'in_tj', 'out_tj'])
    if in_tij_out == set(kwargs):
        in_ti = kwargs.get('in_ti', 'None')
        out_ti = kwargs.get('out_ti', 'None')
        in_tj = kwargs.get('in_tj', 'None')
        out_tj = kwargs.get('out_tj', 'None')

        replacements = (in_ti, str(out_ti)), (in_tj, str(out_tj))

    in_tijm_out = set(['in_ti', 'out_ti', 'in_tj', 'out_tj',
                        'in_tim', 'out_tim', 'in_tjm', 'out_tjm'])

    if in_tijm_out == set(kwargs):
        in_ti = kwargs.get('in_ti', 'None')
        out_ti = kwargs.get('out_ti', 'None')
        in_tj = kwargs.get('in_tj', 'None')
        out_tj = kwargs.get('out_tj', 'None')
        in_tim = kwargs.get('in_tim', 'None')
        out_tim = kwargs.get('out_tim', 'None')
        in_tjm = kwargs.get('in_tjm', 'None')
        out_tjm = kwargs.get('out_tjm', 'None')

        replacements = (in_ti, str(out_ti)), (in_tj, str(out_tj)), \
                       (in_tim, str(out_tim)), (in_tjm, str(out_tjm))

    in_cwv_out = set(['in_ti', 'out_ti', 'in_tj', 'out_tj', 'in_cwv',
                      'out_cwv'])
    if in_cwv_out == set(kwargs):
        in_cwv = kwargs.get('in_cwv', 'None')
        out_cwv = kwargs.get('out_cwv', 'None')
        in_ti = kwargs.get('in_ti', 'None')
        out_ti = kwargs.get('out_ti', 'None')
        in_tj = kwargs.get('in_tj', 'None')
        out_tj = kwargs.get('out_tj', 'None')

        replacements = (in_ti, str(out_ti)), (in_tj, str(out_tj)), \
                       (in_cwv, str(out_cwv))

    return reduce(lambda alpha, omega: alpha.replace(*omega),
                  replacements, string)


def get_cwv_window_means(outname, t1x, t1x_mean_expression):
    """
    Get window means for T1x
    """
    msg = ('\n >>> Deriving window means from {Tx} ')
    msg +=('using the expression:\n {exp}')
    msg = msg.format(Tx=t1x, exp=t1x_mean_expression)
    g.message(msg)

    tx_mean_equation = equation.format(result=outname,
                                       expression=t1x_mean_expression)
    grass.mapcalc(tx_mean_equation, overwrite=True)
    
    # run('r.info', map=outname, flags='r')

def estimate_ratio_ji(outname, tmp_ti_mean, tmp_tj_mean, ratio_expression):
    """
    Estimate Ratio ji for the Column Water Vapor retrieval equation.
    """
    msg = '\n >>> Estimating ratio Rji'
    msg += ratio_expression
    g.message(msg)
 
    ratio_expression = replace_dummies(ratio_expression,
                                       in_ti='Mean_Ti', out_ti=tmp_ti_mean,
                                       in_tj='Mean_Tj', out_tj=tmp_tj_mean)

    ratio_equation = equation.format(result=outname,
                                     expression=ratio_expression)

    grass.mapcalc(ratio_equation, overwrite=True)
 
    # run('r.info', map=outname, flags='r')


def estimate_column_water_vapor(outname, ratio, cwv_expression):
    """
    """
    msg = "\n >>> Estimating atmospheric column water vapor "
    msg += '| Mapcalc expression: '
    msg += cwv_expression
    g.message(msg)

    cwv_expression = replace_dummies(cwv_expression,
                                     instring='Ratio_ji',
                                     outstring=ratio)

    cwv_equation = equation.format(result=outname, expression=cwv_expression)

    grass.mapcalc(cwv_equation, overwrite=True)
    #run('r.info', map=outname, flags='r')

    # uncomment below to save for testing!
    # save_map(outname)


def estimate_column_water_vapor_big_expression(outname, t10, t11, cwv_expression):
    """
    Derive a column water vapor map using a single mapcalc expression based on
    eval.

            *** To Do: evaluate -- does it work correctly? *** !
    """
    msg = "\n >>> Estimating atmospheric column water vapor "
    #msg += '| One big mapcalc expression: '
    #msg += cwv_expression
    g.message(msg)
    
    cwv_expression = replace_dummies(cwv_expression,
                                     in_ti='TIRS10', out_ti=t10,
                                     in_tj='TIRS11', out_tj=t11)


    cwv_equation = equation.format(result=outname, expression=cwv_expression)
    
    grass.mapcalc(cwv_equation, overwrite=True)
    # run('r.info', map=outname, flags='r')

    # uncomment below to save for testing!
    #save_map(outname)


def estimate_lst(outname, t10, t11, cwv_map, lst_expression):
    """
    Produce a Land Surface Temperature map based on a mapcalc expression
    returned from a SplitWindowLST object.

    Inputs are:

    - brightness temperature maps t10, t11
    - column water vapor map
    - a temporary filename
    - a valid mapcalc expression
    """
    # replace the "dummy" string...
    split_window_expression = replace_dummies(lst_expression,
                                              in_cwv='Input_CWV',
                                              out_cwv=cwv_map,
                                              in_ti='Input_T10', out_ti=t10,
                                              in_tj='Input_T11', out_tj=t11)

    split_window_equation = equation.format(result=outname,
                                            expression=split_window_expression)

    msg = '\n >>> Estimating the Land Surface Temperature'
    g.message(msg)
    
    grass.mapcalc(split_window_equation, overwrite=True)
    #run('r.info', map=outname, flags='r')


def main():
    """
    Main program
    """

    # for Temporary files
    global tmp
    tmpfile = grass.tempfile()  # replace with os.getpid?
    tmp = "tmp." + grass.basename(tmpfile)  # use its basename

    # Temporary filenames
    tmp_ti_mean = tmp + '.ti_mean'  # for cwv
    tmp_tj_mean = tmp + '.tj_mean'  # for cwv
    tmp_ratio = tmp + '.ratio'  # for cwv
    tmp_cwv = tmp + '.cwv'  # column water vapor map
    tmp_lst = "{prefix}.lst".format(prefix=tmp)  # lst

    # mapcalc basic equation
    global equation, citation_lst
    equation = "{result} = {expression}"

    # user input
    b4 = options['b4']
    b5 = options['b5']
    b10 = options['b10']
    b11 = options['b11']
    t10 = options['t10']
    t11 = options['t11']
    qab = options['qab']
    lst_output = options['lst']
    cwv_output = options['cwv']

    #emissivity_b10 = options['emissivity_b10']
    #emissivity_b11 = options['emissivity_b11']
    landcover = options['landcover']
    emissivity_class = options['emissivity_class']

    # flags
    global info
    info = flags['i']
    keep_region = flags['k']
    
    #timestamps = not(flags['t'])
    #zero = flags['z']
    #null = flags['n']  ### either zero or null, not both
    #evaluation = flags['e'] -- is there a quick way?
    #shell = flags['g']
    
    colortable = flags['c']

    # Temporary Region
    if not keep_region:
        grass.use_temp_region()  # to safely modify the region

    #
    # Part 1: OLI -> NDVI -> FVC -> Emissivities from look-up table
    #

    # derive NDVI, output is tmp_ndvi
    ndvi(b4, b5)

    # compute FVC, output is tmp_fvc
    fvc(tmp_ndvi)  # ToDo: where to plug this in?

    # get average emissivities from Land Cover Map  OR  Look-Up table?
    emissivity_b10, emissivity_b11 = retrieve_emissivities(emissivity_class)

    #
    # Part 2: TIRS > Brightness Temperatures > MSWVCM > CWV > Coefficients
    #

    # TIRS > Brightness Temperatures

    # perform internally? see:
    # https://github.com/micha-silver/grass-landsat8/blob/master/r.in.landsat8.py

    # MSWVCM, determine column water vapor
    window_size = 3  # could it be else!?
    cwv = Column_Water_Vapor(window_size, t10, t11)
    citation_cwv = cwv.citation

    # To be removed -----------------------------------------------
    ## get window means (of adjacent pixels) for Ti, Tj
    #get_cwv_window_means(tmp_ti_mean, t10, cwv.mean_ti_expression)
    #get_cwv_window_means(tmp_tj_mean, t11, cwv.mean_tj_expression)

    ## estimate ratio Rji for column water vapor
    #estimate_ratio_ji(tmp_ratio, tmp_ti_mean, tmp_tj_mean,
    #                  cwv.ratio_ji_expression)

    ## estimate Column Water Vapor map (CWV)
    #estimate_column_water_vapor(tmp_cwv, tmp_ratio,
    #                            cwv.column_water_vapor_expression)
    # --------------------------------------------- To be removed #

    # estimate using one big mapcalc expression
    estimate_column_water_vapor_big_expression(tmp_cwv, t10, t11, cwv._build_cwv_mapcalc())

    # save Column Water Vapor map?
    if cwv_output:
        run('g.copy', raster=(tmp_cwv, cwv_output))

    #
    # Match region to input image if... ?
    #

    # ToDo: check if extent-B10 == extent-B11? Unnecessary?
    if not keep_region:
        run('g.region', rast=t10)   # ## FixMe?
        msg = "\n|! Matching region extent to map {name}"
        msg = msg.format(name=t10)
        g.message(msg)

    elif keep_region:
        grass.warning(_('Operating on current region'))

    #
    # Mask clouds
    #
    
    mask_clouds(qab)

    #
    # Estimate LST
    #

    # SplitWindowLST class, feed with required input values
    split_window_lst = SplitWindowLST(emissivity_b10, emissivity_b11)
    citation_lst = split_window_lst.citation
    estimate_lst(tmp_lst, t10, t11, tmp_cwv, split_window_lst.sw_lst_mapcalc)

    # remove mask
    run('r.mask', flags='r', verbose=True)

    # Strings for metadata
    history_lst = 'Split-Window model: '
    history_lst += split_window_lst.sw_lst_mapcalc
    title_lst = 'Land Surface Temperature (C)'
    description_lst = ('Split-Window LST')
    units_lst = 'Celsius'
    source1_lst = citation_lst
    source2_lst = citation_cwv

    # history entry
    run("r.support", map=tmp_lst, title=title_lst,
        units=units_lst, description=description_lst,
        source1=source1_lst, source2=source2_lst,
        history=history_lst)

    # colors to celsius
    if colortable:
        g.message('\n >>> Assigning the "celsius" color table to the LST map')
        run('r.colors', map=tmp_lst, color='celsius')

    # (re)name end product
    run("g.rename", rast=(tmp_lst, lst_output))

    # Restore region
    if not keep_region:
        grass.del_temp_region()  # restoring previous region settings
        g.message("|! Original Region restored")

    if info:
        print '\nSource: ' + citation_lst


if __name__ == "__main__":
    options, flags = grass.parser()
    atexit.register(cleanup)
    sys.exit(main())
