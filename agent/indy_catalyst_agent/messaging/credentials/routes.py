"""Connection handling admin routes."""

import json

from aiohttp import web
from aiohttp_apispec import docs, request_schema, response_schema
from marshmallow import fields, Schema

from .manager import CredentialManager
from .models.credential_exchange import CredentialExchange

from ..connections.manager import ConnectionManager
from ..connections.models.connection_record import ConnectionRecord

from ...storage.error import StorageNotFoundError


class CredentialOfferRequestSchema(Schema):
    """Result schema for a new connection invitation."""

    connection_id = fields.Str(required=True)
    credential_definition_id = fields.Str(required=True)


class CredentialOfferResultSchema(Schema):
    """Result schema for a new connection invitation."""

    credential_id = fields.Str()


class CredentialRequestResultSchema(Schema):
    """Result schema for a new connection invitation."""

    credential_id = fields.Str()


class CredentialIssueResultSchema(Schema):
    """Result schema for a new connection invitation."""

    credential_id = fields.Str()


@docs(tags=["credential_exchange"], summary="Fetch all credential exchange records")
# @response_schema(ConnectionListSchema(), 200)
async def credential_exchange_list(request: web.BaseRequest):
    """
    Request handler for searching connection records.

    Args:
        request: aiohttp request object

    Returns:
        The connection list response

    """
    context = request.app["request_context"]
    tag_filter = {}
    for param_name in (
        "connection_id",
        "initiator",
        "state",
        "credential_definition_id",
        "schema_id",
    ):
        if param_name in request.query and request.query[param_name] != "":
            tag_filter[param_name] = request.query[param_name]
    records = await CredentialExchange.query(context.storage, tag_filter)
    return web.json_response({"results": [record.serialize() for record in records]})


@docs(tags=["credential_exchange"], summary="Fetch a single credential exchange record")
# @response_schema(ConnectionRecordSchema(), 200)
async def credential_exchange_retrieve(request: web.BaseRequest):
    """
    Request handler for fetching a single connection record.

    Args:
        request: aiohttp request object

    Returns:
        The connection record response

    """
    context = request.app["request_context"]
    credential_exchange_id = request.match_info["id"]
    try:
        record = await CredentialExchange.retrieve_by_id(
            context.storage, credential_exchange_id
        )
    except StorageNotFoundError:
        return web.HTTPNotFound()
    return web.json_response(record.serialize())


@docs(tags=["credential_exchange"], summary="Sends a credential offer")
@request_schema(CredentialOfferRequestSchema())
@response_schema(CredentialOfferResultSchema(), 200)
async def credential_exchange_send_offer(request: web.BaseRequest):
    """
    Request handler for sending a credential offer.

    Args:
        request: aiohttp request object

    Returns:
        The credential offer details.

    """

    context = request.app["request_context"]
    outbound_handler = request.app["outbound_message_router"]

    body = await request.json()

    connection_id = body.get("connection_id")
    credential_definition_id = body.get("credential_definition_id")

    connection_manager = ConnectionManager(context)
    credential_manager = CredentialManager(context)

    connection_record = await ConnectionRecord.retrieve_by_id(
        context.storage, connection_id
    )

    connection_target = await connection_manager.get_connection_target(
        connection_record
    )

    # TODO: validate connection_record valid

    credential_exchange_record, credential_offer_message = await credential_manager.create_offer(
        credential_definition_id, connection_id
    )

    await outbound_handler(credential_offer_message, connection_target)

    return web.json_response(credential_exchange_record.serialize())


@docs(tags=["credential_exchange"], summary="Sends a credential request")
@response_schema(CredentialRequestResultSchema(), 200)
async def credential_exchange_send_request(request: web.BaseRequest):
    """
    Request handler for sending a credential request.

    Args:
        request: aiohttp request object

    Returns:
        The credential request details.

    """

    context = request.app["request_context"]
    outbound_handler = request.app["outbound_message_router"]

    credential_exchange_id = request.match_info["id"]
    credential_exchange_record = await CredentialExchange.retrieve_by_id(
        context.storage, credential_exchange_id
    )

    assert(credential_exchange_record.state, CredentialExchange.STATE_OFFER_RECEIVED)

    credential_manager = CredentialManager(context)
    connection_manager = ConnectionManager(context)

    connection_record = await ConnectionRecord.retrieve_by_id(
        context.storage, credential_exchange_record.connection_id
    )

    connection_target = await connection_manager.get_connection_target(
        connection_record
    )

    credential_exchange_record, credential_request_message = await credential_manager.create_request(
        credential_exchange_record
    )

    await outbound_handler(credential_request_message, connection_target)
    return web.json_response(credential_exchange_record.serialize())


@docs(tags=["credential_exchange"], summary="Sends a credential")
@response_schema(CredentialIssueResultSchema(), 200)
async def credential_exchange_issue(request: web.BaseRequest):
    """
    Request handler for sending a credential.

    Args:
        request: aiohttp request object

    Returns:
        The credential details.

    """
    # TODO: Once the entire credential flow is not automatic, we can allow
    #       manual triggering of issueing a credential
    pass


async def register(app: web.Application):
    """Register routes."""
    app.add_routes([web.get("/credential_exchange", credential_exchange_list)])
    app.add_routes([web.get("/credential_exchange/{id}", credential_exchange_retrieve)])
    app.add_routes(
        [web.post("/credential_exchange/send-offer", credential_exchange_send_offer)]
    )
    app.add_routes(
        [
            web.post(
                "/credential_exchange/{id}/send-request",
                credential_exchange_send_request,
            )
        ]
    )
    app.add_routes(
        [web.post("/credential_exchange/{id}/issue", credential_exchange_issue)]
    )
