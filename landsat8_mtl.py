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


class Landsat8_MTL():
    """
    Retrieve metadata from a Landsat8's MTL file.
    """

    def __init__(self, mtl_filename):
        """
        Initialise class object based on a Landsat8 MTL filename.
        """
        import os

        # read lines
        with open(mtl_filename, 'r') as mtl_file:
                mtl_lines = mtl_file.readlines()
        mtl_file.close()
        del(mtl_file)

        # clean and convert MTL lines in to a named tuple
        self.mtl = self.list_to_namedtuple(mtl_lines, 'metadata')
 
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

        # get band filenames
        #self.band_filenames = [line.strip() for line in self._mtl_lines if 'FILE_NAME_BAND' in line]
    
    def list_to_namedtuple(self, list_of_lines, name_for_tuple):
        """
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

            # get name, value and clean whitespaces, '"'
            field_name = line_split[0].strip()
            field_names.append(field_name)
            field_value = line_split[1].strip()
            field_value = field_value.translate(string.maketrans("", "", ), '"')
            field_values.append(field_value)

        # named tuple
        named_tuple = namedtuple(name_for_tuple, field_names)

        return named_tuple(*field_values)

    def __str__(self):
        """
        """
        msg = 'Landsat8 scene ID:'
        return msg + ' ' + self.scene_id

    def _get_mtl_lines(self):
        """
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
    
def test(mtlfile):
    """
    Code and test...
    """

    if not mtlfile:
        print "! No file defined, testing with default MTl file!"
        mtl = Landsat8_MTL("/geo/grassdb/ellas/meteora/LC81840332014146LGN00/cell_misc/LC81840332014146LGN00_MTL.txt")
        print
        
    else:
        mtl = Landsat8_MTL(mtlfile)

    print "| MTL object:", mtl
    print "| Test method _get_mtl_lines:\n ", mtl._get_mtl_lines()
    print

    print "| Basic metadata:\n"
    print mtl.scene_id
    print mtl.wrs_path
    print mtl.wrs_row
    print mtl.date_acquired
    print mtl.scene_center_time
    print mtl.corner_ul
    print mtl.corner_lr
    print mtl.corner_ul_projection
    print mtl.corner_lr_projection

#test(MTLFILE)

if __name__ == "__main__":
    main()

