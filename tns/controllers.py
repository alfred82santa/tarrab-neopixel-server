import asyncio
import struct
import time

__author__ = 'alfred'
from serial import Serial, to_bytes


class NeoPixelArduino:

    ACTION_SET_PIXEL_COLOR = 1
    ACTION_SET_SECTOR_COLOR = 2
    ACTION_SHOW = 3
    ACTION_CONFIG_STRIP = 4
    ACTION_SET_8_PIXELS_COLOR = 5

    def __init__(self, num_leds=180, refresh_ms=0.01, loop=None, *args, **kwargs):
        self.serial_port = Serial(*args, **kwargs)
        self.stack = []
        if loop:
            self.loop = loop
        else:
            self.loop = asyncio.get_event_loop()
        self.num_leds = num_leds
        self.refresh_ms = refresh_ms
        self.reconfigure_leds(num_leds)

    def reconfigure_leds(self, num_leds):
        self.num_leds = num_leds
        self.stack.append(self.create_reconfigure_leds_command(self.num_leds))

    def create_reconfigure_leds_command(self, num_leds):
        comm = [self.ACTION_CONFIG_STRIP]
        add_16_bits_param(comm, num_leds)
        return to_bytes(comm)

    def set_pixel_color(self, pixel, color):
        self.stack.append(self.create_set_pixel_color_command(pixel, color))

    def create_set_pixel_color_command(self, pixel, color):
        comm = [self.ACTION_SET_PIXEL_COLOR]
        add_16_bits_param(comm, pixel)
        add_color_param(comm, color)
        return to_bytes(comm)

    def set_sector_color(self, pixel, length, color):
        self.stack.append(self.create_set_sector_color_command(pixel, length, color))

    def create_set_sector_color_command(self, pixel, length, color):
        comm = [self.ACTION_SET_SECTOR_COLOR]
        add_16_bits_param(comm, pixel)
        add_16_bits_param(comm, length)
        add_color_param(comm, color)
        return to_bytes(comm)

    def show(self):
        self.stack.append(self.create_show_command())

    def create_show_command(self):
        return to_bytes([self.ACTION_SHOW])

    def set_8_pixels_color(self, pixel, colors):
        self.stack.append(self.create_set_8_pixels_color_command(pixel, colors))

    def create_set_8_pixels_color_command(self, pixel, colors):
        comm = [self.ACTION_SET_8_PIXELS_COLOR]
        add_16_bits_param(comm, pixel)
        for color in colors:
            add_color_param(comm, color)
        return to_bytes(comm)

    def process_command_stack(self):
        run = True
        used = False
        while run:
            try:
                comm = self.stack.pop(0)
                used = True
                self.send_command(comm)

            except IndexError:
                run = False
        if used:
            self.send_command(self.create_show_command())

    def send_command(self, comm):
        self.serial_port.flushInput()
        # self.serial_port.flushOutput()
        t1 = time.time()
        # print('Command start time: {0}'.format(t1))
        self.serial_port.write(comm)
        t2 = time.time()
        ela = t2 - t1
        if ela > 0.001:
            print('Command elapsed time: {0}. Command {1}'.format(ela, comm))
        # res = self.serial_port.read(1)
        # t3 = time.time()
        # print('Command response elapsed time: {0}'.format(t3 - t2))
        # if res != b'A':
        #    raise Exception('Wow, arduino returned "{0}"'.format(res))
        # print('Check response elapsed time: {0}'.format(time.time() - t3))
        # print('Command elapsed time total: {0}'.format(time.time() - t1))

    @asyncio.coroutine
    def start_loop(self):
        while True:
            yield from asyncio.sleep(self.refresh_ms, loop=self.loop)
            self.process_command_stack()


def add_16_bits_param(comm, param):
    data = bytearray(struct.pack(">H", param))
    comm.append(data[0])
    comm.append(data[1])


def add_color_param(comm, color):
    comm.append(int("0x" + color[:2], 0))
    comm.append(int("0x" + color[2:4], 0))
    comm.append(int("0x" + color[-2:], 0))
