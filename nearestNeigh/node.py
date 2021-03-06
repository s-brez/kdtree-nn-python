class Node():

    def __init__(self, point=None, left=None, right=None, parent=None, split=None):
        self.point = point if point else None
        self.left = left if left else None
        self.right = right if right else None
        self.parent = parent if parent else None
        self.was_split_on = split if split else ""
