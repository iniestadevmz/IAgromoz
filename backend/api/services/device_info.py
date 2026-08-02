"""
DeviceInfoService
=================
Extrai informação de dispositivo a partir do User-Agent sem dependências externas.
Usa parsing básico — pode ser substituído por ua-parser/user-agents se instalado.
"""
import re


def parse_device_info(user_agent: str) -> dict:
    """
    Retorna {browser, operating_system, device_type}.
    device_type: mobile | tablet | desktop
    """
    if not user_agent:
        return {'browser': '', 'operating_system': '', 'device_type': 'desktop'}

    ua = user_agent.lower()

    # Device type
    if 'tablet' in ua or 'ipad' in ua:
        device_type = 'tablet'
    elif any(x in ua for x in ['mobile', 'android', 'iphone', 'windows phone']):
        device_type = 'mobile'
    else:
        device_type = 'desktop'

    # Browser
    if 'edg/' in ua or 'edge/' in ua:
        browser = 'Edge'
    elif 'opr/' in ua or 'opera' in ua:
        browser = 'Opera'
    elif 'chrome/' in ua and 'chromium' not in ua:
        browser = 'Chrome'
    elif 'firefox/' in ua:
        browser = 'Firefox'
    elif 'safari/' in ua and 'chrome' not in ua:
        browser = 'Safari'
    elif 'msie' in ua or 'trident/' in ua:
        browser = 'Internet Explorer'
    else:
        browser = 'Unknown'

    # OS
    if 'windows nt' in ua:
        os = 'Windows'
    elif 'mac os x' in ua or 'macos' in ua:
        os = 'macOS'
    elif 'android' in ua:
        os = 'Android'
    elif 'iphone os' in ua or 'ios' in ua:
        os = 'iOS'
    elif 'linux' in ua:
        os = 'Linux'
    else:
        os = 'Unknown'

    return {
        'browser': browser,
        'operating_system': os,
        'device_type': device_type,
    }
