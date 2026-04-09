PostGIS must be installed and available in the PostgreSQL server.
Run the following SQL commands as a database superuser before installing
this module::

    CREATE SCHEMA postgis;

    CREATE EXTENSION postgis WITH SCHEMA postgis;

    ALTER DATABASE <db_name> SET search_path = public, postgis;

    GRANT USAGE ON SCHEMA postgis TO public;

    GRANT SELECT, REFERENCES, TRIGGER ON ALL TABLES IN SCHEMA postgis TO public;
    GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA postgis TO public;
    GRANT USAGE ON SCHEMA postgis TO DB_USER;
    ALTER ROLE DB_USER SET search_path = public, postgis;
