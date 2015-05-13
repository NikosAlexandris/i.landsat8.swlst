DESCRIPTION
-----------

*i.landsat8.swlst* is an implementation of the robust and practical
Slit-Window (SW) algorithm estimating land surface temperature, from the
Thermal Infra-Red Sensor (TIRS) aboard Landsat 8 with an accuracy of
better than 1.0 K.

### Details

A new refinement of the generalized split-window algorithm proposed by
Wan (2014) [19] is added with a quadratic term of the difference amongst
the brightness temperatures (Ti, Tj) of the adjacent thermal infrared
channels, which can be expressed as (equation 2 in the paper [0])

`LST = b0 + [b1 + b2 * (1-ε)/ε + b3 * (Δε/ε2)] * (Ti+T)/j2 + [b4 + b5 * (1-ε)/ε
+ b6 * (Δε/ε2)] * (Ti-Tj)/2 + b7 * (Ti-Tj)^2`

where:

- Ti and Tj are Top of Atmosphere brightness temperatures measured in channels
  i (\~11.0 μm) and j (\~12.0 µm), respectively
- from http://landsat.usgs.gov/band\_designations\_landsat\_satellites.php:
    - Band 10, Thermal Infrared (TIRS) 1, 10.60-11.19, 100\*(30)
    - Band 11, Thermal Infrared (TIRS) 2, 11.50-12.51, 100\*(30)
- ε is the average emissivity of the two channels (i.e., `ε = 0.5 [εi + εj]`)
- Δε is the channel emissivity difference (i.e., `Δε = εi - εj`)
- bk (k = 0,1,...7) are the algorithm coefficients derived from a simulated
  dataset.

[...]

In the above equations,
- dk (k = 0, 1...6) and ek (k = 1, 2, 3, 4) are the algorithm coefficients;
- w is the CWV;
- ε and ∆ε are the average emissivity and emissivity difference of two adjacent
  thermal channels, respectively, which are similar to Equation (2);
- and fk (k = 0 and 1) is related to the influence of the atmospheric
  transmittance and emissivity, i.e., `fk = f(εi,εj,τ i ,τj).

Note that the algorithm (Equation (6a)) proposed by Jiménez-Muñoz et al. added
CWV directly to estimate LST.

Rozenstein et al. used CWV to estimate the atmospheric transmittance (τi, τj)
and optimize retrieval accuracy explicitly.

Therefore, if the atmospheric CWV is unknown or cannot be obtained
successfully, neither of the two algorithms in Equations (6a) and (6b) will
work. By contrast, although our algorithm also needs CWV to determine the
coefficients, this algorithm still works for unknown CWVs because the
coefficients are obtained regardless of the CWV, as shown in Table 1.

NOTES
-----

The algorithm's flowchart (Figure 3 in the paper [0]) is:

![](Figure_3_Flowchart_of_retrieving_LST_from_Landsat8.jpg)

### Cloud Masking

The first important step of the algorithm is cloud screening. The module
offers two ways to achieve this:

1. use of the Quality Assessment band and some user-defined QA pixel value
2. use an external cloud map as an inverted MASK

### Calibration of TIRS channels 10, 11

#### Conversion to Spectral Radiance

Conversion of Digital Numbers to TOA Radiance. OLI and TIRS band data
can be converted to TOA spectral radiance using the radiance rescaling
factors provided in the metadata file:

`Lλ = ML * Qcal + AL`

where:

- Lλ = TOA spectral radiance (Watts/( m2 \* srad \* μm))
- ML = Band-specific multiplicative rescaling factor from the metadata
  (RADIANCE\_MULT\_BAND\_x, where x is the band number)
- AL = Band-specific additive rescaling factor from the metadata
  (RADIANCE\_ADD\_BAND\_x, where x is the band number)
- Qcal = Quantized and calibrated standard product pixel values (DN)

#### Conversion to at-Satellite Temperature

Conversion to At-Satellite Brightness Temperature TIRS band data can be
converted from spectral radiance to brightness temperature using the
thermal constants provided in the metadata file:

`T = K2 / ln((K1/Lλ) + 1)`

where:

- T = At-satellite brightness temperature (K) - Lλ = TOA spectral radiance
  (Watts/( m2 \* srad \* μm)), below 'DUMMY\_RADIANCE'
- K1 = Band-specific thermal conversion constant from the metadata
  (K1\_CONSTANT\_BAND\_x, where x is the band number, 10 or 11)
- K2 = Band-specific thermal conversion constant from the metadata
  (K2\_CONSTANT\_BAND\_x, where x is the band number, 10 or 11) ...

### Land Surface Emissivity

An overview of "Section 3.2: Determination of LSEs":

1. The FROM-GLC (30m) contains 10 types of land covers (cropland, forest,
grassland, shrubland, wetland, waterbody, tundra, impervious, barren land and
snow-ice).

2. Deriving emissivities for each land cover class by using different
combinations of three BRDF kernel models (geometrical, volumetric and specular
models)

3. Vegetation and ground emissivity spectra for the BRDF models selected from
the MODIS University of California, Santa Barbara (UCSB) Emissivity Library

4. Estimating FVC (to obtain emissivity of land cover with temporal variation))
from NDVI based on Carlson (1997) and Sobrino (2001)

5. Finally, establishing the
average emissivity Look-Up table

### Column Water Vapor

Retrieving atmospheric column water vapor from Landsat8 TIRS data based
on the modified split-window covariance and variance ratio
(MSWCVR).

-------------------------------------------------------------------------
\*Note,\* this class produces valid expressions for GRASS GIS' mapcalc raster
processing module and does not directly compute column water vapor estimations.
-------------------------------------------------------------------------

With a vital assumption that the atmosphere is unchanged over the
neighboring pixels, the MSWCVR method relates the atmospheric CWV to the
ratio of the upward transmittances in two thermal infrared bands,
whereas the transmittance ratio can be calculated based on the TOA
brightness temperatures of the two bands. Considering N adjacent pixels,
the CWV in the MSWCVR method is estimated as:

- `cwv = c0 + c1*(tj/ti) + c2*(tj/ti)^2`
- `tj/ti` \~ `Rji = SUM [(Tik-Ti\_mean) \* (Tjk-Tj\_mean)] / SUM[(Tik-Tj\_mean)\^2]`

In Equation (3a):
- c0, c1 and c2 are coefficients obtained from simulated data;
- τ is the band effective atmospheric transmittance;
- N is the number of adjacent pixels (excluding water and cloud pixels) in a
  spatial window of size n (i.e., N = n × n);
- Ti,k and Tj,k are Top of Atmosphere brightness temperatures (K) of bands i
  and j for the kth pixel;
- mean(Ti) and mean(Tj) are the mean or median brightness temperatures of the N
  pixels for the two bands.

The regression coefficients:
- c0 = -9.674
- c1 = 0.653
- c2 = 9.087 

where obtained by:
- 946 cloud-free TIGR atmospheric profiles,
- the new high accurate atmospheric radiative transfer model MODTRAN 5.2
- simulating the band effective atmospheric transmittance Model analysis
  indicated that this method will obtain a CWV RMSE of about 0.5 g/cm2.

Details about the CWV retrieval can be found in:

Ren, H.; Du, C.; Qin, Q.; Liu, R.; Meng, J.;
Li, J. Atmospheric water vapor retrieval from landsat 8 and its
validation. In Proceedings of the IEEE International Geosciene and
Remote Sensing Symposium (IGARSS), Quebec, QC, Canada, July 2014; pp.
3045–3048.


#### Modified Split-Window Covariance-Variance Method

...

### Land Surface Temperature

...

#### Split-Window Algorithm

A class implementing the split-window algorithm for Landsat8 imagery
Inputs:

- The class itself requires only a string for 'landcover' which
is:

1) a fixed land cover class string (one from the classes defined in
the FROM-GLC legend)

2) a land cover class code (integer) one from the classes defined in the FROM-GLC classification scheme.

- Inputs for individual functions vary, look at their definitions.

Outputs:

- Valid expressions for GRASS GIS' r.mapcalc raster processing module
- Direct computation for... though not necessary, nor useful for GRASS GIS
modules directly?

#####Details

The algorithm removes the atmospheric effect
through differential atmospheric absorption in the two adjacent thermal
infrared channels centered at about 11 and 12 μm. The linear or
non-linear combination of the brightness temperatures is finally applied
for LST estimation based on the equation:

LST = b0 + + (b1 + b2 \*
((1-ae)/ae)) + + b3 \* (de/ae) \* ((t10 + t11)/2) + + (b4 + b5 \*
((1-ae)/ae) + b6 \* (de/ae\^2)) \* ((t10 - t11)/2) + + b7 \* (t10 -
t11)\^2

To reduce the influence of the CWV error on the LST, for a CWV
within the overlap of two adjacent CWV sub-ranges, we first use the
coefficients from the two adjacent CWV sub-ranges to calculate the two
initial temperatures and then use the average of the initial
temperatures as the pixel LST.

For example, the LST pixel with a CWV of 2.1 g/cm2 is estimated by using the
coefficients of [0.0, 2.5] and [2.0, 3.5]. This process initially reduces the
δLSTinc and improves the spatial continuity of the LST product.

EXAMPLE
-------

At minimum, the module requires the following in order to derive a land
surface temperature map:

1. The Landsat8 scene's acquisition metadata
(MTL file)

2. Bands 10, 11 and QA

3. The FROM-GLC product for the same Path and Row The shorted call for
   processing a complete Landsat8 scene normally is:

<div class="code">

    i.landsat8.swlst mtl=MTL prefix=B landcover=FROM_GLC

</div>

where:
-   mtl= the name of the MTL metadata file (normally with a ".txt"
    extension)
-   prefix= the prefix of the band names imported in GRASS GIS' data
    base
-   landcover= the name of the FROM-GLC map that covers the extent of
    the Landsat8 scene under processing

The pixel value 61440 is selected to automatically to build a cloud
mask. At the moment, only one pixel value may be requested from the
Quality Assessment band. For details, refer to
[http://landsat.usgs.gov/L8QualityAssessmentBand.php USGS' webpage for Landsat8 Quality
Assessment Band]

In order to restrict the processing in to the currently set
computational region, the *-k* flag can be used:

<div class="code">

    i.landsat8.swlst mtl=MTL prefix=B landcover=FROM_GLC -k 

</div>

A user defined map for clouds, instead of relying on the Quality
Assessment band, can be used via the `clouds` option:

<div class="code">

    i.landsat8.swlst mtl=MTL prefix=B landcover=FROM_GLC clouds=Cloud_Map -k 

</div>

The Celsius color table may be applied for the output land surface
temperature map via the *-c* flag:

<div class="code">

    i.landsat8.swlst mtl=MTL prefix=B landcover=FROM_GLC -c 

</div>

The user can use existing at-satellite temperature maps via the `t10`
and `t11` options, selectively. For example:

<div class="code">

    i.landsat8.swlst mtl=MTL b10=B10 t11=AtSatellite_Temperature_11 landcover=FROM_GLC -c 

</div>

or

<div class="code">

    i.landsat8.swlst mtl=MTL t10=AtSatellite_Temperature_10 t11=AtSatellite_Temperature_11 landcover=FROM_GLC -c 

</div>

Expert users may need to request for a "fixed" average surface
emissivity, in order to perform the algorithm for a single land cover class (one
from the classes defined in the FROM-GLC classification scheme) via the
`emissivity\_class` option. Consequently, `emissivity\_class` cannot
be used at the same time with the `landover` option.

<div class="code">

    i.landsat8.swlst mtl=MTL b10=B10 t11=AtSatellite_Temperature_11 qab=BQA emissivity_class='Croplands' -c 

</div>

A complete "transparent" run-through of what kind of and how the module performs
its computations, may be requested via the use of both the *--v* and *-i*
flags:

<div class="code">

    i.landsat8.swlst mtl=MTL prefix=B landcover=FROM_GLC -i --v 

</div>

The above will print out a description of each individual processing step, as
well as the actual mathematical epxressions applied via GRASS GIS'
`r.mapcalc` module.

<div class="code">

    i.landsat8.swlst

</div>

![](.jpg)

...

<div class="code">

    i.landsat8.swlst

</div>

![](.jpg)

TODO
----

- Go through [Submitting Python](http://trac.osgeo.org/grass/wiki/Submitting/Python)
- Proper command history tracking.
- Add timestamps (r.timestamp, temporal framework)
- Deduplicate code where applicable
- Test if it compiles in other systems
- Improve documentation

REFERENCES
----------

* [0] Du, Chen; Ren, Huazhong; Qin, Qiming; Meng, Jinjie; Zhao, Shaohua. 2015.
  "A Practical Split-Window Algorithm for Estimating Land Surface Temperature
  from Landsat 8 Data." Remote Sens. 7, no. 1: 647-665.
  http://www.mdpi.com/2072-4292/7/1/647/htm\#sthash.ba1pt9hj.dpuf

* [1] Huazhong Ren, Chen Du, Qiming Qin, Rongyuan Liu, Jinjie Meng, and Jing
  Li. "Atmospheric Water Vapor Retrieval from Landsat 8 and Its Validation."
  3045–3048. IEEE, 2014.

SEE ALSO
--------

*[i.emissivity](i.emissivity.html)*

AUTHORS
-------

Nikos Alexandris\

