#!/usr/bin/python\<nl>\
# -*- coding: utf-8 -*-

"""
@author nik |
"""

import sys
from collections import namedtuple


MTLFILE = ''


# helper functions
def set_mtlfile():
    """
    Set user defined csvfile, if any
    """
    if len(sys.argv) > 1:
        return sys.argv[1]
    else:
        return False


# where to use this?
def get_float_from_mtl_line(string):
    import re
    return float(re.findall(r"[+-]? *(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?",
                 string)[-1])


class Landsat8_MTL():
    """
    Retrieve metadata from a Landsat8's MTL file.
    """

    def __init__(self, mtl_filename):
        """
        Initialise class object based on a Landsat8 MTL filename.
        """
        # read lines
        with open(mtl_filename, 'r') as mtl_file:
                mtl_lines = mtl_file.readlines()

        # close and remove 'mtl_file'
        mtl_file.close()
        del(mtl_file)

        # clean and convert MTL lines in to a named tuple
        self.mtl = self._to_namedtuple(mtl_lines, 'metadata')

        # is it possible to feed directly to self?
        #for field in self.mtl._fields:
        #    field_lowercase = field.lower()
        #    print "Field of named tuple:", field_lowercase 
        #    self.test.field_lowercase = self.mtl.'{f}'.format(f=field)
        #    print self.test.field_lowercase
        #print
        
        # basic metadata
        self.scene_id = self.mtl.LANDSAT_SCENE_ID
        self.wrs_path = self.mtl.WRS_PATH
        self.wrs_row = self.mtl.WRS_ROW
        self.date_acquired = self.mtl.DATE_ACQUIRED
        self.scene_center_time = self.mtl.SCENE_CENTER_TIME
        self.corner_ul = (self.mtl.CORNER_UL_LAT_PRODUCT, self.mtl.CORNER_UL_LON_PRODUCT)
        self.corner_lr = (self.mtl.CORNER_LR_LAT_PRODUCT, self.mtl.CORNER_LR_LON_PRODUCT)
        self.corner_ul_projection = (self.mtl.CORNER_UL_PROJECTION_X_PRODUCT, self.mtl.CORNER_UL_PROJECTION_Y_PRODUCT)
        self.corner_lr_projection = (self.mtl.CORNER_LR_PROJECTION_X_PRODUCT, self.mtl.CORNER_LR_PROJECTION_Y_PRODUCT)
        self.cloud_cover = self.mtl.CLOUD_COVER
        self.sun_azimuth = self.mtl.SUN_AZIMUTH
        self.sun_elevation = self.mtl.SUN_ELEVATION
        self.earth_sun_distance = self.mtl.EARTH_SUN_DISTANCE
        self.map_projection = self.mtl.MAP_PROJECTION
        self.datum = self.mtl.DATUM
        self.ellipsoid = self.mtl.ELLIPSOID
        self.utm_zone = self.mtl.UTM_ZONE
        self.grid_cell_size_panchromatic = self.mtl.GRID_CELL_SIZE_PANCHROMATIC
        self.grid_cell_size_reflective = self.mtl.GRID_CELL_SIZE_REFLECTIVE
        self.grid_cell_size_thermal = self.mtl.GRID_CELL_SIZE_THERMAL

        # get band filenames
        # self.band_filenames = [line.strip() for line in self._mtl_lines if 'FILE_NAME_BAND' in line]
    
    def _to_namedtuple(self, list_of_lines, name_for_tuple):
        """
        This function performs the following actions on the given
        'list_of_lines':
        - exclude lines containing the strings 'GROUP' and 'END'
        - remove whitespaces and doublequotes from strings
        - convert list of lines in to a named tuple
        """
        import string
        
        # exclude lines containing 'GROUP', 'END'
        lines = [line.strip() for line in list_of_lines if not any(x in line for x in ('GROUP', 'END'))]
        
        # keep a copy, maybe useful?
        self._mtl_lines = lines
        del(list_of_lines)
        
        # list comprehension below not easy to read!
        # self.mtl_lines = [(self.mtl_lines[idx].split('=')[0].strip(), self.mtl_lines[idx].split('=')[1].strip().translate(string.maketrans("", "", ), '"')) for idx in range(len(self.mtl_lines))]

        # loop over lines, do some cleaning
        field_names = []
        field_values = []
        for idx in range(len(lines)):

            # split line in '='
            line = lines[idx]
            line_split = line.split('=')

            # get field name & field value, clean whitespaces and "
            field_name = line_split[0].strip()
            field_names.append(field_name)
            field_value = line_split[1].strip()
            field_value = field_value.translate(string.maketrans("", "", ), '"')
            field_values.append(field_value)

        # named tuple
        named_tuple = namedtuple(name_for_tuple, field_names)

        # return named tuple
        return named_tuple(*field_values)

    def __str__(self):
        """
        Return a string representation of the scene's id.
        """
        msg = 'Landsat8 scene ID:'
        return msg + ' ' + self.scene_id

    def _get_mtl_lines(self):
        """
        Return the "hidden" copy of the MTL lines before cleaning (lines
        containing 'GROUP' or 'END' are though excluded).
        """
        return self._mtl_lines


def main():
    """
    Main program.
    """
    if set_mtlfile():
        MTLFILE = set_mtlfile()
        print "| Reading metadata from:", MTLFILE
    else:
        MTLFILE = ''
    

if __name__ == "__main__":
    main()

