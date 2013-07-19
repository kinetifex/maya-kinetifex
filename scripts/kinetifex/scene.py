"""
Functions for managing and organizing aspects of the Maya scene.
"""

import os
import sets
import maya.cmds as mc
import pymel.core as pm
from pymel.core import Path, mel
# from pymelX import register_runtime, exploreFolder, OptionVar
import impress.utils
from impress import register


from config import RUNTIME_SUITE


def setWritable( fileName ):
    fileName = Path( fileName )

    writable = True

    if fileName.exists() and fileName.isfile():
        if not fileName.access( os.W_OK ):
            writable = False

    return writable


def checkSave( fileName=None ):

    if fileName is None:
        fileName = pm.sceneName()
    else:
        fileName = Path( fileName )
        mc.file( rename=fileName )

    if not setWritable( fileName ):
        mel.warning( 'File "%s" is read-only. Could not save.' % fileName.basename() )

        return False


    mc.file( save=True )
    print '// Result: %s //' % fileName

    return True


@register.runtime
def exploreSceneFolder():
    """Opens current scene's folder in Explorer"""

    pathName = pm.sceneName().dirname()
    impress.utils.revealInFileManager( pathName )

@register.runtime
def orderedRename( objects=[], name=None, prompt=True ):
    """Renames selected objects in order of selection."""
    result = 'OK'

    if prompt:
        opt_name = 'orderedRename_name'

        result = pm.promptDialog( title='Ordered Rename',
                              message='Enter name:',
                              text=pm.optionVar.get( opt_name, 'object0' ),
                              button=( 'OK', 'Cancel' ),
                              defaultButton='OK',
                              cancelButton='Cancel',
                              dismissString='Cancel'
                              )
        if result == 'OK':
            name = pm.promptDialog( query=True, text=True )
            pm.optionVar[opt_name] = name

    if result == 'OK':
        if not prompt and name is None:
            assert False, r"'name' needs to be set when using 'prompt=False'"
        else:
            if len( objects ) is 0:
                objects = pm.ls( selection=True, type='transform' )

            i = 0
            for obj in objects:
                pm.rename( obj, name )
                i += 1

            print '// Results: %i objects renamed as "%s" //' % ( i, name )


def superRename( object, newName, force=False ):
    print 'object:', object
    result = pm.rename( object, newName )
    result = str( result )

    if result == newName:
        print '// Result:', result
    else:
        nsList = pm.namespaceInfo( listOnlyNamespaces=True )
        nodeList = pm.ls( '*' + newName )

        if force:
            if newName in nsList:
                nsName = newName + 'NS'

                try:
                    pm.namespace( add=nsName )
                except RuntimeError:
                    pass

                pm.namespace( force=True, moveNamespace=( newName, nsName ) )
                pm.namespace( removeNamespace=newName )

                mel.warning( 'Renamed namespace "%s" to "%s".' % ( newName, nsName ) )

            if newName in nodeList:
                for n in nodeList:
                    if n.type() == 'displayLayer':
                        pm.rename( n, n + 'L' )
                        mel.warning( 'SuperRename: Forced DisplayLayer "%s" to "%s".' % ( newName, n + 'L' ) )
                    else:
                        try:
                            print n.nextName().split( '|' )[-1]
                            r = pm.rename( n, n.nextName().split( '|' )[-1] )
                        except RuntimeError:
                            # pass
                            r = pm.rename( n, n + '100' )
                        except:
                            pass

                        mel.warning( 'SuperRename: Forced renamed "%s" to "%s".' % ( newName, r ) )

            # renamed conflicting nodes, try again
            superRename( result, newName, force=False )

        else:
            print '// Conflicts:'
            if newName in nsList:
                print '// (namespace)'.ljust( 10 ), newName
            if nodeList:
                for n in nodeList:
                    print '// (%s)'.ljust( 10 ) % n.type(), n
                    # print '- %s (%s)' % ( n, n.type() )

@register.runtime
def suffixName( objects=[], suffix=None, dag=True, prompt=True ):
    """Add a suffix to all hierarchy names."""
    result = 'OK'

    if prompt:
        opt_suffix = 'suffixNames_suffix'

        result = pm.promptDialog( title='Suffix Name',
                              message='Enter suffix:',
                              text=pm.optionVar.get( opt_suffix, '_suffix' ),
                              button=( 'OK', 'Cancel' ),
                              defaultButton='OK',
                              cancelButton='Cancel',
                              dismissString='Cancel'
                              )
        if result == 'OK':
            suffix = pm.promptDialog( query=True, text=True )
            pm.optionVar[opt_suffix] = suffix

    if result == 'OK':
        if not prompt and suffix is None:
            assert False, r"'suffix' needs to be set when using 'prompt=False'"
        else:
            if len( objects ) is 0:
                objects = pm.ls( selection=True, type='transform', dag=dag )
            else:
                objects = pm.ls( objects, type='transform', dag=dag )

            i = 0
            for obj in objects:
                pm.rename( obj, obj.split( '|' )[-1] + suffix )
                i += 1

            print '// Results: %i objects rename with suffix "%s" //' % ( i, suffix )


@register.runtime
def colorWireWindow():
    """Color the wireframe of objects."""
    userColors = []

    for i in range( 1, 9 ):
        userColors.append( pm.displayRGBColor( 'userDefined%i' % i, query=True ) )

    if pm.window( 'colorWireWindow', exists=True ):
        pm.deleteUI( 'colorWireWindow' )

    win = pm.window( 'colorWireWindow', title="Color", sizeable=False, resizeToFitChildren=True, toolbox=True )

    pm.columnLayout( adjustableColumn=True )
    pm.frameLayout( borderStyle="etchedOut", labelVisible=False, marginWidth=2, marginHeight=2 )

    pm.columnLayout( adjustableColumn=True, rowSpacing=2 )
    i = 1
    for userColor in userColors:
        pm.button( backgroundColor=userColor, command='color(userDefined=%i)' % i, label='' )
        i += 1

    pm.button( label='Default', command='color()' )

    win.show()

'''
@register.runtime
def setCameraClipPlanes( near=0.1, far=10000 ):
    for cam in pm.ls( type='camera' ):
        cam.setFarClipPlane( far )
        cam.setNearClipPlane( near )

    pm.PyNode( 'top' ).ty.set( far * 0.9 )
    pm.PyNode( 'front' ).tz.set( far * 0.9 )
    pm.PyNode( 'side' ).tx.set( far * 0.9 )

    mel.fitAllPanels( '-all' )

    print '// Result: All Camera Clip Planes set [ near=%f, far=%f ]' % ( near, far )
'''


def _iter_namespace( ns_list, level=0 ):

    count = 0

    for ns in ns_list:
        count += 1

        pm.namespace( set=':' )
        pm.namespace( set=ns )

        print '//    ' + '  ' * level + '- ' + ns

        if pm.namespaceInfo( lon=1 ):
            count += _iter_namespace( pm.namespaceInfo( lon=1 ), ( level + 1 ) )

        pm.namespace( set=':' )
        for obj in pm.ls( ns + ':*' ):
            obj.rename( obj.replace( ns + ':', '' ) )

        pm.namespace( rm=ns )

    return count


def removeNamespaces():
    """
    Strips and removes all possible namespaces from scene.
    """
    core_ns = sets.Set( ['UI', 'shared'] )

    pm.namespace( set=':' )
    root_ns = sets.Set( pm.namespaceInfo( lon=1 ) )
    ns_list = list( root_ns.difference( core_ns ) )

    print '// Clearning Namespaces:'
    count = _iter_namespace( ns_list )

    print '//', count, 'namespaces removed.'

def setRelativeReferences():
    """
    Changes unresolved paths of references to relative paths.
    """
    scene_path = pm.sceneName().parent

    for ref_node in pm.listReferences():
        rel_path = scene_path.relpathto( ref_node.path.realpath() )
        if ref_node.unresolvedPath() != rel_path:
            ref_node.load( rel_path )
            print "// set relative (%s)" % rel_path


def addToSet( object_list, set_name ):

    if not isinstance( object_list, tuple ) and not isinstance( object_list, list ):
        object_list = [object_list]

    if not pm.objExists( set_name ):
        pm.select( cl=1 )
        pm.sets( name=set_name )

    sel_set = pm.PyNode( set_name )

    sel_set.addMembers( object_list )

    print "# Set", set_name, "includes:", ", ".join( [o.nodeName() for o in object_list] )


def removeFromSet( object_list, set_name ):

    if not isinstance( object_list, tuple ) and not isinstance( object_list, list ):
        object_list = [object_list]

    sel_set = pm.PyNode( set_name )

    sel_set.removeMembers( object_list )

    print "# Removed from", set_name + ":", ", ".join( [o.nodeName() for o in object_list] )


@register.runtime
def addSelectedToSet():
    """
    Select objects and set to add to.
    """

    object_list = pm.ls( sl=1 )
    sel_set = pm.ls( sl=1, type='objectSet' )[0]
    object_list.pop( object_list.index( sel_set ) )

    sel_set.addMembers( object_list )

    print "# Set", sel_set.name(), "includes:", ", ".join( [o.nodeName() for o in object_list] )


@register.runtime
def removeSelectedFromSet():
    """
    Select objects and set to remove from.
    """

    object_list = pm.ls( sl=1 )
    sel_set = pm.ls( sl=1, type='objectSet' )[0]
    object_list.pop( object_list.index( sel_set ) )

    sel_set.removeMembers( object_list )

    print "# Set", sel_set.name(), "includes:", ", ".join( [o.nodeName() for o in object_list] )
