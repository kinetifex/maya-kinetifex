

import pymel.core as pm

from kinetifex import rigging



def setupStretchyIk( name="leg" ):

    try:
        start_joint, end_joint = pm.ls(sl=1,type="joint")
    except ValueError:
        raise ValueError, "Select the start and end joints to setup."

    mid_joint = end_joint.getParent()
    parent_joint = start_joint.getParent()

    guide_ik_start = pm.duplicate( start_joint, rc=1 )[0]
    guide_ik_mid, guide_ik_end = pm.ls( guide_ik_start, dag=1 )[1:3]

    for n in pm.ls( guide_ik_start, dag=1 ):
        pm.rename( n, name+'_guide_ik_%s' % n[:-1] )

    guide_start = pm.duplicate( start_joint, rc=1 )[0]
    guide_mid, guide_end = pm.ls( guide_start, dag=1 )[1:3]

    for n in pm.ls( guide_start, dag=1 ):
        pm.rename( n, name+'_guide_%s' % n[:-1] )

    #positions and length
    start_point = start_joint.getRotatePivot(ws=1) * start_joint.getRotatePivot(ws=1)[-1]
    end_point =   end_joint.getRotatePivot(ws=1)   * end_joint.getRotatePivot(ws=1)[-1]
    length =      start_point.distanceTo( end_point )


    #Create Control
    control = rigging.createNurbsShape( "%s_control" % name, width=length*.2, height=length*.2, depth=length*.2 )
    control.translate.set( end_point / end_point[-1] )
    pm.makeIdentity( apply=True, s=0, r=0, t=1, n=0 )


    parent_group = pm.group( name='%s_stretch_ik' % name, em=1 )

    if parent_joint is not None:
        parent_group.setRotatePivot( parent_joint.getRotatePivot(ws=1), ws=1 )
        pm.parentConstraint( parent_joint, parent_group, weight=1 )

    pm.parent( guide_ik_start, guide_start, parent_group )



    #build a temp joint chain to get loc_mid position
    loc_start = pm.group( n="%s_loc_start" % name, em=1 )


    pm.parent( loc_start, parent_group )


    loc_start.setRotatePivot( start_joint.getRotatePivot( ws=1), ws=1 )

    pm.aimConstraint( control, loc_start, weight=1, aimVector=(1,0,0) )

    loc_end = pm.group( n="%s_loc_end" % name, em=1, parent=loc_start )
    loc_end.setRotatePivot( start_joint.getRotatePivot( ws=1), ws=1 )

    pm.pointConstraint( control, loc_end, offset=(0,0,0), skip=('y','z'), weight=1 )


    pm.select(cl=1)
    temp_start = pm.joint( p=start_point )
    temp_end = pm.joint( p=end_point )
    pm.joint( temp_start, edit=1, oj='xyz', secondaryAxisOrient='yup', ch=1 )
    pm.pointConstraint( mid_joint, temp_end, offset=(0,0,0), skip=('y','z'), weight=1 )

    mid_point =   temp_end.getRotatePivot(ws=1)
    pm.delete( temp_start )



    #create the mid locator
    loc_mid = pm.group( n="%s_loc_mid" % name, em=1)#spaceLocator()
    loc_mid.translate.set( mid_point )
    pm.makeIdentity( apply=True, s=0, r=0, t=1, n=0 )

    pm.pointConstraint( loc_start, loc_mid, mo=1, weight=1 )
    pm.pointConstraint( loc_end,   loc_mid, mo=1, weight=1 )

    #create the guide locator
    loc_guide = pm.group( n="%s_loc_guide" % name, em=1)

    guide_constraint = pm.pointConstraint( loc_mid, loc_guide, offset=(0,0,0), weight=1 )
    pm.pointConstraint( guide_ik_mid, loc_guide, offset=(0,0,0), weight=1 )

    pm.parent( loc_mid, loc_guide, parent_group )

    guide_ik, guide_ee = pm.ikHandle( sj=guide_ik_start, ee=guide_ik_end )
    pm.delete( guide_ik_end)

    pm.rename( guide_ik, "%s_guide_ik" % name )
    pm.rename( guide_ee, "%s_guide_effector" % name )


    #SET STRETCH BLEND START
    guide_ik.addAttr( "stretchStart", at='double', k=1 )
    guide_ik.stretchStart.set( loc_end.tx.get() )

    #SET STRETCH BLEND END
    guide_ik.addAttr( "stretchEnd", at='double', k=1 )
    guide_ik.stretchEnd.set( loc_end.tx.get()*1.1 )

    #SET STRETCH BLEND END
    guide_ik.addAttr( "stretchFactor", at='double', k=1 )
    guide_ik.stretchFactor.set( 1 )


    #hook up the original joints
    main_ik, main_ee = pm.ikHandle( sj=start_joint, ee=end_joint )
    pm.rename( main_ik, "%s_ik" % name )
    pm.rename( main_ee, "%s_effector" % name )


    pm.parent( guide_ik, loc_end )
    pm.parent( main_ik, guide_ik, control )


    #add stretch addtributes
    start_joint.addAttr( "stretch", at='double', k=1, dv=1 )
    mid_joint.addAttr( "stretch", at='double', k=1, dv=1 )

    control.addAttr( "stretchBlend", at='double', k=1, dv=1 )


    #setup guide joints
    pm.aimConstraint( loc_guide, guide_start, weight=1, aimVector=(1,0,0) )
    pm.aimConstraint( loc_end, guide_mid, weight=1, aimVector=(1,0,0) )

    pm.pointConstraint( loc_guide, guide_mid, offset=(0,0,0), skip=('y','z'), weight=1 )
    pm.pointConstraint( loc_end, guide_end, offset=(0,0,0), skip=('y','z'), weight=1 )



    #build the expression
    exp_str = \
"""
$stretch_blend = linstep( %(guide_ik)s.stretchStart, %(guide_ik)s.stretchEnd, %(loc_end)s.tx);
%(constraint)s.%(loc_mid)sW0 = $stretch_blend;
%(constraint)s.%(guide_ik_mid)sW1 = 1-$stretch_blend;

%(start_joint)s.scaleX =  %(start_joint)s.stretch +
    ( abs( %(guide_mid)s.translateX ) - abs( %(mid_joint)s.translateX ) ) *
    %(guide_ik)s.stretchFactor * %(control)s.stretchBlend;

%(mid_joint)s.scaleX = %(mid_joint)s.stretch +
    ( abs( %(guide_end)s.translateX ) - abs( %(end_joint)s.translateX ) ) *
    %(guide_ik)s.stretchFactor * %(control)s.stretchBlend;
""" \
% { 'guide_ik'      : guide_ik,
    'loc_end'       : loc_end,
    'constraint'    : guide_constraint,

    #we only need these names for the constraint attribute names
    'guide_ik_mid'  : guide_ik_mid.split('|')[-1],
    'loc_mid'       : loc_mid.split('|')[-1],

    'control'       : control,
    'start_joint'   : start_joint,
    'mid_joint'     : mid_joint,
    'end_joint'     : end_joint,
    'guide_mid'     : guide_mid,
    'guide_end'     : guide_end,
    }

    pm.expression( s=exp_str, o="", n="%s_EXP" % start_joint, a=1, uc='all' )

    #make things look pretty
    for n in pm.ls( [ parent_group, main_ik, guide_ik ], dag=1 ):
        n.visibility.set(0)

    try:
        pm.delete( guide_end.getChildren()[0] )
    except:
        pass
    try:
        pm.delete( guide_ik_end.getChildren()[0] )
    except:
        pass


    control.displayHandle.set(1)
    pm.select( control, r=1 )


    '''


    select([loc_start,loc_end], r=1)
    makeIdentity( apply=True, s=0, r=0, t=1, n=0 )

    loc_start.rotate.set(0,0,0)

    select([],r=1)
    aimConstraint( loc_end, loc_start, weight=1, skip=('x','y'), aimVector=(1,0,0) )


    parent( distShape.getParent(), guide_ik )


    loc_mid = group(empty=True)#spaceLocator()
    rename( loc_mid, "%s_loc_mid" % name )
    parent( loc_mid, loc_start )
    loc_mid.translate.set(0,0,0)
    loc_mid.rotate.set(0,0,0)

    pointConstraint( guide_ik_mid, loc_mid, offset=(0,0,0), skip=('y','z'), weight=1 )


    loc_mid_split = group(empty=True)#spaceLocator()
    rename( loc_mid_split, "%s_loc_split" % name )
    parent( loc_mid_split, loc_mid )
    loc_mid_split.translate.set(0,0,0)
    loc_mid_split.rotate.set(0,0,0)

    pointConstraint( loc_start, loc_mid_split, mo=1, weight=1 )
    pointConstraint( loc_end,   loc_mid_split, mo=1, weight=1 )


    loc_guide = group(empty=True)#spaceLocator()
    rename( loc_guide, "%s_loc_guide" % name )
    parent( loc_guide, loc_start )
    loc_guide.translate.set(0,0,0)
    loc_guide.rotate.set(0,0,0)



    #hook up the guide joints
    aimConstraint( loc_guide, guide_start, weight=1, skip=('x','y'), aimVector=(1,0,0) )
    parentConstraint( guide_ik_start, guide_start, skipRotate=('z'), weight=1 )

    aimConstraint( loc_end, guide_mid, weight=1, skip=('x','y'), aimVector=(1,0,0) )
    pointConstraint( loc_guide, guide_mid, weight=1 )

    parentConstraint( control, guide_end, weight=1 )



    control.displayHandle.set(1)
    select( control, r=1 )
    '''


def getStretchyIk():
    for ik in pm.ls(sl=1,dag=1,type="ikHandle"):
        if ik.hasAttr("stretchStart"):
            ik_handle = ik
            distShape = pm.ls(ik_handle,dag=1,type="distanceDimShape")[0]
            break

    try:
        return ik_handle
    except UnboundLocalError:
        raise UnboundLocalError, "Could not find ik with stretch attributes in selection."


def setStretchStart():
    ik_handle = getStretchyIk()

    distShape = pm.ls(ik_handle,dag=1,type="distanceDimShape")[0]
    start_joint = ik_handle.getStartJoint()
    mid_joint = start_joint .getChildren(type="joint")[0]

    ik_handle.stretchStart.set( distShape.distance.get() )

    mid_joint.minRotYLimitEnable.set(0)
    mid_joint.minRotZLimitEnable.set(0)

    #shuffle to re-solve ik
    mid_joint.rz.set(1000)

    mid_joint.minRotYLimit.set( mid_joint.ry.get() )
    mid_joint.minRotZLimit.set( mid_joint.rz.get() )
    mid_joint.minRotYLimitEnable.set(1)
    mid_joint.minRotZLimitEnable.set(1)


def setStretchEnd():
    ik_handle = getStretchyIk()

    distShape = pm.ls(ik_handle,dag=1,type="distanceDimShape")[0]
    ik_handle.stretchEnd = distShape.distance.get()


