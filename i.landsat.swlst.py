# -*- coding: utf-8 -*-
"""
@author: nik | Created on Wed Mar 18 10:00:53 2015
"""

"""
A new refinement of the generalized split-window algorithm proposed by Wan 
(2014) [19] is added with a quadratic term of the difference amongst the 
brightness temperatures (Ti, Tj) of the adjacent thermal infrared channels, 
which can be expressed as

LST = b0 + [b1 + b2 * (1−ε)/ε + b3 * (Δε/ε2)] * (Ti+T)/j2 + [b4 + b5 * (1−ε)/ε + b6 * (Δε/ε2)] * (Ti−Tj)/2 + b7 * (Ti−Tj)^2
(2)

where:

  - Ti and Tj are the TOA brightness temperatures measured in channels i 
(~11.0 μm) and j (~12.0 µm), respectively;
  - ε is the average emissivity of the two channels (i.e., ε = 0.5 [εi + εj]),
  - Δε is the channel emissivity difference (i.e., Δε = εi − εj);
  - bk (k = 0,1,...7) are the algorithm coefficients derived in the following 
  simulated dataset.

...

In the above equations,
    - dk (k = 0, 1...6) and ek (k = 1, 2, 3, 4) are the algorithm coefficients;
    - w is the CWV;
    - ε and ∆ε are the average emissivity and emissivity difference of two adjacent
      thermal channels, respectively, which are similar to Equation (2);
    - and fk (k = 0 and 1) is related to the influence of the atmospheric transmittance and emissivity,
      i.e., f k = f(εi,εj,τ i ,τj).
      
Note that the algorithm (Equation (6a)) proposed by Jiménez-Muñoz et al. added CWV
directly to estimate LST.

Rozenstein et al. used CWV to estimate the atmospheric transmittance (τi, τj) and
optimize retrieval accuracy explicitly.

Therefore, if the atmospheric CWV is unknown or cannot be obtained successfully,
neither of the two algorithms in Equations (6a) and (6b) will work. By contrast,
although our algorithm also needs CWV to determine the coefficients, this algorithm
still works for unknown CWVs because the coefficients are obtained regardless of the CWV,
as shown in Table 1.

...


  Source:
  - <http://www.mdpi.com/2072-4292/7/1/647/htm#sthash.ba1pt9hj.dpuf>

"""

"""
From <http://landsat.usgs.gov/band_designations_landsat_satellites.php>
Band 10 - Thermal Infrared (TIRS) 1 	10.60 - 11.19 	100 * (30)
Band 11 - Thermal Infrared (TIRS) 2 	11.50 - 12.51 	100 * (30)
"""

#%option G_OPT_R_BASENAME_INPUT
#% key: input_prefix
#% key_desc: prefix string
#% type: string
#% label: Prefix of input bands
#% description: Prefix of Landsat8 brightness temperatures bands imported in GRASS' data base
#% required: yes
#%end

or

#%option G_OPT_R_INPUTS
#% key: band
#% key_desc: band name
#% type: string
#% label: QuickBird2 band
#% description: QuickBird2 acquired spectral band(s) (DN values)
#% multiple: yes
#% required: yes
#%end

#%option G_OPT_R_OUTPUT
#%end

import SplitWindowLandSurfaceTemperature
t10  # i
t11  # j


def main():
    
    t10 = input
    t11 = input
    
    b0 to b7 -> from dictionary/class?
    emissivities -> from dictionary/class?
    emissivity_b10 = float()
    emissivity_b11 = float()


    land_surface_temperature = SplitWindowLandSurfaceTemperature() 


