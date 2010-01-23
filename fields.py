
from djata.orderedclass import *

def map_field(field):
    return field

class Cell(object):
    def __init__(self, field, object):
        self.field = field
        self.object = object
    def __unicode__(self):
        return self.value
    @property
    def value(self):
        return self.field.value_from_object(self.object)

class Field(OrderedProperty):
    Cell = Cell

    def __init__(self, name = None, link = False, filter = False, identity = False):
        self.name = name
        self.link = link
        self.filter = filter

    def dub(self, view, field, name):
        self.view = view
        self.field = field
        if self.name is None:
            self.name = name
        return self

    def to_python(self, value):
        return value

    def value_from_object(self, object):
        return object[self.attname]

    def __get__(self, object, klass):
        return object[self.attname]
    def __set__(self, object, value):
        object[self.attname] = value

class ForeignKey(Field):
    def __init__(self, view):
        self.to = view

