ToDo:

[High Priority]

- Evaluate the BIG mapcalc expressions -- are they correct?

  - Expression for Column Water Vapor
  - Expression for Land Surface Temperature
  - Why is the LST out of range when using a fixed land cover class?

- ~~Why does the multi-step approach on deriving the CWV map differ from the
  single big mapcalc expression? See column_water_vapor? See
  column_water_vapor.py (function: _build_cwv_mapcalc()).~~ Fixed

- ~~Implement direct conversion of B10, B11 to brightness temperature values.~~  Done

- ~~Get the FROM-GLC map,~~ Found
- ~~implement mechanism to read land cover classes from it
  and use'm to retrieve emissivities~~

- ~~How to use the FVC?~~ Don't. Just use the Look-up table (see [\*] for details).


[Mid]

- Use existing i.emissivity?

- Raster Row I/O -- Maybe this is *not* an option: see discussion with Peter
  Zambelli

[Low]

- Profiling

- Implement a complete cloud masking function using the BQA image. Support for
  user requested confidence or types of clouds (?). Eg: optios=
  clouds,cirrus,high,low ?

- Multi-Threading


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

An overview of what they did (Section 3.2: Determination of LSEs):

1) used the FROM-GLC (30m) which contains 10 types of land covers (cropland,
forest, grassland, shrubland, wetland, waterbody, tundra, impervious, barren
land and snow-ice).

2) derived emissivities for each land cover class by using different
combinations of three BRDF kernel models (geometrical, volumetric and specular
models)

3) vegetation & ground emissivity spectra for the BRDF models were selected
from the MODIS University of California, Santa Barbara (UCSB) Emissivity
Library

4) estimated FVC (to obtain emissivity of land cover with temporal variation))
from NDVI based on Carlson (1997) and Sobrino (2001)

5) Finally, they established the emissivity LUT

