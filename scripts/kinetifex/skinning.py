

import pymel.core as pm
from pymel.core import api
#from pymelX import register_runtime
from impress import register

from config import RUNTIME_SUITE


copy_skin_cluster = None
copy_skin_weights = []


@register.runtime
def copyVertexWeights( vert=None ):
    """Store the skin weights data for a single vertex."""

    global copy_skin_cluster
    global copy_skin_weights

    if vert is None:
        vert = pm.ls(sl=1,type='float3')[0]

    assert isinstance(vert,pm.MeshVertex), "Requires vertex. (MeshVertex)"

    node = vert.node()

    copy_skin_cluster = node.listHistory(type='skinCluster')[0]

    skin_cluster = api.MFnSkinCluster( copy_skin_cluster.__apiobject__() )
    influences = api.MDagPathArray()
    influence_count = skin_cluster.influenceObjects( influences )

    influence_list = [influences[o].partialPathName() for o in xrange(influences.length())]
    copy_skin_weights = []

    for i in range( influence_count ):
        weights = api.MFloatArray()
        skin_cluster.getWeights( node.__apiobject__(), vert.__apimobject__(), i, weights )

        if weights[0] > 0.0:
            copy_skin_weights.append( (influence_list[i], weights[0]) )


@register.runtime
def pasteVertexWeights( vert=None ):
    """Paste previously copied skin weights data to a single vertex."""

    global copy_skin_cluster
    global copy_skin_weights

    if vert is None:
        vert = pm.ls(sl=1,type='float3')[0]

    assert isinstance(vert,pm.MeshVertex), "Requires vertex. (MeshVertex)"

    pm.skinPercent( copy_skin_cluster.name(), transformValue=copy_skin_weights )


@register.runtime
def matchSkinning():
    """Select a skin mesh, followed the mesh you wish to match skinning to."""

    source, target = pm.ls(sl=1,type='transform')

    src_cluster = source.listHistory(type='skinCluster')[0]
    influences = src_cluster.influenceObjects()

    pm.select(influences, r=1 )
    pm.select(target, add=1)

    pm.skinCluster(toSelectedBones=1,
                   obeyMaxInfluences=src_cluster.getObeyMaxInfluences(),
                   maximumInfluences=src_cluster.getMaximumInfluences(),
                   dropoffRate=2,
                   removeUnusedInfluence=False
                   )

    tgt_cluster = target.listHistory(type='skinCluster')[0]

    pm.copySkinWeights( ss=src_cluster, ds=tgt_cluster, noMirror=True )

    pm.select(target, replace=1)


@register.runtime
def getOverInfluencedVerts():
    """Find vertices that have more weights than set maximumInfluences."""
    selected = pm.ls(sl=1)[0]

    if isinstance(selected, pm.nt.Mesh):
        mesh = selected
    elif isinstance(selected, pm.Component):
        mesh = selected.node()
    elif isinstance(selected, pm.nt.Transform):
        mesh = selected.getShape()

    skin_cluster = mesh.listHistory(type='skinCluster')[0]
    mfn_skin_cluster = api.MFnSkinCluster( skin_cluster.__apiobject__() )

    max_influences = skin_cluster.getMaximumInfluences()

    vertIter = api.MItMeshVertex ( mesh.__apiobject__() )
    vert_list = set()

    while not vertIter.isDone():
        vert_influences = 0

        for i in range( skin_cluster.numInfluenceObjects() ):
            weights = api.MFloatArray()
            mfn_skin_cluster.getWeights( mesh.__apimdagpath__(), vertIter.currentItem(), i, weights )

            if weights[0] > 0.0:
                vert_influences += 1

                if vert_influences > max_influences:
                    vert_list.add( vertIter.index() )

        vertIter.next()

    vert_list = list(vert_list)

    pm.select(cl=1)

    if vert_list:
        pm.hilite(mesh, r=1)
        print '# ', list(vert_list), 'have too many weights.'
        for v in vert_list:
            pm.select(mesh.vtx[v], add=1)
    else:
        pm.select(selected, replace=1)
        print '# Ok.'


