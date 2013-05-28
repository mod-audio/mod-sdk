var wizard_db // populated in index.html
$(document).ready(function() {
    var wizard = $('#wizard-window')
    wizard.wizard(wizard_db)
    $('#wizard').click(function() { wizard.wizard('open') })
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
	self.data('label', 'Label here')
	self.data('author', 'brand')
    },

    open: function() {
	var self = $(this)
	var effect = effects.find('option:selected').data()

	self.data('effect', effect)
	self.data('label', effect.name)

	if (effect.gui.templateData) {
	    var data = effect.gui.templateData
	    if (data.label)
		self.data('label', data.label)
	    if (data.author)
		self.data('author', data.author)
	}

	self.show()
	self.wizard('step', 0)
    },

    close: function() {
	$(this).hide()
    },
    
    step: function(step) {
	var self = $(this)
	var steps = [ 'chooseModel',
		      'configure',
		      'edit_ttl',
		      'save_template',
		      'docs',
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
	var self = $(this)
	var effect = self.data('effect')
	var model = self.data('model')
	var panel = self.data('panel')
	var db = self.data('model_index')

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

	var template = self.wizard('getTemplate')
	var templateData = self.wizard('getTemplateData')
	effect.gui = {
	    template: template,
	    templateData: templateData,
	}
	new GUI(effect).renderIcon(template).appendTo(icon)
    },

    getTemplate: function() {
	return TEMPLATES['pedal-' + $(this).data('model') + '-' + $(this).data('panel')]
    },

    getTemplateData: function() {
	var self = $(this)
	var color = self.data('color')
	var knob = self.data('knob')

	var controls = self.data('controls')

	if (!controls) {
	    var db = self.data('model_index')
	    var effect = self.data('effect')
	    var model = self.data('model')
	    var panel = self.data('panel')
	    controls =  effect.ports.control.input.slice(0, db[model].panels[panel])
	}

	var data =  {
	    label: self.data('label'),
	    author: self.data('author'),
	    controls: []
	}

	if (color)
	    data.color = color
	if (knob)
	    data.knob = knob

	for (var i in controls) {
	    var control = controls[i]
	    data.controls.push({
		name: control.name,
		symbol: control.symbol
	    })
	}

	return data	
    },

    configure: function() {
	var self = $(this)
	var effect = self.data('effect')
	var label = self.data('label')
	var author = self.data('author')
	var panel = self.data('panel')
	var controls = self.data('controls')
	var db = self.data('model_index')

	var i
	if (!controls) {
	    controls = effect.ports.control.input.slice(0, db[self.data('model')].panels[panel])
	    self.data('controls', controls)
	}

	var max = self.data('model_index')[self.data('model')]['panels'][panel]

	var labelInput = self.find('input[name=label]')
	var authorInput = self.find('input[name=author]')

	labelInput.val(label)
	authorInput.val(author)

	var control
	var controlPorts = effect.ports.control.input
	var select = $('<select>')
	$('<option>').val('').html('-- Select control --').appendTo(select)
	var controlIndex = {}
	for (i in controlPorts) {
	    control = controlPorts[i]
	    controlIndex[control.symbol] = control
	    $('<option>').val(control.symbol).html(control.name).appendTo(select)
	}

	var factory = function(sel, i) {
	    return function() {
		controls[i] = controlIndex[sel.val()]
		self.wizard('render')
	    }
	}
	var sel
	$('#pedal-buttons').html('')
	for (i=0; i<max && i < controls.length; i++) {
	    sel = select.clone()
	    sel.val(controls[i].symbol || controls[i])
	    sel.change(factory(sel, i))
	    $('#pedal-buttons').append(sel)
	}

	labelInput.keyup(function() {
	    self.data('label', labelInput.val())
	    self.wizard('render')
	})
	authorInput.keyup(function() {
	    self.data('author', authorInput.val())
	    self.wizard('render')
	})

	self.wizard('render')
    },

    slug: function() {
	return $(this).data('effect')['name'].toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '').replace(/-+/g, '-')
    },
    
    edit_ttl: function() {
	var self = $(this)
	var effect = self.data('effect')
	var label = self.data('label')
	var author = self.data('author')
	var model = self.data('model')
	var panel = self.data('panel')
	var controls = self.data('controls')
	var db = self.data('model_index')

	var slug = self.wizard('slug')

	var canvas = $('#ttl-body')
	canvas.text('')
	canvas.append('    mod:gui [\n')
	canvas.append('        a mod:Gui;\n')
	canvas.append('        mod:resourcesDirectory &lt;modgui&gt;;\n')
	canvas.append('        mod:iconTemplate &lt;modgui/'+slug+'.html&gt;;\n')
	canvas.append('        mod:templateData &lt;modgui/data-'+slug+'.json&gt;;\n')
	canvas.append('        mod:screenshot &lt;modgui/screenshot-'+slug+'.png&gt;;\n')
	canvas.append('        mod:thumbnail &lt;modgui/thumb-'+slug+'.png&gt;;\n')
	canvas.append('    ].')
    },

    save_template: function() {
	var self = $(this)
	var data = {
	    slug: self.wizard('slug'),
	    data: self.wizard('getTemplateData'),
	    template: self.wizard('getTemplate')	    
	}
	$.ajax({ url: '/effect/save/' + self.data('effect').package,
		 type: 'POST',
		 data: JSON.stringify(data),
		 success: function() {
		     //self.wizard('generate_thumbnail')
		 },
		 error: function() {
		     self.wizard('previous')
		     alert("Error: Can't save your effect configuration. Is your server running? Check the logs.")
		 }
	       })
    },

    generate_thumbnail: function() {
	var self = $(this)
	var effect = self.data('effect')
	var icon = $(self.find('.wizard-icon').children()[0])
	
	var canvas = self.find('#wizard-thumbnail')
	canvas.html('')

	var param = { bundle: effect['package'],
		      effect: effect.url,
		      width: icon.width(),
		      height: icon.height(),
		      slug: self.wizard('slug')
		    }

	$.ajax({ url: '/screenshot',
		 data: param,
		 success: function(result) {
		     if (result.ok) {
			 var img = $('<img class="screenshot">').appendTo(canvas).attr('src', 'data:image/png;base64,'+result.screenshot)
		     } else {
			 alert('Could not generate thumbnail')
		     }
		 },
		 error: function(resp) {
		     alert("Error: Can't generate thumbnail. Is your server running? Check the logs.")
		 }
	       })
    },

    docs: function() {
	var self = $(this)
	var effect = self.data('effect')
	var model = self.data('model')
	var panel = self.data('panel')
	var canvas = $('#wizard-modifications')
	var slug = self.wizard('slug')
	$('<li>').html('modgui/'+slug+'.html').appendTo(canvas)
 	$('<li>').html('modgui/data-'+slug+'.json').appendTo(canvas)
 	$('<li>').html('modgui/screenshot-'+slug+'.png').appendTo(canvas)
 	$('<li>').html('modgui/thumb-'+slug+'.png').appendTo(canvas)
    },

    finish: function() {
	document.location.reload()
    }

})
