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
from checkers_computer_players import machine_client
from libcomponent.component import (
    Event,
    ExternalRaiseManager,
)
from neuro_api.command import Action as CommandAction
from neuro_api.trio_ws import TrioNeuroAPIComponent

if sys.version_info < (3, 11):
    from exceptiongroup import BaseExceptionGroup

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from checkers.state import Action as GameAction, Pos, State
    from neuro_api.api import NeuroAction
    from trio_websocket import WebSocketConnection


class ComputerPlayer(machine_client.BaseRemoteState):
    """Computer player."""

    __slots__ = ()

    def bind_handlers(self) -> None:
        """Register event handlers."""
        super().bind_handlers()

        self.register_handlers(
            {
                "submit_move": self.handle_submit_move,
                "network_stop": self.handle_network_stop,
            },
        )

    async def base_perform_turn(self) -> None:
        """Perform turn."""
        self.moves += 1
        winner = self.state.check_for_win()
        if winner is not None:
            print("Terminal state, not performing turn")
            value = ("Lost", "Won")[winner == self.playing_as]
            message = f"{value} after {self.moves} moves"
            print(message)
            await self.raise_event(
                Event("send_neuro_context", (f"You {message}", False), 1),
            )
            return
        await self.handle_perform_turn()

    async def handle_action_complete(
        self,
        event: Event[tuple[Pos, Pos, int]],
    ) -> None:
        """Perform action on internal state and perform our turn if possible."""
        from_pos, to_pos, turn = event.data
        # types: has-type error: Cannot determine type of "state"
        action = self.state.action_from_points(from_pos, to_pos)
        # types: ^^^^^^^^^^
        # types: misc error: Trying to assign name "state" that is not in "__slots__" of type "checkers_neuro.ComputerPlayer"
        # types: has-type error: Cannot determine type of "state"
        self.state = self.state.perform_action(action)
        # types: ^   ^^^^^^^^^^
        ##        print(f'{turn = }')
        if turn == self.playing_as:
            await self.base_perform_turn()
        else:
            state_context = build_state_context(self.state)
            await self.raise_event(
                Event(
                    "send_neuro_context",
                    (
                        f"Opponent moved from {from_pos} to {to_pos}\n{state_context}",
                        True,
                    ),
                    1,
                ),
            )

    async def handle_perform_turn(self) -> None:
        """Perform turn."""
        print("Neuro's Turn")
        await self.raise_event(
            Event(
                "need_take_action",
                self.state,
                1,
            ),
        )

    # types: no-any-unimported error: Argument 2 to "handle_submit_move" becomes "Event[Any]" due to an unfollowed import
    async def handle_submit_move(self, event: Event[GameAction]) -> None:
        # types: ^^^^^^^^^^^^^^^^^^^^^^^^
        """Handle submit move event."""
        action = event.data
        await self.perform_action(action)

    async def handle_network_stop(self, event: Event[None]) -> None:
        """Handle network stop event."""
        await self.raise_event(
            Event(
                "send_neuro_context",
                ("The checkers game has ended.", True),
                1,
            ),
        )


# types: no-any-unimported error: Argument 1 to "build_state_context" becomes "Any" due to an unfollowed import
def build_state_context(state: State) -> str:
    # types: ^^^^^^^^^^^^^^
    """Build game state context."""
    width, height = state.size
    separator = "═" * width

    lines = ["Current game board:"]
    lines.append(f"╔{separator}╗")
    lines.extend(
        f"║{line.replace(' ', '░')}║" for line in str(state).splitlines()
    )
    lines.append(f"╚{separator}╝")
    lines.append("`+` -> Black Pawn")
    lines.append("`-` -> Red Pawn")
    lines.append("`O` -> Black King")
    lines.append("`X` -> Red King")
    lines.append("Top-left is (0, 0), x is row, y is column")
    lines.append(f"({width - 1}, {height - 1}) is bottom right")
    return "\n".join(lines)


class NeuroComponent(TrioNeuroAPIComponent):
    """Neuro Component."""

    __slots__ = ("handshake_failure_callback",)

    def __init__(
        self,
        websocket: WebSocketConnection | None = None,
        handshake_failure_callback: Callable[[], None] | None = None,
    ) -> None:
        """Initialize Neuro Component."""
        super().__init__("NeuroComponent", "Checkers", websocket)

        self.handshake_failure_callback = handshake_failure_callback

    def bind_handlers(self) -> None:
        """Register event handlers."""
        super().bind_handlers()

        self.register_handlers(
            {
                "neuro_connect": self.handle_connect,
                "need_take_action": self.handle_need_take_action,
                "client_connect": self.handle_client_connect,
                "send_neuro_context": self.handle_send_neuro_context,
            },
        )

    async def handle_client_connect(
        self,
        event: Event[tuple[str, int]],
    ) -> None:
        """Handle game client connect event."""
        await self.send_startup_command()

        address = event.data

        await self.send_context(
            f"You are playing a new checkers game on {address}.",
            silent=True,
        )

    async def handle_send_neuro_context(
        self,
        event: Event[tuple[str, bool]],
    ) -> None:
        """Handle send neuro context event."""
        message, silent = event.data
        await self.send_context(message, silent)

    def websocket_connect_failed(self) -> None:
        """Call handshake_failure_callback if it's set."""
        if self.handshake_failure_callback is None:
            return
        self.handshake_failure_callback()

    # types: no-any-unimported error: Argument 2 to "build_game_action_fires" becomes "Any" due to an unfollowed import
    def build_game_action_fires(
        # types: ^^^^^^^^^^^^^^^^^
        self,
        game_action: GameAction,
    ) -> Callable[[NeuroAction], Awaitable[tuple[bool, str | None]]]:
        """Return NeuroAction handler from a checkers game action."""
        from_pos, to_pos = game_action

        async def trigger_game_action(
            neuro_action: NeuroAction,
        ) -> tuple[bool, str | None]:
            """Raise submit move event for associated game action."""
            await self.raise_event(
                Event(
                    "submit_move",
                    game_action,
                ),
            )
            return True, f"Moving piece from {from_pos} to {to_pos}"

        return trigger_game_action

    @staticmethod
    # types: no-any-unimported error: Argument 1 to "game_action_to_command_action" becomes "Any" due to an unfollowed import
    def game_action_to_command_action(
        game_action: GameAction,
    ) -> CommandAction:
        """Convert game state action to Neuro action."""
        from_pos, to_pos = game_action
        from_x, from_y = from_pos
        to_x, to_y = to_pos
        return CommandAction(
            f"move_from_{from_x}_{from_y}_to_{to_x}_{to_y}",
            f"Move the piece from {from_pos} to {to_pos}, jumping any pieces on the way.",
            schema={},
        )

    # types: no-any-unimported error: Argument 2 to "handle_need_take_action" becomes "Event[Any]" due to an unfollowed import
    async def handle_need_take_action(self, event: Event[State]) -> None:
        """Handle need to take action event."""
        state = event.data

        action_names = await self.register_temporary_actions_group(
            (
                self.game_action_to_command_action(game_action),
                self.build_game_action_fires(game_action),
            )
            for game_action in state.get_all_actions(int(state.get_turn()))
        )
        state_data = build_state_context(state)
        print(state_data)
        await self.send_force_action(
            state=state_data,
            query="It is now your turn. Please perform an action.",
            action_names=action_names,
        )


async def run_client(
    event_manager: ExternalRaiseManager,
    host: str,
    port: int,
) -> None:
    """Run machine client and raise tick events."""
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


async def run_client_in_local_servers(
    websocket_url: str,
) -> None:
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

            needs_retry_connect = False

            def handshake_failure_callback() -> None:
                """Handle websocket handshake failure."""
                nonlocal needs_retry_connect
                needs_retry_connect = True
                print("Websocket handshake failure.")

            neuro_component = NeuroComponent(
                handshake_failure_callback=handshake_failure_callback,
            )
            event_manager.add_component(neuro_component)

            await event_manager.raise_event(
                Event("neuro_connect", websocket_url),
            )

            while True:
                advertisements = set(await read_advertisements())
                for motd, server in advertisements:
                    print(f"Found server ({motd = })")
                    if neuro_component.not_connected:
                        print("Neuro not connected, skip join.")
                        if needs_retry_connect:
                            print("Attempting to join Neuro websocket server.")
                            needs_retry_connect = False
                            await event_manager.raise_event(
                                Event("neuro_connect", websocket_url),
                            )
                    else:
                        await run_client(event_manager, *server)
                        break
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

    websocket_url = "ws://localhost:8000"

    try:
        trio.run(run_client_in_local_servers, websocket_url)
    except Exception:
        traceback.print_exc()


if __name__ == "__main__":
    cli_run()
