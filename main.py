import RPi.GPIO as GPIO
import sys
import os
import time
from datetime import datetime
import tm1637
import subprocess
import pygame
import threading
import queue
import time
from typing import NamedTuple


class cAlarm(NamedTuple):
  hour: int
  minute: int
  song: str

oAlarm = cAlarm(0, 38, "")

tm = tm1637.TM1637(clk=5, dio=4)
pygame.mixer.init()
now = datetime.now()
BTN_ONE = 17
BTN_TWO = 27
BTN_THREE = 22
iBrightness = 7
bIsWifiActivated = 1
bMusicPlay = 0
nDisplay = 1
nButton = 0
nMode = 0
nVolume = 0.2
nVolume_prev = nVolume
x = 0
iBrightness = 0

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

def read_kbd_input(inputQueue):
  print('Ready for keyboard input:')
  while (True):
    input_str = input()
    inputQueue.put(input_str)

def fActions():
  global nButton, nDisplay, bIsWifiActivated, bMusicPlay, nMode, iBrightness, nVolume, nVolume_prev

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

  if (nVolume != nVolume_prev):
    pygame.mixer.music.set_volume(nVolume)
    nVolume_prev = nVolume

  # => mode 0: time
  if (nMode == 0):
    nDisplay = 0

  # => mode 1: mp3
  elif (nMode == 1):
    nDisplay = 1

    # button 2: play/stop
    if (nButton == 2):
      if (bMusicPlay == 0):
        pygame.mixer.music.load("11.mp3")
        pygame.mixer.music.set_volume(nVolume)
        pygame.mixer.music.play()
        bMusicPlay = 1

      elif (bMusicPlay == 1):
        pygame.mixer.music.pause()
        bMusicPlay = 2
      elif (bMusicPlay == 2):
        pygame.mixer.music.unpause()
        bMusicPlay = 1

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
  global nDisplay, x, bMusicPlay, bIsWifiActivated, tm
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


def fCommands():
  global bContinue, nButton, nVolume, inputQueue, oAlarm

  if (inputQueue.qsize() > 0):
    input_str = inputQueue.get()
    print("input_str = {}".format(input_str))

    if (input_str == "q"):
      bContinue = False
    elif (input_str == "1"):
      nButton = 1
    elif (input_str == "2"):
      nButton = 2
    elif (input_str == "3"):
      nButton = 3
    elif (input_str == "+"):
      if (nVolume < 1):
        nVolume = nVolume + 0.1
    elif (input_str == "-"):
      if (nVolume > 0):
        nVolume = nVolume - 0.1
    elif (input_str == "t"):
      print("time: ", now.hour, ":", now.minute)
      print("alarm: ", oAlarm.hour, ":", oAlarm.minute)

    else:
      print("Unknown command. Comands are:")
      print("- 'q' => exit ;")
      print("- '1' => button 1")
      print("- '2' => button 2")
      print("- '3' => button 3")
      print("- '+' => vol +10%")
      print("- '-' => vol -10%")
      print("- 't' => show time")

def fAlarm():
  global oAlarm
  # if alarm time reached => play the sound
  # now.hour, now.minute
  if ((now.hour == oAlarm.hour) & (now.minute == oAlarm.minute)):
    print("Time to wakeup")


def main():
  global x, iBrightness, tm, inputQueue, bContinue

  # set the buttons
  GPIO.setmode(GPIO.BCM)
  GPIO.setup(BTN_ONE, GPIO.IN, pull_up_down=GPIO.PUD_UP)
  GPIO.setup(BTN_TWO, GPIO.IN, pull_up_down=GPIO.PUD_UP)
  GPIO.setup(BTN_THREE, GPIO.IN, pull_up_down=GPIO.PUD_UP)

  inputQueue = queue.Queue()
  inputThread = threading.Thread(target=read_kbd_input, args=(inputQueue,), daemon=True)
  inputThread.start()

  # when a falling edge is detected on port 17, regardless of whatever
  # else is happening in the program, the function my_callback will be run
  GPIO.add_event_detect(BTN_ONE, GPIO.FALLING, callback=button1, bouncetime=300)
  GPIO.add_event_detect(BTN_TWO, GPIO.FALLING, callback=button2, bouncetime=300)
  GPIO.add_event_detect(BTN_THREE, GPIO.FALLING, callback=button3, bouncetime=300)

  # Initialization
  tm.brightness(iBrightness)
  print("=== starting ===")

  bContinue = True
  while (bContinue):

    fActions()
    fAlarm()
    fDisplay()
    fCommands()

    time.sleep(0.01)

  GPIO.cleanup()
  sys.exit()
  print("=== ending ===")

if (__name__ == '__main__'):
  main()

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
