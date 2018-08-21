#
# Copyright 2017-2018 Government of Canada
# Public Services and Procurement Canada - buyandsell.gc.ca
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

"""
Importing this file causes the standard settings to be loaded
and a standard service manager to be created. This allows services
to be properly initialized before the webserver process has forked.
"""

import logging
import os
import platform

from django.conf import settings

from vonx.common.eventloop import run_coro
from vonx.indy.manager import IndyManager

LOGGER = logging.getLogger(__name__)


def get_genesis_path():
    if platform.system() == "Windows":
        txn_path = os.path.realpath("./genesis")
    else:
        txn_path = "/home/indy/genesis"
    txn_path = os.getenv("INDY_GENESIS_PATH", txn_path)
    return txn_path

def indy_client():
    return MANAGER.get_client()

def indy_env():
    return {
        "INDY_GENESIS_PATH": get_genesis_path(),
        "INDY_LEDGER_URL": os.environ.get("LEDGER_URL"),
    }

def indy_holder_id():
    return settings.INDY_HOLDER_ID

def indy_verifier_id():
    return settings.INDY_VERIFIER_ID

def pre_init():
    #MANAGER.start_process()
    MANAGER.start()
    run_coro(register_services())

async def register_services():

    import asyncio
    await asyncio.sleep(2) # temp fix for messages being sent before exchange has started

    wallet_seed = os.environ.get('INDY_WALLET_SEED')
    if not wallet_seed or len(wallet_seed) is not 32:
        raise Exception('INDY_WALLET_SEED must be set and be 32 characters long.')

    LOGGER.info("Registering holder service")
    client = indy_client()
    holder_wallet_id = await client.register_wallet({
        "name": "TheOrgBook_Holder_Wallet",
        "seed": wallet_seed,
    })
    LOGGER.debug("holder wallet id: %s", holder_wallet_id)
    holder_id = await client.register_holder(holder_wallet_id, {
        "id": indy_holder_id(),
        "name": "TheOrgBook Holder",
    })
    LOGGER.debug("holder id: %s", holder_id)

    LOGGER.info("Registering verifier service")
    verifier_wallet_id = await client.register_wallet({
        "name": "TheOrgBook_Verifier_Wallet",
        "seed": "tob-verifier-wallet-000000000001",
    })
    LOGGER.info("verifier wallet id: %s", verifier_wallet_id)
    verifier_id = await client.register_verifier(verifier_wallet_id, {
        "id": indy_verifier_id(),
        "name": "TheOrgBook Verifier",
    })
    LOGGER.info("verifier id: %s", verifier_id)

    await client.sync()
    LOGGER.info("synced")
    LOGGER.info(await client.get_status())

def shutdown():
    MANAGER.stop()


MANAGER = IndyManager(indy_env())