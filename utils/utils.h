/*
 * MOD-SDK fast-lilv
 * Copyright (C) 2015-2016 Filipe Coelho <falktx@falktx.com>
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License as
 * published by the Free Software Foundation; either version 2 of
 * the License, or any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU General Public License for more details.
 *
 * For a full copy of the GNU General Public License see the COPYING file.
 */

#ifndef MOD_SDK_FAST_LILV_H_INCLUDED
#define MOD_SDK_FAST_LILV_H_INCLUDED

#ifdef __cplusplus
#include <cstdint>
extern "C" {
#else
#include <stdint.h>
#endif

#define MOD_API __attribute__ ((visibility("default")))

typedef struct {
    const char* name;
    const char* homepage;
    const char* email;
} PluginAuthor;

typedef struct {
    bool valid;
    unsigned int index;
    const char* name;
    const char* symbol;
} PluginGUIPort;

typedef struct {
    const char* resourcesDirectory;
    const char* iconTemplate;
    const char* settingsTemplate;
    const char* javascript;
    const char* stylesheet;
    const char* screenshot;
    const char* thumbnail;
    const char* brand;
    const char* label;
    const char* model;
    const char* panel;
    const char* color;
    const char* knob;
    PluginGUIPort* ports;
    bool modificableInPlace;
    bool usingSeeAlso;
} PluginGUI;

typedef struct {
    const char* screenshot;
    const char* thumbnail;
} PluginGUI_Mini;

typedef struct {
    float min;
    float max;
    float def;
} PluginPortRanges;

typedef struct {
    const char* label;
    const char* render;
    const char* symbol;
    bool _custom;
} PluginPortUnits;

typedef struct {
    bool valid;
    float value;
    const char* label;
} PluginPortScalePoint;

typedef struct {
    bool valid;
    unsigned int index;
    const char* name;
    const char* symbol;
    PluginPortRanges ranges;
    PluginPortUnits units;
    const char* designation;
    const char* const* properties;
    int rangeSteps;
    const PluginPortScalePoint* scalePoints;
    const char* shortName;
} PluginPort;

typedef struct {
    PluginPort* input;
    PluginPort* output;
} PluginPortsI;

typedef struct {
    PluginPortsI audio;
    PluginPortsI control;
    PluginPortsI cv;
    PluginPortsI midi;
} PluginPorts;

typedef struct {
    bool valid;
    const char* uri;
    const char* label;
} PluginPreset;

typedef struct {
    bool valid;
    const char* uri;
    const char* name;
    const char* binary;
    const char* brand;
    const char* label;
    const char* license;
    const char* comment;
    const char* const* category;
    int microVersion;
    int minorVersion;
    int release;
    int builder;
    const char* version;
    const char* stability;
    PluginAuthor author;
    const char* const* bundles;
    PluginGUI gui;
    PluginPorts ports;
    const PluginPreset* presets;
} PluginInfo;

// initialize
MOD_API void init(void);

// cleanup, cannot be used afterwards
MOD_API void cleanup(void);

// get all available plugin bundles
MOD_API const char* const* get_all_bundles(void);

// get all available plugins in a bundle
MOD_API const PluginInfo* const* get_bundle_plugins(const char* bundle);

// get a specific plugin
MOD_API const PluginInfo* get_plugin_info(const char* uri);

#ifdef __cplusplus
} // extern "C"
#endif

#endif // MOD_UTILS_H_INCLUDED
