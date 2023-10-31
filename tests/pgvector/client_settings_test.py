from vectorapi.pgvector.client_settings import Settings

POSTGRES_USER = "foo"
POSTGRES_DB = "BAR"
POSTGRES_PASSWORD = "mysecretpassword"
POSTGRES_HOST = "pgmock"
POSTGRES_PORT = 5431
EXPECTED = (
    f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@"
    f"{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)


class TestSettings:
    # make sure that the default settings are correct
    def test_default_settings(self):
        settings = Settings(
            POSTGRES_USER=POSTGRES_USER,
            POSTGRES_DB=POSTGRES_DB,
            POSTGRES_HOST=POSTGRES_HOST,
            POSTGRES_PASSWORD=POSTGRES_PASSWORD,
            POSTGRES_PORT=POSTGRES_PORT,
        )
        assert settings.SQLALCHEMY_DATABASE_URL == EXPECTED

    def test_with_db_url(self):
        settings = Settings(DB_URL=EXPECTED)
        assert settings.SQLALCHEMY_DATABASE_URL == EXPECTED
