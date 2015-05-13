MODULE_TOPDIR = ../..

PGM = i.landsat8.swlst

ETCFILES = split_window_lst column_water_vapor csv_to_dictionary

include $(MODULE_TOPDIR)/include/Make/Script.make
include $(MODULE_TOPDIR)/include/Make/Python.make

default: script
