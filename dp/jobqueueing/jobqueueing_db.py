import sqlalchemy
from sqlalchemy import MetaData
from sqlalchemy import Table, Column, Integer, String, Enum
from sqlalchemy import DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base(metadata=MetaData())
metadata = Base.metadata

gcq_statuses = ['NEW', 'SUBMITTED', 'RUNNING', 'SUCCESS', 'ERROR']


class GenerateClimosQueueEntry(Base):
    """
    This class represents an entry in the generate_climos queue.
    """
    __tablename__ = 'generate_climos_queue'
    id = Column('generate_climos_queue_id', Integer, primary_key=True,
                nullable=False)

    # File to process
    input_filepath = Column(String(1024), nullable=False, index=True)

    # Execution environment
    py_venv = Column(String(1024), nullable=False)

    # generate_climos parameters
    output_directory = Column(String(1024), nullable=False)
    # This attribute was originally defined with:
    #   convert_longitude = Column(Boolean, default=True, nullable=False)
    # resulting in column named 'convert_longitude'.
    # Should rename the column, but SQLite makes it hard.
    # Alembic can do it with extra effort, but it's not worth it at this time.
    # We just re-map it here.
    convert_longitudes = Column('convert_longitude', Boolean, default=True,
                                nullable=False)
    split_vars = Column(Boolean, default=True, nullable=False)
    split_intervals = Column(Boolean, default=True, nullable=False)

    # PBS parameters
    ppn = Column(Integer, default=1, nullable=False)
    walltime = Column(String(12), default='10:00:00', nullable=False)

    # Status tracking
    status = Column(Enum(*gcq_statuses), nullable=False, default='NEW')
    added_time = Column(DateTime, nullable=False)
    submitted_time = Column(DateTime)
    pbs_job_id = Column(String(64), index=True)
    started_time = Column(DateTime)
    completed_time = Column(DateTime)
    completion_message = Column(String(2048))
    