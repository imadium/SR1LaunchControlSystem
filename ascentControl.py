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


# SR display resolution = 1024x768



R = 6371000 #m
g = 9.8 #m/s^2
gamma_1 = 85 #deg
to = 0
delta_gamma = 0


teleX, teleY ,teleW, teleH = pag.locateOnScreen(r"C:\Users\IMAD-PC\Desktop\LaunchControlSystem\marker.PNG")
pag.click(teleX, teleY, button='left')
print('Marker found '+str(teleX)+','+str(teleY))
time.sleep(2)




def throttle(P):
    if P == 0:
        pass
        #pag.press('0')



def autoHeading(targetAngle , currentAngle):

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
    pag.moveTo(Xi,Yi)
    pag.mouseDown()
    pag.moveTo(Xf,Yf,0.3)
    pag.mouseUp()
    
    print('#')
    

autoHeading(gamma_1,90)
#autoHeading(90,45)


Y1=teleX+1130; X1=teleY+37
Y2=teleX+1140; X2=teleY+65

#pag.press('0')

to = time.time()
while True:
    t1 = time.time()
    alt=''; vel=''
    with mss.mss() as sct:
        # The screen part to capture
        region1 = {'top': X1, 'left': Y1, 'width': 102, 'height': 30}
        region2 = {'top': X2, 'left': Y2, 'width': 72, 'height': 30}
        # Grab the data
        agd = sct.grab(region1)
        vgd = sct.grab(region2)
        # Convert to PNG
        tele_alt1 = mss.tools.to_png(agd.rgb, agd.size, output=r'C:\Users\IMAD-PC\Desktop\SRlogger\alt_RT.png')
        tele_vel1 = mss.tools.to_png(vgd.rgb, vgd.size, output=r'C:\Users\IMAD-PC\Desktop\SRlogger\vel_RT.png')
    tele_alt = Image.open(r'C:\Users\IMAD-PC\Desktop\SRlogger\alt_RT.png')
    tele_vel = Image.open(r'C:\Users\IMAD-PC\Desktop\SRlogger\vel_RT.png')
    text_alt = pytesseract.image_to_string(tele_alt, lang='Droid')
    text_vel = pytesseract.image_to_string(tele_vel, lang='Droid')

    textre_alt = re.compile('\d') # NUMBERS ONLY
    digits_alt = textre_alt.findall(text_alt)
    textre_vel = re.compile('\d') # NUMBERS ONLY
    digits_vel = textre_vel.findall(text_vel)

    for da in digits_alt:
        alt = alt + da
    for ve in digits_vel:
        vel = vel + ve
    if alt != '' and vel != '':
        #print(alt+' m  |  ' + vel+' m/s')
        alt_t = float(alt)
        vel_t = float(vel)

        g = (3.9777e14)/(R+alt_t)**2


        #-------------------------------------------

        delta_t = time.time() - to
        

        if delta_t >= 3:
            gamma_2 = gamma_1 - math.degrees((((delta_t+0.3)*math.cos(math.radians(gamma_1)) / vel_t) * (g - ((vel_t**2)/(R+alt_t)))))
            
            
            delta_gamma = gamma_2 - gamma_1
            autoHeading(gamma_2,gamma_1)
            print(gamma_2,gamma_1)
            gamma_1 = gamma_2
            to = time.time()

            
        
            
        


    else:
         print('---')
         #pag.press('num0')

         
 
