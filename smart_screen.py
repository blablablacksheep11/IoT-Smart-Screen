from machine import Pin, ADC, PWM
from gui.core.writer import Writer
from gui.core.nanogui import refresh
from color_setup import ssd
from time import sleep, sleep_us, ticks_ms, ticks_us, ticks_diff
from blynklib import Blynk
import gui.fonts.montserrat20 as font_sm
import gui.fonts.montserrat30 as font_md
import gui.fonts.montserrat40 as font_lg
import gui.fonts.montserrat50 as font_xl
import gc
import asyncio
import env
import connection

# Turn on backlight in default
blk_pwm = PWM(Pin(22))
blk_pwm.freq(1000)

# Setup writers
wri_sm = Writer(ssd, font_sm)
wri_md = Writer(ssd, font_md)
wri_lg = Writer(ssd, font_lg)
wri_xl = Writer(ssd, font_xl)

# Blynk object
BLYNK = Blynk(env.BLYNK_AUTH_TOKEN, insecure=True)

configs = {
    "md": (wri_md, 150),
    "lg": (wri_lg, 160),
    "xl": (wri_xl, 170)
}

last_send = 0 # Track last Blynk updates

md_threshold = 5
lg_threshold = 15

# Sensors pins
TRIG = Pin(13, Pin.OUT)
ECHO = Pin(12, Pin.IN)
BTN = Pin(15, Pin.IN)
ldr = ADC(Pin(26))

class SharedState:
    brightness = 0
    mode = 0
    distance = 0
    btnCount = 0
    
state = SharedState()

async def getDistance():
    while True:
        start_time = ticks_us() # Timer start, for fps calculation
        
        TRIG.low()
        await asyncio.sleep(0.000002)
        TRIG.high()
        await asyncio.sleep(0.000010)
        TRIG.low()

        # Only wait the echo for 30 ms
        timeout = ticks_us() + 30000
        while ECHO.value() == 0:
            if ticks_us() > timeout:
                break
        start = ticks_us()

        while ECHO.value() == 1:
            if ticks_us() > timeout:
                break
        end = ticks_us()

        duration = ticks_diff(end, start)
        state.distance = min(99,(duration * 0.0343) / 2)
                
        await displayText()
        
        fps_textarea = (0, 10, 240, 25) 
        ssd.fill_rect(*fps_textarea, 0)

        # Timer end, calculate fps
        # While loop sleep time is included in calculation, +1000000
        refresh_rate = int(1000000 / (ticks_diff(ticks_us(), start_time) + 100000))

        # Print fps
        Writer.set_textpos(ssd, 10, 10)
        wri_sm.printstring(f"Refresh rate:  {refresh_rate} fps")
    
        await asyncio.sleep(0.1)

async def brightnessCtrl():
    while True:
        in_min, in_max = 1100, 64000
        light_val = ldr.read_u16()
        light_val = max(min(light_val, in_max), in_min) # Ensure in range 1100-64000
    
        # Min-max scaling
        scaled_val = (light_val - in_min) / (in_max - in_min)
    
        # Constrain to stay within 0-65535
        final_val = int((1.0 - scaled_val) * 65535)
        blk_pwm.duty_u16(final_val)
    
        state.brightness = final_val / 65535 * 100
    
        brightness_textarea = (0, 35, 240, 25) 
        ssd.fill_rect(*brightness_textarea, 0) 

        # Print brightness
        Writer.set_textpos(ssd, 35, 10)
        wri_sm.printstring(f"Brightness:  {state.brightness:.2f} %")
            
        await asyncio.sleep(0.2)

async def changeMode():    
    while True:
        if BTN.value() == 1:
            state.btnCount += 1
    
        if state.btnCount % 2 == 0:
            state.mode = 0 # Short sightedness
        else:
            state.mode = 1 # Long sightedness
                
        mode_textarea = (0, 60, 240, 25) 
        ssd.fill_rect(*mode_textarea, 0)

        # Print mode
        Writer.set_textpos(ssd, 60, 10)
        wri_sm.printstring(f"Mode:  {state.mode}")
        
        await asyncio.sleep(0.2)
        
async def displayText():
    main_textarea = (0, 120, 240, 120) 
    ssd.fill_rect(*main_textarea, 0)
    
    
    # Font go bigger when distance increased in mode 0, short sightedness
    # Font go smaller when distance increased in mode 1, long sightedness
    if state.distance < md_threshold:
        key = "md" if state.mode == 0 else "xl"
    elif state.distance < lg_threshold:
        key = "lg"
    else:
        key = "xl" if state.mode == 0 else "md"
        
    writer, y_pos = configs[key]

    Writer.set_textpos(ssd, 120, 10)
    writer.printstring("Distance:")

    # Print distance
    Writer.set_textpos(ssd, y_pos, 10)
    writer.printstring(f"{state.distance:.2f} cm")
                        
async def updateDisplay():
    while True: 
        refresh(ssd) # Push everything at once
        await asyncio.sleep(0.05) # Caps refresh at 20 fps
        
async def sendReq():
    global last_send
    
    while True:
        if last_send is 0:
            last_send = ticks_ms() # Only updates when variable reset
            
        # Update Blynk every minutes
        if ticks_diff(ticks_ms(), last_send) > 60000:
            try:
                BLYNK.virtual_write(0, state.brightness)
                BLYNK.virtual_write(1, state.distance)
            except Exception as e:
                print(f"Error: {e}")
            finally:
                print("Data updated to Blynk!!!")
                last_send = 0 # Reset variable
                
        await asyncio.sleep(1)

# Keep Blynk connection alive
async def blynk_maintenance():
    while True:
        BLYNK.run()
        await asyncio.sleep(00.05)
        
# Function to clear memory
async def clearMemory():
    while True:
        gc.collect()
        
        await asyncio.sleep(0.5)

async def main():
    """
    Function does:
    - Clear old text
    - Place new text into position
    - Doesn't push new text to screen
    
    **updateDisplay() will push all text onto screen 20 times per sec
    **FPS will be calculated based get distance operation's duration, not based on updateDisplay()
    """
    task1 = asyncio.create_task(changeMode())
    task2 = asyncio.create_task(brightnessCtrl())
    task3 = asyncio.create_task(getDistance())
    task4 = asyncio.create_task(updateDisplay())
    task5 = asyncio.create_task(blynk_maintenance())
    task6 = asyncio.create_task(sendReq())
    task7 = asyncio.create_task(clearMemory())
    
    await asyncio.gather(task1, task2, task3, task4, task5, task6, task7)

asyncio.run(main())


