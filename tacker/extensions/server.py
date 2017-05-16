import abc

import six

from tacker._i18n import _
from tacker.api import extensions
from tacker.api.v1 import attributes as attr
from tacker.api.v1 import resource_helper
from tacker.common import exceptions
from tacker.plugins.common import constants
from tacker.services import service_base

class ServerNotFoundException(exceptions.TackerException):
    message = _("Specified server id %(server_id)s is invalid. Please verify and "
                "pass a valid VIM id")

class Server(extensions.ExtensionDescriptor):
    @classmethod
    def get_name(cls):
        return 'SERVER MANAGER'

    @classmethod
    def get_alias(cls):
        return 'SERVER'

    @classmethod
    def get_description(cls):
        return "Extension for NFV Orchestrator"

    @classmethod
    def get_namespace(cls):
        return 'http://wiki.openstack.org/Tacker'

    @classmethod
    def get_updated(cls):
        return "2017-1-13T10:00:00-00:00"

    # @classmethod
    # def get_resources(cls):
    #     special_mappings = {}
    #     plural_mappings = resource_helper.build_plural_mappings(
    #         special_mappings, RESOURCE_ATTRIBUTE_MAP)
    #     attr.PLURALS.update(plural_mappings)
    #     return resource_helper.build_resource_info(
    #         plural_mappings, RESOURCE_ATTRIBUTE_MAP, constants.NFVO,
    #         translate_name=True)

    @classmethod
    def get_plugin_interface(cls):
        return ServerPluginBase

    # def update_attributes_map(self, attributes):
    #     super(Server, self).update_attributes_map(
    #         attributes, extension_attrs_map=RESOURCE_ATTRIBUTE_MAP)
    #
    # def get_extended_resources(self, version):
    #     version_map = {'1.0': RESOURCE_ATTRIBUTE_MAP}
    #     return version_map.get(version, {})


@six.add_metaclass(abc.ABCMeta)
class ServerPluginBase(service_base.NFVPluginBase):
    def get_plugin_name(self):
        return constants.SERVER

    def get_plugin_type(self):
        return constants.SERVER

    def get_plugin_description(self):
        return 'Tacker VNF Server plugin'
