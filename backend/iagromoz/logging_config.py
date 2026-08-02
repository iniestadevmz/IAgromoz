"""
Logging configuration — importado no settings.py.
"""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
LOGS_DIR = BASE_DIR / 'logs'
LOGS_DIR.mkdir(exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,

    'filters': {
        'request_context': {
            '()': 'api.logging.filters.RequestContextFilter',
        },
        'skip_health_check': {
            '()': 'api.logging.filters.SkipHealthCheckFilter',
        },
    },

    'formatters': {
        'verbose': {
            '()': 'api.logging.formatters.VerboseFormatter',
        },
        'json': {
            '()': 'api.logging.formatters.JSONFormatter',
        },
        'simple': {
            'format': '[%(asctime)s] %(levelname)s %(name)s — %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
    },

    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
            'filters': ['request_context'],
        },
        'file_django': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': str(LOGS_DIR / 'django.log'),
            'maxBytes': 5 * 1024 * 1024,
            'backupCount': 5,
            'formatter': 'verbose',
            'filters': ['request_context'],
        },
        'file_error': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': str(LOGS_DIR / 'error.log'),
            'maxBytes': 5 * 1024 * 1024,
            'backupCount': 5,
            'formatter': 'verbose',
            'filters': ['request_context'],
            'level': 'ERROR',
        },
        'file_api': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': str(LOGS_DIR / 'api.log'),
            'maxBytes': 5 * 1024 * 1024,
            'backupCount': 5,
            'formatter': 'verbose',
            'filters': ['request_context', 'skip_health_check'],
        },
        'file_security': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': str(LOGS_DIR / 'security.log'),
            'maxBytes': 5 * 1024 * 1024,
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'file_sql': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': str(LOGS_DIR / 'sql.log'),
            'maxBytes': 5 * 1024 * 1024,
            'backupCount': 5,
            'formatter': 'simple',
        },
    },

    'loggers': {
        'django': {
            'handlers': ['console', 'file_django', 'file_error'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console', 'file_django', 'file_error'],
            'level': 'WARNING',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['file_sql'],
            'level': 'WARNING',
            'propagate': False,
        },
        'api': {
            'handlers': ['console', 'file_api', 'file_error'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'api.audit': {
            'handlers': ['console', 'file_api'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'api.security': {
            'handlers': ['console', 'file_security', 'file_error'],
            'level': 'INFO',
            'propagate': False,
        },
        'api.requests': {
            'handlers': ['console', 'file_api'],
            'level': 'INFO',
            'propagate': False,
        },
        'api.exceptions': {
            'handlers': ['console', 'file_error'],
            'level': 'ERROR',
            'propagate': False,
        },
    },

    'root': {
        'handlers': ['console', 'file_django'],
        'level': 'WARNING',
    },
}
