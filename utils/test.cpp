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

#ifndef DEBUG
#define DEBUG
#endif

#include "utils.h"

#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

void scanPlugins()
{
    if (const char* const* const bundles = get_all_bundles())
    {
        for (int i=0; bundles[i] != nullptr; ++i)
        {
            if (const PluginInfo* const* const plugins = get_bundle_plugins(bundles[i]))
            {
                for (int j=0; plugins[j] != nullptr; ++j)
                {
                    if (! plugins[j]->valid)
                    {
                        printf("Invalid plugin found\n");
                        break;
                    }

                    assert(get_plugin_info(plugins[j]->uri) != nullptr);
                }
            }
            else
            {
                printf("null bundle found\n");
                break;
            }
        }
    }
}

int main()
{
    init();
    scanPlugins();
    cleanup();

    return 0;
}
