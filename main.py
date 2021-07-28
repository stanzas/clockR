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
import configparser


class cAlarm:
  pass

class cDisplay:
  pass

class cMusic:
  pass

class cConfig:
  pass

oAlarm = cAlarm()
oAlarm.bAlarmIsOn = True
oAlarm.iHour = 00
oAlarm.iMinute = 00
oAlarm.sMusicFilename = "11.mp3"
oAlarm.bRunForToday = False
oAlarm.bIsRunning = False

oDisplay = cDisplay()
oDisplay.iPanel = 1
oDisplay.iBrightness = 0
oDisplay.sModeTextTitle = "Time"
oDisplay.tmp_iSecond = 0
oDisplay.tmp_bBlink = True

oMusic = cMusic()
oMusic.iMusicPlay = 0
oMusic.iVolume = 0.2
oMusic.iVolume_prev = oMusic.iVolume

oConfig = cConfig()
oConfig.bAlarmIsOn = True
oConfig.iAlarmHour = 0
oConfig.iAlarmMinute = 0
oConfig.sAlarmMusicFilename = ""
oConfig.iDisplayBrightness = 0
oConfig.iSoundVolume = 0.2



tm = tm1637.TM1637(clk=5, dio=4)
pygame.mixer.init()
now = datetime.now()
BTN_ONE = 17
BTN_TWO = 27
BTN_THREE = 22
bIsWifiActivated = 1
nButton = 0
nMode = 0

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


# read config file and update variables
def fReadConfig():
  config = configparser.ConfigParser()
  config = configparser.ConfigParser()
  config.read_file(open('config.cfg'))

  if ('alarm' in config):
    print (config['alarm']['hour'])
    print (config['alarm']['minute'])
    print (config['alarm']['activated'])
    print (config['alarm']['music_filename'])
    print (config['display']['brightness'])
    print (config['sound']['volume'])

    oConfig.bAlarmIsOn = config.getboolean('alarm', 'activated')
    oConfig.iAlarmHour = int(config['alarm']['hour'])
    oConfig.iAlarmMinute = int(config['alarm']['minute'])
    oConfig.sAlarmMusicFilename = config['alarm']['music_filename']
    oConfig.iDisplayBrightness = int(config['display']['brightness'])
    oConfig.iSoundVolume = int(config['sound']['volume'])

    oAlarm.bAlarmIsOn = oConfig.bAlarmIsOn
    oAlarm.iHour = oConfig.iAlarmHour
    oAlarm.iMinute = oConfig.iAlarmMinute
    oAlarm.sMusicFilename = oConfig.sAlarmMusicFilename
    oDisplay.iBrightness = oConfig.iDisplayBrightness
    oMusic.iVolume = oConfig.iSoundVolume


def fActions():
  global nMode, nButton, bIsWifiActivated, oMusic, oDisplay, oAlarm

  # nMode
  # 0: time
  # 1: music
  # 2: wifi
  # 3: set alarm hours
  # 4: set alarm minutes

  # Button 1: toggle modes
  if (nButton == 1):
    if (nMode < 4):
      nMode = nMode + 1
    else:
      nMode = 0

    if (nMode == 0):
      oDisplay.sModeTextTitle = "Time"
    elif (nMode == 1):
      oDisplay.sModeTextTitle = "Music"
    elif (nMode == 2):
      oDisplay.sModeTextTitle = "Config: wifi"
    elif (nMode == 3):
      oDisplay.sModeTextTitle = "Alarm: set Hour"
    elif (nMode == 4):
      oDisplay.sModeTextTitle = "Alarm: set Minute"

    print("nMode: ", nMode, " - ", oDisplay.sModeTextTitle)


  # => mode 0: time
  if (nMode == 0):
    oDisplay.iPanel = 0

    if (nButton == 2):
      # when alarm is running => stop it with button 2
      if (oAlarm.bIsRunning == True):
        print("Alarm has been stopped")
        pygame.mixer.music.stop()
        oMusic.iMusicPlay = 0
        oAlarm.bRunForToday = False
        oAlarm.bIsRunning = False

      # when alarm is not running => toggle alarm on/off
      else:

        oAlarm.bAlarmIsOn = not oAlarm.bAlarmIsOn
        if (oAlarm.bAlarmIsOn == True):
          print("Alarm is On")
        else:
          print("Alarm is Off")

    # Button 3: toggle brightness
    elif (nButton == 3):
      print("button3 pressed - ", oDisplay.iBrightness)
      if (oDisplay.iBrightness >= 7):
        oDisplay.iBrightness = 0
      else:
        oDisplay.iBrightness = oDisplay.iBrightness + 1
      tm.brightness(oDisplay.iBrightness)


  # => mode 1: music
  elif (nMode == 1):
    oDisplay.iPanel = 1

    # button 2: play/stop
    if (nButton == 2):
      if (oMusic.iMusicPlay == 0):
        pygame.mixer.music.load(oAlarm.sMusicFilename)
        pygame.mixer.music.set_volume(oMusic.iVolume)
        pygame.mixer.music.play()
        oMusic.iMusicPlay = 1

      elif (oMusic.iMusicPlay == 1):
        pygame.mixer.music.pause()
        oMusic.iMusicPlay = 2
      elif (oMusic.iMusicPlay == 2):
        pygame.mixer.music.unpause()
        oMusic.iMusicPlay = 1

    # button 3: next or stop?
    elif (nButton == 3):
      pygame.mixer.music.stop()
      oMusic.iMusicPlay = 0

    # button 4: button +
    elif (nButton == 4):
      if (oMusic.iVolume < 1):
        oMusic.iVolume = oMusic.iVolume + 0.1

    # button 5: button -
    elif (nButton == 5):
      if (oMusic.iVolume > 0):
        oMusic.iVolume = oMusic.iVolume - 0.1

    if (oMusic.iVolume != oMusic.iVolume_prev):
      pygame.mixer.music.set_volume(oMusic.iVolume)
      oMusic.iVolume_prev = oMusic.iVolume

  # => mode 2: config wifi
  elif (nMode == 2):
    oDisplay.iPanel = 2

    if (nButton == 2):

      if (bIsWifiActivated == 1):
        subprocess.call(["sudo","ifconfig","wlan0","down"])
        bIsWifiActivated = 0
      else:
        subprocess.call(["sudo","ifconfig","wlan0","up"])
        bIsWifiActivated = 1

  # => mode 3: change alarm hours
  elif (nMode == 3):
    oDisplay.iPanel = 3

    # Button 3: button '+'
    if (nButton == 4):
      if (oAlarm.iHour < 23):
        oAlarm.iHour = oAlarm.iHour + 1
      else:
        oAlarm.iHour = 0
      print(oAlarm.iHour, ":", oAlarm.iMinute)

    # Button 4: button '-'
    elif (nButton == 5):
      if (oAlarm.iHour > 0):
        oAlarm.iHour = oAlarm.iHour - 1
      else:
        oAlarm.iHour = 23
      print(oAlarm.iHour, ":", oAlarm.iMinute)

  # => mode 4: change alarm minutes
  elif (nMode == 4):
    oDisplay.iPanel = 4

    # Button 4: button '+'
    if (nButton == 4):
      if (oAlarm.iMinute < 59):
        oAlarm.iMinute = oAlarm.iMinute + 1
      else:
        oAlarm.iMinute = 0
      print(oAlarm.iHour, ":", oAlarm.iMinute)

    # Button 5: button '-'
    elif (nButton == 5):
      if (oAlarm.iMinute > 0):
        oAlarm.iMinute = oAlarm.iMinute - 1
      else:
        oAlarm.iMinute = 59
      print(oAlarm.iHour, ":", oAlarm.iMinute)

  # reset button pressed
  nButton = 0


def fDisplay():
  global bIsWifiActivated, tm, now, oAlarm, oDisplay, oMusic

  # display current time (compare seconds to blink the ":")
  if (oDisplay.iPanel == 0):
    if (now.second != oDisplay.tmp_iSecond):
      oDisplay.tmp_iSecond = now.second
      tm.numbers(now.hour, now.minute, colon=oDisplay.tmp_bBlink)
      oDisplay.tmp_bBlink = not oDisplay.tmp_bBlink

  # display mp3 play/stop
  elif (oDisplay.iPanel == 1):
    if (oMusic.iMusicPlay == 0):
      tm.show("play")
    else:
      tm.show("stop")

  # display Wifi state
  elif (oDisplay.iPanel == 2):
    if (bIsWifiActivated == 0):
      tm.show("WOFF")
    else:
      tm.show("WON-")

  # display Alarm time set: hours
  elif (oDisplay.iPanel == 3):
    if (now.second != oDisplay.tmp_iSecond):
      oDisplay.tmp_iSecond = now.second
      oDisplay.tmp_bBlink = not oDisplay.tmp_bBlink
      if (oDisplay.tmp_bBlink == True):
        tm.number(oAlarm.iMinute)
      else:
        tm.numbers(oAlarm.iHour, oAlarm.iMinute, colon=False)

  # display Alarm time set: minutes
  elif (oDisplay.iPanel == 4):
    if (now.second != oDisplay.tmp_iSecond):
      oDisplay.tmp_iSecond = now.second
      oDisplay.tmp_bBlink = not oDisplay.tmp_bBlink
      if (oDisplay.tmp_bBlink == True):
        tm.show(str(oAlarm.iHour).zfill(2) + "  ")
      else:
        tm.numbers(oAlarm.iHour, oAlarm.iMinute, colon=False)


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
      print("alarm: ", oAlarm.iHour, ":", oAlarm.iMinute)

    elif (input_str == "pvol"):
      print("volume: ", oMusic.iVolume)

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
      print("- 'pvol' => show current volume")


def fAlarm():
  global now, oMusic, oAlarm
  # if alarm time reached => play the sound
  # now.hour, now.minute
  if ((oAlarm.bAlarmIsOn == True) and
      (now.hour == oAlarm.iHour) and
      (now.minute == oAlarm.iMinute) and
      (oAlarm.bRunForToday == False)):

    oAlarm.bIsRunning = True
    oAlarm.bRunForToday = True
    print("Time to wakeup!")

    # music is stopped or paused => we stop it first, then play alarm song
    if ((pygame.mixer.music.get_busy() == True) or (oMusic.iMusicPlay == 2)):
      pygame.mixer.music.stop()

    # time to play
    pygame.mixer.music.load(oAlarm.sMusicFilename)
    pygame.mixer.music.set_volume(oMusic.iVolume)
    pygame.mixer.music.play()
    oMusic.iMusicPlay = 1

  # when music stops => return oMusic.iMusicPlay to 0 & set alarm is not running
  if ((pygame.mixer.music.get_busy() == False) and
      ((oMusic.iMusicPlay == 1) or (oMusic.iMusicPlay == 2))):
    oMusic.iMusicPlay = 0
    oAlarm.bIsRunning = False
    oAlarm.bRunForToday = False

  # reset alarm for next day
  if (oAlarm.bRunForToday == True):
    # Alarm = Last minute of the hour, need to compare with next hour
    if ((oAlarm.iMinute == 59) and (now.hour > oAlarm.iHour)):
      oAlarm.bRunForToday = False

    elif ((now.hour == oAlarm.iHour) and (now.minute > oAlarm.iMinute)):
      oAlarm.bRunForToday = False


def main():
  global oDisplay, tm, inputQueue, bContinue, now

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

  fReadConfig()

  # Initialization
  tm.brightness(oDisplay.iBrightness)
  print("=== starting ===")

  bContinue = True
  while (bContinue):

    fCommands()
    if (nButton != 0):
      fActions()
    fAlarm()
    fDisplay()

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
