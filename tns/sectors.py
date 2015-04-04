from colorsys import rgb_to_hls, hls_to_rgb
import asyncio
import collections
import weakref

__author__ = 'alfred'


class BaseAnimation:

    max_step_cycle = 0
    default_step_stop = -1

    def __init__(self, sector, color='000000', step_stop=None):
        self._sector = weakref.ref(sector)
        self.color = color
        self.step = 0
        self.active = True
        self.step_stop = step_stop if step_stop is not None else self.default_step_stop

    @property
    def sector(self):
        return self._sector()

    def paint(self):
        pass

    def get_color_by_step(self, step):
        return self.color

    def clear(self):
        self.sector.controller.set_sector_color(self.sector.pixel,
                                                self.sector.length,
                                                '000000')

    def draw_line(self, pixel, length, color):
        if pixel < self.sector.pixel:
            pixel = self.sector.pixel
        elif pixel > self.sector.pixel + self.sector.length:
            return
        if pixel + length > self.sector.pixel + self.sector.length:
            length = self.sector.pixel + self.sector.length - pixel

        self.sector.controller.set_sector_color(pixel, length, color)

    def draw_sequence(self, pixel, colors):
        if pixel < self.sector.pixel:
            colors = colors[len(colors) - (self.sector.pixel - pixel):]
            pixel = self.sector.pixel
        elif pixel > self.sector.pixel + self.sector.length:
            return

        if pixel + len(colors) > self.sector.pixel + self.sector.length:
            colors = colors[:(self.sector.pixel + self.sector.length - pixel)]

        aux = []
        while len(colors):
            aux.append(colors.pop(0))
            if len(aux) == 8:
                self.sector.controller.set_8_pixels_color(pixel, aux)
                aux = []
                pixel += 8

        if len(aux):
            for color in aux:
                self.sector.controller.set_pixel_color(pixel, color)
                pixel += 1

    def lightness_color(self, color, increment):
        hls_color = rgb_to_hls(int("0x" + color[:2], 0),
                               int("0x" + color[2:4], 0),
                               int("0x" + color[-2:], 0))

        lightness = hls_color[1] + increment
        if lightness > 127:
            lightness = 127
        elif lightness < 0:
            lightness = 0

        color = hls_to_rgb(hls_color[0],
                           lightness,
                           hls_color[2])

        return "".join(["{:02X}".format(int(cr)) for cr in color])

    def next_step(self):
        if not self.active:
            return
        self.paint()
        self.step += 1

        if self.step > self.step_stop >= 0:
            self.active = False
        if self.step > self.max_step_cycle:
            self.step = 0


class StaticAnimation(BaseAnimation):

    default_step_stop = 0

    def paint(self):
        self.sector.controller.set_sector_color(self.sector.pixel,
                                                self.sector.length,
                                                self.get_color_by_step(self.step))


class BaseLightnessAnimationMixin:

    default_step_stop = 30

    def __init__(self, increment=4, *args, **kwargs):
        super(BaseLightnessAnimationMixin, self).__init__(*args, **kwargs)
        self.increment = increment
        self.max_step_cycle = self.step_stop + 1


class IncreaseAnimationMixin(BaseLightnessAnimationMixin):

    def get_color_by_step(self, step):
        return self.lightness_color(self.color, self.increment * step)


class DecreaseAnimationMixin(BaseLightnessAnimationMixin):

    def get_color_by_step(self, step):
        return self.lightness_color(self.color, -self.increment * step)


class BounceLightnessAnimationMixin(BaseLightnessAnimationMixin):

    default_step_stop = -1

    def __init__(self, bounce_steps=30, *args, **kwargs):
        super(BounceLightnessAnimationMixin, self).__init__(*args, **kwargs)
        self.bounce_steps = bounce_steps
        self.max_step_cycle = bounce_steps * 2

    def get_color_by_step(self, step):
        if step == self.bounce_steps:
            pass
        elif not step // self.bounce_steps:
            step %= self.bounce_steps
        else:
            step %= -self.bounce_steps
            step *= -1
        return self.lightness_color(self.color, -self.increment * step)


class DecreaseLightnessAnimation(DecreaseAnimationMixin, StaticAnimation):
    pass


class IncreaseLightnessAnimation(IncreaseAnimationMixin, StaticAnimation):
    pass


class BounceLightnessAnimation(BounceLightnessAnimationMixin, StaticAnimation):
    pass


class SequenceAnimation(BaseAnimation):

    def __init__(self, pattern=(0, 1), speed=1, *args, **kwargs):
        super(SequenceAnimation, self).__init__(*args, **kwargs)
        self.pattern = pattern
        self.speed = speed
        self.max_step_cycle = len(self.pattern) * self.speed

    def get_sequence(self, step, length):
        pattern = collections.deque(self.pattern)
        pattern.rotate(step)
        return self.generate_sequence(pattern, length)

    def generate_sequence(self, pattern, length):

        def get_color(pattern_item):
            if pattern_item == 0:
                return '000000'
            elif isinstance(pattern_item, str):
                return pattern_item
            else:
                return self.color
        return [get_color(pattern[i % len(pattern)]) for i in range(length)]

    def paint(self):
        if self.step % self.speed:
            return
        step = (self.step // self.speed) % len(self.pattern)
        self.draw_sequence(self.sector.pixel, self.get_sequence(step, self.sector.length))


class BounceSnakeAnimation(BaseAnimation):

    def __init__(self, snake_size=8, speed=1, *args, **kwargs):
        super(BounceSnakeAnimation, self).__init__(*args, **kwargs)
        self.snake_size = snake_size
        self.speed = speed
        self.max_pixel = self.sector.length - self.snake_size
        self.max_step_cycle = self.speed * self.max_pixel * 2

    def paint(self):
        if self.step % self.speed:
            return
        self.clear()
        step = self.step // self.speed
        if step > self.max_pixel:
            step = 2 * self.max_pixel - step
        self.draw_line(pixel=self.sector.pixel + step,
                       length=self.snake_size,
                       color=self.get_color_by_step(self.step))


class BounceSnakeAndLightnessAnimation(BounceLightnessAnimationMixin, BounceSnakeAnimation):
    pass


class BaseStackAnimation(BaseAnimation):

    def _recalculate_max_steps(self):
        self.step_stop = max(self.stack.keys())
        self.max_step_cycle = self.step_stop + 1

    def paint(self):
        animation = self.stack[max([step for step in self.stack.keys()
                                    if step <= self.step])]
        animation.next_step()

    def next_step(self):
        self.paint()

        if not self.active:
            return

        self.step += 1

        if self.step > self.max_step_cycle:
            self.step = 0
        if self.step > self.step_stop >= 0:
            self.active = False


class Sector:

    def __init__(self, name, pixel, length, controller):
        self.name = name
        self.animation = None
        self.pixel = pixel
        self.length = length
        self.controller = controller


class SectorManager:

    sector_cls = Sector

    def __init__(self, controller, refresh=0.03, loop=asyncio.get_event_loop()):
        self.controller = controller
        self.refresh = refresh
        self.sectors = []
        asyncio.async(self.clock(), loop=loop)

    @asyncio.coroutine
    def clock(self):
        while True:
            yield from asyncio.sleep(self.refresh)
            for sector in self.sectors:
                sector.animation.next_step()

    def create_sector(self, name, pixel, length, *args, **kwargs):
        self.sectors.append(self.sector_cls(name, pixel, length, self.controller, *args, **kwargs))

    def get_sectors_by_name(self, name):
        return [sector for sector in self.sectors if sector.name == name]

    def set_animation(self, name, animation, **kwargs):
        for sector in self.get_sectors_by_name(name):
            sector.animation = animation(sector=sector, **kwargs)
            sector.animation.paint()
