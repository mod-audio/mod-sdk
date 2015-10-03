backgrounds = """.mod-pedal-boxy{{{cns}}}.mod-<COLOR> {
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

colors = ( { "black" : """{
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
