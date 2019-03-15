"""Classes to manage credentials."""

import logging

from ..connections.manager import ConnectionManager
from ..request_context import RequestContext
from ...error import BaseError


class CredentialManagerError(BaseError):
    """Credential error."""


class CredentialManager:
    """Class for managing credentials."""

    def __init__(self, context: RequestContext):
        """
        Initialize a CredentialManager.

        Args:
            context: The context for this credential
        """
        self._context = context
        self._logger = logging.getLogger(__name__)

    async def create_credential_offer(self, credential_definition_id):
        await indy.anoncreds.issuer_create_credential_offer(self.wallet.handle, cd_id)

    async def send_credential_offer(
        self, context, connection_record, schema_name, schema_version
    ):
        """
        Send a credential offer to a connection.

        Args:
            context: The request context
            connection_record: The connection to send the credential offer to
            schema_name: The schema name to send a credential offer for
            schema_version: The schema version to send a credential offer for

        """

        connection_manager = ConnectionManager(context)

        pass