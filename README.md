[![YouTube Channel Views](https://img.shields.io/youtube/channel/views/UCz5BOU9J9pB_O0B8-rDjCWQ?label=YouTube&style=social)](https://www.youtube.com/channel/UCz5BOU9J9pB_O0B8-rDjCWQ)

# Lazycook

A [proportional integral derivative](https://en.wikipedia.org/wiki/PID_controller) (PID) controller that will be used to run a home-made immersion circulator. PID is a fancy way of saying that the code plays a game of 'Warmer', 'Colder' to get something to a particular value (in our example, a particular temperature). The internet is littered with examples of these things, so it is primarily a didactic exercise that will use a few bits of code we've previously developed, and hopefully it will make us a little smarter along the way.

# Hardware

- Raspberry Pi Pico 
- SSD1351 Waveshare OLED 
- WGCD KY-040 Rotary Encoder
- DS18B20 Stainless Steel Temperature Sensor
- A relay switch
- A plug socket for the heating device, we use one of [these](https://www.galaxus.ch/de/s2/product/rommelsbacher-ts1502-wasserkocher-8406453?supplier=406802)
- Wires Galore

**Warning: Don't generate heat using something that dislikes being power-cycled a lot. This is GPL code.Yada yada NO WARRANTY**

# Installing Lazycook onto a Pico

First flash the board with the latest version of micropython. 

Then clone this repository onto your computer

     git clone https://github.com/veebch/lazycook

and move into the repository directory

     cd lazycook

There are a few files to copy to the pico, [ampy](https://learn.adafruit.com/micropython-basics-load-files-and-run-code/install-ampy) is a good way to do it.

     sudo ampy -p /dev/ttyACM0 put ./
     
substitute the device name to whatever the pico is on your system.

# Wiring

Insert wiring diagram

# Using Lazycook

Plug it in, pop the temperature probe into the medium you are going to heat, plug the heat-providing device into the plug socket, pick a setpoint using the dial. That's it!

# Video 

From GitHub to GutGrub. Thank you, thank you, I'm here all week, don't forget to tip your waitress.

# Contributing to the code

If you look at this and think you can make it better, please fork the repository and use a feature branch. Pull requests are welcome and encouraged.

# Licence 
GPL 3.0
