

from __future__ import with_statement
import pymel.core as pm
from impress.ui import commandMenuItem
import kinetifex as kx

MENU_LABEL = pm.getMelGlobal( 'string', 'KINETIFEX_MENU_TITLE' )
MAYA_WINDOW = pm.getMelGlobal( 'string', 'gMainWindow' )

if MENU_LABEL == '':
    MENU_LABEL = 'Kinetifex'


scene_menu = None


def show( reset=False ):

    global scene_menu

    if pm.about( batch=True ):
        print 'menu not available in batch mode.'
        return
    else:
        # get things ready for building the menu

        menu_name = MENU_LABEL.replace( ' ', '' )

        if pm.menu( menu_name, exists=True ):
            if reset:
                pm.deleteUI( menu_name )
            else:
                main_menu = pm.menu( menu_name, edit=True )
                return main_menu

        pm.setParent( MAYA_WINDOW )

        if not pm.menu( menu_name, exists=True ):
            main_menu = pm.menu( menu_name, tearOff=True, familyImage='burst_family.xpm' )

        # build the menu
        with  main_menu:

            with pm.subMenuItem( 'Display', aob=True, tearOff=True ):
                commandMenuItem( kx.display.jointCountHUD,
                          checkBox=pm.optionVar.get( 'jointCountHUDVis', False ) ),
                '''
                commandMenuItem(kx.display.particleCountHUD,
                          checkBox=pm.optionVar.get('particleCountHUDVis', False)),
                commandMenuItem(kx.display.transformCountHUD,
                          checkBox=pm.optionVar.get('transformCountHUDVis', False)),
                commandMenuItem(kx.display.currentFrameHUD,
                          checkBox=pm.optionVar.get('currentFrameHUDVis', False)),
                '''
                commandMenuItem( kx.display.currentTimeHUD,
                          checkBox=pm.optionVar.get( 'currentTimeHUDVis', False ) ),

                pm.menuItem( divider=True ),
                # commandMenuItem(kx.display.cycleBackgroundColors),
                commandMenuItem( kx.display.cycleGridDisplay ),

                pm.menuItem( divider=True ),
                commandMenuItem( kx.display.togglePlaybackSpeed ),
                commandMenuItem( kx.display.togglePlaybackSnap ),

                pm.menuItem( divider=True ),
                commandMenuItem( kx.display.toggleIsolateSelected ),
                commandMenuItem( kx.display.toggleXRay ),
                commandMenuItem( kx.display.toggleWireframeOnShaded ),

                pm.menuItem( divider=True ),
                commandMenuItem( kx.display.closeWindows ),


            with pm.subMenuItem( 'Modify', tearOff=True ) as sub_modify:
                commandMenuItem( kx.modify.cycleMoveMode ),
                commandMenuItem( kx.modify.cycleRotateMode ),
                pm.menuItem( divider=True ),
                commandMenuItem( kx.modify.unfreezeTranslation )

            pm.menuItem( divider=True )

            with pm.subMenuItem( 'Animation', tearOff=True ) as anim_menu:

                with pm.subMenuItem( 'Poses', tearOff=True ):
                    commandMenuItem( kx.poses.copyClipboardPose, label='Capture Pose' ),
                    commandMenuItem( kx.poses.applyClipboardPose, label='Apply Pose' ),
                    commandMenuItem( kx.poses.applyClipboardPoseToSelected, label='Apply Pose To Selected' ),
                    commandMenuItem( kx.poses.mirrorClipboardPose, label='Mirror Pose' ),
                    pm.menuItem( divider=True ),
                    commandMenuItem( kx.poses.openPoseManagerWindow, label='Pose Manager Window...' ),

                    pm.menuItem( divider=True )

                with pm.subMenuItem( 'Curves', tearOff=True ):
                    commandMenuItem( kx.animation.smoothTangentIn ),
                    commandMenuItem( kx.animation.smoothTangentOut ),

                    pm.menuItem( divider=True ),
                    commandMenuItem( kx.animation.flipCurve ),
                    commandMenuItem( kx.animation.mirrorCurve ),
                    commandMenuItem( kx.animation.reverseCurve ),
                    commandMenuItem( kx.animation.general.loopCurveFirst ),
                    commandMenuItem( kx.animation.general.loopCurveLast ),

                    pm.menuItem( divider=True ),
                    commandMenuItem( kx.animation.offsetKeyframesUp360 ),
                    commandMenuItem( kx.animation.offsetKeyframesDown360 ),

                    pm.menuItem( divider=True ),
                    commandMenuItem( kx.animation.toggleInfinityCycle ),

                    pm.menuItem( divider=True ),
                    commandMenuItem( kx.animation.keyTickSpecialOn ),
                    commandMenuItem( kx.animation.keyTickSpecialOff )


                with pm.subMenuItem( 'Reset IK', tearOff=True ):
                    commandMenuItem( kx.animation.resetIk, ( True, False ), label='T',
                                annotation='Reset translation of selected IK control(s)' ),
                    commandMenuItem( kx.animation.resetIk, ( False, True ), label='R',
                                annotation='Reset rotation of selected IK control(s)' ),
                    commandMenuItem( kx.animation.resetIk, ( True, True ), label='T/R',
                                annotation='Reset translation and rotation of selected IK control(s)' ),


                pm.menuItem( divider=True ),
                commandMenuItem( kx.animation.openSwitchParentWindow, label='Switch Parent...' ),
                pm.menuItem( divider=True ),
                commandMenuItem( kx.animation.performTransferAnimation ),



            with pm.subMenuItem( 'Modeling', aob=True, tearOff=True ):
                # commandMenuItem(kx.modeling.attachObject),
                commandMenuItem( kx.modeling.performRandomTransform ),
                # commandMenuItem(kx.modeling.targetCombine),
                commandMenuItem( kx.modeling.performReplaceShape ),
                pm.menuItem( divider=True ),
                commandMenuItem( kx.modeling.matchVertexNormals ),
                # pm.menuItem(divider=True),
                # commandMenuItem(kx.modeling.polyFaceProjection),
                pm.menuItem( divider=True ),
                commandMenuItem( kx.modeling.reverseOppositeGeometry ),
                commandMenuItem( kx.modeling.cleanGroupCombine ),


            with pm.subMenuItem( 'Rigging', aob=True, tearOff=True ):
                # commandMenuItem(kx.rigging.modifyAttributes),
                commandMenuItem( kx.rigging.performLockObjects ),
                commandMenuItem( kx.rigging.performUnlockObjects ),

                pm.menuItem( divider=True ),
                commandMenuItem( kx.rigging.performSprintJoint ),
                pm.menuItem( divider=True ),
                commandMenuItem( kx.rigging.performTweakJointOrient )

                pm.menuItem( divider=True ),
                commandMenuItem( kx.rigging.resetIkSetup ),
                commandMenuItem( kx.rigging.switchParentSetup )


                pm.menuItem( divider=True )

                with pm.subMenuItem( 'Curve Shapes', aob=False, tearOff=True ):
                    commandMenuItem( kx.rigging.createNurbsShape, ( '', 'cube', ), label='Cube' ),
                    commandMenuItem( kx.rigging.createNurbsShape, ( '', 'square', ), label='Square' ),
                    commandMenuItem( kx.rigging.createNurbsShape, ( '', 'sphere', ), label='Sphere' ),
                    commandMenuItem( kx.rigging.createNurbsShape, ( '', 'locator', ), label='Locator' ),
                    commandMenuItem( kx.rigging.createNurbsShape, ( '', 'pointer', ), label='Pointer' ),
                    commandMenuItem( kx.rigging.createNurbsShape, ( '', 'star', ), label='Star' ),
                    commandMenuItem( kx.rigging.createNurbsShape, ( '', 'axis', ), label='Axis' ),
                    commandMenuItem( kx.rigging.createNurbsShape, ( '', 'arrow', ), label='Arrow' ),
                    commandMenuItem( kx.rigging.createNurbsShape, ( '', 'triangle', ), label='Triangle' ),
                    commandMenuItem( kx.rigging.createNurbsShape, ( '', 'circle', ), label='Circle' ),

                commandMenuItem( kx.rigging.performScaleCurveShape )


            with pm.subMenuItem( 'Skinning', aob=True, tearOff=True ):
                commandMenuItem( kx.skinning.copyVertexWeights ),
                commandMenuItem( kx.skinning.pasteVertexWeights ),
                commandMenuItem( kx.skinning.getOverInfluencedVerts ),
                pm.menuItem( divider=True ),
                commandMenuItem( kx.skinning.matchSkinning )


            with pm.subMenuItem( 'Dynamics', tearOff=True ):
                commandMenuItem( kx.dynamics.loopDynamics ),
                commandMenuItem( kx.dynamics.restDynamics )


            with pm.subMenuItem( 'Materials', tearOff=True ):
                commandMenuItem( kx.materials.reloadTextures )

            pm.menuItem( divider=True )

            with pm.subMenuItem( 'Scene', tearOff=True ) as scene_menu:
                commandMenuItem( kx.scene.colorWireWindow ),
                pm.menuItem( divider=True ),
                commandMenuItem( kx.scene.orderedRename ),
                commandMenuItem( kx.scene.suffixName ),
                commandMenuItem( kx.scene.removeNamespaces ),
                pm.menuItem( divider=True ),
                commandMenuItem( kx.scene.setRelativeReferences ),
                pm.menuItem( divider=True ),
                commandMenuItem( kx.scene.exploreSceneFolder ),
                pm.menuItem( divider=True ),
                commandMenuItem( kx.scene.addSelectedToSet ),
                commandMenuItem( kx.scene.removeSelectedFromSet ),


        return main_menu

