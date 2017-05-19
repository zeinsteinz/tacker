# Copyright 2017 Telecom ParisTech
# All Rights Reserved.
#
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import uuid

from oslo_utils import strutils
from oslo_utils import timeutils
from oslo_config import cfg
from oslo_log import log as logging
import sqlalchemy as sa
from sqlalchemy import orm
from sqlalchemy.orm import exc as orm_exc
from sqlalchemy import sql

from tacker.db.common_services import common_services_db
from tacker.db import db_base
from tacker.db import model_base
from tacker.db import models_v1
from tacker.db import types
from tacker.db.vnfm import vnfm_db
from tacker.extensions import server
from tacker import manager
from tacker.plugins.common import constants
from tacker.services import service_base
from tacker.common.utils import get_hostname

LOG = logging.getLogger(__name__)
CONF = cfg.CONF

class Server(model_base.BASE,
          models_v1.HasId):
    __tablename__ = 'server'
    status = sa.Column(sa.String(255), nullable=True)
    role = sa.Column(sa.String(255), nullable=True)
    description = sa.Column(sa.Text, nullable=True)
    updated_at = sa.Column(sa.DateTime(), nullable=False)
    created_at = sa.Column(sa.DateTime(), nullable=False)

class ServerPluginDb(service_base.NFVPluginBase, db_base.CommonDbMixin):
    def __init__(self):
        super(ServerPluginDb, self).__init__()
        self._cos_db_plg = common_services_db.CommonServicesPluginDb()

    @property
    def _core_plugin(self):
        return manager.TackerManager.get_plugin()

    def _make_server_dict(self, server_db, fields=None):
        key_list = ('id', 'status', 'role', 'description', 'updated_at', 'created_at')
        res = dict((key, server_db[key]) for key in key_list)
        return self._fields(res, fields)

    def _get_resource(self, context, model, id):
        try:
            return self._get_by_id(context, model, id)
        except orm_exc.NoResultFound:
            if issubclass(model, Server):
                raise server.ServerNotFoundException(server_id=id)
            else:
                raise

    def _get_by_id(self, context, model, id):
        query = self._model_query(context, model)
        return query.filter(model.id == id).one()

    def create_server(self, context):
        with context.session.begin(subtransactions=True):
            cfg.CONF.uuid = str(uuid.uuid4())
            server_db = Server(
                id=cfg.CONF.uuid,
                status="active",
                role="normal",
                description="hostname: " + get_hostname(),
                updated_at=timeutils.utcnow(),
                created_at=timeutils.utcnow())
            context.session.add(server_db)
        LOG.debug("Server item is created in DB")
        server_dict = self._make_server_dict(server_db)
        return server_dict

    def update_server(self, context, server_id, server=None):
        with context.session.begin(subtransactions=True):
            server_db = self._get_resource(context, Server, server_id)
            if server:
                server_db.update({'status': server['status']})
                server_db.update({'role': server['role']})
                server_db.update({'description': server['description']})
            server_db.update({'updated_at': timeutils.utcnow()})
        server_dict = self._make_server_dict(server_db)
        return server_dict

    def delete_server(self, context, server_id):
        with context.session.begin(subtransactions=True):
            server_db = self._get_resource(context, Server, server_id)
            context.session.delete(server_db)

    def get_servers(self, context, filters=None, fields=None):
        return self._get_collection(context, Server, self._make_server_dict,
                                    filters=filters, fields=fields)

    def get_server_by_id(self, context, server_id):
        with context.session.begin(subtransactions=True):
            server_db = self._get_resource(context, Server, server_id)
        server_dict = self._make_server_dict(server_db)
        return server_dict
