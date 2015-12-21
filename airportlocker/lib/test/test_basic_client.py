from airportlocker.lib.client import AirportLockerClient
from airportlocker.lib.test import AirportlockerTest


class TestBasicClient(AirportlockerTest):

    def test_upload_file(self):
        client = AirportLockerClient(self.base_url)
        result = client.create(self.test_file, {'foo': 'bar'})
        assert result

        remote_file = client.read(self.test_filename)
        assert remote_file == open(self.test_file, 'rb').read()
