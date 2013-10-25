from geoserver.support import ResourceInfo, bbox, write_bbox, \
        write_string, xml_property, url

def _maybe_text(n):
    if n is None:
        return None
    else:
        return n.text

def _layer_list(node):
    if node is not None:
        return [_maybe_text(n.find("name")) for n in node.findall("layer")]        
        
def _publishable_list(node):
    if node is not None:
        return [_maybe_text(n.find("name")) for n in node.findall("published")]
    
def _style_list(node):
    if node is not None:
        return [_maybe_text(n.find("name")) for n in node.findall("style")]

def _write_layers(builder, layers):
    builder.start("layers", dict())
    for l in layers:
        builder.start("layer", dict())
        if l is not None:
            builder.start("name", dict())
            builder.data(l)
            builder.end("name")
        builder.end("layer")
    builder.end("layers")

def _write_styles(builder, styles):
    builder.start("styles", dict())
    for s in styles:
        builder.start("style", dict())
        if s is not None:
            builder.start("name", dict())
            builder.data(s)
            builder.end("name")
        builder.end("style")
    builder.end("styles")

class LayerGroup(ResourceInfo):
    """
    Represents a layer group in geoserver 
    """

    resource_type = "layerGroup"
    save_method = "PUT"

    def __init__(self, catalog, name):
        super(LayerGroup, self).__init__()

        assert isinstance(name, basestring)

        self.catalog = catalog
        self.name = name

    @property
    def href(self):
        return url(self.catalog.service_url, ["layergroups", self.name + ".xml"])

    styles = xml_property("styles", _style_list)
    bounds = xml_property("bounds", bbox)    
        
    def _layers_getter(self):
        if self.catalog.gsversion() == "2.2.x":
            path, converter = "layers", _layer_list
        else:
            path, converter = "publishables", _publishable_list
        if path in self.dirty:
            return self.dirty[path]
        else:
            if self.dom is None:
                self.fetch()
            node = self.dom.find(path)
            return converter(self.dom.find(path)) if node is not None else None

    def _layers_setter(self, value):
        self.dirty["layers"] = value

    def _layers_delete(self):
        self.dirty["layers"] = None
    
    layers =  property(_layers_getter, _layers_setter, _layers_delete)

    writers = dict(
              name = write_string("name"),
              styles = _write_styles,
              layers = _write_layers,
              bounds = write_bbox("bounds")
            )

    def __str__(self):
        return "<LayerGroup %s>" % self.name

    __repr__ = __str__

class UnsavedLayerGroup(LayerGroup):
    save_method = "POST"
    def __init__(self, catalog, name, layers, styles, bounds):
        super(UnsavedLayerGroup, self).__init__(catalog, name)
        bounds = bounds if bounds is not None else ("-180","180","-90","90","EPSG:4326")
        self.dirty.update(name = name, layers = layers, styles = styles, bounds = bounds)

    @property
    def href(self):
        return "%s/layergroups?name=%s" % (self.catalog.service_url, self.name)
