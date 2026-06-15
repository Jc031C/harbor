from harbor.core.models import HarborResponse


class LocalConsoleReturnChannel:
    def send(self, response: HarborResponse) -> None:
        print(f"Harbor > {response.text}")
        print("")
