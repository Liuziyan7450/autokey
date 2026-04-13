"""
Windows 后台按键自动化工具（Python + tkinter + pywin32）
-----------------------------------------------------
比纯 AHK ControlSend 更可控的方案：
- 使用 PostMessage 直接向窗口句柄发送 WM_KEYDOWN/WM_KEYUP。
- 支持最小化/未激活窗口（取决于目标程序是否处理消息队列）。
- 支持窗口列表选择、固定/随机间隔、循环次数、随机点击偏移、日志。

依赖：
    pip install pywin32
打包：
    pyinstaller -F -w windows_autokey_py.py
"""

import random
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox

import win32api
import win32con
import win32gui


SPECIAL_KEYS = {
    "TAB": win32con.VK_TAB,
    "ESC": win32con.VK_ESCAPE,
    "SPACE": win32con.VK_SPACE,
    "ENTER": win32con.VK_RETURN,
    "UP": win32con.VK_UP,
    "DOWN": win32con.VK_DOWN,
    "LEFT": win32con.VK_LEFT,
    "RIGHT": win32con.VK_RIGHT,
    "F1": win32con.VK_F1,
    "F2": win32con.VK_F2,
    "F3": win32con.VK_F3,
    "F4": win32con.VK_F4,
}


class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Windows 后台按键自动化工具 (Python)")
        self.root.geometry("760x620")

        self.running = False
        self.worker_thread = None
        self.hwnd_map = {}

        self.build_ui()
        self.refresh_windows()

    def build_ui(self):
        frm = ttk.Frame(self.root, padding=10)
        frm.pack(fill="both", expand=True)

        row = 0
        ttk.Label(frm, text="目标窗口标题(备用匹配):").grid(row=row, column=0, sticky="w")
        self.title_var = tk.StringVar()
        ttk.Entry(frm, textvariable=self.title_var, width=60).grid(row=row, column=1, columnspan=3, sticky="we", padx=6)

        row += 1
        ttk.Button(frm, text="刷新窗口列表", command=self.refresh_windows).grid(row=row, column=0, pady=6, sticky="we")
        self.window_var = tk.StringVar()
        self.window_combo = ttk.Combobox(frm, textvariable=self.window_var, width=70, state="readonly")
        self.window_combo.grid(row=row, column=1, columnspan=2, sticky="we", padx=6)
        ttk.Button(frm, text="使用所选窗口", command=self.use_selected_window).grid(row=row, column=3, pady=6, sticky="we")

        row += 1
        ttk.Button(frm, text="锁定当前活动窗口", command=self.pick_active_window).grid(row=row, column=0, sticky="we")
        self.hwnd_var = tk.StringVar(value="当前未锁定句柄")
        ttk.Label(frm, textvariable=self.hwnd_var).grid(row=row, column=1, columnspan=3, sticky="w", padx=6)

        row += 1
        ttk.Label(frm, text="按键序列(示例: {TAB}3{ESC}{SPACE}):").grid(row=row, column=0, sticky="w", pady=(12, 0))
        self.seq_var = tk.StringVar(value="{TAB}3{ESC}{SPACE}")
        ttk.Entry(frm, textvariable=self.seq_var, width=60).grid(row=row, column=1, columnspan=3, sticky="we", padx=6, pady=(12, 0))

        row += 1
        ttk.Label(frm, text="每步基础延迟(ms):").grid(row=row, column=0, sticky="w", pady=(6, 0))
        self.interval_var = tk.StringVar(value="2000")
        ttk.Entry(frm, textvariable=self.interval_var, width=15).grid(row=row, column=1, sticky="w", pady=(6, 0))

        ttk.Label(frm, text="循环次数(0=无限):").grid(row=row, column=2, sticky="e", pady=(6, 0))
        self.loop_var = tk.StringVar(value="0")
        ttk.Entry(frm, textvariable=self.loop_var, width=15).grid(row=row, column=3, sticky="w", pady=(6, 0))

        row += 1
        self.rand_interval_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(frm, text="启用随机间隔", variable=self.rand_interval_var).grid(row=row, column=0, sticky="w", pady=(6, 0))
        ttk.Label(frm, text="最小(ms):").grid(row=row, column=1, sticky="e", pady=(6, 0))
        self.rand_min_var = tk.StringVar(value="1500")
        ttk.Entry(frm, textvariable=self.rand_min_var, width=12).grid(row=row, column=2, sticky="w", pady=(6, 0))
        ttk.Label(frm, text="最大(ms):").grid(row=row, column=2, sticky="e", padx=(90, 0), pady=(6, 0))
        self.rand_max_var = tk.StringVar(value="2500")
        ttk.Entry(frm, textvariable=self.rand_max_var, width=12).grid(row=row, column=3, sticky="w", pady=(6, 0))

        row += 1
        self.rand_click_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(frm, text="启用随机点击偏移", variable=self.rand_click_var).grid(row=row, column=0, sticky="w", pady=(6, 0))
        ttk.Label(frm, text="基准X:").grid(row=row, column=1, sticky="e", pady=(6, 0))
        self.base_x_var = tk.StringVar(value="200")
        ttk.Entry(frm, textvariable=self.base_x_var, width=12).grid(row=row, column=2, sticky="w", pady=(6, 0))
        ttk.Label(frm, text="基准Y:").grid(row=row, column=2, sticky="e", padx=(90, 0), pady=(6, 0))
        self.base_y_var = tk.StringVar(value="200")
        ttk.Entry(frm, textvariable=self.base_y_var, width=12).grid(row=row, column=3, sticky="w", pady=(6, 0))

        row += 1
        ttk.Label(frm, text="偏移X(±):").grid(row=row, column=1, sticky="e", pady=(6, 0))
        self.off_x_var = tk.StringVar(value="10")
        ttk.Entry(frm, textvariable=self.off_x_var, width=12).grid(row=row, column=2, sticky="w", pady=(6, 0))
        ttk.Label(frm, text="偏移Y(±):").grid(row=row, column=2, sticky="e", padx=(90, 0), pady=(6, 0))
        self.off_y_var = tk.StringVar(value="10")
        ttk.Entry(frm, textvariable=self.off_y_var, width=12).grid(row=row, column=3, sticky="w", pady=(6, 0))

        row += 1
        ttk.Button(frm, text="开始", command=self.start).grid(row=row, column=0, sticky="we", pady=10)
        ttk.Button(frm, text="停止", command=self.stop).grid(row=row, column=1, sticky="we", pady=10)
        ttk.Button(frm, text="清空日志", command=self.clear_log).grid(row=row, column=2, sticky="we", pady=10)

        row += 1
        ttk.Label(frm, text="运行日志:").grid(row=row, column=0, sticky="w")
        row += 1
        self.log = tk.Text(frm, height=18)
        self.log.grid(row=row, column=0, columnspan=4, sticky="nsew")

        frm.columnconfigure(1, weight=1)
        frm.columnconfigure(2, weight=1)
        frm.rowconfigure(row, weight=1)

    def append_log(self, text: str):
        now = time.strftime("%Y-%m-%d %H:%M:%S")
        self.log.insert("end", f"[{now}] {text}\n")
        self.log.see("end")

    def clear_log(self):
        self.log.delete("1.0", "end")

    def refresh_windows(self):
        self.hwnd_map.clear()
        items = []

        def callback(hwnd, _):
            if not win32gui.IsWindowVisible(hwnd):
                return True
            title = win32gui.GetWindowText(hwnd).strip()
            if not title:
                return True
            item = f"[{hwnd}] {title}"
            items.append(item)
            self.hwnd_map[item] = hwnd
            return True

        win32gui.EnumWindows(callback, None)
        self.window_combo["values"] = items
        if items:
            self.window_combo.current(0)
        self.append_log("窗口列表已刷新。")

    def use_selected_window(self):
        selected = self.window_var.get()
        hwnd = self.hwnd_map.get(selected)
        if not hwnd:
            messagebox.showwarning("提示", "请先选择有效窗口。")
            return
        self.hwnd_var.set(f"已锁定句柄: {hwnd}")
        self.target_hwnd = hwnd
        title = win32gui.GetWindowText(hwnd)
        self.title_var.set(title)
        self.append_log(f"已选择窗口: [{hwnd}] {title}")

    def pick_active_window(self):
        hwnd = win32gui.GetForegroundWindow()
        if not hwnd:
            messagebox.showwarning("提示", "当前无法获取活动窗口。")
            return
        self.target_hwnd = hwnd
        title = win32gui.GetWindowText(hwnd)
        self.hwnd_var.set(f"已锁定句柄: {hwnd}")
        self.title_var.set(title)
        self.append_log(f"已锁定当前活动窗口: [{hwnd}] {title}")

    def parse_sequence(self, seq: str):
        # 解析例如：{TAB}3{ESC}{SPACE}
        tokens = []
        i = 0
        while i < len(seq):
            if seq[i] == "{":
                j = seq.find("}", i)
                if j == -1:
                    raise ValueError("按键序列花括号不匹配")
                key_name = seq[i + 1:j].strip().upper()
                if key_name not in SPECIAL_KEYS:
                    raise ValueError(f"不支持的特殊按键: {{{key_name}}}")
                tokens.append(("vk", SPECIAL_KEYS[key_name]))
                i = j + 1
            else:
                ch = seq[i]
                tokens.append(("char", ch))
                i += 1
        return tokens

    def resolve_hwnd(self):
        hwnd = getattr(self, "target_hwnd", 0)
        if hwnd and win32gui.IsWindow(hwnd):
            return hwnd

        title = self.title_var.get().strip()
        if not title:
            return 0

        found = []

        def callback(h, _):
            t = win32gui.GetWindowText(h)
            if title in t:
                found.append(h)
            return True

        win32gui.EnumWindows(callback, None)
        if found:
            self.target_hwnd = found[0]
            self.hwnd_var.set(f"已锁定句柄: {found[0]} (标题匹配)")
            return found[0]
        return 0

    def send_vk(self, hwnd: int, vk_code: int):
        win32api.PostMessage(hwnd, win32con.WM_KEYDOWN, vk_code, 0)
        win32api.PostMessage(hwnd, win32con.WM_KEYUP, vk_code, 0)

    def send_char(self, hwnd: int, ch: str):
        code = win32api.VkKeyScan(ch)
        if code == -1:
            raise ValueError(f"字符无法映射为虚拟键: {ch}")

        vk = code & 0xFF
        shift_state = (code >> 8) & 0xFF

        if shift_state & 1:
            win32api.PostMessage(hwnd, win32con.WM_KEYDOWN, win32con.VK_SHIFT, 0)
        if shift_state & 2:
            win32api.PostMessage(hwnd, win32con.WM_KEYDOWN, win32con.VK_CONTROL, 0)
        if shift_state & 4:
            win32api.PostMessage(hwnd, win32con.WM_KEYDOWN, win32con.VK_MENU, 0)

        win32api.PostMessage(hwnd, win32con.WM_KEYDOWN, vk, 0)
        win32api.PostMessage(hwnd, win32con.WM_KEYUP, vk, 0)

        if shift_state & 4:
            win32api.PostMessage(hwnd, win32con.WM_KEYUP, win32con.VK_MENU, 0)
        if shift_state & 2:
            win32api.PostMessage(hwnd, win32con.WM_KEYUP, win32con.VK_CONTROL, 0)
        if shift_state & 1:
            win32api.PostMessage(hwnd, win32con.WM_KEYUP, win32con.VK_SHIFT, 0)

    def random_click(self, hwnd: int, base_x: int, base_y: int, off_x: int, off_y: int):
        rx = base_x + random.randint(-off_x, off_x)
        ry = base_y + random.randint(-off_y, off_y)
        lparam = (ry << 16) | (rx & 0xFFFF)
        win32api.PostMessage(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lparam)
        win32api.PostMessage(hwnd, win32con.WM_LBUTTONUP, 0, lparam)
        self.append_log(f"随机点击: ({rx}, {ry})")

    def start(self):
        if self.running:
            self.append_log("任务已在运行中。")
            return

        try:
            self.tokens = self.parse_sequence(self.seq_var.get().strip())
            self.base_interval = int(self.interval_var.get())
            self.loop_count = int(self.loop_var.get())
            self.rand_min = int(self.rand_min_var.get())
            self.rand_max = int(self.rand_max_var.get())
            self.base_x = int(self.base_x_var.get())
            self.base_y = int(self.base_y_var.get())
            self.off_x = int(self.off_x_var.get())
            self.off_y = int(self.off_y_var.get())

            if self.base_interval < 0 or self.loop_count < 0:
                raise ValueError("间隔与循环次数不能为负数")
            if self.rand_min < 0 or self.rand_max < 0 or self.rand_min > self.rand_max:
                raise ValueError("随机间隔范围无效")
            if self.off_x < 0 or self.off_y < 0:
                raise ValueError("随机偏移不能为负数")
        except Exception as e:
            messagebox.showerror("参数错误", str(e))
            return

        hwnd = self.resolve_hwnd()
        if not hwnd:
            messagebox.showerror("错误", "未找到目标窗口，请先锁定或输入正确标题")
            return

        self.running = True
        self.sent_count = 0
        self.append_log(f"任务开始: hwnd={hwnd}, 序列={self.seq_var.get()}")
        self.worker_thread = threading.Thread(target=self.worker, daemon=True)
        self.worker_thread.start()

    def stop(self):
        self.running = False
        self.append_log("收到停止指令。")

    def worker(self):
        loops = 0
        while self.running:
            hwnd = self.resolve_hwnd()
            if not hwnd:
                self.append_log("目标窗口已不存在，任务结束。")
                self.running = False
                break

            if self.loop_count != 0 and loops >= self.loop_count:
                self.append_log(f"任务完成，总循环次数={loops}")
                self.running = False
                break

            try:
                if self.rand_click_var.get():
                    self.random_click(hwnd, self.base_x, self.base_y, self.off_x, self.off_y)

                for token_type, value in self.tokens:
                    if token_type == "vk":
                        self.send_vk(hwnd, value)
                    else:
                        self.send_char(hwnd, value)

                    delay_ms = self.base_interval
                    if self.rand_interval_var.get():
                        delay_ms = random.randint(self.rand_min, self.rand_max)
                    time.sleep(delay_ms / 1000.0)

                loops += 1
                self.sent_count += 1
                self.append_log(f"发送成功，第 {self.sent_count} 次。")
            except Exception as e:
                self.append_log(f"发送失败: {e}")
                self.running = False
                break


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
