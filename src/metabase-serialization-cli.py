#!/usr/bin/env python
import logging

import fire

import metabase_serialization_py as msp


LOGGER = logging.getLogger(__name__)
logging.basicConfig(encoding='utf-8', level=logging.DEBUG)


if __name__ == '__main__':
    fire.Fire(msp.cli)
