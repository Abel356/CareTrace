from alembic import context
from caretrace_api.database import Database
from caretrace_api.settings import Settings
from caretrace_api.source_store import metadata
from sqlalchemy.engine import URL, Connection


def database_url() -> URL:
    url = Settings().get_database_url()
    if url is None:
        raise ValueError("set CARETRACE_DATABASE_URL when running migrations")
    return url


def migrate_online(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=metadata)
    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    context.configure(
        url=database_url().render_as_string(hide_password=False),
        target_metadata=metadata,
        literal_binds=True,
    )
    with context.begin_transaction():
        context.run_migrations()
else:
    supplied_connection = context.config.attributes.get("connection")
    if supplied_connection is not None:
        migrate_online(supplied_connection)
    else:
        database = Database(database_url())
        try:
            with database.engine.connect() as connection:
                migrate_online(connection)
        finally:
            database.dispose()
