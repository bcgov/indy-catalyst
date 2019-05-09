"""Action menu message handler."""

from ...base_handler import BaseHandler, BaseResponder, RequestContext
from ..messages.menu import Menu
from ..util import save_connection_menu


class MenuHandler(BaseHandler):
    """Message handler class for action menus."""

    async def handle(self, context: RequestContext, responder: BaseResponder):
        """
        Message handler logic for action menus.

        Args:
            context: request context
            responder: responder callback
        """
        self._logger.debug(f"MenuHandler called with context {context}")
        assert isinstance(context.message, Menu)

        self._logger.info("Received action menu: %s", context.message)

        await save_connection_menu(
            context.message,
            context.connection_record.connection_id,
            context.storage,
            context.service_factory,
        )
        self._logger.debug(
            "Updated action menu on connection: %s",
            context.connection_record.connection_id,
        )
