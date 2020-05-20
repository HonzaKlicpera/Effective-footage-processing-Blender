import bpy
import os, glob
from pathlib import Path
from enum import Enum
from abc import ABC, abstractmethod
import csv

from . import keying_module

def export_tracking_data(self, context):
    clip = context.space_data.clip
    clip_name = os.path.splitext(clip.name)[0]
    tracker_name = context.scene.tracking_local.tracker_name
    output_path = os.path.join(keying_module.get_abs_output_path(context),clip_name)
    keying_module.create_directory(output_path)
    
    file = open(os.path.join(output_path,clip_name+".csv"), "w", newline='')
    writer = csv.writer(file, delimiter=',')
    
    multiplier = context.scene.tracking_local.tracking_multiplier
    tracker = clip.tracking.tracks.get(tracker_name)
    if tracker is not None:
        prev = tracker.markers[0].co[0]
        for m in tracker.markers:
            writer.writerow([(m.co[0] - prev) * multiplier])
            prev = m.co[0]
        self.report({"INFO"},"TRACKER SUCESSFULLY EXPORTED")
    else:
        self.report({"ERROR"},"TRACKER NOT FOUND")
        
    file.close()
            

#----------------------------------------
#   PROPERTIES
#----------------------------------------     
      
class TrackingSceneProps(bpy.types.PropertyGroup):
    tracker_name: bpy.props.StringProperty \
      (
      name = "Track name",
      description = "Name of the tracker for data export",
      )
     
    tracking_multiplier: bpy.props.FloatProperty \
      (
      name = "Distance multiplier",
      description = "The exported tracking distance gets multiplied by this value",
      default = 1,
      min = 0.0001
      )
      
class TrackingPanel(bpy.types.Panel):
    bl_label = "Tracking Panel"
    bl_idname = "SCENE_PT_tracking_rendering"
    bl_space_type = "CLIP_EDITOR"
    bl_region_type = "UI"
    bl_context = "render"


    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        box = layout.box()
        box.row().label(text = "Tracking export")
        box.row().prop(scene.tracking_local, "tracker_name")
        box.row().prop(scene.tracking_local, "tracking_multiplier")
        box.row().operator("tracking.export_data")

        
class TrackingExportDataOp(bpy.types.Operator):
    bl_idname = "tracking.export_data"
    bl_label = "Export Data"
    bl_description = "Export the tracking data of the chosen tracker"
    
    def execute(self, context):
        export_tracking_data(self, context)
        return {"FINISHED"}
      
classes = (
    TrackingExportDataOp,
    TrackingPanel,
    TrackingSceneProps
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.tracking_local = bpy.props.PointerProperty(type=TrackingSceneProps)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.tracking_local