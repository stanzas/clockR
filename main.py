import RPi.GPIO as GPIO
import sys
import os
import time
from datetime import datetime
import tm1637
import subprocess

BTN_ONE = 17
BTN_TWO = 27
BTN_THREE = 22
iBrightness = 7

# set the 7-segments display
tm = tm1637.TM1637(clk=5, dio=4)
tm.brightness(iBrightness)

# Get current time
now = datetime.now()

# set the buttons
GPIO.setmode(GPIO.BCM)
GPIO.setup(BTN_ONE, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(BTN_TWO, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(BTN_THREE, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Button 1 => display time
def button1(channel):
  global nCommand
  print("button1 pressed")
  nCommand = 1

# Button 2 => show Mod2
def button2(channel):
  global nCommand
  print("button2 pressed")
  nCommand = 2

# Buton 3 => brightness
def button3(channel):
  global iBrightness
  if (iBrightness >= 7):
    iBrightness = 0
  else:
    iBrightness = iBrightness + 1
  tm.brightness(iBrightness)
  print("button3 pressed - ", iBrightness)


def fCommands():
  global nCommand, nDisplay, bIsWifiActivated
  # == commands ==
  if (nCommand == 1):
    nCommand = 0
    nDisplay = 1
  elif (nCommand == 2):
    nCommand = 0
    nDisplay = 2
    if (bIsWifiActivated == 1):
#      cmd = 'ifconfig wlan0 down'
#      os.system(cmd)
      subprocess.call(["sudo","ifconfig","wlan0","down"])
      bIsWifiActivated = 0
    else:
#      cmd = 'ifconfig wlan0 up'
#      os.system(cmd)
      subprocess.call(["sudo","ifconfig","wlan0","up"])
      bIsWifiActivated = 1

def fDisplay():
  global nDisplay, x
  # display time
  if (nDisplay == 1):
    if (x!=1):
      tm.numbers(now.hour, now.minute)
      x = 1
    else:
      tm.show(now.strftime("%H%M"))
      x = 0

  # display
  elif (nDisplay == 2):
    if (bIsWifiActivated == 1):
      tm.show("WOFF")
    else:
      tm.show("WON-")


# when a falling edge is detected on port 17, regardless of whatever
# else is happening in the program, the function my_callback will be run
GPIO.add_event_detect(BTN_ONE, GPIO.FALLING, callback=button1, bouncetime=300)
GPIO.add_event_detect(BTN_TWO, GPIO.FALLING, callback=button2, bouncetime=300)
GPIO.add_event_detect(BTN_THREE, GPIO.FALLING, callback=button3, bouncetime=300)

bIsWifiActivated = 1
nDisplay = 1
nCommand = 0
x = 0
iBrightness = 0
tm.brightness(iBrightness)
while True:
  fCommands()
  fDisplay()
  time.sleep(1)

GPIO.cleanup()
sys.exit()

#------------------------------------
# all LEDS on "88:88"
tm.write([127, 255, 127, 127])

# all LEDS off
tm.write([0, 0, 0, 0])

# show "0123"
tm.write([63, 6, 91, 79])

# show "COOL"
tm.write([0b00111001, 0b00111111, 0b00111111, 0b00111000])

# show "HELP"
tm.show('help')

# display "dEAd", "bEEF"
tm.hex(0xdead)
tm.hex(0xbeef)

#tm.show('EthL')
#tm.scroll('Ethel', delay=250)

# show "-123"
#tm.number(-123)

# show temperature '24*C'
#tm.temperature(24)
