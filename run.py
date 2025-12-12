#!/usr/bin/env python3
"""Hashiwokakero Solver - CSC14003 Group 3"""
import sys, os
import tkinter as tk

SOURCE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Source")
sys.path.insert(0, SOURCE)
os.chdir(SOURCE)

def run_gui():
    from gui import HashiGUI
    root = tk.Tk()
    HashiGUI(root)
    root.mainloop()

if __name__ == "__main__":
    run_gui()
