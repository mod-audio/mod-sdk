options = { "type"          : "boxy",
            
            "gimp_image"    : "sources/boxy.xcf",
            "blender_image" : "sources/boxy.blend",
            "layers"        : [
                                  { "scene" : "Knob",  "index" : 1000, "visible" : 1, "layer" : "knob" },
                                  { "scene" : "Mask",  "index" : 1001, "visible" : 0, "layer" : "mask" },
                                  { "scene" : "Black", "index" :    0, "visible" : 0, "layer" : "over_black" },
                                  { "scene" : "White", "index" :    0, "visible" : 0, "layer" : "over_white" } ],
            
            "css_source"    : "sources/boxy.css.in",
            "css_dest"      : "../boxy/boxy.css",
            
            "chdir"         : "../boxy",
            
            "color_prefix"  : "color_",
            "over_prefix"   : "over_",
            "mask_layer"    : "mask",
            "export_suffix" : ".png" }

colors =  { "aluminium"     : "black",
            "black"         : "white",
            "blue"          : "white",
            "bronze"        : "black",
            "copper"        : "black",
            "gold"          : "black",
            "green"         : "black",
            "silver"        : "black",
            "steel"         : "black",
            "petrol"        : "white",
            "purple"        : "black" }

backgrounds_css = """.mod-pedal-boxy{{{cns}}} .mod-control-group.mod-<COLOR> .mod-knob .mod-knob-image {
    background-image:url(/resources/knobs/boxy/<COLOR>.png{{{ns}}});
}"""
