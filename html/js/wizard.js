var wizard_db // populated in index.html
$(document).ready(function() {
    var wizard = $('#wizard-window')
    wizard.wizard(wizard_db)

    $('#wizard').click(function() {
        wizard.wizard('open')
    })
})

JqueryClass('wizard', {
    init: function(models) {
        var self = $(this)

        self.find('#wizard-cancel').click(function() { self.wizard('close') })
        self.find('#wizard-next').click(function() { self.wizard('next') })
        self.find('#wizard-previous').click(function() { self.wizard('previous') })
        self.find('#wizard-generate-thumbnail').click(function() { self.wizard('generate_thumbnail') })
        self.find('#wizard-skip-thumbnail').click(function() { self.wizard('next') })

        var model_list = Object.keys(models).sort()
        self.data('model_index', models)
        self.data('model_list', model_list)

        self.find('.previous').click(function() { self.wizard('shiftModel', -1) })
        self.find('.next').click(function() { self.wizard('shiftModel', 1) })

        self.data('model', model_list[0])
        self.data('color', null)
        self.data('panel', null)
        self.data('knob', null)
        self.data('brand', 'brand')
        self.data('label', 'Label here')
        self.data('uri', null)
        self.data('controls', null)
    },

    open: function() {
        var self = $(this)
        var effect = effects.find('option:selected').data()

        self.data('effect', effect)
        self.data('label', effect.name)

        if (effect.gui.model)
            self.data('model', effect.gui.model)
        if (effect.gui.color)
            self.data('color', effect.gui.color)
        if (effect.gui.panel)
            self.data('panel', effect.gui.panel)
        if (effect.gui.knob)
            self.data('knob', effect.gui.knob)

        if (effect.gui.brand)
            self.data('brand', effect.gui.brand)
        else
            self.data('brand', effect.brand)

        if (effect.gui.label)
            self.data('label', effect.gui.label)
        else
            self.data('label', effect.label)

        if (effect.gui.ports)
            self.data('controls', effect.gui.ports)
        else if (self.data('uri') != effect.uri)
            self.data('controls', null)

        var resDir = effect.gui.resourcesDirectory
                   ? effect.gui.resourcesDirectory.split('/').filter(function(i){return i.length != 0}).reverse()[0]
                   : "modgui"

        self.data('resourcesDir', resDir)
        self.data('uri', effect.uri)

        self.show()
        self.wizard('step', 0)
    },

    close: function() {
        $(this).hide()
    },

    step: function(step) {
        var self = $(this)
        var steps = [
            'chooseModel',
            'configure',
            'save_template',
            'finish'
        ]

        if (step < 0 || step >= steps.length)
            return

        self.find('.step').hide()
        self.find('#wizard-step-'+step).show()
        self.data('step', step)

        if (step == 0)
            self.find('#wizard-previous').hide()
        else
            self.find('#wizard-previous').show()

        if (step == steps.length-1)
            self.find('#wizard-next').hide()
        else
            self.find('#wizard-next').show()

        self.find('#wizard-next').text((step == steps.length-2) ? "Finish" : "Next")

        self.wizard(steps[step])
    },

    next: function() {
        var self = $(this)
        if (self.data('allowNext'))
            self.wizard('step', self.data('step') + 1)
        else
            alert('Please give all information in this step first')
    },

    previous: function() {
        var self = $(this)
        self.wizard('step', self.data('step') - 1)
    },

    ok: function(ok) {
        var self = $(this)
        self.data('allowNext', ok)
    },

    shiftModel: function(diff) {
        var self = $(this)
        var model = self.data('model')
        var models = self.data('model_list')
        var i = models.indexOf(model)
        self.wizard('chooseModel', i+diff)
    },

    chooseModel: function(i) {
        var self = $(this)
        var list = self.data('model_list')
        var len = list.length;
        var model
        if (i == null) {
            model = self.data('model')
            i = list.indexOf(model)
        } else {
            i = (i + len) % len
            model = list[i]
            self.data('model', model)
            self.data('color', null)
            self.data('panel', null)
            self.data('knob', null)
        }

        self.find('#model-choice h3').html(model)

        var factory

        var data = self.data('model_index')[model]
        var colorCanvas = self.find('#color-options')
        colorCanvas.html('')

        var colors
        if (data.colors) {
            colors = data.colors.sort()
            factory = function(color) {
                return function() {
                    colorCanvas.find('.selected').removeClass('selected')
                    $(this).addClass('selected')
                    self.data('color', color)
                    self.wizard('render')
                }
            }
            for (var j in colors) {
                var img = $('<img>')
                img.attr('src', '/resources/pedals/'+model+'/'+colors[j]+'.png')
                img.height(64)
                img.click(factory(colors[j]))
                if (colors[j] == self.data('color'))
                    img.addClass('selected')
                img.appendTo(colorCanvas)
            }
            $('#color-select-title').show()
        } else {
            $('#color-select-title').hide()
        }

        var panelCanvas = self.find('#panel-options')
        panelCanvas.html('')
        var panels = Object.keys(data.panels).sort()
        factory = function(panel) {
            return function() {
                panelCanvas.find('.selected').removeClass('selected')
                $(this).addClass('selected')
                self.data('panel', panel)
                self.data('controls', null)
                self.wizard('render')
            }
        }
        for (var j in panels) {
            var li = $('<li>')
            li.html(panels[j].replace(/-/, ' '))
            li.click(factory(panels[j]))
            if (panels[j] == self.data('panel'))
                li.addClass('selected')
            li.appendTo(panelCanvas)
        }

        var knobs = data.knobs
        if (!knobs) {
            self.find('#knob-choice').hide()
            self.wizard('render')
            return
        }
        knobs = knobs.sort()
        self.find('#knob-choice').show()

        var knobCanvas = self.find('#knob-options')
        knobCanvas.html('')
        factory = function(knob) {
            return function() {
                knobCanvas.find('.selected').removeClass('selected')
                $(this).addClass('selected')
                self.data('knob', knob)
                self.wizard('render')
            }
        }
        var height = 64
        var width = height * (data.knobProportion || 1)
        for (var j in knobs) {
            var div = $('<div>')
            div.css('backgroundImage', 'url('+ '/resources/knobs/'+model+'/'+knobs[j]+'.png)')
            div.height(height)
            div.width(width)
            div.css('backgroundSize', 'auto '+height+'px')
            div.css('backgroundRepeat', 'no-repeat')
            div.click(factory(knobs[j]))
            if (knobs[j] == self.data('knob'))
                div.addClass('selected')
            div.appendTo(knobCanvas)
        }

        self.wizard('render')
    },

    chooseColor: function(color) {
        var self = $(this)
    },

    choosePanel: function(panel) {
        var self = $(this)
    },

    render: function() {
        var self   = $(this)
        var effect = self.data('effect')
        var model  = self.data('model')
        var panel  = self.data('panel')
        var db     = self.data('model_index')

        var step = self.data('step')
        var icon = self.find('.wizard-icon')
        icon.html('')

        var ok = true
        ok = ok && panel
        ok = ok && (self.data('color') || !db[model].colors)
        ok = ok && (self.data('knob') || !db[model].knobs)

        self.wizard('ok', ok)

        if (!ok)
            return

        effect.gui = {
            templateData: self.wizard('getTemplateData'),
            iconTemplate: self.wizard('getIconTemplate'),
        }

        effopts = {
            bypassed: false,
            loadDependencies: false,
        }
        new GUI(effect, effopts).render(null, function(iconElement) { iconElement.appendTo(icon) }, true)
    },

    getIconTemplate: function() {
        return TEMPLATES['pedal-' + $(this).data('model') + '-' + $(this).data('panel')]
    },

    getTemplateData: function() {
        var self  = $(this)
        var color = self.data('color')
        var knob  = self.data('knob')
        var model = self.data('model')
        var panel = self.data('panel')

        var controls = self.data('controls')
        var effect   = self.data('effect')

        var controlsWasNull = false

        if (!controls) {
            var db    = self.data('model_index')
            var limit = db[model].panels[panel]

            controls = []
            controlsWasNull = true

            for (var i in effect.ports.control.input)
            {
                port = effect.ports.control.input[i]
                if (shouldSkipPort(port))
                    continue
                controls.push(port)
                if (controls.length == limit)
                    break
            }
        }

        var data = {
            effect  : $.extend({ gui: null }, effect),
            brand   : self.data('brand'),
            label   : self.data('label'),
            model   : model,
            panel   : panel,
            controls: [],
        }

        if (color)
            data.color = color
        if (knob)
            data.knob = knob

        for (var i in controls) {
            var control = controls[i]
            if (!control)
                continue
            data.controls.push({
                name  : control.name,
                symbol: control.symbol
            })
        }

        if (controlsWasNull)
            self.data('controls', data.controls)

        return data
    },

    configure: function() {
        var self     = $(this)
        var effect   = self.data('effect')
        var brand    = self.data('brand')
        var label    = self.data('label')
        var panel    = self.data('panel')
        var controls = self.data('controls')
        var db       = self.data('model_index')

        /*if (!controls) {
            controls = effect.ports.control.input.slice(0, db[self.data('model')].panels[panel])
            self.data('controls', controls)
        }*/

        var max = self.data('model_index')[self.data('model')]['panels'][panel]

        var brandInput = self.find('input[name=brand]')
        var labelInput = self.find('input[name=label]')

        brandInput.val(brand)
        labelInput.val(label)

        var control
        var controlPorts = effect.ports.control.input
        var select = $('<select>')
        $('<option>').val('').html('-- Select control --').appendTo(select)
        var controlIndex = {}
        for (var i in controlPorts) {
            control = controlPorts[i]
            if (shouldSkipPort(control))
                continue
            controlIndex[control.symbol] = control
            $('<option>').val(control.symbol).html(control.name).appendTo(select)
        }

        var factoryNam = function(nam, i) {
            return function() {
                console.log("name changed from '" + controls[i].name +"' to '"+ nam.val())
                controls[i].name = nam.val()
                self.wizard('render')
            }
        }
        var factorySel = function(sel, nam, i) {
            return function() {
                controls[i] = controlIndex[sel.val()]
                nam.val(controls[i] ? controls[i].name : "")
                self.wizard('render')
            }
        }

        var sel, nam, symbol
        $('#pedal-buttons').html('')
        for (var i=0; i<max && i < controls.length; i++) {
            symbol = controls[i].symbol

            nam = $('<input name="'+symbol+'" type="text">')
            nam.val(controls[i].name)
            nam.keyup(factoryNam(nam, i))

            sel = select.clone()
            sel.val(symbol)
            sel.change(factorySel(sel, nam, i))

            $('#pedal-buttons').append(sel).append(nam)
        }

        brandInput.keyup(function() {
            self.data('brand', brandInput.val())
            self.wizard('render')
        })
        labelInput.keyup(function() {
            self.data('label', labelInput.val())
            self.wizard('render')
        })

        self.wizard('render')
    },

    slug: function() {
        return $(this).data('effect')['name'].toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '').replace(/-+/g, '-')
    },

    save_template: function() {
        var self   = $(this)
        var effect = self.data('effect')
        var slug   = self.wizard('slug')
        var resDir = self.data('resourcesDir')

        var templateData = self.wizard('getTemplateData')
        //delete templateData.effect

        //var settingsTemplate = Mustache.render(defaultSettingsTemplate, templateData)

        var ttlText = ''
        ttlText += '@prefix modgui: <http://moddevices.com/ns/modgui#> .\n'
        ttlText += '@prefix lv2:    <http://lv2plug.in/ns/lv2core#> .\n'
        //ttlText += '@prefix ui:     <http://lv2plug.in/ns/extensions/ui#> .\n'
        ttlText += '\n'
        ttlText += '<' + effect.uri + '>\n'
        //ttlText += '    ui:ui modgui:X11UI ;\n'
        ttlText += '    modgui:gui [\n'
        ttlText += '        modgui:resourcesDirectory <'+resDir+'> ;\n'
        ttlText += '        modgui:iconTemplate <'+resDir+'/icon-'+slug+'.html> ;\n'
        //ttlText += '        modgui:settingsTemplate <'+resDir+'/settings-'+slug+'.html> ;\n'
        ttlText += '        modgui:stylesheet <'+resDir+'/stylesheet-'+slug+'.css> ;\n'
        ttlText += '        modgui:screenshot <'+resDir+'/screenshot-'+slug+'.png> ;\n'
        ttlText += '        modgui:thumbnail <'+resDir+'/thumbnail-'+slug+'.png> ;\n'
        ttlText += '        modgui:brand "'+templateData.brand+'" ;\n'
        ttlText += '        modgui:label "'+templateData.label+'" ;\n'
        ttlText += '        modgui:model "'+templateData.model+'" ;\n'
        ttlText += '        modgui:panel "'+templateData.panel+'" ;\n'

        if (templateData.color)
            ttlText += '        modgui:color "'+templateData.color+'" ;\n'

        if (templateData.knob)
            ttlText += '        modgui:knob "'+templateData.knob+'" ;\n'

        var i = 0
        var numControls = templateData.controls.length
        for (var j in templateData.controls)
        {
            control = templateData.controls[j]

            if (i == 0)
                ttlText += '        modgui:port [\n'

            ttlText += '            lv2:index '+i+' ;\n'
            ttlText += '            lv2:symbol "'+control.symbol+'" ;\n'
            ttlText += '            lv2:name "'+control.name+'" ;\n'

            if (i+1 == numControls)
                ttlText += '        ] ;\n'
            else
                ttlText += '        ] , [\n'

            i += 1;
        }

        ttlText += '    ] .\n'
        ttlText += '\n'

        filesToCopy = []

        var model = templateData.model

        if (model == "boxy")
        {
            var suffix, panel = templateData.panel

            filesToCopy.push('pedals/boxy/boxy.css')
            filesToCopy.push('knobs/boxy/boxy.css')
            filesToCopy.push('pedals/footswitch.png')

            // TODO: selected copy of white, black or no arrows
            filesToCopy.push('utils/dropdown-arrow-black.png')
            filesToCopy.push('utils/dropdown-arrow-white.png')

            if (panel.indexOf("knob") >= 0) {
                filesToCopy.push('knobs/boxy/'+templateData.knob+'.png')
            }
            if (panel.indexOf("slider") >= 0) {
                filesToCopy.push('pedals/slider.png')
            }

            if (panel == "12-sliders")
                suffix = '100'
            //else if (panel == "10-sliders")
            //    suffix = '85'
            else if (panel == "9-sliders" || panel == "8-sliders" || panel == "7-sliders")
                suffix = '75'
            else if (panel == "8-knobs" || panel == "7-knobs")
                suffix = '75'
            else
                suffix = ''

            filesToCopy.push('pedals/boxy'+suffix+'/'+templateData.color+'.png')
        }
        else if (model == "boxy-small")
        {
            filesToCopy.push('pedals/boxy/boxy.css')
            filesToCopy.push('pedals/boxy-small/'+templateData.color+'.png')
            filesToCopy.push('pedals/footswitch.png')
        }
        else if (model == "japanese")
        {
            filesToCopy.push('pedals/japanese/japanese.css')
            filesToCopy.push('pedals/japanese/'+templateData.color+'.png')

            filesToCopy.push('knobs/japanese/japanese.css')
            filesToCopy.push('knobs/japanese/'+templateData.knob+'.png')
        }
        else if (model == "lata")
        {
            filesToCopy.push('pedals/lata/lata.css')
            filesToCopy.push('pedals/lata/'+templateData.color+'.png')
            filesToCopy.push('pedals/footswitch.png')

            filesToCopy.push('knobs/lata/lata.css')
            filesToCopy.push('knobs/lata/lata.png')
        }
        else if (model == "british")
        {
            filesToCopy.push('pedals/british/british.css')
            filesToCopy.push('pedals/british/'+templateData.color+'.png')
            filesToCopy.push('pedals/footswitch.png')
            filesToCopy.push('knobs/british/british.png')
        }
        else if (model == "head-model-001")
        {
            filesToCopy.push('heads/model-001/model-001.css')
            filesToCopy.push('heads/model-001/model-'+templateData.panel+'.png')
            filesToCopy.push('switches/switch-001.png')
            filesToCopy.push('knobs/chicken-head/_strip.png')
        }
        if (model == "combo-model-001")
        {
            filesToCopy.push('combos/model-001/model-001.css')
            filesToCopy.push('combos/model-001/model-'+templateData.panel+'.png')
            filesToCopy.push('switches/switch-001.png')
            filesToCopy.push('knobs/chicken-head/_strip.png')
            filesToCopy.push('utils/dropdown-arrow-white.png')
        }
        else if (model == "rack")
        {
            filesToCopy.push('racks/model-001/model-001.css')
            filesToCopy.push('racks/model-001/model-001.png')
            filesToCopy.push('switches/switch-001.png')
            filesToCopy.push('knobs/chicken-head/_strip.png')
            filesToCopy.push('utils/dropdown-arrow-white.png')
        }

        $.ajax({
            url: '/effect/save',
            type: 'POST',
            data: {
                uri: effect.uri,
                ttlText: ttlText,
                filesToCopy: JSON.stringify(filesToCopy),
                iconTemplateData: self.wizard('getIconTemplate'),
                iconTemplateFile: 'icon-'+slug+'.html',
                stylesheetFile: 'stylesheet-'+slug+'.css',
            },
            success: function() {
                //self.wizard('generate_thumbnail')
            },
            error: function() {
                self.wizard('previous')
                alert("Error: Can't save your effect configuration. Is your server running? Check the logs.")
            },
            dataType: 'json'
        })
    },

    generate_thumbnail: function() {
        var self   = $(this)
        var effect = self.data('effect')
        var icon   = $(self.find('.wizard-icon').children()[0])

        var canvas = self.find('#wizard-thumbnail')
        canvas.html('')

        $.ajax({
            url: '/screenshot',
            data: {
                uri   : effect.uri,
                width : icon.width(),
                height: icon.height(),
            },
            success: function(result) {
                if (result.ok) {
                    $('<img class="screenshot">').appendTo(canvas).attr('src', 'data:image/png;base64,'+result.screenshot)
                } else {
                    alert('Could not generate thumbnail')
                }
            },
            error: function(resp) {
                alert("Error: Can't generate thumbnail. Is your server running? Check the logs.")
            },
            dataType: 'json'
        })
    },

    finish: function() {
        document.location.reload()
    }
})
