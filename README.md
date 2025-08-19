# Checkers-Neuro-Client
[Neuro API](https://github.com/VedalAI/neuro-game-sdk) client for my [Checkers Game](https://github.com/CoolCat467/Checkers)

<!-- BADGIE TIME -->

[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/CoolCat467/Checkers-Neuro-Client/main.svg)](https://results.pre-commit.ci/latest/github/CoolCat467/Checkers-Neuro-Client/main)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)

<!-- END BADGIE TIME -->

## Installation
Ensure Python 3 is installed, and use pip to install this project.

```bash
pip install git+https://github.com/CoolCat467/Checkers-Neuro-Client.git
```

## Commands
- Start Neuro-API client with
```bash
checkers_neuro_client
```

- Start graphical checkers game with
```bash
checkers_game
```

- Start non-integrated checkers game server with
```bash
checkers_game_server
```

- Start Minimax AI client with
```bash
checkers_game_minimax_ai_client
```

## Usage
To play against Neuro:
1. Start checkers game GUI and click Host Game
2. Start Neuro-API client

To have Neuro play against Minimax AI with you as a spectator:
1. Start checkers game server
2. Start Neuro-API client
3. Start checkers game GUI and click Join Game (do not join server yet)
4. Start Minimax AI client
5. Quickly join server after starting minimax client
