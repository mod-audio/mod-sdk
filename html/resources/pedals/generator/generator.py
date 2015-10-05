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
import sys
import getopt
import gimp, css

def create_css (mod):
    with open (mod.options["css_source"], "r") as css_file:
        css_in=css_file.read()
    bg_str = ""
    for c in mod.colors:
        bg_str += mod.backgrounds_css.replace("<COLOR>", c)
    css_out = css_in.replace("<BACKGROUNDS>", bg_str);
    col_str = ""
    for cs in mod.colors_css:
        cols = { }
        for c in mod.colors:
            if not cs[mod.colors[c]]:
                continue
            if not mod.colors[c] in cols:
                cols[mod.colors[c]] = [ ];
            cols[mod.colors[c]] += [ cs["identifier"].replace("<COLOR>", c) ]
        for c in cols:
            col_str += ",\n".join(cols[c]) + "\n"
            col_str += cs[c] + "\n"
    with open(mod.options["css_dest"], "w") as out_file:
        out_file.write(css_out.replace("<COLORS>", col_str))
    
def run_gimp (mod):
    mod.options["colors"] = "\"" + "\" \"".join(mod.colors.keys()) + "\""
    mod.options["sizes"] = ""
    for s in range(0, len(mod.sizes)):
        mod.options["sizes"] += "\n(list (list %d %d) \"%s%s/\")" % (mod.sizes[s]["x"], mod.sizes[s]["y"], mod.options["chdir"], mod.sizes[s]["folder"])
    gimp_exec = gimp.gimp_exec
    for r in mod.options:
        gimp_exec = gimp_exec.replace("<" + r.upper() + ">", str(mod.options[r]))
    os.system(gimp_exec)
    
    
if __name__ == '__main__':
    try:
        opts, args = getopt.getopt(sys.argv[1:], "ci", ["css", "images"])
    except getopt.GetoptError as err:
        print str(err)
        usage()
        sys.exit(2)
    css = False
    images = False
    for o, a in opts:
        if o in ("-c", "--css"):
            css = True
        if o in ("-i", "--images"):
            images = True
    for a in args:
        try:
            mod = __import__(a)
        except:
            print "No module named %s" % a
            continue
        if (images):
            print "Creating images for %s..." % a
            run_gimp(mod)
        if (css):
            print "Creating CSS for %s..." % a
            create_css(mod)
