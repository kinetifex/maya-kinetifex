"""
Functions used in animating.
"""


import pymel.core as pm
from pymel.core import mel
from impress import register


def getSelectedCurvesKeys():
    """
    Get the currently selected animation curves and keys.

    @return: A dict containing animation curves and keys.
    @rtype: dict
    """

    selList = {}

    for object in pm.ls( sl=True ):
        try:
            for curve in pm.keyframe( object, query=True, selected=True, name=True ):
                selList[curve] = tuple( pm.keyframe( curve, query=True, selected=True ) )
        except:
            pass

    return selList


def smoothTangent( side='in' ):
    """
    Adjusts selected key tangents to have a smooth linear in or out.

    @param side: default: C{'in'} Which tangent side to set linear angle. Valid options are 'in' and 'out'.
    @type side: string
    """

    for ( curve, keys ) in getSelectedCurvesKeys().iteritems():
        for key in keys:
            lockState = pm.keyTangent( curve, time=( key, key ), query=True, lock=True )[0]

            if side == 'in':
                pm.keyTangent( curve, time=( key, key ), outTangentType='linear', lock=False )
                pm.keyTangent( curve, time=( key, key ),
                            inAngle=pm.keyTangent( curve, query=True, outAngle=True, time=( key, key ) )[0] )

            elif side == 'out':
                pm.keyTangent( curve, time=( key, key ), inTangentType='linear', lock=False )
                pm.keyTangent( curve, time=( key, key ),
                            outAngle=pm.keyTangent( curve, query=True, inAngle=True, time=( key, key ) )[0] )
            else:
                pm.mel.error( 'Invalid argument: "%s"' % side )

            pm.keyTangent( curve, lock=lockState, time=( key, key ) )


smoothTangentIn = register.RuntimeCommand( smoothTangent, name='smoothTangentIn', args=( 'in', ) )
smoothTangentOut = register.RuntimeCommand( smoothTangent, name='smoothTangentOut', args=( 'out', ) )


@register.runtime
def flipCurve( curves=None, valuePiv=None ):
    """
    Flip the selected curve(s). If valuePiv is C{'None'}, curve will be flipped over value at current time.

    @param valuePiv: default: C{None} If valuePiv is C{'None'}, curve will be flipped over value at current time.
    @type valuePiv: float
    """
    if curves is None:
        curves = getSelectedCurvesKeys().iterkeys()

    for curve in curves:
        if valuePiv is None:
            valuePiv = pm.keyframe( curve, query=True, eval=True )[0]
        else:
            pass
        pm.scaleKey( curve, valueScale= -1.0, valuePivot=valuePiv )


@register.runtime
def mirrorCurve( curves=None ):
    """
    Mirror selected curve(s) over zero value. Simply calls the flipCurve function with '0' as the value pivot.
    """
    flipCurve( valuePiv=0, curves=curves )


@register.runtime
def reverseCurve( timePiv=None ):
    """
    Reverse the selected curve(s). If timePiv is C{'None'}, curve will be reversed at current time.

    @param timePiv: timePiv: C{None} If timePiv is C{'None'}, curve will be reversed at current time.
    @type timePiv: float
    """
    for curve in getSelectedCurvesKeys().iterkeys():
        if timePiv is None:
            timePiv = ( pm.findKeyframe( curve, which='first' ) + pm.findKeyframe( curve, which='last' ) ) / 2
        else:
            pass
        pm.scaleKey( curve, timeScale= -1.0, timePivot=timePiv )


def loopCurve( curveList=[], which='first' ):
    """
    Adjust keyframes and tangents of selected curves to loop.

    @param curveList: a list of curves to affect.
    @type curveList: list
    @param which: default: Specify which keyframe will be adjusted. Options are C{'first'} (default) and {'last'}
    @type which: string
    """

    if len( curveList ) is 0:
        curveList = getSelectedCurvesKeys().keys()

    for curve in curveList:
        endsKeys = [pm.findKeyframe( curve, which='first' ), pm.findKeyframe( curve, which='last' )]
        if which is 'last':
            endsKeys.reverse()
        lockState = pm.keyTangent( curve, time=( endsKeys[0], endsKeys[0] ), query=True, lock=True )[0]

        pm.keyframe( curve, time=( endsKeys[0], endsKeys[0] ),
                  valueChange=pm.keyframe( curve, time=( endsKeys[1], endsKeys[1] ), query=True, valueChange=True )[0] )
        if which is 'first':
            pm.keyTangent( curve, time=( endsKeys[0], endsKeys[0] ), edit=True, lock=False,
                        outAngle=pm.keyTangent( curve, query=True, inAngle=True, time=( endsKeys[1], endsKeys[1] ) )[0] )
        elif which is 'last':
            pm.keyTangent( curve, time=( endsKeys[0], endsKeys[0] ), edit=True, lock=False,
                        inAngle=pm.keyTangent( curve, query=True, outAngle=True, time=( endsKeys[1], endsKeys[1] ) )[0] )
        else:
            pass
        pm.keyTangent( curve, lock=lockState, time=( endsKeys[0], endsKeys[0] ) )


loopCurveFirst = register.RuntimeCommand( loopCurve, name="loopCurveFirst", kwargs={'which':'first'} )
loopCurveLast = register.RuntimeCommand( loopCurve, name="loopCurveLast", kwargs={'which':'last'} )


def offsetKeyframes( valueChange=360 ):
    """Offset selected keyframes."""
    pm.keyframe( edit=True, iub=True, relative=True, valueChange=valueChange )


offsetKeyframesUp360 = register.RuntimeCommand( offsetKeyframes, name="offsetKeyframesUp360", kwargs={'valueChange':360} )
offsetKeyframesDown360 = register.RuntimeCommand( offsetKeyframes, name="offsetKeyframesDown360", kwargs={'valueChange':-360} )


@register.runtime
def resetIk( translation=True, rotation=True ):
    """Reset translation and rotation of selected IK control(s)"""
    objects = pm.ls( selection=True, type='transform' )

    if not objects:
        mel.warning( 'no transform objects selected.' )
    else:
        resetIkCmd( objects, translation, rotation )


@register.runtime
def resetIkTranslate():
    """Reset translation of selected IK control(s)"""
    resetIk( translation=True, rotation=False )


@register.runtime
def resetIkRotate():
    """Reset rotation of selected IK control(s)"""
    resetIk( translation=False, rotation=True )


def resetIkCmd( controls, translation=False, rotation=False ):
    for control in controls:

        try:
            reset_target = pm.PyNode( control + '_resetik' )
        except pm.MayaNodeError:
            mel.warning ( 'Reset IK target not found for %s' % control )
            return False


        unit_scale = reset_target.getRotatePivot( worldSpace=True )[-1]

        tgtPos = reset_target.getRotatePivot( worldSpace=True ) * unit_scale
        objPos = control.getRotatePivot( worldSpace=True ) * unit_scale

        newPos = tgtPos - objPos

        tgtRot = reset_target.getRotation( worldSpace=True )

        if translation:
            pm.xform( control, translation=newPos, relative=True, worldSpace=True )
        if rotation:
            pm.xform( control, rotation=tgtRot, worldSpace=True )

"""
def forceOriginToggle( axis=['translateX','translateZ','translateY'] ):
    "Wrapper for forceOriginToggle mel script."
    mel.kx_forceOriginToggle( axis )


def forceOriginSetup():
    "Wrapper for forceOriginSetup mel script."
    mel.kx_forceOriginSetup()

def mirrorAnimation( options=False ):
    "Wrapper for mirrorAnimation mel script."
    mel.kx_mirrorAnim( int(options) )
"""

@register.runtime
def toggleInfinityCycle():
    """Toggle infinite cycle with offset for curves on selected object(s)"""

    try:
        if 'constant' not in pm.setInfinity( query=True, poi=True ):
            pm.setInfinity( poi='constant', pri='constant' )
        else:
            pm.setInfinity( poi='cycleRelative', pri='cycleRelative' )
    except:
        mel.warning( 'Select object(s) with animation curves.' )

    pm.animCurveEditor( 'graphEditor1GraphEd', edit=True, displayInfinities='on' )



prefix = [ 'L', 'R' ]

transList = ( 'translateX', 'translateY', 'translateZ',
              'rotateX', 'rotateY', 'rotateZ',
              'scaleX', 'scaleY', 'scaleZ'
              )
mirrAttrs = { 'XY': ( 'translateZ', 'rotateX', 'rotateY' ),
              'YZ': ( 'translateX', 'rotateY', 'rotateZ' ),
              'XZ': ( 'translateY', 'rotateX', 'rotateZ' )
              }
extrasList = ( 'toeSwing', 'ballSwing', 'heelSwing',
               'toeBank', 'ballBank', 'heelBank'
               )

@register.runtime
def mirrorAnimation( defaultAxis='XZ' ):

    tempGroups = []

    st2 = pm.timerX()

    pm.waitCursor( state=True )

    autoKeyState = pm.autoKeyframe( query=True, state=True )
    pm.autoKeyframe( state=False )


    pm.select( pm.ls( selection=True ), replace=True )
    objects = pm.ls( selection=True, type='transform' )

    if len( objects ) == 0:
        mel.warning( 'No Transform objects selected for mirroring.' )
    else:
        for obj in objects:

            if obj.mirrorAxis.exists():
                axis = ( 'XY', 'YZ', 'XZ' )[ obj.mirrorAxis.get() ]
            else:
                axis = defaultAxis

            split = obj.split( ':' )

            if len( split ) > 1:
                a = split[1]
            else:
                a = obj

            if a.startswith( prefix[0] ) or  a.startswith( prefix[1] ):
                if a.startswith( prefix[1] ):
                    prefix.reverse()

                opposite = pm.PyNode( obj.replace( prefix[0], prefix[1] ) )
            else:
                opposite = None

            if opposite is not None and opposite.exists():

                # -- make holder group --

                g = pm.group( name='%s_holder' % obj, empty=True )
                tempGroups.append( g )

                ud_attrs = map( pm.Attribute, obj.listAttr( keyable=True ) )
                for attr in ud_attrs:
                    newAttr = pm.Attribute( '%s.%s' % ( g, attr.longName() ) )

                    if not newAttr.exists():
                        newAttr.add( attributeType=attr.type(), keyable=True )

                    if attr.longName() in mirrAttrs[axis] or attr.longName() in extrasList:
                        newAttr.set( -attr.get() )
                    else:
                        newAttr.set( attr.get() )

                    copy_result = pm.copyKey( obj, hierarchy='none', controlPoints=0, shape=1 )

                    if copy_result > 0:
                        pm.pasteKey( g, option='replaceCompletely', copies=1, connect=1, timeOffset=0, floatOffset=0, valueOffset=0 )

                # -- get opposite's values/keys --

                og = '%s_holder' % opposite
                print 'tempGroups:', tempGroups
                print 'og:', og

                print len( tempGroups )

                if og in tempGroups:
                    obj2 = og
                else:
                    obj2 = opposite

                copy_result = pm.copyKey( obj2, hierarchy=None, controlPoints=0, shape=1 )

                if copy_result > 0:
                    pm.pasteKey( obj, option='replaceCompletely', copies=1, connect=1, timeOffset=0, floatOffset=0, valueOffset=0 )

                for attr in ud_attrs:
                    srcAttr = pm.Attribute( '%s.%s' % ( obj2, attr.longName() ) )

                    if srcAttr.exists():
                        if attr.longName() in mirrAttrs[axis] or attr.longName() in extrasList:
                            attr.set( -srcAttr.get() )
                            mirrorCurve( curves=attr.listConnections() )

                        else:
                            attr.set( srcAttr.get() )
            else:
                for attr in map( pm.Attribute, obj.listAttr( keyable=True ) ):

                    if attr.longName() in mirrAttrs[axis] or attr.longName() in extrasList:
                        attr.set( -attr.get() )
                        mirrorCurve( curves=attr.listConnections() )

        # -- Finalize --

        try:
            pm.delete( tempGroups )
        except:
            pass

        pm.select( objects, replace=True )

        pm.autoKeyframe( state=autoKeyState )

        print '// Results: Mirrored animation for %i objects in %f seconds' % ( len( objects ), pm.timerX( st=st2 ) )

    pm.waitCursor( state=False )





def _keyTickSpecial( enable=True ):

    keys_sl = True

    nodes = pm.ls( sl=1 )

    # -- if no keys are selected, get keys at current time
    if not pm.keyframe( q=1, sl=1 ):
        keys_sl = False
        ct = pm.currentTime( q=1 )
        pm.selectKey( nodes, k=1, t=( ct, ct ) )

    # -- only update the ticks if we have selected keys
    if pm.keyframe( q=1, sl=1 ):
        pm.keyframe( e=1, tickDrawSpecial=enable )

    # -- if we didn't start out with selected keys, clear the selection.
    if not keys_sl:
        pm.selectKey( cl=1 )


@register.runtime
def keyTickSpecialOn():
    _keyTickSpecial( 1 )

@register.runtime
def keyTickSpecialOff():
    _keyTickSpecial( 0 )


class switchParentWindow ( object ):

    def __init__( self, name, title='Switch Parent Window' ):
        self.__name__ = name
        self.title = title

    def _switchParent( self, *args ):
        parent_name = self.scroll_control.getSelectItem()[0]
        switchParentCmd( self.sel_control, parent_name )


    def _buildControls( self ):
        main_form = pm.formLayout()

        self.scroll_control = pm.textScrollList( allowMultiSelection=False, selectCommand=self._switchParent )

        ok_btn = pm.button( label="Switch", command=lambda args: self._switchParent() )
        close_btn = pm.button( label="Close", command=lambda args: self.delete() )

        main_form.attachForm( self.scroll_control, 'top', 6 )
        main_form.attachForm( self.scroll_control, 'left', 0 )
        main_form.attachForm( self.scroll_control, 'right', 0 )
        main_form.attachControl( self.scroll_control, 'bottom', 6, ok_btn )

        main_form.attachNone( ok_btn, 'top' )
        main_form.attachForm( ok_btn, 'left', 0 )
        main_form.attachPosition( ok_btn, 'right', 1, 50 )
        main_form.attachForm( ok_btn, 'bottom', 6 )

        main_form.attachNone( close_btn, 'top' )
        main_form.attachPosition( close_btn, 'left', 1, 50 )
        main_form.attachForm( close_btn, 'right', 0 )
        main_form.attachForm( close_btn, 'bottom', 6 )


    def _updateControls( self, forceDefaults=False ):

        self.scroll_control.removeAll()

        sel_list = pm.ls( sl=1, type='transform' )
        if sel_list:
            self.sel_control = sel_list[-1]

            if self.sel_control.hasAttr( 'parent' ):
                enum_list = pm.addAttr( str( self.sel_control.parent ), enumName=1, q=1 ).split( ':' )
                self.scroll_control.append( enum_list )
                self.scroll_control.setSelectIndexedItem( self.sel_control.parent.get() + 1 )


    def show( self, *args ):
        self.delete()

        self.win = pm.window( self.__name__, toolbox=True, resizeToFitChildren=True )
        self.win.setTitle( self.title )

        self._buildControls()
        self._updateControls()

        self.win.show()

        jobCmd = r'python(\"%s.%s._updateControls()\");' % ( __name__, self.__name__ )
        job1 = "scriptJob -parent \"%s\" -event \"SelectionChanged\" \"%s\";" % ( self.__name__, jobCmd )
        job2 = "scriptJob -parent \"%s\" -event \"timeChanged\" \"%s\";" % ( self.__name__, jobCmd )
        mel.eval( job1 )
        mel.eval( job2 )


    def delete( self, *args ):
        try:
            pm.deleteUI( self.__name__ )
        except:
            pass


switchParentWin = switchParentWindow( 'switchParentWin' )

@register.runtime
def openSwitchParentWindow():
    """
    Window for switching the "parent" attribute with translation and rotation.
    """
    switchParentWin.show()


def switchParentCmd( control, parent_name ):

    control = pm.PyNode( control )

    if not control.hasAttr( 'parent' ):
        assert 'No "parent" attribute found for "%s".' % control

    enum_list = pm.addAttr( str( control.parent ), enumName=1, q=1 ).split( ':' )

    if not parent_name in enum_list:
        assert '"%s" not in %s parent list (%s)' % ( parent_name, control, ','.join( enum_list ) )

    parent_id = enum_list.index( parent_name )
    parent_current = enum_list[ control.parent.get() ]
    target = pm.PyNode( "%s_target%d" % ( control, parent_id ) )

    _t = pm.xform( target, q=1, t=1 )
    _r = pm.xform( target, q=1, ro=1 )

    pm.xform( control, t=_t, ro=_r )
    control.parent.set( parent_id )

    print '// Switched "%s" from "%s" to "%s".' % ( control, parent_current, parent_name )


