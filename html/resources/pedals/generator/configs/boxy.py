options = { "gimp_image"    : "sources/boxy.xcf",
            "css_source"    : "sources/boxy.css.in",
            "css_dest"      : "../boxy/boxy.css",
            "borderx"       : 12,
            "bordery"       : 29,
            "chdir"         : "../",
            "color_prefix"  : "color_",
            "mask_prefix"   : "mask_",
            "export_suffix" : ".png" }

colors =  { "black"         : "white",
            "blue"          : "black",
            "brown"         : "white",
            "cream"         : "black",
            "cyan"          : "black",
            "darkblue"      : "white",
            "dots"          : "black",
            "flowerpower"   : "white",
            "gold"          : "black",
            "gray"          : "white",
            "green"         : "white",
            "lava"          : "white",
            "none"          : "white",
            "orange"        : "black",
            "petrol"        : "white",
            "pink"          : "black",
            "purple"        : "white",
            "racing"        : "white",
            "red"           : "white",
            "slime"         : "black",
            "tribal1"       : "black",
            "tribal2"       : "white",
            "warning"       : "white",
            "white"         : "black",
            "wood0"         : "black",
            "wood1"         : "black",
            "wood2"         : "white",
            "wood3"         : "white",
            "wood4"         : "white",
            "yellow"        : "black",
            "zinc"          : "black" }
            
sizes = ( { "x" : 230, "y" : 431, "folder" : "boxy" },
          { "x" : 326, "y" : 431, "folder" : "boxy75" },
          { "x" : 364, "y" : 431, "folder" : "boxy85" },
          { "x" : 421, "y" : 431, "folder" : "boxy100" },
          { "x" : 301, "y" : 315, "folder" : "boxy-small" } )

backgrounds_css = """.mod-pedal-boxy{{{cns}}}.mod-<COLOR> {
    background-image:url(/resources/pedals/boxy/<COLOR>.png{{{ns}}});
}
.mod-pedal-boxy{{{cns}}}.mod-boxy50.mod-<COLOR> {
    background-image:url(/resources/pedals/boxy-small/<COLOR>.png{{{ns}}});
}
.mod-pedal-boxy{{{cns}}}.mod-boxy75.mod-<COLOR> {
    background-image:url(/resources/pedals/boxy75/<COLOR>.png{{{ns}}});
}
.mod-pedal-boxy{{{cns}}}.mod-boxy85.mod-<COLOR> {
    background-image:url(/resources/pedals/boxy85/<COLOR>.png{{{ns}}});
}
.mod-pedal-boxy{{{cns}}}.mod-boxy100.mod-<COLOR> {
    background-image:url(/resources/pedals/boxy100/<COLOR>.png{{{ns}}});
}
"""

colors_css = ( { "black" : """{
    background-image:url(/resources/utils/dropdown-arrow-black.png{{{ns}}});
}""",
             "white" : """{
    background-image:url(/resources/utils/dropdown-arrow-white.png{{{ns}}});
}""",
             "identifier" : """.mod-pedal-boxy{{{cns}}}.mod-<COLOR> .mod-enumerated""" },
             
           { "black" : """{
    color:black;
}""",
             "white" : """{
    color:white;
}""",
             "identifier" : """.mod-pedal-boxy{{{cns}}}.mod-<COLOR> h1,
.mod-pedal-boxy{{{cns}}}.mod-<COLOR> .mod-enumerated,
.mod-pedal-boxy{{{cns}}}.mod-<COLOR> .mod-control-group .mod-knob > span.mod-knob-title""" },
            
           { "black" : """{
    border-color:black;
}""",
             "white" : """{
    border-color:white;
}""",
             "identifier" : """.mod-pedal-boxy{{{cns}}}.mod-<COLOR> h1""" } )
