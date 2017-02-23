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
from tacker.extensions import nfvo
from tacker import manager
from tacker.plugins.common import constants
from tacker.services import service_base

LOG = logging.getLogger(__name__)
CONF = cfg.CONF

class Server(model_base.BASE,
          models_v1.HasId):
    __tablename__ = 'server'
    is_active = sa.Column(sa.Boolean, default=True, server_default=sql.true(
    ), nullable=False)
    description = sa.Column(sa.Text, nullable=True)
    type = sa.Column(sa.String(64), nullable=True)
    name = sa.Column(sa.String(255), nullable=True)
    last_update = sa.Column(sa.DateTime(), nullable=False)

class ServerPluginDb(service_base.NFVPluginBase, db_base.CommonDbMixin):
    def __init__(self):
        super(ServerPluginDb, self).__init__()
        self._cos_db_plg = common_services_db.CommonServicesPluginDb()

    @property
    def _core_plugin(self):
        return manager.TackerManager.get_plugin()

    def _make_server_dict(self, server_db, fields=None):
        key_list = ('id', 'is_active', 'description', 'type', 'name',
                    'last_update')
        res = dict((key, server_db[key]) for key in key_list)
        return self._fields(res, fields)

    def create_server(self, context):
        with context.session.begin(subtransactions=True):
            cfg.CONF.uuid = uuid.uuid4()
            server_db = Server(
                id=str(cfg.CONF.uuid),
                is_active=True,
                description="",
                type="default",
                name="",
                last_update=timeutils.utcnow())
            context.session.add(server_db)
        server_dict = self._make_server_dict(server_db)
        return server_dict

    # def delete_server(self, context, vim_id, soft_delete=True):
    #     with context.session.begin(subtransactions=True):
    #         vim_db = self._get_resource(context, Vim, vim_id)
    #         if soft_delete:
    #             vim_db.update({'deleted_at': timeutils.utcnow()})
    #             self._cos_db_plg.create_event(
    #                 context, res_id=vim_db['id'],
    #                 res_type=constants.RES_TYPE_VIM,
    #                 res_state=vim_db['status'],
    #                 evt_type=constants.RES_EVT_DELETE,
    #                 tstamp=vim_db[constants.RES_EVT_DELETED_FLD])
    #         else:
    #             context.session.query(VimAuth).filter_by(
    #                 vim_id=vim_id).delete()
    #             context.session.delete(vim_db)
    #
    # def update_server(self, context, vim_id, vim):
    #     self._validate_default_vim(context, vim, vim_id=vim_id)
    #     with context.session.begin(subtransactions=True):
    #         vim_cred = vim['auth_cred']
    #         vim_project = vim['vim_project']
    #         is_default = vim.get('is_default')
    #         vim_db = self._get_resource(context, Vim, vim_id)
    #         try:
    #             if is_default:
    #                 vim_db.update({'is_default': is_default})
    #             vim_auth_db = (self._model_query(context, VimAuth).filter(
    #                 VimAuth.vim_id == vim_id).with_lockmode('update').one())
    #         except orm_exc.NoResultFound:
    #                 raise nfvo.VimNotFoundException(vim_id=vim_id)
    #         vim_auth_db.update({'auth_cred': vim_cred, 'password':
    #                            vim_cred.pop('password'), 'vim_project':
    #                            vim_project})
    #         vim_db.update({'updated_at': timeutils.utcnow()})
    #         self._cos_db_plg.create_event(
    #             context, res_id=vim_db['id'],
    #             res_type=constants.RES_TYPE_VIM,
    #             res_state=vim_db['status'],
    #             evt_type=constants.RES_EVT_UPDATE,
    #             tstamp=vim_db[constants.RES_EVT_UPDATED_FLD])