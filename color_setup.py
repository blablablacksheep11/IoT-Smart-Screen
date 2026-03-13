from machine import SPI, Pin
from drivers.st7789.st7789_4bit import ST7789 as SSD
import gc

pdc = Pin(21, Pin.OUT, value=0)
prst = Pin(20, Pin.OUT, value=1)
pcs = Pin(28, Pin.OUT, value=1) # Dummy pin

gc.collect() # Clear memory
spi = SPI(0, 30_000_000, sck=Pin(18), mosi=Pin(19), polarity=1, phase=1)
ssd = SSD(spi, dc=pdc, cs=pcs, rst=prst, height=240, width=240)
