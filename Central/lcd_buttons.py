from machine import Pin
import utime

class ButtonHandler:
    def __init__(self):
        self.button_callbacks = {}

        self.A_button= Pin(15,Pin.IN,Pin.PULL_UP)
        self.B_button = Pin(17,Pin.IN,Pin.PULL_UP)
        self.X_button = Pin(19 ,Pin.IN,Pin.PULL_UP)
        self.Y_button= Pin(21 ,Pin.IN,Pin.PULL_UP)
        self.up_button = Pin(2,Pin.IN,Pin.PULL_UP)
        self.down_button = Pin(18,Pin.IN,Pin.PULL_UP)
        self.left_button = Pin(16,Pin.IN,Pin.PULL_UP)
        self.right_button = Pin(20,Pin.IN,Pin.PULL_UP)
        self.select_button = Pin(3,Pin.IN,Pin.PULL_UP)

        self.A_button_pressed = False
        self.B_button_pressed = False
        self.X_button_pressed = False
        self.Y_button_pressed = False
        self.up_button_pressed = False
        self.down_button_pressed = False
        self.left_button_pressed = False
        self.right_button_pressed = False
        self.select_button_pressed = False

        self.set_handlers()

        self.new_time = 0
        self.last_time = 0
        self.debounce_limit = 300

    def wait_time_has_elapsed(self):
        self.new_time = utime.ticks_ms()
        if (self.new_time - self.last_time > self.debounce_limit):
            self.last_time = self.new_time
            return True
        else:
            return False

    def A_button_handler(self, pin):
        if self.wait_time_has_elapsed():
            self.A_button_pressed = True

    def B_button_handler(self, pin):
        if self.wait_time_has_elapsed():
            self.B_button_pressed = True

    def X_button_handler(self, pin):
        if self.wait_time_has_elapsed:
            self.X_button_pressed = True

    def Y_button_handler(self, pin):
        if self.wait_time_has_elapsed:
            self.Y_button_pressed = True

    def up_button_handler(self, pin):
        if self.wait_time_has_elapsed:
            self.up_button_pressed = True

    def down_button_handler(self, pin):
        if self.wait_time_has_elapsed:
            self. down_button_pressed = True

    def left_button_handler(self, pin):
        if self.wait_time_has_elapsed:
            self.left_button_pressed = True

    def right_button_handler(self, pin):
        if self.wait_time_has_elapsed:
            self.right_button_pressed = True

    def select_button_handler(self, pin):
        if self.wait_time_has_elapsed:
            self.select_button_pressed = True

    def set_handlers(self):
        self.A_button.irq(trigger=Pin.IRQ_FALLING, handler = lambda pin: self.A_button_handler(pin))
        self.B_button.irq(trigger=Pin.IRQ_FALLING, handler = lambda pin: self.B_button_handler(pin))
        self.X_button.irq(trigger=Pin.IRQ_FALLING, handler = lambda pin: self.X_button_handler(pin))
        self.Y_button.irq(trigger=Pin.IRQ_FALLING, handler = lambda pin: self.Y_button_handler(pin))
        self.up_button.irq(trigger=Pin.IRQ_FALLING, handler = lambda pin: self.up_button_handler(pin))
        self.down_button.irq(trigger=Pin.IRQ_FALLING, handler = lambda pin: self.down_button_handler(pin))
        self.left_button.irq(trigger=Pin.IRQ_FALLING, handler = lambda pin: self.left_button_handler(pin))
        self.right_button.irq(trigger=Pin.IRQ_FALLING, handler = lambda pin: self.right_button_handler(pin))
        self.select_button.irq(trigger=Pin.IRQ_FALLING, handler = lambda pin: self.select_button_handler(pin))