"""
Pure algorithms, not specific to an application.
"""

class UnionFind(object):
    """
    Union-find data structure, also known as disjoint set.
    Only works on a range of integers [0, n).
    All operations are permitted to mutate the underlying list.
    """
    def __init__(self, n):
        """
        Make a union-find data structure that starts with
        the integers [0, n) each as a singleton set.
        """
        self.leaders = list(range(n))
    def test(self, i, j):
        """
        Are these values in the same set?
        """
        leaders = self.leaders
        it = []
        jt = []
        while leaders[i] != i:
            it.append(i)
            i = leaders[i]
        while leaders[j] != j:
            jt.append(j)
            j = leaders[j]
        for k in it:
            leaders[k] = i
        for k in jt:
            leaders[k] = j
        return i == j
    def join(self, i, j):
        """
        Join the sets containing these values.
        """
        leaders = self.leaders
        it = []
        while leaders[i] != i:
            it.append(i)
            i = leaders[i]
        while leaders[j] != j:
            it.append(j)
            j = leaders[j]
        it.append(j)
        for k in it:
            leaders[k] = i
    def test_and_join(self, i, j):
        """
        Join the sets containing these values (if they are different).
        Returns true if they were already in the same set, otherwise false.
        
        Functionally equivalent to:
          flag = uf.test(i, j)
          uf.join(i, j)
          return flag
        
        ... but this operation can be optimized somewhat if they are fused.
        """
        leaders = self.leaders
        it = []
        while leaders[i] != i:
            it.append(i)
            i = leaders[i]
        while leaders[j] != j:
            it.append(j)
            j = leaders[j]
        result = i == j
        it.append(j)
        for k in it:
            leaders[k] = i
        return result