"""
Functions and windows for managing materials, their attributes, and texture paths.
"""


import pymel.core as pm
from pymel.core import mel, Path
#import pymelX as pmx
#from pymelX import register_runtime, OptionVar
from impress import register

from config import RUNTIME_SUITE


@register.runtime
def reloadTextures():
    """Reload all texture files."""
    mel.source("AEfileTemplate")
    for _file in pm.ls(type="file"):
        mel.AEfileTextureReloadCmd(_file.fileTextureName)

    print "# Textures reloaded."


def renameMaterials( options=False ):
    mel.kx_renameMaterials( int(options) )


def adjustMaterials( options=False ):
    mel.kx_adjustMaterials( int(options) )

'''
class TexturePathViewer:
    def __init__(self, name='texturePathViewer'):
        self.__name__ = name
        self.m_title = 'Texture Path Viewer'

        self._resizeCalls = 0

    class Option( OptionVar ):
        control = None


    def _buildFileList(self):
        nodeList = pm.ls( type='file' )
        dupList = []
        brokenList = []
        pathList = []

        for node in nodeList:
            p = Path( node._fileTextureName.get() )

            if p not in pathList:
                pathList.append(p)
            else:
                dupList.append(node)

            if not p.isfile():
                brokenList.append(p)

        print 'total:', len(nodeList)
        print 'duplicates:', len(dupList)
        print 'broken:', len(brokenList)


    def _buildControls(self):
        self.optSearch  = self.Option( 'texturePathViewer_searchString', '' )
        self.optReplace = self.Option( 'texturePathViewer_replaceString', '' )

        self.options = [ self.optSearch, self.optReplace ]
        pmx.setOptionVars( self.options )

        pm.rowLayout(numberOfColumns=2, adjustableColumn=1, columnWidth2=(1,60) )
        self.optSearch.control = pm.textFieldGrp( label='Search:',
                                               columnAttach2=[ 'left', 'both' ],
                                               columnOffset2=[2, 2],
                                               adjustableColumn=2,
                                               columnWidth2=[60, 1]
                                               )
        pm.setParent( self.mainHeader_col )

        self.optReplace.control = pmx.pathHistoryBrowser(label='Replace:',
                                                     columnAttach3=[ 'left', 'both', 'both'],
                                                     columnOffset3=[2, 2, 2],
                                                     adjustableColumn=2,
                                                     columnWidth3=[60, 1, 60],
                                                     buttonLabel='Browse..',
                                                     pathType='dir'
                                                     )


        pm.rowLayout( numberOfColumns=2, columnWidth2=(166,300),
                   columnAttach2=('right','left'),
                   columnOffset2=(1,1),
                   columnAlign2=('both','both')
                   )
        pm.button( label='Replace All', width=100, command=lambda *args: self._updateBodyControls() )
        pm.button( label='Replace Selected', width=100, command='print "replace selected"' )


    def _updateControls( self, forceDefaults=False ):
        pmx.setOptionVars( self.options, forceDefaults )

        pm.textFieldGrp( self.optSearch.control, edit=True, fileName=self.optSearch.get() )
        pm.textFieldButtonGrp( self.optReplace.control, edit=True, fileName=self.optReplace.get() )


    def _updateOptions(self):
        value = pm.textFieldGrp( self.optSearch.control, query=True, value=True )
        self.optSearch.set( value )
        value = pm.textFieldButtonGrp( self.optReplace.control, query=True, select=True )
        self.optReplace.set( value )


    def _buildBodyControls( self ):
        pm.text( self.bodyText, edit=True, visible=True, label='Building texture path list' )

        try:
            pm.deleteUI( self.bodyCol )
        except:
            pass

        pm.setParent( self.mainForm_col )
        self.bodyCol = pm.rowColumnLayout( numberOfColumns=3,
                                        columnAttach=[(1,"both",0),(2,"both",0),(3,"left",6)],
                                        visible=False
                                        )

        for node in pm.ls(type='file'):
            pm.button( label=node, align='left', command='select("%s", replace=True), mel.openAEWindow()' % node )

            pm.textField( text=node._fileTextureName.get() )
            pm.checkBox( label = '' )

        pm.text( self.bodyText, edit=True, visible=False )
        pm.rowColumnLayout( self.bodyCol, edit=True, visible=True )

        self._resizeWindow()


    def _updateBodyControls(self):
        self._buildBodyControls()


    def _resizeWindow(self):
        self._resizeCalls += 1

        if self._resizeCalls > 3:
            cw1 = 150
            cw3 = 50
            width = pm.scrollLayout( self.mainForm_body, query=True, width=True ) - cw3
            cw1 = width*.4 < cw1 and width*.4 or cw1
            cw2 = width - cw1

            pm.rowColumnLayout( self.bodyCol, edit=True, columnWidth=[( 1, cw1 ),( 2, cw2 ), ( 3, cw3 )] )


    def show( self ):
        try:
            pm.deleteUI( self.__name__ )
        except:
            pass

        self.win = pm.window( self.__name__ )
        self.win.setTitle( self.m_title )
        self.win.setWidthHeight( (300,600) )

        pm.menuBarLayout()
        pm.menu( label='Edit' )
        pm.menu( label='Help', helpMenu=True )
        pm.menuItem( label='About...' )

        self.mainForm = pm.formLayout( numberOfDivisions=100 )

        self.mainForm_header = pm.frameLayout( borderStyle='etchedIn',
                                            marginWidth=6,
                                            marginHeight=0,
                                            label='Search & Replace Paths',
                                            labelVisible=True,
                                            labelAlign='center',
                                            collapsable=False,
                                            collapse=False,
                                            labelIndent=6 )

        self.mainHeader_col = pm.columnLayout( adjustableColumn=True, rowSpacing=6, columnAttach=["left", 0] )

        self._buildControls()
        #self._updateControls()

        pm.setParent( self.mainForm )

        self.mainForm_body = pm.scrollLayout( horizontalScrollBarThickness=0, childResizable=True )
        pm.scrollLayout( self.mainForm_body, edit=True, resizeCommand=lambda *args: self._resizeWindow()  )

        pm.setParent( self.mainForm_body )
        self.mainForm_col = pm.columnLayout( adjustableColumn=True, rowSpacing=4, columnAttach=["both", 0], columnAlign='left' )
        self.bodyText = pm.text( label=' No materials with file nodes in current scene.' )

        self._buildBodyControls()
        #self._updateBodyControls()

        pm.setParent( self.mainForm )
        self.mainForm_footer = pm.formLayout( numberOfDivisions=100 )

        self.mainFooter_details = pm.frameLayout( marginWidth=6, marginHeight=2, labelVisible=False )
        pm.rowLayout( numberOfColumns=5,  adjustableColumn=4, columnAlign=[(4, 'right'),(5, 'left')], columnWidth=[(1,74),(2,60),(3,60),(4,1),(5,28)])
        pm.text( label='Textures:100' )
        pm.text( label='Listed:10' )
        pm.text( label='Selected:1' )
        pm.text( label='Select All  ' )
        pm.checkBox( label='' )

        pm.setParent( self.mainForm_footer )
        self.mainFooter_col = pm.columnLayout( adjustableColumn=True, rowSpacing=3, columnAttach=["left", 6] )

        pm.radioButtonGrp( label='Show:',
                        numberOfRadioButtons=4,
                        labelArray4=['All', 'Unresolved', 'Duplicates', 'Empty'],
                        columnWidth=[(1,50),(2,50),(3,80),(4,80),(5,60)],
                        columnAttach=[(1,'left',2)]
                        )

        #separator(style='none')

        pm.radioButtonGrp( label='Filter:',
                        numberOfRadioButtons=3,
                        labelArray3=['None', 'Contains..', 'Doesn\'t Contain..'],
                        columnWidth=[(1,50),(2,50),(3,80),(4,100)],
                        columnAttach=[(1,'left',2)]
                        )


        self.filterStringTFBG = pmx.pathHistoryBrowser(label='String:',
                                                    columnAttach3=[ 'left', 'both', 'both'],
                                                    columnOffset3=[2, 2, 2],
                                                    adjustableColumn=2,
                                                    columnWidth3=[60, 1, 60],
                                                    buttonLabel='Browse..',
                                                    pathType='dir'
                                                    )


        pm.rowLayout( numberOfColumns=2, columnWidth2=(166,300),
                   columnAttach2=('right','left'),
                   columnOffset2=(1,1),
                   columnAlign2=('both','both')
                   )
        pm.button( label='Update', width=100, command='print "update Filters"' )

        pm.setParent( self.mainForm_footer )
        self.closeButton = pm.button( label='Close', height=26, command=lambda *args: self.delete() )


        self.mainForm_footer.attachForm( self.mainFooter_details, 'top', 6)
        self.mainForm_footer.attachForm( self.mainFooter_details, 'left', 0)
        self.mainForm_footer.attachForm( self.mainFooter_details, 'right', 0 )
        self.mainForm_footer.attachNone( self.mainFooter_details, 'bottom' )

        self.mainForm_footer.attachControl( self.mainFooter_col, 'top', 6, self.mainFooter_details)
        self.mainForm_footer.attachForm( self.mainFooter_col, 'left', 12)
        self.mainForm_footer.attachForm( self.mainFooter_col, 'right', 12)
        self.mainForm_footer.attachNone( self.mainFooter_col, 'bottom' )

        self.mainForm_footer.attachControl( self.closeButton, 'top', 6, self.mainFooter_col)
        self.mainForm_footer.attachForm( self.closeButton, 'left', 0)
        #self.mainForm_footer.attachPosition( self.closeButton, 'left', 2, 50 )
        self.mainForm_footer.attachForm( self.closeButton, 'right', 0)
        self.mainForm_footer.attachForm( self.closeButton, 'bottom', 0 )


        self.mainForm.attachForm( self.mainForm_header, 'top', 4 )
        self.mainForm.attachForm( self.mainForm_header, 'left', 2 )
        self.mainForm.attachForm( self.mainForm_header, 'right', 2 )
        self.mainForm.attachNone( self.mainForm_header, 'bottom' )

        self.mainForm.attachControl( self.mainForm_body, 'top', 2, self.mainForm_header )
        self.mainForm.attachForm( self.mainForm_body, 'left', 0 )
        self.mainForm.attachForm( self.mainForm_body, 'right', 0 )
        self.mainForm.attachControl( self.mainForm_body, 'bottom', 0, self.mainForm_footer)

        self.mainForm.attachNone( self.mainForm_footer, 'top')
        self.mainForm.attachForm( self.mainForm_footer, 'left', 5)
        self.mainForm.attachForm( self.mainForm_footer, 'right', 5)
        self.mainForm.attachForm( self.mainForm_footer, 'bottom', 5)

        self.win.show()

        jobCmd = 'python(\\\"%s.updateTexturePathViewer()\\\")' % __name__
        job = "scriptJob -replacePrevious -parent \"%s\" -event \"SceneOpened\" \"%s\";" % ( win.__name__, jobCmd )
        mel.eval(job)

    def delete( self ):
        self.win.delete()


def openTexturePathViewer():
    global win
    win = TexturePathViewer()
    win.show()


def updateTexturePathViewer():
    win._updateBody()
'''