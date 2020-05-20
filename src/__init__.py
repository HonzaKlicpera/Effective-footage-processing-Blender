
bl_info = {
    "name": "Effective footage processing",
    "description": "Addon created for efficient greenscreen footage processing for game development (used with EbSynth).",
    "author": "Jan Klicpera",
    "version": (1, 0),
    "blender": (2, 81, 16),
    "location": "Properties > Render Properties",
    "category": "Interface" 
}


if "bpy" in locals():
    import importlib
else:
    from . import (
            keying_module,
            tracking_module
            )

import bpy


def register():
    keying_module.register()
    tracking_module.register()

def unregister():
    keying_module.unregister()
    tracking_module.unregister()

