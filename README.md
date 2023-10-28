![An abandoned (for now) splashpage design](/heatomatic.jpg)

[![YouTube Channel Views](https://img.shields.io/youtube/channel/views/UCz5BOU9J9pB_O0B8-rDjCWQ?label=YouTube&style=social)](https://www.youtube.com/channel/UCz5BOU9J9pB_O0B8-rDjCWQ)

[![Instagram](https://img.shields.io/badge/Instagram-E4405F?style=for-the-badge&logo=instagram&logoColor=white)](https://www.instagram.com/v_e_e_b/)

# Heat-o-matic

A [proportional integral derivative](https://en.wikipedia.org/wiki/PID_controller) (PID) controller that will be used to run a home-made precision heater and can be useful for various applications.There are some example applications in the video section, but there are of tons other possible use-cases. 

PID is a fancy way of saying that the code plays a game of 'Warmer', 'Colder' to get something to a particular value (in our example, a particular temperature). The internet is littered with examples of these things, so it is primarily a didactic exercise that will use a few bits of code we've previously developed, and hopefully it will make us a little smarter along the way.

(You can use the PID controller to regulate other things, depending on the sensor and device being powered. It just needs to measure **X**, and then to be able to influence **X**. People have used PID controllers to make robots follow lines, self-balance, [maintain mosture content in soil](https://github.com/veeb.ch/sploosh),  and loads of other things I can't think of right now)

# Hardware

- Raspberry Pi Pico  (Pico W not needed here)
- SSD1351 Waveshare OLED 
- WGCD KY-040 Rotary Encoder
- DS18B20 Stainless Steel Temperature Sensor (with 5K1 pull-up resistor)
- A relay switch ([seeed 103020005](https://www.seeedstudio.com/Grove-Relay.html))
- A plug socket for the heating device. For cooking, we use one of [these](https://www.galaxus.ch/de/s2/product/rommelsbacher-ts1502-wasserkocher-8406453?supplier=406802)
- Wires Galore

**Warning: Don't generate heat using something that dislikes being power-cycled a lot. This is GPL code, ie NO WARRANTY**

# Installing Heat-o-matic onto a Pico

First flash the board with the latest version of [micropython](https://micropython.org/download/RPI_PICO/). 

Then clone this repository onto your computer

     git clone https://github.com/veebch/heat-o-matic

and move into the repository directory

     cd heat-o-matic

There are a few files to copy to the pico, [ampy](https://learn.adafruit.com/micropython-basics-load-files-and-run-code/install-ampy) is a good way to do it.

     sudo ampy -p /dev/ttyACM0 put ./
     
substitute the device name to whatever the pico is on your system.

# Wiring

All of the pins are listed in main.py. Note that the temperature sensor needed a pull-up resistor on the signal. Also, the switch on the roatary encoder (that was being used as a means to toggle the UI) is disabled as it was being triggered by the relay.... this can probably be fixed with a capacitor. 

- The data lines of the OLED connect to the GPIO as follows:

| [Pico GPIO](https://www.elektronik-kompendium.de/sites/raspberry-pi/bilder/raspberry-pi-pico-gpio.png) | OLED |
|-----------|------|
|   19       | DIN/MOSI  |
|   18      | CLK/SCK  |
|   17      | CS  |
|   20       | DC  |
|   21      | RST  |


- The Rotary Encoder connects to the GPIO as follows:

| [Pico GPIO](https://www.elektronik-kompendium.de/sites/raspberry-pi/bilder/raspberry-pi-pico-gpio.png) | Rotary Encoder |
|-----------|----------------|
|   2       | CLK            |
|   3       | DT             |

(GND and VCC are both connected to the Pico pins too)

# Using heat-o-matic

Plug it in, pop the temperature probe into the medium you are going to heat, plug the heat-providing device into the plug socket, pick a setpoint using the dial. That's it!

# Video 

[![Cooking With Micropython](http://img.youtube.com/vi/rooKTWVzXWw/0.jpg)](http://www.youtube.com/watch?v=rooKTWVzXWw "Video Title")

From GitHub to GutGrub. Thank you, thank you, I'm here all week, don't forget to tip your waitress.

# Contributing to the code

If you look at this and feel like you can make it better, please fork the repository and use a feature branch. Pull requests are welcome and encouraged.

# Licence 
GPL 3.0
