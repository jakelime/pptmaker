Configurations
==============
TETK implements the use of YAML to allow users to specify software configurations.

|

How to use Recipes
------------------
Recipe(s) are a different set of instructions for the application to function differently. It enables the app to support
across a multitude of different products with different specifications. The general use case instruction is as follow:

#. Use the GUI *TETK File Menu* -> *Open config folder*. Alternatively, you can find the *_TOOLS_TETK*/*_configurations* folder from *My Documents* in your Operating System

#. All *.yml* files in this folder will be process and loaded into the recipe menu.

   .. figure:: images/showcase-recipeMenu.png
      :alt: Image, open config folder and recipe menu
      :align: center
      :width: 300px

      A screenshot of the *File Menu*: *Open Config Folder* and *Choose Recipes*

#. Choose *project.yml* to load the recipe settings. You can duplicate from template and create any number
   of recipes. In case of recipe failures, you can use the *reset factory settings* function from *File Menu*.

|


General settings
----------------

| Mostly self-explanatory.
| More details can be updated later.

.. code-block:: python

   ## Recipe version changes
   # v0.0.1     initial release
   # v0.0.2     updated. added features in 0.1.0

   recipe_version: 0.0.2
   project_name: oca_img_profile
   user_OS_default: '~/Documents/'
   user_working_dir_name: _TOOLS-tetk
   folders_key_names:
     ## dict{} or dict{key:str = foldername:str}
     inpf01: 00-input-folder
     outf01: 01-output-plots
     outf02: 02-output-plots_individual
     outf03: 03-output-ppt
     outf04: 04-output-debugging
   files_key_names:
     ## dict{} or dict{key:str = filename:str}
     recipe1: oca.yml
     ppt_template1: ppt_template01.pptx
   folders_to_clear: ['outf01', 'outf02', 'outf03', 'outf04']
   auto_check_sn: True
   debug_mode: False

   variable_configurations:
     SERIALNUMBER: SerialNumber

   xy_data_reader:
     header_configurations:
       header: null
       nrows: 3
       serialnumber_data_row: 0
       groups:
         radiometry_data_row: 1
         axis_data_row: 2

   xy_plot_settings:
     default_figsize: [8, 6]
     seaborn_style: darkgrid  # [white, dark, whitegrid, darkgrid]
     seaborn_context: notebook  # [null, talk, poster, notebook]
     seaborn_context_fontscale: 0.8
     self_normalise: True

   grouped_stacked_plot_settings:
     image_format: png
     figsize: [10,5]
     groups: ["irr", "radiant"]
     layout: [ ["hor", "ver"], ["3-1", "2-4"] ]

   grouped_side_by_side_plot_settings:
     image_format: png
     figsize: [10,3]
     groups: ["irr", "radiant"]
     layout: [ ["hor", "ver"], ["3-1", "2-4"] ]

   individual_plot_settings:
     image_format: png
     figsize: [8,6]

   powerpoint_maker_settings:
     image_format: png

   interactive_plotter_settings:
     color_wheel: ["#FB9902", "#0247FE", "#9A0794", "#7FBD32", "#EA202C", "#347B98", "#FC600A"]
     sections: ['Section Hor', 'Section Ver', 'Section Diag2-4', 'Section Diag3-1']
     groups: ["irr", "radiant"]  # list[str], or [] to disable

|

.. automodule:: config
   :members:
   :undoc-members:
   :show-inheritance:
