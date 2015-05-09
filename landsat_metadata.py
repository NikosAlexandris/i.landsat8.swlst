#!/usr/bin/python\<nl>\
# -*- coding: utf-8 -*-

"""
@author nik |
"""
mtl_filename = '/geo/grassdb/ellas/meteora/LC81840332014146LGN00/cell_misc/LC81840332014146LGN00_MTL.txt'
band_numbers = [10, 11]

# helper function
def get_float_from_mtl_line(string):
    import re
    return float(re.findall(r"[+-]? *(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?", string)[-1])

def get_metadata(mtl_filename, band_numbers):
    """
    """
    import collections

    # feed MTL file's lines in a list
    with open(mtl_filename, 'r') as mtl_file:
            mtl_lines = mtl_file.readlines()
    mtl_file.close()
    
    dictionary = {}
    print "Empty dictionary initialised"
    print


    for band in band_numbers:

        band = str(band)
       
       # strings of interest
        strings = {'multiplicative': 'RADIANCE_MULT_BAND_' + band,
                'additive': 'RADIANCE_ADD_BAND_' + band}
        
        print "Strings of interest", strings
        print

        # retrieve lines of interest
        mtl = []
        for key in strings.keys():

            print "String-Key:", key
            print "Some print:", strings[key]
            string = strings[key]

            lines_of_interest = [line.strip() for line in mtl_lines if string in line]
            mtl += lines_of_interest
        print "MTL lines of interest:", mtl

        print "Processig lines <---"
        print
        for key in strings.keys():
            
            for line in mtl:
            
                print "MTL line:", line

                mtl_line = line.split()
                print "MTL line split:", mtl_line

                mtl_float = get_float_from_mtl_line(line)
                print "MTL float extracted:", mtl_float
                print

                if 'MULT' in strings[key]:
                    print "Adding a named tuple for MULT"
                    factors = collections.namedtuple('b' + str(band), key)
                    print "Factors (named tuple):", factors
                    print

                elif 'ADD' in strings[key]:
                    print "Adding a named tuple for ADD"
                    factors = collections.namedtuple('b' + str(band), key)
                    print "Factors (named tuple):", factors
                    print

                dictionary[key] = dictionary.get(key, factors)

        print "Dictionary:", dictionary
        print "keys:", dictionary.keys()
        print "items:", dictionary.items()
        print

        test_value = dictionary['multiplicative'].multiplicative
        print test_value

        #

get_metadata(mtl_filename, [10, 11])
