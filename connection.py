import network
import time
import env

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(env.WIFI_NAME, env.WIFI_PASSWORD)

while not wlan.isconnected():
    print("Connecting...")
    time.sleep(1)
print("Connected!")

