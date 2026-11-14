"""GestureMouse AI Fruit Ninja Game package."""
from game.fruit_ninja import FruitNinjaGame, launch_fruit_ninja
from game.fruit_objects import Fruit, FruitType
from game.game_settings import GAME_WIDTH, GAME_HEIGHT, FPS

__all__ = [
    "FruitNinjaGame",
    "launch_fruit_ninja",
    "Fruit",
    "FruitType",
    "GAME_WIDTH",
    "GAME_HEIGHT",
    "FPS",
]
