"""
Connection management
"""

import aiohttp
import json
import logging

from typing import Tuple, Union

from ...error import BaseError
from ..agent_message import AgentMessage
from .messages.connection_invitation import ConnectionInvitation
from .messages.connection_request import ConnectionRequest
from .messages.connection_response import ConnectionResponse
from ..message_factory import MessageParseError
from .models.connection_detail import ConnectionDetail
from .models.connection_target import ConnectionTarget
from ...models.thread_decorator import ThreadDecorator
from ..request_context import RequestContext
from ..routing.messages.forward import Forward
from ...storage.error import StorageNotFoundError
from ...storage.record import StorageRecord
from ...wallet.error import WalletError, WalletNotFoundError
from ...wallet.util import bytes_to_b64

from von_anchor.a2a import DIDDoc
from von_anchor.a2a.publickey import PublicKey, PublicKeyType
from von_anchor.a2a.service import Service


class ConnectionManagerError(BaseError):
    """Connection error."""


class ConnectionRecord:
    ROLE_ROUTER = "router"
    STATE_INVITED = "invited"
    STATE_REQUESTED = "requested"
    STATE_RESPONDED = "responded"
    STATE_COMPLETE = "complete"

    """Assembles connection state and target information"""

    def __init__(self, state: str, target: ConnectionTarget, role: str = None):
        self.role = role
        self.state = state
        self.target = target


class ConnectionManager:
    """Class for managing connections."""

    def __init__(self, context: RequestContext):
        self._context = context
        self._logger = logging.getLogger(__name__)

    @property
    def context(self) -> RequestContext:
        """Accessor for the current request context"""
        return self._context

    async def create_invitation(
        self, label: str, my_endpoint: str, seed: str = None, metadata: dict = None
    ) -> ConnectionInvitation:
        """
        Generate new connection invitation.
        This interaction represents an out-of-band communication channel. In the future
        and in practice, these sort of invitations will be received over any number of
        channels such as SMS, Email, QR Code, NFC, etc.

        Structure of an invite message:
        {
            "@type": "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/connections/1.0/invitation",
            "label": "Alice",
            "did": "did:sov:QmWbsNYhMrjHiqZDTUTEJs"
        }

        Or, in the case of a peer DID:
        {
            "@type": "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/connections/1.0/invitation",
            "label": "Alice",
            "did": "did:peer:oiSqsNYhMrjHiqZDTUthsw",
            "recipientKeys": ["8HH5gYEeNc3z7PYXmd54d4x6qAfCNrqQqEB3nS7Zfu7K"],
            "serviceEndpoint": "https://example.com/endpoint"
        }
        Currently, only peer DID is supported.
        """
        self._logger.debug("Creating invitation")

        # Create and store new connection key
        connection_key = await self.context.wallet.create_signing_key(
            seed=seed, metadata=metadata
        )
        # may want to store additional metadata on the key (creation date etc.)

        # Create connection invitation message
        invitation = ConnectionInvitation(
            label=label, recipient_keys=[connection_key.verkey], endpoint=my_endpoint
        )
        return invitation

    async def send_invitation(self, invitation: ConnectionInvitation, endpoint: str):
        """
        Deliver an invitation to an HTTP endpoint
        """
        self._logger.debug("Sending invitation to %s", endpoint)
        invite_json = invitation.to_json()
        invite_b64 = bytes_to_b64(invite_json.encode("ascii"), urlsafe=True)
        async with aiohttp.ClientSession() as session:
            await session.get(endpoint, params={"invite": invite_b64})

    async def store_invitation(
        self, invitation: ConnectionInvitation, received: bool, tags: dict = None
    ) -> str:
        """
        Save an invitation for acceptance/rejection and later processing
        """
        # may want to generate another unique ID, or use the message ID
        # instead of the key
        invitation_id = invitation.recipient_keys[0]

        await self.context.storage.add_record(
            StorageRecord(
                "received_invitation" if received else "sent_invitation",
                json.dumps(invitation.serialize()),
                tags,
                invitation_id,
            )
        )
        self._logger.debug(
            "Stored %s invitation: %s",
            "incoming" if received else "outgoing",
            invitation_id,
        )
        return invitation_id

    async def find_invitation(
        self, invitation_id: str, received: bool
    ) -> Tuple[ConnectionInvitation, dict]:
        """
        Locate a previously-received invitation.
        """
        self._logger.debug(
            "Looking up %s invitation: %s",
            "incoming" if received else "outgoing",
            invitation_id,
        )
        # raises StorageNotFoundError if not found
        result = await self.context.storage.get_record(
            "received_invitation" if received else "sent_invitation", invitation_id
        )
        invitation = ConnectionInvitation.deserialize(result.value)
        return invitation, result.tags

    async def remove_invitation(self, invitation_id: str):
        """
        Remove a previously-stored invitation
        """
        # raises StorageNotFoundError if not found
        await self.context.storage.delete_record("invitation", invitation_id)

    async def accept_invitation(
        self,
        invitation: ConnectionInvitation,
        my_label: str = None,
        my_endpoint: str = None,
        my_router_verkey: str = None,
        their_role: str = None,
    ) -> Tuple[ConnectionRequest, ConnectionTarget]:
        """
        Create a new connection request for a previously-received invitation
        """

        their_connection_key = invitation.recipient_keys[0]
        their_endpoint = invitation.endpoint
        their_label = invitation.label
        their_routing_keys = invitation.routing_keys

        # Create my information for connection
        my_info = await self.context.wallet.create_local_did(
            None,
            None,
            {
                "my_router_verkey": my_router_verkey,
                "their_endpoint": their_endpoint,
                "their_label": their_label,
                "their_role": their_role,
                "their_routing_keys": their_routing_keys,
            },
        )
        if not my_endpoint:
            my_endpoint = self.context.default_endpoint
        if not my_label:
            my_label = self.context.default_label

        did_doc = DIDDoc(did=my_info.did)
        controller = my_info.did
        value = my_info.verkey
        pk = PublicKey(
            my_info.did, "1", PublicKeyType.ED25519_SIG_2018, controller, value, True
        )
        did_doc.verkeys.append(pk)

        if my_router_verkey:
            # May raise ConnectionManagerError
            router_conn = await self.find_connection(my_router_verkey)
            router_pk = PublicKey(
                my_info.did,
                "routing",
                PublicKeyType.ED25519_SIG_2018,
                controller,  # TODO: should controller DID match the router's DID?
                router_conn.target.recipient_keys[0],
                False,
            )
            did_doc.verkeys.append(router_pk)
            service = Service(
                my_info.did, "indy", "Agency", router_conn.target.endpoint
            )
            did_doc.services.append(service)
        else:
            service = Service(my_info.did, "indy", "IndyAgent", my_endpoint)
            did_doc.services.append(service)

        # Create connection request message
        request = ConnectionRequest(
            label=my_label,
            connection=ConnectionDetail(did=my_info.did, did_doc=did_doc),
        )

        # Store message so that response can be processed
        await self.context.storage.add_record(
            StorageRecord("connection_request", request.to_json(), {}, request._id)
        )

        # Request must be sent to their_endpoint using their_connection_key,
        # from my_info.verkey
        target = ConnectionTarget(
            endpoint=their_endpoint,
            recipient_keys=[their_connection_key],
            sender_key=my_info.verkey,
        )
        return request, target

    async def find_request(self, request_id: str) -> ConnectionRequest:
        """
        Locate a previously saved connection request
        """
        # raises exception if not found
        result = await self.context.storage.get_record("connection_request", request_id)
        request = ConnectionRequest.deserialize(result.value)
        return request

    async def remove_request(self, request_id: str):
        """
        Remove a previously-stored connection request
        """
        # raises exception if not found
        await self.context.storage.delete_record("connection_request", request_id)

    async def accept_request(
        self, request: ConnectionRequest, my_endpoint: str = None
    ) -> Tuple[ConnectionResponse, ConnectionTarget]:
        """
        Create a connection response for a received connection request.
        """

        invitation = None
        if not self.context.recipient_did_public:
            connection_key = self.context.recipient_verkey
            try:
                invitation, _inv_tags = await self.find_invitation(
                    connection_key, False
                )
            except StorageNotFoundError:
                # temporarily disabled - not requiring an existing invitation
                # raise ConnectionManagerError(
                #   "No invitation found for pairwise connection")
                pass
        self._logger.debug("Found invitation: %s", invitation)
        if not my_endpoint:
            my_endpoint = self.context.default_endpoint

        their_label = request.label
        their_did = request.connection.did
        conn_did_doc = request.connection.did_doc
        their_endpoint = conn_did_doc.services[0].endpoint
        their_routing_keys = []
        their_verkey = None  # may be different from self.context.sender_verkey
        for verkey in conn_did_doc.verkeys:
            if verkey.id == "routing":
                their_routing_keys.append(verkey.value)
            elif not their_verkey:
                their_verkey = verkey.value

        # Create a new pairwise record with a newly-generated local DID
        pairwise = await self.context.wallet.create_pairwise(
            their_did,
            their_verkey,
            None,
            {
                "label": their_label,
                "endpoint": their_endpoint,
                "role": None,
                "routing_keys": their_routing_keys,
                "state": ConnectionRecord.STATE_RESPONDED,
                # TODO: store established & last active dates
            },
        )

        my_did = pairwise.my_did
        did_doc = DIDDoc(did=my_did)
        controller = my_did
        value = pairwise.my_verkey
        pk = PublicKey(
            my_did, "1", PublicKeyType.ED25519_SIG_2018, controller, value, True
        )
        did_doc.verkeys.append(pk)
        service = Service(my_did, "indy", "IndyAgent", my_endpoint)
        did_doc.services.append(service)

        response = ConnectionResponse(
            connection=ConnectionDetail(did=my_did, did_doc=did_doc)
        )
        if request._id:
            response._thread = ThreadDecorator(thid=request._id)
        await response.sign_field(
            "connection", self.context.recipient_verkey, self.context.wallet
        )
        self._logger.debug("Created connection response for %s", their_did)

        # response must be sent to their_endpoint, packed with their_verkey
        # and pairwise.my_verkey
        target = ConnectionTarget(
            endpoint=their_endpoint,
            recipient_keys=[their_verkey],
            sender_key=pairwise.my_verkey,
        )
        return response, target

    async def accept_response(self, response: ConnectionResponse) -> ConnectionTarget:
        """
        Process a ConnectionResponse message by looking up
        the connection request and setting up the pairwise connection
        """
        if response._thread:
            request_id = response._thread.thid
            request = await self.find_request(request_id)
            my_did = request.connection.did
        else:
            my_did = self.context.recipient_did
        if not my_did:
            raise ConnectionManagerError(f"No DID associated with connection response")

        their_did = response.connection.did
        conn_did_doc = response.connection.did_doc
        their_endpoint = conn_did_doc.services[0].endpoint
        their_routing_keys = []
        their_verkey = None
        for verkey in conn_did_doc.verkeys:
            if verkey.id == "routing":
                their_routing_keys.append(verkey.value)
            elif not their_verkey:
                their_verkey = verkey.value

        my_info = await self.context.wallet.get_local_did(my_did)
        their_label = my_info.metadata.get("their_label")
        if not their_endpoint:
            their_endpoint = my_info.metadata.get("their_endpoint")
        if not their_label:
            raise ConnectionManagerError(
                f"DID not associated with a connection: {my_did}"
            )
        their_role = my_info.metadata.get("their_role")

        # update local DID metadata to mark connection as accepted, prevent multiple
        # responses? May also set a creation time on the local DID to allow request
        # expiry.

        # In the final implementation, a signature will be provided to verify changes to
        # the keys and DIDs to be used long term in the relationship.
        # Both the signature and signature check are omitted for now until specifics of
        # the signature are decided.

        # Create a new pairwise record associated with our previously-generated local
        # DID
        # Note: WalletDuplicateError will be raised if their_did already has a
        # connection
        pairwise = await self.context.wallet.create_pairwise(
            their_did,
            their_verkey,
            my_did,
            {
                "endpoint": their_endpoint,
                "label": their_label,
                "role": their_role,
                "routing_keys": their_routing_keys,
                "state": ConnectionRecord.STATE_RESPONDED,
                # TODO: store established & last active dates
            },
        )

        # Store their_verkey on the local DID so we can find the pairwise record
        upd_did_meta = my_info.metadata.copy()
        upd_did_meta["their_verkey"] = their_verkey
        await self.context.wallet.replace_local_did_metadata(my_did, upd_did_meta)

        self._logger.debug("Accepted connection response from %s", their_did)

        target = ConnectionTarget(
            endpoint=their_endpoint,
            recipient_keys=[their_verkey],
            sender_key=pairwise.my_verkey,
        )
        # Caller may wish to send a Trust Ping to verify the endpoint
        # and confirm the connection
        return target

    async def find_connection(
        self, their_verkey: str, my_verkey: str = None, auto_complete=False
    ) -> ConnectionRecord:
        """Look up existing connection information for a sender verkey"""
        try:
            pairwise = await self.context.wallet.get_pairwise_for_verkey(their_verkey)
        except WalletNotFoundError:
            pairwise = None

        if pairwise:
            pairwise_state = pairwise.metadata.get("state")
            pair_meta = pairwise.metadata
            pair_endp = pair_meta.get("endpoint")
            if pairwise_state == ConnectionRecord.STATE_RESPONDED and auto_complete:
                # automatically promote state when a subsequent message is received
                pairwise_state = ConnectionRecord.STATE_COMPLETE
                pair_meta = pair_meta.copy()
                pair_meta.update({"state": pairwise_state})
                await self.context.wallet.replace_pairwise_metadata(
                    pairwise.their_did, pair_meta
                )
                self._logger.debug("Connection promoted to active: %s", their_verkey)
            elif pairwise_state != ConnectionRecord.STATE_COMPLETE or not pair_endp:
                # something wrong with the state
                self._logger.error("Discarding pairwise record, unexpected state")
                return None
            return ConnectionRecord(
                pairwise_state,
                ConnectionTarget(
                    did=pairwise.their_did,
                    endpoint=pair_endp,
                    label=pair_meta.get("label"),
                    recipient_keys=[pairwise.their_verkey],
                    routing_keys=pair_meta.get("routing_keys"),
                    sender_key=pairwise.my_verkey,
                ),
                pair_meta.get("role"),
            )

        if not my_verkey:
            return None

        try:
            did_info = await self.context.wallet.get_local_did(my_verkey)
        except WalletNotFoundError:
            did_info = None
        if did_info:
            did_meta = did_info.metadata
            if did_meta.get("their_verkey"):
                # their_verkey indicates that the connection has been completed,
                # but we didn't find a pairwise record so it must not be active
                self._logger.error("Discarding connection record, missing pairwise")
                return None

            if did_meta.get("their_did") or did_meta.get("their_endpoint"):
                return ConnectionRecord(
                    ConnectionRecord.STATE_REQUESTED,
                    ConnectionTarget(
                        did=did_meta.get("their_did"),
                        endpoint=did_info.metadata.get("their_endpoint"),
                        label=did_meta.get("their_label"),
                        recipient_keys=[their_verkey],
                        routing_keys=did_meta.get("their_routing_keys"),
                        sender_key=my_verkey,
                    ),
                    did_meta.get("their_role"),
                )
            else:
                self._logger.error("Discarding connection record, no DID or endpoint")
                return None

        try:
            invitation, _tags = await self.find_invitation(my_verkey, False)
        except StorageNotFoundError:
            return None
        return ConnectionRecord(
            ConnectionRecord.STATE_INVITED, None  # no target information available
        )

    async def expand_message(
        self, message_body: Union[str, bytes], transport_type: str
    ) -> RequestContext:
        """
        Deserialize an incoming message and further populate the request context
        """
        if not self.context.message_factory:
            raise MessageParseError("Message factory not defined")
        if not self.context.wallet:
            raise MessageParseError("Wallet not defined")

        message_dict = None
        message_json = message_body
        from_verkey = None
        to_verkey = None

        if isinstance(message_body, bytes):
            try:
                unpacked = await self.context.wallet.unpack_message(message_body)
                message_json, from_verkey, to_verkey = unpacked
            except WalletError:
                self._logger.debug("Message unpack failed, trying JSON")

        try:
            message_dict = json.loads(message_json)
        except ValueError:
            raise MessageParseError("Message JSON parsing failed")
        self._logger.debug(f"Extracted message: {message_dict}")

        ctx = self.context.copy()
        ctx.message = ctx.message_factory.make_message(message_dict)
        ctx.transport_type = transport_type

        if from_verkey:
            # must be a packed message for from_verkey to be populated
            ctx.sender_verkey = from_verkey
            conn = await self.find_connection(from_verkey, to_verkey, True)
            if conn:
                ctx.connection_active = conn.state == conn.STATE_COMPLETE
                ctx.connection_target = conn.target
                if conn.target:
                    ctx.sender_did = conn.target.did

        if to_verkey:
            ctx.recipient_verkey = to_verkey
            try:
                did_info = await self.context.wallet.get_local_did_for_verkey(to_verkey)
            except WalletNotFoundError:
                did_info = None
            if did_info:
                ctx.recipient_did = did_info.did
            # TODO set ctx.recipient_did_public if DID is published to the ledger
            # could also choose to set ctx.default_endpoint and ctx.default_label
            # (these things could be stored on did_info.metadata)

        # look up thread information

        # handle any other decorators having special behaviour (timing, trace, etc)

        return ctx

    async def compact_message(
        self, message: Union[AgentMessage, str, bytes], target: ConnectionTarget
    ) -> Union[str, bytes]:
        """
        Serialize an outgoing message for transport
        """
        if isinstance(message, AgentMessage):
            message_json = message.to_json()
            if target.sender_key and target.recipient_keys:
                message = await self.context.wallet.pack_message(
                    message_json, target.recipient_keys, target.sender_key
                )
                if target.routing_keys:
                    recip_keys = target.recipient_keys
                    for router_key in target.routing_keys:
                        fwd_msg = Forward(recip_keys, bytes_to_b64(message))
                        message = await self.context.wallet.pack_message(
                            fwd_msg.to_json(), recip_keys, target.sender_key
                        )
                        recip_keys = [router_key]
            else:
                message = message_json
        return message
