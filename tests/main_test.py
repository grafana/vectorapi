from unittest import mock
from unittest.mock import Mock

import fastapi.testclient

from vectorapi import main


class AnyStringWith(str):
    def __eq__(self, other):
        return self in other


def test_healthz():
    app = main.create_app()
    client = fastapi.testclient.TestClient(app)
    response = client.get("/healthz")
    assert response.status_code == 200


@mock.patch("vectorapi.main.loguru.logger")
def test_endpoints_have_log(logger):
    patch_mock = Mock()
    logger.patch.return_value = patch_mock
    app = main.create_app()
    client = fastapi.testclient.TestClient(app)
    client.get("/")
    patch_mock.info.assert_called_once_with(
        AnyStringWith("Request failed, GET /, status code=404, took=")
    )
