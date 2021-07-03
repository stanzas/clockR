import RPi.GPIO as GPIO
import sys
import os
import time
from datetime import datetime
import tm1637
import subprocess
import pygame

BTN_ONE = 17
BTN_TWO = 27
BTN_THREE = 22
iBrightness = 7

pygame.mixer.init()

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
  global nButton
  print("button1 pressed")
  nButton = 1

# Button 2 => show Mod2
def button2(channel):
  global nButton
  print("button2 pressed")
  nButton = 2

# Buton 3 => brightness
def button3(channel):
  global nButton
  print("button3 pressed")
  nButton = 3


def fCommands():
  global nButton, nDisplay, bIsWifiActivated, bMusicPlay, nMode, iBrightness

  # Button 1: toggle functions
  if (nButton == 1):
    if (nMode >= 2):
      nMode = 0
    else:
      nMode = nMode + 1

  # Button 3: toggle brightness
  elif (nButton == 3):
    print("button3 pressed - ", iBrightness)
    if (iBrightness >= 7):
      iBrightness = 0
    else:
      iBrightness = iBrightness + 1
    tm.brightness(iBrightness)


  # => mode 0: time
  if (nMode == 0):
    nDisplay = 0

  # => mode 1: mp3
  elif (nMode == 1):
    nDisplay = 1

    # button 2: play/stop
    if (nButton == 2):
      if (bMusicPlay == 0):
        #p = subprocess.Popen(["music123","11.mp3"])
        pygame.mixer.music.load("11.mp3")
        pygame.mixer.music.set_volume(1.0)
        pygame.mixer.music.play()

        bMusicPlay = 1
      elif (bMusicPlay == 1):
        #p = subprocess.Popen(["sudo","pkill","music123"])
        pygame.mixer.pause()
        bMusicPlay = 0

  # => mode 2: wifi
  elif (nMode == 2):
    nDisplay = 2

    if (nButton == 2):
      if (bIsWifiActivated == 1):
        subprocess.call(["sudo","ifconfig","wlan0","down"])
        bIsWifiActivated = 0
      else:
        subprocess.call(["sudo","ifconfig","wlan0","up"])
        bIsWifiActivated = 1

  nButton = 0


def fDisplay():
  global nDisplay, x, bMusicPlay, bIsWifiActivated
  # display time
  if (nDisplay == 0):
    if (x!=1):
      tm.numbers(now.hour, now.minute)
      x = 1
    else:
      tm.show(now.strftime("%H%M"))
      x = 0

  elif (nDisplay == 1):
    if (bMusicPlay == 0):
      tm.show("play")
    else:
      tm.show("stop")

  elif (nDisplay == 2):
    if (bIsWifiActivated == 0):
      tm.show("WOFF")
    else:
      tm.show("WON-")


# when a falling edge is detected on port 17, regardless of whatever
# else is happening in the program, the function my_callback will be run
GPIO.add_event_detect(BTN_ONE, GPIO.FALLING, callback=button1, bouncetime=300)
GPIO.add_event_detect(BTN_TWO, GPIO.FALLING, callback=button2, bouncetime=300)
GPIO.add_event_detect(BTN_THREE, GPIO.FALLING, callback=button3, bouncetime=300)

bIsWifiActivated = 1
bMusicPlay = 0
nDisplay = 1
nButton = 0
nMode = 0
x = 0
iBrightness = 0
tm.brightness(iBrightness)
print("=== starting ===")
while True:
  fCommands()
  fDisplay()
  time.sleep(1)

print("=== ending ===")

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
