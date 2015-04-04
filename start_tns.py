#! /usr/bin/python3

import asyncio
import yaml
from os import path
from tns import factory


CONFIG_FILE = path.join(path.dirname(path.abspath(__file__)),
                        'conf', 'config.yaml')

if __name__ == '__main__':
    try:
        with open(CONFIG_FILE, 'r') as stream:
            config = yaml.load(stream)
        srv = asyncio.get_event_loop().run_until_complete(factory(config))
        asyncio.get_event_loop().run_forever()
    except Exception as ex:
        print(ex)
