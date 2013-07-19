"""
Module for building and working with Poses.
"""


import thread, random, re, pprint, sets
import pickle

import maya.cmds as mc
import pymel.core as pm
from pymel.core import mel, Path
from pymel.core.uitypes import OptionMenu
#from pymelX import register_runtime
from impress import register

from config import RUNTIME_SUITE, PREF_POSES
from pickle import TRUE


global selectedPose


def __getValueStr(self):
    value = self.getValue()
    return str(value)

OptionMenu.getValueStr = __getValueStr


class StoredAttr( object ):

    def __init__(self, attr, value):
        self.__name__ = self._attr = attr
        self._value = value

    def __repr__(self):
        return "%s('%s', %s, %s)" % ( self.__class__.__name__, self.__name__, self._value )

    @property
    def attr(self):
        return pm.Attribute( self._attr )

    @property
    def value(self):
        return self._value

    @property
    def node(self):
        return pm.PyNode( self._attr.split('.')[0] )


class Pose( object ):
    """
    Class for storing, manipulating and apply poses.
    Use 'capture' or 'captureSwap' methods for storing a pose on selected objects.
    """

    _transList = ( 'translateX', 'translateY', 'translateZ',
                   'rotateX', 'rotateY', 'rotateZ',
                   'scaleX', 'scaleY', 'scaleZ',
                   'footRoll'
                   )
    _mirrAttrs = { u'XY': (u'translateZ', u'rotateX', u'rotateY'),
                   u'YZ': (u'translateX', u'rotateY', u'rotateZ'),
                   u'XZ': (u'translateY', u'rotateX', u'rotateZ')
                   }
    leftSuffix = '_l'
    rightSuffix = '_r'
    leftPrefix = 'L'
    rightPrefix = 'R'

    def __init__( self, name=None, stored = [] ):
        self._stored = stored

        if name:
            self.__name__ = name
        else:
            self.__name__ = 'pose'+str( int( random.uniform( 100, 999 ) ) )


    def __repr__(self):
        return "%s('%s', %s)" % ( self.__class__.__name__, self.__name__, str(self._stored) )


    def _getAttr(self, obj):
        l = []
        for attr in map( pm.Attribute, obj.listAttr( keyable=True ) ):
            l = attr.get()
        return l


    def capture(self):
        """
        stores attributes of selected controls into list _stored resulting dict looks like:
            { object:{attribute1: value, attribute2: value}, object2...

            [ ( attribute1, value, node ), ( attribute1, value, node ) ]
        """
        pm.select(pm.ls(selection=True), replace=True)

        self._stored = []
        for obj in pm.ls(selection=True):
            for attr in map( pm.Attribute, obj.listAttr(keyable=True, unlocked=True) ):
                self._stored.append( ( str(attr), attr.get() ) )

        # -- push all non-transform attributes to the top --
        for t in self._stored:
            attr, v = t
            if attr.split('.')[-1] not in self._transList:
                self._stored.insert( 0, self._stored.pop( self._stored.index(t) ) )


    def mirror( self, defaultAxis='YZ' ):
        prefix = [self.leftPrefix, self.rightPrefix]
        suffix = [self.leftSuffix, self.rightSuffix]

        pm.select(pm.ls(selection=True), replace=True)

        stored = {}
        for obj in pm.ls(selection=True, type="transform"):

            if obj.hasAttr("mirrorAxis"):
                axis = ('XY','YZ','XZ')[ obj.mirrorAxis.get() ]
            else:
                axis = defaultAxis

            for attr in map( pm.Attribute, obj.listAttr( keyable=True, unlocked=True ) ):
                if attr.split('.')[-1] in self._transList:
                    split = attr.split(':')
                    if len( split ) > 1:
                        a = split[1]
                    else:
                        a = attr

                    has_side = False

                    if a.startswith( prefix[0] ) or  a.startswith( prefix[1] ):
                        if a.startswith( prefix[1] ):
                            prefix.reverse()
                        v = pm.Attribute( attr.replace( prefix[0], prefix[1] ) ).get()
                        has_side = TRUE

                    elif obj.endswith( suffix[0] ) or obj.endswith( suffix[1] ):
                        if obj.endswith( suffix[1] ):
                            suffix.reverse()
                        v = pm.Attribute( attr.replace( suffix[0], suffix[1] ) ).get()
                        has_side = TRUE
                    else:
                        v = attr.get()

                    if obj.type() == 'joint':
                        if has_side:
                            stored[attr] = v
                        elif attr.split('.')[-1] in self._mirrAttrs['XY']:
                            stored[attr] = -v
                        else:
                            stored[attr] = v

                    elif attr.split('.')[-1] in self._mirrAttrs[axis]:
                        stored[attr] = -v
                    else:
                        stored[attr] = v

        # -- apply --
        for (attr, v) in stored.iteritems():
            pm.setAttr( attr, v )


    def apply( self, alterNamespace=False, namespace='' ):
        "apply the stored pose to the current scene"

        for t in self._stored:
            attr, v = t

            if alterNamespace:
                split = attr.split(':')
                if len( split ) > 1:
                    attr = split[1]
                attr = '%s:%s' % (namespace, attr)

            try:
                pm.Attribute(attr).set(v)
            except pm.MayaAttributeError, msg:
                mel.warning( str(msg) )


    def applyToSelected( self ):
        "apply the stored pose to the current scene"

        sel_list = pm.ls(sl=1, type="transform")

        stored_list = [ StoredAttr(*s) for s in self._stored]

        stored_nodes = []

        for stored in stored_list:
            if stored.node not in stored_nodes:
                stored_nodes.append(stored.node)

        mapped_nodes = dict( zip( stored_nodes, sel_list ) )

        for stored in stored_list:
            if stored.node in mapped_nodes.keys():
                attr = '.'.join( [ mapped_nodes[stored.node].nodeName(), stored.attr.split('.')[1] ] )

            try:
                pm.Attribute(attr).set(stored.value)
            except pm.MayaAttributeError, msg:
                mel.warning( str(msg) )


class PoseManagerWindow( object ):
    """Instanciate PoseManagerWindow objects with name as the instance name."""

    def __init__(self, name, title='Pose Rack' ):
        self.__name__ = name
        self._title = title

        self.__instance = __name__ + '.' + self.__name__

        # -- Default Pose Group. Adding whitespace to distinguish and widen dropdown.
        self._default = 'Default' + ''.join([' ' for x in range(90)])

        self._poseGroups = { self._default : {} }
        self._loadPrefs()
        self.namespace = 'Default'


    def _threadSavePrefs( self, pretty=False ):
        pose_file = open( PREF_POSES, 'wb')
        pickle.dump( self._poseGroups, pose_file )
        pose_file.close()


    def _savePrefs( self ):
        thread.start_new_thread(self._threadSavePrefs, (False,) )
        #self._threadSavePrefs()


    def _loadPrefs( self ):
        if Path(PREF_POSES).isfile():
            pose_file = open( PREF_POSES, 'rb')
            self._poseGroups = pickle.load( pose_file )
            pose_file.close()

        if not self._poseGroups.has_key( self._default ):
            self._poseGroups.update(  { self._default : {} } )


    def _sortedGroupList( self ):
        """simple reodering of list to set 'Default' to the top"""
        li = self._poseGroups.keys()

        li.sort()
        li.insert( 0, li.pop( li.index( self._default ) ) )
        return li


    def _updateGroupList( self ):
        try:
            pm.deleteUI( self.groupOM )
            pm.deleteUI( self.groupMenu, menuItem=True )
        except:
            pass

        pm.setParent( self.optionMenuCol )
        self.groupOM = OptionMenu( changeCommand=lambda *args: self._updatePoseList() )

        for i in self._sortedGroupList():
            pm.setParent( self.optionMenuCol )
            pm.menuItem( label=i )

        pm.setParent( self.radMenu, menu=True )
        self.groupMenu = pm.menuItem( label='Move Pose To: ', subMenu=True)
        for i in self._sortedGroupList():
            pm.menuItem( label=i.rstrip(), command='%s.regroupPose("%s")' % (__name__,i) )


    def _newGroup( self ):
        result = pm.promptDialog( title='Create New Group',
                               message='Group Name:',
                               button=['OK', 'Cancel'],
                               defaultButton='OK',
                               cancelButton='Cancel',
                               dismissString='Cancel'
                               )

        if result == 'OK':
            groupName = re.sub('\W', '_', pm.promptDialog(query=True, text=True) )
            self._poseGroups[ str(groupName) ] = {}
            self._updateGroupList()
            OptionMenu( self.groupOM, edit=True, select=self._sortedGroupList().index(groupName) + 1 )
            self._updatePoseList()
            self._savePrefs()


    def _renameGroup( self ):
        selPose = self.poseListTSL.getSelectItem()

        groupName = self.groupOM.getValueStr()
        group = self._poseGroups[ groupName ]

        assert (groupName != self._default), 'Cannot rename \'%s\' group' % self._default.rstrip()

        #if groupname == self._default:
            #mel.warning( 'cannot rename \'%s\' group' % self._default.rstrip() )
        #else:
        result = pm.promptDialog( title='Rename Pose',
                               message='Pose Name:',
                               text=groupName,
                               button=['OK', 'Cancel'],
                               defaultButton='OK',
                               cancelButton='Cancel',
                               dismissString='Cancel')
        if result == 'OK':
            newGroupName = str( re.sub('\W', '_', pm.promptDialog(query=True, text=True) ) )

            self._poseGroups.pop( groupName )
            self._poseGroups[newGroupName] = group

            self._updateGroupList()
            OptionMenu( self.groupOM, edit=True, select=self._sortedGroupList().index(newGroupName) + 1 )
            self._updatePoseList()
            if selPose is not None:
                self.poseListTSL.setSelectItem( selPose )
            self._savePrefs()


    def _deleteGroup( self ):
        groupName = self.groupOM.getValueStr()

        assert (groupName != self._default), 'Cannot delete \'%s\' group' % self._default.rstrip()

        #if groupName == self._default:
            #mel.warning( 'Cannot delete \'%s\' group' % self._default.rstrip() )
        #else:
        result = pm.confirmDialog( title='Confirm Delete Group',
                                message='Delete the group "%s" and all of its poses?' % groupName,
                                button=['Delete','No'],
                                defaultButton='No',
                                cancelButton='No',
                                dismissString='No' )
        if result == 'Delete':
            self._poseGroups.pop( groupName )
            self._updateGroupList()
            self._updatePoseList()
            self._savePrefs()


    def _clearGroup( self ):
        group = self.groupOM.getValueStr()

        result = pm.confirmDialog( title='Confirm Clear Group',
                                message='Clear all poses found in the group "%s"?' % group.rstrip(),
                                button=['Clear','No'],
                                defaultButton='No',
                                cancelButton='No',
                                dismissString='No' )
        if result == 'Clear':
            self._poseGroups[ group ].clear()
            self._updatePoseList()
            self._savePrefs()


    def _updatePoseList( self ):
        li = self._poseGroups[ self.groupOM.getValueStr() ].keys()
        li.sort()

        self.poseListTSL.removeAll( True )
        self.poseListTSL.extend( li )

        if self.poseListTSL.getNumberOfItems() > 0:
            self.poseListTSL.setSelectIndexedItem(1)


    def _applyPose( self ):
        applySelectedPose()
        #executeFromMEL( '%s.applySelectedPose()' % __name__ )


    def _import( self, *args ):

        path = pm.fileDialog2( dialogStyle=2,
                               fileMode=1,
                               caption='Choose Pose File',
                               okCaption='Import',
                               selectFileFilter='Poses',
                               fileFilter='Poses (*.pose *.group)'
                               )

        if path is None:
            return
        else:
            path = path[0]

        path = Path(path)
        if path.isfile():
            data = ''.join(file( path ).read().splitlines())

            if len( data ) is not 0:
                data = eval( data )

                name = path.namebase
                ext = path.ext[1:]

                if ext == 'group':
                    print 'Group: "%s"' % name
                    if self._poseGroups.has_key( name ):

                        result = pm.confirmDialog( title='Import Group',
                                                message='Group "%s" already exists. Overwrite existing poses?' % name,
                                                button=['Overwrite', 'Cancel'],
                                                defaultButton='Overwrite',
                                                cancelButton='Cancel',
                                                dismissString='Cancel' )
                        if result == 'Overwrite':
                            self._poseGroups[ name ].update( data )
                    else:
                        self._poseGroups[ name ] = data

                    self._updateGroupList()
                    #setSelect for optionMenu broken with pymel 0.6+
                    OptionMenu( self.groupOM, edit=True, select=self._sortedGroupList().index( name ) + 1 )
                    self._updatePoseList()

                elif ext == 'pose':
                    print 'Pose: "%s"' % name

                    currentGroup = self._poseGroups[ self.groupOM.getValueStr() ]
                    if currentGroup.has_key( name ):
                        result = pm.confirmDialog( title='Import Pose',
                                                message='Overwrite existing pose "%s"?' % name,
                                                button=['Overwrite', 'Cancel'],
                                                defaultButton='Overwrite',
                                                cancelButton='Cancel',
                                                dismissString='Cancel' )
                        if result == 'Overwrite':
                            currentGroup[ name ] = data
                    else:
                        currentGroup[ name ] = data

                    self._updatePoseList()
                    self.poseListTSL.setSelectItem( name )

                self._savePrefs()


    def _exportPose( self, *args ):

        path = pm.fileDialog2( dialogStyle=2,
                               fileMode=0,
                               caption='Choose Pose File',
                               okCaption='Export',
                               selectFileFilter='Pose',
                               fileFilter='Pose (*.pose)'
                               )

        if path is None:
            return
        else:
            path = path[0]

        group = self._poseGroups[ self.groupOM.getValueStr() ]

        #try:
        poseName = self.poseListTSL.getSelectItem()[0]

        f = open( path, 'w' )
        pp = pprint.PrettyPrinter( stream=f, indent=1 )
        #output = ( poseName, 'pose', group[poseName] )
        pp.pprint( group[poseName] )
        f.close()

        print "Exported Pose: '%s' to: %s" % ( group[poseName], path )

        #except:
        #    mel.warning('No pose selected for export.')


    def _exportGroup( self, *args ):

        path = pm.fileDialog2( dialogStyle=2,
                               fileMode=0,
                               caption='Choose Group File',
                               okCaption='Export',
                               selectFileFilter='Group',
                               fileFilter='Group (*.group)'
                               )

        if path is None:
            return
        else:
            path = path[0]

        groupName = self.groupOM.getValueStr()
        group = self._poseGroups[ groupName ]

        f = open( path, 'w' )
        pp = pprint.PrettyPrinter( stream=f, indent=1 )
        #output = ( groupName, 'group', group )
        pp.pprint( group )
        f.close()

        print "Exported Group: '%s' to: %s" % ( groupName, path )


    def _newPose( self ):
        assert len( pm.ls( selection=True, type=("transform","objectSet") ) ), 'Select objects to capture pose of'

        #if len( ls( selection=True ) ) == 0:
            #mel.warning('Select objects to capture pose of')
        #else:

        result = pm.promptDialog( title='Create New Pose',
                               message='Pose Name:',
                               button=['OK', 'Cancel'],
                               defaultButton='OK',
                               cancelButton='Cancel',
                               dismissString='Cancel')
        if result == 'OK':
            poseName = re.sub('\W', '_', pm.promptDialog(query=True, text=True) )
            pose = Pose( poseName, [] ) #empty braces needed due to weirdness with python
            pose.capture()

            _g = self._poseGroups[ self.groupOM.getValueStr() ]
            _g[ poseName ] = pose
            self._poseGroups[ self.groupOM.getValueStr() ] = _g


            self._updatePoseList()
            self.poseListTSL.setSelectItem( poseName )

            self._savePrefs()


    def _renamePose( self ):
        group = self._poseGroups[ self.groupOM.getValueStr() ]

        try:
            poseName = self.poseListTSL.getSelectItem()[0]
            pose = group[poseName]
        except:
            assert False, 'No pose selected for rename.'

        result = pm.promptDialog( title='Rename Pose',
                               message='Pose Name:',
                               text=poseName,
                               button=['OK', 'Cancel'],
                               defaultButton='OK',
                               cancelButton='Cancel',
                               dismissString='Cancel')
        if result == 'OK':
            newPoseName = re.sub('\W', '_', pm.promptDialog(query=True, text=True) )

            if not group.has_key( newPoseName ):
                group.pop( poseName )
                group[ newPoseName ] = pose
                self._poseGroups[ self.groupOM.getValueStr() ] = group

                self._updatePoseList()
                self._savePrefs()

                self.poseListTSL.setSelectItem(newPoseName)
            else:
                assert False, 'Pose named "%s" already exists in group.' % newPoseName

        else:
            pass #mel.warning('Process Canceled.')


    def _deletePose( self ):
        group = self._poseGroups[ self.groupOM.getValueStr() ]

        try:
            poseName = self.poseListTSL.getSelectItem()[0]
        except:
            assert False, 'No pose selected for delete.'

        result = pm.confirmDialog( title='Confirm Delete Pose',
                                message='Are you sure you want to delete the pose "%s"?' % poseName,
                                button=['Delete','No'],
                                defaultButton='No',
                                cancelButton='No',
                                dismissString='No' )
        if result == 'Delete':
            group.pop( poseName )
            ##group[ 'empty' ] = None
            self._poseGroups[ self.groupOM.getValueStr() ] = group

            self._updatePoseList()
            self._savePrefs()


    def _setGlobalPose( self, *args, **kwargs ):
        global selectedPose
        groupName = self.groupOM.getValueStr()
        poseName = self.poseListTSL.getSelectItem()[0]
        selectedPose = self._poseGroups[ groupName ][ poseName ]


    def _setSelectedNS( self, ns ):
        self.namespace = ns

        pm.textField( self.namespaceTF, edit=True, text=self.namespace, font='boldLabelFont' )


    def _updateNamespaceList( self ):
        self.refNS = []
        self.charNS = []

        refFiles = mc.file( query=True, reference=True )

        for ref in refFiles:
            self.refNS.extend( mc.file( ref, query=True, renamingPrefixList=True ) )

        self.refNS = list( sets.Set(self.refNS) )

        for ns in self.refNS:
            if pm.objExists( ns+':characterRoot' ):
                self.charNS.append( self.refNS.pop( self.refNS.index(ns) ) )

        self.refNS.sort()
        self.charNS.sort()

        if self.namespace not in self.refNS and self.namespace not in self.charNS and self.namespace != '':
            self._setSelectedNS('Default')


    def _updateNamespacePopupList( self ):
        self._updateNamespaceList()

        pm.menu( self.namespacePM, edit=True, deleteAllItems=True )
        pm.setParent( self.namespacePM, menu=True )

        pm.radioMenuItemCollection()

        rbState = self.namespace == 'Default'
        pm.menuItem( 'Default', radioButton=rbState, command=pm.Callback( self._setSelectedNS, 'Default' ) )

        rbState = self.namespace == ''
        pm.menuItem( 'None', radioButton=rbState, command=pm.Callback( self._setSelectedNS, '' ) )

        pm.menuItem( divider=True )
        for ns in self.charNS:
            rbState = self.namespace == ns
            pm.menuItem( ns, radioButton=rbState, command=pm.Callback( self._setSelectedNS, ns ) )

        pm.menuItem( divider=True )
        for ns in self.refNS:
            rbState = self.namespace == ns
            pm.menuItem( ns, radioButton=rbState, command=pm.Callback( self._setSelectedNS, ns ) )


    def show( self ):
        try:
            pm.deleteUI( self.__name__ )
        except:
            pass

        self.win = pm.window( self.__name__ )
        self.win.setTitle( self._title )
        self.win.setWidthHeight( (150,300) )

        pm.menuBarLayout()
        pm.menu( label='File' )

        pm.menuItem( label='Import...', command=self._import )
        pm.menuItem( label='Export Pose...', command=self._exportPose )
        pm.menuItem( label='Export Group...', command=self._exportGroup )

        pm.menu( label='Edit' )
        pm.menuItem( label='New Pose', command=lambda *args: self._newPose() )
        pm.menuItem( label='New Group', command=lambda *args: self._newGroup() )
        pm.menuItem(divider=True)
        pm.menuItem( label='Rename Selected Pose', command=lambda *args: self._renamePose() )
        pm.menuItem( label='Delete Selected Pose', command=lambda *args: self._deletePose() )
        pm.menuItem(divider=True)
        pm.menuItem( label='Rename Current Group', command=lambda *args: self._renameGroup() )
        pm.menuItem( label='Delete Current Group', command=lambda *args: self._deleteGroup() )
        pm.menuItem( label='Clear Current Group',  command=lambda *args: self._clearGroup() )

        pm.menu( label='Help', helpMenu=True )
        pm.menuItem( label='About...' )

        self.mainForm = pm.formLayout( numberOfDivisions=100 )

        self.namespaceCol = pm.rowColumnLayout( numberOfColumns=2,
                                             columnAttach=[(1,"both",0),(2,"both",0)],
                                             columnAlign=[(2,"right"),],
                                             columnWidth=[(1,30),(2,125)]
                                             )

        self.namespacePM = pm.popupMenu( button=1, parent=self.namespaceCol, postMenuCommand=pm.Callback( self._updateNamespacePopupList ) )

        pm.symbolButton( image='pickMenuIcon.xpm' )
        self.namespaceTF = pm.textField( editable=False )

        pm.setParent( self.mainForm )
        self.optionMenuCol = pm.columnLayout( adjustableColumn=True, rowSpacing=0, columnAttach=( 'both', 0 ), columnAlign='right' )

        pm.setParent( self.mainForm )
        self.poseListTSL = pm.textScrollList( allowMultiSelection=False,
                                           doubleClickCommand=pm.Callback( self._applyPose ),
                                           selectCommand=pm.Callback( self._setGlobalPose ),
                                           deleteKeyCommand=pm.Callback( self._deletePose )
                                           )
        self.radMenu = pm.popupMenu( markingMenu=True )
        pm.menuItem( label='New Pose...',
                  radialPosition='N',
                  command=lambda *args: self._newPose()
                  )
        pm.menuItem( label='Apply',
                  radialPosition='W',
                  command=lambda *args: self._applyPose()
                  )
        pm.menuItem( label='Rename Pose...',
                  radialPosition='S',
                  command=lambda *args: self._renamePose()
                  )
        pm.menuItem( label='Delete Pose',
                  radialPosition='SE',
                  command=lambda *args: self._deletePose()
                  )
        pm.menuItem( label='New Group', command=lambda *args: self._newGroup() )
        pm.menuItem( divider=True )
        pm.menuItem( label='Rename Current Group', command=lambda *args: self._renameGroup() )
        pm.menuItem( label='Delete Current Group', command=lambda *args: self._deleteGroup() )
        pm.menuItem( label='Clear Current Group', command=lambda *args: self._clearGroup() )
        pm.menuItem( divider=True )

        self._updateGroupList()
        self._updatePoseList()
        self._updateNamespaceList()

        self.mainForm.attachForm( self.optionMenuCol, 'top', 4 )
        self.mainForm.attachForm( self.optionMenuCol, 'left', 2 )
        self.mainForm.attachForm( self.optionMenuCol, 'right', 2 )
        self.mainForm.attachNone( self.optionMenuCol, 'bottom' )

        self.mainForm.attachControl( self.poseListTSL, 'top', 4, self.optionMenuCol)
        self.mainForm.attachForm( self.poseListTSL, 'left', 2 )
        self.mainForm.attachForm( self.poseListTSL, 'right', 2 )
        self.mainForm.attachControl( self.poseListTSL, 'bottom', 4, self.namespaceCol )

        self.mainForm.attachNone( self.namespaceCol, 'top' )
        self.mainForm.attachForm( self.namespaceCol, 'left', 2 )
        self.mainForm.attachForm( self.namespaceCol, 'right', 2 )
        self.mainForm.attachForm( self.namespaceCol, 'bottom', 4 )

        self.win.show()

        pm.scriptJob( replacePrevious=1, parent=self.__name__, event=['SceneOpened', pm.Callback(self._updateNamespaceList) ] )


    def delete( self ):
        self.win.delete()


clipboardPose = Pose( 'clipboardPose' )
selectedPose  = Pose( 'selectedPose' )


@register.runtime
def copyClipboardPose():
    clipboardPose.capture()

@register.runtime
def applyClipboardPose():
    clipboardPose.apply()

@register.runtime
def applyClipboardPoseToSelected():
    clipboardPose.applyToSelected()

@register.runtime
def mirrorClipboardPose():
    clipboardPose.mirror()


def applySelectedPose():

    alterNamespace = True
    if poseMgrWin.namespace == 'Default':
        alterNamespace = False

    selectedPose.apply( alterNamespace=alterNamespace, namespace=poseMgrWin.namespace )


def regroupPose( newGroup ):
    "Move a group's pose"

    poseName = selectedPose.__name__

    print 'regroup', poseName, 'to', newGroup

    group = poseMgrWin._poseGroups[ poseMgrWin.groupOM.getValueStr() ]
    pose = group.pop(poseName)
    poseMgrWin._poseGroups[ poseMgrWin.groupOM.getValueStr() ] = group

    group = poseMgrWin._poseGroups[ newGroup ]
    group[poseName] = pose
    poseMgrWin._poseGroups[ newGroup ] = group

    poseMgrWin._updatePoseList()
    poseMgrWin._savePrefs()


@register.runtime
def openPoseManagerWindow():
    global poseMgrWin

    poseMgrWin = PoseManagerWindow( 'pm' )
    poseMgrWin.show()