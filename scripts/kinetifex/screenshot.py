

import pymel.core as pm
from pymel.core import Path, mel

import maya.OpenMaya as om
import maya.OpenMayaUI as omUI


JPG = 8
TGA = 19


def render( camera='persp', width=128, height=128, bgc=[0,0,0], name=pm.sceneName().namebase, lights=0 ):

    sel_list = pm.ls(sl=1)

    pm.waitCursor(state=1)

    scene_name = pm.sceneName().namebase
    current_ws = pm.workspace.getName()
    current_frame = pm.currentTime()

    pm.workspace.open('default')

    image_dir = pm.workspace.getcwd()

    # --- ---

    hwr_globals = pm.PyNode('defaultHardwareRenderGlobals')
    hwr_globals.filename.set( scene_name )

    hwr_globals.extension.set( 1 )
    hwr_globals.imageFormat.set( TGA ) #8: JPG, 19: TGA

    hwr_globals.startFrame.set( current_frame )
    hwr_globals.endFrame.set( current_frame )
    hwr_globals.byFrame.set( 1 )

    hwr_globals.resolution.set( "name %s %s %s" % ( width, height,
                                                    float(width)/height ) )
    hwr_globals.alphaSource.set( 0 )
    hwr_globals.writeZDepth.set( 0 )

    hwr_globals.lightingMode.set( lights )
    hwr_globals.drawStyle.set( 3 )
    hwr_globals.texturing.set( 1 )
    hwr_globals.lineSmoothing.set( 0 )
    hwr_globals.fullImageResolution.set( 0 )
    hwr_globals.geometryMask.set( 0 )
    hwr_globals.displayShadows.set( 0 )

    hwr_globals.multiPassRendering.set( 0 )
    hwr_globals.antiAliasPolygons.set( 1 )
    hwr_globals.edgeSmoothing.set( 1 )
    hwr_globals.motionBlur.set( 0 )

    hwr_globals.grid.set( 0 )
    hwr_globals.emitterIcons.set( 0 )
    hwr_globals.lightIcons.set( 0 )
    hwr_globals.fieldIcons.set( 0 )
    hwr_globals.transformIcons.set( 0 )
    hwr_globals.backgroundColor.set( bgc )

    '''
    // --- ---

    string $renderCamera;

    if($camera == "new")
    {
        $tempCamera = `camera -centerOfInterest 5 -focalLength 35 -lensSqueezeRatio 1 -cameraScale 1 -horizontalFilmAperture 1.41732 -horizontalFilmOffset 0 -verticalFilmAperture 0.94488 -verticalFilmOffset 0 -filmFit Fill -overscan 1 -motionBlur 0 -shutterAngle 144 -nearClipPlane 0.01 -farClipPlane 1000 -orthographic 0 -orthographicWidth 30 -name "tempCamera"`;
        xform -ws -t 4 2.7 6.7 -ro -12 32 0 $tempCamera[0];
        viewSet -fit -ff 1 $tempCamera[0];
        lookThroughModelPanelClipped $tempCamera[0] modelPanel4 0.001 10000;

        $renderCamera = $tempCamera[1];
    }
    else
        $renderCamera = ($camera + "Shape");

    // --- ---

    glRenderWin();
//    print("//RENDER: " + $renderCamera + " //\n");
    glRenderEditor -e -lookThru $renderCamera hardwareRenderView;
    '''

    mel.glRenderWin()
    pm.glRender( e=1, flipbookCallback='kx_renderCleanup' )
    mel.glRender( '-renderSequence', 'hardwareRenderView' )

    pm.select( sel_list )
    pm.workspace.open( current_ws )

    pm.waitCursor( state=False )



__cmd = """
global proc kx_renderCleanup( string $image, int $fs, int $fe,
int $fi, int $rate, string $path, string $filename )
{
python("kinetifex.screenshot._renderCleanup( '"+$path+"','"+$filename+"' )");
}
"""
mel.eval( __cmd )


def _renderCleanup( path, filename ):

    pm.window( 'glRenderWindow', e=1, vis=0 )

    f1 = filename.replace('@', str(int(pm.currentTime())) )

    f2 = filename.replace('@.', '' )

    p1 = Path(path) / f1
    p2 = Path(path) / f2

    if not p2.exists():
        p1.rename( p2 )
    else:
        print 'File exists:', p2

    #os.rename


    '''
    global string $gCurrentWorkspace;

    waitCursor -state on;

    workspace -o $gCurrentWorkspace;

    $camera = `glRenderEditor -q -vcn hardwareRenderView`;
    if( startsWith($camera, "tempCamera") )
        delete `pickWalk -d up $camera`;

    window -e -vis 0 glRenderWindow;

    print("// Results: " + $path + $filename + " //\n");

    waitCursor -state off;
    '''

import Image


def render2():

    thumb_size = 200

    img = om.MImage()

    port_view = omUI.M3dView.active3dView()

    port_w, port_h = port_view.portWidth(), port_view.portHeight()

    cam_path  = om.MDagPath()
    port_view.getCamera( cam_path )

    cam_fn = om.MFnCamera( cam_path )

    #fov_horz = om.MScriptUtil(1.0).asDoublePtr()
    #fov_vert = om.MScriptUtil(1.0).asDoublePtr()
    #cam_fn.getPortFieldOfView(200,200, fov_horz, fov_vert)

    cam_fn.setVerticalFieldOfView( .5 )

    '''
    if port_w <= port_h:
        view_w = thumb_size
        view_h = thumb_size * port_h / port_w
        view_x = 0
        view_y = ( view_h - thumb_size )# / 2
    else:
        view_w = thumb_size * port_w / port_h
        view_h = thumb_size
        view_x = ( view_w - thumb_size )# / 2
        view_y = 0
        '''

    port_view.pushViewport( 0, 0, thumb_size, thumb_size )
    port_view.refresh( False, False )
    port_view.readColorBuffer( img, True )

    port_view.popViewport()

    #img.resize(200,200,False)
    #px_ptr = img.pixels()
    #img.setPixels( px_ptr, 200, 200 )

    img.setRGBA

    img.writeToFile(r'C:\test.TGA', 'tga' )


def setPort():
    port_view = omUI.M3dView.active3dView()
    port_view.pushViewport( 0, 0, 200, 200 )
    port_view.refresh( False, False )

