from logging.config import dictConfig

from personalsaving.settings import Settings


def configure_logging(settings: Settings) -> None:

    if settings.environment_name == "production":
        log_format = ""
    elif settings.environment_name == "development":
        log_format = "%(levelprefix)s %(name)s: %(message)s"

    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "()": "uvicorn.logging.DefaultFormatter",
                "format": log_format,
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "standard",
            },
        },
        "root": {
            "level": settings.log_level,
            "handlers": ["console"],
        },
        "loggers": {
            "uvicorn": {
                "handlers": [],
                "propagate": True,
            },
        },
    }

    dictConfig(config)
