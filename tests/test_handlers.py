import logging

import pytest

pytest_plugins = ("pytest_asyncio",)
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


async def test_statistic_handler(client):
    url = "statistic-order"
    response = await client.get(url)
    assert response.status_code == 200


async def test_add_order_handler(client):
    url = "add-too-cart"
    response = await client.get(url)
    assert response.status_code == 404
