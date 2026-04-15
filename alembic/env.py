import asyncio
from logging.config import fileConfig
from sqlalchemy.ext.asyncio import create_async_engine
from alembic import context

from core.config import settings
from core.models import Base

import geoalchemy2
# Import ALL your models so Alembic can see them
from university.models import University
from submission.models import Submissions

config = context.config
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline():
    context.configure(url=settings.DATABASE_URL,
                      target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


def include_object(obj, name, type_, reflected, compare_to):
    # Skip PostGIS system tables
    postgis_tables = {
        'spatial_ref_sys', 'geography_columns',
        'geometry_columns', 'raster_columns', 'raster_overviews'
    }
    if type_ == "table" and name in postgis_tables:
        return False

    # Skip spatial indexes (GeoAlchemy2 creates these automatically)
    if type_ == "index" and name and "_geometry" in name:
        return False

    return True


def do_run_migrations(connection):
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        include_object=include_object
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online():
    connectable = create_async_engine(settings.DATABASE_URL)
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
