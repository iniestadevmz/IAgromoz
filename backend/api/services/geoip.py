"""
GeoIP Service
=============
Interface desacoplada para resolução de geolocalização por IP.
Actualmente retorna dados vazios — pronta para integrar qualquer provider
(MaxMind GeoIP2, ip-api.com, ipinfo.io, etc.) sem alterar o restante sistema.

Para activar:
1. Instalar o provider: pip install geoip2
2. Implementar um GeoIPProvider concreto
3. Registar em GEOIP_PROVIDER no settings
"""
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class GeoIPResult:
    country: str = ''
    city: str = ''
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    timezone: str = ''
    isp: str = ''


class BaseGeoIPProvider:
    """Interface base para providers de GeoIP."""

    def lookup(self, ip: str) -> GeoIPResult:
        raise NotImplementedError


class NullGeoIPProvider(BaseGeoIPProvider):
    """Provider nulo — retorna dados vazios. Usado por defeito."""

    def lookup(self, ip: str) -> GeoIPResult:
        return GeoIPResult()


def get_geoip_info(ip: str) -> GeoIPResult:
    """
    Resolve geolocalização de um IP.
    Usa o provider configurado em settings.GEOIP_PROVIDER ou NullGeoIPProvider.
    Nunca lança exceções.
    """
    try:
        from django.conf import settings
        provider_path = getattr(settings, 'GEOIP_PROVIDER', None)
        if provider_path:
            from django.utils.module_loading import import_string
            provider_cls = import_string(provider_path)
            return provider_cls().lookup(ip)
    except Exception:
        pass
    return NullGeoIPProvider().lookup(ip)
