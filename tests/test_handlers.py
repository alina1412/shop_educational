import logging

import pytest
import sqlalchemy

from service.db_setup.models import OrderItem

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


async def test_client_order_sum_handler(prepare_orders_for_statistic, client):
    url = "client-order-sum"
    response = await client.get(url)
    assert response.status_code == 200
    assert response.json() == [{"name": "Test Client", "total_sum": 185.0}]


async def test_add_to_order_handler(prepare_product_and_order, client):
    url = "/add-to-cart"
    order_id = 1
    product_id = 1
    quantity = 2
    response = await client.post(
        url
        + f"?order_id={order_id}&product_id={product_id}&quantity={quantity}"
    )
    assert response.status_code == 200


async def test_add_to_order_handler_twice_not_enough(
    prepare_product_and_order, client
):
    """Second time - there's not enough product in stock"""
    url = "/add-to-cart"
    order_id = 1
    product_id = 1
    quantity_1 = 2
    quantity_2 = 1
    response = await client.post(
        url
        + f"?order_id={order_id}&product_id={product_id}&quantity={quantity_1}"
    )
    assert response.status_code == 200

    response = await client.post(
        url
        + f"?order_id={order_id}&product_id={product_id}&quantity={quantity_2}"
    )
    assert response.status_code == 400


async def test_add_to_order_handler_twice_same_orderitem(
    prepare_product_and_order, client, get_async_session
):
    url = "/add-to-cart"
    order_id = 1
    product_id = 1
    quantity_1 = 1
    quantity_2 = 1

    session = get_async_session

    async def get_order_item():
        return (
            await session.execute(
                sqlalchemy.select(OrderItem).where(
                    OrderItem.order_id == order_id,
                    OrderItem.product_id == product_id,
                )
            )
        ).scalar_one_or_none()

    order_item = await get_order_item()
    assert order_item is None
    assert 1
    response = await client.post(
        url
        + f"?order_id={order_id}&product_id={product_id}&quantity={quantity_1}"
    )
    assert response.status_code == 200

    order_item = await get_order_item()
    assert order_item.quantity == quantity_1
    order_item_id = order_item.id

    response = await client.post(
        url
        + f"?order_id={order_id}&product_id={product_id}&quantity={quantity_2}"
    )
    assert response.status_code == 200

    await session.refresh(order_item)
    assert order_item.quantity == quantity_1 + quantity_2
    assert order_item.id == order_item_id


async def test_add_to_order_handler_not_enough_product(
    prepare_product_and_order, client
):
    url = "/add-to-cart"
    order_id = 1
    product_id = 1
    quantity = 90
    response = await client.post(
        url
        + f"?order_id={order_id}&product_id={product_id}&quantity={quantity}"
    )
    assert response.status_code == 400


async def test_add_to_order_handler_422_1(client):
    url = "/add-to-cart"
    order_id = 1
    product_id = 2
    quantity = 3
    response = await client.post(
        url + f"?product_id={product_id}&quantity={quantity}"
    )
    assert response.status_code == 422


async def test_add_to_order_handler_422_2(client):
    url = "/add-to-cart"
    order_id = 1
    product_id = 2
    quantity = 3
    response = await client.post(
        url + f"?order_id={order_id}&quantity={quantity}"
    )
    assert response.status_code == 422


async def test_add_to_order_handler_422_3(client):
    url = "/add-to-cart"
    order_id = 1
    product_id = 2
    quantity = 3
    response = await client.post(
        url + f"?order_id={order_id}&product_id={product_id}"
    )
    assert response.status_code == 422


async def test_add_to_order_handler_422_4(client):
    url = "/add-to-cart"
    order_id = "a"
    product_id = 2
    quantity = 3
    response = await client.post(
        url
        + f"?order_id={order_id}&product_id={product_id}&quantity={quantity}"
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


async def test_count_subcategories_handler(prepare_subcategories, client):
    response = await client.get("/count-subcategories")
    assert response.status_code == 200
    data = response.json()

    assert data == [
        {"title": "Electronics", "subcategories_count": 2},
        {"title": "Smartphones", "subcategories_count": 2},
        {"title": "Laptops", "subcategories_count": 1},
        {"title": "Android Phones", "subcategories_count": 0},
        {"title": "iPhones", "subcategories_count": 0},
        {"title": "Gaming Laptops", "subcategories_count": 0},
    ]


async def test_statistics_handler(prepare_orders_for_statistic, client):
    response = await client.get("/statistic-order")
    assert response.status_code == 200
    data = response.json()
    assert data == [
        {
            "product_name": "BookA",
            "category_name": "Books",
            "total_quantity": 3,
        },
        {
            "product_name": "SmartphoneX",
            "category_name": "Electronics",
            "total_quantity": 2,
        },
    ]
