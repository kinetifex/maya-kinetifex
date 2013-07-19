import os
from pymel.core import Path, about, getMelGlobal


DIR_APP = Path( os.environ.get( 'MAYA_APP_DIR' ) )
DIR_VERSION = DIR_APP / about( version=True ).replace(' ','-')

DIR_PREFS = DIR_VERSION / 'prefs'
PREF_POSES = DIR_PREFS / 'poses.bin'

_runtime_suite = getMelGlobal( 'string', 'KINETIFEX_RUNTIME_SUITE' )

if _runtime_suite:
    RUNTIME_SUITE = _runtime_suite
else:
    RUNTIME_SUITE = 'Kinetifex'