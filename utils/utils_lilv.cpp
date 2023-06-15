/*
 * MOD-SDK utilities
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

#include "utils.h"

#include <libgen.h>
#include <limits.h>
#include <stdlib.h>
#include <string.h>

#include <lilv/lilv.h>

#include <lv2/core/lv2.h>
#include <lv2/atom/atom.h>
#include <lv2/midi/midi.h>
#include <lv2/port-props/port-props.h>
#include <lv2/presets/presets.h>
#include <lv2/units/units.h>

#include <algorithm>
#include <cassert>
#include <fstream>
#include <list>
#include <map>
#include <string>
#include <vector>

#define OS_SEP     '/'
#define OS_SEP_STR "/"

#ifndef HAVE_NEW_LILV
#warning Your current lilv version is too old, please update it
char* lilv_file_uri_parse2(const char* uri, const char*)
{
    if (const char* const parsed = lilv_uri_to_path(uri))
        return strdup(parsed);
    return nullptr;
}
#define lilv_free(x) free(x)
#define lilv_file_uri_parse(x,y) lilv_file_uri_parse2(x,y)
#endif

namespace std {
typedef list<string> stringlist;
}

// our lilv world
LilvWorld* W = nullptr;

// list of loaded bundles
std::stringlist BUNDLES;

// plugin info, mapped to URIs
std::map<std::string, PluginInfo> PLUGNFO;

// bundle mapped to list of plugins (URIs)
std::map<std::string, std::stringlist> BUNDLED_PLUGINS;

// some other cached values
static const char* const HOME = getenv("HOME");
static size_t HOMElen = strlen(HOME);

#define PluginInfo_Init {                            \
    false,                                           \
    nullptr, nullptr,                                \
    nullptr, nullptr, nullptr, nullptr, nullptr,     \
    nullptr, 0, 0,                                   \
    nullptr, nullptr,                                \
    { nullptr, nullptr, nullptr },                   \
    nullptr,                                         \
    {                                                \
        nullptr, nullptr, nullptr, nullptr, nullptr, \
        nullptr, nullptr,                            \
        nullptr, nullptr,                            \
        nullptr, nullptr, nullptr, nullptr,          \
        nullptr,                                     \
        false, false                                 \
    },                                               \
    {                                                \
        { nullptr, nullptr },                        \
        { nullptr, nullptr },                        \
        { nullptr, nullptr },                        \
        { nullptr, nullptr }                         \
    },                                               \
    nullptr                                          \
}

// --------------------------------------------------------------------------------------------------------

inline bool ends_with(const std::string& value, const std::string ending)
{
    if (ending.size() > value.size())
        return false;
    return std::equal(ending.rbegin(), ending.rend(), value.rbegin());
}

// --------------------------------------------------------------------------------------------------------

#define LILV_NS_INGEN    "http://drobilla.net/ns/ingen#"
#define LILV_NS_MOD      "http://moddevices.com/ns/mod#"
#define LILV_NS_MODGUI   "http://moddevices.com/ns/modgui#"
#define LILV_NS_MODPEDAL "http://moddevices.com/ns/modpedal#"

struct NamespaceDefinitions {
    LilvNode* const doap_license;
    LilvNode* const doap_maintainer;
    LilvNode* const foaf_homepage;
    LilvNode* const rdf_type;
    LilvNode* const rdfs_comment;
    LilvNode* const rdfs_label;
    LilvNode* const lv2core_designation;
    LilvNode* const lv2core_index;
    LilvNode* const lv2core_microVersion;
    LilvNode* const lv2core_minorVersion;
    LilvNode* const lv2core_name;
    LilvNode* const lv2core_project;
    LilvNode* const lv2core_portProperty;
    LilvNode* const lv2core_shortName;
    LilvNode* const lv2core_symbol;
    LilvNode* const lv2core_default;
    LilvNode* const lv2core_minimum;
    LilvNode* const lv2core_maximum;
    LilvNode* const mod_brand;
    LilvNode* const mod_label;
    LilvNode* const mod_default;
    LilvNode* const mod_minimum;
    LilvNode* const mod_maximum;
    LilvNode* const mod_rangeSteps;
    LilvNode* const modgui_gui;
    LilvNode* const modgui_resourcesDirectory;
    LilvNode* const modgui_iconTemplate;
    LilvNode* const modgui_settingsTemplate;
    LilvNode* const modgui_javascript;
    LilvNode* const modgui_stylesheet;
    LilvNode* const modgui_screenshot;
    LilvNode* const modgui_thumbnail;
    LilvNode* const modgui_brand;
    LilvNode* const modgui_label;
    LilvNode* const modgui_model;
    LilvNode* const modgui_panel;
    LilvNode* const modgui_color;
    LilvNode* const modgui_knob;
    LilvNode* const modgui_port;
    LilvNode* const atom_bufferType;
    LilvNode* const atom_Sequence;
    LilvNode* const midi_MidiEvent;
    LilvNode* const pprops_rangeSteps;
    LilvNode* const pset_Preset;
    LilvNode* const units_render;
    LilvNode* const units_symbol;
    LilvNode* const units_unit;

    NamespaceDefinitions()
        : doap_license             (lilv_new_uri(W, LILV_NS_DOAP   "license"           )),
          doap_maintainer          (lilv_new_uri(W, LILV_NS_DOAP   "maintainer"        )),
          foaf_homepage            (lilv_new_uri(W, LILV_NS_FOAF   "homepage"          )),
          rdf_type                 (lilv_new_uri(W, LILV_NS_RDF    "type"              )),
          rdfs_comment             (lilv_new_uri(W, LILV_NS_RDFS   "comment"           )),
          rdfs_label               (lilv_new_uri(W, LILV_NS_RDFS   "label"             )),
          lv2core_designation      (lilv_new_uri(W, LILV_NS_LV2    "designation"       )),
          lv2core_index            (lilv_new_uri(W, LILV_NS_LV2    "index"             )),
          lv2core_microVersion     (lilv_new_uri(W, LILV_NS_LV2    "microVersion"      )),
          lv2core_minorVersion     (lilv_new_uri(W, LILV_NS_LV2    "minorVersion"      )),
          lv2core_name             (lilv_new_uri(W, LILV_NS_LV2    "name"              )),
          lv2core_project          (lilv_new_uri(W, LILV_NS_LV2    "project"           )),
          lv2core_portProperty     (lilv_new_uri(W, LILV_NS_LV2    "portProperty"      )),
          lv2core_shortName        (lilv_new_uri(W, LILV_NS_LV2    "shortName"         )),
          lv2core_symbol           (lilv_new_uri(W, LILV_NS_LV2    "symbol"            )),
          lv2core_default          (lilv_new_uri(W, LILV_NS_LV2    "default"           )),
          lv2core_minimum          (lilv_new_uri(W, LILV_NS_LV2    "minimum"           )),
          lv2core_maximum          (lilv_new_uri(W, LILV_NS_LV2    "maximum"           )),
          mod_brand                (lilv_new_uri(W, LILV_NS_MOD    "brand"             )),
          mod_label                (lilv_new_uri(W, LILV_NS_MOD    "label"             )),
          mod_default              (lilv_new_uri(W, LILV_NS_MOD    "default"           )),
          mod_minimum              (lilv_new_uri(W, LILV_NS_MOD    "minimum"           )),
          mod_maximum              (lilv_new_uri(W, LILV_NS_MOD    "maximum"           )),
          mod_rangeSteps           (lilv_new_uri(W, LILV_NS_MOD    "rangeSteps"        )),
          modgui_gui               (lilv_new_uri(W, LILV_NS_MODGUI "gui"               )),
          modgui_resourcesDirectory(lilv_new_uri(W, LILV_NS_MODGUI "resourcesDirectory")),
          modgui_iconTemplate      (lilv_new_uri(W, LILV_NS_MODGUI "iconTemplate"      )),
          modgui_settingsTemplate  (lilv_new_uri(W, LILV_NS_MODGUI "settingsTemplate"  )),
          modgui_javascript        (lilv_new_uri(W, LILV_NS_MODGUI "javascript"        )),
          modgui_stylesheet        (lilv_new_uri(W, LILV_NS_MODGUI "stylesheet"        )),
          modgui_screenshot        (lilv_new_uri(W, LILV_NS_MODGUI "screenshot"        )),
          modgui_thumbnail         (lilv_new_uri(W, LILV_NS_MODGUI "thumbnail"         )),
          modgui_brand             (lilv_new_uri(W, LILV_NS_MODGUI "brand"             )),
          modgui_label             (lilv_new_uri(W, LILV_NS_MODGUI "label"             )),
          modgui_model             (lilv_new_uri(W, LILV_NS_MODGUI "model"             )),
          modgui_panel             (lilv_new_uri(W, LILV_NS_MODGUI "panel"             )),
          modgui_color             (lilv_new_uri(W, LILV_NS_MODGUI "color"             )),
          modgui_knob              (lilv_new_uri(W, LILV_NS_MODGUI "knob"              )),
          modgui_port              (lilv_new_uri(W, LILV_NS_MODGUI "port"              )),
          atom_bufferType          (lilv_new_uri(W, LV2_ATOM__bufferType               )),
          atom_Sequence            (lilv_new_uri(W, LV2_ATOM__Sequence                 )),
          midi_MidiEvent           (lilv_new_uri(W, LV2_MIDI__MidiEvent                )),
          pprops_rangeSteps        (lilv_new_uri(W, LV2_PORT_PROPS__rangeSteps         )),
          pset_Preset              (lilv_new_uri(W, LV2_PRESETS__Preset                )),
          units_render             (lilv_new_uri(W, LV2_UNITS__render                  )),
          units_symbol             (lilv_new_uri(W, LV2_UNITS__symbol                  )),
          units_unit               (lilv_new_uri(W, LV2_UNITS__unit                    )) {}

    ~NamespaceDefinitions()
    {
        lilv_node_free(doap_license);
        lilv_node_free(doap_maintainer);
        lilv_node_free(foaf_homepage);
        lilv_node_free(rdf_type);
        lilv_node_free(rdfs_comment);
        lilv_node_free(rdfs_label);
        lilv_node_free(lv2core_designation);
        lilv_node_free(lv2core_index);
        lilv_node_free(lv2core_microVersion);
        lilv_node_free(lv2core_minorVersion);
        lilv_node_free(lv2core_name);
        lilv_node_free(lv2core_project);
        lilv_node_free(lv2core_portProperty);
        lilv_node_free(lv2core_shortName);
        lilv_node_free(lv2core_symbol);
        lilv_node_free(lv2core_default);
        lilv_node_free(lv2core_minimum);
        lilv_node_free(lv2core_maximum);
        lilv_node_free(mod_brand);
        lilv_node_free(mod_label);
        lilv_node_free(mod_default);
        lilv_node_free(mod_minimum);
        lilv_node_free(mod_maximum);
        lilv_node_free(mod_rangeSteps);
        lilv_node_free(modgui_gui);
        lilv_node_free(modgui_resourcesDirectory);
        lilv_node_free(modgui_iconTemplate);
        lilv_node_free(modgui_settingsTemplate);
        lilv_node_free(modgui_javascript);
        lilv_node_free(modgui_stylesheet);
        lilv_node_free(modgui_screenshot);
        lilv_node_free(modgui_thumbnail);
        lilv_node_free(modgui_brand);
        lilv_node_free(modgui_label);
        lilv_node_free(modgui_model);
        lilv_node_free(modgui_panel);
        lilv_node_free(modgui_color);
        lilv_node_free(modgui_knob);
        lilv_node_free(modgui_port);
        lilv_node_free(atom_bufferType);
        lilv_node_free(atom_Sequence);
        lilv_node_free(midi_MidiEvent);
        lilv_node_free(pprops_rangeSteps);
        lilv_node_free(pset_Preset);
        lilv_node_free(units_render);
        lilv_node_free(units_symbol);
        lilv_node_free(units_unit);
    }
};

static const char* const kCategoryDelayPlugin[] = { "Delay", nullptr };
static const char* const kCategoryDistortionPlugin[] = { "Distortion", nullptr };
static const char* const kCategoryWaveshaperPlugin[] = { "Distortion", "Waveshaper", nullptr };
static const char* const kCategoryDynamicsPlugin[] = { "Dynamics", nullptr };
static const char* const kCategoryAmplifierPlugin[] = { "Dynamics", "Amplifier", nullptr };
static const char* const kCategoryCompressorPlugin[] = { "Dynamics", "Compressor", nullptr };
static const char* const kCategoryExpanderPlugin[] = { "Dynamics", "Expander", nullptr };
static const char* const kCategoryGatePlugin[] = { "Dynamics", "Gate", nullptr };
static const char* const kCategoryLimiterPlugin[] = { "Dynamics", "Limiter", nullptr };
static const char* const kCategoryFilterPlugin[] = { "Filter", nullptr };
static const char* const kCategoryAllpassPlugin[] = { "Filter", "Allpass", nullptr };
static const char* const kCategoryBandpassPlugin[] = { "Filter", "Bandpass", nullptr };
static const char* const kCategoryCombPlugin[] = { "Filter", "Comb", nullptr };
static const char* const kCategoryEQPlugin[] = { "Filter", "Equaliser", nullptr };
static const char* const kCategoryMultiEQPlugin[] = { "Filter", "Equaliser", "Multiband", nullptr };
static const char* const kCategoryParaEQPlugin[] = { "Filter", "Equaliser", "Parametric", nullptr };
static const char* const kCategoryHighpassPlugin[] = { "Filter", "Highpass", nullptr };
static const char* const kCategoryLowpassPlugin[] = { "Filter", "Lowpass", nullptr };
static const char* const kCategoryGeneratorPlugin[] = { "Generator", nullptr };
static const char* const kCategoryConstantPlugin[] = { "Generator", "Constant", nullptr };
static const char* const kCategoryInstrumentPlugin[] = { "Generator", "Instrument", nullptr };
static const char* const kCategoryOscillatorPlugin[] = { "Generator", "Oscillator", nullptr };
static const char* const kCategoryModulatorPlugin[] = { "Modulator", nullptr };
static const char* const kCategoryChorusPlugin[] = { "Modulator", "Chorus", nullptr };
static const char* const kCategoryFlangerPlugin[] = { "Modulator", "Flanger", nullptr };
static const char* const kCategoryPhaserPlugin[] = { "Modulator", "Phaser", nullptr };
static const char* const kCategoryReverbPlugin[] = { "Reverb", nullptr };
static const char* const kCategorySimulatorPlugin[] = { "Simulator", nullptr };
static const char* const kCategorySpatialPlugin[] = { "Spatial", nullptr };
static const char* const kCategorySpectralPlugin[] = { "Spectral", nullptr };
static const char* const kCategoryPitchPlugin[] = { "Spectral", "Pitch Shifter", nullptr };
static const char* const kCategoryUtilityPlugin[] = { "Utility", nullptr };
static const char* const kCategoryAnalyserPlugin[] = { "Utility", "Analyser", nullptr };
static const char* const kCategoryConverterPlugin[] = { "Utility", "Converter", nullptr };
static const char* const kCategoryFunctionPlugin[] = { "Utility", "Function", nullptr };
static const char* const kCategoryMixerPlugin[] = { "Utility", "Mixer", nullptr };

static const char* const kStabilityExperimental = "experimental";
static const char* const kStabilityStable = "stable";
static const char* const kStabilityTesting = "testing";

// label, render, symbol
static const char* const kUnit_s[] = { "seconds", "%f s", "s" };
static const char* const kUnit_ms[] = { "milliseconds", "%f ms", "ms" };
static const char* const kUnit_min[] = { "minutes", "%f mins", "min" };
static const char* const kUnit_bar[] = { "bars", "%f bars", "bars" };
static const char* const kUnit_beat[] = { "beats", "%f beats", "beats" };
static const char* const kUnit_frame[] = { "audio frames", "%f frames", "frames" };
static const char* const kUnit_m[] = { "metres", "%f m", "m" };
static const char* const kUnit_cm[] = { "centimetres", "%f cm", "cm" };
static const char* const kUnit_mm[] = { "millimetres", "%f mm", "mm" };
static const char* const kUnit_km[] = { "kilometres", "%f km", "km" };
static const char* const kUnit_inch[] = { "inches", """%f\"""", "in" };
static const char* const kUnit_mile[] = { "miles", "%f mi", "mi" };
static const char* const kUnit_db[] = { "decibels", "%f dB", "dB" };
static const char* const kUnit_pc[] = { "percent", "%f%%", "%" };
static const char* const kUnit_coef[] = { "coefficient", "* %f", "*" };
static const char* const kUnit_hz[] = { "hertz", "%f Hz", "Hz" };
static const char* const kUnit_khz[] = { "kilohertz", "%f kHz", "kHz" };
static const char* const kUnit_mhz[] = { "megahertz", "%f MHz", "MHz" };
static const char* const kUnit_bpm[] = { "beats per minute", "%f BPM", "BPM" };
static const char* const kUnit_oct[] = { "octaves", "%f octaves", "oct" };
static const char* const kUnit_cent[] = { "cents", "%f ct", "ct" };
static const char* const kUnit_semitone12TET[] = { "semitones", "%f semi", "semi" };
static const char* const kUnit_degree[] = { "degrees", "%f deg", "deg" };
static const char* const kUnit_midiNote[] = { "MIDI note", "MIDI note %d", "note" };

static const char nc[1] = { '\0' };

bool _isalnum(const char* const string)
{
    for (size_t i=0;; ++i)
    {
        if (string[i] == '\0')
            return (i != 0);
        if (! isalnum(string[i]))
            return false;
    }
}

void _swap_preset_data(PluginPreset* preset1, PluginPreset* preset2)
{
    std::swap(preset1->uri,   preset2->uri);
    std::swap(preset1->label, preset2->label);
}

// adjusted from https://stackoverflow.com/questions/19612152/quicksort-string-array-in-c
void _sort_presets_data(PluginPreset presets[], unsigned int count)
{
    if (count <= 1)
        return;

    unsigned int pvt = 0;

    // swap a randomly selected value to the last node
    _swap_preset_data(presets+(rand() % count), presets+(count-1));

    // reset the pivot index to zero, then scan
    for (unsigned int i=0; i<count-1; ++i)
    {
        if (strcmp(presets[i].uri, presets[count-1].uri) < 0)
            _swap_preset_data(presets+i, presets+(pvt++));
    }

    // move the pivot value into its place
    _swap_preset_data(presets+pvt, presets+count-1);

    // and invoke on the subsequences. does NOT include the pivot-slot
    _sort_presets_data(presets, pvt++);
    _sort_presets_data(presets+pvt, count - pvt);
}

// adjust bundle safely to lilv, as it wants the last character as the separator
// this also ensures paths are always written the same way
const char* _get_safe_bundlepath(const char* const bundle, size_t& bundlepathsize)
{
    static char tmppath[PATH_MAX+2];
    char* bundlepath = realpath(bundle, tmppath);

    if (bundlepath == nullptr)
    {
        bundlepathsize = 0;
        return nullptr;
    }

    bundlepathsize = strlen(bundlepath);

    if (bundlepathsize <= 1)
        return nullptr;

    if (bundlepath[bundlepathsize] != OS_SEP)
    {
        bundlepath[bundlepathsize  ] = OS_SEP;
        bundlepath[bundlepathsize+1] = '\0';
    }

    return bundlepath;
}

// refresh everything
// plugins are not truly scanned here, only later per request
void _refresh()
{
    BUNDLES.clear();
    PLUGNFO.clear();
    BUNDLED_PLUGINS.clear();

    const LilvPlugins* const plugins = lilv_world_get_all_plugins(W);

    // Make a list of all installed bundles
    LILV_FOREACH(plugins, itpls, plugins)
    {
        const LilvPlugin* const p = lilv_plugins_get(plugins, itpls);

        const LilvNodes* const bundles = lilv_plugin_get_data_uris(p);

        const std::string uri = lilv_node_as_uri(lilv_plugin_get_uri(p));

        // store empty dict for later
        PLUGNFO[uri] = PluginInfo_Init;

        LILV_FOREACH(nodes, itbnds, bundles)
        {
            const LilvNode* const bundlenode = lilv_nodes_get(bundles, itbnds);

            if (bundlenode == nullptr)
                continue;
            if (! lilv_node_is_uri(bundlenode))
                continue;

            char* lilvparsed;
            const char* bundlepath;

            lilvparsed = lilv_file_uri_parse(lilv_node_as_uri(bundlenode), nullptr);
            if (lilvparsed == nullptr)
                continue;

            bundlepath = dirname(lilvparsed);
            if (bundlepath == nullptr)
            {
                lilv_free(lilvparsed);
                continue;
            }

            size_t bundlepathsize;
            bundlepath = _get_safe_bundlepath(bundlepath, bundlepathsize);
            lilv_free(lilvparsed);

            if (bundlepath == nullptr)
                continue;

            const std::string bundlestr = bundlepath;

            if (std::find(BUNDLES.begin(), BUNDLES.end(), bundlestr) == BUNDLES.end())
                BUNDLES.push_back(bundlestr);

            if (BUNDLED_PLUGINS.count(bundlestr) == 0)
                BUNDLED_PLUGINS[bundlestr] = std::stringlist();

            std::stringlist& bplugs(BUNDLED_PLUGINS[bundlestr]);

            if (std::find(bplugs.begin(), bplugs.end(), uri) == bplugs.end())
                bplugs.push_back(uri);
        }
    }
}

const PluginInfo& _get_plugin_info(const LilvPlugin* const p, const NamespaceDefinitions& ns)
{
    static PluginInfo info;
    memset(&info, 0, sizeof(PluginInfo));

    const char* const bundleuri = lilv_node_as_uri(lilv_plugin_get_bundle_uri(p));
    const char* const bundle    = lilv_file_uri_parse(bundleuri, nullptr);

    const size_t bundleurilen = strlen(bundleuri);

    // --------------------------------------------------------------------------------------------------------
    // uri

    info.uri = lilv_node_as_uri(lilv_plugin_get_uri(p));

    // --------------------------------------------------------------------------------------------------------
    // name

    if (LilvNode* const node = lilv_plugin_get_name(p))
    {
        const char* const name = lilv_node_as_string(node);
        info.name = (name != nullptr) ? strdup(name) : nc;
        lilv_node_free(node);
    }
    else
    {
        info.name = nc;
    }

    // --------------------------------------------------------------------------------------------------------
    // binary

    info.binary = lilv_node_as_string(lilv_plugin_get_library_uri(p));
    if (info.binary != nullptr)
        info.binary = lilv_file_uri_parse(info.binary, nullptr);
    else
        info.binary = nc;

    // --------------------------------------------------------------------------------------------------------
    // license

    if (LilvNodes* const nodes = lilv_plugin_get_value(p, ns.doap_license))
    {
        const char* license = lilv_node_as_string(lilv_nodes_get_first(nodes));

        if (strncmp(license, bundleuri, bundleurilen) == 0)
            license += bundleurilen;

        info.license = strdup(license);
        lilv_nodes_free(nodes);
    }
    else if (LilvNodes* const nodes2 = lilv_plugin_get_value(p, ns.lv2core_project))
    {
        if (LilvNode* const lcsnode = lilv_world_get(W, lilv_nodes_get_first(nodes2), ns.doap_license, nullptr))
        {
            const char* license = lilv_node_as_string(lcsnode);

            if (strncmp(license, bundleuri, bundleurilen) == 0)
                license += bundleurilen;

            info.license = strdup(license);
            lilv_node_free(lcsnode);
        }
        else
        {
            info.license = nc;
        }
        lilv_nodes_free(nodes2);
    }
    else
    {
        info.license = nc;
    }

    // --------------------------------------------------------------------------------------------------------
    // comment

    if (LilvNodes* const nodes = lilv_plugin_get_value(p, ns.rdfs_comment))
    {
        info.comment = strdup(lilv_node_as_string(lilv_nodes_get_first(nodes)));
        lilv_nodes_free(nodes);
    }
    else
    {
        info.comment = nc;
    }

    // --------------------------------------------------------------------------------------------------------
    // categories

    if (LilvNodes* const nodes = lilv_plugin_get_value(p, ns.rdf_type))
    {
        LILV_FOREACH(nodes, it, nodes)
        {
            const LilvNode* const node2 = lilv_nodes_get(nodes, it);
            const char* const nodestr = lilv_node_as_string(node2);

            if (nodestr == nullptr)
                continue;

            if (const char* cat = strstr(nodestr, "http://lv2plug.in/ns/lv2core#"))
            {
                cat += 29; // strlen("http://lv2plug.in/ns/lv2core#")

                if (cat[0] == '\0')
                    continue;
                if (strcmp(cat, "Plugin") == 0)
                    continue;

                else if (strcmp(cat, "DelayPlugin") == 0)
                    info.category = kCategoryDelayPlugin;
                else if (strcmp(cat, "DistortionPlugin") == 0)
                    info.category = kCategoryDistortionPlugin;
                else if (strcmp(cat, "WaveshaperPlugin") == 0)
                    info.category = kCategoryWaveshaperPlugin;
                else if (strcmp(cat, "DynamicsPlugin") == 0)
                    info.category = kCategoryDynamicsPlugin;
                else if (strcmp(cat, "AmplifierPlugin") == 0)
                    info.category = kCategoryAmplifierPlugin;
                else if (strcmp(cat, "CompressorPlugin") == 0)
                    info.category = kCategoryCompressorPlugin;
                else if (strcmp(cat, "ExpanderPlugin") == 0)
                    info.category = kCategoryExpanderPlugin;
                else if (strcmp(cat, "GatePlugin") == 0)
                    info.category = kCategoryGatePlugin;
                else if (strcmp(cat, "LimiterPlugin") == 0)
                    info.category = kCategoryLimiterPlugin;
                else if (strcmp(cat, "FilterPlugin") == 0)
                    info.category = kCategoryFilterPlugin;
                else if (strcmp(cat, "AllpassPlugin") == 0)
                    info.category = kCategoryAllpassPlugin;
                else if (strcmp(cat, "BandpassPlugin") == 0)
                    info.category = kCategoryBandpassPlugin;
                else if (strcmp(cat, "CombPlugin") == 0)
                    info.category = kCategoryCombPlugin;
                else if (strcmp(cat, "EQPlugin") == 0)
                    info.category = kCategoryEQPlugin;
                else if (strcmp(cat, "MultiEQPlugin") == 0)
                    info.category = kCategoryMultiEQPlugin;
                else if (strcmp(cat, "ParaEQPlugin") == 0)
                    info.category = kCategoryParaEQPlugin;
                else if (strcmp(cat, "HighpassPlugin") == 0)
                    info.category = kCategoryHighpassPlugin;
                else if (strcmp(cat, "LowpassPlugin") == 0)
                    info.category = kCategoryLowpassPlugin;
                else if (strcmp(cat, "GeneratorPlugin") == 0)
                    info.category = kCategoryGeneratorPlugin;
                else if (strcmp(cat, "ConstantPlugin") == 0)
                    info.category = kCategoryConstantPlugin;
                else if (strcmp(cat, "InstrumentPlugin") == 0)
                    info.category = kCategoryInstrumentPlugin;
                else if (strcmp(cat, "OscillatorPlugin") == 0)
                    info.category = kCategoryOscillatorPlugin;
                else if (strcmp(cat, "ModulatorPlugin") == 0)
                    info.category = kCategoryModulatorPlugin;
                else if (strcmp(cat, "ChorusPlugin") == 0)
                    info.category = kCategoryChorusPlugin;
                else if (strcmp(cat, "FlangerPlugin") == 0)
                    info.category = kCategoryFlangerPlugin;
                else if (strcmp(cat, "PhaserPlugin") == 0)
                    info.category = kCategoryPhaserPlugin;
                else if (strcmp(cat, "ReverbPlugin") == 0)
                    info.category = kCategoryReverbPlugin;
                else if (strcmp(cat, "SimulatorPlugin") == 0)
                    info.category = kCategorySimulatorPlugin;
                else if (strcmp(cat, "SpatialPlugin") == 0)
                    info.category = kCategorySpatialPlugin;
                else if (strcmp(cat, "SpectralPlugin") == 0)
                    info.category = kCategorySpectralPlugin;
                else if (strcmp(cat, "PitchPlugin") == 0)
                    info.category = kCategoryPitchPlugin;
                else if (strcmp(cat, "UtilityPlugin") == 0)
                    info.category = kCategoryUtilityPlugin;
                else if (strcmp(cat, "AnalyserPlugin") == 0)
                    info.category = kCategoryAnalyserPlugin;
                else if (strcmp(cat, "ConverterPlugin") == 0)
                    info.category = kCategoryConverterPlugin;
                else if (strcmp(cat, "FunctionPlugin") == 0)
                    info.category = kCategoryFunctionPlugin;
                else if (strcmp(cat, "MixerPlugin") == 0)
                    info.category = kCategoryMixerPlugin;
            }
        }
        lilv_nodes_free(nodes);
    }

    // --------------------------------------------------------------------------------------------------------
    // version

    if (LilvNodes* const minorvers = lilv_plugin_get_value(p, ns.lv2core_minorVersion))
    {
        info.minorVersion = lilv_node_as_int(lilv_nodes_get_first(minorvers));
        lilv_nodes_free(minorvers);
    }

    if (LilvNodes* const microvers = lilv_plugin_get_value(p, ns.lv2core_microVersion))
    {
        info.microVersion = lilv_node_as_int(lilv_nodes_get_first(microvers));
        lilv_nodes_free(microvers);
    }

    {
        char versiontmpstr[32+1] = { '\0' };
        snprintf(versiontmpstr, 32, "%d.%d", info.minorVersion, info.microVersion);
        info.version = strdup(versiontmpstr);
    }

    // 0.x is experimental
    if (info.minorVersion == 0)
        info.stability = kStabilityExperimental;

    // odd x.2 or 2.x is testing/development
    else if (info.minorVersion % 2 != 0 || info.microVersion % 2 != 0)
        info.stability = kStabilityTesting;

    // otherwise it's stable
    else
        info.stability = kStabilityStable;

    // --------------------------------------------------------------------------------------------------------
    // author name

    if (LilvNode* const node = lilv_plugin_get_author_name(p))
    {
        info.author.name = strdup(lilv_node_as_string(node));
        lilv_node_free(node);
    }
    else
    {
        info.author.name = nc;
    }

    // --------------------------------------------------------------------------------------------------------
    // author homepage

    if (LilvNode* const node = lilv_plugin_get_author_homepage(p))
    {
        info.author.homepage = strdup(lilv_node_as_string(node));
        lilv_node_free(node);
    }
    else if (LilvNodes* const nodes2 = lilv_plugin_get_value(p, ns.lv2core_project))
    {
        if (LilvNode* const mntnr = lilv_world_get(W, lilv_nodes_get_first(nodes2), ns.doap_maintainer, nullptr))
        {
            if (LilvNode* const hmpg = lilv_world_get(W, lilv_nodes_get_first(mntnr), ns.foaf_homepage, nullptr))
            {
                info.author.homepage = strdup(lilv_node_as_string(hmpg));
                lilv_node_free(hmpg);
            }
            else
            {
                info.author.homepage = nc;
            }
            lilv_node_free(mntnr);
        }
        else
        {
            info.author.homepage = nc;
        }
        lilv_nodes_free(nodes2);
    }
    else
    {
        info.author.homepage = nc;
    }

    // --------------------------------------------------------------------------------------------------------
    // author email

    if (LilvNode* const node = lilv_plugin_get_author_email(p))
    {
        info.author.email = strdup(lilv_node_as_string(node));
        lilv_node_free(node);
    }
    else
    {
        info.author.email = nc;
    }

    // --------------------------------------------------------------------------------------------------------
    // brand

    if (LilvNodes* const nodes = lilv_plugin_get_value(p, ns.mod_brand))
    {
        char* const brand = strdup(lilv_node_as_string(lilv_nodes_get_first(nodes)));

        /* NOTE: this gives a false positive on valgrind.
                 see https://bugzilla.redhat.com/show_bug.cgi?id=678518 */
        if (strlen(brand) > 10)
            brand[10] = '\0';

        info.brand = brand;
        lilv_nodes_free(nodes);
    }
    else if (info.author.name == nc)
    {
        info.brand = nc;
    }
    else
    {
        if (strlen(info.author.name) <= 10)
        {
            info.brand = strdup(info.author.name);
        }
        else
        {
            char brand[10+1] = { '\0' };
            strncpy(brand, info.author.name, 10);
            info.brand = strdup(brand);
        }
    }

    // --------------------------------------------------------------------------------------------------------
    // label

    if (LilvNodes* const nodes = lilv_plugin_get_value(p, ns.mod_label))
    {
        char* const label = strdup(lilv_node_as_string(lilv_nodes_get_first(nodes)));

        /* NOTE: this gives a false positive on valgrind.
                 see https://bugzilla.redhat.com/show_bug.cgi?id=678518 */
        if (strlen(label) > 16)
            label[16] = '\0';

        info.label = label;
        lilv_nodes_free(nodes);
    }
    else if (info.name == nc)
    {
        info.label = nc;
    }
    else
    {
        if (strlen(info.name) <= 16)
        {
            info.label = strdup(info.name);
        }
        else
        {
            char label[16+1] = { '\0' };
            strncpy(label, info.name, 16);
            info.label = strdup(label);
        }
    }

    // --------------------------------------------------------------------------------------------------------
    // bundles

    {
        std::vector<std::string> bundles;

        size_t bundlepathsize;
        const char* bundlepath = _get_safe_bundlepath(bundle, bundlepathsize);

        if (bundlepath != nullptr)
        {
            const std::string bundlestr = bundlepath;
            bundles.push_back(bundlestr);
        }

        if (const LilvNodes* const bundlenodes = lilv_plugin_get_data_uris(p))
        {
            LILV_FOREACH(nodes, itbnds, bundlenodes)
            {
                const LilvNode* const bundlenode = lilv_nodes_get(bundlenodes, itbnds);

                if (bundlenode == nullptr)
                    continue;
                if (! lilv_node_is_uri(bundlenode))
                    continue;

                char* lilvparsed;
                lilvparsed = lilv_file_uri_parse(lilv_node_as_uri(bundlenode), nullptr);
                if (lilvparsed == nullptr)
                    continue;

                bundlepath = dirname(lilvparsed);
                if (bundlepath == nullptr)
                {
                    lilv_free(lilvparsed);
                    continue;
                }

                bundlepath = _get_safe_bundlepath(bundlepath, bundlepathsize);
                lilv_free(lilvparsed);

                if (bundlepath == nullptr)
                    continue;

                const std::string bundlestr = bundlepath;

                if (std::find(bundles.begin(), bundles.end(), bundlestr) == bundles.end())
                    bundles.push_back(bundlestr);
            }
        }

        size_t count = bundles.size();
        const char** const cbundles = new const char*[count+1];
        memset(cbundles, 0, sizeof(const char*) * (count+1));

        count = 0;
        for (const std::string& b : bundles)
            cbundles[count++] = strdup(b.c_str());

        info.bundles = cbundles;
    }

    // --------------------------------------------------------------------------------------------------------
    // get the proper modgui

    LilvNode* modguigui = nullptr;
    const char* resdir = nullptr;

    if (LilvNodes* const nodes = lilv_plugin_get_value(p, ns.modgui_gui))
    {
        LILV_FOREACH(nodes, it, nodes)
        {
            const LilvNode* const mgui = lilv_nodes_get(nodes, it);
            LilvNode* const resdirn = lilv_world_get(W, mgui, ns.modgui_resourcesDirectory, nullptr);
            if (resdirn == nullptr)
                continue;

            lilv_free((void*)resdir);
            resdir = lilv_file_uri_parse(lilv_node_as_string(resdirn), nullptr);

            lilv_node_free(modguigui);
            modguigui = lilv_node_duplicate(mgui);

            lilv_node_free(resdirn);

            if (strncmp(resdir, HOME, HOMElen) == 0)
                // found a modgui in the home dir, stop here and use it
                break;
        }

        lilv_nodes_free(nodes);
    }

    // --------------------------------------------------------------------------------------------------------
    // gui

    if (modguigui != nullptr)
    {
        info.gui.resourcesDirectory = resdir;
        resdir = nullptr;

        // check if modgui is defined in a separate file
        const std::string bundlestr = std::string(bundle) + OS_SEP_STR "modgui.ttl";
        info.gui.usingSeeAlso = std::ifstream(bundlestr.c_str()).good();

        // check if the modgui definition is on its own file and in the user dir
        info.gui.modificableInPlace = ((strstr(info.gui.resourcesDirectory, bundle) == nullptr || info.gui.usingSeeAlso) &&
                                        strncmp(info.gui.resourcesDirectory, HOME, HOMElen) == 0);

        // icon and settings templates
        if (LilvNode* const modgui_icon = lilv_world_get(W, modguigui, ns.modgui_iconTemplate, nullptr))
        {
            info.gui.iconTemplate = lilv_file_uri_parse(lilv_node_as_string(modgui_icon), nullptr);
            lilv_node_free(modgui_icon);
        }
        else
            info.gui.iconTemplate = nc;

        if (LilvNode* const modgui_setts = lilv_world_get(W, modguigui, ns.modgui_settingsTemplate, nullptr))
        {
            info.gui.settingsTemplate = lilv_file_uri_parse(lilv_node_as_string(modgui_setts), nullptr);
            lilv_node_free(modgui_setts);
        }
        else
            info.gui.settingsTemplate = nc;

        // javascript and stylesheet files
        if (LilvNode* const modgui_script = lilv_world_get(W, modguigui, ns.modgui_javascript, nullptr))
        {
            info.gui.javascript = lilv_file_uri_parse(lilv_node_as_string(modgui_script), nullptr);
            lilv_node_free(modgui_script);
        }
        else
            info.gui.javascript = nc;

        if (LilvNode* const modgui_style = lilv_world_get(W, modguigui, ns.modgui_stylesheet, nullptr))
        {
            info.gui.stylesheet = lilv_file_uri_parse(lilv_node_as_string(modgui_style), nullptr);
            lilv_node_free(modgui_style);
        }
        else
            info.gui.stylesheet = nc;

        // screenshot and thumbnail
        if (LilvNode* const modgui_scrn = lilv_world_get(W, modguigui, ns.modgui_screenshot, nullptr))
        {
            info.gui.screenshot = lilv_file_uri_parse(lilv_node_as_string(modgui_scrn), nullptr);
            lilv_node_free(modgui_scrn);
        }
        else
            info.gui.screenshot = nc;

        if (LilvNode* const modgui_thumb = lilv_world_get(W, modguigui, ns.modgui_thumbnail, nullptr))
        {
            info.gui.thumbnail = lilv_file_uri_parse(lilv_node_as_string(modgui_thumb), nullptr);
            lilv_node_free(modgui_thumb);
        }
        else
            info.gui.thumbnail = nc;

        // extra stuff, all optional
        if (LilvNode* const modgui_brand = lilv_world_get(W, modguigui, ns.modgui_brand, nullptr))
        {
            info.gui.brand = strdup(lilv_node_as_string(modgui_brand));
            lilv_node_free(modgui_brand);
        }
        else
            info.gui.brand = nc;

        if (LilvNode* const modgui_label = lilv_world_get(W, modguigui, ns.modgui_label, nullptr))
        {
            info.gui.label = strdup(lilv_node_as_string(modgui_label));
            lilv_node_free(modgui_label);
        }
        else
            info.gui.label = nc;

        if (LilvNode* const modgui_model = lilv_world_get(W, modguigui, ns.modgui_model, nullptr))
        {
            info.gui.model = strdup(lilv_node_as_string(modgui_model));
            lilv_node_free(modgui_model);
        }
        else
            info.gui.model = nc;

        if (LilvNode* const modgui_panel = lilv_world_get(W, modguigui, ns.modgui_panel, nullptr))
        {
            info.gui.panel = strdup(lilv_node_as_string(modgui_panel));
            lilv_node_free(modgui_panel);
        }
        else
            info.gui.panel = nc;

        if (LilvNode* const modgui_color = lilv_world_get(W, modguigui, ns.modgui_color, nullptr))
        {
            info.gui.color = strdup(lilv_node_as_string(modgui_color));
            lilv_node_free(modgui_color);
        }
        else
            info.gui.color = nc;

        if (LilvNode* const modgui_knob = lilv_world_get(W, modguigui, ns.modgui_knob, nullptr))
        {
            info.gui.knob = strdup(lilv_node_as_string(modgui_knob));
            lilv_node_free(modgui_knob);
        }
        else
            info.gui.knob = nc;

        if (LilvNodes* const modgui_ports = lilv_world_find_nodes(W, modguigui, ns.modgui_port, nullptr))
        {
            const unsigned int guiportscount = lilv_nodes_size(modgui_ports);

            PluginGUIPort* const guiports = new PluginGUIPort[guiportscount+1];
            memset(guiports, 0, sizeof(PluginGUIPort) * (guiportscount+1));

            for (unsigned int i=0; i<guiportscount; ++i)
                guiports[i] = { true, i, nc, nc };

            int index;

            LILV_FOREACH(nodes, it, modgui_ports)
            {
                const LilvNode* const modgui_port = lilv_nodes_get(modgui_ports, it);

                if (LilvNode* const guiports_index = lilv_world_get(W, modgui_port, ns.lv2core_index, nullptr))
                {
                    index = lilv_node_as_int(guiports_index);
                    lilv_node_free(guiports_index);
                }
                else
                {
                    continue;
                }

                if (index < 0 || index >= (int)guiportscount)
                    continue;

                PluginGUIPort& guiport(guiports[index]);

                if (LilvNode* const guiports_symbol = lilv_world_get(W, modgui_port, ns.lv2core_symbol, nullptr))
                {
                    // in case of duplicated indexes
                    if (guiport.symbol != nullptr && guiport.symbol != nc)
                        free((void*)guiport.symbol);

                    guiport.symbol = strdup(lilv_node_as_string(guiports_symbol));
                    lilv_node_free(guiports_symbol);
                }

                if (LilvNode* const guiports_name = lilv_world_get(W, modgui_port, ns.lv2core_name, nullptr))
                {
                    // in case of duplicated indexes
                    if (guiport.name != nullptr && guiport.name != nc)
                        free((void*)guiport.name);

                    guiport.name = strdup(lilv_node_as_string(guiports_name));
                    lilv_node_free(guiports_name);
                }
            }

            info.gui.ports = guiports;

            lilv_nodes_free(modgui_ports);
        }

        lilv_node_free(modguigui);
    }
    else
    {
        info.gui.resourcesDirectory = nc;
        info.gui.iconTemplate = nc;
        info.gui.settingsTemplate = nc;
        info.gui.javascript = nc;
        info.gui.stylesheet = nc;
        info.gui.screenshot = nc;
        info.gui.thumbnail = nc;
        info.gui.brand = nc;
        info.gui.label = nc;
        info.gui.model = nc;
        info.gui.panel = nc;
        info.gui.color = nc;
        info.gui.knob = nc;
    }

    // --------------------------------------------------------------------------------------------------------
    // ports

    if (const uint32_t count = lilv_plugin_get_num_ports(p))
    {
        uint32_t countAudioInput=0,   countAudioOutput=0;
        uint32_t countControlInput=0, countControlOutput=0;
        uint32_t countCvInput=0,      countCvOutput=0;
        uint32_t countMidiInput=0,    countMidiOutput=0;

        // precalculate port counts first
        for (uint32_t i=0; i<count; ++i)
        {
            const LilvPort* const port = lilv_plugin_get_port_by_index(p, i);

            int direction = 0; // using -1 = input, +1 = output
            int type      = 0; // using by order1-4: audio, control, cv, midi

            if (LilvNodes* const nodes = lilv_port_get_value(p, port, ns.rdf_type))
            {
                LILV_FOREACH(nodes, it, nodes)
                {
                    const LilvNode* const node2 = lilv_nodes_get(nodes, it);
                    const char* const nodestr = lilv_node_as_string(node2);

                    if (nodestr == nullptr)
                        continue;

                    else if (strcmp(nodestr, LV2_CORE__InputPort) == 0)
                        direction = -1;
                    else if (strcmp(nodestr, LV2_CORE__OutputPort) == 0)
                        direction = +1;
                    else if (strcmp(nodestr, LV2_CORE__AudioPort) == 0)
                        type = 1;
                    else if (strcmp(nodestr, LV2_CORE__ControlPort) == 0)
                        type = 2;
                    else if (strcmp(nodestr, LV2_CORE__CVPort) == 0)
                        type = 3;
                    else if (strcmp(nodestr, LV2_ATOM__AtomPort) == 0 && lilv_port_supports_event(p, port, ns.midi_MidiEvent))
                    {
                        if (LilvNodes* const nodes2 = lilv_port_get_value(p, port, ns.atom_bufferType))
                        {
                            if (lilv_node_equals(lilv_nodes_get_first(nodes2), ns.atom_Sequence))
                                type = 4;
                            lilv_nodes_free(nodes2);
                        }
                    }
                }
                lilv_nodes_free(nodes);
            }

            if (direction == 0 || type == 0)
                continue;

            switch (type)
            {
            case 1: // audio
                if (direction == 1)
                    ++countAudioOutput;
                else
                    ++countAudioInput;
                break;
            case 2: // control
                if (direction == 1)
                    ++countControlOutput;
                else
                    ++countControlInput;
                break;
            case 3: // cv
                if (direction == 1)
                    ++countCvOutput;
                else
                    ++countCvInput;
                break;
            case 4: // midi
                if (direction == 1)
                    ++countMidiOutput;
                else
                    ++countMidiInput;
                break;
            }
        }

        // allocate stuff
        if (countAudioInput > 0)
        {
            info.ports.audio.input = new PluginPort[countAudioInput+1];
            memset(info.ports.audio.input, 0, sizeof(PluginPort) * (countAudioInput+1));
        }
        if (countAudioOutput > 0)
        {
            info.ports.audio.output = new PluginPort[countAudioOutput+1];
            memset(info.ports.audio.output, 0, sizeof(PluginPort) * (countAudioOutput+1));
        }
        if (countControlInput > 0)
        {
            info.ports.control.input = new PluginPort[countControlInput+1];
            memset(info.ports.control.input, 0, sizeof(PluginPort) * (countControlInput+1));
        }
        if (countControlOutput > 0)
        {
            info.ports.control.output = new PluginPort[countControlOutput+1];
            memset(info.ports.control.output, 0, sizeof(PluginPort) * (countControlOutput+1));
        }
        if (countCvInput > 0)
        {
            info.ports.cv.input = new PluginPort[countCvInput+1];
            memset(info.ports.cv.input, 0, sizeof(PluginPort) * (countCvInput+1));
        }
        if (countCvOutput > 0)
        {
            info.ports.cv.output = new PluginPort[countCvOutput+1];
            memset(info.ports.cv.output, 0, sizeof(PluginPort) * (countCvOutput+1));
        }
        if (countMidiInput > 0)
        {
            info.ports.midi.input = new PluginPort[countMidiInput+1];
            memset(info.ports.midi.input, 0, sizeof(PluginPort) * (countMidiInput+1));
        }
        if (countMidiOutput > 0)
        {
            info.ports.midi.output = new PluginPort[countMidiOutput+1];
            memset(info.ports.midi.output, 0, sizeof(PluginPort) * (countMidiOutput+1));
        }

        // use counters as indexes now
        countAudioInput=countAudioOutput=countControlInput=countControlOutput=0;
        countCvInput=countCvOutput=countMidiInput=countMidiOutput=0;

        // now fill info
        for (uint32_t i=0; i<count; ++i)
        {
            const LilvPort* const port = lilv_plugin_get_port_by_index(p, i);

            // ----------------------------------------------------------------------------------------------------

            int direction = 0; // using -1 = input, +1 = output
            int type      = 0; // using by order1-4: audio, control, cv, midi

            if (LilvNodes* const nodes = lilv_port_get_value(p, port, ns.rdf_type))
            {
                LILV_FOREACH(nodes, it, nodes)
                {
                    const LilvNode* const node2 = lilv_nodes_get(nodes, it);
                    const char* const nodestr = lilv_node_as_string(node2);

                    if (nodestr == nullptr)
                        continue;

                    else if (strcmp(nodestr, LV2_CORE__InputPort) == 0)
                        direction = -1;
                    else if (strcmp(nodestr, LV2_CORE__OutputPort) == 0)
                        direction = +1;
                    else if (strcmp(nodestr, LV2_CORE__AudioPort) == 0)
                        type = 1;
                    else if (strcmp(nodestr, LV2_CORE__ControlPort) == 0)
                        type = 2;
                    else if (strcmp(nodestr, LV2_CORE__CVPort) == 0)
                        type = 3;
                    else if (strcmp(nodestr, LV2_ATOM__AtomPort) == 0 && lilv_port_supports_event(p, port, ns.midi_MidiEvent))
                    {
                        if (LilvNodes* const nodes2 = lilv_port_get_value(p, port, ns.atom_bufferType))
                        {
                            if (lilv_node_equals(lilv_nodes_get_first(nodes2), ns.atom_Sequence))
                                type = 4;
                            lilv_nodes_free(nodes2);
                        }
                    }
                }
                lilv_nodes_free(nodes);
            }

            if (direction == 0 || type == 0)
                continue;

            // ----------------------------------------------------------------------------------------------------

            PluginPort portinfo;
            memset(&portinfo, 0, sizeof(PluginPort));

            portinfo.index = i;

            // ----------------------------------------------------------------------------------------------------
            // name

            if (LilvNode* const node = lilv_port_get_name(p, port))
            {
                portinfo.name = strdup(lilv_node_as_string(node));
                lilv_node_free(node);
            }
            else
            {
                portinfo.name = nc;
            }

            // ----------------------------------------------------------------------------------------------------
            // symbol

            if (const LilvNode* const symbolnode = lilv_port_get_symbol(p, port))
                portinfo.symbol = strdup(lilv_node_as_string(symbolnode));
            else
                portinfo.symbol = nc;

            // ----------------------------------------------------------------------------------------------------
            // short name

            if (LilvNodes* const nodes = lilv_port_get_value(p, port, ns.lv2core_shortName))
            {
                portinfo.shortName = strdup(lilv_node_as_string(lilv_nodes_get_first(nodes)));
                lilv_nodes_free(nodes);
            }
            else
            {
                portinfo.shortName = strdup(portinfo.name);
            }

            if (strlen(portinfo.shortName) > 16)
                ((char*)portinfo.shortName)[16] = '\0';

            // ----------------------------------------------------------------------------------------------------
            // comment

            if (LilvNodes* const nodes = lilv_port_get_value(p, port, ns.rdfs_comment))
            {
                portinfo.comment = strdup(lilv_node_as_string(lilv_nodes_get_first(nodes)));
                lilv_nodes_free(nodes);
            }
            else
            {
                portinfo.comment = nc;
            }

            // ----------------------------------------------------------------------------------------------------
            // designation

            if (LilvNodes* const nodes = lilv_port_get_value(p, port, ns.lv2core_designation))
            {
                portinfo.designation = strdup(lilv_node_as_string(lilv_nodes_get_first(nodes)));
                lilv_nodes_free(nodes);
            }
            else
            {
                portinfo.designation = nc;
            }

            // ----------------------------------------------------------------------------------------------------
            // range steps

            if (LilvNodes* const nodes = lilv_port_get_value(p, port, ns.mod_rangeSteps))
            {
                portinfo.rangeSteps = lilv_node_as_int(lilv_nodes_get_first(nodes));
                lilv_nodes_free(nodes);
            }
            else if (LilvNodes* const nodes2 = lilv_port_get_value(p, port, ns.pprops_rangeSteps))
            {
                portinfo.rangeSteps = lilv_node_as_int(lilv_nodes_get_first(nodes2));
                lilv_nodes_free(nodes2);
            }

            // ----------------------------------------------------------------------------------------------------
            // port properties

            if (LilvNodes* const nodes = lilv_port_get_value(p, port, ns.lv2core_portProperty))
            {
                const unsigned int propcount = lilv_nodes_size(nodes);
                unsigned int pindex = 0;

                const char** const props = new const char*[propcount+1];
                memset(props, 0, sizeof(const char*) * (propcount+1));

                LILV_FOREACH(nodes, itprop, nodes)
                {
                    if (pindex >= propcount)
                        continue;

                    if (const char* prop = strrchr(lilv_node_as_string(lilv_nodes_get(nodes, itprop)), '#'))
                    {
                        prop += 1;
                        if (prop[0] != '\0')
                            props[pindex++] = strdup(prop);
                    }
                }

                portinfo.properties = props;
                lilv_nodes_free(nodes);
            }

            // ----------------------------------------------------------------------------------------------------

            if (type == 2 || type == 3)
            {
                LilvNodes* xminimum = lilv_port_get_value(p, port, ns.mod_minimum);
                if (xminimum == nullptr)
                    xminimum = lilv_port_get_value(p, port, ns.lv2core_minimum);
                LilvNodes* xmaximum = lilv_port_get_value(p, port, ns.mod_maximum);
                if (xmaximum == nullptr)
                    xmaximum = lilv_port_get_value(p, port, ns.lv2core_maximum);
                LilvNodes* xdefault = lilv_port_get_value(p, port, ns.mod_default);
                if (xdefault == nullptr)
                    xdefault = lilv_port_get_value(p, port, ns.lv2core_default);

                if (xminimum != nullptr && xmaximum != nullptr)
                {
                    portinfo.ranges.min = lilv_node_as_float(lilv_nodes_get_first(xminimum));
                    portinfo.ranges.max = lilv_node_as_float(lilv_nodes_get_first(xmaximum));

                    if (portinfo.ranges.min >= portinfo.ranges.max)
                        portinfo.ranges.max = portinfo.ranges.min + 1.0f;

                    if (xdefault != nullptr)
                        portinfo.ranges.def = lilv_node_as_float(lilv_nodes_get_first(xdefault));
                    else
                        portinfo.ranges.def = portinfo.ranges.min;
                }
                else
                {
                    portinfo.ranges.min = (type == 3) ? -1.0f : 0.0f;
                    portinfo.ranges.max = 1.0f;
                    portinfo.ranges.def = 0.0f;
                }

                lilv_nodes_free(xminimum);
                lilv_nodes_free(xmaximum);
                lilv_nodes_free(xdefault);

                if (LilvScalePoints* const scalepoints = lilv_port_get_scale_points(p, port))
                {
                    if (const unsigned int scalepointcount = lilv_scale_points_size(scalepoints))
                    {
                        PluginPortScalePoint* const portsps = new PluginPortScalePoint[scalepointcount+1];
                        memset(portsps, 0, sizeof(PluginPortScalePoint) * (scalepointcount+1));

                        // get all scalepoints and sort them by value
                        std::map<double,const LilvScalePoint*> sortedpoints;

                        LILV_FOREACH(scale_points, itscl, scalepoints)
                        {
                            const LilvScalePoint* const scalepoint = lilv_scale_points_get(scalepoints, itscl);
                            const LilvNode* const xlabel = lilv_scale_point_get_label(scalepoint);
                            const LilvNode* const xvalue = lilv_scale_point_get_value(scalepoint);

                            if (xlabel == nullptr || xvalue == nullptr)
                                continue;

                            const double valueid = lilv_node_as_float(xvalue);
                            sortedpoints[valueid] = scalepoint;
                        }

                        // now store them sorted
                        unsigned int spindex = 0;
                        for (auto& scalepoint : sortedpoints)
                        {
                            if (spindex >= scalepointcount)
                                continue;

                            const LilvNode* const xlabel = lilv_scale_point_get_label(scalepoint.second);
                            const LilvNode* const xvalue = lilv_scale_point_get_value(scalepoint.second);

                            portsps[spindex++] = {
                                true,
                                lilv_node_as_float(xvalue),
                                strdup(lilv_node_as_string(xlabel)),
                            };
                        }

                        portinfo.scalePoints = portsps;
                    }

                    lilv_scale_points_free(scalepoints);
                }
            }

            // ----------------------------------------------------------------------------------------------------
            // control ports might contain unit

            portinfo.units.label  = nc;
            portinfo.units.render = nc;
            portinfo.units.symbol = nc;

            if (type == 2)
            {
                if (LilvNodes* const uunits = lilv_port_get_value(p, port, ns.units_unit))
                {
                    LilvNode* const uunit = lilv_nodes_get_first(uunits);
                    const char* uuri = lilv_node_as_uri(uunit);

                    // using pre-existing lv2 unit
                    if (uuri != nullptr && strncmp(uuri, LV2_UNITS_PREFIX, 38) == 0)
                    {
                        uuri += 38; // strlen(LV2_UNITS_PREFIX)

                        if (_isalnum(uuri))
                        {
                            const char* const* unittable;

                            if (strcmp(uuri, "s") == 0)
                                unittable = kUnit_s;
                            else if (strcmp(uuri, "ms") == 0)
                                unittable = kUnit_ms;
                            else if (strcmp(uuri, "min") == 0)
                                unittable = kUnit_min;
                            else if (strcmp(uuri, "bar") == 0)
                                unittable = kUnit_bar;
                            else if (strcmp(uuri, "beat") == 0)
                                unittable = kUnit_beat;
                            else if (strcmp(uuri, "frame") == 0)
                                unittable = kUnit_frame;
                            else if (strcmp(uuri, "m") == 0)
                                unittable = kUnit_m;
                            else if (strcmp(uuri, "cm") == 0)
                                unittable = kUnit_cm;
                            else if (strcmp(uuri, "mm") == 0)
                                unittable = kUnit_mm;
                            else if (strcmp(uuri, "km") == 0)
                                unittable = kUnit_km;
                            else if (strcmp(uuri, "inch") == 0)
                                unittable = kUnit_inch;
                            else if (strcmp(uuri, "mile") == 0)
                                unittable = kUnit_mile;
                            else if (strcmp(uuri, "db") == 0)
                                unittable = kUnit_db;
                            else if (strcmp(uuri, "pc") == 0)
                                unittable = kUnit_pc;
                            else if (strcmp(uuri, "coef") == 0)
                                unittable = kUnit_coef;
                            else if (strcmp(uuri, "hz") == 0)
                                unittable = kUnit_hz;
                            else if (strcmp(uuri, "khz") == 0)
                                unittable = kUnit_khz;
                            else if (strcmp(uuri, "mhz") == 0)
                                unittable = kUnit_mhz;
                            else if (strcmp(uuri, "bpm") == 0)
                                unittable = kUnit_bpm;
                            else if (strcmp(uuri, "oct") == 0)
                                unittable = kUnit_oct;
                            else if (strcmp(uuri, "cent") == 0)
                                unittable = kUnit_cent;
                            else if (strcmp(uuri, "semitone12TET") == 0)
                                unittable = kUnit_semitone12TET;
                            else if (strcmp(uuri, "degree") == 0)
                                unittable = kUnit_degree;
                            else if (strcmp(uuri, "midiNote") == 0)
                                unittable = kUnit_midiNote;
                            else
                                unittable = nullptr;

                            if (unittable != nullptr)
                            {
                                portinfo.units.label  = unittable[0];
                                portinfo.units.render = unittable[1];
                                portinfo.units.symbol = unittable[2];
                            }
                        }
                    }
                    // using custom unit
                    else
                    {
                        if (LilvNode* const node = lilv_world_get(W, uunit, ns.rdfs_label, nullptr))
                        {
                            portinfo.units.label = strdup(lilv_node_as_string(node));
                            lilv_node_free(node);
                        }

                        if (LilvNode* const node = lilv_world_get(W, uunit, ns.units_render, nullptr))
                        {
                            portinfo.units.render = strdup(lilv_node_as_string(node));
                            lilv_node_free(node);
                        }

                        if (LilvNode* const node = lilv_world_get(W, uunit, ns.units_symbol, nullptr))
                        {
                            portinfo.units.symbol = strdup(lilv_node_as_string(node));
                            lilv_node_free(node);
                        }

                        portinfo.units._custom = true;
                    }

                    lilv_nodes_free(uunits);
                }
            }

            // ----------------------------------------------------------------------------------------------------

            portinfo.valid = true;

            switch (type)
            {
            case 1: // audio
                if (direction == 1)
                    info.ports.audio.output[countAudioOutput++] = portinfo;
                else
                    info.ports.audio.input[countAudioInput++] = portinfo;
                break;
            case 2: // control
                if (direction == 1)
                    info.ports.control.output[countControlOutput++] = portinfo;
                else
                    info.ports.control.input[countControlInput++] = portinfo;
                break;
            case 3: // cv
                if (direction == 1)
                    info.ports.cv.output[countCvOutput++] = portinfo;
                else
                    info.ports.cv.input[countCvInput++] = portinfo;
                break;
            case 4: // midi
                if (direction == 1)
                    info.ports.midi.output[countMidiOutput++] = portinfo;
                else
                    info.ports.midi.input[countMidiInput++] = portinfo;
                break;
            }
        }
    }

    // --------------------------------------------------------------------------------------------------------
    // presets

    if (LilvNodes* const presetnodes = lilv_plugin_get_related(p, ns.pset_Preset))
    {
        const unsigned int presetcount = lilv_nodes_size(presetnodes);
        unsigned int prindex = 0;

        PluginPreset* const presets = new PluginPreset[presetcount+1];
        memset(presets, 0, sizeof(PluginPreset) * (presetcount+1));

        std::vector<const LilvNode*> loadedPresetResourceNodes;

        LILV_FOREACH(nodes, itprs, presetnodes)
        {
            if (prindex >= presetcount)
                continue;

            const LilvNode* const presetnode = lilv_nodes_get(presetnodes, itprs);

            // try to find label without loading the preset resource first
            LilvNode* xlabel = lilv_world_get(W, presetnode, ns.rdfs_label, nullptr);

            // failed, try loading resource
            if (xlabel == nullptr)
            {
                // if loading resource fails, skip this preset
                if (lilv_world_load_resource(W, presetnode) == -1)
                    continue;

                // ok, let's try again
                xlabel = lilv_world_get(W, presetnode, ns.rdfs_label, nullptr);

                // need to unload later
                loadedPresetResourceNodes.push_back(presetnode);
            }

            if (xlabel != nullptr)
            {
                presets[prindex++] = {
                    true,
                    strdup(lilv_node_as_uri(presetnode)),
                    strdup(lilv_node_as_string(xlabel)),
                };

                lilv_node_free(xlabel);
            }
        }

        if (prindex > 1)
            _sort_presets_data(presets, prindex);

#ifdef HAVE_NEW_LILV
        for (const LilvNode* presetnode : loadedPresetResourceNodes)
            lilv_world_unload_resource(W, presetnode);
#endif

        info.presets = presets;

        loadedPresetResourceNodes.clear();
        lilv_nodes_free(presetnodes);
    }

    // --------------------------------------------------------------------------------------------------------

    lilv_free((void*)bundle);

    info.valid = true;
    return info;
}

// --------------------------------------------------------------------------------------------------------

static const PluginInfo** _plug_ret = nullptr;
static size_t _plug_lastsize = 0;
static const char** _bundles_ret = nullptr;

static void _clear_gui_port_info(PluginGUIPort& guiportinfo)
{
    if (guiportinfo.name != nullptr && guiportinfo.name != nc)
        free((void*)guiportinfo.name);
    if (guiportinfo.symbol != nullptr && guiportinfo.symbol != nc)
        free((void*)guiportinfo.symbol);

    memset(&guiportinfo, 0, sizeof(PluginGUIPort));
}

static void _clear_port_info(PluginPort& portinfo)
{
    if (portinfo.name != nullptr && portinfo.name != nc)
        free((void*)portinfo.name);
    if (portinfo.symbol != nullptr && portinfo.symbol != nc)
        free((void*)portinfo.symbol);
    if (portinfo.comment != nullptr && portinfo.comment != nc)
        free((void*)portinfo.comment);
    if (portinfo.designation != nullptr && portinfo.designation != nc)
        free((void*)portinfo.designation);
    if (portinfo.shortName != nullptr && portinfo.shortName != nc)
        free((void*)portinfo.shortName);

    if (portinfo.properties != nullptr)
    {
        for (int i=0; portinfo.properties[i] != nullptr; ++i)
            free((void*)portinfo.properties[i]);
        delete[] portinfo.properties;
    }

    if (portinfo.scalePoints != nullptr)
    {
        for (int i=0; portinfo.scalePoints[i].valid; ++i)
            free((void*)portinfo.scalePoints[i].label);
        delete[] portinfo.scalePoints;
    }

    if (portinfo.units._custom)
    {
        if (portinfo.units.label != nullptr && portinfo.units.label != nc)
            free((void*)portinfo.units.label);
        if (portinfo.units.render != nullptr && portinfo.units.render != nc)
            free((void*)portinfo.units.render);
        if (portinfo.units.symbol != nullptr && portinfo.units.symbol != nc)
            free((void*)portinfo.units.symbol);
    }

    memset(&portinfo, 0, sizeof(PluginPort));
}

static void _clear_plugin_info(PluginInfo& info)
{
    if (info.name != nullptr && info.name != nc)
        lilv_free((void*)info.name);
    if (info.binary != nullptr && info.binary != nc)
        lilv_free((void*)info.binary);
    if (info.license != nullptr && info.license != nc)
        free((void*)info.license);
    if (info.comment != nullptr && info.comment != nc)
        free((void*)info.comment);
    if (info.version != nullptr && info.version != nc)
        free((void*)info.version);
    if (info.brand != nullptr && info.brand != nc)
        free((void*)info.brand);
    if (info.label != nullptr && info.label != nc)
        free((void*)info.label);
    if (info.author.name != nullptr && info.author.name != nc)
        free((void*)info.author.name);
    if (info.author.homepage != nullptr && info.author.homepage != nc)
        free((void*)info.author.homepage);
    if (info.author.email != nullptr && info.author.email != nc)
        free((void*)info.author.email);
    if (info.gui.resourcesDirectory != nullptr && info.gui.resourcesDirectory != nc)
        lilv_free((void*)info.gui.resourcesDirectory);
    if (info.gui.iconTemplate != nullptr && info.gui.iconTemplate != nc)
        lilv_free((void*)info.gui.iconTemplate);
    if (info.gui.settingsTemplate != nullptr && info.gui.settingsTemplate != nc)
        lilv_free((void*)info.gui.settingsTemplate);
    if (info.gui.javascript != nullptr && info.gui.javascript != nc)
        lilv_free((void*)info.gui.javascript);
    if (info.gui.stylesheet != nullptr && info.gui.stylesheet != nc)
        lilv_free((void*)info.gui.stylesheet);
    if (info.gui.screenshot != nullptr && info.gui.screenshot != nc)
        lilv_free((void*)info.gui.screenshot);
    if (info.gui.thumbnail != nullptr && info.gui.thumbnail != nc)
        lilv_free((void*)info.gui.thumbnail);
    if (info.gui.brand != nullptr && info.gui.brand != nc)
        free((void*)info.gui.brand);
    if (info.gui.label != nullptr && info.gui.label != nc)
        free((void*)info.gui.label);
    if (info.gui.model != nullptr && info.gui.model != nc)
        free((void*)info.gui.model);
    if (info.gui.panel != nullptr && info.gui.panel != nc)
        free((void*)info.gui.panel);
    if (info.gui.color != nullptr && info.gui.color != nc)
        free((void*)info.gui.color);
    if (info.gui.knob != nullptr && info.gui.knob != nc)
        free((void*)info.gui.knob);

    if (info.bundles != nullptr)
    {
        for (int i=0; info.bundles[i]; ++i)
            free((void*)info.bundles[i]);
        delete[] info.bundles;
    }

    if (info.gui.ports != nullptr)
    {
        for (int i=0; info.gui.ports[i].valid; ++i)
            _clear_gui_port_info(info.gui.ports[i]);
        delete[] info.gui.ports;
    }

    if (info.ports.audio.input != nullptr)
    {
        for (int i=0; info.ports.audio.input[i].valid; ++i)
            _clear_port_info(info.ports.audio.input[i]);
        delete[] info.ports.audio.input;
    }
    if (info.ports.audio.output != nullptr)
    {
        for (int i=0; info.ports.audio.output[i].valid; ++i)
            _clear_port_info(info.ports.audio.output[i]);
        delete[] info.ports.audio.output;
    }
    if (info.ports.control.input != nullptr)
    {
        for (int i=0; info.ports.control.input[i].valid; ++i)
            _clear_port_info(info.ports.control.input[i]);
        delete[] info.ports.control.input;
    }
    if (info.ports.control.output != nullptr)
    {
        for (int i=0; info.ports.control.output[i].valid; ++i)
            _clear_port_info(info.ports.control.output[i]);
        delete[] info.ports.control.output;
    }
    if (info.ports.cv.input != nullptr)
    {
        for (int i=0; info.ports.cv.input[i].valid; ++i)
            _clear_port_info(info.ports.cv.input[i]);
        delete[] info.ports.cv.input;
    }
    if (info.ports.cv.output != nullptr)
    {
        for (int i=0; info.ports.cv.output[i].valid; ++i)
            _clear_port_info(info.ports.cv.output[i]);
        delete[] info.ports.cv.output;
    }
    if (info.ports.midi.input != nullptr)
    {
        for (int i=0; info.ports.midi.input[i].valid; ++i)
            _clear_port_info(info.ports.midi.input[i]);
        delete[] info.ports.midi.input;
    }
    if (info.ports.midi.output != nullptr)
    {
        for (int i=0; info.ports.midi.output[i].valid; ++i)
            _clear_port_info(info.ports.midi.output[i]);
        delete[] info.ports.midi.output;
    }

    if (info.presets != nullptr)
    {
        for (int i=0; info.presets[i].valid; ++i)
        {
            free((void*)info.presets[i].uri);
            free((void*)info.presets[i].label);
        }
        delete[] info.presets;
    }

    memset(&info, 0, sizeof(PluginInfo));
}

// --------------------------------------------------------------------------------------------------------

void init(void)
{
    lilv_world_free(W);
    W = lilv_world_new();
    lilv_world_load_all(W);
    _refresh();
}

void cleanup(void)
{
    if (_bundles_ret != nullptr)
    {
        for (int i=0; _bundles_ret[i] != nullptr; ++i)
            free((void*)_bundles_ret[i]);
        delete[] _bundles_ret;
        _bundles_ret = nullptr;
    }

    if (_plug_ret != nullptr)
    {
        delete[] _plug_ret;
        _plug_ret = nullptr;
    }

    _plug_lastsize = 0;

    for (auto& map : PLUGNFO)
    {
        PluginInfo& info = map.second;
        _clear_plugin_info(info);
    }

    BUNDLES.clear();
    PLUGNFO.clear();
    BUNDLED_PLUGINS.clear();

    lilv_world_free(W);
    W = nullptr;
}

// --------------------------------------------------------------------------------------------------------

const char* const* get_all_bundles(void)
{
    if (_bundles_ret != nullptr)
    {
        for (int i=0; _bundles_ret[i] != nullptr; ++i)
            free((void*)_bundles_ret[i]);
        delete[] _bundles_ret;
        _bundles_ret = nullptr;
    }

    size_t count = BUNDLES.size();
    _bundles_ret = new const char*[count+1];
    memset(_bundles_ret, 0, sizeof(const char*) * (count+1));

    count = 0;
    for (const std::string& b : BUNDLES)
        _bundles_ret[count++] = strdup(b.c_str());

    return _bundles_ret;
}

const PluginInfo* const* get_bundle_plugins(const char* bundle)
{
    size_t bundlepathsize;
    const char* const bundlepath_ = _get_safe_bundlepath(bundle, bundlepathsize);

    if (bundlepath_ == nullptr)
        return nullptr;

    const std::string bundlepath = bundlepath_;

    if (BUNDLED_PLUGINS.count(bundlepath) == 0)
        return nullptr;

    const std::stringlist& bundleplugins(BUNDLED_PLUGINS[bundlepath]);

    const size_t newsize = bundleplugins.size();

    if (newsize == 0)
    {
        if (_plug_ret != nullptr)
        {
            delete[] _plug_ret;
            _plug_ret = nullptr;
        }
        _plug_lastsize = 0;
        return nullptr;
    }

    if (newsize > _plug_lastsize)
    {
        _plug_lastsize = newsize;

        if (_plug_ret != nullptr)
            delete[] _plug_ret;

        _plug_ret = new const PluginInfo*[newsize+1];
        memset(_plug_ret, 0, sizeof(void*) * (newsize+1));
    }
    else if (newsize < _plug_lastsize)
    {
        memset(_plug_ret, 0, sizeof(void*) * (newsize+1));
    }

    const LilvPlugins* const plugins = lilv_world_get_all_plugins(W);
    const NamespaceDefinitions ns;
    size_t curIndex = 0;

    // Make a list of all installed bundles
    for (const std::string& uri : bundleplugins)
    {
        if (curIndex >= newsize)
            break;

        // check if it's already cached
        if (PLUGNFO.count(uri) > 0 && PLUGNFO[uri].valid)
        {
            _plug_ret[curIndex++] = &PLUGNFO[uri];
            continue;
        }

        // get new info
        if (LilvNode* const urinode = lilv_new_uri(W, uri.c_str()))
        {
            const LilvPlugin* const p = lilv_plugins_get_by_uri(plugins, urinode);
            lilv_node_free(urinode);

            const PluginInfo& info = _get_plugin_info(p, ns);

            if (! info.valid)
                continue;

            PLUGNFO[uri] = info;
            _plug_ret[curIndex++] = &PLUGNFO[uri];
        }
    }

    return _plug_ret;
}

const PluginInfo* get_plugin_info(const char* const uri_)
{
    const std::string uri = uri_;

    // check if it exists
    if (PLUGNFO.count(uri) == 0)
        return nullptr;

    // check if it's already cached
    if (PLUGNFO[uri].valid)
        return &PLUGNFO[uri];

    LilvNode* const urinode = lilv_new_uri(W, uri_);

    if (urinode == nullptr)
        return nullptr;

    const LilvPlugins* const plugins = lilv_world_get_all_plugins(W);
    const LilvPlugin* const p = lilv_plugins_get_by_uri(plugins, urinode);
    lilv_node_free(urinode);

    if (p != nullptr)
    {
        printf("NOTICE: Plugin '%s' was not (fully) cached, scanning it now...\n", uri_);
        const NamespaceDefinitions ns;
        PLUGNFO[uri] = _get_plugin_info(p, ns);
        return &PLUGNFO[uri];
    }

    return nullptr;
}

// --------------------------------------------------------------------------------------------------------
