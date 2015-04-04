import json
from aiohttp import web
import asyncio
from tns.tarrab import TarrabSector

__author__ = 'alfred'


class TarrabApplication:

    def __init__(self, sector_manager, *args, **kwargs):
        self.server = web.Application(*args, **kwargs)
        self.server.router.add_route('POST', '/', self.default_handler)
        self.sector_manager = sector_manager

    @asyncio.coroutine
    def default_handler(self, request):
        data = yield from request.json()
        sector = data.get('sector')
        if sector:
            status = data.get('status', TarrabSector.STATUS_NOOP)
            self.sector_manager.set_status_by_name(sector, status)

        return web.Response(text=json.dumps({'ok': True}),
                            content_type='application/json',
                            status=202)
