# main.py Script for grinder UI
# first prototype is using an OLED and 5V stepper motor
# the display relies on drivers made by Peter Hinch [link]

# Released under the GPL 3.0

# Fonts for Writer
import gui.fonts.freesans20 as freesans20
import gui.fonts.quantico40 as quantico40
from gui.core.writer import CWriter
import time
from machine import Pin,I2C 
from rp2 import PIO, StateMachine, asm_pio
import sys

import time

import math

import machine
import gc

# *** Choose your color display driver here ***
# Driver supporting non-STM platforms
# from drivers.ssd1351.ssd1351_generic import SSD1351 as SSD

# STM specific driver
from drivers.ssd1351.ssd1351 import SSD1351 as SSD

height = 128  # height = 128 # 1.5 inch 128*128 display

pdc = machine.Pin(20, machine.Pin.OUT, value=0)
pcs = machine.Pin(17, machine.Pin.OUT, value=1)
prst = machine.Pin(21, machine.Pin.OUT, value=1)
spi = machine.SPI(0,
                  baudrate=10000000,
                  polarity=1,
                  phase=1,
                  bits=8,
                  firstbit=machine.SPI.MSB,
                  sck=machine.Pin(18),
                  mosi=machine.Pin(19),
                  miso=machine.Pin(16))
gc.collect()  # Precaution before instantiating framebuf
ssd = SSD(spi, pcs, pdc, prst, height)  # Create a display instance

class PCA9685:
    # Registers/etc.
    __SUBADR1            = 0x02
    __SUBADR2            = 0x03
    __SUBADR3            = 0x04
    __MODE1              = 0x00
    __PRESCALE           = 0xFE
    __LED0_ON_L          = 0x06
    __LED0_ON_H          = 0x07
    __LED0_OFF_L         = 0x08
    __LED0_OFF_H         = 0x09
    __ALLLED_ON_L        = 0xFA
    __ALLLED_ON_H        = 0xFB
    __ALLLED_OFF_L       = 0xFC
    __ALLLED_OFF_H       = 0xFD

# soldered jumpers to switch to IC21 
    def __init__(self, address=0x40, debug=False):
        self.i2c = I2C(1, scl=Pin(7), sda=Pin(6), freq=100000)
        self.address = address
        self.debug = debug
        if (self.debug):
            print("Reseting PCA9685") 
        self.write(self.__MODE1, 0x00)
    
    def write(self, cmd, value):
        "Writes an 8-bit value to the specified register/address"
        self.i2c.writeto_mem(int(self.address), int(cmd), bytes([int(value)]))
        if (self.debug):
            print("I2C: Write 0x%02X to register 0x%02X" % (value, cmd))
      
    def read(self, reg):
        "Read an unsigned byte from the I2C device"
        rdate = self.i2c.readfrom_mem(int(self.address), int(reg), 1)
        if (self.debug):
            print("I2C: Device 0x%02X returned 0x%02X from reg 0x%02X" % (self.address, int(reg), rdate[0]))
        return rdate[0]
    
    def setPWMFreq(self, freq):
        "Sets the PWM frequency"
        prescaleval = 25000000.0    # 25MHz
        prescaleval /= 4096.0       # 12-bit
        prescaleval /= float(freq)
        prescaleval -= 1.0
        if (self.debug):
            print("Setting PWM frequency to %d Hz" % freq)
            print("Estimated pre-scale: %d" % prescaleval)
        prescale = math.floor(prescaleval + 0.5)
        if (self.debug):
            print("Final pre-scale: %d" % prescale)

        oldmode = self.read(self.__MODE1)
        #print("oldmode = 0x%02X" %oldmode)
        newmode = (oldmode & 0x7F) | 0x10        # sleep
        self.write(self.__MODE1, newmode)        # go to sleep
        self.write(self.__PRESCALE, int(math.floor(prescale)))
        self.write(self.__MODE1, oldmode)
        time.sleep(0.005)
        self.write(self.__MODE1, oldmode | 0x80)

    def setPWM(self, channel, on, off):
        "Sets a single PWM channel"
        self.write(self.__LED0_ON_L+4*channel, on & 0xFF)
        self.write(self.__LED0_ON_H+4*channel, on >> 8)
        self.write(self.__LED0_OFF_L+4*channel, off & 0xFF)
        self.write(self.__LED0_OFF_H+4*channel, off >> 8)
        if (self.debug):
            print("channel: %d  LED_ON: %d LED_OFF: %d" % (channel,on,off))
      
    def setServoPulse(self, channel, pulse):
        pulse = pulse * (4095 / 100)
        self.setPWM(channel, 0, int(pulse))
    
    def setLevel(self, channel, value):
        if (value == 1):
              self.setPWM(channel, 0, 4095)
        else:
              self.setPWM(channel, 0, 0)

class MotorDriver():
    def __init__(self, debug=False):
        self.debug = debug
        self.pwm = PCA9685()
        self.pwm.setPWMFreq(50)       
        self.MotorPin = ['MA', 0,1,2, 'MB',3,4,5, 'MC',6,7,8, 'MD',9,10,11]
        self.MotorDir = ['forward', 0,1, 'backward',1,0]

    def MotorRun(self, motor, mdir, speed, runtime):
        if speed > 100:
            return
        
        mPin = self.MotorPin.index(motor)
        mDir = self.MotorDir.index(mdir)
        
        if (self.debug):
            print("set PWM PIN %d, speed %d" %(self.MotorPin[mPin+1], speed))
            print("set pin A %d , dir %d" %(self.MotorPin[mPin+2], self.MotorDir[mDir+1]))
            print("set pin b %d , dir %d" %(self.MotorPin[mPin+3], self.MotorDir[mDir+2]))

        self.pwm.setServoPulse(self.MotorPin[mPin+1], speed)        
        self.pwm.setLevel(self.MotorPin[mPin+2], self.MotorDir[mDir+1])
        self.pwm.setLevel(self.MotorPin[mPin+3], self.MotorDir[mDir+2])
        
        time.sleep(runtime)
        self.pwm.setServoPulse(self.MotorPin[mPin+1], 0)
        self.pwm.setLevel(self.MotorPin[mPin+2], 0)
        self.pwm.setLevel(self.MotorPin[mPin+3], 0)

    def MotorStop(self, motor):
        mPin = self.MotorPin.index(motor)
        self.pwm.setServoPulse(self.MotorPin[mPin+1], 0)
        
# define encoder pins 

switch = Pin(4, mode=Pin.IN, pull = Pin.PULL_UP) # inbuilt switch on the rotary encoder, ACTIVE LOW
outA = Pin(2, mode=Pin.IN) # Pin CLK of encoder
outB = Pin(3, mode=Pin.IN) # Pin DT of encoder

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
    
    # read the value of current state of outA pin / CLK pin
    outA_current = outA.value()
    
    # if current state is not same as the last stare , encoder has rotated
    if outA_current != outA_last:
        # read outB pin/ DT pin
        # if DT value is not equal to CLK value
        # rotation is clockwise [or Counterclockwise ---> sensor dependent]
        if outB.value() != outA_current:
            counter += .5
            direction = "Clockwise"
        else:
            counter -= .5
            direction = "Counter Clockwise"
        
        # print the data on screen
        #print("Counter : ", counter, "     |   Direction : ",direction)
        #print("\n")
    
    # update the last state of outA pin / CLK pin with the current state
    outA_last = outA_current
    counter=min(100,counter)
    counter=max(0,counter)
    return(counter)
    

# interrupt handler function (IRQ) for SW (switch) pin
def button(pin):
    # get global variable
    global button_last_state
    global button_current_state
    global stack
    if button_current_state != button_last_state:
        print("Button is Pressed\n")
        number=int(encoder(pin))
        if stack[2]!=number:
            stack.pop(0)
            stack.append(number)
            change=stack[2]-stack[1]
            print("Change",change)           
            dir='ccw'
            if stack[1]-stack[2]>0:
                change=stack[1]-stack[2]
                dir='cw'
            print("Change",change)  
            doaspin(change, dir)
        time.sleep(.1)
        
        button_last_state = button_current_state
    return

def displaynum(num):
    global stack
    #This needs to be fast for nice responsive increments
    #100 increments?
    
    wri = CWriter(ssd,quantico40, fgcolor=255,bgcolor=0)
    CWriter.set_textpos(ssd, 20,0)  # verbose = False to suppress console output
    wri.printstring(str(num)+"   ")
    wrimem = CWriter(ssd,freesans20, fgcolor=255,bgcolor=0)
    CWriter.set_textpos(ssd, 70,0)  
    wrimem.printstring('last three:')
    CWriter.set_textpos(ssd, 100,0)  
    wrimem.printstring(str(stack)+"    ")
    ssd.show()
    return

def doaspin(offset, direction):
    m = MotorDriver()
    print('offset:',float(offset))
    speed=100     
    if direction=='ccw':
        print("motor A backward, speed ",speed,"%, Run for ",offset,"S, then stop")
        m.MotorRun('MA', 'backward', speed,offset )
    else:
        print("motor A forward, speed ",speed,"%, Run for ",offset,"S, then stop")
        m.MotorRun('MA', 'forward', speed,offset )
    return

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
switch.irq(trigger = Pin.IRQ_FALLING,
           handler = button)


# Main Logic
pin=0
stack = []
stack.append(0)
stack.append(0)
stack.append(0)

while True:
    counter=encoder(pin)  
    displaynum(int(counter))
    button_last_state = False # reset button last state to false again ,
                              # totally optional and application dependent,
                              # can also be done from other subroutines
                              # or from the main loop

