from machine import Pin, ADC, PWM
from gui.core.writer import Writer
from gui.core.nanogui import refresh
from color_setup import ssd
from time import sleep, sleep_us, ticks_ms, ticks_us, ticks_diff
import gui.fonts.montserrat20 as font_sm
import gui.fonts.montserrat30 as font_md
import gui.fonts.montserrat40 as font_lg
import gui.fonts.montserrat50 as font_xl
import gc
import network
import urequests
import time
import asyncio
import env

# Turn on backlight in default
blk_pwm = PWM(Pin(22))
blk_pwm.freq(1000)

# Setup writers
wri_sm = Writer(ssd, font_sm)
wri_md = Writer(ssd, font_md)
wri_lg = Writer(ssd, font_lg)
wri_xl = Writer(ssd, font_xl)

configs = {
    "md": (wri_md, 150),
    "lg": (wri_lg, 160),
    "xl": (wri_xl, 170)
}

# ThingSpeak endpoint
API_KEY = env.THINGSPEAK_API_KEY
url = "https://api.thingspeak.com/update"

last_send = 0 # Track last ThingSpeak updates

md_threshold = 5
lg_threshold = 15
xl_threshold = 25

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
        frame_rate = int(1000000 / (ticks_diff(ticks_us(), start_time) + 100000))

        # Print fps
        Writer.set_textpos(ssd, 10, 10)
        wri_sm.printstring(f"Frame rate:  {frame_rate} fps")
    
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
            last_send = ticks_us() # Only updates when variable reset
            
        # Update ThingSpeak every 16 sec
        if ticks_diff(ticks_us(), last_send) > 16000000:
            try:
                response = urequests.get(f"{url}?api_key={env.THINGSPEAK_API_KEY}&field1={state.brightness}&field2={state.distance}", timeout=5)
                if response.status_code == 200:
                    print("Data sent to ThingSpeak!!!")
            except Exception as e:
                print(f"Error: {e}")
            finally:
                if response:
                    response.close()
                last_send = 0 # Reset variable
                
        await asyncio.sleep(0.2)
        
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
    task5 = asyncio.create_task(sendReq())
    task6 = asyncio.create_task(clearMemory())
    
    await asyncio.gather(task1, task2, task3, task4, task5, task6)

# Network connection
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(env.WIFI_NAME, env.WIFI_PASSWORD)

while not wlan.isconnected():
    print("Connecting...")
    time.sleep(1)

if wlan.isconnected():
    print("Connected")
    
asyncio.run(main())
    