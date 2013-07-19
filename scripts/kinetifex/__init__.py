"""
Project independent Maya Python scripts packages.
"""

__version__ = 0.2


import animation
import display
import dynamics
import modeling
import materials
import modify
import poses
import rigging
import scene
import menu
import skinning

import config


from pymel.core import about, evalDeferred, mel


try:
    _initialized
except:
    _initialized = False

if not _initialized:
    _initialized = True

    mel.python( 'import kinetifex' )

    if not about( batch=True ):
        evalDeferred( display._initHudElements )

