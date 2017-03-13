import os
import threading
import time
import uuid
import random

from cryptography import fernet
from oslo_config import cfg
from oslo_log import log as logging
from oslo_utils import excutils
from oslo_utils import strutils
from oslo_utils import timeutils

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

# server status
STATUS_ACTIVE = "active"
STATUS_INACTIVE = "inactive"

# server roles
ROLE_HEAD = "head"
ROLE_NORMAL = "normal"

LOG = logging.getLogger(__name__)
CONF = cfg.CONF

class ServerPlugin(server_db.ServerPluginDb):

    supported_extension_aliases = ['server']
    _lock = threading.RLock()

    OPTS = [
        cfg.IntOpt(
            'update_interval', default=2,
            help=_('Interval to update server status')),
    ]
    cfg.CONF.register_opts(OPTS, 'tacker_server')

    def __init__(self):
        super(ServerPlugin, self).__init__()
        self.context = t_context.get_admin_context()
        LOG.debug("Enter the main server program.")
        server_res = super(ServerPlugin, self).create_server(self.context)
        LOG.debug("Tacker server uuid {0}".format(cfg.CONF.uuid))
        self.update_interval = cfg.CONF.tacker_server.update_interval
        threading.Thread(target=self.__run__).start()
        self._server_monitor = ServerMonitor()

    def __run__(self):
        while(1):
            time.sleep(self.update_interval)
            LOG.debug("Update server status")
            super(ServerPlugin, self).update_server(self.context, cfg.CONF.uuid)

    def get_plugin_name(self):
        return constants.SERVER

    def get_plugin_type(self):
        return constants.SERVER

    def get_plugin_description(self):
        return 'Tacker NFV Orchestrator plugin'

class ServerMonitor(object):
    """Server Monitor."""
    _instance = None
    _server_plugin = None
    _vnfm_plugin = None
    _lock = threading.RLock()

    OPTS = [
        cfg.IntOpt('update_timeout', default=11,
                   help=_("default timeout since last update")),
        cfg.IntOpt('check_interval', default=5,
                   help=_("the interval for checking server status")),
    ]
    cfg.CONF.register_opts(OPTS, 'server_monitor')

    def __new__(cls):
       if not cls._instance:
           cls._instance = super(ServerMonitor, cls).__new__(cls)
       return cls._instance

    def __init__(self,):
        LOG.debug('Spawning server monitor thread')
        self.context = t_context.get_admin_context()
        self.is_head = False
        threading.Thread(target=self.__run__).start()

    def getServerPlugin(self):
        if not self._server_plugin:
            self._server_plugin = manager.TackerManager.get_service_plugins().get(constants.SERVER)
        return self._server_plugin

    def getVnfmPlugin(self):
        if not self._vnfm_plugin:
            self._vnfm_plugin = manager.TackerManager.get_service_plugins().get(constants.VNFM)
        return self._vnfm_plugin

    def __run__(self):
        while(1):
            time.sleep(cfg.CONF.server_monitor.check_interval)
            with self._lock:
                server_dict = self.getServerPlugin().get_servers(self.context, {"status": [STATUS_ACTIVE]})
                LOG.debug('Total number of active servers: {0}'.format(len(server_dict)))
                if not self.is_head:
                    self.is_head = self.can_be_head(server_dict)
                for server in server_dict:
                    self.checkServer(server)
                if self.is_head:
                    self.handleOrphanVnfs()


    def can_be_head(self, server_dict):
        first_active = min(server_dict, key=lambda s: s["created_at"])
        if first_active["id"] == cfg.CONF.uuid and first_active["role"] != ROLE_HEAD:
            LOG.debug("set server {0} as head".format(first_active["id"]))
            first_active["role"] = ROLE_HEAD
            self.getServerPlugin().update_server(self.context, cfg.CONF.uuid, first_active)
            return True
        return False

    def checkServer(self, server):
        if server["id"] != cfg.CONF.uuid:
            LOG.debug("check server: {0}".format(server["id"]))
            elapsed = timeutils.utcnow()-server["updated_at"]
            if server["status"] !=  STATUS_INACTIVE and elapsed.total_seconds() > cfg.CONF.server_monitor.update_timeout:
                LOG.debug("server {0} is not active after {1} seconds".format(server["id"],
                                                                              cfg.CONF.server_monitor.update_timeout))
                self.handleInactiveServer(server)
                return False
        return True

    def handleInactiveServer(self, server):
        server["status"] = STATUS_INACTIVE
        self.getServerPlugin().update_server(self.context, server["id"], server)

    def getMonitoredVnfs(self, server_id):
        vnfs = self.getVnfmPlugin().get_vnfs(self.context, {"server_id": [server_id]})
        LOG.debug("{0} vnfs are monitored by server {1}".format(len(vnfs), server_id))
        #LOG.debug("{0} vnfs are stored by local server dict".format(len(self.getVnfmPlugin()._vnf_monitor._hosting_vnfs)))
        return vnfs

    def handleOrphanVnfs(self):
        active_servers = self.getServerPlugin().get_servers(self.context, {"status": [STATUS_ACTIVE]})
        id_set = set(s["id"] for s in active_servers)
        vnfs = self.getVnfmPlugin().get_vnfs(self.context)
        LOG.debug("Total number of active vnfs: {0}".format(len(vnfs)))
        selected_server = random.choice(active_servers)
        for vnf in vnfs:
            LOG.debug("checking status of vnf {0}".format(vnf["id"]))
            if vnf["server_id"] not in id_set:
                LOG.debug("vnf {0} is an orphan".format(vnf["id"]))
                vnf["server_id"] = selected_server["id"]
                self.getVnfmPlugin().set_vnf_server_id(self.context, vnf["id"], selected_server["id"])
                LOG.debug("rebind vnf {0} to server {1}".format(vnf["id"], selected_server["id"]))
        self.getServerPlugin().update_server(self.context, selected_server["id"], selected_server)

