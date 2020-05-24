import logging
import os
import pathlib

import requests
import requests_cache


class RequestsCache:
    def __init__(self, path):
        self.path = os.fspath(path)

    def mkdir(self):
        """make directory containing cache file if it doesn't exist"""
        directory = pathlib.Path(self.path).parent
        directory.mkdir(parents=True, exist_ok=True)

    def install(self):
        """install cache"""
        requests  # require `import requests` in case this is essential for monkey patching by requests_cache.
        requests_cache.install_cache(self.path, include_get_headers=True)
        self.cache = requests_cache.get_cache()
        logging.info(
            f"requests-cache starting with {len(self.cache.responses)} cached responses"
        )

    def clear(self):
        """clear cache"""
        logging.info("Clearing requests-cache")
        requests_cache.clear()

    def close(self):
        """uninstall cache"""
        logging.info(
            f"requests-cache finished with {len(self.cache.responses)} cached responses"
        )
        requests_cache.uninstall_cache()
