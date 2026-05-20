"""
Creation Engine – generate textures, materials, maps, meshes, shaders, fonts,
localization, navmeshes, and dialogue for game engines.

Quick-start
-----------
>>> from creation_engine import CreationEngine
>>> engine = CreationEngine()
>>> engine.generate_texture(prompt="wet stone", seed=123, output_dir="assets/")
"""

from creation_engine.engine import CreationEngine

__all__ = ["CreationEngine"]
__version__ = "2.0.0"
