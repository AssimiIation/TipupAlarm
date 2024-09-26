The default Micropython firmware for Pi Pico W does not have multiple bluetooth connections enabled

From the link - https://github.com/orgs/micropython/discussions/12674 :

        I too am using the PICO_W. You cannot configure the number of simultaneous connections in aioble as each stack needs its own way of setting up memory for such endeavors and thus it is port dependent. When you build the Micropython firmware for the PICO port (btstack) there will be #defines where you set the number of connections.

        I changed these two
        #define MAX_NR_GATT_CLIENTS 1
        #define MAX_NR_HCI_CONNECTIONS 1
        to
        #define MAX_NR_GATT_CLIENTS 3
        #define MAX_NR_HCI_CONNECTIONS 3
        I am not sure I needed to change the number of GATT clients; I am not sure what that parameter means.
        THese are located in /extmod/btstack/btstack_config_common.h in the MP distribution.

--HOWEVER--

Don't forget to build for Pico W specifically:

        Why so complicated? I use make -j 16 BOARD=PICO_W inside the port directory of rp2 and esp32.
        Sometimes make submodules is required, to get the new dependencies.

        If the current working directory is micropython, then you can also use make from there:

        make -C mpy-cross/ -j 16
        make -C ports/rp2 BOARD=RPI_PICO_W clean
        make -C ports/rp2 BOARD=RPI_PICO_W submodules
        make -C ports/rp2 BOARD=RPI_PICO_W -j 16

        Then ports/rp2/build-RPI_PICO_W is created. There you can find the firmware.uf2



Those changes must be made and then the firmware file must be built from source (though best use commands above):

Link = https://datasheets.raspberrypi.com/pico/raspberry-pi-pico-python-sdk.pdf

Instructions found in Chapter 1.3

