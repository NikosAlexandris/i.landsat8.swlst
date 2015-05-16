*i.landsat8.swlst* is an implementation of the robust and practical
Slit-Window (SW) algorithm estimating land surface temperature (LST), from the
Thermal Infra-Red Sensor (TIRS) aboard Landsat 8 with an accuracy of
better than 1.0 K.

To produce an LST map, the algorithm requires at minimum:

- TIRS bands 10 and 11
- the acquisition's metadata file (MTL)
- a Finer Resolution Observation & Monitoring of Global Land Cover (FROM-GLC) product

Algorithm description
=====================

- To add...

Installation
============

## Requirements
------------

see [GRASS Addons SVN repository, README file, Installation - Code Compilation](https://svn.osgeo.org/grass/grass-addons/README)

## Steps

Making the script `i.fusion.hpf` available from within any GRASS-GIS ver. 7.x session, may be done via the following steps:

1.  launch a GRASS-GIS’ ver. 7.x session

2.  navigate into the script’s source directory

3.  execute `make MODULE_TOPDIR=$GISBASE`

Usage examples
==============

After installation, from within a GRASS-GIS session, see help details via `i.fusion.hpf --help`

- To add...


Implementation notes
====================

- Created on Wed Mar 18 10:00:53 2015
- First all-through execution: Tue May 12 21:50:42 EEST 2015


## To Do

[High Priority]

- Evaluate BIG mapcalc expressions -- are they correct?
    - Expression for Column Water Vapor
    - Expression for Land Surface Temperature
- ~~Why is the LST out of range when using a fixed land cover class?~~ Cloudy
  pixels are, mainly, the reason. Better cloud masking is the solution.
- ~~Why does the multi-step approach on deriving the CWV map differ from the single big mapcalc expression?~~ **Fixed**
- ~~Implement direct conversion of B10, B11 to brightness temperature values.~~  **Done**
- ~~Get the FROM-GLC map,~~ **Found**
- ~~implement mechanism to read land cover classes from it
  and use'm to retrieve emissivities~~ **Done**
- ~~How to use the FVC?~~ Don't. Just **use the Look-up table** (see [\*] for details).
- ~~Save average emissivity and delta emissivity maps for caching (re-use in
  subsequent trials, huge time saver!)~~ **Implemented**

[Mid]

- Use existing i.emissivity?  Not exactly compatible.  Anyhow, options to input
  average and delta emissivity maps implemented.
- Raster Row I/O -- Maybe *not* an option: see discussion with Peter
  Zambelli
- How to perform pixel value validity checks for in-between and end products?
  r.mapcalc can't do this.

[Low]

- Deduplicate code in split_window_lst class >
  _build_average_emissivity_mapcalc() and _build_delta_emissivity_mapcalc() 
- Implement a median window filter, an another option in addition to mean.
- Profiling
- Implement a complete cloud masking function using the BQA image. Support for
  user requested confidence or types of clouds (?). Eg: options=
  clouds,cirrus,high,low ?
- Multi-Threading? Note, r.mapcalc is already.


[\*] Details: the authors followed the CBEM method. Based on the FROM-GLC map,
they derived the following look-up table (LUT):

Emissivity Class|TIRS10|TIRS11
Cropland|0.971|0.968
Forest|0.995|0.996
Grasslands|0.97|0.971
Shrublands|0.969|0.97
Wetlands|0.992|0.998
Waterbodies|0.992|0.998
Tundra|0.98|0.984
Impervious|0.973|0.981
Barren Land|0.969|0.978
Snow and ice|0.992|0.998

An overview of "Section 3.2: Determination of LSEs":

1) The FROM-GLC (30m) contains 10 types of land covers (cropland,
forest, grassland, shrubland, wetland, waterbody, tundra, impervious, barren
land and snow-ice).

2) Deriving emissivities for each land cover class by using different
combinations of three BRDF kernel models (geometrical, volumetric and specular
models)

3) Vegetation & ground emissivity spectra for the BRDF models selected
from the MODIS University of California, Santa Barbara (UCSB) Emissivity
Library

4) Estimating FVC (to obtain emissivity of land cover with temporal variation))
from NDVI based on Carlson (1997) and Sobrino (2001)

5) Finally, establishing the average emissivity Look-Up table

References
==========

-   [0] Du, Chen; Ren, Huazhong; Qin, Qiming; Meng, Jinjie; Zhao,
    Shaohua. 2015. "A Practical Split-Window Algorithm for Estimating
    Land Surface Temperature from Landsat 8 Data." Remote Sens. 7, no.
    1: 647-665.
    http://www.mdpi.com/2072-4292/7/1/647/htm\#sthash.ba1pt9hj.dpuf

-   [1] Huazhong Ren, Chen Du, Qiming Qin, Rongyuan Liu, Jinjie Meng,
    and Jing Li. "Atmospheric Water Vapor Retrieval from Landsat 8 and
    Its Validation." 3045--3048. IEEE, 2014.

Ευχαριστώ
=========

- Yann Chemin
- Pietro Zambelli
- StackExchange contributors
