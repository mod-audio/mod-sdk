options = { "gimp_image"    : "sources/japanese.xcf",
            "css_source"    : "sources/japanese.css.in",
            "css_dest"      : "../japanese/japanese.css",
            "borderx"       : 0,
            "bordery"       : 0,
            "chdir"         : "../",
            "color_prefix"  : "color_",
            "mask_prefix"   : "mask_",
            "export_suffix" : ".png" }

colors =  { "black"         : "white",
            "blue"          : "white",
            "brown"         : "white",
            "cream"         : "white",
            "cyan"          : "white",
            "darkblue"      : "white",
            "gray"          : "white",
            "green"         : "white",
            "none"          : "white",
            "orange"        : "white",
            "petrol"        : "white",
            "pink"          : "white",
            "purple"        : "white",
            "racing"        : "white",
            "red"           : "white",
            "white"         : "black",
            "yellow"        : "white" }
            
sizes = ( { "x" : 274, "y" : 530, "folder" : "japanese" }, )

backgrounds_css = """.mod-pedal-japanese{{{cns}}}.mod-<COLOR> { background-image:url(/resources/pedals/japanese/<COLOR>.png{{{ns}}}); }
"""

colors_css = ( { "black" : """{
    background-image:url(/resources/utils/dropdown-arrow-white.png{{{ns}}});
}""",
                 "white" : """{
    background-image:url(/resources/utils/dropdown-arrow-white.png{{{ns}}});
}""",
             "identifier" : """.mod-pedal-japanese{{{cns}}}.mod-<COLOR> .mod-enumerated""" },
             
           { "white" : """{
    color:white;
}""",
             "black" : """{
    color:#7F7F7F;
}""",
             "identifier" : """.mod-pedal-japanese{{{cns}}}.mod-<COLOR> .mod-plugin-name h1,
.mod-pedal-japanese{{{cns}}}.mod-<COLOR> .mod-enumerated,
.mod-pedal-japanese{{{cns}}}.mod-<COLOR> .mod-control-group .mod-knob > span.mod-knob-title""" } )
