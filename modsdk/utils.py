#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from ctypes import *
import os

# ------------------------------------------------------------------------------------------------------------
# Convert a ctypes c_char_p into a python string

def charPtrToString(charPtr):
    if not charPtr:
        return ""
    if isinstance(charPtr, str):
        return charPtr
    return charPtr.decode("utf-8", errors="ignore")

# ------------------------------------------------------------------------------------------------------------
# Convert a ctypes POINTER(c_char_p) into a python string list

def charPtrPtrToStringList(charPtrPtr):
    if not charPtrPtr:
        return []

    i       = 0
    charPtr = charPtrPtr[0]
    strList = []

    while charPtr:
        strList.append(charPtr.decode("utf-8", errors="ignore"))

        i += 1
        charPtr = charPtrPtr[i]

    return strList

# ------------------------------------------------------------------------------------------------------------
# Convert a ctypes POINTER(c_<num>) into a python number list

def numPtrToList(numPtr):
    if not numPtr:
        return []

    i       = 0
    num     = numPtr[0] #.value
    numList = []

    while num not in (0, 0.0):
        numList.append(num)

        i += 1
        num = numPtr[i] #.value

    return numList

# ------------------------------------------------------------------------------------------------------------

def structPtrToList(structPtr):
    if not structPtr:
        return []

    i      = 0
    ret    = []
    struct = structPtr[0]

    while struct.valid:
        ret.append(structToDict(struct))

        i     += 1
        struct = structPtr[i]

    return ret

def structPtrPtrToList(structPtr):
    if not structPtr:
        return []

    i      = 0
    ret    = []
    struct = structPtr[0]

    while struct:
        ret.append(structToDict(struct.contents))

        i     += 1
        struct = structPtr[i]

    return ret

# ------------------------------------------------------------------------------------------------------------
# Convert a ctypes value into a python one

c_int_types      = (c_int, c_int8, c_int16, c_int32, c_int64, c_uint, c_uint8, c_uint16, c_uint32, c_uint64, c_long, c_longlong)
c_float_types    = (c_float, c_double, c_longdouble)
c_intp_types     = tuple(POINTER(i) for i in c_int_types)
c_floatp_types   = tuple(POINTER(i) for i in c_float_types)
c_struct_types   = () # redefined below
c_structp_types  = () # redefined below
c_structpp_types = () # redefined below

def toPythonType(value, attr):
    #if value is None:
        #return ""
    if isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, bytes):
        return charPtrToString(value)
    if isinstance(value, c_intp_types) or isinstance(value, c_floatp_types):
        return numPtrToList(value)
    if isinstance(value, POINTER(c_char_p)):
        return charPtrPtrToStringList(value)
    if isinstance(value, c_struct_types):
        return structToDict(value)
    if isinstance(value, c_structp_types):
        return structPtrToList(value)
    if isinstance(value, c_structpp_types):
        return structPtrPtrToList(value)
    print("..............", attr, ".....................", value, ":", type(value))
    return value

# ------------------------------------------------------------------------------------------------------------
# Convert a ctypes struct into a python dict

def structToDict(struct):
    return dict((attr, toPythonType(getattr(struct, attr), attr)) for attr, value in struct._fields_)

# ------------------------------------------------------------------------------------------------------------

tryPath1 = os.path.join(os.path.dirname(__file__), "libmod_utils.so")
tryPath2 = os.path.join(os.path.dirname(__file__), "..", "utils", "libmod_utils.so")

if os.path.exists(tryPath1):
    utils = cdll.LoadLibrary(tryPath1)
else:
    utils = cdll.LoadLibrary(tryPath2)

class PluginAuthor(Structure):
    _fields_ = [
        ("name", c_char_p),
        ("homepage", c_char_p),
        ("email", c_char_p),
    ]

class PluginGUIPort(Structure):
    _fields_ = [
        ("valid", c_bool),
        ("index", c_uint),
        ("name", c_char_p),
        ("symbol", c_char_p),
    ]

class PluginGUI(Structure):
    _fields_ = [
        ("resourcesDirectory", c_char_p),
        ("iconTemplate", c_char_p),
        ("settingsTemplate", c_char_p),
        ("javascript", c_char_p),
        ("stylesheet", c_char_p),
        ("screenshot", c_char_p),
        ("thumbnail", c_char_p),
        ("brand", c_char_p),
        ("label", c_char_p),
        ("model", c_char_p),
        ("panel", c_char_p),
        ("color", c_char_p),
        ("knob", c_char_p),
        ("ports", POINTER(PluginGUIPort)),
        ("modificableInPlace", c_bool),
        ("usingSeeAlso", c_bool),
    ]

class PluginPortRanges(Structure):
    _fields_ = [
        ("minimum", c_float),
        ("maximum", c_float),
        ("default", c_float),
    ]

class PluginPortUnits(Structure):
    _fields_ = [
        ("label", c_char_p),
        ("render", c_char_p),
        ("symbol", c_char_p),
        ("_custom", c_bool),
    ]

class PluginPortScalePoint(Structure):
    _fields_ = [
        ("valid", c_bool),
        ("value", c_float),
        ("label", c_char_p),
    ]

class PluginPort(Structure):
    _fields_ = [
        ("valid", c_bool),
        ("index", c_uint),
        ("name", c_char_p),
        ("symbol", c_char_p),
        ("ranges", PluginPortRanges),
        ("units", PluginPortUnits),
        ("comment", c_char_p),
        ("designation", c_char_p),
        ("properties", POINTER(c_char_p)),
        ("rangeSteps", c_int),
        ("scalePoints", POINTER(PluginPortScalePoint)),
        ("shortName", c_char_p),
    ]

class PluginPortsI(Structure):
    _fields_ = [
        ("input", POINTER(PluginPort)),
        ("output", POINTER(PluginPort)),
    ]

class PluginPorts(Structure):
    _fields_ = [
        ("audio", PluginPortsI),
        ("control", PluginPortsI),
        ("cv", PluginPortsI),
        ("midi", PluginPortsI),
    ]

class PluginPreset(Structure):
    _fields_ = [
        ("valid", c_bool),
        ("uri", c_char_p),
        ("label", c_char_p),
    ]

class PluginInfo(Structure):
    _fields_ = [
        ("valid", c_bool),
        ("uri", c_char_p),
        ("name", c_char_p),
        ("binary", c_char_p),
        ("brand", c_char_p),
        ("label", c_char_p),
        ("license", c_char_p),
        ("comment", c_char_p),
        ("category", POINTER(c_char_p)),
        ("microVersion", c_int),
        ("minorVersion", c_int),
        ("version", c_char_p),
        ("stability", c_char_p),
        ("author", PluginAuthor),
        ("bundles", POINTER(c_char_p)),
        ("gui", PluginGUI),
        ("ports", PluginPorts),
        ("presets", POINTER(PluginPreset)),
    ]

c_struct_types = (PluginAuthor,
                  PluginGUI,
                  PluginPortRanges,
                  PluginPortUnits,
                  PluginPortsI,
                  PluginPorts)

c_structp_types = (POINTER(PluginGUIPort),
                   POINTER(PluginPortScalePoint),
                   POINTER(PluginPort),
                   POINTER(PluginPreset))

c_structpp_types = (POINTER(POINTER(PluginInfo)),)

utils.init.argtypes = None
utils.init.restype  = None

utils.cleanup.argtypes = None
utils.cleanup.restype  = None

utils.get_all_bundles.argtypes = None
utils.get_all_bundles.restype  = POINTER(c_char_p)

utils.get_bundle_plugins.argtypes = [c_char_p]
utils.get_bundle_plugins.restype  = POINTER(POINTER(PluginInfo))

utils.get_plugin_info.argtypes = [c_char_p]
utils.get_plugin_info.restype  = POINTER(PluginInfo)

# ------------------------------------------------------------------------------------------------------------

# initialize
def init():
    utils.init()

# cleanup, cannot be used afterwards
def cleanup():
    utils.cleanup()

# ------------------------------------------------------------------------------------------------------------

# get all available plugin bundles
def get_all_bundles():
    return charPtrPtrToStringList(utils.get_all_bundles())

# get all available plugins in a bundle
def get_bundle_plugins(bundle):
    return structPtrPtrToList(utils.get_bundle_plugins(bundle.encode("utf-8")))

# get a specific plugin
# NOTE: may throw
def get_plugin_info(uri):
    info = utils.get_plugin_info(uri.encode("utf-8"))
    if not info:
        raise Exception
    return structToDict(info.contents)

# ------------------------------------------------------------------------------------------------------------
