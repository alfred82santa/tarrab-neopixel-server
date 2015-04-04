from tns.sectors import Sector, BaseStackAnimation, BounceLightnessAnimation, DecreaseLightnessAnimation, \
    BounceSnakeAnimation, SequenceAnimation, StaticAnimation, SectorManager

__author__ = 'alfred'


class SuccessAnimation(BaseStackAnimation):

    def __init__(self, *args, **kwargs):
        super(SuccessAnimation, self).__init__(*args, **kwargs)

        self.stack = {0: BounceLightnessAnimation(sector=self.sector,
                                                  color=self.color,
                                                  bounce_steps=10,
                                                  increment=10),
                      20: DecreaseLightnessAnimation(sector=self.sector,
                                                     color=self.color,
                                                     increment=4.2)}

        self._recalculate_max_steps()


class ReadAnimation(BaseStackAnimation):

    def __init__(self, *args, **kwargs):
        super(ReadAnimation, self).__init__(*args, **kwargs)
        self.stack = {0: BounceSnakeAnimation(sector=self.sector,
                                              color=self.color),
                      120: DecreaseLightnessAnimation(sector=self.sector,
                                                      color=self.color,
                                                      increment=4.2)}
        self._recalculate_max_steps()


class ErrorAnimation(BaseStackAnimation):

    def __init__(self, *args, **kwargs):
        super(ErrorAnimation, self).__init__(*args, **kwargs)
        self.stack = {0: SequenceAnimation(sector=self.sector,
                                           color=self.color,
                                           pattern=('880000', '160000', '080000', '160000', '880000', 1)),
                      60: BounceLightnessAnimation(sector=self.sector,
                                                   color=self.color),
                      120: DecreaseLightnessAnimation(sector=self.sector,
                                                      color=self.color,
                                                      increment=4.2)}
        self._recalculate_max_steps()


class TarrabSector(Sector):

    STATUS_NOOP = 'noop'
    STATUS_READ = 'read'
    STATUS_SUCCESS = 'success'
    STATUS_ERROR = 'error'

    def __init__(self, *args, **kwargs):
        super(TarrabSector, self).__init__(*args, **kwargs)
        self.status = self.STATUS_NOOP
        self.refresh_animation()

    def set_status(self, status):
        self.status = status
        self.refresh_animation()

    def refresh_animation(self):
        if self.status == self.STATUS_NOOP:
            self.animation = StaticAnimation(sector=self,
                                             color='000000')
        elif self.status == self.STATUS_READ:
            self.animation = ReadAnimation(sector=self,
                                           color='0000FF')
        elif self.status == self.STATUS_SUCCESS:
            self.animation = SuccessAnimation(sector=self,
                                              color='00FF00')
        elif self.status == self.STATUS_ERROR:
            self.animation = ErrorAnimation(sector=self,
                                            color='FF0000')
        else:
            self.set_status(self.STATUS_NOOP)


class TarrabSectorManager(SectorManager):

    sector_cls = TarrabSector

    def set_status_by_name(self, name, status):
        for sector in self.get_sectors_by_name(name):
            sector.set_status(status)
