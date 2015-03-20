"""
Convert csv data to a dictionary with namedtuples as values
"""

# based on: <http://pastebin.com/tnyhmCJz>
# see: <http://stackoverflow.com/q/29141609/1172302>

# real data
csv = '''Emissivity Class|TIRS10|TIRS11
Cropland|0.971|0.968
Forest|0.995|0.996
Grasslands|0.97|0.971
Shrublands|0.969|0.97
Wetlands|0.992|0.998
Waterbodies|0.992|0.998
Tundra|0.98|0.984
Impervious|0.973|0.981
Barren Land|0.969|0.978
Snow and ice|0.992|0.998'''

# required librairies -------------------------------------------------------
import collections
import random

# helpers -------------------------------------------------------------------
def is_number(s):
    try:
        float(s) # for int, long and float
    except ValueError:
        try:
            complex(s) # for complex
        except ValueError:
            return False
    return True
 
def csv_to_dictionary(csv):
    '''
    Transform inout from csv into a python dictionary with namedtuples as
    values
    '''
    # split input in rows
    rows = csv.split('\n')
    dictionary = {}  # empty dictionary
    fields = rows.pop(0).split('|')[1:]  # header

    # -----------------------------------------------------------------------    
    def transform(row):
        '''
        Transform an input row as follows
        '''
        elements = row.split('|')  # split row in elements
        key = elements[0].replace (" ", "_")  # key: class name, replace ''w/ _
        ect = collections.namedtuple(key, [fields[0], fields[1]])  # namedtuple
        ect.TIRS10, ect.TIRS11 = is_number(elements[1]), is_number(elements[2])  # feed namedtuples
        dictionary[key] = dictionary.get(key, ect)  # feed dictionary
    # -----------------------------------------------------------------------
    map(transform, rows)
    return dictionary

# main ----------------------------------------------------------------------
def main():
    emissivity_coefficients = csv_to_dictionary(csv)
    return emissivity_coefficients

# Test data =================================================================
def test(testdata):
    '''
    Testing the process...
    '''
    d = csv_to_dictionary(testdata)
    print "Dictionary is:\n", d
    
    somekey = random.choice(d.keys())
    print "Some random key:", somekey
    
    fields = d[somekey]._fields
    print "Fields of namedtuple:", fields
    
    random_field = random.choice(fields)
    print "Some random field:", random_field
    print "Return values (namedtuple):", d[somekey].TIRS10, d[somekey].TIRS11
    
#testdata = '''LandCoverClass|TIRS10|TIRS11
#Cropland|0.971|0.968
#Forest|0.995|0.996
#Grasslands|0.970|0.971
#Shrublands|0.969|0.970
#Wetlands|0.992|0.998
#Waterbodies|0.992|0.998
#Tundra|0.980|0.984
#Impervious|0.973|0.981
#Barren_Land|0.969|0.978
#Snow_and_Ice|0.992|0.998'''

#test(testdata)  # Ucomment to run the test function!

''' Output ------------------------------
{'Wetlands': <class '__main__.Wetlands'>,
 'Snow_and_Ice': <class '__main__.Snow_and_Ice'>,
 'Impervious': <class '__main__.Impervious'>,
 'Grasslands': <class '__main__.Grasslands'>,
 'Shrublands': <class '__main__.Shrublands'>,
 'Cropland': <class '__main__.Cropland'>,
 'Tundra': <class '__main__.Tundra'>,
 'Barren_Land': <class '__main__.Barren_Land'>,
 'Forest': <class '__main__.Forest'>,
 'Waterbodies': <class '__main__.Waterbodies'>}
------------------------------------ '''

if __name__ == "__main__":
    main()
