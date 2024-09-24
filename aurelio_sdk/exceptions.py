import aiohttp


class AurelioAPIError(Exception):
    """
    Custom exception for API errors.
    """

    def __init__(self, response):
        if isinstance(response, aiohttp.ClientResponse):
            self.status_code = response.status
        else:
            self.status_code = response.status_code
        try:
            self.error = response.json()
        except ValueError:
            self.error = response.text
        super().__init__(
            f"API request failed with status {self.status_code}: {self.error}"
        )
