import bpy
import os, glob
import time
import datetime
from pathlib import Path
from enum import Enum
from abc import ABC, abstractmethod

from . import state_machine
from .state_machine import State
from .state_machine import StateMachine
from .state_machine import RenderAllOp

from . import tracking_module


#Video extensions that can be loaded in
exts = frozenset({".mpg2", ".mov", ".avi", ".mpeg", ".movie",
        ".webm", ".mp4", ".wmv", ".mpg", ".mkv"})
        
        
#----------------------------------------
#   CUSTOM FUNCTIONS
#----------------------------------------   
def updated_input_path(self, context):
    """Refreshes the clip list whenever the input path is updated.
    If a namespace is not defined, then the default one is set."""
    input_path = get_abs_input_path(context)
    scene_namespace = get_master_scene().keying_global.scene_namespace
    if not scene_namespace:
        set_default_namespace(input_path)
    load_clip_collection(context,input_path)
    
def updated_namespace(self, context):
    """Refreshes the clip list whenever the namespace is updated."""
    input_path = get_abs_input_path(context)
    load_clip_collection(context,input_path)
        
def updated_auto_frames(self, context):
    """Sets the number of frames to be render to match the current movie clip length."""
    if context.scene.keying.auto_frames is True:
        frame_count = context.window.scene.node_tree.nodes["Movie Clip"].clip.frame_duration
        context.scene.frame_end = frame_count

def set_default_namespace(input_path):
    """Sets default namespace based on the name of the input folder."""
    default_namespace = os.path.basename(os.path.dirname(input_path))
    get_master_scene().keying_global.scene_namespace = default_namespace
        
def load_clip_collection(context, path):
    """Loads new clips into the clip list based on the input folder."""
    master_scene = get_master_scene()
    scene_namespace = master_scene.keying_global.scene_namespace
    master_scene.clip_list.clear()
    master_scene.keying_global.active_clip_index = -1
    
    for ext in exts:
        for file_path in glob.glob(os.path.join(path, "*%s" % ext)):
            clip_item = master_scene.clip_list.add()
            clip_item.clip_name = os.path.basename(file_path)
            if bpy.data.scenes.get(scene_namespace + "/" + clip_item.clip_name) is not None:
                clip_item.icon = "HIDE_OFF"
                
def get_clip_item(context, index):
    """Returns an item from the clip list at the given index."""
    if index < 0: #Checking if index is not negative (negative index does not throw exception)
        return None
    try:
        item = get_master_scene().clip_list[index]
    except IndexError:
        return None
    else:
        return item
   
    
def switch_clip(context, clip_index):
    """Switches the scene to a scene reserved for the given clip index.
    If the scene was not yet created, it gets created by making a full
    copy of the current scene."""
    clip_item = get_clip_item(context, clip_index)
    if clip_item:
        scene_name = get_master_scene().keying_global.scene_namespace + "/" + clip_item.clip_name
        scn = bpy.data.scenes.get(scene_name)
        if scn is None:
            new_scene(context, scene_name)
            load_clip(context, clip_item.clip_name)
        else:
            switch_scene(context, scene_name)
        clip_item.icon = "REC"
    else:
        return
    
    clip = bpy.data.movieclips.get(clip_item.clip_name)
    bpy.context.window.scene.node_tree.nodes["Movie Clip"].clip = clip
    bpy.context.window.scene.node_tree.nodes["Stabilize 2D"].clip = clip
    
    prev_index = get_master_scene().keying_global.active_clip_index
    prev_item = get_clip_item(context, prev_index)
    if prev_item is not None and prev_index is not clip_index:
        prev_item.icon = "HIDE_OFF"
        
    get_master_scene().keying_global.active_clip_index = clip_index

def switch_to_mask(context):
    """Reconnects the nodes into a mask view (Matte socket of the Keying node)."""
    node_tree = context.window.scene.node_tree
    crop_node = node_tree.nodes["Crop"]
    balance_node = node_tree.nodes["Keying"]
    context.window.scene.node_tree.links.new(balance_node.outputs[1],crop_node.inputs[0])
    context.scene.render.image_settings.color_mode = "BW"
    context.scene.keying.showing_mask = True

def switch_to_video(context):
    """Reconnects the nodes into a video view."""
    node_tree = context.window.scene.node_tree
    crop_node = node_tree.nodes["Crop"]
    keying_node = node_tree.nodes["Keying"]
    context.window.scene.node_tree.links.new(keying_node.outputs[0],crop_node.inputs[0])
    context.scene.render.image_settings.color_mode = "RGBA"
    context.scene.keying.showing_mask = False

def load_clip(context, clip_name):
    """Loads a given clip into the Blenders clip storage."""
    path = os.path.join(get_abs_input_path(context), clip_name)
    old_clip = bpy.data.movieclips.get(clip_name)
    if old_clip != None:
        if old_clip.filepath != path:
            bpy.data.movieclips.remove(old_clip)
            bpy.data.movieclips.load(path)
    else:
        bpy.data.movieclips.load(path)
    movie_clip = bpy.data.movieclips.get(clip_name)

def new_scene(context, scene_name):
    """Creates a new scene by making a full copy of the current scene."""
    scn = bpy.data.scenes.get(scene_name)
    if scn is None:
        bpy.ops.scene.new(type="FULL_COPY")
        context.window.scene.name = scene_name

def switch_scene(context, scene_name):
    """Switches the editor to the defined scene."""
    scn = bpy.data.scenes.get(scene_name)
    if scn is not None:
        context.window.scene = scn

def create_directory(path):
    if not os.path.exists(path):
        os.mkdir(path)
        
def get_output_clip_path(context):
    """Returns the current user defined output path."""
    clipName = get_curr_clip_name(context)
    return os.path.join(get_abs_output_path(context), clipName)

def get_curr_clip_name(context):
    """Returns the name of the currently active clip."""
    movie_clip = context.window.scene.node_tree.nodes["Movie Clip"].clip
    if movie_clip is None:
        return None
    return os.path.splitext(movie_clip.name)[0]
    
def get_master_scene():
    """Returns the master scene (used for storing global properties).
    If none exists, then it is created."""
    master_scene = bpy.data.scenes.get("MasterScene")
    if master_scene is None:
        master_scene = bpy.data.scenes.new("MasterScene")
    return master_scene
    
def backup_blend_file(path):
    """Saves the blend file into the given path."""
    curr_filepath = bpy.data.filepath
    curr_time = datetime.datetime.now()
    backup_filename = curr_time.strftime("keying_backup_%Y-%m-%d_%H-%M-%S.blend")
    bpy.ops.wm.save_as_mainfile(filepath = os.path.join(path, backup_filename))
    bpy.ops.wm.save_mainfile(filepath = curr_filepath)
    
def get_render_subfolder(context):
    save_path = get_output_clip_path(context)
    if context.scene.keying.showing_mask:
        return os.path.join(save_path,"mask")
    else:
        return os.path.join(save_path, "video")
        
def get_abs_input_path(context):
    input_path = get_master_scene().keying_global.input_path
    return bpy.path.abspath(input_path)

def get_abs_output_path(context):
    output_path = get_master_scene().keying_global.output_path
    return bpy.path.abspath(output_path)
        

#----------------------------------------
#   PROPERTIES
#----------------------------------------     
    
class KeyingClipCollection(bpy.types.PropertyGroup):
    """Used for storing the information about loaded clips for the clip list."""
    clip_name: bpy.props.StringProperty()
    path: bpy.props.StringProperty()
    icon: bpy.props.StringProperty(default="HIDE_ON")

class KeyingGlobalProps(bpy.types.PropertyGroup):
    """Used for storing all of the global user defined properties."""
    output_path: bpy.props.StringProperty \
      (
      name = "Output",
      default = "C:/",
      description = "Define the output folder",
      subtype = "DIR_PATH"
      )
      
    input_path: bpy.props.StringProperty \
      (
      name = "Input",
      default = "C:/",  
      description = "Define the input folder",
      subtype = "DIR_PATH",
      update = updated_input_path
      )
      
    force_render: bpy.props.BoolProperty \
      (
      name = "Force Render",
      default = False,
      description = "Render all will render even over existing render footage in the output folder."
      )
      
    scene_namespace: bpy.props.StringProperty \
      (
      name = "",
      description = "The prefix for the scenes that are currently being worked on",
      update = updated_namespace
      )
      
    rendering_all: bpy.props.BoolProperty \
      (
      name = "Rendering all",
      default = False
      )
      
    active_clip_index: bpy.props.IntProperty \
      (
      name = "Currently active clip",
      default = -1
      )
      
    auto_backup: bpy.props.BoolProperty \
      (
      name = "Auto Backup",
      default = True,
      description = "Automatically backup the .blend file into output folder when rendering"
      )
      
class KeyingSceneProps(bpy.types.PropertyGroup):
    """Used for storing all of the scene specific user defined settings"""
    render_mask: bpy.props.BoolProperty \
      (
      name = "Render Mask",
      description = "Check if you want to render a mask for the current scene"
      )
      
    auto_frames: bpy.props.BoolProperty \
      (
      name = "Auto Frame Set",
      description = "Set the start and end frames automatically to match clip length",
      update = updated_auto_frames
      )
      
    showing_mask: bpy.props.BoolProperty \
      (
      name = "Showing Mask",
      description = "Check if you want to render a mask for the current scene"
      )
      
      
#----------------------------------------
#   STATES
#----------------------------------------
class BeginState(State):
    """The first state of render all evaluation, prepares the next scene in queue by switching to it.
    If the queue is empty, then FINISHED arguement is returned."""
    def update(self, context):
        if not self._state_machine.render_queue:
            self._state_machine.owner.remove_timer(context)
            return {"FINISHED"} 
        #Setup the next scene
        switch_scene(context, self._state_machine.render_queue[0])
        self._state_machine.render_queue.pop(0)
        self._state_machine.transition_to(PreparedImageState())
        return {"PASS_THROUGH"}
        
class PreparedImageState(State):
    """Begins rendering the image."""
    def update(self, context):
        #File was already rendered previously
        force_render = get_master_scene().keying_global.force_render
        if os.path.exists(get_render_subfolder(context)) and not force_render:
            self._state_machine.transition_to(BeginState())
        else:
            switch_to_video(context)
            self._state_machine.rendering = True
            bpy.ops.keying.render_current()
            self.state_machine.transition_to(RenderedImageState())
        return {"PASS_THROUGH"}
        
class RenderedImageState(State):
    """Checks whether the user has defined mask rendering for the current scene.
    If they did, then the mask view is switched and rendering of the mask begins.
    Otherwise the evaluation returns to the BeginState"""
    def update(self, context):
        if context.scene.keying.render_mask:
            switch_to_mask(context)
            self._state_machine.rendering = True
            bpy.ops.keying.render_current()
            self._state_machine.transition_to(RenderedMaskState())
        else:
            self._state_machine.transition_to(BeginState())
        return {"PASS_THROUGH"}
        
class RenderedMaskState(State):
    """Returns the scene to the previous state and returns the evaluation back to BeginState"""
    def update(self, context):
        switch_to_video(context)
        self._state_machine.transition_to(BeginState())
        return {"PASS_THROUGH"}
        
class CancelledState(State):
    def update(self, context):
        self._state_machine.owner.remove_timer(context)
        return {"FINISHED"}
        

        
#----------------------------------------
#   OPERATORS
#----------------------------------------

class RenderAllCompositeOp(RenderAllOp):
    """Begins the queue rendering process by setting up a modal timer and a new state machine."""
    bl_idname = "keying.keying_render_all"

    def execute(self, context):
        global_props = get_master_scene().keying_global
        self.state_machine = StateMachine(BeginState(), self, global_props)
        if global_props.auto_backup:
            backup_blend_file(global_props.output_path)
        self.setup_timer(context)
        return {"RUNNING_MODAL"}
        
    def on_render_cancel(self, context, dummy):
        self.state_machine.transition_to(CancelledState())
        self.state_machine.rendering = False

class SwitchClipOp(bpy.types.Operator):
    """Switches the scene to the selected clip."""
    bl_idname = "keying.switch_clip"
    bl_label = "Switch to Clip"
    bl_description = "Switches to the clip selected in the list"
    
    def execute(self, context):
        master_scene = get_master_scene()
        
        index = master_scene.clip_list_index
        switch_clip(context, index)
        
        return {"FINISHED"}

class ShowMaskOp(bpy.types.Operator):
    bl_idname = "keying.show_mask"
    bl_label = "Show Mask"
    bl_description = "Switches the compositor to mask view"
    
    def execute(self, context):
        switch_to_mask(context)
        return {"FINISHED"}
    
class ShowVideoOp(bpy.types.Operator):
    bl_idname = "keying.show_video"
    bl_label = "Show Video"
    bl_description = "Switches the compositor to video view"
    
    def execute(self, context):
        switch_to_video(context)
        return {"FINISHED"}
      
class NextOperator(bpy.types.Operator):
    bl_idname = "keying.next"
    bl_label = "Next Clip"
    
    def execute(self, context):
        master_scene = get_master_scene()
        prev_index = get_master_scene().keying_global.active_clip_index
        index = prev_index + 1
        switch_clip(context, index)
        return {"FINISHED"}
    
class PrevOperator(bpy.types.Operator):
    bl_idname = "keying.prev"
    bl_label = "Prev Clip"
    
    def execute(self, context):
        master_scene = get_master_scene()
        prev_index = get_master_scene().keying_global.active_clip_index
        index = prev_index - 1
        switch_clip(context, index)
        return {"FINISHED"}

class RenderOperator(bpy.types.Operator):
    """Renders the current scene into the defined output folder."""
    bl_idname = "keying.render_current"
    bl_label = "Render Current"
    bl_description = "Renders the current clip"
    
    def execute(self, context):
        save_path = get_output_clip_path(context)
        force_render = get_master_scene().keying_global.force_render
        
        render_subfolder = get_render_subfolder(context)
        create_directory(save_path)
        
        if not context.scene.keying.showing_mask:
            create_directory(os.path.join(save_path,"keyframes"))
                
        if os.path.exists(render_subfolder) and not force_render:
            return {"FINISHED"}
        else:
            create_directory(render_subfolder)
        
        updated_auto_frames(self,context)
        context.scene.render.filepath = render_subfolder + os.path.sep
        bpy.ops.render.render("INVOKE_DEFAULT", animation=True, write_still=True)
        return {"FINISHED"}

class DeleteNamespace(bpy.types.Operator):
    bl_idname = "keying.delete_namespace"
    bl_label = "Delete Namespace Scenes"
    bl_description = "Delete all of the scenes in this namespace"
    bl_options = {'REGISTER', 'INTERNAL'}
    
    @classmethod
    
    def poll(cls, context):
        return True

    def execute(self, context):
        namespace = get_master_scene().keying_global.scene_namespace
        scenes = state_machine.filter_scenes(namespace)
        
        for scene_name in scenes:
            scene = bpy.data.scenes[scene_name]
            bpy.data.scenes.remove(scene)
        get_master_scene().keying_global.scene_namespace = ""
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

#----------------------------------------
#   UI
#----------------------------------------   

class KeyingUIList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        split = layout.split(factor = 0.1)
        split.label(text=str(index+1))
        split.label(text=item.clip_name, icon = item.icon)
    
    def invoke(self, context, event):
        pass

class KeyingClipPanel(bpy.types.Panel):
    bl_label = "Effective Keying Clips"
    bl_idname = "SCENE_PT_keying_clips"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "render"
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        box = layout.box()
        box.row().prop(get_master_scene().keying_global, "input_path")
        
        data = get_master_scene()
        box.row().template_list("KeyingUIList", "", data, "clip_list", data, "clip_list_index", rows = 2)
        
        split = box.split()
        split.column().operator("keying.prev")
        split.column().operator("keying.next")
        
        box.row().operator("keying.switch_clip")
        
        box = layout.box()
        
        box.row().label(text = "Current Namespace")
        box.row().prop(get_master_scene().keying_global, "scene_namespace")
        box.row().operator("keying.delete_namespace")
   
class KeyingRenderPanel(bpy.types.Panel):
    bl_label = "Effective Keying Rendering"
    bl_idname = "SCENE_PT_keying_rendering"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "render"


    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        box = layout.box()
        box.row().label(text = "Scene Settings")
        split = box.split()
        split.column().prop(context.scene.keying, "render_mask")
        if context.scene.keying.showing_mask:
            split.column().operator("keying.show_video")
        else:
            split.column().operator("keying.show_mask")
        
        box.row().prop(context.scene.keying, "auto_frames")
        

        box = layout.box()
        box.row().label(text = "Global Settings")
        split = box.split()
        split.column().prop(get_master_scene().keying_global, "force_render")
        split.column().prop(get_master_scene().keying_global, "auto_backup")
        
        box = layout.box()
        box.row().prop(get_master_scene().keying_global, "output_path")
        split = box.split()
        split.column().operator("keying.render_current")
        split.column().operator("keying.keying_render_all")



#----------------------------------------
#   CLASS REGISTER AND UNREGISTER
#----------------------------------------   

classes = (
    KeyingClipPanel,
    KeyingRenderPanel,
    RenderOperator,
    KeyingSceneProps,
    KeyingGlobalProps,
    KeyingUIList,
    NextOperator,
    PrevOperator,
    RenderAllCompositeOp,
    KeyingClipCollection,
    SwitchClipOp,
    ShowMaskOp,
    ShowVideoOp,
    DeleteNamespace,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.keying = bpy.props.PointerProperty(type=KeyingSceneProps)
    bpy.types.Scene.clip_list = bpy.props.CollectionProperty(type=KeyingClipCollection)
    bpy.types.Scene.clip_list_index = bpy.props.IntProperty()
    bpy.types.Scene.keying_global = bpy.props.PointerProperty(type=KeyingGlobalProps)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.keying
    del bpy.types.Scene.clip_list
    del bpy.types.Scene.clip_list_index
    del bpy.types.Scene.keying_global

if __name__ == "__main__":
    register()