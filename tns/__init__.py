import asyncio
from .controllers import NeoPixelArduino
from .tarrab import TarrabSectorManager
from .tarrab.server import TarrabApplication

__author__ = 'alfred'


@asyncio.coroutine
def factory(config):

    controller = NeoPixelArduino(**config.get('arduino', {"port": "/dev/ttyACM0",
                                                          "baudrate": 115200}))

    sector_manager = TarrabSectorManager(controller=controller)

    for sector in config.get('sectors', []):
        sector_manager.create_sector(**sector)

    application = TarrabApplication(sector_manager)
    server_config = config.get('server')
    srv = yield from asyncio.get_event_loop().create_server(application.server.make_handler(),
                                                            server_config.get('host', "127.0.0.1"),
                                                            server_config.get('port', 8080))

    asyncio.async(controller.start_loop())

    return srv
