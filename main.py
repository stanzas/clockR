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


class cAlarm:
  pass

oAlarm = cAlarm()
oAlarm.hour = 23
oAlarm.minute = 10
oAlarm.music = ""
oAlarm.bRunForToday = False

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
  global nButton, nDisplay, bIsWifiActivated, bMusicPlay
  global nMode, iBrightness, nVolume, nVolume_prev, oAlarm

  # nMode
  # 0: time
  # 1: music
  # 2: wifi
  # 3: set alarm hours
  # 4: set alarm minutes

  # Button 1: toggle functions
  if (nButton == 1):
    if (nMode >= 5):
      nMode = 0
    else:
      nMode = nMode + 1

    print("nMode: ", nMode)

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

    # button 3: button +
    elif (nButton == 4):
      if (nVolume < 1):
        nVolume = nVolume + 0.1

    # button 3: button -
    elif (nButton == 5):
      if (nVolume > 0):
        nVolume = nVolume - 0.1

    if (nVolume != nVolume_prev):
      pygame.mixer.music.set_volume(nVolume)
      nVolume_prev = nVolume



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


  # => mode 3: change alarm hours
  elif (nMode == 3):
    # Button 3: button '+'
    if (nButton == 4):
      if (oAlarm.hour < 60):
        oAlarm.hour = oAlarm.hour + 1
      else:
        oAlarm.hour = 0
      print(oAlarm.hour)

    # Button 4: button '-'
    elif (nButton == 5):
      if (oAlarm.hour > 0):
        oAlarm.hour = oAlarm.hour - 1
      else:
        oAlarm.hour = 60
      print(oAlarm.hour)



  # => mode 4: change alarm minutes
  elif (nMode == 4):
    # Button 3: button '+'
    if (nButton == 4):
      if (oAlarm.minute < 60):
        oAlarm.minute = oAlarm.minute + 1
      else:
        oAlarm.minute = 0
      print(oAlarm.minute)

    # Button 4: button '-'
    elif (nButton == 5):
      if (oAlarm.minute > 0):
        oAlarm.minute = oAlarm.minute - 1
      else:
        oAlarm.minute = 60
      print(oAlarm.minute)


  nButton = 0


def fDisplay():
  global nDisplay, x, bMusicPlay, bIsWifiActivated, tm, now
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
  global bContinue, nButton, nVolume, inputQueue, oAlarm, now, nMode

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
      nButton = 4
    elif (input_str == "-"):
      nButton = 5

    elif (input_str == "pmode"):
      print("mode: ", nMode)

    elif (input_str == "ptime"):
      print("time: ", now.hour, ":", now.minute, ":", now.second)
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
  global oAlarm, now, bMusicPlay
  # if alarm time reached => play the sound
  # now.hour, now.minute
  if ((now.hour == oAlarm.hour) and
      (now.minute == oAlarm.minute) and
      (oAlarm.bRunForToday == False)):
    oAlarm.bRunForToday = True
    print("Time to wakeup")

    # music is stopped or paused
    if (bMusicPlay == 0):
      pygame.mixer.music.load("11.mp3")
      pygame.mixer.music.set_volume(nVolume)
      pygame.mixer.music.play()
      bMusicPlay = 1
    elif (bMusicPlay == 2):
      pygame.mixer.music.unpause()
      bMusicPlay = 1

  # reset alarm for next day
  if (oAlarm.bRunForToday == True):
    # Alarm = Last minute of the hour, need to compare with next hour
    if ((oAlarm.minute == 59) and (now.hour > oAlarm.hour)):
      oAlarm.bRunForToday = False

    elif ((now.hour == oAlarm.hour) and (now.minute >= oAlarm.minute)):
      oAlarm.bRunForToday = False


def main():
  global x, iBrightness, tm, inputQueue, bContinue, now

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

    now = datetime.now()
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
