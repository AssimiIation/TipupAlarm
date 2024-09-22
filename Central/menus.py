import aioble, asyncio
from bluetooth import UUID

class MenuManager:
    def __init__(self):
        self.previous_menu = None
        self.active_menu = None

        #Testing below
        self.indication_buffer = []
        aioble.core.register_irq_handler(self.ble_irq, None)

    def ble_irq(self, event, data):
        #_IRQ_GATTC_INDICATE
        if event == 19:
            conn_handle, val_handle, val = data
            self.indication_buffer.append((conn_handle, val_handle, bytes(val)))
    
    def set_active_menu(self, menu):
        if self.active_menu != None:
            self.previous_menu = self.active_menu
        self.active_menu = menu
        menu.draw_menu()

    def button_pressed(self, button):
        if self.active_menu:
            result = self.active_menu.handle_input(button)
            if isinstance(result, BaseMenu):
                self.set_active_menu(result)

class BaseMenu:
    def __init__(self, display, manager):
        self.display = display
        self.manager = manager

    def draw_menu(self):
        # Override this in derived classes
        raise NotImplementedError("Subclass needs to override draw_menu() method")

    def handle_input(self, input):
        # Override for button input handling
        raise NotImplementedError("Subclass needs to override handle_input() method")
    
class MainMenu(BaseMenu):
    def draw_menu(self):
        self.display.clear()
        self.display.move_cursor(0, int(240/2) - 9)
        self.display.printstring("   BlueNote", size=3, charupdate=True, color=self.display.cyan)
        self.display.printstring(" Press any button", size=2)
    
    def handle_input(self, input):
        print(f"Button pressed: { input }")
        return ScanMenu(self.display, self.manager)
    
class ScanMenu(BaseMenu):
    def __init__(self, display, manager):
        self.display = display
        self.manager = manager
        self.scanned_devices = {}

    def draw_menu(self):
        self.display.clear()
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.scan_for_devices())
        self.manager.set_active_menu(DevicesMenu(self.display, self.manager, self.scanned_devices))

    def handle_input(self, input):
        pass

    async def scan_for_devices(self):
        scan_task_obj = asyncio.create_task(self.scan_task())
        spinner_task_obj = asyncio.create_task(self.spinner_task())

        await scan_task_obj
        spinner_task_obj.cancel()
    
    async def spinner_task(self):
        spinner = '-\\|/-\\|/'
        while True:  # Keep the spinner running indefinitely
            for x in spinner:
                c = self.display.cyan
                center = int(240/2) - 18
                self.display.delchar(center, center, 3, True)
                self.display.printchar(x, center, center, 3, True, c)
                await asyncio.sleep(0.05)

    async def scan_task(self):
        # Start scanning
        print("Scanning for devices...")
        self.display.move_cursor(48, 147)
        self.display.printstring("Scanning", size=3, newline=False)
        async with aioble.scan(5000, interval_us=30000, window_us=30000, active=False) as scanner:
            #Scan for 5 seconds total, scan every 30 milliseconds (interval), for 30 milliseconds (window) in active or passive mode
            async for result in scanner:
                print(f"Found device: {result.device.addr} (Name: {result.name()})")
                if result.device.addr not in [d.addr for d in self.scanned_devices.values()] and result.name() != None:
                    self.scanned_devices[result.name()] = result.device

class DevicesMenu(BaseMenu):
    def __init__(self, display, manager, device_list):
        super().__init__(display, manager)
        self.device_list = device_list
        self.selected_device_index = 0
        self.no_devices = False

    def draw_menu(self):
        self.display.clear()
        if len(self.device_list) > 0:
            self.display.printstring("  Select Device", color=self.display.cyan)
            self.draw_selection(self.selected_device_index)
            self.list_devices()
        else:
            self.display.printstring("  No Devices", size=3, color=self.display.red)
            self.display.printstring("    Found", size = 3, color=self.display.red)
            self.display.printstring("Press any button to scan again", size=2)
            self.no_devices = True

    def draw_selection(self, index):
        self.display.delchar(98, 21, 2, False)
        self.display.printchar('<', 70, 21, 2, False)
        self.display.printchar(str(self.selected_device_index), 98, 21, 2, True, self.display.yellow)
        self.display.printchar('>', 126, 21, 2, False)
        self.display.move_cursor(0, 39)

    def handle_input(self, input):
        # TODO - add logic to start a new scan if no devices are found, make buttons change selction index
        if self.no_devices:
            self.manager.set_active_menu(ScanMenu(self.display, self.manager))
        elif input == "LEFT":
            self.selected_device_index -= 1
            if self.selected_device_index < 0:
                self.selected_device_index = len(self.device_list) - 1
            self.draw_selection(self.selected_device_index)
        elif input == "RIGHT":
            self.selected_device_index += 1
            if self.selected_device_index > len(self.device_list) - 1:
                self.selected_device_index = 0
            self.draw_selection(self.selected_device_index)
        elif input == "SELECT":
            try:
                selected_device = list(self.device_list.keys())[self.selected_device_index]
                print(f"You selected { selected_device }")
                connected_menu = TestConnectedMenu(self.display, self.manager, selected_device, self.device_list[selected_device])
                return connected_menu
            except ValueError as e:
                print(e)

    def list_devices(self):
        for index, name in enumerate(self.device_list.keys()):
            self.display.printstring(f"{ index }:{ name }")

class TestConnectedMenu(BaseMenu):
        def __init__(self, display, manager, device_name, device):
            super().__init__(display, manager)
            self.device_name = device_name
            self.device = device
            self.io_service_uuid = UUID('0e024d3a-fa3e-455c-bb2c-4a3bcfaf8454')
            self.io_characteristic_uuid = UUID('1a0e5013-fbd8-4ca7-b38d-683e25c9eb97')
            self.io_characteristic = None
        
        def draw_menu(self):
            self.display.clear()
            loop = asyncio.get_event_loop()
            loop.run_until_complete(self.connect_to_device(self.device))

        def handle_input(self, input):
            if input == "A":
                loop = asyncio.get_event_loop()
                loop.run_until_complete(self.set_io_characteristic(1))
            elif input == "B":
                loop = asyncio.get_event_loop()
                loop.run_until_complete(self.set_io_characteristic(0))
                

        def address_from_bytes(self, bytes_object):
            return ':'.join(f'{byte:02X}' for byte in bytes_object)
        
        def decode_characteristic_properties(self, properties):
            descriptions = []
            if properties & 0x01:  # Broadcast
                descriptions.append("Broadcast")
            if properties & 0x02:  # Read
                descriptions.append("Read")
            if properties & 0x04:  # Write Without Response
                descriptions.append("Write Without Response")
            if properties & 0x08:  # Write
                descriptions.append("Write")
            if properties & 0x10:  # Notify
                descriptions.append("Notify")
            if properties & 0x20:  # Indicate
                descriptions.append("Indicate")
            if properties & 0x40:  # Authenticate
                descriptions.append("Authenticated")
            if properties & 0x80:  # Extended Properties
                descriptions.append("Extended Properties")

            return ', '.join(descriptions)
        
        async def set_io_characteristic(self, byte_value):
            await self.io_characteristic.write(bytearray([byte_value]))

        async def connect_to_device(self, device):
            try:
                connection = await device.connect()
                addr = self.address_from_bytes(device.addr)
                print(f"Connected to { addr }")
                self.display.printstring(f"Connected to", clearscreen=True, color=self.display.green)
                self.display.printstring(f"{ addr }", color=self.display.green)
            except Exception as e:
                print(f"Connection Error: {e}")

            #temporary debugging block below:
            io_service = await connection.service(self.io_service_uuid)
            self.io_characteristic = await io_service.characteristic(self.io_characteristic_uuid)
            print(f"++ io_characteristic={self.io_characteristic}")
            print(f"Characteristic properties: { self.decode_characteristic_properties(self.io_characteristic.properties) }")
            await self.io_characteristic.subscribe(indicate=True)
            # indication_task = asyncio.create_task(self.indication_handler(self.io_characteristic))

            # try:
            #     io_service = await connection.service(self.io_service_uuid)
            #     self.io_characteristic = await io_service.characteristic(self.io_characteristic_uuid)
            #     print(f"Characteristic properties: { self.decode_characteristic_properties(self.io_characteristic.properties) }")
            #     await self.io_characteristic.subscribe(indicate=True)
            #     indication_task = asyncio.create_task(self.indication_handler(self.io_characteristic))
            # except Exception as e:
            #     print(f"Error discovering services/characteristics: {e}")

            led_value = await self.io_characteristic.read()
            if led_value == b'\x01':
                print(f"Current peripheral LED value: ON")
            else:
                print(f"Current peripheral LED value: OFF")

        async def indication_handler(self, characteristic):
            print("indication task started...")
            while True:
                try:
                    print("Waiting for indication...")
                    indication_data = await characteristic.indicated(timeout_ms=10000)
                    # Handle the indication data
                    print(f"Received indication: {indication_data}")
                except asyncio.TimeoutError:
                    print("No indication received within the timeout period")

class AlertMenu(BaseMenu):
    def draw_menu(self):
        self.display.clear()
        self.display.printstring("  FISH ON!  ", size=3, color=self.display.cyan)
        self.display.printstring("Press any button to clear", size=2)

    def handle_input(self, input):
        self.manager.set_active_menu(self.manager.previous_menu)