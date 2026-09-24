from superset.app import create_app

app = create_app()
with app.app_context():
    from superset import db
    from superset.models.core import Database
    trino_db = db.session.query(Database).filter_by(database_name="Trino").first()
    if not trino_db:
        trino_db = Database(
            database_name="Trino",
            sqlalchemy_uri="trino://admin@trino:8080/iceberg",
            expose_in_sqllab=True,
            allow_ctas=True,
            allow_cvas=True,
            allow_dml=True,
            allow_run_async=False
        )
        db.session.add(trino_db)
        db.session.commit()
        print("Trino database successfully auto-registered in Superset!")
    else:
        print("Trino database already exists in Superset.")