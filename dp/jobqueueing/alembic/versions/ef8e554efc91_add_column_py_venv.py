"""add column py_venv

Revision ID: ef8e554efc91
Revises: c4d37392bf0c
Create Date: 2017-07-13 15:18:37.076964

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ef8e554efc91'
down_revision = 'c4d37392bf0c'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'generate_climos_queue',
        sa.Column('py_venv', sa.String(length=1024), nullable=False,
                  server_default='/storage/data/projects/comp_support/'
                                 'climate_exporer_data_prep/'
                                 'climatological_means/venv')
    )


def downgrade():
    op.drop_column('generate_climos_queue', 'py_venv')
