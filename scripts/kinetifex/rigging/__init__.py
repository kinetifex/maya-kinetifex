from kinetifex.rigging.general import *

"""
# -- Run this in the script editor to load the modules and setup globals
LEFT_SIDE = 0
RIGHT_SIDE = 1

import kinetifex.rigging.joints as rig_j
import kinetifex.rigging.controls as rig_c
import kinetifex.rigging.stretch_ik as stretch_ik

# -- Run this block to set up the left side of a human character.

p = rig_j.addRootCmd()[0]

s = rig_j.addSplineCmd( parent=p )[1]

rig_j.addHeadCmd( parent=s )

rig_j.addLegCmd( parent=p )
#rig_j.addLegCmd( side=RIGHT_SIDE, parent=p ) # Use mirror command

rig_j.addArmCmd( parent=s )
#rig_j.addArmCmd(side=RIGHT_SIDE, parent=s ) # Use mirror command

select( p, r=1 )
makeIdentity( apply=1, t=1, r=1, s=1, n=0 )

# -- Run this block to add all the rigging controls.

select( ['pelvis'], r=1 )
rig_c.rigRootCmd()

select( ['spine_1', 'spine_END'], r=1 )
rig_c.rigSpineCmd()

select( ['head_skull'], r=1 )
rig_c.rigHeadCmd()

reload(rig_c)
select( ['leg_hip_l', 'leg_foot_l'], r=1 )
rig_c.rigLimbCmd('leg_', hasStretch=1)

select( ['leg_hip_r', 'leg_foot_r'], r=1 )
rig_c.rigLimbCmd('leg_', side=1)

select( ['arm_shoulder_l', 'arm_wrist_l'], r=1 )
rig_c.rigLimbCmd('arm_')

select( ['arm_shoulder_r', 'arm_wrist_r'], r=1 )
rig_c.rigLimbCmd('arm_', side=1)
"""