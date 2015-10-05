options = { "gimp_image"    : "lata.xcf",
            "css_source"    : "lata.css.in",
            "css_dest"      : "../lata/lata.css",
            "borderx"       : 0,
            "bordery"       : 0,
            "chdir"         : "../",
            "color_prefix"  : "color_",
            "mask_prefix"   : "mask_",
            "export_suffix" : ".png" }

colors =  { "black"         : "white",
            "blue"          : "black",
            "brown"         : "white",
            "camouflage"    : "white",
            "cream"         : "black",
            "cyan"          : "black",
            "darkblue"      : "white",
            "gray"          : "black",
            "green"         : "white",
            "humphreys"     : "red",
            "none"          : "white",
            "orange"        : "black",
            "petrol"        : "white",
            "pink"          : "black",
            "purple"        : "white",
            "racing"        : "white",
            "red"           : "white",
            "white"         : "black",
            "yellow"        : "black" }
            
sizes = ( { "x" : 396, "y" : 514, "folder" : "lata" }, )

backgrounds_css = """.mod-pedal-lata{{{cns}}}.mod-<COLOR> { background-image:url(/resources/pedals/lata/<COLOR>.png{{{ns}}}); }
"""

colors_css = ( { "black" : """{
    background-image:url(/resources/utils/dropdown-arrow-black.png{{{ns}}});
}""",
             "white" : """{
    background-image:url(/resources/utils/dropdown-arrow-white.png{{{ns}}});
}""",
             "red" : """{
    background-image:url(/resources/utils/dropdown-arrow-white.png{{{ns}}});
}""",
             "identifier" : """.mod-pedal-lata{{{cns}}}.mod-<COLOR> .mod-enumerated""" },
             
           { "black" : """{
    color:black;
}""",
             "white" : """{
    color:white;
}""",
             "red" : """{
    color: white;
}""",
             "identifier" : """.mod-pedal-lata{{{cns}}}.mod-<COLOR> h1,
.mod-pedal-lata{{{cns}}}.mod-<COLOR> .mod-enumerated,
.mod-pedal-lata{{{cns}}}.mod-<COLOR> .mod-control-group .mod-knob > span.mod-knob-title""" },
            
           { "black" : """{
    border-color:black;
}""",
             "white" : """{
    border-color:white;
}""",
             "red" : """{
    border-color:white;
}""",
             "identifier" : """.mod-pedal-lata{{{cns}}}.mod-<COLOR> h1""" } )
