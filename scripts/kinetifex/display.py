"""
Functions relating to the display of objects and viewport elements.
"""


import pymel.core as pm
#import pymelX as pmx
#from pymelX import OptionVar
from impress import register

from config import RUNTIME_SUITE


@register.runtime
def toggleIsolateSelected():
    """Toggle isolated view of selection"""

    newState = not pm.isolateSelect( 'modelPanel4', query=True, state=True )

    for i in range( 1, 5 ):
        pm.isolateSelect( 'modelPanel%s' % i, state=newState )
        pm.isolateSelect( 'modelPanel%s' % i, addSelected=True )


@register.runtime
def toggleXRay():
    """Toggle x-ray view"""

    newState = not pm.modelEditor( 'modelPanel4', query=True, xray=True )

    for i in range( 1, 5 ):
        pm.modelEditor( 'modelPanel%s' % i, edit=True, xray=newState )


@register.runtime
def toggleWireframeOnShaded():
    """Toggle Wireframe On Shaded view"""

    newState = not pm.modelEditor( 'modelPanel4', query=True, wireframeOnShaded=True )

    for i in range( 1, 5 ):
        pm.modelEditor( 'modelPanel%s' % i, edit=True, wireframeOnShaded=newState )


@register.runtime
def togglePlaybackSpeed():
    """Toggle between Real-time and Every Frame playback"""

    newSpeed = not bool( pm.playbackOptions( playbackSpeed=True, query=True ) )
    pm.playbackOptions( playbackSpeed=newSpeed )

    pm.headsUpDisplay( 'HUDPlaybackSpeed', edit=True )
    print 'Playback Speed: %s' % ( 'Every Frame', 'Real-time' )[newSpeed]


@register.runtime
def togglePlaybackSnap():
    """Toggle playback snapping on and off"""

    gPlayBackSlider = pm.getMelGlobal( 'string', 'gPlayBackSlider' )

    new_value = not bool( pm.timeControl( gPlayBackSlider, q=1, snap=1 ) )
    pm.timeControl( gPlayBackSlider, e=1, snap=new_value )

    print 'Playback Snapping: %s' % ( 'Off', 'On' )[new_value]


@register.runtime
def cycleGridDisplay():
    """Cycle through different grid views."""

    if pm.grid( toggle=True, query=True ) and pm.grid( displayDivisionLines=True, query=True ):
        pm.grid( displayDivisionLines=False )
        msg = 'divisions OFF'
    elif pm.grid( toggle=True, query=True ) and not pm.grid( displayDivisionLines=True, query=True ):
        pm.grid( toggle=False )
        msg = 'display OFF'
    else:
        pm.grid( toggle=True )
        pm.grid( displayDivisionLines=True )
        msg = 'display ON'

    return "Grid View: %s" % msg


def toggleLighting():
    """Toggle between vertex colors and scene lighting"""

    currentPanel = pm.getPanel( withFocus=True )
    if pm.getPanel( typeOf=currentPanel ) == 'modelPanel':

        displayLights = pm.modelEditor( currentPanel, query=True, displayLights=True )

        if displayLights != 'all':
            pm.polyOptions( cs=0 )
            pm.modelEditor( currentPanel, edit=True, displayLights='all' )
            msg = 'ON (scene lights)'
        else:
            pm.polyOptions( cs=1, cm='ambientDiffuse' )
            pm.modelEditor( currentPanel, edit=True, displayLights='default' )
            pm.modelEditor( currentPanel, edit=True, displayLights='none' )
            msg = 'OFF (vertex colors)'

        return 'Lighting: %s' % msg

'''
class BackgroundColorsOptionBox( pmx.OptionBox ):
    _title = 'Background Color Options'
    _helpTag = 'cycleBackgroundColor'
    _buttonLabel = 'Cycle Colors'

    optCount  = OptionVar( 'backgroundColors_count', 4 )
    optColors = OptionVar( 'backgroundColors_colors', [ (0.631, 0.631, 0.631),
                                                        (0.461, 0.461, 0.461),
                                                        (0.137, 0.137, 0.137),
                                                        ] + [ (0,0,0) ] * 5
                           )

    options = [ optCount, optColors ]


    def _buildControls(self):
        self.optCount.control = pm.intSliderGrp( label='Color Count', min=1, max=8,
                                              changeCommand=lambda *args: ( self._updateOptions(), self._updateControls() )
                                              )
        self.optColors.controls = []

        pm.separator( style='none', height=12 )

        for i in range( 8 ):
            self.optColors.controls.append(
                pm.colorSliderGrp( label='Color %d' % i, rgb=(0,0,0) )
            )


    def _updateControls( self, forceDefaults=False ):
        pmx.setOptionVars( self.options, forceDefaults )

        count = self.optCount.get()
        colors = self.optColors.get()

        pm.intSliderGrp( self.optCount.control, edit=True, value=self.optCount.get() )

        i=0
        for control in self.optColors.controls:
            if i < count:
                pm.colorSliderGrp( control, edit=True, visible=True, rgb=colors[i] )
            else:
                pm.colorSliderGrp( control, edit=True, visible=False, rgb=colors[i] )
            i+=1


    def _updateOptions(self):
        value = pm.intSliderGrp( self.optCount.control, query=True, value=True )
        self.optCount.set( value )

        values = []
        for control in self.optColors.controls:
            values.append( pm.colorSliderGrp( control, query=True, rgb=True ) )

        self.optColors.set( values )


    def apply(self):
        cycleBackgroundColors()


@register.runtime
def cycleBackgroundColors( options=False ):
    """Cycle through background colors"""
    if options:
        BackgroundColorsOptionBox().show()
    else:
        pass
        count  = OptionVar( 'backgroundColors_count', 4 ).get()
        colors = OptionVar( 'backgroundColors_colors', [ (0.631, 0.631, 0.631),
                                                         (0.461, 0.461, 0.461),
                                                         (0.137, 0.137, 0.137),
                                                         ] + [ (0,0,0) ] * 5
                            ).get()

        optCurrent = OptionVar( 'backgroundColors_current', 0 )

        next = ( optCurrent.get() + 1 ) % count

        pm.displayRGBColor( 'background',
                         colors[ next ][0],
                         colors[ next ][1],
                         colors[ next ][2]
                         )

        optCurrent.set( next )
'''

#----------------------------------------------------------------------------
#
#----------------------------------------------------------------------------

def _getParentHeirarchy( node ):
    """
    Returns a list containing the parent objects for the specified node.
    @rtype: list
    """
    nodeList = []
    parents = node.longName().split( '|' )[1:]
    for i in range( 0, len( parents ) + 1 )[1:]:
        nodeList.append( pm.PyNode( "|" + "|".join( parents[:i] ) ) )
    return nodeList


def _checkVisibility( node ):
    """
    Check a node for visibility affected layer display.
    """
    visible = True
    for parent in _getParentHeirarchy( node ):
        for conn in parent.listConnections( type='displayLayer' ):
            if conn.visibility.get() == False:
                visible = False
    return visible


def _countVisible( nodeList ):
    count = 0
    for node in nodeList:
        if _checkVisibility( node ):
            count = count + 1
    return count


def countJoints( checkConnections=False ):
    """
    Counts the visible joints in scene.
    @return: Tuple with 3 int elements: totals for visible joints, selected heiarchy, and selected.
    @rtype: (int,int,int)
    """
    if checkConnections == True:
        jointCount = ( 
            _countVisible( pm.ls( type='joint', visible=True ) ),
            _countVisible( pm.ls( type='joint', visible=True, selection=True, dag=True ) ),
            _countVisible( pm.ls( type='joint', visible=True, selection=True ) )
        )
        return jointCount
    else:
        jointCount = ( 
            len( pm.ls( type='joint', visible=True ) ),
            len( pm.ls( type='joint', visible=True, selection=True, dag=True ) ),
            len( pm.ls( type='joint', visible=True, selection=True ) )
        )
        return jointCount


@register.runtime
def jointCountHUD( toggle=True ):
    """
    Toggle the display of joint count.

    HUD element that shows the total visible joints in scene. The numbers represent the total number if visible joints,
    the number of visible selected joints in selection hierarchy, and the number of visible selected joints only.
    """

    opt_vis = 'jointCountHUDVis'

    if toggle:
        pm.optionVar[opt_vis] = not pm.optionVar.get( opt_vis, False )

    if pm.headsUpDisplay( 'HUDJointCount', exists=True ):
        pm.headsUpDisplay( 'HUDJointCount', remove=True )

    block = pm.headsUpDisplay( nextFreeBlock=0 )

    pm.headsUpDisplay( 
        'HUDJointCount',
        visible=pm.optionVar.get( opt_vis, False ),
        section=0,
        block=block,
        label='Joints:',
        dataAlignment='right',
        labelWidth=50,
        dataWidth=65,
        command=countJoints,
        event='SelectionChanged'
    )


'''
# These HUD elements are now defaults in Maya 2013 so not really needed anymore

def countParticles():
    """
    Counts the visible particles in scene. This function is called by L{particleCountHUD}.
    @return: Tuple with 3 int elements: totals for visible particles, particles in selected/highlighted objects, and selected particle components.
    @rtype: (int,int,int)
    """

    # total number of particles in scene
    visCount = 0
    for obj in pm.ls( visible=True, dag=True, type='particle' ):
        visCount += pm.particle(obj, query=True, count=True)

    # number of particles in selected/hilighted objects
    selCount = 0
    for obj in set(pm.ls(visible=True, selection=True, dag=True, type='particle')) | set(pm.ls(visible=True, hilite=True, dag=True, type='particle' )):
        selCount += pm.particle(obj, query=True, count=True)

    # number of particles selected
    compCount = len( pm.ls( visible=True, selection=True, type='double3' ) )

    return (visCount, selCount, compCount)


@register.runtime
def particleCountHUD( toggle=True ):
    """
    Toggle the display of particle count.

    HUD element that shows the total visible particles in scene. The numbers represent the total visible particles in scene,
    the number of visibile particles in selected and hilighted particle objects, and the number of selected particle components.
    """

    opt_vis = 'particleCountHUDVis'

    if toggle:
        pm.optionVar[opt_vis] = not pm.optionVar.get(opt_vis, False)

    if pm.headsUpDisplay( 'HUDParticleCount', exists=True ):
        pm.headsUpDisplay( 'HUDParticleCount', remove=True )

    block=pm.headsUpDisplay( nextFreeBlock=0 )

    pm.headsUpDisplay(
        'HUDParticleCount',
        visible=pm.optionVar.get(opt_vis, False),
        section=0,
        block=block,
        label='Particle:',
        dataAlignment='right',
        labelWidth=50,
        dataWidth=65,
        command=countParticles,
        attachToRefresh=True
    )


def countTransforms( checkConnections=False ):
    if checkConnections == True:
        transformCount = (
            _countVisible( pm.ls(type='transform', visible=True) ),
            _countVisible( pm.ls(type='transform', visible=True, selection=True, dag=True) ),
            _countVisible( pm.ls(type='transform', visible=True, selection=True) )
        )
        return transformCount
    else:
        transformCount = (
            len( pm.ls(type='transform', visible=True) ),
            len( pm.ls(type='transform', visible=True, selection=True, dag=True) ),
            len( pm.ls(type='transform', visible=True, selection=True) )
        )
        return transformCount


def transformCountHUD( toggle=True ):
    """Toggle the display of transform object count."""

    opt_vis = 'transformCountHUDVis'

    if toggle:
        pm.optionVar[opt_vis] = not pm.optionVar.get(opt_vis, False)

    if pm.headsUpDisplay( 'HUDTransformCount', exists=True ):
        pm.headsUpDisplay( 'HUDTransformCount', remove=True )

    block=pm.headsUpDisplay( nextFreeBlock=0 )

    pm.headsUpDisplay(
        'HUDTransformCount',
        visible=pm.optionVar.get(opt_vis, False),
        section=0,
        block=block,
        label='Objects:',
        dataAlignment='right',
        labelWidth=50,
        dataWidth=65,
        command=countTransforms,
        event='SelectionChanged'
    )


def _getCurrentFrame():
    #currentFrame = str( currentTime(query=True) )

    currentFrame = pm.currentTime(query=True)

    return currentFrame


@register.runtime
def currentFrameHUD( toggle=True ):
    """Toggle the display of current frame."""

    opt_vis = 'currentFrameHUDVis'

    if toggle:
        pm.optionVar[opt_vis] = not pm.optionVar.get(opt_vis, False)

    if pm.headsUpDisplay( 'HUDCurrentFrame', exists=True ):
        pm.headsUpDisplay( 'HUDCurrentFrame', remove=True )

    block=pm.headsUpDisplay( nextFreeBlock=7 )

    pm.headsUpDisplay(
        'HUDCurrentFrame',
        visible=pm.optionVar.get(opt_vis, False),
        section=7,
        block=block,
        #label='',
        dataWidth=22,
        dataAlignment='right',
        command=_getCurrentFrame,
        attachToRefresh=True,
        #event='timeChanged',
        dataFontSize='large'
    )
'''

__time_values = {
    'game': 15,
    'film': 24,
    'pal': 25,
    'ntsc': 30,
    'show': 48,
    'palf': 50,
    'ntscf': 60
    }

def _getCurrentTime():
    #currentFrame = str( currentTime(query=True) )

    currentFrame = pm.currentTime( query=True )

    rate = __time_values[pm.currentUnit( q=1, time=1 )]

    return currentFrame / rate


@register.runtime
def currentTimeHUD( toggle=True ):
    """Toggle the display of current time."""

    opt_vis = 'currentTimeHUDVis'

    if toggle:
        pm.optionVar[opt_vis] = not pm.optionVar.get( opt_vis, False )

    if pm.headsUpDisplay( 'HUDCurrentTime', exists=True ):
        pm.headsUpDisplay( 'HUDCurrentTime', remove=True )

    block = pm.headsUpDisplay( nextFreeBlock=9 )

    pm.headsUpDisplay( 
        'HUDCurrentTime',
        visible=pm.optionVar.get( opt_vis, False ),
        section=9,
        block=block,

        label='Current Time:',
        dataAlignment='left',
        labelWidth=115,
        dataWidth=75,

        #label='',
        #dataWidth=22,
        #dataAlignment='right',
        command=_getCurrentTime,
        attachToRefresh=True,
        #dataFontSize='large'
    )


@register.runtime
def closeWindows( toggle=True ):
    """Close all open windows."""
    uiList = pm.lsUI( windows=True )

    for win in uiList:
        if win in ( 'CommandWindow', 'ColorEditor' ):
            try:
                pm.window( win, edit=True, visible=False )
            except:
                pass
        elif win not in ( 'progressWindow', 'MayaWindow' ):
            try:
                pm.deleteUI( win )
            except:
                pass


def _initHudElements():
    jointCountHUD( toggle=False )
    currentTimeHUD( toggle=False )
    #particleCountHUD( toggle=False )
    #transformCountHUD( toggle=False )

    #currentFrameHUD( toggle=False )
