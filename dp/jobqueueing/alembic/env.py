"""
Customized alembic environment manager.
Adapted from https://gist.github.com/twolfson/4bc5813b022178bd7034

This manager enables command-line specification of the database to migrate.
This simplifies testing and use in various environments, e.g., local dev
machine vs. compute node (with test and prod databases on compute node).

The database to migrate is specified using the command-line argument `-x`,
as follows::

    alembic -x db=<db-name> upgrade ...

This syntax is now required; i.e., `-x db=<db-name>` cannot be omitted from
the command.

The `<db-name>` section must appear in `alembic.ini`, with a
`sqlalchemy.url =` line.
For example, to use `alembic -x db=test upgrade ...`::

    [test]
    sqlalchemy.url = sqlite:////path/to/database/test.sqlite
"""
from alembic import context
from sqlalchemy import engine_from_config, pool
from logging.config import fileConfig

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
from dp.jobqueueing import jobqueueing_db
target_metadata = jobqueueing_db.Base.metadata
# target_metadata = None

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.

# Obtain command-line specification of database to run migration against.
cmd_kwargs = context.get_x_argument(as_dictionary=True)
if 'db' not in cmd_kwargs:
    raise Exception('We couldn\'t find `db` in the CLI arguments. '
                    'Please verify `alembic` was run with `-x db=<db_name>` '
                    '(e.g. `alembic -x db=development upgrade head`)')
db_name = cmd_kwargs['db']


def run_migrations_offline():
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url, target_metadata=target_metadata, literal_binds=True)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # Load db config on top of alembic config. This enables CLI spec of
    # database to migrate.
    alembic_config = config.get_section(config.config_ini_section)
    db_config = config.get_section(db_name)
    for key in db_config:
        alembic_config[key] = db_config[key]

    connectable = engine_from_config(
        alembic_config,
        prefix='sqlalchemy.',
        poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
