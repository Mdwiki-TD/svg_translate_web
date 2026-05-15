""" """

from .engine import Database
from .sql_schema_tables import TablesCreatesSql


def ensure_all_tables(sql_tables: TablesCreatesSql, db: Database):
    db.execute_query(sql_tables.templates_need_update)
    db.execute_query(sql_tables.templates)
    db.execute_query(sql_tables.settings)
    db.execute_query(sql_tables.owid_charts)
    db.execute_query(sql_tables.owid_charts_templates)
    db.execute_query(sql_tables.jobs)
    db.execute_query(sql_tables.admin_users)
