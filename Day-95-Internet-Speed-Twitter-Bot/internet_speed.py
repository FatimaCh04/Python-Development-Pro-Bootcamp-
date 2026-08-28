import speedtest


class InternetSpeedTester:

    def __init__(self):
        self.speed_test = speedtest.Speedtest()

    def get_speed(self):

        print("Finding the best speed test server...")

        self.speed_test.get_best_server()

        print("Testing download speed...")

        download = (
            self.speed_test.download()
            / 1_000_000
        )

        print("Testing upload speed...")

        upload = (
            self.speed_test.upload()
            / 1_000_000
        )

        return download, upload