#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
Stand-in for RPi.GPIO on a computer without the pins of a Raspberry (a PC with Linux, see
cplatform) : the same names, nothing done. No pin is configured there (see Craspberry), these
calls only keep the code of the Raspberry running without a test at each call
'''

BCM = 11
BOARD = 10
IN = 1
OUT = 0
HIGH = 1
LOW = 0
PUD_OFF = 20
PUD_DOWN = 21
PUD_UP = 22
RISING = 31
FALLING = 32
BOTH = 33


def setmode(*_args, **_kwargs):
    pass


def setwarnings(*_args, **_kwargs):
    pass


def setup(*_args, **_kwargs):
    pass


def output(*_args, **_kwargs):
    pass


def input(*_args, **_kwargs):    # pylint: disable=redefined-builtin
    return LOW


def cleanup(*_args, **_kwargs):
    pass


def add_event_detect(*_args, **_kwargs):
    pass


def remove_event_detect(*_args, **_kwargs):
    pass


def event_detected(*_args, **_kwargs):
    return False
