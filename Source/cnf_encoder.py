from typing import List, Dict, Tuple
from pysat.formula import CNF, IDPool
from pysat.card import CardEnc, EncType

Grid = List[List[int]]
IslandInfo = Tuple[int, int, int]
EdgeExtra = Tuple
SolutionDict = Dict[Tuple[int, int], int]

class CNFEncoder:
    def __init__(self) -> None:
        self.vpool: IDPool = IDPool()
        self.cnf: CNF = CNF()
        self.islands: Dict[int, IslandInfo] = {}
        self.edges: List[Tuple[int, int, EdgeExtra]] = []
        self.coord_to_id: Dict[Tuple[int, int], int] = {}
        self.edge_vars: Dict[Tuple[int, int], Tuple[int, int]] = {}
        self.crossing_pairs: List[Tuple[Tuple[int, int], Tuple[int, int]]] = []
        self._top_id: int = 1

    def encode(self, grid: Grid) -> None:
        self.islands = self._find_islands(grid)
        self.edges, self.coord_to_id = self._compute_edges(grid)
        self.edge_vars = self._create_edge_vars()
        self._update_top_id()
        self._add_island_constraints()
        self._add_non_crossing_constraints()
    
    def _update_top_id(self) -> None:
        self._top_id = self.vpool.top + 1

    def _find_islands(self, grid: Grid) -> Dict[int, IslandInfo]:
        islands: Dict[int, IslandInfo] = {}
        cur_id = 1
        for r, row in enumerate(grid):
            for c, val in enumerate(row):
                if val != 0:
                    islands[cur_id] = (r, c, val)
                    cur_id += 1
        return islands

    def _compute_edges(self, grid: Grid):
        edges: List[Tuple[int, int, EdgeExtra]] = []
        coord_to_id: Dict[Tuple[int, int], int] = {}

        for i, (r, c, _) in self.islands.items():
            coord_to_id[(r, c)] = i

        nrows, ncols = len(grid), len(grid[0])

        for i, (r, c, _) in self.islands.items():
            for nc in range(c + 1, ncols):
                if (r, nc) in coord_to_id:
                    if nc - c <= 1: break
                    valid = all(grid[r][cc] == 0 for cc in range(c + 1, nc))
                    if valid:
                        j = coord_to_id[(r, nc)]
                        a, b = sorted((i, j))
                        edges.append((a, b, ('h', r, c, nc)))
                    break

            for nr in range(r + 1, nrows):
                if (nr, c) in coord_to_id:
                    if nr - r <= 1: break
                    valid = all(grid[rr][c] == 0 for rr in range(r + 1, nr))
                    if valid:
                        j = coord_to_id[(nr, c)]
                        a, b = sorted((i, j))
                        edges.append((a, b, ('v', c, r, nr)))
                    break

        uniq: Dict[Tuple[int, int], EdgeExtra] = {}
        for i, j, extra in edges:
            if (i, j) not in uniq:
                uniq[(i, j)] = extra
        final_edges = [(i, j, extra) for (i, j), extra in uniq.items()]
        return final_edges, coord_to_id

    def _create_edge_vars(self) -> Dict[Tuple[int, int], Tuple[int, int]]:
        edge_vars: Dict[Tuple[int, int], Tuple[int, int]] = {}
        for i, j, _ in self.edges:
            x1 = self.vpool.id(('x', i, j, 1))
            x2 = self.vpool.id(('x', i, j, 2))
            self.cnf.append([-x2, x1])
            edge_vars[(i, j)] = (x1, x2)
        return edge_vars

    def _add_island_constraints(self) -> None:
        island_edges: Dict[int, List[Tuple[Tuple[int,int], int, int]]] = {i: [] for i in self.islands}
        
        for (i, j), (x1, x2) in self.edge_vars.items():
            if i in island_edges:
                island_edges[i].append(((i, j), x1, x2))
            if j in island_edges:
                island_edges[j].append(((i, j), x1, x2))

        for island_id, edges_info in island_edges.items():
            degree = self.islands[island_id][2]
            
            if len(edges_info) == 0:
                if degree > 0:
                    self.cnf.append([])
                continue
            
            lits = []
            for _, x1, x2 in edges_info:
                lits.extend([x1, x2])
            
            self._add_cardinality_constraint(lits, degree)
    
    def _add_cardinality_constraint(self, lits: List[int], degree: int) -> None:
        if not lits:
            return
        
        card_cnf = CardEnc.equals(lits=lits, bound=degree, top_id=self._top_id, encoding=EncType.seqcounter)
        
        if card_cnf.clauses:
            max_var = max(abs(lit) for clause in card_cnf.clauses for lit in clause)
            self._top_id = max(self._top_id, max_var + 1)
        
        self.cnf.extend(card_cnf.clauses)

    def _add_non_crossing_constraints(self) -> None:
        edge_list = [((i, j), extra) for (i, j, extra) in self.edges]
        n = len(edge_list)
        self.crossing_pairs = []

        for a in range(n):
            (e1, ex1) = edge_list[a]
            for b in range(a + 1, n):
                (e2, ex2) = edge_list[b]
    
                if ex1[0] == ex2[0]: continue

                crosses = False
                if ex1[0] == 'h':
                    r_h, c_h_start, c_h_end = ex1[1], ex1[2], ex1[3]
                    c_v, r_v_start, r_v_end = ex2[1], ex2[2], ex2[3]
                    crosses = (r_v_start < r_h < r_v_end) and (c_h_start < c_v < c_h_end)
                else:
                    c_v, r_v_start, r_v_end = ex1[1], ex1[2], ex1[3]
                    r_h, c_h_start, c_h_end = ex2[1], ex2[2], ex2[3]
                    crosses = (r_v_start < r_h < r_v_end) and (c_h_start < c_v < c_h_end)

                if crosses:
                    x1_e1, _ = self.edge_vars[e1]
                    x1_e2, _ = self.edge_vars[e2]
                    self.cnf.append([-x1_e1, -x1_e2])
                    self.crossing_pairs.append((e1, e2))

    @staticmethod
    def check_connectivity(islands: Dict[int, IslandInfo], solution: SolutionDict) -> bool:
        if not islands: return True
        adj = {i: [] for i in islands}
        for (u, v), count in solution.items():
            if count > 0:
                adj[u].append(v)
                adj[v].append(u)
        start_node = next(iter(islands))
        visited = set([start_node])
        stack = [start_node]
        
        while stack:
            u = stack.pop()
            for v in adj[u]:
                if v not in visited:
                    visited.add(v)
                    stack.append(v)
        return len(visited) == len(islands)

def build_cnf_from_grid(grid: Grid):
    enc = CNFEncoder()
    enc.encode(grid)
    return enc.cnf, enc.vpool, enc.islands, enc.edges, enc.edge_vars, enc._top_id, enc.crossing_pairs
