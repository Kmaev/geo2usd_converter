class LayerReplacer:
    def __init__(self, old_path, new_path):
        self.old_path = old_path
        self.new_path = new_path

    def __call__(self, layer_path: str):

        if layer_path == self.old_path:

            return self.new_path
        return layer_path



