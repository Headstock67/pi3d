#!/usr/bin/python

""" A large 3D model with shadows baked into textures
"""
import math, random, time

import demo

from pi3d.constants import *

from pi3d import Display
from pi3d.Mouse import Mouse
from pi3d.Texture import Texture

from pi3d.Camera import Camera
from pi3d.Shader import Shader

from pi3d.shape.ElevationMap import ElevationMap
from pi3d.shape import EnvironmentCube
from pi3d.shape.Model import Model

from pi3d.util.Screenshot import screenshot
from pi3d.util.TkWin import TkWin

from pi3d.Light import Light

rads = 0.017453292512  # degrees to radians

#Create a Tkinter window
winw,winh,bord = 1200,600,0   	#64MB GPU memory setting
#winw,winh,bord = 1920,1080,0	#128MB GPU memory setting
win = TkWin(None, "ConferenceHall in Pi3D",winw,winh)

# Setup display and initialise pi3d viewport over the window
win.update()  #requires a window update first so that window sizes can be retreived

DISPLAY = Display.create(x=win.winx, y=win.winy, w=winw, h=winh - bord,
                         far=2200.0, background=(0.4, 0.8, 0.8, 1))

Light((1,-1,1), (1.0, 1.0, 1.0), (0.5, 0.5, 0.5))

shader = Shader("shaders/uv_reflect")
flatsh = Shader("shaders/uv_flat")
#############################
ectex = EnvironmentCube.loadECfiles("textures/ecubes/Miramar", "miramar_256", "png", nobottom = True)
myecube = EnvironmentCube.EnvironmentCube(size=1800.0, maptype="FACES",
                                          nobottom=True)
myecube.set_draw_details(flatsh,ectex)

x,z = 0,0

y = 0.0
cor_win = Model(file_string="models/ConferenceHall/conferencehall.egg",
                name="Hall", x=x, y=y, z=z, sx=0.1, sy=0.1, sz=0.1)
cor_win.set_shader(shader)

#position vars
mouserot=0.0
tilt=0.0
avhgt = 2.3
xm=0.0
zm=0.0
#ym= (mymap.calcHeight(xm,zm) + avhgt)
ym=0.0
spc = 39.32
mody = ym
opendist = 80

# Fetch key presses
mymouse = Mouse(restrict = False)
mymouse.start()

omx, omy = mymouse.position()

# Update display before we begin (user might have moved window)
win.update()
DISPLAY.resize(win.winx, win.winy, win.width, win.height - bord)

CAMERA = Camera.instance()

while DISPLAY.loop_running():
  CAMERA.reset()
  #tilt can be used as a means to prevent the view from going under the landscape!
  if tilt < -1: sf = 6 - 5.5/abs(tilt)
  else: sf = 0.5
  xoff, yoff, zoff = sf*math.sin(mouserot*rads), abs(1.25*sf*math.sin(tilt*rads)) + 3.0, -sf*math.cos(mouserot*rads)
  CAMERA.rotate(tilt, mouserot, 0)           #Tank still affected by scene tilt
  CAMERA.position((xm + xoff, ym + yoff +5, zm + zoff))   #zoom camera out so we can see our robot

  #mymap.draw()		#Draw the landscape

  cor_win.position(0, mody, -spc*1.5)
  cor_win.draw()

  myecube.position(xm, ym, zm)
  myecube.draw()#Draw environment cube

  #update mouse/keyboard input
  mx, my = mymouse.position()

  mouserot -= (mx-omx)*0.2
  tilt += (my-omy)*0.2
  omx=mx
  omy=my

  #Press ESCAPE to terminate

  #Handle window events
  try:
    win.update()
  except:
    print("bye bye 3")
    DISPLAY.stop()
    mymouse.stop()
    exit()

  if win.ev=="resized":
    print("resized")
    DISPLAY.resize(win.winx,win.winy,win.width,win.height-bord)
    win.resized=False

  if win.ev=="key":
    if win.key=="w":
      xm-=math.sin(mouserot*rads)*2
      zm+=math.cos(mouserot*rads)*2
    #ym = -(mymap.calcHeight(xm,zm)+avhgt)
    elif win.key=="s":
      xm+=math.sin(mouserot*rads)*2
      zm-=math.cos(mouserot*rads)*2
    #ym = -(mymap.calcHeight(xm,zm)+avhgt)
    elif win.key=="a":
      mouserot -= 2
    elif win.key=="d":
      mouserot += 2
    elif win.key=="p":
      screenshot("MegaStation.jpg")
    elif win.key=="Escape":
      try:
        DISPLAY.stop()
        print("Bye bye! 1")
      except Exception:
        print("Bye bye! 2")

  if win.ev=="drag" or win.ev=="click" or win.ev=="wheel":
    xm-=math.sin(mouserot*rads)*2
    zm+=math.cos(mouserot*rads)*2

  win.ev=""  #clear the event so it doesn't repeat

