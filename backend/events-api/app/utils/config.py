import os

config_variables = {
    "POSTGRES_DB_PASSWORD": os.getenv("POSTGRES_DB_PASSWORD") or "no db password",
    "POSTGRES_DB_USER": os.getenv("POSTGRES_DB_USER") or "no db user",
    "POSTGRES_DB_HOST": os.getenv("POSTGRES_DB_HOST") or "postgres",
    "POSTGRES_DB_PORT": os.getenv("POSTGRES_DB_PORT") or "5432",
    "POSTGRES_DB_NAME": os.getenv("POSTGRES_DB_NAME") or "eventsdb",
    "POSTGRES_DB_SCHEMA": os.getenv("POSTGRES_DB_SCHEMA") or "postgres"
}


class Config(object):
    def __init__(self):
        self._config = config_variables

    def get_property(self, property_name):
        if property_name not in self._config.keys():
            return None
        return self._config[property_name]


class BasicConfig(Config):

    @property
    def POSTGRES_DB_HOST(self):
        return self.get_property("POSTGRES_DB_HOST")

    @property
    def POSTGRES_DB_PORT(self):
        return self.get_property("POSTGRES_DB_PORT")

    @property
    def POSTGRES_DB_PASSWORD(self):
        return self.get_property("POSTGRES_DB_PASSWORD")

    @property
    def POSTGRES_DB_USER(self):
        return self.get_property("POSTGRES_DB_USER")

    @property
    def POSTGRES_DB_NAME(self):
        return self.get_property("POSTGRES_DB_NAME")

    @property
    def DATABASE_SCHEMA(self):
        return self.get_property("POSTGRES_DB_SCHEMA")

    @property
    def DATABASE_URL(self):
        return f"postgresql://{self.POSTGRES_DB_USER}:{self.POSTGRES_DB_PASSWORD}@{self.POSTGRES_DB_HOST}:{self.POSTGRES_DB_PORT}/{self.POSTGRES_DB_NAME}"

    # Keep old property names for backward compatibility
    @property
    def db_host(self):
        return self.POSTGRES_DB_HOST

    @property
    def db_port(self):
        return self.POSTGRES_DB_PORT

    @property
    def db_password(self):
        return self.POSTGRES_DB_PASSWORD

    @property
    def db_user(self):
        return self.POSTGRES_DB_USER

    @property
    def db_name(self):
        return self.POSTGRES_DB_NAME

    @property
    def db_schema(self):
        return self.DATABASE_SCHEMA


config_by_name = dict(
    BasicConfig=BasicConfig()
)

# Create settings alias for easier access
settings = BasicConfig()
