
import pymel.core as pm
from pymel.core import mel
from impress import models, register

from kinetifex.poses import Pose
#from kinetifex.scene import checkSave


def _checkControls( controlList ):

    for control in controlList:

        if not pm.objExists( control ):
            result = pm.confirmDialog( message='Missing object "%s". Continue?' % control,
                                    button=['Continue', 'Cancel'],
                                    defaultButton='Continue',
                                    dismissString='Continue',
                                    cancelButton='Cancel',
                                    )
            if result == 'Continue':
                pass
            elif result == 'Cancel':
                mel.error( "Transfer Animation Cancelled" )
            else:
                return False

    return True


def transferAnimation( targetFile="", prefix=False, prefixName='ref:' ):
    """
    Set the Target Scene and selected the controls to transfer.
    """

    pm.select( pm.ls( sl=1 ), replace=True )
    control_list = map( str, pm.ls( sl=1 ) )

    if not control_list:
        mel.error( "No Controls Selected for Transfer!" )


    startTime = pm.playbackOptions( query=True, animationStartTime=True )
    minTime = pm.playbackOptions( query=True, minTime=True )
    maxTime = pm.playbackOptions( query=True, maxTime=True )
    endTime = pm.playbackOptions( query=True, animationEndTime=True )

    tempPose = Pose()
    tempPose.capture()

    pm.copyKey( control_list, hierarchy=False )


    pm.openFile( targetFile, force=False )

    if _checkControls( control_list ):

        if prefix:
            tempPose.apply( alterNamespace=True, namespace=prefixName )
        else:
            tempPose.apply()

        pm.pasteKey( control_list, option='replaceCompletely', copies=1, connect=1, timeOffset=0, floatOffset=0, valueOffset=0 )
        pm.playbackOptions( minTime=minTime, ast=startTime, maxTime=maxTime, aet=endTime )
    else:
        raise


class TransferAnimationOptions( models.OptionModel ):

    targetFile = models.FileBrowser( default='', fileFilter="Maya Files (*.ma *.mb)", fileMode=1,
                                     cap="Transfer To Scene", buttonLabel="Browse", optionName="targetFile" )

    prefix = models.CheckBox( default=1, ann='use a prefix' )
    prefixName = models.TextField( default='ref:', label="", requires=( prefix, 1 ) )


performTransferAnimation = register.PerformCommand( transferAnimation, TransferAnimationOptions )


