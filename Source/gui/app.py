import tkinter as tk
from tkinter import ttk, messagebox
import time
import tracemalloc
import os
from concurrent.futures import ProcessPoolExecutor, TimeoutError as FuturesTimeoutError
from utils import read_input, draw_solution, write_output
from benchmark import run_benchmark, DEFAULT_TIMEOUT

try:
    from ctypes import windll
    windll.shcore.SetProcessDpiAwareness(1) 
except:
    pass


def _get_solver_classes():
    from solvers import PySatSolver, AStarSolver, BacktrackingSolver, BruteForceCNFSolver
    return {"PySatSolver": PySatSolver, "AStarSolver": AStarSolver,
            "BacktrackingSolver": BacktrackingSolver, "BruteForceCNFSolver": BruteForceCNFSolver}


def _get_solvers_dict():
    from solvers import PySatSolver, AStarSolver, BacktrackingSolver, BruteForceCNFSolver
    return {"PySAT": PySatSolver, "AStar": AStarSolver, 
            "Backtracking": BacktrackingSolver, "BruteForce": BruteForceCNFSolver}


SOLVERS = None


def _solve_task(solver_cls_name: str, grid):
    solvers_map = _get_solver_classes()
    tracemalloc.start()
    t0 = time.perf_counter()
    solver = solvers_map[solver_cls_name](grid)
    solution, islands, edges = solver.solve()
    elapsed = time.perf_counter() - t0
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return solution, islands, edges, elapsed, peak / (1024 * 1024)


class HashiGUI:
    def __init__(self, root: tk.Tk):
        global SOLVERS
        SOLVERS = _get_solvers_dict()  # Load solvers on GUI init
        
        self.root = root
        self.root.title("CSC14003-Group3")
        self.root.geometry("1280x860")
        self.root.resizable(False, False) 
        
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.tab_solver = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_solver, text="Single Solve")
        self._init_solver_tab()

        self.tab_benchmark = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_benchmark, text="Benchmark")
        self._init_benchmark_tab()

        self.current_grid = None
        self.current_idx = None
        self.current_solution = None
        self.current_islands = None
        self.current_solver_name = None
        self.benchmark_data = None
        self.executor = None
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def _init_solver_tab(self):
        ctrl = ttk.LabelFrame(self.tab_solver, text="Control")
        ctrl.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

        ttk.Label(ctrl, text="Input Index:").pack(pady=5)
        self.input_entry = ttk.Entry(ctrl, width=10)
        self.input_entry.pack(pady=5)
        self.input_entry.insert(0, "1")

        ttk.Button(ctrl, text="Load", command=self.load_input).pack(pady=5)
        ttk.Separator(ctrl, orient='horizontal').pack(fill='x', pady=10)

        ttk.Label(ctrl, text="Solver:").pack(pady=5)
        self.solver_var = tk.StringVar(value="PySAT")
        ttk.Combobox(ctrl, textvariable=self.solver_var, values=list(SOLVERS.keys()), state="readonly", width=15).pack(pady=5)

        ttk.Label(ctrl, text="Timeout (s):").pack(pady=5)
        self.timeout_entry = ttk.Entry(ctrl, width=10)
        self.timeout_entry.pack(pady=5)
        self.timeout_entry.insert(0, "30")
        
        ttk.Button(ctrl, text="SOLVE", command=self.solve).pack(pady=15)
        self.status_lbl = ttk.Label(ctrl, text="Ready", foreground="blue", wraplength=150)
        self.status_lbl.pack(pady=10)
        
        self.save_btn = ttk.Button(ctrl, text="Save Result", command=self.save_result, state=tk.DISABLED)
        self.save_btn.pack(pady=5)

        self.canvas = tk.Canvas(self.tab_solver, width=750, height=750, bg="white")
        self.canvas.pack(side=tk.RIGHT, padx=20, pady=20)

    def _init_benchmark_tab(self):
        ctrl = ttk.LabelFrame(self.tab_benchmark, text="Settings")
        ctrl.pack(fill=tk.X, padx=10, pady=5)

        row1 = ttk.Frame(ctrl)
        row1.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(row1, text="Inputs (e.g. 1,2,3):").pack(side=tk.LEFT)
        self.bench_input = ttk.Entry(row1, width=30)
        self.bench_input.pack(side=tk.LEFT, padx=5)

        row2 = ttk.Frame(ctrl)
        row2.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(row2, text="Solvers:").pack(side=tk.LEFT)
        self.solver_checks = {}
        for name in SOLVERS:
            var = tk.BooleanVar(value=False)
            ttk.Checkbutton(row2, text=name, variable=var).pack(side=tk.LEFT, padx=5)
            self.solver_checks[name] = var

        row3 = ttk.Frame(ctrl)
        row3.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(row3, text="Timeout (s):").pack(side=tk.LEFT)
        self.bench_timeout = ttk.Entry(row3, width=10)
        self.bench_timeout.pack(side=tk.LEFT, padx=5)
        self.bench_timeout.insert(0, str(DEFAULT_TIMEOUT))
        ttk.Button(row3, text="Run", command=self.run_benchmark).pack(side=tk.LEFT, padx=20)
        self.bench_save_btn = ttk.Button(row3, text="Save", command=self.save_benchmark_results, state=tk.DISABLED)
        self.bench_save_btn.pack(side=tk.LEFT, padx=5)

        table_frame = ttk.LabelFrame(self.tab_benchmark, text="Results")
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        style = ttk.Style()
        style.configure("Treeview", rowheight=30)

        cols = ("Input", "Solver", "Time (ms)", "Memory (MB)", "Metric", "Status")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=20)
        widths = {"Input": 100, "Solver": 110, "Time (ms)": 90, "Memory (MB)": 100, "Metric": 170, "Status": 80}
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=widths.get(c, 100), anchor="center")
        
        scroll = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.tag_configure('sep', background='#d0d0d0')

    def load_input(self):
        try:
            idx = int(self.input_entry.get().strip())
            self.current_grid = read_input(f"Inputs/input-{idx:02d}.txt")
            self.current_idx = idx
            self.current_solution = None
            self.current_islands = None
            self.save_btn.config(state=tk.DISABLED)
            self.draw_grid(self.current_grid)
        except:
            messagebox.showerror("Error", "Invalid input")

    def solve(self):
        if not self.current_grid:
            self.load_input()
            if not self.current_grid:
                return

        timeout = float(self.timeout_entry.get() or 30)
        name = self.solver_var.get()
        cls_name = SOLVERS[name].__name__
        
        self.status_lbl.config(text=f"Solving...", foreground="orange")
        self.save_btn.config(state=tk.DISABLED)
        self.root.update()

        self.executor = ProcessPoolExecutor(max_workers=1)
        try:
            future = self.executor.submit(_solve_task, cls_name, self.current_grid)
            solution, islands, _, elapsed, mem = future.result(timeout=timeout)
            if solution:
                self.status_lbl.config(text=f"Done!\n{elapsed:.3f}s, {mem:.2f}MB", foreground="green")
                self.current_solution = solution
                self.current_islands = islands
                self.current_solver_name = name
                self.save_btn.config(state=tk.NORMAL)
                char_grid = draw_solution(self.current_grid, islands, solution)
                self.draw_grid(self.current_grid, char_grid)
            else:
                self.status_lbl.config(text="No solution", foreground="red")
        except FuturesTimeoutError:
            self.status_lbl.config(text="TIMEOUT", foreground="red")
        except Exception as e:
            self.status_lbl.config(text=f"Error: {e}", foreground="red")
        finally:
            self.executor.shutdown(wait=False, cancel_futures=True)

    def save_result(self):
        if self.current_solution and self.current_grid:
            write_output(self.current_solver_name, self.current_idx, self.current_grid, self.current_islands, self.current_solution)
            messagebox.showinfo("Saved", f"Saved to Outputs/{self.current_solver_name}/output-{self.current_idx:02d}.txt")

    def draw_grid(self, grid, char_grid=None):
        self.canvas.delete("all")
        rows, cols = len(grid), len(grid[0])
        a = min(730 / cols, 730 / rows)
        ox, oy = (750 - cols * a) / 2, (750 - rows * a) / 2

        for r in range(rows):
            for c in range(cols):
                x, y = ox + c * a, oy + r * a
                self.canvas.create_rectangle(x, y, x + a, y + a, outline="#e0e0e0")

        if char_grid:
            for r in range(rows):
                for c in range(cols):
                    ch = char_grid[r][c]
                    cx, cy = ox + c * a + a / 2, oy + r * a + a / 2
                    x1, y1, x2, y2 = ox + c * a, oy + r * a, ox + (c + 1) * a, oy + (r + 1) * a
                    off = a * 0.15
                    if ch == "-":
                        self.canvas.create_line(x1, cy, x2, cy, fill="blue", width=2)
                    elif ch == "=":
                        self.canvas.create_line(x1, cy - off, x2, cy - off, fill="blue", width=2)
                        self.canvas.create_line(x1, cy + off, x2, cy + off, fill="blue", width=2)
                    elif ch == "|":
                        self.canvas.create_line(cx, y1, cx, y2, fill="blue", width=2)
                    elif ch == "$":
                        self.canvas.create_line(cx - off, y1, cx - off, y2, fill="blue", width=2)
                        self.canvas.create_line(cx + off, y1, cx + off, y2, fill="blue", width=2)

        for r in range(rows):
            for c in range(cols):
                if grid[r][c]:
                    cx, cy = ox + c * a + a / 2, oy + r * a + a / 2
                    rad = a * 0.4
                    self.canvas.create_oval(cx - rad, cy - rad, cx + rad, cy + rad, fill="white", outline="black", width=2)
                    self.canvas.create_text(cx, cy, text=str(grid[r][c]), font=("Arial", int(a * 0.3), "bold"))

    def run_benchmark(self):
        try:
            indices = [int(x) for x in self.bench_input.get().replace(",", " ").split()]
        except:
            messagebox.showerror("Error", "Invalid indices")
            return

        solvers = [(n, SOLVERS[n]) for n, v in self.solver_checks.items() if v.get()]
        if not solvers:
            messagebox.showwarning("Warning", "Select at least one solver")
            return
        
        timeout = float(self.bench_timeout.get() or DEFAULT_TIMEOUT)
        data = run_benchmark(indices, solvers, timeout)
        self.benchmark_data = data 

        for item in self.tree.get_children():
            self.tree.delete(item)

        metric_info = {
            "PySAT": ("conflicts", "Conflicts"),
            "AStar": ("expanded", "Expanded"),
            "Backtracking": ("calls", "Calls"),
            "BruteForce": ("iterations", "Iterations"),
        }

        grids = data.get("grids", {})
        solved_count = 0
        
        for i, idx in enumerate(indices):
            grid = grids.get(idx)
            size_str = f"({len(grid)}x{len(grid[0])})" if grid else ""
            input_str = f"{idx} {size_str}"
            
            for j, name in enumerate(data["solvers"]):
                res = data["solvers"][name]
                t, m, to = res["times"][i], res["mems"][i], res["timeouts"][i]
                sol = res["solutions"][i]
                
                key, label = metric_info.get(name, (None, "Metric"))
                met_val = res["metrics"][i].get(key, 0) if key else 0
                met_str = f"{label} = {met_val:,}"

                disp_input = input_str if j == 0 else ""

                if to:
                    vals = (disp_input, name, "TIMEOUT", "-", "-", "TIMEOUT")
                elif sol is None:
                    vals = (disp_input, name, "-", "-", "-", "FAILED")
                else:
                    vals = (disp_input, name, f"{t:.2f}", f"{m:.2f}", met_str, "SOLVED")
                    solved_count += 1
                self.tree.insert("", tk.END, values=vals)

            if i < len(indices) - 1:
                self.tree.insert("", tk.END, values=("─" * 8,) * 6, tags=('sep',))
        
        if solved_count > 0:
            self.bench_save_btn.config(state=tk.NORMAL)
        else:
            self.bench_save_btn.config(state=tk.DISABLED)

    def save_benchmark_results(self):
        if not self.benchmark_data:
            return
        
        indices = self.benchmark_data["indices"]
        grids = self.benchmark_data.get("grids", {})
        saved = []
        
        for name, res in self.benchmark_data["solvers"].items():
            for i, idx in enumerate(indices):
                solution = res["solutions"][i]
                islands = res["islands"][i]
                grid = grids.get(idx)
                
                if solution is not None and grid is not None:
                    write_output(name, idx, grid, islands, solution)
                    saved.append(f"{name}/output-{idx:02d}.txt")
        
        if saved:
            messagebox.showinfo("Saved", f"Đã lưu {len(saved)} files vào Outputs/")
        else:
            messagebox.showwarning("Warning", "Không có kết quả SOLVED nào.")

    def on_close(self):
        if self.executor:
            self.executor.shutdown(wait=False, cancel_futures=True)
        self.root.destroy()
        os._exit(0)
