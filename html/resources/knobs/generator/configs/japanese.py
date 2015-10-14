options = { "type"          : "japanese",
            
            "gimp_image"    : "sources/japanese.xcf",
            "blender_image" : "sources/japanese.blend",
            "layers"        : [
                                  { "scene" : "Knob",  "index" : 1000, "visible" : 1, "layer" : "knob" },
                                  { "scene" : "Mask",  "index" : 1001, "visible" : 0, "layer" : "mask" },
                                  { "scene" : "Black", "index" :    0, "visible" : 0, "layer" : "over_black" },
                                  { "scene" : "White", "index" :    0, "visible" : 0, "layer" : "over_white" } ],
            
            "css_source"    : "sources/japanese.css.in",
            "css_dest"      : "../japanese/japanese.css",
            
            "chdir"         : "../japanese",
            
            "color_prefix"  : "color_",
            "over_prefix"   : "over_",
            "mask_layer"    : "mask",
            "export_suffix" : ".png" }

colors =  { "black"         : "white",
            "blue"          : "white",
            "brown"         : "white",
            "cream"         : "black",
            "cyan"          : "black",
            "darkblue"      : "white",
            "gray"          : "black",
            "green"         : "black",
            "none"          : "black",
            "orange"        : "black",
            "petrol"        : "white",
            "pink"          : "black",
            "purple"        : "white",
            "racing"        : "white",
            "red"           : "black",
            "white"         : "black",
            "yellow"        : "black" }
            
backgrounds_css = """.mod-pedal-japanese{{{cns}}} .mod-control-group.mod-<COLOR> .mod-knob .mod-knob-image {
    background-image:url(/resources/knobs/japanese/<COLOR>.png{{{ns}}});
}"""
