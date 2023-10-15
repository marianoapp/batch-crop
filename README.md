Batch cropper
=============

Batch crop images to the desired aspect ratio

## Requirements
* Python 3
* OpenCV
`pip install opencv-python`
* keyboard
`pip install keyboard`

Alternatively use the pre-built Windows executable available [here](https://github.com/marianoapp/batch-crop/releases/latest)

## Usage
Edit the config file and set the desired aspect ratio, the folder where to look for images and the folder where to save the cropped images

## Key bindings
* `arrow keys` Move the crop window
    * `ctrl` Move the crop window in big steps
    * `shift` Snap the crop window to the edge
* `space bar` Crop and save the image
* `p` Force portrait crop window
* `l` Force landscape crop window
* `s` Skip the current image
* `q` Quit
