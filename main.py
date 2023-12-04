"""
      main.py - a script for making a temperature regulating PID, running using a Raspberry Pi Pico
    First prototype is using an OLED, rotary encoder and a relay switch (linked to heating device of some sort)
    The display uses drivers made by Peter Hinch [link](https://github.com/peterhinch/micropython-nano-gui)
    
     Copyright (C) 2023 Veeb Projects https://veeb.ch

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>

    Fonts for Writer (generated using https://github.com/peterhinch/micropython-font-to-py)
"""


import gui.fonts.freesans20 as freesans20
import gui.fonts.quantico40 as quantico40
from gui.core.writer import CWriter
from gui.core.nanogui import refresh
import utime
from machine import Pin,I2C, SPI
from rp2 import PIO, StateMachine, asm_pio
import sys
import math
import gc
import onewire, ds18x20
# Display setup
from drivers.ssd1351.ssd1351_16bit import SSD1351 as SSD
# Look for thermometer (add OLED complaint if one can't be seen)
ds_pin = Pin(22)
relaypin = Pin(15, mode = Pin.OUT, value =0 )
ds_sensor = ds18x20.DS18X20(onewire.OneWire(ds_pin))
roms = ds_sensor.scan()
print('Thermometer: ', roms)
if roms=='':
    print('No Thermometer. STOP')
    beanaproblem('No Therm.')
    utime.sleep(60)
    sys.exit()

height = 128  
pdc = Pin(20, Pin.OUT, value=0)
pcs = Pin(17, Pin.OUT, value=1)
prst = Pin(21, Pin.OUT, value=1)
spi = SPI(0,
                  baudrate=10000000,
                  polarity=1,
                  phase=1,
                  bits=8,
                  firstbit=SPI.MSB,
                  sck=Pin(18),
                  mosi=Pin(19),
                  miso=Pin(16))
gc.collect()  # Precaution before instantiating framebuf
ssd = SSD(spi, pcs, pdc, prst, height)  # Create a display instance
ssd.fill(0)

wri = CWriter(ssd,freesans20, fgcolor=SSD.rgb(100,100,100),bgcolor=0)
CWriter.set_textpos(ssd, 45,51)
wri.printstring(':-)')
CWriter.set_textpos(ssd, 90,25)
wri.printstring('veeb.ch/')

ssd.show()
utime.sleep(4)

# define encoder pins 

switch = Pin(4, mode=Pin.IN, pull = Pin.PULL_UP) # inbuilt switch on the rotary encoder, ACTIVE LOW
outA = Pin(2, mode=Pin.IN) # Pin CLK of encoder
outB = Pin(3, mode=Pin.IN) # Pin DT of encoder

# Define LED pin

ledPin = Pin(25, mode = Pin.OUT, value = 0) # Onboard led on GPIO 25


# define global variables
counter = 0   # counter updates when encoder rotates
direction = "" # empty string for registering direction change
outA_last = 0 # registers the last state of outA pin / CLK pin
outA_current = 0 # registers the current state of outA pin / CLK pin

button_last_state = False # initial state of encoder's button 
button_current_state = "" # empty string ---> current state of button

# Read the last state of CLK pin in the initialisaton phase of the program 
outA_last = outA.value() # lastStateCLK

# interrupt handler function (IRQ) for CLK and DT pins
def encoder(pin):
    # get global variables
    global counter
    global direction
    global outA_last
    global outA_current
    global outA
    
    # read the value of current state of outA pin / CLK pin
    try:
        outA_current = outA.value()
    except:
        print('outA not defined')
        outA_current = 0
        outA_last = 0
    # if current state is not same as the last stare , encoder has rotated
    if outA_current != outA_last:
        # read outB pin/ DT pin
        # if DT value is not equal to CLK value
        # rotation is clockwise [or Counterclockwise ---> sensor dependent]
        if outB.value() != outA_current:
            counter += .05
        else:
            counter -= .05
        
        # print the data on screen
        #print("Counter : ", counter, "     |   Direction : ",direction)
        #print("\n")
    
    # update the last state of outA pin / CLK pin with the current state
    outA_last = outA_current
    counter=min(90,counter)
    counter=max(45,counter)
    return(counter)
    

# interrupt handler function (IRQ) for SW (switch) pin
def button(pin):
    # get global variable
    global button_last_state
    global button_current_state
    global powerup
    if button_current_state != button_last_state:
        utime.sleep(.2)       
        button_last_state = button_current_state
#        powerup = not powerup                    # Toggle power flag - disabled for now
        print('power:'+str(powerup))
    return

# Screen to display on OLED during heating
def displaynum(num,temperature):
    ssd.fill(0)
    #This needs to be fast for nice responsive increments
    #100 increments?
    delta=num-temperature
    text=SSD.rgb(0,255,0)
    if abs(delta)>=1:
        text=SSD.rgb(255,0,0)
    wri = CWriter(ssd,quantico40, fgcolor=text,bgcolor=0)
    CWriter.set_textpos(ssd, 35,0)  # verbose = False to suppress console output
    wri.printstring(str("{:.1f}".format(num)))
    wrimem = CWriter(ssd,freesans20, fgcolor=SSD.rgb(255,255,255),bgcolor=0)
    CWriter.set_textpos(ssd, 90,0)  
    wrimem.printstring('actual: '+str("{:.1f}".format(temperature))+" C ")
    
    ssd.show()
    return

def beanaproblem(string):
    refresh(ssd, True)  # Clear any prior image
    relaypin.value(0)
    utime.sleep(2)
    
# Attach interrupt to Pins

# attach interrupt to the outA pin ( CLK pin of encoder module )
outA.irq(trigger = Pin.IRQ_RISING | Pin.IRQ_FALLING,
              handler = encoder)

# attach interrupt to the outB pin ( DT pin of encoder module )
outB.irq(trigger = Pin.IRQ_RISING | Pin.IRQ_FALLING ,
              handler = encoder)

# attach interrupt to the switch pin ( SW pin of encoder module )
switch.irq(trigger = Pin.IRQ_FALLING ,
           handler = button)


# Main Logic
pin=0
counter= 54.5
integral = 0
lastupdate = utime.time()  
refresh(ssd, True)  # Initialise and clear display.

lasterror = 0
# The Tweakable values that will help tune for our use case. TODO: Make accessible via menu on OLED
checkin = 5
# Explanation Stolen From Reddit: In terms of steering a ship:
# Kp is steering harder the further off course you are,
# Ki is steering into the wind to counteract a drift
# Kd is slowing the turn as you approach your course
Kp=20.   # Proportional term - Basic steering (This is the first parameter you should tune for a particular setup)
Ki=.01   # Integral term - Compensate for heat loss by vessel
Kd=150.  # Derivative term - to prevent overshoot due to inertia - if it is zooming towards setpoint this
         # will cancel out the proportional term due to the large negative gradient
output=0
offstate=False
boil = False  # The override flag that will just get to a boil as quick as possible. (Assumes water at sea level, which is ok for now)
# Heating loop - Default behaviour
powerup = True
while True:
    if powerup:
        try:
            counter=encoder(pin)
            # If the counter is set to 100 and we assume we're heating water, 100 degrees is as hot as the water can get,
            # so the output should just be set to 100 until the target is reached. Much quicker for this use case.
            if counter==100:
                boil = True
            else:
                boil = False
            ds_sensor.convert_temp()
            temp = ds_sensor.read_temp(roms[0])
            displaynum(counter,float(temp))
            button_last_state = False # reset button last state to false again ,
                                      # totally optional and application dependent,
                                      # can also be done from other subroutines
                                      # or from the main loop
            now = utime.time()
            dt= now-lastupdate
            if output<100 and offstate == False and dt > checkin * round(output)/100 :
                relaypin = Pin(15, mode = Pin.OUT, value =0 )
                offstate= True
                utime.sleep(.1)
            if dt > checkin:
                error=counter-temp
                integral = integral + dt * error
                derivative = (error - lasterror)/dt
                output = Kp * error + Ki * integral + Kd * derivative
                print(str(output)+"= Kp term: "+str(Kp*error)+" + Ki term:" + str(Ki*integral) + "+ Kd term: " + str(Kd*derivative))
                output = max(min(100, output), 0) # Clamp output between 0 and 100
                if boil and error>.5:
                    output=100
                print(output)
                if output>0:  
                    relaypin.value(1)
                    offstate = False
                else:
                    relaypine.value(0)
                    offstate = True
                utime.sleep(.1)
                lastupdate = now
                lasterror = error
        except Exception as e:
            # Put something to output to OLED screen
            beanaproblem('error.')
            print('error encountered:'+str(e))
            utime.sleep(checkin)
    else:
        if button_last_state == False:  # To prevent clearing on every cycle when power off
            refresh(ssd, True)  # Clear any prior image
            relaypin = Pin(15, mode = Pin.OUT, value =0 ) 
        

