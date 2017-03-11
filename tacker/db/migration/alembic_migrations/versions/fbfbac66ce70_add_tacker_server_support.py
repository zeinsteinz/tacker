# Copyright 2017 OpenStack Foundation
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
#

"""add tacker server support

Revision ID: fbfbac66ce70
Revises: ef14f8026327
Create Date: 2017-02-23 14:45:02.275730

"""

# revision identifiers, used by Alembic.
revision = 'fbfbac66ce70'
down_revision = 'ef14f8026327'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

from tacker.db import migration
from tacker.db import types

def upgrade(active_plugins=None, options=None):
    op.add_column('vnf', sa.Column('server_id', types.Uuid(length=36), nullable=False))

    op.create_table(
        'server',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('status', sa.String(length=255), nullable=True),
        sa.Column('role', sa.String(length=255), nullable=True),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        mysql_engine='InnoDB'
    )

    op.create_foreign_key("fk_server_id", "vnf", "server", ["server_id"], ["id"])
