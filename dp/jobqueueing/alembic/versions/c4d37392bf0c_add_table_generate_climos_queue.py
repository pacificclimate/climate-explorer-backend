"""Add table generate_climos_queue

Revision ID: c4d37392bf0c
Revises: 
Create Date: 2017-06-27 14:29:59.069718

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c4d37392bf0c'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('generate_climos_queue',
        sa.Column('generate_climos_queue_id', sa.Integer(), nullable=False),
        sa.Column('input_filepath', sa.String(length=1024), nullable=False),
        sa.Column('output_directory', sa.String(length=1024), nullable=False),
        sa.Column('convert_longitude', sa.Boolean(), nullable=False),
        sa.Column('split_vars', sa.Boolean(), nullable=False),
        sa.Column('split_intervals', sa.Boolean(), nullable=False),
        sa.Column('ppn', sa.Integer(), nullable=False),
        sa.Column('walltime', sa.String(length=12), nullable=False),
        sa.Column('status', sa.Enum('NEW', 'SUBMITTED', 'RUNNING', 'SUCCESS', 'ERROR'), nullable=False),
        sa.Column('added_time', sa.DateTime(), nullable=False),
        sa.Column('submitted_time', sa.DateTime(), nullable=True),
        sa.Column('pbs_job_id', sa.String(length=64), nullable=True),
        sa.Column('started_time', sa.DateTime(), nullable=True),
        sa.Column('completed_time', sa.DateTime(), nullable=True),
        sa.Column('completion_message', sa.String(length=2048), nullable=True),
        sa.PrimaryKeyConstraint('generate_climos_queue_id')
    )
    op.create_index(op.f('ix_generate_climos_queue_input_filepath'), 'generate_climos_queue', ['input_filepath'], unique=False)
    op.create_index(op.f('ix_generate_climos_queue_pbs_job_id'), 'generate_climos_queue', ['pbs_job_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_generate_climos_queue_pbs_job_id'), table_name='generate_climos_queue')
    op.drop_index(op.f('ix_generate_climos_queue_input_filepath'), table_name='generate_climos_queue')
    op.drop_table('generate_climos_queue')
