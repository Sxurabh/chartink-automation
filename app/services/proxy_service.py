# app/services/proxy_service.py
import asyncio
from typing import Dict, List, Optional
from ..core.config import settings
from ..utils.logger import log

class ProxyValidator:
    @staticmethod
    async def _test_proxy(proxy_str: str, timeout: int) -> Optional[Dict[str, str]]:
        try:
            host, port_str = proxy_str.split(":")
            port = int(port_str)
            _, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port),
                timeout=timeout
            )
            writer.close()
            await writer.wait_closed()
            if proxy_str.startswith("socks4://") or proxy_str.startswith("socks5://"):
                return {"server": proxy_str}
            return {"server": f"http://{proxy_str}"}
        except (ValueError, OSError, asyncio.TimeoutError):
            return None

    @staticmethod
    async def validate_all(proxies_raw: List[str]) -> List[Dict[str, str]]:
        timeout = settings.proxy_validate_timeout
        max_proxies = settings.proxy_validate_max

        to_validate = proxies_raw[:max_proxies] if max_proxies > 0 else proxies_raw
        log.info(f"Validating {len(to_validate)} proxies (timeout={timeout}s)...")

        tasks = [ProxyValidator._test_proxy(line, timeout) for line in to_validate]
        results = await asyncio.gather(*tasks)

        valid = [r for r in results if r is not None]
        failed = len(to_validate) - len(valid)
        if failed:
            log.warning(f"{failed} proxies failed validation")
        log.info(f"{len(valid)} proxies passed validation")
        return valid
