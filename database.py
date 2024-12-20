import pandas as pd
from sqlalchemy import create_engine, text, MetaData, Table, select
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager


DATABASE_URL = "postgresql://postgres:123456@localhost:5432/solx"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


@contextmanager
def get_db_connection():
  """
  Provides a database connection using a context manager.
  """
  connection = engine.connect()
  try:
    yield connection
  finally:
    connection.close()


def fetch_client_load_profile(client_name, start_date=None, end_date=None):
  query = text("""
    SELECT *
    FROM load_profiles.hourly
    WHERE client_name = :client_name
    AND (:start_date IS NULL OR supply_period >= :start_date)
    AND (:end_date IS NULL OR supply_period <= :end_date)
  """)
  with get_db_connection() as connection:
    client_data = pd.read_sql(query, connection, params={
      "client_name": client_name,
      "start_date": start_date,
      "end_date": end_date
    })
  return client_data


def fetch_unique_clients():
  """
  Fetches a list of unique client names
  """
  with get_db_connection() as connection:
    query = text("""
      SELECT DISTINCT client_name
      FROM load_profiles.solx_clients
    """)
    solx_clients = pd.read_sql(query, connection)

  return solx_clients


def fetch_unique_dus():
  """
  Fetches a list of unique DU names
  """
  with get_db_connection() as connection:
    query = text("""
      SELECT DISTINCT du_name
      FROM du_rates.distribution_utilities
    """)
    dus = pd.read_sql(query, connection)

  return dus
