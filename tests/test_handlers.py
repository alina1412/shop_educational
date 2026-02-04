import logging

import pytest

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


async def test_statistic_handler(client):
    url = "statistic-order"
    response = await client.get(url)
    assert response.status_code == 200


async def test_add_order_handler(client):
    url = "/add-to-cart"
    order_id = 1
    product_id = 2
    quantity = 3
    response = await client.post(
        url
        + f"?order_id={order_id}&product_id={product_id}&quantity={quantity}"
    )
    assert response.status_code == 200
