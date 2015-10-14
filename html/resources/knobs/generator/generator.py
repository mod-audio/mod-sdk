#!/usr/bin/env python

"""
This generator creates knob image sprites from a Blender and a GIMP file.

Dependencies:
GIMP, Blender, ImageMagick

"""

import os
import sys
import imp
import getopt
import shutil
import tempfile
import gimp

def create_css (mod):
    with open (mod.options["css_source"], "r") as css_file:
        css_in=css_file.read()
    bg_str = ""
    for c in mod.colors:
        bg_str += mod.backgrounds_css.replace("<COLOR>", c)
    css_out = css_in.replace("<BACKGROUNDS>", bg_str);
    with open(mod.options["css_dest"], "w") as out_file:
        out_file.write(css_out.replace("<COLORS>", bg_str))
  
def create_layers (mod):
    tmp = tempfile.mkdtemp()
    O = mod.options
    for l in O["layers"]:
        trg = os.path.join(tmp, "%s%s" % (l['layer'], O["export_suffix"]))
        
        os.system("blender -b %s -t 7 -S %s -o %s/ -a" % (mod.options["blender_image"], l['scene'], tmp))
        os.system("convert %s/0* +append -background none %s" % (tmp, trg))
        
        exe = gimp.gimp_layer
        exe = exe.replace("<GIMP_IMAGE>",  O['gimp_image'])
        exe = exe.replace("<LAYER_NAME>",  l['layer'])
        exe = exe.replace("<LAYER_INDEX>", str(l['index']))
        exe = exe.replace("<LAYER_VISIBLE>", str(l['visible']))
        exe = exe.replace("<LAYER_SRC>",   trg)
        os.system(exe)
    shutil.rmtree(tmp, True)
        
    
def create_images (mod):
    # build colors array with all colors to generate
    cols = mod.colors.keys()
    overs = [ ]
    for c in mod.colors.keys():
        p = os.path.join(mod.options["chdir"], "%s%s" % (c, mod.options["export_suffix"]))
        if not force and os.path.isfile(p):
            cols.remove(c);
        else:
            overs += [ mod.colors[c], ]
    if not len(cols):
        print "Nothing to do."
        return
    op = mod.options["over_prefix"]
    mod.options["colors"] = "\"" + "\" \"".join(cols) + "\""
    mod.options["overlays"] = ("\"%s" % op) + ("\" \"%s" % op).join(overs) + "\""
    exe = gimp.gimp_color
    for r in mod.options:
        exe = exe.replace("<" + r.upper() + ">", str(mod.options[r]))
    os.system(exe)

def usage():
    print """Generator for backgrounds and CSS files of MOD stomp boxes.

USAGE:
    generator.py {-c | --css} {-i | --images} {-h | --help} TYPE [TYPE...]

OPTIONS:
    -b --blender
        Render Blender image and apply all scenes as layers to GIMP file
        
    -c --css
        Generate CSS file(s)
    
    -f --force
        Force re-generation of already existing backgrounds
    
    -h --help
        Show this help
        
    -i --images
        Generate background images from GIMP file

EXAMPLE:
    generator.py -c japanese
        Creates the CSS script for all japanese types
    
    generator.py -i -c japanese lata
        Creates CSS and background images for all japanese and lata types"""
        
if __name__ == '__main__':
    try:
        opts, args = getopt.getopt(sys.argv[1:], "cihfb", ["css", "images", "help", "force", "blender"])
    except getopt.GetoptError as err:
        print str(err)
        usage()
        sys.exit(2)
    css     = False
    images  = False
    blender = False
    force   = False
    if not len(opts) or not len(args):
        usage()
        exit(0)
    for o, a in opts:
        if o in ("-c", "--css"):
            css = True
        if o in ("-i", "--images"):
            images = True
        if o in ("-h", "--help"):
            usage()
            exit(0)
        if o in ("-f", "--force"):
            force = True
        if o in ("-b", "--blender"):
            blender = True
    for a in args:
        try:
            mod = imp.load_source(a, os.path.join("configs", "%s.py" % a))
        except:
            print "No module named %s" % a
            continue
        if (blender):
            print "Creating layers for %s..." % a
            create_layers(mod)
        if (images):
            print "Creating images for %s..." % a
            create_images(mod)
        if (css):
            print "Creating CSS for %s..." % a
            create_css(mod)
