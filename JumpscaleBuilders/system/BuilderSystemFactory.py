from Jumpscale import j

from .BuilderBaseClass import BuilderBaseClass, builder_method
from .BuilderBaseFactoryClass import BuilderBaseFactoryClass


class BuilderSystemPackage(j.baseclasses.object):

    __jslocation__ = "j.builders.system"
    BaseClass = BuilderBaseClass
    builder_method = builder_method

    def _init(self, **kwargs):
        j.clients.redis.core_get()
