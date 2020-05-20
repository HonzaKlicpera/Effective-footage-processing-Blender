# A blender add-on for effective processing of greenscreen footage
This Blender add-on partly automates the process of editing greenscreen footage. The processed footage then stylized with for EbSynth to be later used in the Unity game engine. It allows to import and render footage in bulk, without the need to switch folders for each clip or render them individually.

This Blender add-on partly automates the process of editing (stabilizing, chroma keying and cropping) live-action greenscreen footage in bulk. It is made specially for synthesizing the processed image using EbSynth and utilizing it in the Unity game engine, but it can be used for basic chroma keying purposes as well.

## Instalation
1. Download the `Effective_processing_addon.zip` file from the latest release.
2. In Blender, go to Edit->Preferences->Add-ons->Install.
3. Navigate to the downloaded zip file and select it.
4. Enable the add-on.

## User Manual
The user interface for the addon is located in the properties editor, in the render properties tab. It is split into two panels, one used for importing the clips and switching between them and the second one for setting render options and rendering in bulk.

### Preparing the Compositor
The compositor must first be prepared with the editing nodes. You can either download a basic project `Sheepless_base_project.blend` from the latest release, containing the setup, or recreate it based on the following image:

![Compositor Nodes](https://github.com/HonzaKlicpera/Effective-footage-processing-Blender/blob/master/images/BlenderChromaNodes.png "Compositor Nodes")

*Note: the node setup does not have to exactly match the image, adjustments can be made. For switching between the image and mask view, however, the Keying and Crop nodes have to be kept next to each other, as those get rerouted by the script automatically. It is also mandatory for the script to work to have the following nodes: Movie Clip; Stabilize 2D; Keying; Crop*

### Effective Keying Clips Panel
![Clips Panel UI](https://github.com/HonzaKlicpera/Effective-footage-processing-Blender/blob/master/images/Sheepless_clips_UI.png "Clips panel UI")

This panel allows to define the folder containing all of the clips you want to edit. These clips will be loaded into the interactive list. You can switch between clips using the buttons below the list. The icon next to the clip's name in the list indicates, whether it has been visited, or is currently active.

### Effective Keying Rendering Panel
![Rendering Panel UI](https://github.com/HonzaKlicpera/Effective-footage-processing-Blender/blob/master/images/Sheepless_Rendering_UI.png "Rendering Panel UI")

This panel allows to set the following settings:
* **Render Mask** - Indicates, whether the mask will be also rendered **for the current clip** during the batch rendering process.
* **Auto Frame Set** - Indicates, whether the frame range to be rendered **for the current clip** should be automatically set to match the clip's frame count.
* **Force Render** - Indicates, whether already existing renderings should be overwritten during the batch rendering process.
* **Auto Backup** - Indicates, whether the blend file should be saved into the output folder during the batch rendering process.

When done editing all of the clips, the user can select the desired output folder and press the *Render All* button. The batch rendering process will begin and all of the clips will be automatically rendered into the output folder in the following structure:

![Render folder structure](https://github.com/HonzaKlicpera/Effective-footage-processing-Blender/blob/master/images/folder_structure.png "Render folder structure")

