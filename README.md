# Project 02 - Hashiwokakero Solver (CNF & Search)
**Đồ án môn Cơ sở Trí tuệ Nhân tạo (CSC14003)**  
**VNUHCM - University of Science**

Giải và so sánh nhiều cách tiếp cận cho trò chơi Hashiwokakero (Bridges): PySAT (CNF-SAT), A* Search, Backtracking, và Brute Force. Cung cấp GUI Tkinter để giải từng bài và benchmark nhiều test case, kèm notebook để chạy và xuất bảng kết quả.

---

## Tổng quan

### Trò chơi Hashiwokakero
Nối các đảo mang số sao cho:
1) Cầu đi ngang/dọc giữa hai đảo  
2) Mỗi cặp đảo tối đa 2 cầu  
3) Cầu không cắt nhau, không đi qua đảo  
4) Mỗi đảo có đúng số cầu ghi trên ô  
5) Tất cả đảo phải nối thành một thành phần liên thông

### Thuật toán (4)
- **PySAT**: Mã hóa CNF đầy đủ, giải bằng Glucose4 (CDCL).  
- **A\***: Tìm kiếm với heuristic 
- **Backtracking**: DPLL + Unit Propagation trên CNF.  
- **Brute Force**: Liệt kê 0/1/2 cầu cho từng cạnh, chỉ phù hợp lưới nhỏ.

### Bộ test
15 input (1–15) chia 3 mức: Easy (1–5), Medium (6–10), Hard (11–15).

---

## Cài đặt và Sử dụng

### Yêu cầu
- Python ≥ 3.8
- Thư viện chính: `python-sat`, `numpy`, `matplotlib`, `notebook`, `ipykernel`

### Các bước cài đặt nhanh
```bash
git clone <repository-url>
cd CSC14003-Intro2AI-Hashiwokakero
# (khuyến nghị) python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Chạy GUI
```bash
python run.py
```
GUI có 2 tab:
1) **Single Solve**: Chọn input, solver, timeout → Solve → Save output.  
2) **Benchmark**: Chọn danh sách input, chọn nhiều solver, chạy và lưu kết quả hàng loạt.

### Notebook benchmark
Mở `run.ipynb` và Run All để benchmark 15 test case, xuất bảng thời gian, bộ nhớ và metric từng solver.

---

## Cấu trúc Project
```
CSC14003-Intro2AI-Hashiwokakero/
├── run.py              # Chạy GUI
├── run.ipynb           # Notebook benchmark
├── requirements.txt
└── Source/
    ├── benchmark.py    # Logic benchmark
    ├── cnf_encoder.py  # Mã hóa CNF, sinh biến cạnh, ràng buộc
    ├── utils.py        # Đọc input, vẽ lưới ký tự, ghi output
    ├── gui/
    │   ├── app.py      # Tkinter GUI (Single Solve, Benchmark)
    │   └── display.py  # In bảng kết quả ở console
    ├── solvers/
    │   ├── pysat.py        # PySAT (CDCL)
    │   ├── astar.py        # A* trên biến cầu
    │   ├── backtracking.py # DPLL + Unit Propagation
    │   └── bruteforce.py   # Vét cạn 3^|E|
    ├── Inputs/         # 15 test cases
    └── Outputs/        # Thư mục lưu lời giải
```

---

## Kết quả & Visualizations
- GUI hiển thị lời giải trên lưới; nút Save lưu vào `Outputs/<Solver>/output-XX.txt`.  
- Tab Benchmark trình bày bảng kết quả (thời gian, bộ nhớ, metric, trạng thái).  
- Notebook tạo bảng thời gian/bộ nhớ/metric cho 15 input và 4 solver.

### Tổng hợp (trung bình, timeout không tính vào trung bình)
| Solver | Avg Time (ms) | Avg Mem (MB) | Solved / 15 |
|--------|---------------|--------------|-------------|
| PySAT | 42.8 | 0.41 | 15 / 15 |
| A* | 330.5 | 0.39 | 13 / 15 |
| Backtracking | 857.0 | 0.58 | 10 / 15 |
| BruteForce | 584.7 | 0.04 | 4 / 15 |

---

## Metrics đánh giá
1. **Time (ms)**: Thời gian giải mỗi input.  
2. **Memory (MB)**: RAM đỉnh trong lời giải.  
3. **Solver-specific metrics**:  
   - PySAT: `conflicts`, `decisions`  
   - A*: `expanded_nodes`, `generated_nodes`  
   - Backtracking: `recursive_calls`, `backtracks`  
   - BruteForce: `iterations`  
4. **Timeout**: Đánh dấu trường hợp không xong trong thời gian đặt.

---

## Nhóm thực hiện
- 23122014 – Hoàng Minh Trung  
- 23122015 – Nguyễn Gia Bảo  
- 23122021 – Bùi Duy Bảo  
- 23122039 – Huỳnh Trung Kiệt

---

## License
Đồ án phục vụ mục đích học tập – VNUHCM University of Science.

---

## Hỗ trợ
1) Kiểm tra đã cài dependencies: `pip install -r requirements.txt`  
2) Đảm bảo Python ≥ 3.8  
3) Chạy GUI: `python run.py`; hoặc mở `run.ipynb` để benchmark.  

