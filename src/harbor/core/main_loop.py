from harbor.core.engine import HarborCore


class HarborMainLoop:
    def __init__(self, bridge, return_channel, core=None, logger=None):
        self.bridge = bridge
        self.return_channel = return_channel
        self.core = core or HarborCore()
        self.logger = logger

    def run_once(self) -> bool:
        request = self.bridge.receive()

        if request is None:
            return False

        if self.logger:
            self.logger.info(
                "Received request source=%s sender=%s text=%s",
                request.source,
                request.sender,
                request.text,
            )

        response = self.core.handle(request)

        if self.logger:
            self.logger.info(
                "Generated response handled_by=%s success=%s text=%s",
                response.handled_by,
                response.success,
                response.text,
            )

        self.return_channel.send(response)

        return True

    def run_forever(self) -> None:
        if self.logger:
            self.logger.info("Harbor Main Loop started.")

        try:
            while True:
                should_continue = self.run_once()

                if not should_continue:
                    break
        except KeyboardInterrupt:
            print("")
        finally:
            if self.logger:
                self.logger.info("Harbor Main Loop stopped.")
            print("Harbor 已退出。")
