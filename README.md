# YoloTrafficCounter

A Python implementation of Ultralytics YoloV8 for Traffic Counting, used for studying purposes of OpenCV/Computer Vision

## Prerequisites:

* Python 3.12.3 with requirements.txt modules
* Windows 10/11 (OS Module)
* Video Source (Webcam preferably a USB one, .mp4 file or RTSP Stream Link)

## Project Structure:

- src/main.py - Where the magic works
- src/config.yaml - Where most of your configurations like video_source, roi_region and ROI line are set
- src/get_roi.py - A simple Python Script to load your video source so you can get ROI coordinates with ease

## Installation and Usage

### Initial Setup

You can start by cloning the repo

```
git clone https://github.com/ZaleskiThiago/YoloTrafficCounter.git
```

After that you can navigate to the project directory by using

```
cd YoloTrafficCounter
```

if you try to run it without the requirements, or a Module is missing, the main.py file would return the missing module that is needed, but you can make sure by using:

```
pip install -r requirements.txt
```

### Config.yaml file

Check the config.yaml file for in-depth explanation for each config item (and note that some features are still being implemented)

But make sure to point to your video location first

### get_roi.py file

If you need to setup a ROI (Region of Interest), after setting up the video location in config.yaml you can simply run (line by line):

```
cd src
python get_roi.py
```

tne output will be in full var:value format for the .yaml file

You can use the info to set your line_position var too, and line_direction in case if you need a vertical approach

### main.py file

After settiing up all infos at config.yaml, you can run the main.py file with (make sure to be on src):

```
python main.py
```

The first run will download the Yolo model, to the src folder, if you already have one, you can simply paste it on \src

### Yolo Usage:

Yolo is free for personal, educational, and research use under the  **AGPL-3.0 license** (so as this project), but **not for commercial use** without a paid license, if you are looking at this project for commercial usage, consider going to Ultralytics and aquire a proper license, and don't forget to credit it in your project

### Credits:

* [Python](https://www.python.org/) - for existing and being my main coding language 🐍♥
* [OpenCV](https://opencv.org/) - for the main Computer Vision lib and [Numpy](https://numpy.org/) for being part of its usage
* [Ultralytics ](https://github.com/ultralytics/ultralytics)- for the Yolo Image Recognition under the hood of this project
* [Openpyxl](https://pypi.org/project/openpyxl/) - for the amazing excel writer
* [PyYaml](https://pyyaml.org/) - for the Yaml lib to implement config segregation from code
