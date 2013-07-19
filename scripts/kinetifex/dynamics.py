"""
Functions used for working with dynamics.
"""


import pymel.core as pm
##from pymelX import register_runtime
from impress import register

from config import RUNTIME_SUITE


@register.runtime
def loopDynamics( loops=3 ):
    """Sets initial state of particles to values of end frame."""
    pm.waitCursor( state=True )

    startFrame = pm.playbackOptions( query=True, min=True )
    endFrame = pm.playbackOptions( query=True, max=True )

    for i in range( loops ):
        for j in range( startFrame, endFrame+1 ):
            pm.currentTime( j )

        pm.saveInitialState( all=True )

    pm.currentTime( startFrame )

    pm.waitCursor( state=False )

    print '// Result: Particle states set.'

@register.runtime
def restDynamics( restTime=100 ):
    """Positions particles at their goal objects."""
    pm.waitCursor( state=True )

    currentFrame = pm.currentTime()

    for i in range( restTime ):
        pm.currentTime( currentFrame+.1 )
        pm.currentTime( currentFrame )

    pm.waitCursor( state=False )

    print '// Result: Particle states rested.'