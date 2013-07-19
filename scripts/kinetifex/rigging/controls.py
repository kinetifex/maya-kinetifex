

import pymel.core as pm
from pymel.core.datatypes import Vector

from general import createNurbsShape, resetIkSetupCmd, setAttrs
from kinetifex.scene import addToSet


LEFT_SIDE = 0
RIGHT_SIDE = 1

FOOTROLL_AUTO = 0
FOOTROLL_CONTROLS = 1
FOOTROLL_ATTRIBUTES = 2


EXP_STRETCH = \
"""
$stretch_blend = linstep( %(guide_ik)s.stretchStart, %(guide_ik)s.stretchEnd, %(loc_end)s.tx );

%(constraint)s.%(loc_mid)sW0 = $stretch_blend;
%(constraint)s.%(guide_ik_mid)sW1 = 1-$stretch_blend;

$stretch_start = %(start_joint)s.stretch +
    ( abs( %(guide_mid)s.translateX ) - abs( %(mid_joint)s.translateX ) ) *
    %(guide_ik)s.stretchFactor * %(control)s.stretchBlend * %(control)s.ikBlend;

$stretch_mid = %(mid_joint)s.stretch +
    ( abs( %(guide_end)s.translateX ) - abs( %(end_joint)s.translateX ) ) *
    %(guide_ik)s.stretchFactor * %(control)s.stretchBlend * %(control)s.ikBlend;


$squash_start = 0.8 + ( 2- $stretch_start ) *.2;
$squash_mid = 0.8 + ( 2- $stretch_mid ) *.2;

%(start_joint)s.scaleX = $stretch_start;
%(start_joint)s.scaleY = $squash_start;
%(start_joint)s.scaleZ = $squash_start;

%(mid_joint)s.scaleX = $stretch_mid;
%(mid_joint)s.scaleY = $squash_mid;
%(mid_joint)s.scaleZ = $squash_mid;

%(end_joint)s.scaleX = $squash_mid;
%(end_joint)s.scaleY = $squash_mid;
%(end_joint)s.scaleZ = $squash_mid;
"""

EXP_IKFK = \
"""
%(main_ik)s.ikBlend = %(control)s.ikBlend;
%(end_ik)s.ikBlend = %(control)s.orientBlend * %(control)s.ikBlend;
"""

EXP_FOOT_IKFK = \
"""

// -- Foot Roll --
%(toe_ik)s.ikBlend = %(end_ik)s.ikBlend;
"""

EXP_FOOT_IKFK_CONTROLS = \
"""

// -- Foot Roll Controls --
%(heel_pivot_shape)s.visibility = %(end_ik)s.ikBlend;
%(ball_pivot_shape)s.visibility = %(end_ik)s.ikBlend;
%(toe_pivot_shape)s.visibility = %(end_ik)s.ikBlend;
"""

EXP_VIS = \
"""
%(shape1)s.template = abs( %(control)s.ikBlend - 1 );
%(shape2)s.visibility = %(end_ik)s.ikBlend;
"""

class CntlColors:
    left = 6
    right = 3
    center = 1
    head = 8
    tail = 7



def rigLimbCmd( prefix='leg_', suffix=None, side=LEFT_SIDE, hasStretch=False, hasFootRoll=False, footRollMode=FOOTROLL_AUTO ):

    suffix = suffix or ('_l','_r')[side]
    exp_template = ""

    labels = {
        'control'      : prefix + 'control' + suffix,
        'aimControl'   : prefix + 'aim'  + suffix,
        'ik'           : prefix + 'ik' + suffix,
        'ikEnd'        : prefix + 'ik_end' + suffix,
        'expression'   : prefix + 'control' + suffix + '_EXP',

        'guideJointIk' : prefix + 'ik_guide_',
        'guideJoint'   : prefix + 'guide_',
        'ikStretch'    : prefix + 'ik_stretch' + suffix,
        'locStart'     : prefix + 'loc_start' + suffix,
        'locMid'       : prefix + 'loc_mid' + suffix,
        'locEnd'       : prefix + 'loc_end' + suffix,
        'locGuide'     : prefix + 'loc_guide' + suffix,
        'ikGuide'      : prefix + 'ik_guide' + suffix,
    }


    try:
        start_joint, end_joint = pm.ls(sl=1,type="joint")
    except ValueError:
        raise ValueError, "Select the start and end joints to setup."

    mid_joint = end_joint.getParent()
    parent_joint = start_joint.getParent()

    unit_scale = start_joint.getRotatePivot(ws=1)[-1]

    # -- positions and length

    start_point = start_joint.getRotatePivot(ws=1) * unit_scale
    end_point =   end_joint.getRotatePivot(ws=1) * unit_scale
    mid_point =   mid_joint.getRotatePivot(ws=1) * unit_scale
    length =      start_point.distanceTo( end_point )

    # -- Create Control

    control = createNurbsShape( labels['control'], 'sphere', size=length*.2 )
    control2 = createNurbsShape( labels['control'], 'locator', size=length*.3 )
    pm.parent( control2.getShape(), control, r=1, s=1 )
    pm.delete( control2 )
    control.translate.set( end_point )

    pm.makeIdentity( control, apply=True, s=0, r=0, t=1, n=0 )

    control.addAttr( "ikBlend", at='double', k=1, dv=0, min=0, max=1 )
    control.addAttr( "orientBlend", at='double', k=1, dv=0, min=0, max=1 )

    # -- Create Aim Control

    v1 = end_point - start_point
    v2 = mid_point - start_point
    v3 = v1.cross( v2 )
    v4 = v3.cross( v1 )
    aim_point = start_point + ( v4.normal() * length * 1.5 )

    aim_control = createNurbsShape( labels['aimControl'], 'arrow', size=length/5 )
    pm.xform( aim_control, t=aim_point )
    pm.makeIdentity( apply=True, s=0, r=0, t=1, n=0 )

    pm.aimConstraint(  mid_joint, aim_control, weight=1, aimVector=(0, 0, 1) )

    # -- Create Aim Line

    aim_line = pm.curve( name=labels['aimControl']+'_line', d=1, p=[aim_point, mid_point], k=[0, 1] )

    line_cluster0, line_handle0 = pm.cluster( aim_line+'.cv[0]', n=labels['aimControl']+'_line_0', en=1, rel=1 )
    line_cluster1, line_handle1 = pm.cluster( aim_line+'.cv[1]', n=labels['aimControl']+'_line_1', en=1, rel=1 )

    pm.pointConstraint( aim_control, line_handle0, offset=(0,0,0), weight=1 )
    pm.pointConstraint( mid_joint, line_handle1, offset=(0,0,0), weight=1 )

    line_group0 = pm.group( line_handle0, name=line_handle0.name() + "_grp" )
    line_group1 = pm.group( line_handle1, name=line_handle0.name() + "_grp" )

    pm.parent( [aim_line,
                line_group0,
                line_group1,
                aim_control] )

    line_group0.v.set(0)
    line_group1.v.set(0)
    setAttrs( line_group0, ['t','r','s','v'], lock=1 )
    setAttrs( line_group1, ['t','r','s','v'], lock=1 )

    setAttrs( aim_line, ['t','r','s','v'], lock=1 )

    aim_line.overrideEnabled.set(1)
    aim_line.overrideDisplayType.set(1)


    if hasStretch:
        guide_ik_start = pm.duplicate( start_joint, rc=1 )[0]
        guide_ik_mid, guide_ik_end = pm.ls( guide_ik_start, dag=1 )[1:3]

        for n in pm.ls( guide_ik_start, dag=1 ):
            pm.rename( n, labels['guideJointIk'] + n[:-1] )

        guide_start = pm.duplicate( start_joint, rc=1 )[0]
        guide_mid, guide_end = pm.ls( guide_start, dag=1 )[1:3]

        for n in pm.ls( guide_start, dag=1 ):
            pm.rename( n, labels['guideJoint'] + n[:-1] )


        parent_group = pm.group( name=labels['ikStretch'], em=1 )

        if parent_joint is not None:
            parent_group.setRotatePivot( parent_joint.getRotatePivot(ws=1) * unit_scale, ws=1 )
            pm.parentConstraint( parent_joint, parent_group, weight=1 )

        pm.parent( guide_ik_start, guide_start, parent_group )

        # -- build a temp joint chain to get loc_mid position

        loc_start = pm.group( n=labels['locStart'], em=1 )

        pm.parent( loc_start, parent_group )


        loc_start.setRotatePivot( start_joint.getRotatePivot( ws=1) * unit_scale, ws=1 )

        pm.aimConstraint( control, loc_start, weight=1, aimVector=(1,0,0) )

        loc_end = pm.group( n=labels['locEnd'], em=1, parent=loc_start )
        loc_end.setRotatePivot( start_joint.getRotatePivot( ws=1) * unit_scale, ws=1 )

        pm.pointConstraint( control, loc_end, offset=(0,0,0), skip=('y','z'), weight=1 )


        pm.select(cl=1)
        temp_start = pm.joint( p=start_point )
        temp_end = pm.joint( p=end_point )
        pm.joint( temp_start, edit=1, oj='xyz', secondaryAxisOrient='yup', ch=1 )
        pm.pointConstraint( mid_joint, temp_end, offset=(0,0,0), skip=('y','z'), weight=1 )

        loc_mid_point =   temp_end.getRotatePivot(ws=1) * unit_scale
        pm.delete( temp_start )

        # -- create the mid locator

        loc_mid = pm.group( n=labels['locMid'], em=1)#spaceLocator()
        loc_mid.translate.set( loc_mid_point )
        pm.makeIdentity( apply=True, s=0, r=0, t=1, n=0 )

        pm.pointConstraint( loc_start, loc_mid, mo=1, weight=1 )
        pm.pointConstraint( loc_end,   loc_mid, mo=1, weight=1 )

        # -- create the guide locator

        loc_guide = pm.group( n=labels['locGuide'], em=1)

        guide_constraint = pm.pointConstraint( loc_mid, loc_guide, offset=(0,0,0), weight=1 )
        pm.pointConstraint( guide_ik_mid, loc_guide, offset=(0,0,0), weight=1 )

        pm.parent( loc_mid, loc_guide, parent_group )

        guide_ik, guide_ee = pm.ikHandle( sj=guide_ik_start, ee=guide_ik_end, solver="ikRPsolver", dh=1 )
        pm.poleVectorConstraint( aim_control, guide_ik, weight=1 )
        pm.delete( guide_ik_end )

        pm.rename( guide_ik, labels['ikGuide'] )

        # -- SET STRETCH BLEND START

        guide_ik.addAttr( "stretchStart", at='double', k=1 )
        guide_ik.stretchStart.set( loc_end.tx.get() )

        # -- SET STRETCH BLEND END

        guide_ik.addAttr( "stretchEnd", at='double', k=1 )
        guide_ik.stretchEnd.set( loc_end.tx.get()*1.1 )

        # -- SET STRETCH BLEND END

        guide_ik.addAttr( "stretchFactor", at='double', k=1 )
        guide_ik.stretchFactor.set( 0.22 )


        # -- setup guide joints

        pm.aimConstraint( loc_guide, guide_start, weight=1, aimVector=(1,0,0) )
        pm.aimConstraint( loc_end, guide_mid, weight=1, aimVector=(1,0,0) )

        pm.pointConstraint( loc_guide, guide_mid, offset=(0,0,0), skip=('y','z'), weight=1 )
        pm.pointConstraint( loc_end, guide_end, offset=(0,0,0), skip=('y','z'), weight=1 )

        pm.parent( guide_ik, loc_end )
        pm.parent( guide_ik, control )

        # -- add stretch addtributes

        start_joint.addAttr( "stretch", at='double', k=1, dv=0 )
        mid_joint.addAttr( "stretch", at='double', k=1, dv=0 )


        control.addAttr( "stretchBlend", at='double', k=1, dv=0, min=0, max=1 )

        # -- build the expression

        exp_template += EXP_STRETCH \
        % { 'guide_ik'     : guide_ik,
            'loc_end'      : loc_end,
            'constraint'   : guide_constraint,

            # -- we only need these names for the constraint attribute names

            'guide_ik_mid' : guide_ik_mid.split('|')[-1],
            'loc_mid'      : loc_mid.split('|')[-1],

            'control'      : control,
            'start_joint'  : start_joint,
            'mid_joint'    : mid_joint,
            'end_joint'    : end_joint,
            'guide_mid'    : guide_mid,
            'guide_end'    : guide_end,
            }

        # -- make things look pretty

        for n in pm.ls( [ parent_group, guide_ik ], dag=1 ):
            n.visibility.set(0)

        for obj in guide_end.getChildren( type='joint' ):
            try:
                pm.delete( obj )
            except:
                pass


    # -- hook up the original joints

    main_ik, main_ee = pm.ikHandle( sj=start_joint, ee=end_joint, solver="ikRPsolver", dh=1 )
    pm.poleVectorConstraint( aim_control, main_ik, weight=1 )
    pm.rename( main_ik, labels['ik'] )

    end_ik, end_ee = pm.ikHandle( sj=end_joint, ee=end_joint.getChildren(type='joint')[0], solver="ikRPsolver", dh=1 )
    pm.rename( end_ik, labels['ikEnd'] )

    pm.parent( main_ik, end_ik, control )

    # -- fill out the expression template
    exp_template += EXP_IKFK + EXP_VIS

    exp_str = exp_template \
    % {
        #'guide_ik'     : guide_ik,
        #'loc_end'      : loc_end,
        #'constraint'   : guide_constraint,

        #we only need these names for the constraint attribute names
        #'guide_ik_mid' : guide_ik_mid.split('|')[-1],
        #'loc_mid'      : loc_mid.split('|')[-1],

        'control'      : control,
        'start_joint'  : start_joint,
        'mid_joint'    : mid_joint,
        'end_joint'    : end_joint,
        #'guide_mid'    : guide_mid,
        #'guide_end'    : guide_end,
        'main_ik'      : main_ik,
        'end_ik'       : end_ik,

        'shape1'       : control.getChildren(type="nurbsCurve")[0],
        'shape2'       : control.getChildren(type="nurbsCurve")[1],
        }

    pm.expression( s=exp_str, o=control, n=labels['expression'], a=1, uc='all' )

    if hasFootRoll:
        rigFootRoll( end_joint, control, prefix, suffix, side=side, footRollMode=footRollMode )

    resetIkSetupCmd(end_joint, control)
    resetIkSetupCmd(start_joint, aim_control)

    # -- make things look pretty

    for n in pm.ls( control, dag=1, type="transform" )[1:]:
        if n.type() != "transform":
            n.visibility.set(0)

    setAttrs( control, ['sx','sy','sz'], channelBox=0, keyable=0, lock=1 )
    setAttrs( aim_control, ['rx','ry','rz','sx','sy','sz'], channelBox=0, keyable=0, lock=1 )
    pm.setAttr(control.v, keyable=0 )
    pm.setAttr(aim_control.v, keyable=0 )

    addToSet( [control, aim_control], 'controlsSet' )

    pm.select( [control, aim_control], r=1 )
    pm.color( ud=(CntlColors.left, CntlColors.right)[side] )

    control.displayHandle.set(1)
    pm.select( control, r=1 )

    pm.reorder( control.getShape(), back=1 )

    return [ control, aim_control ]


def rigFootRoll( foot_joint, control, prefix, suffix=None, side=LEFT_SIDE, footRollMode=FOOTROLL_AUTO ):

    suffix = suffix or ('_l','_r')[side]
    exp_template = ""

    labels = {
        'expression'   : prefix + 'control' + suffix + '_EXP',
        'ikToe'        : prefix + 'ik_toe' + suffix,
        'pivotBall'    : prefix + 'pivot_ball' + suffix,
        'pivotToe'     : prefix + 'pivot_toe' + suffix,
        'rotateToe'    : prefix + 'rotate_toe' + suffix,
        'pivotHeel'    : prefix + 'pivot_heel' + suffix,
    }

    handles = control.getChildren(type='ikHandle')
    if len(handles) == 3:
        guide_ik, main_ik, end_ik = handles
    else:
        main_ik, end_ik = handles
        guide_ik = None

    toe_joint, heel_joint = foot_joint.getChildren( type='joint' )[:2]
    end_joint = toe_joint.getChildren( type='joint' )[0]

    toe_length = toe_joint.translate.get().length()
    heel_length = heel_joint.translate.get().length()


    pm.select( toe_joint, end_joint, r=1 )
    toe_ik, toe_ee = pm.ikHandle( name=labels['ikToe'], sol='ikRPsolver', dh=1 )

    # -- add pivot groups

    pivot_ball = createNurbsShape( labels['pivotBall'], shape='U', size=toe_length )
    pivot_ball.translate.set( toe_joint.getRotatePivot(ws=1)/100 )
    pivot_ball.ty.set( pivot_ball.ty.get() + toe_length/2 )
    pivot_ball.rotate.set(-90,90,0)
    pm.makeIdentity(pivot_ball, apply=True, translate=True, rotate=True, scale=True)
    pivot_ball.setRotatePivot( toe_joint.getRotatePivot(ws=1), ws=1 )

    if guide_ik:
        pm.parent( main_ik, guide_ik, pivot_ball )
    else:
        pm.parent( main_ik, pivot_ball )


    pivot_toe = createNurbsShape( labels['pivotToe'], shape='U', size=toe_length  )
    pivot_toe.translate.set( end_joint.getRotatePivot(ws=1)/100 )
    pm.makeIdentity(pivot_toe, apply=True, translate=True, rotate=True, scale=True)

    pm.parent( pivot_ball, end_ik, pivot_toe )

    rotate_toe = pm.group( toe_ik, n=labels['rotateToe'] )
    rotate_toe.setRotatePivot( toe_joint.getRotatePivot(ws=1), ws=1 )

    pivot_heel = createNurbsShape( labels['pivotHeel'], shape='U', size=heel_length  )
    pivot_heel.translate.set( heel_joint.getRotatePivot(ws=1)/100 )
    pivot_heel.ry.set(180)
    pm.makeIdentity(pivot_heel, apply=True, translate=True, rotate=True, scale=True)

    pm.parent( pivot_toe, rotate_toe, pivot_heel )

    pm.parent( pivot_heel, control )


    exp_str = pm.expression( labels['expression'], query=1, s=1 )

    # -- fill out the expression template

    exp_template += EXP_FOOT_IKFK

    exp_str += exp_template \
    % {
        'toe_ik'      : toe_ik,
        'end_ik'       : end_ik
        }


    if footRollMode == FOOTROLL_AUTO:

        control.addAttr( "footRoll",  sn="fr", at='double', k=1, dv=0, min=-10, max=20 )
        control.addAttr( "toeRotate", sn="tr", at='double', k=1, dv=0 )

        control.tr >> rotate_toe.rx

        # -- Set Driven Keys

        pm.setDrivenKeyframe( pivot_toe.rx, cd=control.fr,  dv=10,  v=0,   ott='linear' )
        pm.setDrivenKeyframe( pivot_toe.rx, cd=control.fr,  dv=20,  v=60, itt='linear' )

        pm.setDrivenKeyframe( pivot_ball.rx, cd=control.fr, dv=0,   v=0,   ott='linear' )
        pm.setDrivenKeyframe( pivot_ball.rx, cd=control.fr, dv=10,  v=60, itt='linear' )
        pm.setDrivenKeyframe( pivot_ball.rx, cd=control.fr, dv=20,  v=0, itt='linear' )

        pm.setDrivenKeyframe( pivot_heel.rx, cd=control.fr, dv=0,   v=0,   ott='linear' )
        pm.setDrivenKeyframe( pivot_heel.rx, cd=control.fr, dv=-10, v=-40,  itt='linear' )


    elif footRollMode == FOOTROLL_CONTROLS:

        for obj in pm.ls( control, dag=1, type="nurbsCurve" ):
            addToSet( [obj.getParent()], 'controlsSet' )

        exp_template += EXP_FOOT_IKFK

        exp_str += EXP_FOOT_IKFK_CONTROLS \
        % {
            'heel_pivot_shape'  : pivot_heel.getShape(),
            'ball_pivot_shape'  : pivot_ball.getShape(),
            'toe_pivot_shape'   : pivot_toe.getShape(),
            'end_ik'            : end_ik
            }

    else: #footRollMode == FOOTROLL_ATTRIBUTES

        control.addAttr( "heelPivot", sn="hp", at='double', k=1, dv=0 )
        control.addAttr( "ballPivot", sn="bp", at='double', k=1, dv=0 )
        control.addAttr( "toePivot",  sn="tp", at='double', k=1, dv=0 )
        control.addAttr( "toeRotate", sn="tr", at='double', k=1, dv=0 )

        control.hp >> pivot_heel.rx
        control.bp >> pivot_ball.rx
        control.tp >> pivot_toe.rx
        control.tr >> rotate_toe.rx


    for obj in pm.ls( control, dag=1, type="transform" ):
        shape = obj.getShape()

        if shape is not None:
            pm.reorder(shape, back=1)

        if obj != control:
            setAttrs( obj, ['t','s'], channelBox=0, keyable=0, lock=1 )
            if footRollMode != FOOTROLL_CONTROLS:
                setAttrs( obj, ['r'], channelBox=1, keyable=0, lock=0 )
                obj.visibility.set(0)

        obj.v.set( channelBox=0, keyable=0 )
        pm.select( obj, r=1 )
        pm.color( ud=(CntlColors.left, CntlColors.right)[side] )


    pm.expression( labels['expression'], edit=1, s=exp_str )



def rigRootCmd( prefix='root_', seperate_rotation=False, rotate_prefix='pelvis_' ):

    labels = {
        'control' : prefix + 'control',
        'rotateControl' : rotate_prefix + 'control'
    }

    try:
        start_joint = pm.ls(sl=1,type="joint")[0]
    except ValueError:
        raise ValueError, "Select the root joint to setup."


    start_point = start_joint.getRotatePivot(ws=1) * start_joint.getRotatePivot(ws=1)[-1]

    control = pm.circle( n=labels['control'], radius=(start_point[1] / .035), normal=(0,1,0), ch=0 )[0]
    control2 =  createNurbsShape( labels['rotateControl'],
                                  width=( start_point[1] / .025),
                                  height=(start_point[1] / .045),
                                  depth=( start_point[1] / .035),
                                  )

    control.translate.set( start_point )
    control2.translate.set( start_point )

    if not seperate_rotation:
        pm.parent( control2.getShape(), control, r=1, s=1 )
        pm.delete( control2 )
    else:
        pm.parent( control2, control )
        pm.makeIdentity( control2, apply=True, s=0, r=0, t=1, n=0 )

    pm.makeIdentity( control, apply=True, s=0, r=0, t=1, n=0 )


    pm.pointConstraint(  control, start_joint, offset=(0,0,0), weight=1 )

    if not seperate_rotation:
        pm.orientConstraint( control, start_joint, weight=1, mo=1 )
    else:
        pm.orientConstraint( control2, start_joint, weight=1, mo=1 )


    control.displayHandle.set(1)
    addToSet( [control], 'controlsSet' )

    setAttrs( control, ['sx','sy','sz'], channelBox=0, keyable=0, lock=1 )
    pm.setAttr(control.v, keyable=0 )

    pm.select( control, r=1 )
    pm.color( ud=CntlColors.center )

    pm.reorder( control.getShape(), back=1 )

    if seperate_rotation:
        addToSet( [control2], 'controlsSet' )

        setAttrs( control2, ['t','s'], channelBox=0, keyable=0, lock=1 )
        pm.setAttr(control2.v, keyable=0 )

        pm.select( control2, add=1 )
        pm.color( ud=CntlColors.center )


    return pm.ls(sl=1)



EXP_SPINE = \
"""
%(main_ik)s.twist = %(main_ik)s.roll = %(control)s.ry * .5;
%(main_ik)s.ikBlend = %(control)s.ikBlend;

%(shape)s.template = abs( %(control)s.ikBlend - 1 );
%(mid_shape)s.template = abs( %(control)s.ikBlend - 1 );
"""

EXP_SPINE_STRETCH = \
"""
//spine_1.scaleY = %(control)s.stretch;
//spine_2.scaleY = %(control)s.stretch;

$stretch = 1 + ( smoothstep( -1, 1, %(control)s.stretch ) - 0.5 ) * 1.7;
$inv = 1 - ( ($stretch-1)*.5 );

%(start_joint)s.scaleX = $stretch;
%(start_joint)s.scaleY = $inv;
%(start_joint)s.scaleZ = $inv;

%(mid_joint)s.scaleX = $stretch;
%(mid_joint)s.scaleY = $inv;
%(mid_joint)s.scaleZ = $inv;

//%(parent_joint)s.scaleY = 1;
%(parent_joint)s.scaleX = $inv;
%(parent_joint)s.scaleZ = $inv;
"""


def rigSpineCmd( prefix='spine_', suffix='', hasStretch=False, worldSpace=False ):

    exp_template = ''

    labels = {
        'end_control' : prefix + 'control_end' + suffix,
        'mid_control' : prefix + 'control_mid' + suffix,
        'ik'          : prefix + 'ik' + suffix,
        'curve'       : prefix + 'curve' + suffix,
        'cluster'     : prefix + 'cluster' + suffix,
        'clusters'    : prefix + 'clusters' + suffix,
        'parent'      : prefix + 'parent' + suffix,
        'expression'  : prefix + 'controls' + suffix + '_EXP',
    }

    try:
        start_joint, end_joint = pm.ls(sl=1,type="joint")
    except ValueError:
        raise ValueError, "Select the start and end joints to setup."

    parent_joint = start_joint.getParent()
    mid_joint = start_joint.getChildren(type='joint')[0]

    if parent_joint is None:
        raise ValueError, "Start joint must have a parent transform."

    main_ik, main_ee, main_curve = pm.ikHandle( n=labels['ik'],
                                             sj=start_joint,
                                             ee=end_joint,
                                             sol='ikSplineSolver',
                                             pcv=True,
                                             numSpans=1,
                                             dh=1
                                             )

    main_curve.rename( labels['curve'] )

    cluster0, handle0 = pm.cluster( main_curve+'.cv[0]', main_curve+'.cv[1]',
                                 n=labels['cluster']+'0', en=1, rel=1
                                 )
    cluster1, handle1 = pm.cluster( main_curve+'.cv[1]', main_curve+'.cv[2]',
                                 n=labels['cluster']+'1', en=1, rel=1
                                 )
    cluster2, handle2 = pm.cluster( main_curve+'.cv[4]',
                                 n=labels['cluster']+'2', en=1, rel=1
                                 )


    start_point = start_joint.getRotatePivot(ws=1) * start_joint.getRotatePivot(ws=1)[-1]
    end_point = end_joint.getRotatePivot(ws=1) * end_joint.getRotatePivot(ws=1)[-1]
    handle1_point = handle1.getRotatePivot(ws=1) * handle1.getRotatePivot(ws=1)[-1]
    length = start_point.distanceTo( end_point )

    # -- build controls

    control = pm.circle( n=labels['end_control'], radius=(length / 2), normal=(0,1,0), ch=0 )[0]
    control.translate.set( end_point )
    control.rotateOrder.set(1)

    mid_control = pm.circle( n=labels['mid_control'], radius=(length / 2), normal=(0,1,0), ch=0 )[0]
    mid_control.translate.set( handle1_point )

    pm.makeIdentity( [ control, mid_control ], apply=True, s=0, r=0, t=1, n=0 )

    # -- add control attributes

    control.addAttr( "ikBlend", at='double', k=1, dv=0, min=0, max=1 )


    # -- constrain controls

    pm.pointConstraint( control, handle2, offset=(0,0,0), weight=1 )
    pm.aimConstraint( handle1, control, weight=1, aimVector=(0,-1,0), skip='y' )

    pm.pointConstraint( mid_control, handle1, offset=(0,0,0), weight=1 )
    pm.aimConstraint( handle0, mid_control, weight=1, aimVector=(0,1,0) )

    if worldSpace:
        pm.pointConstraint( parent_joint, handle0, maintainOffset=1, weight=1 )


    # -- group and parent nodes

    cluster_group = pm.group( handle0, handle1, handle2, name=labels['clusters'] )

    parent_group = pm.group( name=labels['parent'], em=1 )
    parent_group.rotatePivot.set( parent_joint.getRotatePivot(ws=1) )

    pm.parent( control, mid_control, main_ik, main_curve, cluster_group, parent_group )
    if not worldSpace:
        pm.parentConstraint( parent_joint, parent_group, w=1, mo=1 )


    if hasStretch:
        control.addAttr( "stretch", at='double', k=1, dv=0, min=-1, max=1 )
        exp_template += EXP_SPINE_STRETCH


    exp_template += EXP_SPINE

    exp_str = exp_template \
    % { 'control'      : control,
        'start_joint'  : start_joint,
        'end_joint'    : end_joint,
        'mid_joint'    : mid_joint,
        'parent_joint' : parent_joint,
        'main_ik'      : main_ik,

        'shape'        : control.getShape(),
        'mid_shape'    : mid_control.getShape(),
        }

    pm.expression( s=exp_str, o=control, n=labels['expression'], a=1, uc='all' )

    resetIkSetupCmd(end_joint, control)

    # -- make things look pretty

    for n in pm.ls( [main_ik, main_curve, cluster_group], dag=1, type="transform" ):
        n.visibility.set(0)

    addToSet( [control, mid_control], 'controlsSet' )
    control.displayHandle.set(1)

    setAttrs( control, ['rx','rz','sx','sy','sz'], channelBox=0, keyable=0, lock=1 )
    setAttrs( mid_control, ['rx','ry','rz','sx','sy','sz'], channelBox=0, keyable=0, lock=1 )
    pm.setAttr(control.v, keyable=0 )
    pm.setAttr(mid_control.v, keyable=0 )

    pm.color( ud=CntlColors.center )

    pm.select( control, r=1 )

    return [ control, mid_control ]


EXP_HEAD_STRETCH = \
"""
$stretch = smoothstep( -1.5, 1.5, %(control)s.stretch ) + 0.5;
$inv = 2 - $stretch;

head.scaleX = $stretch;
head.scaleY = $inv;
head.scaleZ = $inv;

head.translateX = .166 - (1-head.scaleY)*.2;
"""

EXP_HEAD = \
"""
%(pivot)s.blendAim1 = %(control)s.aimBlend * %(control)s.ikBlend;
%(main_ik)s.ikBlend = %(control)s.ikBlend;


%(shape)s.template = abs( %(control)s.ikBlend - 1 );
"""


def rigHeadCmd( prefix='head_', suffix='', hasStretch=True ):

    exp_template = EXP_HEAD

    labels = {
        'control'     : prefix + 'control' + suffix,
        'aimControl'  : prefix + 'aim' + suffix,
        'ik'          : prefix + 'ik' + suffix,
        'ikEnd'       : prefix + 'ik_end' + suffix,
        'parent'      : prefix + 'parent' + suffix,
        'expression'  : prefix + 'control' + suffix + '_EXP',
        'parent'      : prefix + 'parent' + suffix,
        'pivot'       : prefix + 'pivot' + suffix,
    }

    try:
        start_joint = pm.ls(sl=1,type="joint")[0]
    except ValueError:
        raise ValueError, "Select the root joint to setup."

    end_joint = start_joint.getChildren(type='joint')[0]
    neck_joint = start_joint.getParent()
    parent_joint = neck_joint.getParent()

    if neck_joint is None:
        raise ValueError, "Start joint must have a parent joint (neck)."
    if parent_joint is None:
        raise ValueError, "Start joint parent must have a parent transform (spine)."


    unit_scale = start_joint.getRotatePivot(ws=1)[-1]
    start_point = start_joint.getRotatePivot(ws=1) * unit_scale
    end_point = end_joint.getRotatePivot(ws=1) * unit_scale

    mid_point = ( start_point + end_point ) / 2
    length = start_point.distanceTo( end_point )

    aim_point = Vector( start_point[0], start_point[1], start_point[1])*100

    # -- build controls

    control = createNurbsShape( labels['control'], width=length, height=length*1.2, depth=length*1.1 )
    control.translate.set( mid_point )
    pm.makeIdentity( control, apply=True, t=1 )
    control.rotatePivot.set( start_joint.getRotatePivot(ws=1) * unit_scale )
    control.scalePivot.set( start_joint.getRotatePivot(ws=1) * unit_scale )
    control.selectHandle.set( start_joint.getRotatePivot(ws=1) * unit_scale )

    control.addAttr( "ikBlend", at='double', k=1, dv=0, min=0, max=1 )
    control.addAttr( "aimBlend", at='double', k=1, dv=0, min=0, max=1 )

    # -- build aim control

    aim_control = createNurbsShape( labels['aimControl'], 'arrow', size=length/1.5 )
    aim_control.translate.set( aim_point )
    pm.makeIdentity( aim_control, apply=True, t=1 )

    pm.aimConstraint(  start_joint, aim_control, weight=1, aimVector=(0, 0, 1) )

    # -- Create Aim Line

    aim_line = pm.curve( name=labels['aimControl']+'_line', d=1, p=[aim_point, mid_point], k=[0, 1] )

    line_cluster0, line_handle0 = pm.cluster( aim_line+'.cv[0]', n=labels['aimControl']+'_line_0', en=1, rel=1 )
    line_cluster1, line_handle1 = pm.cluster( aim_line+'.cv[1]', n=labels['aimControl']+'_line_1', en=1, rel=1 )

    pm.pointConstraint( aim_control, line_handle0, offset=(0,0,0), weight=1 )
    pm.pointConstraint( start_joint, line_handle1, offset=(0,0,0), weight=1 )

    line_group0 = pm.group( line_handle0, name=line_handle0.name() + "_grp" )
    line_group1 = pm.group( line_handle1, name=line_handle0.name() + "_grp" )

    pm.parent( [aim_line,
                line_group0,
                line_group1,
                aim_control] )

    line_group0.v.set(0)
    line_group1.v.set(0)
    setAttrs( line_group0, ['t','r','s','v'], lock=1 )
    setAttrs( line_group1, ['t','r','s','v'], lock=1 )

    setAttrs( aim_line, ['t','r','s','v'], lock=1 )

    aim_line.overrideEnabled.set(1)
    aim_line.overrideDisplayType.set(1)

    # -- build helper groups

    pivot_grp = pm.group( n=labels['pivot'], em=1 )
    parent_grp = pm.group( pivot_grp, n=labels['parent'] )
    parent_grp.translate.set( control.getRotatePivot(ws=1) * unit_scale )
    pm.makeIdentity( parent_grp, apply=True, t=1 )

    pivot_grp.rotateOrder.set(2)

    # -- create ik handles

    main_ik, main_ee = pm.ikHandle( n=labels['ik'],  sj=neck_joint, ee=end_joint, sol='ikRPsolver', dh=1 )
    #main_ik, main_ee = pm.ikHandle( n=labels['ik'],  sj=neck_joint, ee=start_joint, sol='ikRPsolver', dh=1 )
    #end_ik, end_ee = pm.ikHandle( n=labels['ikEnd'], sj=start_joint, ee=end_joint, sol='ikSCsolver', dh=1 )

    pm.parent( main_ik, control )
    pm.parent( control, pivot_grp )

    # -- set up constraints

    #pm.aimConstraint( control, aim_control, weight=1, aimVector=(0, 0, -1), mo=1 )
    pm.aimConstraint( aim_control, pivot_grp, weight=1, aimVector=(0, 0, 1), mo=1 )
    pm.setKeyframe( pivot_grp.r )

    pm.parentConstraint( parent_joint, parent_grp, weight=1, mo=1 )


    resetIkSetupCmd(start_joint, control)
    resetIkSetupCmd(start_joint, aim_control)


    exp_str = exp_template \
    % { 'control'      : control,
        'start_joint'  : start_joint,
        'end_joint'    : end_joint,
        'parent_joint' : parent_joint,
        'main_ik'      : main_ik,
        #'end_ik'       : end_ik,

        'pivot'        : pivot_grp,
        'shape'        : control.getShape(),
        }

    pm.expression( s=exp_str, o=control, n=labels['expression'], a=1, uc='all' )

    # -- make things look pretty

    for n in pm.ls( [main_ik], dag=1, type="transform" ):
        n.visibility.set(0)

    control.displayHandle.set(1)
    addToSet( [control, aim_control], 'controlsSet' )

    setAttrs( control, ['sx','sy','sz'], channelBox=0, keyable=0, lock=1 )
    setAttrs( aim_control, ['rx','ry','rz','sx','sy','sz'], channelBox=0, keyable=0, lock=1 )
    pm.setAttr(control.v, keyable=0 )
    pm.setAttr(aim_control.v, keyable=0 )

    pm.select( [control,aim_control], r=1 )

    pm.color( ud=CntlColors.head )


    return [ control, aim_control ]


def rigParentControl( joint_name ):

    jnt = pm.nt.Transform(joint_name)
    grp = pm.group(name="%s_parent"%jnt, em=True)
    pm.parent(grp, joint_name)
    grp.t.set([0,0,0])
    grp.r.set([0,0,0])
    pm.parent(grp, world=1)

    try:
        rig, rig_type = pm.ls('rig',showType=1)
    except:
        rig, rig_type = (None, None)

    if rig_type == 'transform':
        pm.parent(grp,rig)

    pm.parentConstraint( jnt.getParent(), grp, mo=1, w=1)
    grp.t.lock()
    grp.r.lock()
    grp.s.lock()

    control = createNurbsShape("%s_control"%jnt,"cube",width=0.5, height=0.5, depth=0.5)
    addToSet( [control], 'controlsSet' )

    pm.parent(control,grp)
    control.t.set([0,0,0])
    control.r.set([0,0,0])
    control.displayHandle.set(1)

    pm.parentConstraint( control, jnt, mo=1, w=1)

    pm.select( control, r=1 )

    return [ control ]



def rigDigit( joint_name, name=None, suffix=None ):

    joint_name_split = joint_name.split('_')

    if name is None:
        name = joint_name_split[0]

    if suffix is None:
        if len(joint_name_split) >= 2:
            suffix = '_' + joint_name_split[-1]
        else:
            suffix = ''

    control_name = "_".join([name,'control'])
    if suffix != '':
        control_name += suffix


    pm.select(joint_name, r=1)
    joints = pm.ls(sl=1,dag=1,type='joint')[:-1]


    size = joints[1].tx.get()


    grp = pm.group( name="%s_parent" % name, em=True)
    pm.parent(grp, joints[0])
    grp.t.set([0,0,0])
    grp.r.set([0,0,0])
    pm.parent(grp, world=1)

    try:
        rig, rig_type = pm.ls('rig',showType=1)
    except:
        rig, rig_type = (None, None)

    if rig_type == 'transform':
        pm.parent(grp,rig)

    pm.parentConstraint( joints[0].getParent(), grp, mo=1, w=1)
    grp.t.lock()
    grp.r.lock()
    grp.s.lock()

    control = createNurbsShape( control_name, "triangle", size=size )
    addToSet( [control], 'controlsSet' )

    pm.parent(control,grp)
    control.t.set([0,size/2,0])
    control.r.set([0,30,0])
    control.displayHandle.set(1)
    pm.setAttr(control.displayHandle, keyable=0, channelBox=1 )

    pm.makeIdentity( apply=True, s=1, r=1, t=1, n=0 )
    control.setRotatePivot( joints[0].getRotatePivot(ws=1), ws=1 )

    control.selectHandle.set( [0,size/2,0] )

    setAttrs( control, ['t','s'], channelBox=0, keyable=0, lock=1 )
    pm.setAttr(control.v, keyable=0, channelBox=0 )


    for idx, joint in enumerate(joints[1:]):
        attr_name = "rotate_%s" % (idx+2)
        attr = control.addAttr( attr_name, at='double', k=1, dv=0 )
        pm.connectAttr( "%s.%s" % (control,attr_name) , joint.rz )

    pm.parentConstraint( control, joints[0], mo=1, w=1, skipTranslate=['x','y','z'])

    pm.select( control, r=1 )

    return [ control ]

