class BaseMenu:
    def __init__(self, display):
        self.display = display

    def draw_menu(self):
        pass  # Override this in derived classes

    def handle_input(self, input):
        pass  # Override for button input handling

class ConnectionMenu(BaseMenu):
    def __init__(self, display, device_list):
        super().__init__(display)
        self.devices = device_list

    def draw_menu(self):
        self.display.clear()
        self.display.printstring("  Select Device", color=self.display.cyan)
        self.list_devices()

    def list_devices(self):
        for name in self.devices.keys():
            self.display.printstring(name)
