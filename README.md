ToDo:

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

