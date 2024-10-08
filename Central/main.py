import lcd_screen, lcd_buttons, menus
import asyncio, gc


buttons = lcd_buttons.ButtonHandler()
menu_manager = menus.MenuManager()
display = lcd_screen.LCD_1inch3()

def gc_test():
    free = gc.mem_free()
    used = gc.mem_alloc()
    print("Free memory:", free)
    print("Allocated memory:", used)
    print(f"Used { int(used/(free + used)*100) }% of total memory")

async def check_input():
    if buttons.A_button_pressed:
        await menu_manager.button_pressed("A")
        buttons.A_button_pressed = False
    elif buttons.B_button_pressed:
        await menu_manager.button_pressed("B")
        buttons.B_button_pressed = False
    elif buttons.X_button_pressed:
        await menu_manager.button_pressed("X")
        gc_test()
        buttons.X_button_pressed = False
    elif buttons.Y_button_pressed:
        await menu_manager.button_pressed("Y")
        buttons.Y_button_pressed = False
    elif buttons.up_button_pressed:
        await menu_manager.button_pressed("UP")
        buttons.up_button_pressed = False
    elif buttons.down_button_pressed:
        await menu_manager.button_pressed("DOWN")
        buttons.down_button_pressed = False
    elif buttons.left_button_pressed:
        await menu_manager.button_pressed("LEFT")
        buttons.left_button_pressed = False
    elif buttons.right_button_pressed:
        await menu_manager.button_pressed("RIGHT")
        buttons.right_button_pressed = False
    elif buttons.select_button_pressed:
        await menu_manager.button_pressed("SELECT")
        buttons.select_button_pressed = False

async def run():
    main_menu = menus.MainMenu(display, menu_manager)
    await menu_manager.set_active_menu(main_menu)

    while True:
        if len(menu_manager.indication_buffer) > 0:
            for i in menu_manager.indication_buffer:
                conn_handle, val_handle, val = i
                print("####[Indication Received]####")
                print(f"Connection Handle: { conn_handle }")
                print(f"Value Handle: { val_handle }")
                print(f"Value: { val }")
                del menu_manager.indication_buffer[0]
                await menu_manager.set_active_menu(menus.AlertMenu(display, menu_manager))

        await check_input()
        await asyncio.sleep(0.01)

asyncio.run(run())