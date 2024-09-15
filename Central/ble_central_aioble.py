import uasyncio as asyncio
import aioble, asyncio
from machine import Pin
# import utime
import lcd_screen, lcd_buttons
from bluetooth import UUID

# UUIDs for your services and characteristics
IO_SERVICE_UUID = UUID('0e024d3a-fa3e-455c-bb2c-4a3bcfaf8454')
IO_CHARACTERISTIC_UUID = UUID('1a0e5013-fbd8-4ca7-b38d-683e25c9eb97')

# Dictionary to store scanned devices
scanned_devices = {}

#Initialize Button handler
buttons = lcd_buttons.ButtonHandler()
    
def address_from_bytes(bytes_object):
    return ':'.join(f'{byte:02X}' for byte in bytes_object)

async def write_value(connection, byte_value):
    try:
        # Find characteristic to write
        service = await connection.service(SERVICE_UUID)
        characteristic = await service.characteristic(CHARACTERISTIC_UUID)
        await characteristic.write(byte_value)
#         print(f"Characteristic updated to: {byte_value}")
    except Exception as e:
#         print(f"Error writing characteristic: {e}")
        pass

async def handle_characteristic_update(data):
    # Handle incoming notifications or indications from connected peripheral devices
    print(f"\nUpdate received: {data}")

async def spinner_task():
    spinner = '-\\|/-\\|/'
    while True:  # Keep the spinner running indefinitely
        for x in spinner:
            c = lcd_screen.white
            lcd_screen.printchar(x, lcd_screen.cursor_x, lcd_screen.cursor_y, 2, True, c)
            await asyncio.sleep(0.1)
            lcd_screen.delchar(lcd_screen.cursor_x, lcd_screen.cursor_y, 2, True)

async def scan_task():
    global scanned_devices
    # Start scanning
    print("Scanning for devices...")
    lcd_screen.printstring("Scanning ", newline=False)
    async with aioble.scan(5000, interval_us=30000, window_us=30000, active=False) as scanner:
        #Scan for 5 seconds total, scan every 30 milliseconds (interval), for 30 milliseconds (window) in active or passive mode
        async for result in scanner:
            print(f"Found device: {result.device.addr} (Name: {result.name()})")
            if result.device.addr not in [d.addr for d in scanned_devices.values()] and result.name() != None:
                scanned_devices[result.name()] = result.device


async def run():
    # Create the BLE scan task and the spinner task
    scan_task_obj = asyncio.create_task(scan_task())
    spinner_task_obj = asyncio.create_task(spinner_task())

    await scan_task_obj
    spinner_task_obj.cancel()
    
   
    # Print the list of scanned devices
    lcd_screen.clear()
    print("\nScanned devices:")
    for i, (name, device) in enumerate(scanned_devices.items()):
        print(f"{i}: {device.addr} (Name: {name})")
        lcd_screen.printstring(f"{i}: {name}")

    # Ask user to select a device
    while True:
        try:
            choice = int(input("\nEnter the number of the device you want to connect to: "))
            if 0 <= choice < len(scanned_devices):
                break  # Valid input, exit the loop
            else:
                print("Invalid selection. Please choose a valid device number.")
        except ValueError:
            print("Invalid input. Please enter a number.")

    # Retrieve the selected device
    selected_device_name = list(scanned_devices.keys())[choice]
    selected_device = scanned_devices[selected_device_name]

    # Connect to the selected device
    await connect_to_device(selected_device)

async def indication_handler(characteristic):
    print("indication task started...")
    while True:
        try:
            print("Waiting for indication...")
            indication_data = await characteristic.indicated(timeout_ms=10000)
            # Handle the indication data
            print(f"Received indication: {indication_data}")
        except asyncio.TimeoutError:
            print("No indication received within the timeout period")

async def connect_to_device(device):
    global button_A_pressed, button_B_pressed
    try:
        # async with aioble.connect(device) as connection:
        connection = await device.connect()
        addr = address_from_bytes(device.addr)
        print(f"Connected to { addr }")
        lcd_screen.printstring(f"Connected to", clearscreen=True, color=lcd_screen.green)
        lcd_screen.printstring(f"{ addr }", color=lcd_screen.green)
    except Exception as e:
        print(f"Connection Error: {e}")

    try:
        io_service = await connection.service(IO_SERVICE_UUID)
        io_characteristic = await io_service.characteristic(IO_CHARACTERISTIC_UUID)
        print(f"Characteristic properties: {io_characteristic.properties}")
        await io_characteristic.subscribe(indicate=True)
        indication_task = asyncio.create_task(indication_handler(io_characteristic))
    except Exception as e:
        print(f"Error discovering services/characteristics: {e}")

    led_value = await io_characteristic.read()
    if led_value == b'\x01':
        print(f"Current peripheral LED value: ON")
    else:
        print(f"Current peripheral LED value: OFF")

    while connection.is_connected():
        if buttons.A_button_pressed:           
            await io_characteristic.write(bytearray([1]))
            buttons.A_button_pressed = False
        if buttons.B_button_pressed:
            await io_characteristic.write(bytearray([0]))
            buttons.B_button_pressed = False

# Run the async event loop
asyncio.run(run())