
import math

import pymel.core as pm
from pymel.core.datatypes import Vector
from pymel.core.nodetypes import Joint


LEFT_SIDE = 0
RIGHT_SIDE = 1


class ParentDesc(object):
    def __init__(self, name ):
        self.name = self.fullName = name

class JointDesc( object ):

    prefix = ''
    suffix = ''

    def __init__(self, name, position, rotation=(0,0,0), worldSpace=0, parent=None ):
        self.name = self.fullName = name
        self.position = position
        self.rotation = rotation
        self.ws = self.worldSpace = worldSpace
        self.parent = parent

    def build(self):
        if self.parent is not None:
            pm.select( self.parent.fullName, replace=True )
        else:
            pm.select( clear=True )

        name = self.prefix + self.name + self.suffix

        pm.joint( name=name, position=self.position,
               absolute=self.ws, relative=1-self.ws
               )

        _joint = Joint( pm.ls(sl=1)[0] )
        _joint.rotate.set( self.rotation )

        self.fullName = str(_joint)

        if isinstance( self.parent, Joint ):
            pm.joint( self.parent.fullName, e=1, zso=1, oj='xyz', sao='yup' )

        return _joint


def _mirror( topJoint ):
    grp = pm.group( topJoint )

    grp.setRotatePivot( (0,0,0) )
    original = pm.select( grp.getChildren()[0], r=1)
    mirrored = [ Joint(m) for m in pm.mirrorJoint( mirrorYZ=1, mirrorBehavior=1 ) ]

    pm.parent( mirrored[0], w=1 )

    pm.delete( original, grp )
    for m in mirrored:
        m.rename( m[:-1] )

    return mirrored



class Modulate( object ):

    def __init__(self, base=0, amplitude=1, phase=1, frequency=1 ):
        self.base = base
        self.amplitude = amplitude
        self.phase = phase
        self.frequency = frequency

    def getInterval( self, interval ):
        return math.sin( self.phase + (self.frequency*interval) ) * self.amplitude + self.base

'''
def modulate( base=0, amplitude=1, phase=1, frequency=1, interval ):
    joint_list = []
    for i in range(intervals):
        joint_list.append( math.sin( phase + ( frequency * (i/intervals) ) ) * amplitude + base )

    return joint_list
'''


def addArmCmd( prefix='arm_', suffix=None, side=LEFT_SIDE, parent=None,
               hasCollar=True, hasForearm=True
               ):

    _collar =   JointDesc( 'collar',   Vector(0.3, 14.75, 0.4)*.1,    (0, 0, 0  ), True )
    _shoulder = JointDesc( 'shoulder', Vector(1.92, 14.75, -0.29)*.1, (0, 0, -25), True )
    _elbow =    JointDesc( 'elbow',    Vector(2.79, 0.0, 0.0)*.1,     (0, -5, 0 ), False, _shoulder )
    _wrist =    JointDesc( 'wrist',    Vector(2.42, 0.0, 0.0)*.1,     (0, 5, 25 ), False, _elbow    )
    _forearm =  JointDesc( 'forearm',  Vector(1.21, 0.0, 0.0)*.1,     (0, 0, 0 ),  False, _elbow    )
    _wristEnd = JointDesc( 'wristEND', Vector(0.74, 0.0, 0.0)*.1,     (0, 0, 0 ),  False, _wrist    )

    desc_list = [ _collar, _shoulder, _elbow, _wrist, _forearm, _wristEnd ]

    for j in desc_list:
        j.suffix = suffix or ('_l','_r')[side]
        j.prefix = prefix

    if hasCollar:
        _shoulder.parent = _collar
        collar = _collar.build()

    shoulder = _shoulder.build()
    elbow = _elbow.build()
    wrist = _wrist.build()
    wristEnd = _wristEnd.build()

    joint_list = [ shoulder, elbow, wrist, wristEnd ]

    if hasForearm:
        forearm = _forearm.build()
        joint_list.insert( 3, forearm )

    top_joint = shoulder

    if hasCollar:
        top_joint = collar
        joint_list.insert( 0, collar )

    #mirror if right-side
    if side == RIGHT_SIDE:
        mirrored = _mirror( top_joint )

    if parent is not None:
        pm.parent( top_joint, parent )

    try:
        pm.select( mirrored[0], r=1 )
    except:
        pm.select( top_joint, r=1 )

    return joint_list


def addLegCmd( prefix='leg_', suffix=None, side=LEFT_SIDE, parent=None ):

    _hip =     JointDesc( 'hip',     Vector(0.91, 9.81, -0.14)*.1, (0, 0, 0 ), True )
    _knee =    JointDesc( 'knee',    Vector(0.91, 5.08, -0.13)*.1, (0, 0, 0 ), True, _hip )
    _foot =    JointDesc( 'foot',    Vector(0.91, 0.79, -0.48)*.1, (0, 0, 0 ), True, _knee )
    _toe =     JointDesc( 'toe',     Vector(0.91, 0.21,  0.98)*.1, (0, 0, 0 ), True, _foot )
    _toeEnd =  JointDesc( 'toeEND',  Vector(0.91, 0.17,  1.53)*.1, (0, 0, 0 ), True, _toe  )
    _heelEnd = JointDesc( 'heelEND', Vector(0.91, 0.10, -1.00)*.1, (0, 0, 0 ), True, _foot )

    desc_list = [ _hip, _knee, _foot, _toe, _toeEnd, _heelEnd ]

    for j in desc_list:
        j.suffix = suffix or ('_l','_r')[side]
        j.prefix = prefix


    hip = _hip.build()
    knee = _knee.build()
    foot = _foot.build()
    toe = _toe.build()
    toeEnd = _toeEnd.build()
    heelEnd = _heelEnd.build()

    joint_list = [ hip, knee, foot, toe, toeEnd, heelEnd ]

    pm.joint( knee, e=1, oj='xyz', secondaryAxisOrient='ydown' )

    #mirror if right-side
    if side == RIGHT_SIDE:
        mirrored = _mirror( hip )
        joint_list = mirrored

    if parent is not None:
        pm.parent( hip, parent )

    try:
        pm.select( mirrored[0], r=1 )
    except:
        pm.select( hip, r=1 )

    return joint_list


def addRootCmd( prefix='' ):

    _pelvis = JointDesc( 'pelvis', Vector(0.0, 9.9, 0.0)*.1, worldSpace=True )
    _pelvis.prefix = prefix

    pelvis = _pelvis.build()

    pm.select( pelvis, r=1 )

    return [pelvis]


def addSplineCmd( prefix='spine_', parent=None ):

    _joint1 =   JointDesc( '1',   Vector(0.0, 10.51,  0.0228)*.1, (0, 0, 0), True )
    _joint2 =   JointDesc( '2',   Vector(0.0, 12.81, -0.4903)*.1, (0, 0, 0), True, _joint1 )
    _jointEnd = JointDesc( 'END', Vector(0.0, 15.11, -0.5358)*.1, (0, 0, 0), True, _joint2 )

    desc_list = [ _joint1, _joint2, _jointEnd ]
    joint_list = []

    for j in desc_list:
        j.prefix = prefix
        joint_list.append( j.build() )

    if parent is not None:
        pm.parent( joint_list[0], parent )

    pm.select( joint_list[0], r=1 )

    return joint_list


def addHeadCmd( prefix='head_', parent=None ):

    _neck =  JointDesc( 'neck',  Vector(0.0, 15.73, -0.37)*.1, (0, 0, 0), True )
    _skull = JointDesc( 'skull', Vector(0.0, 16.59, -0.27)*.1, (0, 0, 0), True, _neck )
    _end =   JointDesc( 'END',   Vector(0.0, 16.59,  1.21)*.1, (0, 0, 0), True, _skull )

    desc_list = [ _neck, _skull, _end ]
    joint_list = []

    for j in desc_list:
        j.prefix = prefix
        joint_list.append( j.build() )

    if parent is not None:
        pm.parent( joint_list[0], parent )

    pm.select( joint_list[0], r=1 )

    return joint_list


def addDigitCmd( prefix='index_', suffix=None, side=LEFT_SIDE, joints=4, parent=None ):

    if parent is not None:
        _parent = ParentDesc( parent )

    joint_list = []

    length = 0.074

    for i in range( 1,joints+1 ):
        name = i == joints and 'END' or str(i)
        try:
            _joint = JointDesc( name, (length, 0, 0), (0, 0, -10), False, _parent )
        except NameError:
            _joint = JointDesc( name, (0, 0, 0), (0, 0, 0), False )

        _joint.suffix = suffix or ('_l','_r')[side]
        _joint.prefix = prefix

        joint_list.append( _joint.build() )

        _parent = _joint
        length = length/1.618

    pm.select( joint_list[0], r=1 )
    pm.makeIdentity( joint_list[0], apply=True, r=1 )

    return joint_list