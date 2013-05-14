var wizard_db // populated in index.html
$(document).ready(function() {
    var wizard = $('#wizard-window')
    wizard.wizard(wizard_db)
    $('#wizard').click(function() { wizard.wizard('open') })
    $('#wizard-cancel').click(function() { wizard.wizard('close') })
    $('#wizard-next').click(function() { wizard.wizard('next') })
    $('#wizard-previous').click(function() { wizard.wizard('previous') })
    $('#wizard-generate-thumbnail').click(function() { wizard.wizard('generate_thumbnail') })
})

JqueryClass('wizard', {
    init: function(models) {
	var self = $(this)
	var model_list = Object.keys(models).sort()
	self.data('model_index', models)
	self.data('model_list', model_list)
	self.find('.previous').click(function() { self.wizard('shiftModel', -1) })
	self.find('.next').click(function() { self.wizard('shiftModel', 1) })

	self.data('label', 'Label here')
	self.data('author', 'brand')
    },

    open: function() {
	var self = $(this)
	var effect = effects.find('option:selected').data()

	self.data('effect', effect)
	self.data('label', effect.name)

	if (effect.icon.templateData) {
	    var data = effect.icon.templateData
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

	self.find('.step').hide()
	self.find('#wizard-step-'+step).show()
	self.data('step', step)
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
	if (i == null)
	    i = 0
	i = (i + len) % len
	var model = list[i]

	self.data('model', model)
	self.data('color', null)
	self.data('panel', null)

	self.find('#model-choice h3').html(model)

	var canvas, factory

	var data = self.data('model_index')[model]
	canvas = self.find('#color-options')
	canvas.html('')
	var colors = data.colors.sort()
	factory = function(color) { return function() { self.wizard('chooseColor', color) } }
	for (var j in colors)
	    $('<img>').attr('src', '/resources/pedals/'+model+'/'+colors[j]+'.png').height(64).click(factory(colors[j])).appendTo(canvas)

	canvas = self.find('#panel-options')
	canvas.html('')
	var panels = Object.keys(data.panels).sort()
	factory = function(panel) { return function() { self.wizard('choosePanel', panel) } }
	for (var j in panels)
	    $('<li>').html(panels[j].replace(/-/, ' ')).click(factory(panels[j])).appendTo(canvas)

	self.wizard('render')
    },

    chooseColor: function(color) {
	var self = $(this)
	self.data('color', color)
	self.wizard('render')
    },

    choosePanel: function(panel) {
	var self = $(this)
	self.data('panel', panel)
	self.data('controls', null)
	self.wizard('render')
    },

    render: function() {
	var self = $(this)
	var effect = self.data('effect')
	var model = self.data('model')
	var panel = self.data('panel')
	var color = self.data('color') || 'none'
	var label = self.data('label') 
	var author = self.data('author') 
	var db = self.data('model_index')
	var controls = self.data('controls') || effect.ports.control.input.slice(0, db[model].panels[panel])

	var step = self.data('step')
	var icon = self.find('.wizard-icon')
	icon.html('')

	var element
	if (!panel) { // no template yet
	    element = $('<img>').attr('src', '/resources/pedals/'+model+'/'+color+'.png')
	} else {
	    var template = TEMPLATES['pedal-' + model + '-' + panel]
	    effect.icon = {
		template: template,
		templateData: {
		    color: color,
		    controls: controls,
		    label: label,
		    author: author
		}
	    }
	    element = $(Mustache.render(template, getTemplateData(effect)))
	}

	element.appendTo(icon)

	self.wizard('ok', model && panel && self.data('color'))
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
	    controls = []
	    for (i in effect.ports.control.input.slice(0, db[self.data('model')].panels[panel]))
		controls.push(effect.ports.control.input[i].symbol)
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
	for (i in controlPorts) {
	    control = controlPorts[i]
	    $('<option>').val(control.symbol).html(control.name).appendTo(select)
	}

	var factory = function(sel, i) {
	    return function() {
		controls[i] = sel.val()
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
	canvas.append('    mod:icon [\n')
	canvas.append('        a mod:Icon;\n')
	canvas.append('        mod:resourcesDirectory &lt;modgui&gt;;\n')
	canvas.append('        mod:template &lt;modgui/pedal-'+model+'-'+panel+'.html&gt;;\n')
	canvas.append('        mod:templateData &lt;modgui/data-'+slug+'.json&gt;;\n')
	canvas.append('        mod:screenshot &lt;modgui/screenshot-'+slug+'.png&gt;;\n')
	canvas.append('        mod:thumbnail &lt;modgui/thumb-'+slug+'.png&gt;;\n')
	canvas.append('    ].')
    },

    save_template: function() {
	var self = $(this)
	$.ajax({ url: '/effect/save',
		 type: 'POST',
		 data: JSON.stringify(self.data()),
		 success: function() {
		     self.wizard('generate_thumbnail')
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
		      height: icon.height()
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
	$('<li>').html('modgui/pedal-'+model+'-'+panel+'.html').appendTo(canvas)
 	$('<li>').html('modgui/data-'+slug+'.json').appendTo(canvas)
 	$('<li>').html('modgui/screenshot-'+slug+'.png').appendTo(canvas)
 	$('<li>').html('modgui/thumb-'+slug+'.png').appendTo(canvas)
    },

    finish: function() {
	document.location.reload()
    }

})
