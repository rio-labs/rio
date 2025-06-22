__version__ = "0.11.2rc6"


import logging

_logger = logging.getLogger(__name__)

# Re-export dataclass stuff for easy use.
from dataclasses import KW_ONLY as KW_ONLY
from dataclasses import field as field

# URLs are used as an important datatype within rio. Re-export them for easy
# use.
from yarl import URL as URL

from . import event as event
from . import extension_event as extension_event
from . import icons as icons  # For backwards compat. Delete eventually
from . import patches_for_3rd_party_stuff
from .app import *
from .color import *
from .components import *
from .cursor_style import *
from .dialog import *
from .errors import *
from .extension import *
from .extension_event import (
    ExtensionAppCloseEvent as ExtensionAppCloseEvent,
)
from .extension_event import (
    ExtensionAppStartEvent as ExtensionAppStartEvent,
)
from .extension_event import (
    ExtensionAsFastapiEvent as ExtensionAsFastapiEvent,
)
from .extension_event import (
    ExtensionPageChangeEvent as ExtensionPageChangeEvent,
)
from .extension_event import (
    ExtensionSessionCloseEvent as ExtensionSessionCloseEvent,
)
from .extension_event import (
    ExtensionSessionStartEvent as ExtensionSessionStartEvent,
)
from .fills import *
from .observables import *
from .routing import *
from .session import *
from .text_style import *
from .theme import *
from .user_settings_module import *
from .utils import *

del patches_for_3rd_party_stuff
