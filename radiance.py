from grass.pygrass.modules.shortcuts import general as g
from dummy_mapcalc_strings import replace_dummies
from constants import DUMMY_MAPCALC_STRING_DN
from constants import DUMMY_MAPCALC_STRING_RADIANCE
from constants import EQUATION
import grass.script as grass
from helpers import run

def digital_numbers_to_radiance(
        outname,
        band,
        radiance_expression,
        null=False,
        info=False,
    ):
    """
    Convert Digital Number values to TOA Radiance. For details, see in Landsat8
    class.  Zero (0) DNs set to NULL here (not via the class' function).
    """
    if null:
        msg = f'\n|i Setting zero (0) Digital Numbers in {band} to NULL'
        g.message(msg)
        run('r.null',
                map=band,
                setnull=0,
        )

    msg = f'\n|i Rescaling {band} digital numbers to spectral radiance'

    if info:
        msg += f'\n   {radiance_expression}'

    g.message(msg)
    radiance_expression = replace_dummies(
            radiance_expression,
            instring=DUMMY_MAPCALC_STRING_DN,
            outstring=band,
    )
    radiance_equation = EQUATION.format(
            result=outname,
            expression=radiance_expression,
    )
    grass.mapcalc(radiance_equation, overwrite=True)

    if info:
        run('r.info',
                map=outname,
                flags='r',
        )


def radiance_to_brightness_temperature(
        outname,
        radiance,
        temperature_expression,
        info=False,
    ):
    """
    Convert Spectral Radiance to At-Satellite Brightness Temperature. For
    details see Landsat8 class.
    """
    temperature_expression = replace_dummies(
            temperature_expression,
            instring=DUMMY_MAPCALC_STRING_RADIANCE,
            outstring=radiance,
    )

    msg = "\n|i Converting spectral radiance to at-satellite temperature"
    if info:
        msg += f'\n   {temperature_expression}'
    g.message(msg)

    temperature_equation = EQUATION.format(
            result=outname,
            expression=temperature_expression,
    )

    grass.mapcalc(temperature_equation, overwrite=True)

    if info:
        run('r.info',
                map=outname,
                flags='r',
        )
