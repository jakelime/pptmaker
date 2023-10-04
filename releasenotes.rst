#############
Release Notes
#############

- v1.0.0

  - KEY Feature: Detects
    - wafer images in ``input folder``
    - sorts, throwaway (discard)
    - hashmapping for other functions
    - display to UI for debugging

  - KEY Feature: Plot all images, in a lot per slide

  - KEY Feature: Plot all images, 1-to-1 comparison

  - Features:
    - Debug with text output window
    - Configurable config.yml file
    - Easy to use UI
    - Factory reset function

- v1.2.0

  - Added error catching features
    - Use debug=True in configuration file
    - Hashmap of input file to aid in debugging
  - Used error catching to bypass exception if a single 
    image failed
    - Bad image will be skipped
    - The coor_x, coor_y of the bad image will be empty,
      but subsequent images will continue processing

      