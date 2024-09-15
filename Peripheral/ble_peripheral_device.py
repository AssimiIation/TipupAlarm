from machine import Pin
import ubluetooth
import time
from micropython import const

_IRQ_CENTRAL_CONNECT = const(1)
_IRQ_CENTRAL_DISCONNECT = const(2)
_IRQ_GATTS_WRITE = const(3)
_IRQ_GATTS_READ_REQUEST = const(4)
_IRQ_SCAN_RESULT = const(5)
_IRQ_SCAN_DONE = const(6)
_IRQ_PERIPHERAL_CONNECT = const(7)
_IRQ_PERIPHERAL_DISCONNECT = const(8)
_IRQ_GATTC_SERVICE_RESULT = const(9)
_IRQ_GATTC_SERVICE_DONE = const(10)
_IRQ_GATTC_CHARACTERISTIC_RESULT = const(11)
_IRQ_GATTC_CHARACTERISTIC_DONE = const(12)
_IRQ_GATTC_DESCRIPTOR_RESULT = const(13)
_IRQ_GATTC_DESCRIPTOR_DONE = const(14)
_IRQ_GATTC_READ_RESULT = const(15)
_IRQ_GATTC_READ_DONE = const(16)
_IRQ_GATTC_WRITE_DONE = const(17)
_IRQ_GATTC_NOTIFY = const(18)
_IRQ_GATTC_INDICATE = const(19)
_IRQ_GATTS_INDICATE_DONE = const(20)
_IRQ_MTU_EXCHANGED = const(21)
_IRQ_L2CAP_ACCEPT = const(22)
_IRQ_L2CAP_CONNECT = const(23)
_IRQ_L2CAP_DISCONNECT = const(24)
_IRQ_L2CAP_RECV = const(25)
_IRQ_L2CAP_SEND_READY = const(26)
_IRQ_CONNECTION_UPDATE = const(27)
_IRQ_ENCRYPTION_UPDATE = const(28)
_IRQ_GET_SECRET = const(29)
_IRQ_SET_SECRET = const(30)

_FLAG_BROADCAST = const(0x0001)
_FLAG_READ = const(0x0002)
_FLAG_WRITE_NO_RESPONSE = const(0x0004)
_FLAG_WRITE = const(0x0008)
_FLAG_NOTIFY = const(0x0010)
_FLAG_INDICATE = const(0x0020)
_FLAG_AUTHENTICATED_SIGNED_WRITE = const(0x0040)

_FLAG_AUX_WRITE = const(0x0100)
_FLAG_READ_ENCRYPTED = const(0x0200)
_FLAG_READ_AUTHENTICATED = const(0x0400)
_FLAG_READ_AUTHORIZED = const(0x0800)
_FLAG_WRITE_ENCRYPTED = const(0x1000)
_FLAG_WRITE_AUTHENTICATED = const(0x2000)
_FLAG_WRITE_AUTHORIZED = const(0x4000)

class BLEPeripheral:
    def __init__(self):
        self.ble = ubluetooth.BLE()
        self.ble.active(True)
        self.ble.irq(self.on_ble_event)
        self.display_config()
        self.binary_state = False
        
        # Initialize the LED pin
        self.led = Pin("LED", Pin.OUT)  #Specific for Pi Pico
        self.led_on = False
        self.advertising = False
        
        self.init_ble_services()
        self.advertise()

    def address_from_bytes(self, bytes_object):
        return ':'.join(f'{byte:02X}' for byte in bytes_object)

    def display_config(self):
        mac_address = self.address_from_bytes(self.ble.config('mac')[1])
        print(f"Device address: { mac_address }")

    def init_ble_services(self):
        self.io_service_uuid = ubluetooth.UUID('0e024d3a-fa3e-455c-bb2c-4a3bcfaf8454')
        self.io_char = (ubluetooth.UUID('1a0e5013-fbd8-4ca7-b38d-683e25c9eb97'), ubluetooth.FLAG_READ | ubluetooth.FLAG_WRITE | ubluetooth.FLAG_NOTIFY,)
        io_service = (self.io_service_uuid, (self.io_char,),)
        
        self.registered_service = self.ble.gatts_register_services([io_service])
        print(self.registered_service)

        self.update_characteristic()  # Set initial value for the characteristic
        print("BLE services initialized.")

    def update_characteristic(self):
        # Update the characteristic value based on the binary state
        state_bytes = bytearray([int(self.binary_state)])
        print(f"state_bytes: { state_bytes }")
        self.ble.gatts_write(self.registered_service[0][0], state_bytes)
        print(f"Characteristic updated to: {self.binary_state}")


    def advertise(self):
        # BLE advertising parameters
        name = "Matts Pico"  # Name of the device
        self.ble.gap_advertise(100, b'\x02\x01\x06\x03\x03\xAA\xFE\x0B\x09' + name.encode())
        self.advertising = True
        print("Advertising started...")

    def stop_advertising(self):
        self.ble.gap_advertise(0)  # Stop advertising
        self.advertising = False
        print("Advertising stopped.")

    def on_ble_event(self, event, data):
        print(f"BLE Event code received: { event }") #Debug line

        if event == _IRQ_CENTRAL_CONNECT:
            conn_handle, addr_type, addr = data
            print(f"Connected to: { self.address_from_bytes(addr) }")
            self.stop_advertising()

        elif event == _IRQ_CENTRAL_DISCONNECT:
            conn_handle, addr_type, addr = data
            print(f"Disconnected from: { self.address_from_bytes(addr) }")
            self.advertise()

        elif event == _IRQ_GATTS_WRITE:
            conn_handle, attr_handle = data
            value = self.ble.gatts_read(attr_handle)
            print(f"GATTS Write data: { value }")
            if value == b'\x01':
                self.led.on()
                print("LED turned on")

    def update_led(self):
        if self.advertising:
            # Blink the LED while advertising
            self.led_on = not self.led_on
        else:
            # Keep the LED on when connected
            self.led_on = False

        self.led.value(self.led_on)

# Create an instance of the BLEPeripheral class to start advertising
ble_peripheral = BLEPeripheral()

# Keep the script running
while True:
    time.sleep(.5)
    ble_peripheral.update_led()