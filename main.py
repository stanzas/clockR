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

class cDisplay:
  pass

class cMusic:
  pass

oAlarm = cAlarm()
oAlarm.hour = 23
oAlarm.minute = 10
oAlarm.music_filename = "11.mp3"
oAlarm.bRunForToday = False
oAlarm.isOn = False

oDisplay = cDisplay()
oDisplay.second = 0
oDisplay.panel = 1
oDisplay.iBrightness = 0
oDisplay.blink = True

oMusic = cMusic()
oMusic.bMusicPlay = 0
oMusic.nVolume = 0.2
oMusic.nVolume_prev = oMusic.nVolume


tm = tm1637.TM1637(clk=5, dio=4)
pygame.mixer.init()
now = datetime.now()
BTN_ONE = 17
BTN_TWO = 27
BTN_THREE = 22
bIsWifiActivated = 1
nButton = 0
nMode = 0
x = 0

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
  global nMode, nButton, bIsWifiActivated, oMusic, oDisplay, oAlarm

  # nMode
  # 0: time
  # 1: music
  # 2: wifi
  # 3: set alarm hours
  # 4: set alarm minutes

  # Button 1: toggle functions
  if (nButton == 1):
    if (nMode < 4):
      nMode = nMode + 1
    else:
      nMode = 0

    print("nMode: ", nMode)

  # Button 3: toggle brightness
  elif (nButton == 3):
    print("button3 pressed - ", oDisplay.iBrightness)
    if (oDisplay.iBrightness >= 7):
      oDisplay.iBrightness = 0
    else:
      oDisplay.iBrightness = oDisplay.iBrightness + 1
    tm.brightness(oDisplay.iBrightness)


  # => mode 0: time
  if (nMode == 0):
    oDisplay.panel = 0

  # => mode 1: mp3
  elif (nMode == 1):
    oDisplay.panel = 1

    # button 2: play/stop
    if (nButton == 2):
      if (oMusic.bMusicPlay == 0):
        pygame.mixer.music.load(oAlarm.music_filename)
        pygame.mixer.music.set_volume(oMusic.nVolume)
        pygame.mixer.music.play()
        oMusic.bMusicPlay = 1

      elif (oMusic.bMusicPlay == 1):
        pygame.mixer.music.pause()
        oMusic.bMusicPlay = 2
      elif (oMusic.bMusicPlay == 2):
        pygame.mixer.music.unpause()
        oMusic.bMusicPlay = 1

    # button 3: next or stop?
    elif (nButton == 3):
      pygame.mixer.music.stop()
      oMusic.bMusicPlay = 0

    # button 4: button +
    elif (nButton == 4):
      if (oMusic.nVolume < 1):
        oMusic.nVolume = oMusic.nVolume + 0.1

    # button 5: button -
    elif (nButton == 5):
      if (oMusic.nVolume > 0):
        oMusic.nVolume = oMusic.nVolume - 0.1

    if (oMusic.nVolume != oMusic.nVolume_prev):
      pygame.mixer.music.set_volume(oMusic.nVolume)
      oMusic.nVolume_prev = oMusic.nVolume

  # => mode 2: config wifi
  elif (nMode == 2):
    oDisplay.panel = 2

    if (nButton == 2):

      if (bIsWifiActivated == 1):
        subprocess.call(["sudo","ifconfig","wlan0","down"])
        bIsWifiActivated = 0
      else:
        subprocess.call(["sudo","ifconfig","wlan0","up"])
        bIsWifiActivated = 1

  # => mode 3: change alarm hours
  elif (nMode == 3):
    oDisplay.panel = 3

    # Button 3: button '+'
    if (nButton == 4):
      if (oAlarm.hour < 23):
        oAlarm.hour = oAlarm.hour + 1
      else:
        oAlarm.hour = 0
      print(oAlarm.hour, ":", oAlarm.minute)

    # Button 4: button '-'
    elif (nButton == 5):
      if (oAlarm.hour > 0):
        oAlarm.hour = oAlarm.hour - 1
      else:
        oAlarm.hour = 23
      print(oAlarm.hour, ":", oAlarm.minute)

  # => mode 4: change alarm minutes
  elif (nMode == 4):
    oDisplay.panel = 4

    # Button 4: button '+'
    if (nButton == 4):
      if (oAlarm.minute < 59):
        oAlarm.minute = oAlarm.minute + 1
      else:
        oAlarm.minute = 0
      print(oAlarm.hour, ":", oAlarm.minute)

    # Button 5: button '-'
    elif (nButton == 5):
      if (oAlarm.minute > 0):
        oAlarm.minute = oAlarm.minute - 1
      else:
        oAlarm.minute = 59
      print(oAlarm.hour, ":", oAlarm.minute)

  # reset button pressed
  nButton = 0


def fDisplay():
  global x, bIsWifiActivated, tm, now, oAlarm, oDisplay, oMusic

  # display current time (compare seconds to blink the ":")
  if (oDisplay.panel == 0):
    if (now.second != oDisplay.second):
      oDisplay.second = now.second
      tm.numbers(now.hour, now.minute, colon=oDisplay.blink)
      oDisplay.blink = not oDisplay.blink

  # display mp3 play/stop
  elif (oDisplay.panel == 1):
    if (oMusic.bMusicPlay == 0):
      tm.show("play")
    else:
      tm.show("stop")

  # display Wifi state
  elif (oDisplay.panel == 2):
    if (bIsWifiActivated == 0):
      tm.show("WOFF")
    else:
      tm.show("WON-")

  # display Alarm time set: hours
  elif (oDisplay.panel == 3):
    if (now.second != oDisplay.second):
      oDisplay.second = now.second
      oDisplay.blink = not oDisplay.blink
      if (oDisplay.blink == True):
        tm.number(oAlarm.minute)
      else:
        tm.numbers(oAlarm.hour, oAlarm.minute, colon=False)

  # display Alarm time set: minutes
  elif (oDisplay.panel == 4):
    if (now.second != oDisplay.second):
      oDisplay.second = now.second
      oDisplay.blink = not oDisplay.blink
      if (oDisplay.blink == True):
        tm.numbers(oAlarm.hour, 0, colon=False)
      else:
        tm.numbers(oAlarm.hour, oAlarm.minute, colon=False)


def fCommands():
  global bContinue, nButton, inputQueue, now, nMode, oAlarm, oMusic

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
      print("- 'ptime' => show current time & alarm")
      print("- 'pmode' => show current mode")


def fAlarm():
  global now, oMusic, oAlarm
  # if alarm time reached => play the sound
  # now.hour, now.minute
  if ((now.hour == oAlarm.hour) and
      (now.minute == oAlarm.minute) and
      (oAlarm.bRunForToday == False)):

    oAlarm.bRunForToday = True
    print("Time to wakeup!")

    # music is stopped or paused => we stop it first, then play alarm song
    if ((pygame.mixer.music.get_busy() == True) or (oMusic.bMusicPlay == 2)):
      pygame.mixer.music.stop()

    # time to play
    pygame.mixer.music.load(oAlarm.music_filename)
    pygame.mixer.music.set_volume(oMusic.nVolume)
    pygame.mixer.music.play()
    oMusic.bMusicPlay = 1

  # when music stops => return oMusic.bMusicPlay to 0
  if ((pygame.mixer.music.get_busy() == False) and
      ((oMusic.bMusicPlay == 1) or (oMusic.bMusicPlay == 2))):
    oMusic.bMusicPlay = 0

  # reset alarm for next day
  if (oAlarm.bRunForToday == True):
    # Alarm = Last minute of the hour, need to compare with next hour
    if ((oAlarm.minute == 59) and (now.hour > oAlarm.hour)):
      oAlarm.bRunForToday = False

    elif ((now.hour == oAlarm.hour) and (now.minute > oAlarm.minute)):
      oAlarm.bRunForToday = False


def main():
  global x, oDisplay, tm, inputQueue, bContinue, now

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
  tm.brightness(oDisplay.iBrightness)
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
