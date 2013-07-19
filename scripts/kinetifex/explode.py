

import maya.OpenMaya as om
import maya.OpenMayaUI as omUI
import math

import maya.OpenMayaRender as omR

import pymel.core as pm

glRenderer = omR.MHardwareRenderer.theRenderer()
glFT = glRenderer.glFunctionTable()


def MFVector_str(self):
    return '%f, %f, %f' % (self.x, self.y, self.z)

om.MVector.__str__ = MFVector_str
om.MFloatVector.__str__ = MFVector_str


def drawTest():
    port_view = omUI.M3dView.active3dView()

    '''
    port_view.getRendererName

    #port_view.beginGL()

    port_view.beginGL()
    port_view.beginOverlayDrawing()
    glFT.glPushAttrib( omR.MGL_ALL_ATTRIB_BITS )

    glFT.glDisable(omR.MGL_LIGHTING)
    glFT.glBegin(omR.MGL_LINES)
    glFT.glColor3f( 1.0, 0.0, 0.0 );
    glFT.glVertex3f( 0.0, 0.0, 0.0 );
    glFT.glVertex3f( 3.0, 0.0, 0.0 );

    glFT.glColor3f( 0.0, 1.0, 0.0 );
    glFT.glVertex3f( 0.0, 0.0, 0.0 );
    glFT.glVertex3f( 0.0, 3.0, 0.0 );

    glFT.glColor3f( 0.0, 0.0, 1.0 );
    glFT.glVertex3f( 0.0, 0.0, 0.0 );
    glFT.glVertex3f( 0.0, 0.0, 3.0 );
    glFT.glEnd()

    glFT.glPopAttrib()
    port_view.endOverlayDrawing()
    port_view.endGL()

    glFT.glEnable( omR.MGL_LIGHTING )
    '''

    TORUS_PI = 3.14159265
    TORUS_2PI = 2.0 * TORUS_PI
    EDGES = 30
    SEGMENTS = 20

    port_view.beginGL()
    for j in range(SEGMENTS):
        glFT.glPushMatrix()
        glFT.glRotatef(360.0 * j / SEGMENTS, 0.0, 1.0, 0.0)
        glFT.glTranslatef(1.5, 0.0, 0.0)
        for i in range(EDGES):
            glFT.glBegin(omR.MGL_LINE_STRIP)
            p0 = TORUS_2PI * i / EDGES
            p1 = TORUS_2PI * (i+1) / EDGES
            glFT.glVertex2f(math.cos(p0), math.sin(p0))
            glFT.glVertex2f(math.cos(p1), math.sin(p1))
            glFT.glEnd()
        glFT.glPopMatrix()
    port_view.endGL()


def getSelectedNode( MFnType=om.MFn.kTransform ):

    selList = om.MSelectionList()
    om.MGlobal.getActiveSelectionList( selList )
    sel_iter = om.MItSelectionList( selList, MFnType )

    node = om.MDagPath()
    comp = om.MObject()

    while not sel_iter.isDone():
        sel_iter.getDagPath( node, comp )

        print node.partialPathName()

        sel_iter.next()


def explodeUVs():

    selList = om.MSelectionList()
    om.MGlobal.getActiveSelectionList( selList )
    sel_iter = om.MItSelectionList( selList, om.MFn.kMeshPolygonComponent )

    node = om.MDagPath()
    comp = om.MObject()

    i=0
    while not sel_iter.isDone():
        sel_iter.getDagPath( node, comp )

        mesh_iter = om.MItMeshPolygon( node, comp )

        while not mesh_iter.isDone():

            n = om.MVector()
            mesh_iter.getNormal( n )
            center = om.MVector( mesh_iter.center() )

            print n

            d = center*n

            m1 = ( 1,0,0,0,  0,1,0,0,  0,0,1,0,  0,0,0,0 )
            M = om.MMatrix()
            om.MScriptUtil.createMatrixFromList( m1, M )

            for i in range( mesh_iter.polygonVertexCount() ):
                q = om.MVector( mesh_iter.point( i ) )
                vUV = center - q

                a = d - ( q * n )
                an = om.MVector(n) * a
                #q1 = q + om.MPoint(q1.x,q1.y,q1.z) * n

                v1 = n^vUV^n

                print 'n:', n
                print 'a:', a
                print 'an:', an
                print 'v1:', v1

                f = om.MScriptUtil()
                f.createFromDouble( v1.x, v1.z )

                mesh_iter.setUV( i, f.asFloat2Ptr() )

            mesh_iter.next()

        sel_iter.next()

        mesh_iter.updateSurface()


def explodeUVs2():

    selList = om.MSelectionList()
    om.MGlobal.getActiveSelectionList( selList )
    sel_iter = om.MItSelectionList( selList, om.MFn.kMeshPolygonComponent )

    node = om.MDagPath()
    comp = om.MObject()

    i=0
    while not sel_iter.isDone():
        sel_iter.getDagPath( node, comp )

        mesh_iter = om.MItMeshPolygon( node, comp )

        while not mesh_iter.isDone():

            vNormal = om.MVector()
            mesh_iter.getNormal( vNormal )
            center = mesh_iter.center()

            print vNormal

            for i in range( mesh_iter.polygonVertexCount() ):
                vert_point = mesh_iter.point( i )
                vUV = center - vert_point

                v2 = vNormal^vUV

                f = om.MScriptUtil()
                f.createFromDouble( v2.x, v2.z )

                mesh_iter.setUV( i, f.asFloat2Ptr() )

            mesh_iter.next()

        sel_iter.next()

        mesh_iter.updateSurface()



def getPos():

    from pymel.core import xform, joint

    j1 = xform( 'joint2', ws=1, t=1, q=1 )
    j2 = xform( 'joint3', ws=1, t=1, q=1 )

    v1 = om.MVector( *j1 )
    v2 = om.MVector( *j2 )

    v3 = v1^v2
    v4 = v3^v1 * .0001

    joint( p=[ v4.x, v4.y, v4.z ] )


'''
import maya.OpenMayaRender as OpenMayaRender

# Get a renderer, then a function table
def initializeGL():
    glRenderer = OpenMayaRender.MHardwareRenderer.theRenderer()
    glFT = glRenderer.glFunctionTable()

# Query the maximum texture size
def printMaxTextureSize():
    maxTxtSize = glFT.maxTextureSize()
    print maxTxtSize

# Draw an axis
def drawAxis():
    glFT.glDisable(OpenMayaRender.MGL_LIGHTING)
    glFT.glBegin(OpenMayaRender.MGL_LINES)

    glFT.glColor3f( 1.0, 0.0, 0.0 )
    glFT.glVertex3f( 0.0, 0.0, 0.0 )
    glFT.glVertex3f( 3.0, 0.0, 0.0 )

    glFT.glColor3f( 0.0, 1.0, 0.0 )
    glFT.glVertex3f( 0.0, 0.0, 0.0 )
    glFT.glVertex3f( 0.0, 3.0, 0.0 )

    glFT.glColor3f( 0.0, 0.0, 1.0 )
    glFT.glVertex3f( 0.0, 0.0, 0.0 )
    glFT.glVertex3f( 0.0, 0.0, 3.0 )

    glFT.glEnd()
    glFT.glEnable(OpenMayaRender.MGL_LIGHTING)

'''