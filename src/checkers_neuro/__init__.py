"""Checkers Neuro Client - Neuro API client for Checkers game."""

# Programmed by CoolCat467

from __future__ import annotations

# Checkers Neuro Client - Neuro API client for Checkers game
# Copyright (C) 2025  CoolCat467
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

__title__ = "Checkers Neuro Client"
__author__ = "CoolCat467"
__version__ = "0.0.0"
__license__ = "GNU General Public License Version 3"


import sys
import traceback
from typing import TYPE_CHECKING

import trio
from checkers.client import read_advertisements
from checkers.state import Action
from checkers_computer_players import machine_client
from libcomponent.component import (
    Event,
    ExternalRaiseManager,
)
from neuro_api.event import NeuroAPIComponent

if sys.version_info < (3, 11):
    from exceptiongroup import BaseExceptionGroup

if TYPE_CHECKING:
    from trio_websocket import WebSocketConnection


class ComputerPlayer(machine_client.BaseRemoteState):
    """Computer player."""

    __slots__ = ()

    async def handle_perform_turn(self) -> None:
        """Perform turn."""
        print("preform_turn")
        print(str(self.state))
        action = Action((0, 0), (1, 1))
        await self.perform_action(action)
        raise NotImplementedError()


class NeuroComponent(NeuroAPIComponent):
    """Neuro Component."""

    __slots__ = ()

    def __init__(self, websocket: WebSocketConnection | None = None) -> None:
        """Initialize Neuro Component."""
        super().__init__("NeuroComponent", "Checkers", websocket)


async def run_client(
    event_manager: ExternalRaiseManager,
    host: str,
    port: int,
) -> None:
    """Run machine client and raise tick events."""
    async with trio.open_nursery():
        client = machine_client.MachineClient(ComputerPlayer)
        with event_manager.temporary_component(client):
            async with client.client_with_block():
                await event_manager.raise_event(
                    Event("client_connect", (host, port)),
                )
                print(f"Connected to server {host}:{port}")
                try:
                    while client.running:  # noqa: ASYNC110
                        # Wait so backlog things happen
                        await trio.sleep(1)
                except KeyboardInterrupt:
                    print("Shutting down client from keyboard interrupt.")
                    await event_manager.raise_event(
                        Event("network_stop", None),
                    )
        print(f"Disconnected from server {host}:{port}")
        client.unbind_components()


async def run_client_in_local_servers() -> None:
    """Run client in local servers."""
    print("Watching for advertisements...\n(CTRL + C to quit)")
    try:
        async with trio.open_nursery(
            strict_exception_groups=True,
        ) as main_nursery:
            event_manager = ExternalRaiseManager(
                "checkers",
                main_nursery,
                "client",
            )
            while True:
                advertisements = set(await read_advertisements())
                for motd, server in advertisements:
                    print(f"Found server ({motd = })")
                    await run_client(event_manager, *server)
                    break
                if not advertisements:
                    await trio.sleep(1)
    except BaseExceptionGroup as exc:
        for ex in exc.exceptions:
            if isinstance(ex, KeyboardInterrupt):
                print("Shutting down from keyboard interrupt.")
                break
        else:
            raise


def cli_run() -> None:
    """Run ComputerPlayer clients in local servers."""
    print(f"{__title__} v{__version__}\nProgrammed by {__author__}.\n")
    try:
        trio.run(run_client_in_local_servers)
    except Exception:
        traceback.print_exc()


if __name__ == "__main__":
    cli_run()
