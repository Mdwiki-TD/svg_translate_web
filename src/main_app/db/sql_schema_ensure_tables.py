""" """


from .sql_schema_tables import TablesCreatesSql
from .engine import Database


def ensure_all_tables(database_data, sql_tables: TablesCreatesSql, db: None | Database = None):
    db = db or Database(database_data)

    db.execute_query(sql_tables.templates_need_update)
    db.execute_query(sql_tables.templates)
    db.execute_query(sql_tables.settings)
    db.execute_query(sql_tables.owid_charts)
    db.execute_query(sql_tables.owid_charts_templates)
    db.execute_query(sql_tables.jobs)
    db.execute_query(sql_tables.admin_users)
