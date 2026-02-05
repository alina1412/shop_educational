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


async def test_add_order_handler_422_1(client):
    url = "/add-to-cart"
    order_id = 1
    product_id = 2
    quantity = 3
    response = await client.post(
        url + f"?product_id={product_id}&quantity={quantity}"
    )
    assert response.status_code == 422


async def test_add_order_handler_422_2(client):
    url = "/add-to-cart"
    order_id = 1
    product_id = 2
    quantity = 3
    response = await client.post(
        url + f"?order_id={order_id}&quantity={quantity}"
    )
    assert response.status_code == 422


async def test_add_order_handler_422_3(client):
    url = "/add-to-cart"
    order_id = 1
    product_id = 2
    quantity = 3
    response = await client.post(
        url + f"?order_id={order_id}&product_id={product_id}"
    )
    assert response.status_code == 422


async def test_add_to_cart_product_not_found(
    client, prepare_product_and_order
):
    NOT_EXISTING_PRODUCT_ID = 9999
    order_id = 1
    quantity = 1
    response = await client.post(
        f"/add-to-cart?order_id={order_id}&product_id={NOT_EXISTING_PRODUCT_ID}&quantity={quantity}"
    )
    assert response.status_code == 404


async def test_add_to_cart_order_not_found(client):
    NOT_EXISTING_ORDER_ID = 9999
    product_id = 1
    quantity = 1
    response = await client.post(
        f"/add-to-cart?order_id={NOT_EXISTING_ORDER_ID}&product_id={product_id}&quantity={quantity}"
    )
    assert response.status_code == 404
