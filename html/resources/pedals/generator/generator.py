#!/usr/bin/env python

# This generator takes a special GIMP file and generates different
# PNG images from it.
# The source must contain some hidden layers with a special prefix in
# their name. The script loops over those layers taking the following
# actions:
#     * layer is set to visible
#     * all visible layers are merged
#     * the result together with two (hidden) b/w masks are copied to new image
#     * the result gets resized the following way (e.g. horizontal):
#         * the base layer is copied and a mask is applied
#         * the base layer gets cropped by the necessary amount of pixels
#           plus borderx from the right
#         * the masked copy is translated by the necessary amount of pixels
#           to the left
#         * the masked copy is merged onto the base layer
#         * the masks are deleted
#         * the image is exported to its final destination as PNG

import os

import boxy, gimp



def create_css (options, colors, sizes):
    1

def run_gimp (options, colors, sizes, gimp_exec):
    options["colors"] = "\"" + "\" \"".join(colors) + "\""
    options["sizes"] = ""
    for s in range(0, len(sizes)):
        options["sizes"] += "\n(list (list %d %d) \"%s%s/\")" % (sizes[s]["x"], sizes[s]["y"], options["chdir"], sizes[s]["folder"])
    for r in options:
        gimp_exec = gimp_exec.replace("<" + r.upper() + ">", str(options[r]))
    os.system(gimp_exec)
    
    
if __name__ == '__main__':
    run_gimp(boxy.options, boxy.colors, boxy.sizes, gimp.gimp_exec)
    create_css(boxy.options, boxy.colors, boxy.sizes)
    exit(0)
