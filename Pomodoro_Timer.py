import os
# ============================================
# 导入必要的Python标准库和第三方库
# ============================================
import subprocess  # 用于调用系统命令，如启动外部音乐播放器
import sys  # 系统相关操作
import threading  # 多线程支持，用于后台计时
import time  # 时间处理功能
import tkinter as tk  # Python标准GUI图形界面库
from tkinter import ttk, filedialog, messagebox  # Tkinter扩展组件

import pygame  # 多媒体库，主要用于播放背景音乐


class WorkTimerApp:
    def __init__(self, break_time=300, work_time=25 * 60):
        # ============================================
        # 创建主窗口和基本配置
        # ============================================
        self.root = tk.Tk()  # 创建主窗口对象
        self.root.title("番茄计时器")  # 设置窗口标题
        self.root.geometry("400x550")  # 设置窗口尺寸 400x600像素
        self.root.resizable(False, False)  # 禁止调整窗口大小

        # 设置窗口图标和协议
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # 初始化音乐播放器
        pygame.mixer.init()
        self.music_file = None
        self.music_thread = None
        self.stop_music = threading.Event()

        # 工作状态
        self.work_time = work_time
        self.break_time = break_time
        self.is_working = True
        self.is_running = False
        self.remaining_time = self.work_time
        self.auto_restart = True

        # 计时器控制
        self.timer_running = threading.Event()
        self.current_timer_thread = None

        # 加载金句
        self.quotes = self.load_quotes()

        self.setup_ui()

    def setup_ui(self):
        # 主框架
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 标题
        title_label = ttk.Label(main_frame, text="工作计时器", font=("Arial", 16, "bold"))
        title_label.pack(pady=10)

        # 计时器显示
        self.time_label = ttk.Label(main_frame, text=self.format_time(self.remaining_time),
                                    font=("Arial", 24, "bold"))
        self.time_label.pack(pady=20)

        # 进度条
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var,
                                            maximum=self.work_time, length=300)
        self.progress_bar.pack(pady=10)

        # 状态标签
        self.status_label = ttk.Label(main_frame, text="准备开始工作", font=("Arial", 12))
        self.status_label.pack(pady=10)

        # 控制按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=20)

        # 使用更大的按钮提高可用性
        self.start_button = ttk.Button(button_frame, text="开始", command=self.start_timer, width=10)
        self.start_button.pack(side=tk.LEFT, padx=8)

        self.pause_button = ttk.Button(button_frame, text="暂停", command=self.pause_timer,
                                       state=tk.DISABLED, width=10)
        self.pause_button.pack(side=tk.LEFT, padx=8)

        self.skip_work_button = ttk.Button(button_frame, text="跳过工作", command=self.skip_work,
                                           state=tk.DISABLED, width=10)
        self.skip_work_button.pack(side=tk.LEFT, padx=8)

        self.reset_button = ttk.Button(button_frame, text="重置", command=self.reset_timer, width=10)
        self.reset_button.pack(side=tk.LEFT, padx=8)

        # 时间设置按钮
        ttk.Button(main_frame, text="设置时间", command=self.open_time_settings, width=30).pack(pady=15)

        # 设置框架
        settings_frame = ttk.LabelFrame(main_frame, text="设置", padding="10")
        settings_frame.pack(fill=tk.X, pady=15)

        # 音乐选择
        music_frame = ttk.Frame(settings_frame)
        music_frame.pack(fill=tk.X, pady=5)

        ttk.Label(music_frame, text="休息音乐:").pack(side=tk.LEFT)
        self.music_label = ttk.Label(music_frame, text="未选择", width=20)
        self.music_label.pack(side=tk.LEFT, padx=10)
        ttk.Button(music_frame, text="选择", command=self.select_music).pack(side=tk.LEFT)

        # 自动重启选项
        auto_restart_frame = ttk.Frame(settings_frame)
        auto_restart_frame.pack(fill=tk.X, pady=5)

        self.auto_restart_var = tk.BooleanVar(value=self.auto_restart)
        auto_restart_check = ttk.Checkbutton(
            auto_restart_frame,
            text="自动重新开始",
            variable=self.auto_restart_var,
            command=self.toggle_auto_restart
        )
        auto_restart_check.pack(side=tk.LEFT)

        # 测试音乐按钮（可选）
        if self.music_file:
            ttk.Button(settings_frame, text="测试音乐", command=self.test_music).pack(pady=5)

    def format_time(self, seconds):
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes:02d}:{seconds:02d}"

    def toggle_auto_restart(self):
        self.auto_restart = self.auto_restart_var.get()

    def load_quotes(self):
        """加载金句"""
        quotes_file = os.path.join(os.path.dirname(__file__), "motivational_quotes.txt")
        try:
            if os.path.exists(quotes_file):
                with open(quotes_file, "r", encoding="utf-8") as f:
                    quotes = [line.strip() for line in f if line.strip()]
                return quotes
            else:
                # 创建默认的金句文件
                default_quotes = [
                    "休息是为了走更长远的路。",
                    "劳逸结合是高效工作的关键。",
                    "短暂的休息，更好的开始。",
                    "停下来是为了更好的前进。",
                    "what will be will be  该来的总会来",
                    "往者不可谏，来者犹可追\n——《论语·微子》",
                    "The more you look, the less you see.俞看其表，俞不见其里"
                ]
                try:
                    with open(quotes_file, "w", encoding="utf-8") as f:
                        f.write("\n".join(default_quotes))
                except:
                    pass  # 如果无法创建文件，继续使用默认值
                return default_quotes
        except Exception as e:
            print(f"加载金句时出错: {e}")
            return ["停下来是为了更好的前进。", "劳逸结合是高效工作的关键。"]

    def get_random_quote(self):
        """获取随机金句"""
        if self.quotes:
            import random
            return random.choice(self.quotes)
        return "休息一下，让大脑重新充电"

    def start_timer(self):
        if not self.is_running:
            self.is_running = True
            self.timer_running.set()  # 设置事件为真
            self.update_buttons_state()

            # 创建新的计时器线程
            self.current_timer_thread = threading.Thread(target=self.run_timer, daemon=True)
            self.current_timer_thread.start()

    def pause_timer(self):
        self.is_running = False
        self.timer_running.clear()  # 清除事件
        self.update_buttons_state()

    def reset_timer(self):
        self.is_running = False
        self.timer_running.clear()
        self.is_working = True
        self.remaining_time = self.work_time
        self.update_display()
        self.update_buttons_state()
        self.status_label.config(text="准备开始工作")

    def update_buttons_state(self):
        """更新按钮状态"""
        if self.is_running:
            self.start_button.config(state=tk.DISABLED)
            self.pause_button.config(state=tk.NORMAL)
            self.skip_work_button.config(state=tk.NORMAL if self.is_working else tk.DISABLED)
        else:
            self.start_button.config(state=tk.NORMAL)
            self.pause_button.config(state=tk.DISABLED)
            self.skip_work_button.config(state=tk.DISABLED)

    def run_timer(self):
        """计时器线程函数"""
        while self.is_running and self.remaining_time > 0:
            start_time = time.time()

            # 等待1秒或直到暂停
            if self.timer_running.wait(1.0):
                self.remaining_time -= 1
                self.update_display()
            else:
                # 计时器被暂停，跳出循环
                break

            # 调整时间补偿，保持精确
            elapsed = time.time() - start_time
            if elapsed < 1.0:
                time.sleep(1.0 - elapsed)

        if self.remaining_time <= 0 and self.is_running:
            self.is_running = False
            self.timer_running.clear()
            self.root.after(0, self.timer_complete)

    def update_display(self):
        """更新显示"""
        self.root.after(0, self._update_display)

    def _update_display(self):
        self.time_label.config(text=self.format_time(self.remaining_time))

        if self.is_working:
            progress_value = self.work_time - self.remaining_time
            self.progress_var.set(progress_value)
            self.progress_bar.config(maximum=self.work_time)
            self.status_label.config(text=f"工作中... {self.format_time(self.remaining_time)}")
        else:
            progress_value = self.break_time - self.remaining_time
            self.progress_var.set(progress_value)
            self.progress_bar.config(maximum=self.break_time)
            self.status_label.config(text=f"休息中... {self.format_time(self.remaining_time)}")

    def timer_complete(self):
        """计时器完成回调"""
        if self.is_working:
            # 工作结束，开始休息
            self.is_working = False
            self.remaining_time = self.break_time
            self.show_break_window()
        else:
            # 休息结束，开始工作
            self.is_working = True
            self.remaining_time = self.work_time
            self.stop_music_event()
            self.status_label.config(text="工作完成! 准备开始下一轮")

            # 如果启用自动重启，则自动开始下一轮
            if self.auto_restart:
                self.root.after(1000, self._auto_start)
            else:
                self.update_buttons_state()

    def _auto_start(self):
        """自动开始下一轮"""
        if not self.is_running:
            self.start_timer()

    def show_break_window(self):
        """显示休息窗口"""
        # 创建休息窗口
        self.break_window = tk.Toplevel(self.root)
        self.break_window.title("休息时间")
        self.break_window.attributes('-topmost', True)

        # 设置窗口大小和位置
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        window_width = 300
        window_height = 200
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.break_window.geometry(f"{window_width}x{window_height}+{x}+{y}")

        # 绑定关闭事件
        self.break_window.protocol("WM_DELETE_WINDOW", lambda: self.skip_break(self.break_window))

        # 休息内容框架
        content_frame = ttk.Frame(self.break_window)
        content_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        # 倒计时标签
        break_time_label = ttk.Label(content_frame, text="休息时间", font=("Arial", 14, "bold"))
        break_time_label.pack(pady=5)

        self.break_time_var = tk.StringVar()
        self.break_time_var.set(self.format_time(self.break_time))
        break_timer_label = ttk.Label(content_frame, textvariable=self.break_time_var,
                                      font=("Arial", 18, "bold"))
        break_timer_label.pack(pady=5)

        # 随机金句
        quote_label = ttk.Label(content_frame, text=self.get_random_quote(),
                                font=("Arial", 10), wraplength=250, justify="center")
        quote_label.pack(pady=5)

        # 休息进度条
        self.break_progress_var = tk.DoubleVar()
        self.break_progress_var.set(0)
        break_progress = ttk.Progressbar(content_frame, variable=self.break_progress_var,
                                         maximum=self.break_time, length=200)
        break_progress.pack(pady=10)

        # 跳过休息按钮
        skip_button = ttk.Button(content_frame, text="跳过休息",
                                 command=lambda: self.skip_break(self.break_window))
        skip_button.pack(pady=5)

        # 开始播放音乐
        self.start_music()

        # 开始休息计时
        self.start_break_timer()

    def start_break_timer(self):
        """开始休息计时"""
        if self.remaining_time > 0:
            self.remaining_time -= 1
            self.break_time_var.set(self.format_time(self.remaining_time))
            self.break_progress_var.set(self.break_time - self.remaining_time)

            # 更新主窗口的显示
            self.update_display()

            # 设置下一次更新
            self.break_window.after(1000, self.start_break_timer)
        else:
            # 休息时间结束
            if hasattr(self, 'break_window') and self.break_window:
                self.break_window.destroy()
            self.timer_complete()

    def skip_break(self, break_window):
        """跳过休息"""
        break_window.destroy()
        self.remaining_time = 0
        self.stop_music_event()
        self.timer_complete()

    def skip_work(self):
        """跳过工作时间"""
        if self.is_running and self.is_working:
            self.remaining_time = 0
            self.root.after(0, self.timer_complete)

    def start_music(self):
        """开始播放音乐"""
        if self.music_file:
            self.stop_music_event()  # 先停止之前的音乐
            self.stop_music.clear()  # 清除停止标志
            self.music_thread = threading.Thread(target=self.play_music, daemon=True)
            self.music_thread.start()

    def stop_music_event(self):
        """停止音乐事件"""
        self.stop_music.set()  # 设置停止标志
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()

    def play_music(self):
        """播放音乐线程函数"""
        try:
            # 尝试使用pygame播放
            pygame.mixer.music.load(self.music_file)
            pygame.mixer.music.play(-1)  # -1表示循环播放

            # 等待音乐停止
            while pygame.mixer.music.get_busy() and not self.stop_music.is_set():
                time.sleep(0.1)

        except pygame.error as e:
            # 如果pygame播放失败，尝试使用系统默认播放器
            print(f"PyGame播放失败: {e}")
            try:
                if sys.platform == "win32":
                    subprocess.Popen(["start", "", self.music_file], shell=True)
                elif sys.platform == "darwin":  # macOS
                    subprocess.Popen(["open", self.music_file])
                else:  # Linux
                    subprocess.Popen(["xdg-open", self.music_file])
            except Exception as e2:
                print(f"使用系统播放器播放音乐时出错: {e2}")
                messagebox.showerror("播放错误", f"无法播放音乐: {e2}")
        except Exception as e:
            print(f"播放音乐时出错: {e}")
            messagebox.showerror("播放错误", f"无法播放音乐: {e}")

    def test_music(self):
        """测试音乐播放"""
        if self.music_file:
            try:
                pygame.mixer.music.load(self.music_file)
                pygame.mixer.music.play()
                messagebox.showinfo("测试音乐", "正在播放测试音乐...")
            except Exception as e:
                messagebox.showerror("播放错误", f"无法播放音乐: {e}")
        else:
            messagebox.showwarning("未选择音乐", "请先选择音乐文件")

    def open_time_settings(self):
        """打开时间设置对话框"""
        dialog = TimeSettingsDialog(self.root, self.work_time, self.break_time)
        self.root.wait_window(dialog.dialog)

        if dialog.result:
            self.work_time = dialog.work_time
            self.break_time = dialog.break_time
            self.reset_timer()

    def select_music(self):
        """选择音乐文件"""
        file_path = filedialog.askopenfilename(
            title="选择音乐文件",
            filetypes=[("音频文件", "*.mp3 *.wav *.ogg *.flac *.mp4"),
                       ("所有文件", "*.*")]
        )
        if file_path:  # 如果用户选择了文件
            self.music_file = file_path  # 保存音乐文件路径
            # 更新显示标签，只显示文件名的前20个字符
            filename = os.path.basename(file_path)  # 获取文件名
            display_text = filename[:20] + "..." if len(filename) > 20 else filename
            self.music_label.config(text=display_text)

    def on_closing(self):
        """窗口关闭事件处理"""
        self.stop_music_event()
        self.is_running = False
        self.timer_running.set()  # 唤醒等待的线程
        self.root.destroy()

    def run(self):
        """运行应用程序"""
        self.root.mainloop()


class TimeSettingsDialog:
    """时间设置对话框类"""

    def __init__(self, parent, work_time, break_time):
        self.result = False
        self.work_time = work_time
        self.break_time = break_time

        # 创建对话框
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("时间设置")
        self.dialog.geometry("300x400")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # 居中显示
        self.center_window()

        self.create_widgets()

    def center_window(self):
        """将窗口居中显示"""
        self.dialog.update_idletasks()
        width = self.dialog.winfo_width()
        height = self.dialog.winfo_height()
        x = (self.dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (height // 2)
        self.dialog.geometry(f'{width}x{height}+{x}+{y}')

    def create_widgets(self):
        """创建对话框控件"""
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 标题
        title_label = ttk.Label(main_frame, text="设置工作和休息时间", font=("Arial", 14, "bold"))
        title_label.pack(pady=(0, 20))

        # 工作时间设置
        work_frame = ttk.LabelFrame(main_frame, text="工作时间", padding="10")
        work_frame.pack(fill=tk.X, pady=(0, 15))

        work_time_frame = ttk.Frame(work_frame)
        work_time_frame.pack()

        ttk.Label(work_time_frame, text="分钟:").pack(side=tk.LEFT)
        self.work_minutes_var = tk.StringVar(value=str(self.work_time // 60))
        self.work_minutes = tk.Spinbox(work_time_frame, from_=1, to=120, width=5,
                                       textvariable=self.work_minutes_var)
        self.work_minutes.pack(side=tk.LEFT, padx=(5, 15))

        ttk.Label(work_time_frame, text="秒:").pack(side=tk.LEFT)
        self.work_seconds_var = tk.StringVar(value=str(self.work_time % 60))
        self.work_seconds = tk.Spinbox(work_time_frame, from_=0, to=59, width=5,
                                       textvariable=self.work_seconds_var)
        self.work_seconds.pack(side=tk.LEFT, padx=(5, 0))

        # 休息时间设置
        break_frame = ttk.LabelFrame(main_frame, text="休息时间", padding="10")
        break_frame.pack(fill=tk.X, pady=(0, 20))

        break_time_frame = ttk.Frame(break_frame)
        break_time_frame.pack()

        ttk.Label(break_time_frame, text="分钟:").pack(side=tk.LEFT)
        self.break_minutes_var = tk.StringVar(value=str(self.break_time // 60))
        self.break_minutes = tk.Spinbox(break_time_frame, from_=1, to=60, width=5,
                                        textvariable=self.break_minutes_var)
        self.break_minutes.pack(side=tk.LEFT, padx=(5, 15))

        ttk.Label(break_time_frame, text="秒:").pack(side=tk.LEFT)
        self.break_seconds_var = tk.StringVar(value=str(self.break_time % 60))
        self.break_seconds = tk.Spinbox(break_time_frame, from_=0, to=59, width=5,
                                        textvariable=self.break_seconds_var)
        self.break_seconds.pack(side=tk.LEFT, padx=(5, 0))

        # 预设按钮
        preset_frame = ttk.Frame(main_frame)
        preset_frame.pack(fill=tk.X, pady=(0, 20))

        ttk.Label(preset_frame, text="快速设置:").pack(anchor=tk.W)

        button_frame = ttk.Frame(preset_frame)
        button_frame.pack(pady=5)

        ttk.Button(button_frame, text="(25/5)",
                   command=lambda: self.set_preset(25, 5)).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="(40/10)",
                   command=lambda: self.set_preset(40, 10)).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="(50/10)",
                   command=lambda: self.set_preset(50, 10)).pack(side=tk.LEFT, padx=5)

        # 按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)

        ttk.Button(button_frame, text="确定", command=self.on_ok).pack(side=tk.RIGHT, padx=(10, 0))
        ttk.Button(button_frame, text="取消", command=self.on_cancel).pack(side=tk.RIGHT)

    def set_preset(self, work_min, break_min):
        """设置预设时间"""
        self.work_minutes_var.set(str(work_min))
        self.work_seconds_var.set("0")
        self.break_minutes_var.set(str(break_min))
        self.break_seconds_var.set("0")

    def on_ok(self):
        """确认按钮回调"""
        try:
            work_min = int(self.work_minutes_var.get())
            work_sec = int(self.work_seconds_var.get())
            break_min = int(self.break_minutes_var.get())
            break_sec = int(self.break_seconds_var.get())

            # 验证输入
            if work_min < 1 or work_min > 120:
                messagebox.showerror("错误", "工作时间必须在1-120分钟之间")
                return
            if break_min < 1 or break_min > 60:
                messagebox.showerror("错误", "休息时间必须在1-60分钟之间")
                return
            if work_sec < 0 or work_sec > 59 or break_sec < 0 or break_sec > 59:
                messagebox.showerror("错误", "秒数必须在0-59之间")
                return

            # 计算总秒数
            self.work_time = work_min * 60 + work_sec
            self.break_time = break_min * 60 + break_sec
            self.result = True
            self.dialog.destroy()

        except ValueError:
            messagebox.showerror("错误", "请输入有效的数字")

    def on_cancel(self):
        """取消按钮回调"""
        self.dialog.destroy()


if __name__ == "__main__":
    app = WorkTimerApp()
    app.run()
