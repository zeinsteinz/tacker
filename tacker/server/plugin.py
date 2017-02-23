import os
import threading
import time
import uuid

from cryptography import fernet
from oslo_config import cfg
from oslo_log import log as logging
from oslo_utils import excutils
from oslo_utils import strutils

from tacker._i18n import _
from tacker.common import driver_manager
from tacker.common import exceptions
from tacker.common import log
from tacker.common import utils
from tacker import context as t_context
from tacker.db.nfvo import nfvo_db
from tacker.db.nfvo import vnffg_db
from tacker.extensions import nfvo
from tacker import manager
from tacker.plugins.common import constants
from tacker.vnfm.tosca import utils as toscautils
from toscaparser import tosca_template
from tacker.db.server import server_db

LOG = logging.getLogger(__name__)
CONF = cfg.CONF

class ServerPlugin(server_db.ServerPluginDb):

    supported_extension_aliases = ['server']

    def __init__(self):
        super(ServerPlugin, self).__init__()
        context = t_context.get_admin_context()
        LOG.debug("Finally enter the program."+"*"*2000)
        server_res = super(ServerPlugin, self).create_server(context)
        LOG.debug("Tacker server uuid {0}".format(cfg.CONF.uuid))
        LOG.debug("Server uuid in database {0}".format(server_res['id']))

    def get_plugin_name(self):
        return constants.SERVER

    def get_plugin_type(self):
        return constants.SERVER

    def get_plugin_description(self):
        return 'Tacker NFV Orchestrator plugin'