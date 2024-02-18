from datetime import datetime
import time
import threading
import subprocess
import queue
import sys
import os
import configparser
from typing import NamedTuple
import RPi.GPIO as GPIO
import tm1637
import pygame

BTN_ONE = 17
BTN_TWO = 27
BTN_THREE = 22
BTN_FOUR = 23

now = datetime.now()
tm = tm1637.TM1637(clk=5, dio=4)
bIsWifiActivated = 1
nMode = 0

class cButton:
  def __init__(self, argId, argChannel):
    self.iButtonId = argId
    self.iChannel = argChannel
    self.bPressed = False

  def setup(self):
    GPIO.setup(self.iChannel, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(self.iChannel, GPIO.BOTH, callback=self.onAction, bouncetime=300)
    print("button ", self.iButtonId," setup OK")

  def onAction(self, channel):
    if GPIO.input(self.iChannel):
      print("button ", self.iButtonId," unpressed")
      self.bPressed = False
    else:
      print("button ", self.iButtonId," pressed")
      self.bPressed = True

  def isPressed(self):
    return self.bPressed

class cMusic:
  def __init__(self):
    self.iMusicPlay = 0
    self.fVolume = 0.2
    self.fVolume_prev = self.fVolume
    self.sDirectory = "music/Louane - Jour 1/"
    self.sDirPos = 0
    self.sMusicFilename = ""
    self.files = os.listdir(os.getcwd() + "/" + self.sDirectory)
    self.files.sort()
  
  def getSongDirFirst(self):
    if self.files:
      self.sDirPos = 0
      self.sMusicFilename = self.files[self.sDirPos]
      return self.sDirectory + self.files[0]
    else:
      print ("first song: something went wrong")
      return None
  
  def getSongDirPrev(self):
    if (self.files):
      if ((self.sDirPos - 1) > 0) and \
          ((self.sDirPos -1) < len(self.files)):
        self.sDirPos = self.sDirPos + 1
        self.sMusicFilename = self.files[self.sDirPos]
        return self.files[self.sDirPos]
      else:
        print ("prev song: something went wrong")
        return None

  def getSongDirNext(self):
    if (self.files):
      if (self.sDirPos + 1) <= len(self.files):
        self.sDirPos = self.sDirPos + 1
        print ("prev filename = ", self.files[self.sDirPos])
        self.sMusicFilename = self.files[self.sDirPos]
        return self.files[self.sDirPos]
      else:
        print ("next song: something went wrong")
        return None

class cAlarm:
  def __init__(self):
    self.bAlarmIsOn = True
    self.iHour = 00
    self.iMinute = 00
    self.sMusicFilename = "01 - Jour 1.mp3"
    self.bRunForToday = False
    self.bIsRunning = False

  def stop(self):
    pygame.mixer.music.stop()
    self.bIsRunning = False
    print("Alarm has been stopped")

class cDisplay:
  def __init__(self):
    self.iPanel = 0
    self.iInfo = 0
    self.iBrightness = 0
    self.sModeTextTitle = "Time"
    self.tmp_iSecond = 0
    self.tmp_bBlink = True

class cConfig(object):
  def __init__(self):
    self.config = configparser.ConfigParser()
    self.config_filename = 'config.cfg'

    self._bAlarmIsOn = True
    self._iAlarmHour = 0
    self._iAlarmMinute = 0
    self._sAlarmMusicFilename = ""
    self._iDisplayBrightness = 0
    self._fSoundVolume = 0.2

  @property
  def bAlarmIsOn(self):
    return self._bAlarmIsOn

  @bAlarmIsOn.setter
  def bAlarmIsOn(self, value):
    self._bAlarmIsOn = value

  @property
  def iAlarmHour(self):
    return self._iAlarmHour

  @iAlarmHour.setter
  def iAlarmHour(self, value):
    self._iAlarmHour = value

  @property
  def iAlarmMinute(self):
    return self._iAlarmMinute

  @iAlarmMinute.setter
  def iAlarmMinute(self, value):
    self._iAlarmMinute = value

  @property
  def sAlarmMusicFilename(self):
    return self._sAlarmMusicFilename

  @sAlarmMusicFilename.setter
  def sAlarmMusicFilename(self, value):
    self._sAlarmMusicFilename = value

  @property
  def iDisplayBrightness(self):
    return self._iDisplayBrightness

  @iDisplayBrightness.setter
  def iDisplayBrightness(self, value):
    self._iDisplayBrightness = value

  @property
  def fSoundVolume(self):
    return self._fSoundVolume

  @fSoundVolume.setter
  def fSoundVolume(self, value):
    self._fSoundVolume = value

  def read(self):
    self.config.read_file(open(self.config_filename))

  def write(self):
    self.config.set('alarm', 'activated', str(self._bAlarmIsOn))
    self.config.set('alarm', 'hour', str(self._iAlarmHour))
    self.config.set('alarm', 'minute', str(self._iAlarmMinute))
    self.config.set('alarm', 'music_filename', self._sAlarmMusicFilename)
    self.config.set('display', 'brightness', str(self._iDisplayBrightness))
    self.config.set('sound', 'volume', str(self._fSoundVolume))

    with open(self.config_filename, 'w') as configfile:
      self.config.write(configfile)

oConfig = cConfig()

def read_kbd_input(inputQueue):
  print('Ready for keyboard input:')
  while (True):
    input_str = input()
    inputQueue.put(input_str)


# read config file and update variables
def fReadConfig():
  global oConfig, oAlarm, oDisplay, oMusic

  oConfig.read()
  if ('alarm' in oConfig.config):
    print ("Alarm, hours: ", oConfig.config['alarm']['hour'])
    print ("Alarm, minutes: ", oConfig.config['alarm']['minute'])
    print ("Alarm, activate: ", oConfig.config['alarm']['activated'])
    print ("Alarm, default music file: ", oConfig.config['alarm']['music_filename'])
    print ("Display, brightness", oConfig.config['display']['brightness'])
    print ("Sound, volume: ", oConfig.config['sound']['volume'])

    oConfig.bAlarmIsOn = oConfig.config.getboolean('alarm', 'activated')
    oConfig.iAlarmHour = int(oConfig.config['alarm']['hour'])
    oConfig.iAlarmMinute = int(oConfig.config['alarm']['minute'])
    oConfig.sAlarmMusicFilename = oConfig.config['alarm']['music_filename']
    oConfig.iDisplayBrightness = int(oConfig.config['display']['brightness'])
    oConfig.fSoundVolume = float(oConfig.config['sound']['volume'])

    oAlarm.bAlarmIsOn = oConfig.bAlarmIsOn
    oAlarm.iHour = oConfig.iAlarmHour
    oAlarm.iMinute = oConfig.iAlarmMinute
    oAlarm.sMusicFilename = oConfig.sAlarmMusicFilename
    oDisplay.iBrightness = oConfig.iDisplayBrightness
    oMusic.fVolume = oConfig.fSoundVolume


def fActions():
  global nMode, bIsWifiActivated, oMusic, oDisplay, oAlarm, oConfig
  global oButton1, oButton2, oButton3, oButton4

  # nMode
  # 0: time
  # 1: music
  # 2: wifi
  # 3: set alarm hours
  # 4: set alarm minutes

  # when alarm is running (woke up):
  # - button 1 => stop the alarm until next day
  # - button 2 => snooze // not implemented yet
  if (oAlarm.bIsRunning == True):
    if (oButton1.isPressed() == True):
      oMusic.iMusicPlay = 0
      oAlarm.stop()

  else:
    # Button 1: toggle modes
    if (oButton1.isPressed() == True):
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

      if (oButton2.isPressed() == True):
        oAlarm.bAlarmIsOn = not oAlarm.bAlarmIsOn
        if (oAlarm.bAlarmIsOn == True):
          print("Alarm is On")
        else:
          print("Alarm is Off")

      # Button 3: toggle brightness
      elif (oButton3.isPressed() == True):
        print("button3 pressed - brightness: ", oDisplay.iBrightness)
        if (oDisplay.iBrightness >= 7):
          oDisplay.iBrightness = 0
        else:
          oDisplay.iBrightness = oDisplay.iBrightness + 1
        tm.brightness(oDisplay.iBrightness)
        oConfig.iDisplayBrightness = oDisplay.iBrightness
        oConfig.write()


    # => mode 1: music
    elif (nMode == 1):
      oDisplay.iPanel = 1

      # button 2: play/stop
      if (oButton2.isPressed() == True):
        if (oMusic.iMusicPlay == 0):
          pygame.mixer.music.load(oMusic.getSongDirFirst())
          pygame.mixer.music.set_volume(oMusic.fVolume)
          pygame.mixer.music.play()
          oMusic.iMusicPlay = 1

        elif (oMusic.iMusicPlay == 1):
          pygame.mixer.music.pause()
          oMusic.iMusicPlay = 2
        elif (oMusic.iMusicPlay == 2):
          pygame.mixer.music.unpause()
          oMusic.iMusicPlay = 1

      # button 3: next or stop?
      elif (oButton3.isPressed() == True):
        pygame.mixer.music.load(oMusic.getSongDirNext())
        pygame.mixer.music.play()
        oMusic.iMusicPlay = 1
        oDisplay.iInfo = 2

      # button 4: button +
      elif (oButton4.isPressed() == True):
        if ((oMusic.fVolume + 0.1) < 1):
          oMusic.fVolume = oMusic.fVolume + 0.1
        else:
          oMusic.fVolume = 0
        oDisplay.iInfo = 3

      # button 5: button -
#      elif (nButton == 5):
#        if (oMusic.fVolume > 0):
#          oMusic.fVolume = oMusic.fVolume - 0.1

      if (oMusic.fVolume != oMusic.fVolume_prev):
        pygame.mixer.music.set_volume(oMusic.fVolume)
        oMusic.fVolume_prev = oMusic.fVolume
        oConfig.iSoundVolume = oMusic.fVolume
        oConfig.write()

    # => mode 2: config wifi
    elif (nMode == 2):
      oDisplay.iPanel = 2

      if (oButton2.isPressed() == True):

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
      if (oButton4.isPressed() == True):
        if (oAlarm.iHour < 23):
          oAlarm.iHour = oAlarm.iHour + 1
        else:
          oAlarm.iHour = 0
        print(oAlarm.iHour, ":", oAlarm.iMinute)
        oConfig.iAlarmHour = oAlarm.iHour
        oConfig.write()

      # Button 4: button '-'
      elif (oButton4.isPressed() == True):
        if (oAlarm.iHour > 0):
          oAlarm.iHour = oAlarm.iHour - 1
        else:
          oAlarm.iHour = 23
        print(oAlarm.iHour, ":", oAlarm.iMinute)
        oConfig.iAlarmHour = oAlarm.iHour
        oConfig.write()

    # => mode 4: change alarm minutes
    elif (nMode == 4):
      oDisplay.iPanel = 4

      # Button 4: button '+'
      if (oButton4.isPressed() == True):
        if (oAlarm.iMinute < 59):
          oAlarm.iMinute = oAlarm.iMinute + 1
        else:
          oAlarm.iMinute = 0
        print(oAlarm.iHour, ":", oAlarm.iMinute)
        oConfig.iAlarmMinute = oAlarm.iMinute
        oConfig.write()

      # Button 5: button '-'
#      elif (nButton == 5):
#        if (oAlarm.iMinute > 0):
#          oAlarm.iMinute = oAlarm.iMinute - 1
#        else:
#          oAlarm.iMinute = 59
#        print(oAlarm.iHour, ":", oAlarm.iMinute)
#        oConfig.iAlarmMinute = oAlarm.iMinute
#        oConfig.write()

  oButton1.bPressed = False
  oButton2.bPressed = False
  oButton3.bPressed = False
  oButton4.bPressed = False

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
    if (oDisplay.iInfo == 0):
      if (oMusic.iMusicPlay == 0):
        tm.show("play")
      else:
        tm.show("stop")
    elif (oDisplay.iInfo == 2):
      tm.show(oMusic.sMusicFilename[0:3])
    elif (oDisplay.iInfo == 3):
      tm.number(int(oMusic.fVolume*100))

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
  global bContinue, inputQueue, now, nMode, oAlarm, oMusic

  if (inputQueue.qsize() > 0):
    input_str = inputQueue.get()
    print("input_str = {}".format(input_str))

    if (input_str == "q"):
      bContinue = False
    elif (input_str == "1"):
      oButton1.bPressed = True
    elif (input_str == "2"):
      oButton2.bPressed = True
    elif (input_str == "3"):
      oButton3.bPressed = True
    elif (input_str == "+"):
      oButton4.bPressed = True
#    elif (input_str == "-"):
#      oButton5.bPressed = True
#      nButton = 5

    elif (input_str == "pmode"):
      print("mode: ", nMode)

    elif (input_str == "ptime"):
      print("time: ", now.hour, ":", now.minute, ":", now.second)
      print("alarm: ", oAlarm.iHour, ":", oAlarm.iMinute)

    elif (input_str == "pvol"):
      print("volume: ", oMusic.fVolume)

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
    pygame.mixer.music.set_volume(oMusic.fVolume)
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

oButton1 = cButton(1, BTN_ONE)
oButton2 = cButton(2, BTN_TWO)
oButton3 = cButton(3, BTN_THREE)
oButton4 = cButton(4, BTN_FOUR)

oMusic = cMusic()
oAlarm = cAlarm()
oDisplay = cDisplay()

def main():
  global oDisplay, oConfig, oAlarm, tm, inputQueue, bContinue, now, pygame
  global oButton1, oButton2, oButton3, oButton4

  # init the sound
  pygame.mixer.init()

  # setup the GPIO/buttons
  GPIO.setmode(GPIO.BCM)

  inputQueue = queue.Queue()
  inputThread = threading.Thread(target=read_kbd_input, args=(inputQueue,), daemon=True)
  inputThread.start()

  oButton1.setup()
  oButton2.setup()
  oButton3.setup()
  oButton4.setup()

  # read & init config from ini file
  fReadConfig()

  # Display TM1637 Initialization
  tm.brightness(oDisplay.iBrightness)

  print("=== starting ===")

  bContinue = True
  while (bContinue):

    fCommands()
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
