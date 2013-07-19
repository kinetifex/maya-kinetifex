"""
Does some rig stuff.
"""


import pymel.core as pm
from pymel.core.datatypes import Vector

from impress import models, register

from kinetifex.config import RUNTIME_SUITE


def setAttributes(obj, attributes=[], **kwargs):
    """Adjust attributes for multiple objects"""

    for at in ('translate', 'scale', 'rotate'):
        if at in attributes:
            attributes.remove(at)
            attributes.extend([at + 'X', at + 'Y', at + 'Z'])
    i = 0
    try:
        for attr in pm.listAttr(obj, scalarAndArray=True, keyable=True, string=attributes) :
            if attr.count('.') == 0 :
                pm.setAttr('%s.%s' % (obj, attr), **kwargs)
                i += 1
    except:
        pass


def createNurbsShape(name='', shape='cube', width=1.0, height=1.0, depth=1.0, size=1.0):
    """
    Create vaious NURBS curve shapes. Useful for building control objects for animation.

    Different parameters are used depend on shape type:
        - B{cube} : width, height, depth
        - B{square} : width, depth
        - B{sphere} : size
        - B{locator} : size
        - B{pointer} : size
        - B{star} : size

    @param type: Required. Name of the shape to create. Available shapes are: cube, square, sphere, locator, pointer, star.
    @type type: string
    """

    if name == '':
        name = 'nurbs%s' % shape.capitalize()

    w, h, d = width / 2, height / 2, depth / 2

    s = size

    r = size / 2.0
    rh = r / 2.0
    rb = r * .866025

    s = size / 2.0

    if shape == 'cube':
        result = pm.curve(
            d=1,
            p=[(-w, -h, -d), (w, -h, -d), (w, -h, d), (-w, -h, d),
               (-w, -h, -d), (-w, h, -d), (w, h, -d), (w, -h, -d),
               (w, h, -d), (w, h, d), (w, -h, d), (w, h, d),
               (-w, h, d), (-w, -h, d), (-w, h, d), (-w, h, -d)],
            k=range(16)
        )

    elif shape == 'square':
        result = pm.curve(
            d=1,
            p=[(-w, 0, -d), (w, 0, -d), (w, 0, d), (-w, 0, d), (-w, 0, -d)],
            k=range(5)
        )

    elif shape == 'sphere':
        result = pm.curve(
            d=1,
            p=[(0, r, 0), (rh, rb, 0), (rb, rh, 0), (r, 0, 0), (rb, -rh, 0), (rh, -rb, 0),
               (0, -r, 0), (0, -rb, rh), (0, -rh, rb), (0, 0, r), (0, rh, rb), (0, rb, rh),
               (0, r, 0), (-rh, rb, 0), (-rb, rh, 0), (-r, 0, 0), (-rb, -rh, 0),
               (-rh, -rb, 0), (0, -r, 0), (0, -rb, -rh), (0, -rh, -rb), (0, 0, -r), (0, rh, -rb),
               (0, rb, -rh), (0, r, 0), (rh, rb, 0), (rb, rh, 0), (r, 0, 0), (rb, 0, rh),
               (rh, 0, rb), (0, 0, r), (-rh, 0, rb), (-rb, 0, rh), (-r, 0, 0),
               (-rb, 0, -rh), (-rh, 0, -rb), (0, 0, -r), (rh, 0, -rb), (rb, 0, -rh), (r, 0, 0)],
            k=range(40)
        )

    elif shape == 'locator':
        #uses radius parameter
        result = pm.curve(
            d=1,
            p=[(0, 0, -r), (0, 0, r), (0, 0, 0), (0, r, 0), (0, -r, 0), (0, 0, 0), (r, 0, 0), (-r, 0, 0)],
            k=range(8)
        )

    elif shape == 'pointer':
        result = pm.curve(
            d=3,
            p=[ Vector(x) * s for x in
               [(0, 1, -1.5), (0, .25, 0), (0, 0, 0), (0, -.25, 0), (0, -1, -1.5)]
               ],
            k=[0, 0, 0, 1, 2, 2, 2]
        )

    elif shape == 'star':
        result = pm.circle(normal=(0, 1, 0), radius=r * 1.35358, constructionHistory=False)[0]
        for i in (0, 2, 4, 6):
            pm.move('%s.cv[%i]' % (result.getShape(), i), [0, 0, 0], absolute=True)

    elif shape == 'axis':
        result = pm.curve(d=1, p=[(-r / 2, 0, 0), (r, 0, 0)], k=[0, 1])
        n = pm.PyNode(result).getShape()
        n.overrideEnabled.set(1)
        n.overrideColor.set(13)

        obj = pm.curve(d=1, p=[(0, -r / 2, 0), (0, r, 0)], k=[0, 1])
        n = pm.PyNode(obj).getShape()
        n.overrideEnabled.set(1)
        n.overrideColor.set(14)
        pm.parent(n, result, r=1, s=1)
        pm.delete(obj)

        obj = pm.curve(d=1, p=[(0, 0, -r / 2), (0, 0, r)], k=[0, 1])
        n = pm.PyNode(obj).getShape()
        n.overrideEnabled.set(1)
        n.overrideColor.set(6)
        pm.parent(n, result, r=1, s=1)
        pm.delete(obj)

    elif shape == 'arrow':
        result = pm.curve(d=1,
            p=[ Vector(x) * s for x in
                [(0, 0, 0), (0, 0.5, -1), (0, -0.5, -1), (0, 0, 0), (-0.5, 0, -1), (0.5, 0, -1), (0, 0, 0), (0, 0, -1)]
              ],
            k=[0, 1, 2, 3, 4, 5, 6, 7]
        )
    elif shape == 'triangle':
        result = pm.curve( d=1,
            p=[ Vector(x) * s for x in
                [(0, 0, 0.5),
                (-0.433013, 0, -0.25),
                (0.433013, 0, -0.25),
                (0, 0, 0.5)
                ]
            ],
            k=[0, 1, 2, 3]
        )
    elif shape == 'line':
        result = pm.curve( d=1,
            p=[ Vector(x) * s for x in
                [(0, 0, -0.5),
                 (0, 0, 0.5),
                ]
            ],
            k=[0, 1]
        )
    elif shape == 'circle':
        result = pm.circle( c=(0,0,0), nr=(0,1,0), sw=360, r=s, d=3, ut=0, tol=0, s=8, ch=0 )[0]
    elif shape == 'halfCircle':
        result = pm.circle( c=(0,0,0), nr=(0,1,0), sw=180, r=s, d=3, ut=0, tol=0, s=8, ch=0 )[0]
        result.ry.set(90)
        pm.makeIdentity(result, apply=True, translate=True, rotate=True, scale=True)
    elif shape in ['u','U']:
        result = pm.circle( c=(0,0,0), nr=(0,1,0), sw=180, r=s, d=1, ut=0, tol=0, s=4, ch=0 )[0]
        result.ry.set(90)
        pm.makeIdentity(result, apply=True, translate=True, rotate=True, scale=True)

    else:
        result = None

    #if type(result) is unicode:
    result = pm.PyNode(result)
    result.rename(name)
    pm.select(result, r=1)

    return result


#-------------------------------------------------
'''
class ResizeControlsOptionBox( OptionBox ):
    _title = 'Resize Controls Options'
    _helpTag = 'ResizeControls'
    _buttonLabel = 'Resize'

    optScale =  OptionVar( 'resizeControls_scale', 1 )

    options = [ optScale ]


    def _buildControls(self):
        self.optScale.control = radioButtonGrp( label='Affected Objects', numberOfRadioButtons=2, labelArray2=( 'Selected', 'Hierarchy' ), select=1 )


    def _updateControls( self, forceDefaults=False ):
        setOptionVars( self.options, forceDefaults )

        radioButtonGrp( self.optScale.control, edit=True, select=self.optScale.get() )


    def _updateOptions(self):
        value = radioButtonGrp( self.optScale.control, query=True, select=True )
        self.optScale.set( value )


    def apply(self):
        executeFromMEL( '%s.resizeControls()' % __name__ )


@register_runtime( category=RUNTIME_SUITE )
def ResizeControls( options=False ):
    """Select object(s) to lock node and attributes"""
    if options:
        LockObjectsOptionBox().show()
    else:
        select( ls( selection=True ), replace=True )
        selection = ls( selection=True )

        assert len( selection ) != 0, 'No objects selected to lock'

        optScale = bool( 1 - OptionVar( 'resizeControls_scale' ).get() )

        lockObjectsCmd( selection=True, dag=optScale )


def ResizeControlsCmd( *args, **kwargs ):
    objects = ls( *args, **kwargs )

    for obj in objects:
        for attr in obj.listAttr( scalarAndArray=True, keyable=True ) + obj.listAttr( channelBox=True ) :
            try:
                Attribute(attr).lock()
            except:
                pass

        lockNode(obj, lock=True, ignoreComponents=True)
'''
#-------------------------------------------------

class LockObjectsOptions(models.OptionModel):

    hierarchy = models.RadioButton(label='Affected Objects', default=0, labels=['Selected', 'Hierarchy'], basezero=True)


def lockObjects(hierarchy=False):
    """Select object(s) to lock node and attributes"""

    objects = pm.ls(selection=True, dag=hierarchy)

    for obj in objects:
        for attr in obj.listAttr(scalarAndArray=True, keyable=True) + obj.listAttr(channelBox=True) :
            try:
                pm.Attribute(attr).lock()
            except:
                pass

        pm.lockNode(obj, lock=True, ignoreComponents=True)


performLockObjects = register.PerformCommand(lockObjects, LockObjectsOptions)


class UnlockObjectsOptions(models.OptionModel):

    hierarchy = models.RadioButton(label='Affected Objects', default=0, labels=['Selected', 'Hierarchy'], basezero=True)


def unlockObjects(hierarchy=False):
    """Select object(s) to unlock node and attributes"""

    objects = pm.ls(selection=True, dag=hierarchy)

    for obj in objects:
        pm.lockNode(obj, lock=False, ignoreComponents=True)

        for attr in obj.listAttr(scalarAndArray=True, keyable=True) + obj.listAttr(channelBox=True) :
            try:
                pm.Attribute(attr).unlock()
            except:
                pass


performUnlockObjects = register.PerformCommand(unlockObjects, UnlockObjectsOptions)



class SpringJointOptions(models.OptionModel):

    type = models.EnumOptionMenu(1, labels=['Joint', 'ikHandle'])


def springJoint(joint=None, type=1):
    """Select a joint to apply spring to"""

    type = ('joint', 'ikHandle')[type - 1]

    if joint is None:
        joint = pm.ls(sl=1, type='joint')[0]


    pm.waitCursor(state=True)

    targetJoint = pm.PyNode(joint)
    parentJoint = targetJoint.getParent()
    topParent = parentJoint.getParent()

    print 'parentJoint:', parentJoint

    # --- error checking

    if targetJoint.type() != 'joint':
        assert False, 'only works on joint types'

    if parentJoint is None:
        assert False, 'joint must be child'
    if type == 'ikHandle' and topParent is None:
        assert False, 'joint must be child (2 deep)'


    targetJointWPos = targetJoint.getTranslation(worldSpace=True)
    parentJointWPos = parentJoint.getTranslation(worldSpace=True)
    length = Vector(targetJointWPos - parentJointWPos).length()

    control = createNurbsShape('spring_%s' % targetJoint, shape='star', size=length / 2)
    control.setTranslation(targetJointWPos, worldSpace=True)

    controlGroup = pm.group(control, name='springGroupControl_%s' % targetJoint)

    if type == 'joint':
        pm.parentConstraint(parentJoint, controlGroup, maintainOffset=True, weight=1.0)
    elif type == 'ikHandle':
        pm.parentConstraint(topParent, controlGroup, maintainOffset=True, weight=1.0)

    pm.makeIdentity(control, apply=True, translate=True, rotate=True, scale=True)
    pm.aimConstraint(parentJoint, control, aim=(0, 1, 0), weight=1.0)
    pm.toggle(control, selectHandle=True)

    # --- ---

    trans = pm.group(empty=True, name='springTrans_%s' % targetJoint)

    ptcl = pm.particle(name='springParticle_%s' % targetJoint, position=(0, 0, 0), conserve=1.0)[0]
    pm.move(ptcl, targetJointWPos, worldSpace=True)
    pm.goal(ptcl, weight=0.5, useTransformAsGoal=False, goal=control)
    ptcl.visibility.set(False)


    control.addAttr('goalWeight', shortName='gw', keyable=True, attributeType='double', min=0, max=1, defaultValue=0.5)
    control.goalWeight >> ptcl.goalWeight[0]

    control.addAttr('goalSmoothness', shortName='gsm',
                     keyable=True, attributeType='double',
                     min=0, defaultValue=3)
    control.goalSmoothness >> ptcl.goalSmoothness

    control.addAttr('goalConserve', shortName='con',
                     keyable=True, attributeType='double',
                     min=0, max=1, defaultValue=1)
    control.goalConserve >> ptcl.conserve

    control.addAttr('isDynamic', shortName='isd',
                     keyable=True, attributeType='bool')
    control.isDynamic >> ptcl.isDynamic

    ptcl.startFrame = 0
    ptcl.visibility = False

    # --- ---

    newExp = """
if(%s.isd)
{
    $pos = `xform -q -ws -t  %s.pt[0]`;
    translateX = $pos[0];
    translateY = $pos[1];
    translateZ = $pos[2];
}""" % (control, ptcl)

    pm.expression(name="%s_Exp" % targetJoint, object=trans, alwaysEvaluate=True, unitConversion='all', string=newExp)

    # --- ---

    if type == 'joint':
        pm.setKeyframe(targetJoint, attribute='translate')
        pm.pointConstraint(trans, targetJoint, offset=(0, 0, 0), weight=1.0)
        control.isd >> targetJoint.blendPoint1

        grp = pm.group(ptcl, trans, name='springGroup_%s' % targetJoint)

    elif type == "ikHandle":
        ik = pm.ikHandle(name='ik_%s' % targetJoint, startJoint=parentJoint, endEffector=targetJoint, solver='ikRPsolver')[0]
        ik.visibility = False
        control.isDynamic >> ik.ikBlend

        pm.pointConstraint(trans, ik, offset=(0, 0, 0), weight=1.0)

        grp = pm.group(ptcl, trans, ik, name='springGroup_%s' % targetJoint)

        control.addAttr('ikTwist', shortName='twi', keyable=True, attributeType='double', defaultValue=0.0)
        control.ikTwist >> ik.twi


    # --- setup springJoints container


    container_name = 'springJoints_group'

    if not pm.objExists(container_name):
        container = pm.group(empty=True, name=container_name)
        setAttributes(container, lock=True)
        setAttributes(container, attributes=['visibility'], lock=False, keyable=False)
    else:
        container = pm.PyNode('springJoints_group')

    pm.parent(controlGroup, grp, container)

    setAttributes(control, attributes=['scale', 'rotate'], lock=True, keyable=False)
    for obj in (controlGroup, grp):
        setAttributes(obj, lock=True)
        setAttributes(obj, attributes=['visibility'], lock=False, keyable=False)

    pm.select(control, replace=True)
    pm.setFocus(pm.getPanel(wf=True))

    pm.waitCursor(state=False)


performSprintJoint = register.PerformCommand(springJoint, SpringJointOptions)


class ModifyAttributesOptions(models.OptionModel):

    translate = models.CheckBox([0, 0, 0])
    rotate = models.CheckBox([0, 0, 0])
    scale = models.CheckBox([0, 0, 0])
    visibile = models.CheckBox(0)

    sep1 = models.Separator(style='in', height=14)

    change = models.CheckBox(1)
    affected = models.CheckBox(1)

'''
class ModifyAttributesOptionBox( pmx.OptionBox ):
    _title = 'Modify Attributes Options'
    _helpTag = 'ModifyAttributes'
    _buttonLabel = 'Modify'

    optTranslate = OptionVar( 'modifyAttributes_translate', ( 0, 0, 0 ) )
    optRotate = OptionVar( 'modifyAttributes_rotate', ( 0, 0, 0 ) )
    optScale = OptionVar( 'modifyAttributes_scale', ( 0, 0, 0 ) )
    optVis = OptionVar( 'modifyAttributes_visibility', 0 )

    optChange = OptionVar( 'modifyAttributes_change', 1 )
    optScale = OptionVar( 'modifyAttributes_affected', 1 )

    options = [ optTranslate, optRotate, optScale, optVis,
                optChange, optScale ]


    def _buildControls( self ):

        self.optScale.control = pm.radioButtonGrp( label='Affected Objects', numberOfRadioButtons=2, labelArray2=( 'Selected', 'Hierarchy' ), select=1 )

        pm.separator( height=20 )

        self.optTranslate.control = pm.checkBoxGrp( label='Translate', numberOfCheckBoxes=3, labelArray3=( 'TX', 'TY', 'TZ' ) )
        pm.popupMenu()
        pm.menuItem( label='Select All',
                  command=lambda * args: pm.checkBoxGrp( self.optTranslate.control, edit=True, valueArray3=( 1, 1, 1 ) )
                  )
        pm.menuItem( label='Deselect All',
                  command=lambda * args: pm.checkBoxGrp( self.optTranslate.control, edit=True, valueArray3=( 0, 0, 0 ) )
                  )

        self.optRotate.control = pm.checkBoxGrp( label='Rotate', numberOfCheckBoxes=3, labelArray3=( 'RX', 'RY', 'RZ' ) )
        pm.popupMenu()
        pm.menuItem( label='Select All',
                  command=lambda * args: pm.checkBoxGrp( self.optRotate.control, edit=True, valueArray3=( 1, 1, 1 ) )
                  )
        pm.menuItem( label='Deselect All',
                  command=lambda * args: pm.checkBoxGrp( self.optRotate.control, edit=True, valueArray3=( 0, 0, 0 ) )
                  )

        self.optScale.control = pm.checkBoxGrp( label='Scale', numberOfCheckBoxes=3, labelArray3=( 'SX', 'SY', 'SZ' ) )
        pm.popupMenu()
        pm.menuItem( label='Select All',
                  command=lambda * args: pm.checkBoxGrp( self.optScale.control, edit=True, valueArray3=( 1, 1, 1 ) )
                  )
        pm.menuItem( label='Deselect All',
                  command=lambda * args: pm.checkBoxGrp( self.optScale.control, edit=True, valueArray3=( 0, 0, 0 ) )
                  )

        self.optVis.control = pm.checkBoxGrp( label='Visibility' )

        pm.separator( height=20 )

        self.changeRGB0 = pm.radioButtonGrp( numberOfRadioButtons=3, labelArray3=( 'Keyable', 'Nonkeyable', 'Hidden' ) )
        self.changeRGB1 = pm.radioButtonGrp( numberOfRadioButtons=2, labelArray2=( 'Lock', 'Unlock' ), shareCollection=self.changeRGB0 )


    def _updateControls( self, forceDefaults=False ):
        pmx.setOptionVars( self.options, forceDefaults )

        #pm.checkBoxGrp( self.optScale.control, edit=True, valueArray3=self.optScale.get() )
        #self.optScale.control.setSelect( self.optScale.get() )

        for opt in ( self.optTranslate, self.optRotate, self.optScale ):
                v = opt.get()
                pm.checkBoxGrp( opt.control, edit=True, value1=v[0], value2=v[1], value3=v[2] )

        v = self.optChange.get()
        if v <= 3:
            pm.radioButtonGrp( self.changeRGB0, edit=True, select=v )
        else:
            pm.radioButtonGrp( self.changeRGB1, edit=True, select=v - 3 )

        pm.checkBoxGrp( self.optVis.control, edit=True, value1=self.optVis.get() )


    def _updateOptions( self ):

        value = pm.radioButtonGrp( self.optScale.control, query=True, select=True )
        self.optScale.set( value )

        for opt in ( self.optTranslate, self.optRotate, self.optScale ):
            value = ( pm.checkBoxGrp( opt.control, query=True, value1=True ),
                      pm.checkBoxGrp( opt.control, query=True, value2=True ),
                      pm.checkBoxGrp( opt.control, query=True, value3=True )
                      )
            opt.set( value )
        value = pm.checkBoxGrp( self.optVis.control, query=True, value1=True )
        self.optVis.set( value )

        v0 = pm.radioButtonGrp( self.changeRGB0, query=True, select=True )
        v1 = pm.radioButtonGrp( self.changeRGB1, query=True, select=True )

        self.optChange.set( v0 or v1 + 3 )


    def apply( self ):
        pmx.executeFromMEL( '%s.modifyAttributes()' % __name__ )


@register.runtime
def modifyAttributes( options=False ):
    """Modify the transform attributes of multiple objects"""
    if options:
        win = ModifyAttributesOptionBox()
        win.show()
    else:
        optAffected = bool( 1 - OptionVar( 'modifyAttributes_affected' ).get() )

        optTranslate = OptionVar( 'modifyAttributes_translate' ).get()
        optRotate = OptionVar( 'modifyAttributes_rotate' ).get()
        optScale = OptionVar( 'modifyAttributes_scale' ).get()
        optVis = OptionVar( 'modifyAttributes_visibility' ).get()

        optChange = ( None, 'keyable', 'nonkeyable', 'hidden', 'lock', 'unlock' )[ OptionVar( 'modifyAttributes_change' ).get() ]


        radioOptList = ( True, False, None )

        attrList = ['tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz', 'v']

        optList = []
        optList += optTranslate + optRotate + optScale + ( optVis, )

        attributes = []

        for i in range( len( optList ) ):
            if optList[i] == 1:
                attributes.append( attrList[i] )


        pm.select( pm.ls( selection=True ), replace=True )
        objects = pm.ls( selection=True, type='transform' )

        assert len( attributes ) != 0, 'No attributes selected.'
        assert len( objects ) != 0, 'No objects selected.'

        modifyAttributesCmd( objects, attributes,
                             change=optChange,
                             dag=optAffected
                             )


def modifyAttributesCmd( objectList, attributeList, change, dag=False ):

    objects = pm.ls( objectList, dag=dag, type='transform' )

    objCount = 0
    attrCount = 0

    assert change is not None, 'No attribute changes specified'

    for object in objects:
        objCount += 1

        for attr in map( pm.Attribute , [ '%s.%s' % ( object, a ) for a in attributeList ] ):
            attrCount += 1

            if change == 'keyable':
                attr.setKeyable( True )
            if change == 'nonkeyable':
                if attr.isKeyable():
                    attr.set( channelBox=True )
            if change == 'hidden':
                attr.setKeyable( False )
                if attr.isInChannelBox():
                    attr.set( channelBox=False )
            if change == 'lock':
                attr.lock()
            if change == 'unlock':
                attr.unlock()

    print '# Results: %i attributes of %i objects set to "%s".' % ( attrCount, objCount, change )
'''

def resetIkSetupCmd(joint, control):
    """
    prepares ikControls and reset target for the kx_resetIk command
    global command which sets up bindings based provided variables
    """

    try:
        container = pm.PyNode("resetik_group")
    except pm.MayaNodeError:
        container = pm.group(em=1, n="resetik_group")

    reset_target = pm.group(n='%s_resetik' % control, em=1)
    reset_target.setRotatePivot(control.getRotatePivot(ws=1), ws=1)

    pm.parentConstraint(joint, reset_target, mo=1, w=1)

    pm.parent(reset_target, container)

    return reset_target


@register.runtime
def resetIkSetup():
    """select joint then control to set IK targets for"""

    try:
        joint, control = pm.ls(sl=1, type='transform')
    except ValueError:
        raise ValueError, "Select the start and end joints to setup."

    resetIkSetupCmd(joint, control)

    pm.select(control, r=1)


def setAttrs(node, attrs=[], **kwargs):

    if('t' in attrs):
        attrs.pop(attrs.index('t'))
        attrs.extend(['tx','ty','tz'])

    if('r' in attrs):
        attrs.pop(attrs.index('r'))
        attrs.extend(['rx','ry','rz'])

    if('s' in attrs):
        attrs.pop(attrs.index('s'))
        attrs.extend(['sx','sy','sz'])

    for a in attrs:
        node.attr(a).set(**kwargs)


def switchParentSetupCmd(parent_obj, target, build_world=False):

    print "# Setting up SwitchParent:", target, parent_obj

    target = pm.PyNode(target)
    parent_obj = pm.PyNode(parent_obj)

    container = "switchParent_group";

    try:
        container = pm.PyNode('switchParent_group')
    except pm.MayaNodeError:
        container = pm.group(em=1, n='switchParent_group')

    try:
        _world = pm.PyNode('_world')
    except pm.MayaNodeError:
        _world = pm.group(em=1, n='_world')
        _world.v.set(False, k=0, l=0)
        pm.parent(_world, container)


    # -- if first parent_obj not found, set as _world
    if not target.hasAttr('parent') and not build_world:
        switchParentSetupCmd(_world, target, build_world=True)

    # --- ---

    try:
        target_holder = pm.PyNode("holder_" + target)
    except pm.MayaNodeError:
        target_holder = pm.group(target, n="holder_" + target)
        pm.parent(target_holder, container)

    try:
        parent_obj_space = pm.PyNode("space_" + parent_obj)
    except pm.MayaNodeError:
        parent_obj_space = pm.group(em=1, n="space_" + parent_obj)
        pm.parent(parent_obj_space, container)
        pm.parentConstraint(parent_obj, parent_obj_space, mo=1, w=1, n="parentConstraint_" + parent_obj_space)

    target_piv = target.getRotatePivot(ws=1)

    target_pos = target.translate.get()
    target_rot = target.rotate.get()

    setAttrs(target, ['tx', 'ty', 'tz', 'rx', 'ry', 'rz'], l=0)
    target.translate.set((0, 0, 0))
    target.rotate.set((0, 0, 0))

    src_constraint = pm.parentConstraint(parent_obj, target_holder, mo=1, w=0, n="parentConstraint_" + target_holder)

    # --- setup parent_obj guide

    existing_guides = pm.ls(regex=target + '_target([0-9])')

    parent_obj_guide = pm.group(em=1, n=target + '_target%d' % len(existing_guides))

    pm.parent(parent_obj_guide, parent_obj_space)
    parent_obj_guide.setRotatePivot(target_piv, ws=1)
    pm.parentConstraint(target, parent_obj_guide, mo=1, w=1, n="parentConstraint_" + parent_obj_guide)
    parent_obj_guide.v.set(0, k=0, l=1)
    parent_obj_guide.nds.set(k=0)

    if not target.hasAttr('parent'):
        enum_name = '%s:' % parent_obj
        target.addAttr('parent', at='enum', enumName=enum_name)
        target.parent.set(k=1)
    else:
        enum_list = pm.addAttr(target + '.parent', enumName=1, q=1).split(':')#target.parent.getEnums()#
        target.parent.setEnums(enum_list + [str(parent_obj)])

    enum_list = pm.addAttr(target + '.parent', enumName=1, q=1).split(':')#target.parent.getEnums()

    constraint_list = pm.listAttr("parentConstraint_" + target_holder, ud=1, k=1)

    for i in range(len(enum_list)):
        for j in range(len(enum_list)):
            if j == i:
                pm.setDrivenKeyframe(src_constraint + '.' + constraint_list[i], cd=target.parent, dv=j, v=1, ott='linear')
            else:
                pm.setDrivenKeyframe(src_constraint + '.' + constraint_list[i], cd=target.parent, dv=j, v=0, ott='linear')


    target.translate.set(target_pos)
    target.rotate.set(target_rot)

    pm.select(target, r=1)

    print "# Setup SwitchParent for %s to %s." % (target, parent_obj)


@register.runtime
def switchParentSetup():
    selection = pm.ls(selection=True, type='transform')

    assert len(selection) == 2, 'Select 2 transform nodes (target,target)'
    parent_obj, target = selection

    print r'switchParentSetupCmd( "%s", "%s" )' % (parent_obj, target)
    switchParentSetupCmd(parent_obj, target)


class ScaleCurveShapeOptions(models.OptionModel):

    amount = models.FloatSlider(default=1.1, ann="Amount by which to scale.", min=0, max=2)


def scaleCurveShape(amount, transforms=None):

    if transforms is None:
        transforms = pm.ls(sl=1)

    for transform in transforms:
        try:
            pm.scale(transform.cv, [amount] * 3, cp=1)
        except:
            pm.scale(transform.verts, [amount] * 3, cp=1)


performScaleCurveShape = register.PerformCommand(scaleCurveShape, ScaleCurveShapeOptions)


class TweakJointOrientOptions(models.OptionModel):

    rotation = models.FloatField(default=[5, 0, 0], ann="Amount by which to rotate.")


def tweakJointOrient(rotation, joints=None):

    if joints is not None:
        pm.select(joints, replace=1)

    joints = pm.ls(sl=1, type='joint')
    pm.select(joints, replace=1)

    if not joints:
        pm.error("Requires valid joints to be specified or selected.")

    for jnt in joints:
        pm.xform(jnt, r=1, os=1, ra=rotation)
        pm.joint(jnt, e=True, zeroScaleOrient=True)
        pm.makeIdentity(jnt, apply=True, t=0, r=1, s=0, n=0)


performTweakJointOrient = register.PerformCommand(tweakJointOrient, TweakJointOrientOptions)
