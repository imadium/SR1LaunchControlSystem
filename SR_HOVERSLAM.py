import pyautogui as pag
import math
import os
import time
import PIL
from PIL import Image
import pytesseract
import re
import mss
import mss.tools
import time
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"

teleX, teleY ,teleW, teleH = pag.locateOnScreen(r"C:\Users\IMAD-PC\Desktop\LaunchControlSystem\marker.PNG")
pag.click(teleX, teleY, button='left')
print('Marker found')
#print(teleX,teleY)

# for SR display resolution = 1024x768
Y1=teleX+1130; X1=teleY+37
Y2=teleX+1140; X2=teleY+65

# The screen part to capture
region1 = {'top': X1, 'left': Y1, 'width': 102, 'height': 30}
region2 = {'top': X2, 'left': Y2, 'width': 72, 'height': 30}



def throttle(level): # for linear thrust only (don't use on thrustExponential engines)
    if level > 1:
        level = 1
    if level < 0:
        level = 0
    
    Xpos = 1235 + teleX
    Ypos = (910 + teleY) - (level * 10 * 32.5)
    pag.click(x=Xpos,y=Ypos)



def autoHeading(targetAngle , currentAngle):
    print('AutoHeading: '+str(targetAngle)+'deg')
    # Angle off-set
    targetAngle = targetAngle - 180
    currentAngle = currentAngle - 180

    X0 = 621 + teleX
    Y0 = 169 + teleY
    r = 319 #radius
    
    # Center
    Xcenter = X0
    Ycenter = Y0 + r
    
    # current position
    Xi = Xcenter + (r * math.cos(math.radians(currentAngle)))
    Yi = Ycenter + (r * math.sin(math.radians(currentAngle)))
    
    # target position
    Xf = Xcenter + (r * math.cos(math.radians(targetAngle)))
    Yf = Ycenter + (r * math.sin(math.radians(targetAngle)))

    # Action
    pag.moveTo(Xi,Yi) # pag.drag wont work, thats why :)
    pag.mouseDown()
    pag.moveTo(Xf,Yf,0.3) # dont remove time, otherwise systematic error
    pag.mouseUp()







#=========================================================
#=========================================================
R = 6371000 #m Radius of Earth (get from SmolarSystem.xml)

# Launch Config.

targetHeight = 500 # meters

print('Target Height : '+str(targetHeight))
hop = 1

if hop == 1: #just to provide initial velocity
    throttle(0.8)

criticalThrottle = 0.2 # at what throttle value to trigger the controller

HS_calc = 0
HS_activeCtrl = 0

# Rocket Data
radarOffset = 14 #m (pod offset from the ground with landing legs deployed)
mo = 44350 # kg (total mass WITH fuel) get this from partlist.xml
fuelmass = 36450 # kg (tank mass - tank dry mass) get this from partlist.xml
mf = mo - fuelmass # kg (dry mass) get this from partlist.xml
maxThrust = 850e3 # Newtons (maxThrust = power * 85 kN) get 'power' from partlist.xml
mfr = 270 * 0.9 # kg/s (vfr*density) consumption = vfr in partlist.xml
CF = 1 # correction factor
#targetHeight = targetHeight - radarOffset

maxDeltaV = (maxThrust/mfr) * math.log(mo/mf) * CF
#=========================================================
#=========================================================

'''
NOTES:
> 1 mass in partlist.xml = 500 kg
'''






while True:
    
    t1 = time.time()
    #alt_t=0; vel_t=0
    with mss.mss() as sct:
        
        # Grab the data
        agd = sct.grab(region1)
        vgd = sct.grab(region2)

    # Convert to Image
    tele_alt = Image.frombytes("RGB", agd.size, agd.bgra, "raw", "BGRX")
    tele_vel = Image.frombytes("RGB", vgd.size, vgd.bgra, "raw", "BGRX")

    # Apply tesseract OCR
    text_alt = pytesseract.image_to_string(tele_alt, lang='Droid')
    text_vel = pytesseract.image_to_string(tele_vel, lang='Droid')

    if text_alt == '': # Single Character Mode
        text_alt = pytesseract.image_to_string(tele_alt, lang='Droid', config=" --psm 10")
    if text_vel == '': # Single Character Mode
        text_vel = pytesseract.image_to_string(tele_vel, lang='Droid', config=" --psm 10")

    if text_vel == '0': text_vel = ''


    if text_alt != '' and text_vel != '':
        
        try: # Removing commas and dots
            alt_t = float(text_alt.replace(',',''))
            vel_t = float(text_vel.replace(',',''))
            alt_t = float(text_alt.replace('.',''))
            vel_t = float(text_vel.replace('.',''))
        except ValueError:
            None

        g = (3.9777e14)/(R+alt_t)**2 # Acc. due t gravity w.r.t. altitude


        
        if hop == 1 and alt_t <= targetHeight: # HOP CONTROLLER
            mode = 'HOP'
            alt_t = alt_t - (radarOffset + targetHeight)
            
            maxDecel =  g - (maxThrust/mo)
            stopDist = (vel_t**2)/(2*maxDecel)
            idealThrottle = 1 - (stopDist/alt_t)
            impactTime = abs(alt_t / vel_t)
            mo = mf * math.exp((maxDeltaV*(mfr*(idealThrottle/maxThrust)))/idealThrottle)
            if idealThrottle >= criticalThrottle:
                throttle(1-criticalThrottle) # or just use throttle(idealThrottle) and remove this condition
            else:
                throttle(idealThrottle)
        else:
            HS_calc = 1
            HS_activeCtrl = 0
            hop = 0


    
        if HS_calc == 1: # HOVERSLAM CONTROLLER
            mode = 'HOVERSLAM'
            alt_t = abs(alt_t - radarOffset)
            if alt_t <= 2:
                print('\n    LANDED')
                throttle(0.0)
                break
            maxDecel = (maxThrust/mo) - g
            stopDist = (vel_t**2)/(2*maxDecel)
            try:
                idealThrottle = stopDist/alt_t
                impactTime = abs(alt_t / vel_t)
            except ZeroDivisionError:
                None
            mo = mf * math.exp((maxDeltaV*(mfr*(idealThrottle/maxThrust)))/idealThrottle)

        if idealThrottle >= criticalThrottle and hop == 0:
            HS_activeCtrl = 1
        if HS_activeCtrl == 1:
            throttle(idealThrottle)


        print('Mode: '+mode+' |Throttle: '+str(int(idealThrottle*100))+'% |Alt: '+str(int(alt_t))+'m |Vel: '+str(int(vel_t))+'m/s')

    else:
         print('---')
         #pag.press('num0')

         
 
