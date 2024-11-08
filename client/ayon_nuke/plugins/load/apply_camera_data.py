import json

from ayon_core.pipeline import load
from ayon_nuke.api.lib import maintained_selection, set_node_data


class ApplyCameraData(load.LoaderPlugin):
    """Apply camera data to the selected Camera Node"""
    representations = {"*"}
    product_types = {"cameradata"}

    label = "Apply Camera Data"
    order = 25
    icon = "camera"
    color = "#4CAF50"

    def load(self, context, name=None, namespace=None, data=None):
        # Get representation data from context
        representation = context["representation"]
        
        try:
            # Get the JSON file path from the representation
            json_file = representation["files"][0]["path"]
            root = context["project"]["config"]["roots"]["work"]["linux"]
            json_file = json_file.replace("{root[work]}", root)
            
            # Read the JSON file
            with open(json_file, 'r') as f:
                camera_data = json.load(f)
            
            winsizex = camera_data.get("winsizex")
            winsizey = camera_data.get("winsizey")
            
            if winsizex is None or winsizey is None:
                msg = "Missing 'winsizex' or 'winsizey' in camera data."
                self.log.error(msg)
                return False

            # Get the selected Camera Node
            with maintained_selection():
                selected_nodes = self.get_selected_camera_node()
                if not selected_nodes:
                    msg = "No Camera Node is selected."
                    self.log.error(msg)
                    return False

                camera_node = selected_nodes[0]
                # Update the win_scale knobs
                self.set_win_scale(camera_node, winsizex, winsizey)
                
                msg = f"Successfully applied camera data to {camera_node.name()}"
                self.log.info(msg)
                return True

        except (json.JSONDecodeError, IOError, KeyError) as e:
            msg = f"Failed to load camera data: {e}"
            self.log.error(msg)
            return False

    def get_selected_camera_node(self):
        import nuke
        
        nodes = nuke.selectedNodes()
        self.log.warning(f"Selected nodes: {nodes}")
        
        camera_nodes = [node for node in nodes if node.Class() == "Camera2" or node.Class() == "Camera3"]
        self.log.warning(f"Found camera nodes: {camera_nodes}")
        
        return camera_nodes

    def set_win_scale(self, camera_node, winsizex, winsizey):
        try:
            # Store camera data using AYON's node data system
            set_node_data(camera_node, "camera_data", {
                "winsizex": winsizex,
                "winsizey": winsizey
            })

            win_scale = camera_node['win_scale']
            win_scale.setValue(winsizex, 0)  # U value
            win_scale.setValue(winsizey, 1)  # V value

            self.log.info(
                f"Set win_scale to (U: {winsizex}, V: {winsizey}) on node {camera_node.name()}"
            )
        except Exception as e:
            self.log.error(f"Failed to set win_scale: {e}") 