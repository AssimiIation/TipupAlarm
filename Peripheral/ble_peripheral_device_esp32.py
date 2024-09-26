from machine import Pin
from math import floor
import ubluetooth
import time
from micropython import const

_IRQ_CENTRAL_CONNECT = const(1)
_IRQ_CENTRAL_DISCONNECT = const(2)
_IRQ_GATTS_WRITE = const(3)
_IRQ_GATTS_READ_REQUEST = const(4)

_FLAG_READ = const(0x0002)
_FLAG_WRITE_NO_RESPONSE = const(0x0004)
_FLAG_WRITE = const(0x0008)
_FLAG_NOTIFY = const(0x0010)
_FLAG_INDICATE = const(0x0020)


# button_a = Button(12, invert=True)  #Signal button
button_a= Pin(27,Pin.IN,Pin.PULL_UP)

button_a_pressed = False

def button_a_handler(pin):
    global button_a_pressed
    button_a_pressed = True

button_a.irq(trigger=Pin.IRQ_FALLING, handler=button_a_handler)

class BLEPeripheral:
    def __init__(self):
        self.ble = ubluetooth.BLE()
        self.ble.active(True)
        self.ble.irq(self.on_ble_event)
        self.display_config()
        
        # Initialize the LED pin
        self.led = Pin(2, Pin.OUT)  # Specific for Pi Pico
        self.led_on = False
        self.advertising = False
        self.connected = False  #Track connection status
        self.connection_handle = None #Store the connection once made to a central device
        self.registered_service = None  # Will hold the service and characteristic
        self.io_service_uuid = ubluetooth.UUID('0e024d3a-fa3e-455c-bb2c-4a3bcfaf8454')
        self.io_char = (ubluetooth.UUID('1a0e5013-fbd8-4ca7-b38d-683e25c9eb97'), _FLAG_READ | _FLAG_WRITE_NO_RESPONSE | _FLAG_INDICATE)
        
        self.init_ble_services()
        self.advertise()

    def address_from_bytes(self, bytes_object):
        return ':'.join(f'{byte:02X}' for byte in bytes_object)

    def display_config(self):
        mac_address = self.address_from_bytes(self.ble.config('mac')[1])
        message = f"Device address: { mac_address }"
        print(message)

    def init_ble_services(self):
        io_service = (self.io_service_uuid, (self.io_char,),)
        
        self.registered_service = self.ble.gatts_register_services([io_service])
        print(self.registered_service)

        self.update_characteristic()  # Set initial value for the characteristic
        print("BLE services initialized.")

    def update_characteristic(self):
        # Update the characteristic value based on the binary state
        state_bytes = bytearray([int(self.led_on)])
        print(f"state_bytes: { state_bytes }")
        self.ble.gatts_write(self.registered_service[0][0], state_bytes)
        print(f"Characteristic updated to: {self.led_on}")

    def send_indication(self):
        #Notify central device of characteristic state change
        if self.connected and self.conn_handle is not None:
            self.ble.gatts_indicate(self.conn_handle, self.registered_service[0][0])
            print(f"--Notification sent to central: {self.conn_handle}")

    def advertise(self):
        # BLE advertising parameters
        name = "ESP tipup"  # Name of the device
        
        # Advertising flags: General Discoverable Mode, BR/EDR Not Supported
        adv_flags = b'\x02\x01\x06'
        
        # Complete Local Name (type 0x09)
        adv_name = b'\x0B\x09' + name.encode()
        
        # Combine advertising flags and name
        adv_data = adv_flags + adv_name
        
        # Start advertising with the modified advertisement data
        self.ble.gap_advertise(100, adv_data)
        
        self.advertising = True
        message = "Advertising started..."
        print(message)

    def stop_advertising(self):
        self.ble.gap_advertise(0)  # Stop advertising
        self.advertising = False
        message = "Advertising stopped."
        print(message)

    def on_ble_event(self, event, data):
        print(f"BLE Event code received: { event }")  # Debug line

        if event == _IRQ_CENTRAL_CONNECT:
            self.conn_handle, addr_type, addr = data
            print(f"Connected to device { self.address_from_bytes(addr) }")

            self.stop_advertising()
            self.connected = True

        elif event == _IRQ_CENTRAL_DISCONNECT:
            conn_handle, addr_type, addr = data
            print(f"Disconnected from: { self.address_from_bytes(addr) }")
            message = f"Disconnected"
            print(message)
            self.advertise()
            self.connected = False
            self.conn_handle = None 

        elif event == _IRQ_GATTS_WRITE:
            conn_handle, attr_handle = data
            value = self.ble.gatts_read(attr_handle)
            print(f"GATTS Write data: { value }")
            if value == b'\x01':
                self.led_on = True
                self.led.value(self.led_on)
                self.update_characteristic()  # Update the characteristic with new LED state
                print(f"LED state toggled: ON")

            elif value == b'\x00':
                self.led_on = False
                self.led.value(self.led_on)
                self.update_characteristic()  # Update the characteristic with new LED state
                print(f"LED state toggled: OFF")

    def update_led(self):
        if self.advertising and not self.connected:
            # Blink the LED while advertising and not connected
            self.led_on = not self.led_on
            self.led.value(self.led_on)
        else:
            # Ensure the LED is set to the correct state if not advertising
            self.led.value(self.led_on)

# Create an instance of the BLEPeripheral class to start advertising
ble_peripheral = BLEPeripheral()

# Keep the script running
while True:
    time.sleep(0.5)
    ble_peripheral.update_led()
    if button_a_pressed:
        print("Button A Pressed")
        ble_peripheral.send_indication()
        button_a_pressed = False