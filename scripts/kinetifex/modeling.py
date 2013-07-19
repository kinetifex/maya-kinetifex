"""
Commands and options for manipulating transform nodes and poly surfaces.
"""


import random

import pymel.core as pm
from pymel.core import mel
# import pymelX as pmx
# from pymelX import register_runtime, OptionVar

from impress import models, register

from config import RUNTIME_SUITE
from modify import unfreezeTranslationCmd


def lsSelectedVerts():
    sel_list = pm.ls( sl=1, type="float3" )
    vert_list = []
    for sel in sel_list:
        for v in sel:
            vert_list.append( v )

    return vert_list


@register.runtime
def matchVertexNormals():
    """
    Match the 2 selected vertex normals of 2 different meshes.
    """

    try:
        src, tgt = pm.ls( hl=1 )
    except ValueError:
        assert False, "must have source and target meshes hilighted"


    sel_verts = lsSelectedVerts()
    if len( sel_verts ) != 2:
        assert False, "must have 2 verts selected"

    if sel_verts[0].node().getParent() == src:
        src_v = sel_verts[0]
    elif sel_verts[1].node().getParent() == src:
        src_v = sel_verts[1]
    else:
        assert False, "no vert selected from source mesh (%s)" % src

    if sel_verts[0].node().getParent() == tgt:
        tgt_v = sel_verts[0]
    elif sel_verts[1].node().getParent() == tgt:
        tgt_v = sel_verts[1]
    else:
        assert False, "no vert selected from target mesh (%s)" % tgt

    n = src_v.getNormals()[0]

    # if the transform is scaled in the x axis
    if bool( src.getScale()[0] < 0 ) is not bool( tgt.getScale()[0] < 0 ):
        n = n * [-1, 1, 1]

    pm.select( tgt_v, r=1 )
    pm.polyNormalPerVertex( xyz=n )

    pm.select( ( src_v, tgt_v ), r=1 )


'''
@register.runtime
def attachObject( options=False ):
    """Select target objects followed by object to be duplicated and moved"""
    mel.kx_attachObject( int( options ) )
'''

'''
class SelectFacesOptionBox( pmx.OptionBox ):

    _title = 'Select Faces Options'
    _helpTag = 'SelectFaces'
    _buttonLabel = 'Select Faces'

    optThreshold = OptionVar( 'selectFaces_threshold', 0.65 )
    optAxis      = OptionVar( 'selectFaces_axis',      1 )
    optSign      = OptionVar( 'selectFaces_sign',      1 )
    optMethod    = OptionVar( 'selectFaces_method',    1 )

    options = [ optThreshold, optAxis, optSign, optMethod ]


    def _buildControls(self):
        self.optThreshold.control = pm.floatSliderGrp( label='Threshold', min=0, max=1, precision=3 )

        self.optAxis.control = pm.radioButtonGrp( label='Axis', numberOfRadioButtons=3,
                                               labelArray3=('X', 'Y', 'Z') )

        self.optSign.control = pm.radioButtonGrp( label='Direction', numberOfRadioButtons=2,
                                               labelArray2=('(1) positive', '(-1) negative') )

        pm.separator( style='none', height=14 )

        self.optMethod.control = pm.radioButtonGrp( label='Selection', numberOfRadioButtons=4,
                                                 columnWidth5=( 170, 45, 55, 60, 60 ),
                                                 labelArray4=('add', 'toggle', 'replace', 'deselect') )

    def _updateControls( self, forceDefaults=False ):
        pmx.setOptionVars( self.options, forceDefaults )

        pm.floatSliderGrp( self.optThreshold.control, edit=True, value=self.optThreshold.get() )
        pm.radioButtonGrp( self.optAxis.control, edit=True, select=self.optAxis.get() )
        pm.radioButtonGrp( self.optSign.control, edit=True, select=self.optSign.get() )
        pm.radioButtonGrp( self.optMethod.control, edit=True, select=self.optMethod.get() )


    def _updateOptions(self):
        value = pm.floatSliderGrp( self.optThreshold.control, query=True, value=True )
        self.optThreshold.set( value )
        value = pm.radioButtonGrp( self.optAxis.control, query=True, select=True )
        self.optAxis.set( value )
        value = pm.radioButtonGrp( self.optSign.control, query=True, select=True )
        self.optSign.set( value )
        value = pm.radioButtonGrp( self.optMethod.control, query=True, select=True )
        self.optMethod.set( value )

    def apply(self):
        pmx.executeFromMEL( '%s.selectFaces()' % __name__ )


def selectFaces( options=False ):
    if options:
        SelectFacesOptionBox().show()
    else:
        optThreshold = OptionVar( 'selectFaces_threshold' ).get()
        optAxis =      OptionVar( 'selectFaces_axis'      ).get()
        optSign =      OptionVar( 'selectFaces_sign'      ).get()
        optMethod =    OptionVar( 'selectFaces_method'    ).get()

        method = ( 'add', 'toggle', 'replace', 'deselect' )[optMethod - 1]
        axis = ( 'x', 'y', 'z' )[optAxis - 1]
        sign = (1,-1)[optSign - 1]

        #print 'selectFacesCmd(', ', '.join( [ str(axis), str(sign), str(optThreshold), str(method) ] ), ' )'
        selectFacesCmd( axis, sign, optThreshold, method )


def selectFacesCmd(axis_str, sign, threshold, method):
    results = 0
    selList = []
    axis = {'x':0, 'y':1, 'z':2}[ axis_str.lower() ]

    add = toggle = replace = deselect = False
    if method == 'add':
        add=True
    elif method == 'toggle':
        toggle = True
    elif method == 'replace':
        replace = True
    elif method == 'deselect':
        deselect = True

    objects = pm.ls( selection=True, dag=True, geometry=True, assemblies=True, objectsOnly=True)

    assert len(objects), 'selectFacesCmd requires at least 1 selected polygon object.'

    for object in objects:
        if not pm.objectType( object, isType='mesh' ):
            mel.warning( 'Only works on polygon objects, ignored' + object + '.\n' )
        else:
            faces = range( pm.polyEvaluate( object, face=True ) )
            for face in faces:
                faceNormal = [ float(f) for f in pm.polyInfo( '%s.f[%s]' % (object, face), faceNormals=True )[0].split()[2:] ]

                if ( faceNormal[axis] * sign ) >= threshold:
                    selList.append( '%s.f[%s]' % (object, face) )
                    results += 1

    pm.selectMode( component=True )

    pm.select( selList, replace=replace, add=add, toggle=toggle, deselect=deselect )

    print '// Results: %i faces updated (%s) //' % ( results, method )
'''

class RandomTransformOptions( models.OptionModel ):

    translate = models.CheckBox( default=1 )
    translateAmount = models.FloatSlider( default=1, precision=3, requires=( translate, 1 ) )
    translateAxis = models.CheckBox( labels=['X', 'Y', 'Z'], default=[1, 1, 1], requires=( translate, 1 ) )

    sep1 = models.Separator( style='in', height=14 )

    rotate = models.CheckBox( default=1 )
    rotateAmount = models.FloatSlider( default=1, precision=3, requires=( rotate, 1 ) )
    rotateAxis = models.CheckBox( labels=['X', 'Y', 'Z'], default=[1, 1, 1], requires=( rotate, 1 ) )

    sep2 = models.Separator( style='in', height=14 )

    scale = models.CheckBox( default=1 )
    scaleAmount = models.FloatSlider( default=1, precision=3, requires=( scale, 1 ) )
    scaleAxis = models.CheckBox( labels=['X', 'Y', 'Z'], default=[1, 1, 1], requires=( scale, 1 ) )


def randomTransform( translate=False, translateAmount=1.0, translateAxis=( False, False, False ),
                     rotate=False, rotateAmount=1.0, rotateAxis=( False, False, False ),
                     scale=False, scaleAmount=1.0, scaleAxis=( False, False, False ) ):
    """
    Transforms selected objects.
    """
    results = 0

    objects = pm.ls( selection=True, type='transform' )

    assert len( objects ), 'randomTransform requires at least 1 selected transform object.'

    for object in objects:
        if translate:
            offset = map( lambda axis: random.uniform( -translateAmount, translateAmount ) * float( axis ), translateAxis )
            object.setTranslation( offset, relative=True )
        if rotate:
            offset = map( lambda axis: random.uniform( -rotateAmount, rotateAmount ) * float( axis ), rotateAxis )
            object.setRotation( offset, relative=True )
        if scale:
            offset = map( lambda axis: 1 + ( random.uniform( -scaleAmount, scaleAmount ) * float( axis ) ), scaleAxis )
            object.setScale( offset )
        results += 1

    print '// Results: %i object randomized. //' % results


performRandomTransform = register.PerformCommand( randomTransform, RandomTransformOptions )

'''
class PolyNoiseOptionBox( pmx.OptionBox ):

    _title = 'Poly Noise Options'
    _helpTag = 'polyNoise'
    _buttonLabel = 'Poly Noise'

    optAmount = OptionVar( 'polyNoise_amount', 1.0 )
    optAxis =   OptionVar( 'polyNoise_axis', (True,True,True) )

    options = [ optAmount, optAxis ]


    def _buildControls(self):
        self.optAmount.control = pm.floatSliderGrp( label='Amount', min=0, max=10, precision=4 )
        self.optAxis.control =   pm.checkBoxGrp( label='Axis', numberOfCheckBoxes=3, labelArray3=('X', 'Y', 'Z') )

    def _updateControls( self, forceDefaults=False ):
        pmx.setOptionVars( self.options, forceDefaults )

        pm.floatSliderGrp( self.optAmount.control, edit=True, value=self.optAmount.get() )
        pm.checkBoxGrp( self.optAxis.control, edit=True, valueArray3=self.optAxis.get() )

    def _updateOptions(self):
        value = pm.floatSliderGrp( self.optAmount.control, query=True, value=True )
        self.optAmount.set( value )
        value = ( pm.checkBoxGrp( self.optAxis.control, query=True, value1=True ),
                  pm.checkBoxGrp( self.optAxis.control, query=True, value2=True ),
                  pm.checkBoxGrp( self.optAxis.control, query=True, value3=True )
                  )
        self.optAxis.set( value )

    def apply(self):
        pmx.executeFromMEL( '%s.polyNoise()' % __name__ )

@register_runtime( category=RUNTIME_SUITE )
def polyNoise( options=False ):
    if options:
        PolyNoiseOptionBox().show()
    else:
        optAmount = OptionVar( 'polyNoise_amount' ).get()
        optAxis =   OptionVar( 'polyNoise_axis'   ).get()

        print 'polyNoiseCmd(', ', '.join( [ str(optAmount), str(optAxis) ] ), ')'
        polyNoiseCmd( optAmount, optAxis )


def polyNoiseCmd( amount, axis ):
    results = 0
    selList = []

    components = pmx.lsComponents( selection=True )

    assert len(components), 'polyNoiseCmd requires at least 1 selected polygon object or component.'

    for component in components:
        offset = map( lambda x: random.uniform( -amount, amount )*float(x), axis )

        pm.move( component, offset, relative=True )

        results += 1

    print '// Results: %i transforms and components randomized //' % results
'''

'''
class UVNoiseOptionBox( pmx.OptionBox ):
    _title = 'UV Noise Options'
    _helpTag = 'UVNoise'
    _buttonLabel = 'Make Noise'

    optAmount =  OptionVar( 'uvNoise_amount', 1.0 )
    optAxis =    OptionVar( 'uvNoise_axis', (True,True) )

    options = [ optAmount, optAxis ]


    def _buildControls(self):
        self.optAmount.control = pm.floatSliderGrp( label='Amount', min=0, max=1, precision=4 )
        self.optAxis.control =   pm.checkBoxGrp( label='Axis', numberOfCheckBoxes=2, labelArray2=('U', 'V') )


    def _updateControls( self, forceDefaults=False ):
        pmx.setOptionVars( self.options, forceDefaults )

        pm.floatSliderGrp( self.optAmount.control, edit=True, value=self.optAmount.get() )
        pm.checkBoxGrp( self.optAxis.control, edit=True, valueArray2=self.optAxis.get() )


    def _updateOptions(self):
        value = pm.floatSliderGrp( self.optAmount.control, query=True, value=True )
        self.optAmount.set( value )

        value = ( pm.checkBoxGrp( self.optAxis.control, query=True, value1=True ),
                  pm.checkBoxGrp( self.optAxis.control, query=True, value2=True )
                  )
        self.optAxis.set( value )

    def apply(self):
        pmx.executeFromMEL( '%s.uvNoise()' % __name__ )

@register_runtime( category=RUNTIME_SUITE )
def uvNoise( options=False ):
    if options:
        UVNoiseOptionBox().show()
    else:
        optAmount = OptionVar( 'uvNoise_amount' ).get()
        optAxis =   OptionVar( 'uvNoise_axis'   ).get()

        print 'uvNoiseCmd(', ', '.join( [ str(optAmount), str(optAxis) ] ), ')'
        uvNoiseCmd( optAmount, optAxis )


def uvNoiseCmd( amount, axis ):
    results = 0
    selList = []

    components = pmx.lsComponents( selection=True, type='float2' )

    assert len(components), 'uvNoiseCmd requires at least 1 selected polygon object or component.'

    for component in components:
        offset = map( lambda x: random.uniform( -amount, amount )*float(x), axis )
        pm.polyEditUV( component, uValue=offset[0], vValue=offset[1], relative=True )

        results += 1

    print '// Results: %i UVs randomized //' % results
'''

'''
class TargetCombineOptionBox( pmx.OptionBox ):
    _title = 'Target Combine Options'
    _helpTag = 'targetCombine'
    _buttonLabel = 'Target Combine'

    optCH = OptionVar( 'targetCombine_construcionHistory', False )

    options = [ optCH ]


    def _buildControls(self):
        self.optCH.control = pm.checkBoxGrp( numberOfCheckBoxes=1, label1='Construction History' )


    def _updateControls( self, forceDefaults=False ):
        pmx.setOptionVars( self.options, forceDefaults )

        pm.checkBoxGrp( self.optCH.control, edit=True, value1=self.optCH.get() )


    def _updateOptions(self):
        self.optCH.set( bool( pm.checkBoxGrp( self.optCH.control, query=True, value1=True ) ) )


    def apply(self):
        pmx.executeFromMEL( '%s.targetCombine()' % __name__ )

@register_runtime( category=RUNTIME_SUITE )
def targetCombine( options=False ):
    """Select polygon objects to combine with target object last."""
    if options:
        TargetCombineOptionBox().show()
    else:

        objects = pm.ls(selection=True, type='transform')

        optCH = OptionVar( 'targetCombine_construcionHistory', False ).get()

        assert len(objects) >= 2, 'Target Combine requires at least 2 polygonal objects.'

        targetCombineCmd( objects, optCH )


def targetCombineCmd( objects, constructionHistory=False ):

    pivot = objects[-1].getRotatePivot( worldSpace=True )

    combined = pm.polyUnite( objects, ch=constructionHistory )
    combined = pm.rename( combined[0], objects[-1] )

    combined.setRotatePivot( pivot, worldSpace=True )
    combined.setScalePivot(  pivot, worldSpace=True )

    unfreezeTranslationCmd( (combined,) )

    print '// Results: Combined %i objects to %s. //' % ( len(objects), combined )
'''

class ReplaceShapeOptions( models.OptionModel ):

    constructionHistory = models.CheckBox( default=0 )


def replaceShape( objects, constructionHistory=False ):
    """Select source polygon object followed by target you wish to update."""
    source, target = objects

    if not constructionHistory:
        pm.select( source, replace=True )
        mel.DeleteHistory()

    srcShape = source.getChildren( type='mesh' )[0]
    tgtShape = target.getChildren( type='mesh' )[0]
    resultShape = pm.parent( srcShape, target, r=True, s=True )
    pm.delete( source, tgtShape )

    pm.rename( resultShape, tgtShape )
    pm.select( target, replace=True )

    print '// Results: Replaced shape for object %s. //' % target


performReplaceShape = register.PerformCommand( replaceShape, ReplaceShapeOptions )

'''
class PolyFaceProjectionOptionBox( pmx.OptionBox ):
    _title = 'Poly Face Projection Options'
    _helpTag = 'polyFaceProjection'
    _buttonLabel = 'Face Project'

    optCH = OptionVar( 'polyFaceProjection_construcionHistory', False )

    options = [ optCH ]


    def _buildControls(self):
        self.optCH.control = pm.checkBoxGrp( numberOfCheckBoxes=1, label1='Construction History' )


    def _updateControls( self, forceDefaults=False ):
        pmx.setOptionVars( self.options, forceDefaults )

        pm.checkBoxGrp( self.optCH.control, edit=True, value1=self.optCH.get() )


    def _updateOptions(self):
        self.optCH.set( bool( pm.checkBoxGrp( self.optCH.control, query=True, value1=True ) ) )


    def apply(self):
        pmx.executeFromMEL( '%s.polyFaceProjection()' % __name__ )


@register_runtime( category=RUNTIME_SUITE )
def polyFaceProjection( options=False ):
    """
    Performs planar UV projection for each selected face.
    Delete History before executing for speed enhancement.
    """
    if options:
        PolyFaceProjectionOptionBox().show()
    else:

        components = pm.ls(sl=1, type="float3")

        optCH = OptionVar( 'polyFaceProjection_construcionHistory', False ).get()

        assert len(components) >= 1, 'Poly Face Projection requires at least 1 face selected.'

        polyFaceProjectionCmd( components, optCH )


def polyFaceProjectionCmd( components, constructionHistory=False ):

    sel_list = []
    count = 0

    for comp in components:
        if isinstance( comp, pm.MeshFace ):
            sel_list.append(str(comp))
            ch = True
            if not constructionHistory:
                if len( comp.node().listHistory() ) < 3:
                    ch = False
                else:
                    mel.eval(r'warning("# Delete History on \"%s\" for speed enhancement. #")' % comp.node() )

            for c in comp._range:
                face = comp._node.f[c]
                pm.select(face, r=1)

                pm.polyProjection( face, ch=ch, type='Planar', ibd=1, kir=1,  md='b')

                count+=1

    pm.select( sel_list, replace=1 )

    print '// Results: %d faces projected. //' % count
'''

def cleanGroupCombineCmd( group_list ):

    combined_list = []

    for grp in group_list:

        grp_parent = grp.getParent()
        print "grp_parent:", grp_parent

        pm.delete( ch=1 )
        grp_str = grp.nodeName()

        mesh_children = pm.ls( grp, dag=1, type="mesh" )

        if len( mesh_children ) > 1:

            if grp_parent is not None:
                pm.parent( grp, world=1 )
            obj = pm.polyUnite( grp, ch=1 )[0]
            pm.delete( obj, ch=1 )

            try:
                pm.delete( grp )
            except TypeError:
                pass

            if grp_parent is not None:
                pm.parent( obj, grp_parent )
            obj_str = obj.rename( grp_str )

            print '// Result: Combined group as', obj_str

        elif len( mesh_children ) == 1:

            obj = mesh_children[0].getParent()
            if grp_parent is not None:
                pm.parent( obj, grp_parent )
            pm.delete( grp )
            obj_str = obj.rename( grp_str )

            print '// Result: Promoted mesh as', obj_str

        else:
            obj = None
            mel.warning( "No meshes found under group." )

        if not obj is None:
            combined_list.append( obj )

    return combined_list




@register.runtime
def cleanGroupCombine():
    """
    Combines all the meshes of each selected group and retains name.
    """
    group_list = pm.ls( sl=1, type='transform' )
    cleanGroupCombineCmd( group_list )



@register.runtime
def reverseOppositeGeometry():
    """
    Finds and reverses meshes under selection with opposite flag set.
    """

    sel_list = pm.ls( sl=1, dag=1, type="mesh" )

    if not sel_list:
        mel.warning( "No meshes found in selection." )

    count = 0

    for obj in sel_list:
        if obj.opposite.get():
            obj.opposite.set( 0 )
            pm.polyNormal( obj, normalMode=0, userNormalMode=0, ch=0 )
            count += 1

    print '// Results: %d opposite meshes reversed.' % count
