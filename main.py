# main.py - a script for making a temperature regulating PID, running using a Raspberry Pi Pico
# First prototype is using an OLED, rotary encoder and a relay switch (linked to heating device of some sort)
# The display relies on drivers made by Peter Hinch [link](https://github.com/peterhinch/micropython-nano-gui)

# Released under the GPL 3.0

# Fonts for Writer (generated using https://github.com/peterhinch/micropython-font-to-py)

import gui.fonts.freesans20 as freesans20
import gui.fonts.quantico40 as quantico40
from gui.core.writer import CWriter
from gui.core.colors import RED, BLUE, GREEN
from gui.core.nanogui import refresh
import utime
from machine import Pin,I2C, SPI
from rp2 import PIO, StateMachine, asm_pio
import sys
import math
import gc
import onewire, ds18x20
# Display setup
from drivers.ssd1351.ssd1351 import SSD1351 as SSD

# Look for thermometer (add OLED complaint if one can't be seen)
ds_pin = Pin(22)
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

# define encoder pins 

switch = Pin(4, mode=Pin.IN, pull = Pin.PULL_UP) # inbuilt switch on the rotary encoder, ACTIVE LOW
outA = Pin(2, mode=Pin.IN) # Pin CLK of encoder
outB = Pin(3, mode=Pin.IN) # Pin DT of encoder

# Define relay and LED pins

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
    outA_current = outA.value()
    
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
        togglesleep()
        utime.sleep(.2)       
        button_last_state = button_current_state
        powerup = not powerup
        print('power:'+str(powerup))
    return

# Screen to display on OLED during heating
def displaynum(num,temperature):
    #This needs to be fast for nice responsive increments
    #100 increments?
    delta=num-temperature
    text=GREEN
    if abs(delta)>.3:
        text=RED
    wri = CWriter(ssd,quantico40, fgcolor=text,bgcolor=0)
    CWriter.set_textpos(ssd, 35,0)  # verbose = False to suppress console output
    wri.printstring(str("{:.1f}".format(num))+" ")
    wrimem = CWriter(ssd,freesans20, fgcolor=255,bgcolor=0)
    CWriter.set_textpos(ssd, 90,0)  
    wrimem.printstring('actual: '+str("{:.1f}".format(temperature))+" C ")
    
    ssd.show()
    return

def beanaproblem(string):
    refresh(ssd, True)  # Clear any prior image
    relaypin = Pin(15, mode = Pin.OUT, value =0 )
    utime.sleep(2)
    
def togglesleep():
    relaypin = Pin(15, mode = Pin.OUT, value =0 )
    
# Attach interrupt to Pins
""" If you need to write a program which triggers an interrupt whenever
    a pin changes, without caring whether it’s rising or falling,
    you can combine the two triggers using a pipe or
    a vertical bar symbol ( | ) . Logical AND """

# attach interrupt to the outA pin ( CLK pin of encoder module )
outA.irq(trigger = Pin.IRQ_RISING | Pin.IRQ_FALLING,
              handler = encoder)

# attach interrupt to the outB pin ( DT pin of encoder module )
outB.irq(trigger = Pin.IRQ_RISING | Pin.IRQ_FALLING ,
              handler = encoder)

# attach interrupt to the switch pin ( SW pin of encoder module )
switch.irq(trigger = Pin.IRQ_FALLING | Pin.IRQ_RISING ,
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
# Stolen From Reddit: In terms of steering a ship:
# Kp is steering harder the further off course you are,
# Ki is steering into the wind to counteract a drift
# Kd is slowing the turn as you approach your course
Kp=75.   # Proportional term - Basic steering
Ki=.01   # Integral term - Compensate for heat loss by vessel
Kd=200.  # Derivative term - to prevent overshoot due to inertia - if it is zooming towards setpoint this
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
                lastupdate = now
                lasterror = error
                output = Kp * error + Ki * integral + Kd * derivative
                print(str(output)+"= Kp term: "+str(Kp*error)+" + Ki term:" + str(Ki*integral) + "+ Kd term: " + str(Kd*derivative))
                output = max(min(100, output), 0) # Clamp output between 0 and 100
                if boil:
                    output=100
                print(output)
                if output>30.:  # If output is more than 30 percent, turn on the heater. Otherwise don't turn it on at all (not enough time for it to warm up)
                    relaypin = Pin(15, mode = Pin.OUT, value =1 )
                    offstate = False
                else:
                    relaypin = Pin(15, mode = Pin.OUT, value =0 )
                    offstate = True
                utime.sleep(.1)
        except Exception as e:
            # Put something to output to OLED screen
            beanaproblem('error.')
            print('error encountered:'+str(e))
            utime.sleep(checkin)
    else:
        refresh(ssd, True)  # Clear any prior image

