
from itertools import cycle

class LoadBalancer:
    def __init__(self, service_urls):
        self.service_urls = cycle(service_urls)

    def get_next_service_url(self):
        return next(self.service_urls)

