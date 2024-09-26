import aioble, asyncio, gc
from bluetooth import UUID
from tipup_device import TipupDevice

class MenuManager:
    def __init__(self):
        self.previous_menu = None
        self.active_menu = None

        #Testing below
        self.indication_buffer = []
        self.connected_devices = {}
        aioble.core.register_irq_handler(self.ble_irq, None)

    def ble_irq(self, event, data):
        #_IRQ_PERIPHERAL_CONNECT
        if event == 7:
            conn_handle, addr_type, addr = data
            print(f"--IRQ CONNECT: handle={ conn_handle } addr_type={ addr_type } addr={ bytes(addr) } ")
        #_IRQ_PERIPHERAL_DISCONNECT
        elif event == 8:
            conn_handle, addr_type, addr = data
            pass
        #_IRQ_GATTC_INDICATE
        elif event == 19:
            conn_handle, val_handle, val = data
            self.indication_buffer.append((conn_handle, val_handle, bytes(val)))
    
    async def set_active_menu(self, menu):
        #Only assigns current active_menu to previous_menu if it isn't None type, or the same type as the incoming menu
        if self.active_menu is not None and not isinstance(self.active_menu, type(menu)):
            self.previous_menu = self.active_menu
        if self.active_menu != None:
            self.active_menu.exit()
        self.active_menu = menu
        await menu.draw_menu()
        gc.collect()

    async def button_pressed(self, button):
        if self.active_menu:
            result = await self.active_menu.handle_input(button)
            if isinstance(result, BaseMenu):
                await self.set_active_menu(result)

class BaseMenu:
    def __init__(self, display, manager):
        self.display = display
        self.manager = manager

    async def draw_menu(self):
        raise NotImplementedError("Subclass needs to override draw_menu() method")
    
    def exit(self):
        # Override this in derived classes
        raise NotImplementedError("Subclass needs to override exit_menu() method")

    async def handle_input(self, input):
        # Override for button input handling
        raise NotImplementedError("Subclass needs to override handle_input() method")
    
class SplashMenu(BaseMenu):
    async def draw_menu(self):
        self.display.clear()
        self.display.move_cursor(0, int(240/2) - 9)
        self.display.printstring("   BlueNote", size=3, charupdate=True, color=self.display.cyan)
        self.display.printstring(" Press any button", size=2)

    def exit(self):
        pass
    
    async def handle_input(self, input):
        print(f"Button pressed: { input }")
        return ScanMenu(self.display, self.manager)
    
class MainMenu(BaseMenu):
    def __init__(self, display, manager):
        super().__init__(display, manager)
        self.selected_option_index = 0

    async def draw_menu(self):
        self.display.clear()
        self.display.printstring("   Main Menu", color=self.display.cyan)
        self.draw_selection()
        self.list_options()

    def exit(self):
        pass

    async def handle_input(self, input):
        if input == "LEFT":
            self.selected_option_index -= 1
            if self.selected_option_index < 0:
                self.selected_option_index = 2
            self.draw_selection()
        elif input == "RIGHT":
            self.selected_option_index += 1
            if self.selected_option_index > 2:
                self.selected_option_index = 0
            self.draw_selection()
        elif input == "SELECT":
            if self.selected_option_index == 0:
                return ScanMenu(self.display, self.manager)
            elif self.selected_option_index == 1:
                print("==[ Connected Devices ]==")
                for device in self.manager.connected_devices.keys():
                    print(device)


    def list_options(self):
        self.display.printstring("0: Scan for          Devices")
        self.display.printstring("1: Connected         Devices")
        self.display.printstring("2: Options")

    def draw_selection(self):
        self.display.delchar(98, 21, 2, False)
        self.display.printchar('<', 70, 21, 2, False)
        self.display.printchar(str(self.selected_option_index), 98, 21, 2, True, self.display.yellow)
        self.display.printchar('>', 126, 21, 2, False)
        self.display.move_cursor(0, 39)

class ConnectedDevices(BaseMenu):
    def __init__(self, display, manager):
        super().__init__(display, manager)
        self.selected_option_index = 0

    async def draw_menu(self):
        self.display.clear()
        self.display.printstring(" Connected Devices", color=self.display.green)
        self.draw_selection
        self.list_devices()

    def exit(self):
        pass

    async def handle_input(self, input):
        if input == "LEFT":
            self.selected_option_index -= 1
            if self.selected_option_index < 0:
                self.selected_option_index = 2
            self.draw_selection()
        elif input == "RIGHT":
            self.selected_option_index += 1
            if self.selected_option_index > 2:
                self.selected_option_index = 0
            self.draw_selection()
        elif input == "SELECT":
            pass

    def draw_selection(self):
        self.display.delchar(98, 21, 2, False)
        self.display.printchar('<', 70, 21, 2, False)
        self.display.printchar(str(self.selected_option_index), 98, 21, 2, True, self.display.yellow)
        self.display.printchar('>', 126, 21, 2, False)
        self.display.move_cursor(0, 39)

    def list_devices(self):
       for index, device in enumerate(self.manager.connected_devices.items()):
            self.display.printstring(f"{ index }:{ device.name }")            
    
class ScanMenu(BaseMenu):
    def __init__(self, display, manager):
        self.display = display
        self.manager = manager
        self.scanned_devices = {}

    async def draw_menu(self):
        self.display.clear()
        await self.scan_for_devices()

        await self.manager.set_active_menu(DevicesMenu(self.display, self.manager, self.scanned_devices))

    def exit(self):
        pass

    async def handle_input(self, input):
        pass

    async def scan_for_devices(self):
        scan_task_obj = asyncio.create_task(self.scan_task())
        spinner_task_obj = asyncio.create_task(self.spinner_task(scan_task_obj))

        await scan_task_obj
        await spinner_task_obj
    
    async def spinner_task(self, scan_task_obj):
        spinner = '-\\|/-\\|/'
        scan_ongoing = True
        while scan_ongoing:  # Keep the spinner running indefinitely
            for x in spinner:
                c = self.display.cyan
                center = int(240/2) - 18
                self.display.delchar(center, center, 3, True)
                self.display.printchar(x, center, center, 3, True, c)
                await asyncio.sleep(0.05)

                if scan_task_obj.done():
                    scan_ongoing = False   
        print("Spinner task completed")                 

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
        print("Scan task finished")

class DevicesMenu(BaseMenu):
    def __init__(self, display, manager, device_list):
        super().__init__(display, manager)
        self.device_list = device_list
        self.selected_device_index = 0
        self.no_devices = False

    async def draw_menu(self):
        self.display.clear()
        if len(self.device_list) > 0:
            self.display.printstring("  Select Device", color=self.display.cyan)
            self.draw_selection()
            self.list_devices()
        else:
            self.display.printstring("  No Devices", size=3, color=self.display.red)
            self.display.printstring("    Found", size = 3, color=self.display.red)
            self.display.printstring("Press any button to scan again", size=2)
            self.no_devices = True

    def exit(self):
        pass

    def draw_selection(self):
        self.display.delchar(98, 21, 2, False)
        self.display.printchar('<', 70, 21, 2, False)
        self.display.printchar(str(self.selected_device_index), 98, 21, 2, True, self.display.yellow)
        self.display.printchar('>', 126, 21, 2, False)
        self.display.move_cursor(0, 39)

    async def handle_input(self, input):
        # TODO - add logic to start a new scan if no devices are found, make buttons change selction index
        if self.no_devices:
            self.manager.set_active_menu(ScanMenu(self.display, self.manager))
        elif input == "LEFT":
            self.selected_device_index -= 1
            if self.selected_device_index < 0:
                self.selected_device_index = len(self.device_list) - 1
            self.draw_selection()
        elif input == "RIGHT":
            self.selected_device_index += 1
            if self.selected_device_index > len(self.device_list) - 1:
                self.selected_device_index = 0
            self.draw_selection()
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
        
        async def draw_menu(self):
            self.display.clear()
            await self.connect_to_device(self.device)

        def exit(self):
            pass

        async def handle_input(self, input):
            if input == "A":
                await self.set_io_characteristic(1)
            elif input == "B":
                await self.set_io_characteristic(0)
            elif input == "Y":
                return MainMenu(self.display, self.manager)      

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
            addr = self.address_from_bytes(device.addr)
            if addr not in self.manager.connected_devices:
                # try:
                #Connect to the selected device
                connection = await device.connect()
                new_device = TipupDevice(connection._conn_handle, self.device_name, addr)
                # except Exception as e:
                #     print(f"Connection Error: {e}")

                try:
                    #Discover services and subscribe to characteristics
                    io_service = await connection.service(self.io_service_uuid)
                    self.io_characteristic = await io_service.characteristic(self.io_characteristic_uuid)
                    print(f"Characteristic properties: { self.decode_characteristic_properties(self.io_characteristic.properties) }")
                    await self.io_characteristic.subscribe(indicate=True)
                except Exception as e:
                    print(f"Error discovering services/characteristics: {e}")

                #Adds the new device to the connected devices list
                self.manager.connected_devices[addr] = new_device

                led_value = await self.io_characteristic.read()
                if led_value == b'\x01':
                    print(f"Current peripheral LED value: ON")
                else:
                    print(f"Current peripheral LED value: OFF")
            
            self.display.printstring(f"Connected to", clearscreen=True, color=self.display.green)
            self.display.printstring(f"{ addr }", color=self.display.green)



class AlertMenu(BaseMenu):
    def __init__(self, display, manager):
        super().__init__(display, manager)
        self.flashing_task = None
        self.flashing = True
        
    async def draw_menu(self):
        self.display.clear()
        self.flashing_task = asyncio.create_task(self.draw_background())
        print("draw_menu() finished")
        # await flash_background_task

    def exit(self):
        if not self.flashing_task.done():
            self.flashing_task.cancel()

    async def handle_input(self, input):
        self.flashing = False
        await self.manager.set_active_menu(self.manager.previous_menu)

    async def draw_background(self):
        print("Drawing background")
        bg_colors = [self.display.cyan, self.display.black]

        while self.flashing:
            self.display.fill_rect(0, 0, 240, 240, bg_colors[0])    #xywh
            #Swap colors to imitate screen flashing
            bg_colors[0], bg_colors[1] = bg_colors[1], bg_colors[0]
            self.display.fill_rect(40, 92, 160, 100, self.display.black)
            self.write_message()
            await asyncio.sleep(.5)
        print("Flashing task finished")
    
    def write_message(self):
        self.display.move_cursor(0, int(240 * .5) - 18)
        self.display.printstring("   FISH ON!", size=3, strupdate=False, color=self.display.cyan)
        self.display.printstring("    Press any          button          to clear")
