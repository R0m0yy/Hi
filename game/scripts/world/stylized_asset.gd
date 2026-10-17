@tool
class_name StylizedAsset
extends Node3D
## Root script for wrapper scenes around generated GLB assets: swaps the
## glTF placeholder materials for the stylised shader materials, in the
## editor as well as at runtime.


func _ready() -> void:
	MaterialLibrary.apply(self)
