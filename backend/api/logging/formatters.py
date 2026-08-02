"""
Logging Formatters
==================
Formatadores customizados para logs estruturados.
"""
import logging
import json
from datetime import datetime


class VerboseFormatter(logging.Formatter):
    """
    Formato legível para console e ficheiros.
    Inclui: timestamp | level | logger | request_id | user | ip | mensagem
    """

    FORMAT = (
        '[%(asctime)s] %(levelname)-8s %(name)s | '
        'req=%(request_id)s user=%(user)s ip=%(ip)s | '
        '%(message)s'
    )
    DATEFMT = '%Y-%m-%d %H:%M:%S'

    def format(self, record: logging.LogRecord) -> str:
        # Garantir campos mesmo que o filtro não tenha corrido
        for field in ('request_id', 'user', 'ip', 'method', 'path'):
            if not hasattr(record, field):
                setattr(record, field, '-')
        formatter = logging.Formatter(self.FORMAT, datefmt=self.DATEFMT)
        return formatter.format(record)


class JSONFormatter(logging.Formatter):
    """
    Formato JSON para integração com ferramentas de log centralizado (Loki, ELK, etc.).
    Cada linha de log é um objecto JSON válido.
    """

    def format(self, record: logging.LogRecord) -> str:
        data = {
            'timestamp': datetime.utcfromtimestamp(record.created).isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'request_id': getattr(record, 'request_id', '-'),
            'user': getattr(record, 'user', '-'),
            'ip': getattr(record, 'ip', '-'),
            'method': getattr(record, 'method', '-'),
            'path': getattr(record, 'path', '-'),
        }
        if record.exc_info:
            data['exception'] = self.formatException(record.exc_info)
        return json.dumps(data, ensure_ascii=False)
