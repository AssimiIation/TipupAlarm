import asyncio
import lcd_screen, lcd_buttons, menus

buttons = lcd_buttons.ButtonHandler()
menu_manager = menus.MenuManager()
display = lcd_screen.LCD_1inch3()

async def run():
    main_menu = menus.MainMenu(display, menu_manager)
    menu_manager.set_active_menu(main_menu)

    while True:
        if buttons.A_button_pressed:
            menu_manager.button_pressed("A")
            buttons.A_button_pressed = False
        elif buttons.B_button_pressed:
            menu_manager.button_pressed("B")
            buttons.B_button_pressed = False
        elif buttons.X_button_pressed:
            menu_manager.button_pressed("X")
            buttons.X_button_pressed = False
        elif buttons.Y_button_pressed:
            menu_manager.button_pressed("Y")
            buttons.Y_button_pressed = False
        elif buttons.up_button_pressed:
            menu_manager.button_pressed("UP")
            buttons.up_button_pressed = False
        elif buttons.down_button_pressed:
            menu_manager.button_pressed("DOWN")
            buttons.down_button_pressed = False
        elif buttons.left_button_pressed:
            menu_manager.button_pressed("LEFT")
            buttons.left_button_pressed = False
        elif buttons.right_button_pressed:
            menu_manager.button_pressed("RIGHT")
            buttons.right_button_pressed = False
        elif buttons.select_button_pressed:
            menu_manager.button_pressed("SELECT")
            buttons.select_button_pressed = False

asyncio.run(run())