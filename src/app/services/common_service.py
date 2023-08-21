from sqlalchemy.dialects import postgresql


def show_raw_sql(query):
    try:
        print(str(query.statement.compile(dialect=postgresql.dialect())))
    except AttributeError as error:
        print(f"{show_raw_sql.__name__}: {error}")
