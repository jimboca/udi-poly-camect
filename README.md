# Camect Nodeserver

This is a Polyglot Nodeserver for the [Universal Devices](https://www.universal-devices.com/) ISY to integrate the [Camect](http://camect.com) System.

This is the initial version so it may change drastically but you are welcome to test and give feedback.

## Installation

Install from the Polyglot Store.  See [Configuration](POLYGLOT_CONFIG.md) on the configuration page after installing.

## Requirements

This has been tested on an RPI running the latest Buster release and the Polisy.  
- You must have Python verison 3.6 or newer.
- This uses the [Camect Python Library](https://github.com/camect/camect-py)

## Using this Nodeserver

After configuring you should get a Node for each Camera, and under each Camera an ObjectDetected node for each type of object currently detected by Camect.

### Controller

The conroller looks like this:
![The Controller](pics/Controller.png)
The Status shows:
    - Nodeserver Online: Nodeserver connected to Polyglot
    - Camect Connected: Status of connection to your Camect
    - Logger Level: The current Logging level
The Controls available:
    - Logger Level
        Usually set to Warning, unless you are debugging issues and want to see all information, but this will use up a lot of disk space. 
        - Debug + Modules: All Debug including referenced modules
        - Debug
        - Info
        - Warning
        - Error

### Camera

A node is created for each Camera:
![A Camera Node](pics/Camera.png)
The Status shows:
    - Enabled: If the Camera is enabled
    - Alerting: If the Camera is sending Alerts
    - Streaming: If the Camera is streaming
The Controls Available:
    - Enabled: [Coming soon](https://github.com/jimboca/udi-poly-Camect/issues/1)
    - Alerting: [Coming soon](https://github.com/jimboca/udi-poly-Camect/issues/2)

### Detected Object

The Camera nodes all have a child node for each known detected object type by Camect.  For comments see [Allow user to control what time of objects they want to detect?](https://github.com/jimboca/udi-poly-Camect/issues/4)
When the object is detected the ST is set to True and a DON is sent.  The status remains True until a different type of obejct is detected See: [Should timeout be set for detected object #3
](https://github.com/jimboca/udi-poly-Camect/issues/3)
![A Detected Object](pics/DetectedObject.png)
The Status Shows:
    - Detected: True when object has been detected

#### How to use Detected Objects

You can create a program to know when a Skunk enters your front yard ![Skunk Program](pics/ProgramSkunk.png)

You can add the nodes to a scene to know when a Skunk enters the front yard ![Skunk Scene](pics/SceneSkunk.png)

## Version History

- 0.0.4
    - Changed methods used to send DON so it's clear in the log
    - Fixed profile for Controller GV2 name
- 0.0.3
    - Fixed event passing, and receiving DON/DOF's in DetectedObject's
- 0.0.2
    - First working version
- 0.0.1
    - First release
