# Smart Screen 👁️💻

A privacy-first IoT solution designed to mitigate digital eye strain by automatically adjusting **screen brightness** and **typography size** based on user proximity and ambient lighting.


## 📌 Features
* **Privacy-Centric Sensing:** Uses the **HC-SR04P Ultrasonic Sensor** (sound waves) instead of cameras to detect distance, ensuring zero risk of unauthorized surveillance.
* **Dynamic Font Scaling:** Automatically scales text size across 4 discrete levels to maintain readability as the user moves.
* **Auto-Brightness:** Adjusts display intensity based on real-time LDR sensor data to prevent glare and visual fatigue.
* **IoT Dashboard:** Real-time data visualization via **Blynk Cloud** with near-zero latency for remote monitoring.
* **Ergonomic Logic:** Treats light and distance as independent variables to provide a more stable and comfortable user experience.


## 🛠️ Tech Stack
* **Microcontroller:** Raspberry Pi Pico WH
* **Display:** ST7789 IPS LCD (240x240)
* **Firmware:** MicroPython
* **Connectivity:** Wi-Fi via Blynk IoT Library
* **Sensors:** HC-SR04P (Ultrasonic), LDR (Photoresistor)


## 🚀 Quick Start
You many copy the source code to the board using the ```mip```.

**Make sure your board is connected to Wi-Fi !!!**
```python
  >>> import mip
  >>> mip.install("github:blablablacksheep11/IoT-Smart-Screen", target="/")
```
