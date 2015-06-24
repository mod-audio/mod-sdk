#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import rdflib, argparse, os

parser = argparse.ArgumentParser(description='Opens a bundle and add a mod:GUI section to each plugin inside it')
parser.add_argument('bundles', help="The bundle path (a directory containing manifest.ttl file", type=str, nargs='+')

args = parser.parse_args()

def modfy(bundle):
    manifest_path = os.path.join(bundle, 'manifest.ttl')
    resources = os.path.join(os.path.realpath(bundle), 'modgui')
    if not os.path.exists(resources):
        os.mkdir(resources)
    resources = 'file://%s' % resources


    rdfschema = rdflib.Namespace('http://www.w3.org/2000/01/rdf-schema#')
    rdfsyntax = rdflib.Namespace('http://www.w3.org/1999/02/22-rdf-syntax-ns#')
    lv2core = rdflib.Namespace('http://lv2plug.in/ns/lv2core#')
    mod = rdflib.Namespace('http://moddevices.com/ns/modgui#')

    manifest = rdflib.ConjunctiveGraph()
    manifest.parse(manifest_path, format='n3')

    for triple in manifest.triples((None, rdfsyntax.type, lv2core.Plugin)):
        url = triple[0]
        for triple in manifest.triples((url, rdfschema.seeAlso, None)):
            ttl_path = triple[2]
            plugin_name = ttl_path.split('/')[-1].replace('.ttl', '')
            plugin = rdflib.ConjunctiveGraph()
            plugin.parse(ttl_path, format='n3')
            try:
                modgui = list(plugin.triples(url, rdfsyntax.type, mod.GUI))[0]
            except:
                pass
            else:
                continue

            for triple in plugin.triples((None, None, None)):
                if triple[0].startswith('http://moddevices.com/ns/extensions/effect#'):
                    plugin.remove(triple)
            gui = rdflib.BNode()
            uri = rdflib.term.URIRef
            resources = 'modgui'
            plugin.add((url, mod.gui, gui))
            plugin.add((gui, mod.resourcesDirectory, uri(resources)))
            plugin.add((gui, mod.iconTemplate, uri('%s/%s.html' % (resources, plugin_name))))
            plugin.add((gui, mod.templateData, uri('%s/%s.json' % (resources, plugin_name))))
            plugin.add((gui, mod.screenshot, uri('%s/%s.png' % (resources, plugin_name))))
            plugin.add((gui, mod.thumbnail, uri('%s/%s-thumb.png' % (resources, plugin_name))))

            plugin.namespace_manager.bind('mod', mod)

            plugin.serialize(ttl_path, format='n3')

for bundle in args.bundles:
    modfy(bundle)
