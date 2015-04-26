ToDo:

[High Priority]

- Evaluate the BIG mapcalc expressions -- are they correct?

- ~~Why does the multi-step approach on deriving the CWV map differ from the
  single big mapcalc expression? See column_water_vapor? See
  column_water_vapor.py (function: _build_cwv_mapcalc()).~~ Fixed

- Implement direct conversion of B10, B11 to brightness temperature values

- ~~Get the FROM-GLC map,~~ Found
- implement mechanism to read land cover classes from it
  and use'm to retrieve emissivities

- ~~How to use the FVC?~~ Don't. Just use the Look-up table!

[Mid]

- Use existing i.emissivity?

- Raster Row I/O

[Low]

- Implement a complete cloud masking function using the BQA image. Support for
  user requested confidence or types of clouds (?). Eg: optios=
  clouds,cirrus,high,low ?

- Multi-Threading
