from nearestNeigh.nearest_neigh import NearestNeigh
from nearestNeigh.point import Point
from nearestNeigh.node import Node
import sys

class KDTreeNN(NearestNeigh):

    def __init__(self):

        self.root = None

        # Holds results of NN search queries

        # Used for detailed print/debug output
        self.print_count = 0

        # Hashes of leaf nodes already backtracked from
        self.b_list = []

        # Combined Hashes of parent+child nodes.
        # Used to avoid double traversing already explored subtrees
        self.t_list = []

        self.iteration = 0

    def build_index(self, points: [Point]):
        """
        Creates KD tree by partitioning given list of points recursively
        """

        self.root = self.partition(points, 0, None)
        # self.print(self.root)

    def partition(self, points: list, axis: int, parent=None) -> Node:
        """
        Partitions the given list of points into KD tree nodes.

        1.  Sort list of points by lon and lat alternatively
        2.  Return median point as current node with points
            above/below the median as subtrees.
        """

        # Empty point set, do nothing
        if len(points) < 1:
            return None

        
        elif len(points) == 1:
            split = "lat" if axis % 2 == 0 else "lon"
            return Node(
                Point(points[0].id, points[0].cat,
                      points[0].lat, points[0].lon),
                left=None,
                right=None,
                parent=parent,
                split=split)

        # >1 point in subset, sort according to alternating axis
        elif len(points) > 1:

            # Even, x-axis (lat). Odd, y-axis (long)
            if axis % 2 == 0:
                points = sorted(points, key=lambda k: k.lat)
                split = "lat"
            else:
                points = sorted(points, key=lambda k: k.lon)
                split = "lon"

            # Get median point
            if len(points) % 2 == 0:
                m_index = int((len(points) / 2) - 1)
            else:
                m_index = int(len(points) // 2)
            median = points[m_index]

            # Give node a reference to parent node for ease of backtracking
            node = Node(
                Point(median.id, median.cat, median.lat, median.lon),
                left=None, right=None, parent=parent, split=split)

            # Slice and partition subsets as child nodes/subtrees
            node.left = self.partition(points[:m_index], axis + 1, node)
            node.right = self.partition(points[m_index + 1:], axis + 1, node)

            return node

    def search(self, search_term: Point, k: int) -> [Point]:
        """
        Return k nearest neighbours of search_term co-ords and category

        1. Move down tree recursively, considerate of split and co-ord
            at each branch
        2. When leaf node reached, add node to saved closest neighbours.
        3. Backtrack node by node.
        4. If backtracked node closer than saved neighbour, add to saved list.
        5. Check other subtree of split only dist from target to current
            closest point > dist from target to split.
        6. Lastly, once we have our list of NN, sort by distance.
        """

        # Find k nearest neighbours
        self.neighbours, self.closed_list, self.b_list, self.t_list = [], [], [], []
        self.forward_traverse(None, self.root, search_term, 0, k)

        # Flatten neighbour list to points-only and sort by distance.
        if self.neighbours:
            self.neighbours = sorted(self.neighbours, key=lambda k: k['dist'])
            self.neighbours = [n['point'] for n in self.neighbours]



        return self.neighbours

    def forward_traverse(self, parent, cur_node, targ: Point, axis: int,
                         k: int, subtree=None):
        """
        Helper method for search()
        """

        input("----------forward_traverse()---------")

        if cur_node is not None:

            if not self.axis_is_valid(axis, cur_node):
                print("provided axis does not match current nodes splitting axis")
                sys.exit(0)

            c_val = cur_node.point.lat if axis % 2 == 0 else cur_node.point.lon
            t_val = targ.lat if axis % 2 == 0 else targ.lon
            split = cur_node.was_split_on
            values, status = "", ""

            dist = cur_node.point.dist_to(targ)

            if cur_node.left:
                l_val = cur_node.left.point.lat if axis % 2 == 0 else cur_node.left.point.lon
                status += str("L " + cur_node.left.point.id + ", ")
                values += str(str(round(l_val, 4)) + " < " + str(round(t_val, 4)) + ", ")
            if cur_node.right:
                r_val = cur_node.right.point.lat if axis % 2 == 0 else cur_node.right.point.lon
                status += str("R " + cur_node.right.point.id)
                values += str(str(round(r_val, 4)) + " => " + str(round(t_val, 4)))

            # Even, x-axis (lat). Odd, y-axis (lon)
            print("current point:", cur_node.point.id)
            print("children:", status)
            if subtree:
                print(str("subtree: " + subtree + ", split: " + split))
            else:
                print("split: ", split)
            print("target", split, "value:", t_val)
            print(cur_node.point.id, split, "value:", c_val)

            # Traverse child nodes if they exist
            # X-dim split, compare lat
            if axis % 2 == 0:
                if targ.lat >= cur_node.point.lat:
                    if cur_node.right:
                        print(cur_node.point.id, "attempting to traverse right child", cur_node.right.point.id, "beacause", targ.lat, ">=", cur_node.point.lat)
                        if not self.already_travelled(cur_node, cur_node.right):
                            self.forward_traverse(cur_node, cur_node.right, targ,
                                                  axis + 1, k, subtree="right")
                        else:
                            print("Already explored this subtree, dont explore again")

                    else:
                        print(cur_node.point.id, "tried traversing right but no subtree exists")
                        if cur_node.left:
                            print(cur_node.point.id, "other (left) subtree", cur_node.left.point.id, "should be traversed")
                            if not self.already_travelled(cur_node, cur_node.left):
                                self.forward_traverse(
                                    cur_node, cur_node.left, targ,
                                    axis + 1, k, subtree="left")
                            else:
                                print("Already explored this subtree, dont explore again")
                else:
                    if cur_node.left:
                        print(cur_node.point.id, "attempting to traverse left child", cur_node.left.point.id, "beacause", targ.lat, "<", cur_node.point.lat)
                        if not self.already_travelled(cur_node, cur_node.left):
                            self.forward_traverse(cur_node, cur_node.left, targ,
                                                  axis + 1, k, subtree="left")
                        else:
                            print("Already explored this subtree, dont explore again")

                    else:
                        print(cur_node.point.id, "tried traversing left but no subtree exists.")
                        if cur_node.right:
                            print(cur_node.point.id, "other (right) subtree", cur_node.right.point.id, "should be traversed")
                            if not self.already_travelled(cur_node, cur_node.right):
                                self.forward_traverse(
                                    cur_node, cur_node.right, targ,
                                    axis + 1, k, subtree="right")
                            else:
                                print("Already explored this subtree, dont explore again")

            # Y-dim split, compare lon
            else:
                if targ.lon >= cur_node.point.lon:
                    if cur_node.right:
                        print(cur_node.point.id, "attempting to traverse right child", cur_node.right.point.id, "beacause", targ.lon, ">=", cur_node.point.lon)
                        if not self.already_travelled(cur_node, cur_node.right):
                            self.forward_traverse(cur_node, cur_node.right, targ,
                                                  axis + 1, k, subtree="right")
                        else:
                            print("Already explored this subtree, dont explore again")

                    else:
                        print(cur_node.point.id, "tried traversing right but no subtree exists")
                        if cur_node.left:
                            print(cur_node.point.id, "other (left) subtree", cur_node.left.point.id, "should be traversed")
                            if not self.already_travelled(cur_node, cur_node.left):
                                self.forward_traverse(
                                    cur_node, cur_node.left, targ,
                                    axis + 1, k, subtree="left")
                            else:
                                print("Already explored this subtree, dont explore again")
                else:
                    if cur_node.left:
                        print(cur_node.point.id, "attempting to traverse left child", cur_node.left.point.id, "beacause", targ.lon, "<", cur_node.point.lon)
                        self.forward_traverse(cur_node, cur_node.left, targ,
                                              axis + 1, k, subtree="left")
                    else:
                        print(cur_node.point.id, "tried traversing left but no subtree exists")
                        # if self.save_neighbour(dist, cur_node.point, k, targ, False):
                        if cur_node.right:
                            print(cur_node.point.id, "other (right) subtree", cur_node.right.point.id, "should be traversed")
                            if not self.already_travelled(cur_node, cur_node.right):
                                self.forward_traverse(
                                    cur_node, cur_node.right, targ,
                                    axis + 1, k, subtree="right")
                            else:
                                print("Already explored this subtree, dont explore again")

            # Save neighbour and backtrack when leaf node reached
            if cur_node.left is None and cur_node.right is None:
                print(cur_node.point.id, "leaf node reached")
                self.save_neighbour(dist, cur_node.point, k, targ)

                # Safeguard multiple backtrack
                if self.hash_point(cur_node.point) not in self.b_list:
                    self.b_list.append(self.hash_point(cur_node.point))
                    self.backtrack(cur_node, targ, axis, k, subtree)



    def axis_is_valid(self, axis: int, node: Node) -> bool:
        """
        Checks axis matches the given node
        """

        if axis % 2 == 0 and node.was_split_on == "lat":
            validity = True
        elif axis % 2 != 0 and node.was_split_on == "lon":
            validity = True
        else:
            validity = False

        return validity

    def backtrack(self, cur_node, targ: Point, axis: int, k: int,
                  tree=None):
        """
        Helper method for search() and forward_traverse()

        axis must be cur_node axis
        subtree must be cur_node subtree

        """

        if cur_node:
            if cur_node.parent:

                input("-------------backtrack()-------------")

                st = "right" if tree == "left" else "left"
                split = "lat" if (axis - 1) % 2 == 0 else "lon"

                status = ""
                if cur_node.parent.left:
                    status += str("L " + cur_node.parent.left.point.id + ", ")
                if cur_node.parent.right:
                    status += str("R " + cur_node.parent.right.point.id)

                print("current point:", cur_node.parent.point.id, "(backtracked from", cur_node.point.id, "to", str(cur_node.parent.point.id + ")"))
                print("children:", status)
                print("subtree:", tree, "split:", split)

                if not self.axis_is_valid(axis - 1, cur_node.parent):
                    print("provided axis does not match current nodes splitting axis")
                    sys.exit(0)

                # Check if other subtree should be explored
                # dist = cur_node.parent.point.dist_to(targ)
                p_dist = self.p_distance_to(axis - 1, cur_node.parent.point, targ)
                dist = cur_node.parent.point.dist_to(targ)

                if self.save_neighbour(p_dist, cur_node.parent.point, k, targ, False):
                    self.save_neighbour(dist, cur_node.parent.point, k, targ)
                    print(cur_node.parent.point.id, "splitting line dist < smallest neighbours dist, other subtree should be explored")

                    # if cur_node.parent.left.point.id == "id238":
                    #     print("yeet")

                    if tree == "left":
                        if cur_node.parent.right:
                            if not self.already_travelled(
                                cur_node.parent, cur_node.parent.right):
                                self.forward_traverse(
                                    cur_node.parent, cur_node.parent.right,
                                    targ, axis, k, subtree="right")
                        else:
                            print(cur_node.parent.point.id, "(backtrack) tried traversing right but no subtree exists")
                            # if self.save_neighbour(p_dist, cur_node.parent.point, k, targ, False):
                            if cur_node.parent.left:
                                print(cur_node.parent.point.id, "(backtrack) other (left) subtree", cur_node.parent.left.point.id, "should be traversed")
                                if not self.already_travelled(
                                    cur_node.parent, cur_node.parent.left):
                                    self.forward_traverse(
                                        cur_node.parent, cur_node.parent.left, targ,
                                        axis, k, subtree="left")

                    elif tree == "right":
                        if cur_node.parent.left:
                            if not self.already_travelled(
                                cur_node.parent, cur_node.parent.left):
                                self.forward_traverse(
                                    cur_node.parent, cur_node.parent.left,
                                    targ, axis, k, subtree="left")
                        else:
                            print(cur_node.parent.point.id, "(backtrack) tried traversing left but no subtree exists")
                            # if self.save_neighbour(p_dist, cur_node.parent.point, k, targ, False):
                            if cur_node.parent.right:
                                print(cur_node.parent.point.id, "(backtrack) other (right) subtree", cur_node.parent.right.point.id, "should be traversed")
                                if not self.already_travelled(
                                    cur_node.parent, cur_node.parent.right):                                  
                                    self.forward_traverse(
                                        cur_node.parent, cur_node.parent.right, targ,
                                        axis, k, subtree="right")
                else:
                    print("Dont explore other subtree")

                # Keep backtracking until branches no longer valid
                self.backtrack(cur_node.parent, targ, axis - 1, k, st)

            else:
                print("backtracked to root", cur_node.point.id)

    def already_travelled(self, parent: Node, child: Node) -> bool:
        """
        Check combined hash of parent + child against t_list
        so explored subtrees are not traversed twice.

        Return true if hash exists in t_list (i.e, dont traverse)
        """

        # return False

        c_hash = self.hash_point(child.point) + self.hash_point(parent.point)

        if c_hash not in self.t_list:
            self.t_list.append(c_hash)
            return False
        else:
            return True


    def save_neighbour(self, dist, point: Point, k: int, targ: Point, save=True):
        """
        Helper method for search()

        Save to or overwrite an element of neighbours list with the
        incoming point.

        Returns true if a save was made. If a save was made, this nodes subtree
        should be explored.
        """

        if save:

            p_hash = self.hash_point(point)

            # If k neighbours and cur_node dist > max(saved), replace max.
            if len(self.neighbours) == k and point.cat == targ.cat:
                self.neighbours = sorted(self.neighbours,
                                         key=lambda k: k['dist'], reverse=True)

                if self.neighbours[0]['dist'] > dist:
                    if p_hash not in [n['hash'] for n in self.neighbours]:
                        print("Saving new nearest neighbour", point.id, "because", self.neighbours[0]['dist'], ">", dist)
                        print("current node distance to target:", dist)

                        del self.neighbours[0]
                        self.neighbours.append({
                            'dist': dist,
                            'point': point,
                            'hash': p_hash
                        })

                        print("neighbours:")
                        for n in [(n['point'].id, n['dist']) for n in self.neighbours]:
                            print(n)

                    return True
                else:
                    return False

            # Save immediately if < k neighbours in list
            elif len(self.neighbours) < k and point.cat == targ.cat:
                if p_hash not in [n['hash'] for n in self.neighbours]:
                    print("Saving new nearest neighbour", point.id, "because < k neighbours already saved")
                    print("current node distance to target:", dist)

                    self.neighbours.append({
                        'dist': dist,
                        'point': point,
                        'hash': p_hash
                    })

                    print("neighbours:")
                    for n in [(n['point'].id, n['dist']) for n in self.neighbours]:
                        print(n)
                return True

            else:
                return False

        # For other tree traverse-or-not checking only, no save
        else:
            if len(self.neighbours) < k:
                return True
            elif len(self.neighbours) == k:
                self.neighbours = sorted(self.neighbours,
                                         key=lambda k: k['dist'], reverse=True)
                if self.neighbours[0]['dist'] >= dist:
                    return True

    def add_point(self, point: Point) -> bool:
        """
        Recursive traverse tree to appropriate location and adds point.
        """

        return self.add_traverse(point, self.root, 0)

    def add_traverse(self, point, cur_node, axis: int, parent=None):
        """
        Helper method for add_point()

        """

        # Check each node for duplication as we move down the tree.
        if self.hash_point(cur_node.point) == self.hash_point(point):
            print("Duplicate point", point)
            return False

        # CORRECT:
        # Even, x-axis (longitude). Odd, y-axis (latitude)

        # Even, compare x-axis (latitude).
        if axis % 2 == 0:
            c_node_val = cur_node.point.lat
            point_val = point.lat

        # Odd, compare y-axis (longitude)
        else:
            c_node_val = cur_node.point.lon
            point_val = point.lon

        # Evaluate right branch
        if point_val >= c_node_val:

            # Traverse right subtree if it exists
            if cur_node.right:
                # print("Traversing right of ", cur_node.point)
                return self.add_traverse(
                    point, cur_node.right, axis + 1, cur_node)

            # If no subtree, target location has been reached.
            else:
                # print("Adding new node under parent", cur_node.point)
                cur_node.right = Node(
                    point, left=None, right=None, parent=cur_node)
                return True

        # Evaluate left branch
        else:

            # Traverse left subtree if it exists
            if cur_node.left:
                # print("Traversing left of ", cur_node.point)
                return self.add_traverse(
                    point, cur_node.left, axis + 1, cur_node)

            # If no subtree, target location has been reached.
            else:
                # print("Adding new node under parent", cur_node.point)
                cur_node.left = Node(
                    point, left=None, right=None, parent=cur_node)
                return True

    def delete_point(self, point: Point) -> bool:
        # To be implemented.
        pass

    def is_point_in(self, point: Point) -> bool:
        # To be implemented.
        pass

    def hash_point(self, point) -> int:
        """
        Hash method provided in Point class kept giving me unsupported operand
        errors for float ^ float sums. This implementation is the same but uses
        float * float instead instead of float ^ float.
        """

        hash_value = 7
        hash_value = 53 * hash_value + hash(point.id)
        hash_value = 53 * hash_value + hash(point.cat)
        hash_value = 53 * hash_value + int(point.lat * point.lat)
        hash_value = 53 * hash_value + int(point.lon * point.lon)
        return hash_value

    def print(self, root):
        """
        Prints tree top to bottom, left to right descending. 
        """

        depth = self.depth(root)
        for i in range(1, depth + 1):
            print("\n***", "Level", i, "*********************************")
            self.print_level(root, i)

    def print_level(self, node, depth):
        """
        Helper method for print()
        """

        if not node:
            return

        if depth == 1:
            self.print_count += 1
            print(node.point, self.print_count)

        elif depth > 1:
            self.print_level(node.left, depth - 1)
            self.print_level(node.right, depth - 1)

    def depth(self, node):
        """
        Returns depth of a given node
        """

        if not node:
            return 0
        else:
            l_depth = self.depth(node.left)
            r_depth = self.depth(node.right)

            if l_depth > r_depth:
                return l_depth + 1
            else:
                return r_depth + 1
