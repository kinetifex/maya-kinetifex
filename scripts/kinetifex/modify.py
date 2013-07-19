"""
Functions for modifying the transformation tools.
"""


import pymel.core as pm
from pymel.core import mel
from pymel.core.datatypes import Vector
#from pymelX import register_runtime
from impress import register

from config import RUNTIME_SUITE


@register.runtime
def cycleMoveMode():
    """Cycle movement modes of the Move Tool (Object, Local, World)"""

    mode = pm.manipMoveContext( 'Move', query=True, mode=True )
    newMode = (mode+1)%3
    pm.manipMoveContext( 'Move', edit=True, mode=newMode )

    mel.MoveTool()

    print "// Move Tool: %s //" % ("Object", "Local", "World")[newMode]


@register.runtime
def cycleRotateMode():
    """Cycle rotation modes of the Rotate Tool (Local, Global, Gimbal)"""

    mode = pm.manipRotateContext( 'Rotate', query=True, mode=True )
    newMode = (mode+1)%3
    pm.manipRotateContext( 'Rotate', edit=True, mode=newMode )

    mel.RotateTool()

    print "// Rotate Tool: %s //" % ("Local", "Global", "Gimbal")[newMode]


def pickWalkAdd( direction ):
    """Pick walk that adds pickwalk selected items to current selection"""
    selected = pm.ls( selection=True )
    pm.pickWalk( direction=direction )
    pm.select( selected, add=True )

    selected = pm.ls( selection=True )

    print '// Result: %s //' % ' '.join( [str(x) for x in selected] )


@register.runtime
def pickWalkAddUp():
    """Pick walk that adds Up selected items to current selection"""
    pickWalkAdd('up')


@register.runtime
def pickWalkAddDown():
    """Pick walk that adds Down selected items to current selection"""
    pickWalkAdd('down')


@register.runtime
def pickWalkAddLeft():
    """Pick walk that adds Left selected items to current selection"""
    pickWalkAdd('left')


@register.runtime
def pickWalkAddRight():
    """Pick walk that adds Right selected items to current selection"""
    pickWalkAdd('right')


@register.runtime
def unfreezeTranslation( options=False ):
    if options:
        pass
    else:
        objects = pm.ls(selection=True, type='transform')

        if not objects:
            mel.warning('Unfreeze Translation requires at least 1 selected object.')
        else:
            unfreezeTranslationCmd( objects )


def unfreezeTranslationCmd( objects ):
    results=0

    for object in pm.ls( objects, dag=True, type='transform' ):
        pm.makeIdentity( object, apply=True, translate=True )
        pos = Vector( pm.xform( object, query=True, objectSpace=True, rotatePivot=True ) )
        object.translate.set( pos*-1 )
        pm.makeIdentity( object, apply=True, translate=True )
        object.translate.set( pos )
        results+=1

    print '// Results: Translation of %i objects unfrozen. //' % results