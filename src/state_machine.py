import bpy
import os
from pathlib import Path
from abc import ABC, abstractmethod
import time
import datetime


def filter_scenes(scene_prefix):
    """Returns all scene names starting with the given prefix."""
    scenes = bpy.data.scenes.keys()
    filtered = list(filter(lambda x: x.startswith(scene_prefix + "/"),scenes))
    return filtered
    
#----------------------------------------
#   STATES
#----------------------------------------
class State(ABC): pass

class StateMachine(ABC):
    state = None

    render_queue = None
    rendering = False
    owner = None
    
    def transition_to(self, state: State):
        self.state = state
        self.state.state_machine = self
    
    def __init__(self, state: State, owner, global_props) -> None:
        self.transition_to(state)
        self.rendering = False
        self.owner = owner
            
        namespace = global_props.scene_namespace
        self.render_queue = filter_scenes(namespace)
        
    def update(self, context):
        return self.state.update(context)
        
class State(ABC):
    @property
    def state_machine(self) -> StateMachine:
        return self._state_machine

    @state_machine.setter
    def state_machine(self, state_machine: StateMachine) -> None:
        self._state_machine = state_machine
    
    @abstractmethod
    def update(self, context):
        pass

        
#----------------------------------------
#   OPERATORS
#----------------------------------------

class RenderAllOp(bpy.types.Operator):
    bl_label = "Render All"
    bl_description = "Renders all visited clips"
    
    state_machine = None
    timer_event = None

    def setup_timer(self, context):
        bpy.app.handlers.render_complete.append(self.complete_render)
        bpy.app.handlers.render_cancel.append(self.on_render_cancel)
        #Create timer event that runs every second to check if render renderQueue needs to be updated
        self.timer_event = context.window_manager.event_timer_add(1.0, window=context.window)
        #register this as running in background 
        context.window_manager.modal_handler_add(self)
    
    def remove_timer(self, context):
        bpy.app.handlers.render_complete.remove(self.complete_render)
        bpy.app.handlers.render_cancel.remove(self.on_render_cancel)
        context.window_manager.event_timer_remove(self.timer_event)
        self.report({"INFO"},"RENDER QUEUE FINISHED")
        
    def modal(self, context, event):
        print(event)
        if event.type == "TIMER" and self.state_machine.rendering is False:
            return self.state_machine.update(context)
        return {"PASS_THROUGH"}
    
    def complete_render(self, context, dummy):
        self.state_machine.rendering = False
        


