import os
import sys
import zipfile
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, scrolledtext
from PIL import Image, ImageTk
import shutil
import tempfile
import subprocess
import time
import threading
import traceback
from pathlib import Path


class FileCompressorDecompressor:
    def __init__(self, root):
        self.extract_path = ""

        self.root = root
        self.root.title("文件压缩解压工具")
        self.root.geometry("1000x800")
        self.root.minsize(1000, 800)

        # 确保中文显示正常
        self.setup_fonts()

        # 变量初始化
        self.compress_files = []
        self.extract_file = ""
        self.image_path = ""
        self.output_dir = os.getcwd()
        self.pyinstaller_log = ""  # 存储PyInstaller的日志

        # 创建界面
        self.create_widgets()

    def setup_fonts(self):
        # 设置默认字体支持中文
        default_font = ('SimHei', 10)
        self.root.option_add("*Font", default_font)

    def create_widgets(self):
        # 创建主标签页
        tab_control = ttk.Notebook(self.root)

        # 压缩标签页
        self.compress_tab = ttk.Frame(tab_control)
        tab_control.add(self.compress_tab, text="压缩文件")

        # 解压标签页
        self.decompress_tab = ttk.Frame(tab_control)
        tab_control.add(self.decompress_tab, text="解压文件")

        # 日志标签页
        self.log_tab = ttk.Frame(tab_control)
        tab_control.add(self.log_tab, text="运行日志")

        # 关于标签页
        self.about_tab = ttk.Frame(tab_control)
        tab_control.add(self.about_tab, text="关于")

        tab_control.pack(expand=1, fill="both")

        # 设置各标签页
        self.create_compress_tab()
        self.create_decompress_tab()
        self.create_log_tab()
        self.create_about_tab()

    def create_log_tab(self):
        """创建日志标签页，用于显示错误信息和调试内容"""
        main_frame = ttk.Frame(self.log_tab, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text="PyInstaller 输出日志:").pack(anchor=tk.W, pady=(0, 5))

        self.log_text = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.log_text.config(state=tk.DISABLED)

        # 清除日志按钮
        clear_btn = ttk.Button(main_frame, text="清除日志", command=self.clear_log)
        clear_btn.pack(pady=10, anchor=tk.E)

    def clear_log(self):
        """清除日志内容"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.pyinstaller_log = ""

    def append_log(self, text):
        """向日志添加内容"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, text + "\n")
        self.log_text.see(tk.END)  # 滚动到最后
        self.log_text.config(state=tk.DISABLED)
        self.pyinstaller_log += text + "\n"

    def create_compress_tab(self):
        # 压缩标签页内容
        main_frame = ttk.Frame(self.compress_tab, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 文件列表区域
        ttk.Label(main_frame, text="待压缩文件/文件夹:").pack(anchor=tk.W, pady=(0, 5))

        file_frame = ttk.Frame(main_frame)
        file_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        self.file_listbox = tk.Listbox(file_frame, selectmode=tk.EXTENDED)
        scrollbar = ttk.Scrollbar(file_frame, orient=tk.VERTICAL, command=self.file_listbox.yview)
        self.file_listbox.config(yscrollcommand=scrollbar.set)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 按钮区域
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(0, 10))

        add_file_btn = ttk.Button(btn_frame, text="添加文件", command=self.add_files)
        add_file_btn.pack(side=tk.LEFT, padx=5)

        add_dir_btn = ttk.Button(btn_frame, text="添加文件夹", command=self.add_directory)
        add_dir_btn.pack(side=tk.LEFT, padx=5)

        remove_btn = ttk.Button(btn_frame, text="移除选中", command=self.remove_selected)
        remove_btn.pack(side=tk.LEFT, padx=5)

        clear_btn = ttk.Button(btn_frame, text="清空列表", command=self.clear_file_list)
        clear_btn.pack(side=tk.LEFT, padx=5)

        # 选项区域
        options_frame = ttk.LabelFrame(main_frame, text="压缩选项", padding="10")
        options_frame.pack(fill=tk.X, pady=(0, 10))

        # 解压图片选择
        image_frame = ttk.Frame(options_frame)
        image_frame.pack(fill=tk.X, pady=5)

        ttk.Label(image_frame, text="解压时显示的图片:").pack(side=tk.LEFT, padx=5)
        self.compress_image_entry = ttk.Entry(image_frame)
        self.compress_image_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        browse_image_btn = ttk.Button(image_frame, text="浏览", command=self.browse_compress_image)
        browse_image_btn.pack(side=tk.LEFT, padx=5)

        # 输出目录
        output_frame = ttk.Frame(options_frame)
        output_frame.pack(fill=tk.X, pady=5)

        ttk.Label(output_frame, text="输出目录:").pack(side=tk.LEFT, padx=5)
        self.compress_output_entry = ttk.Entry(output_frame)
        self.compress_output_entry.insert(0, self.output_dir)
        self.compress_output_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        browse_output_btn = ttk.Button(output_frame, text="浏览", command=self.browse_compress_output)
        browse_output_btn.pack(side=tk.LEFT, padx=5)

        # 文件名
        name_frame = ttk.Frame(options_frame)
        name_frame.pack(fill=tk.X, pady=5)

        ttk.Label(name_frame, text="压缩文件名:").pack(side=tk.LEFT, padx=5)
        self.archive_name_entry = ttk.Entry(name_frame)
        self.archive_name_entry.insert(0, "archive")
        self.archive_name_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        ttk.Label(name_frame, text=".exe").pack(side=tk.LEFT, padx=5)

        # 高级选项
        advanced_frame = ttk.LabelFrame(options_frame, text="高级选项", padding="5")
        advanced_frame.pack(fill=tk.X, pady=5)

        self.debug_mode = tk.BooleanVar(value=False)
        debug_check = ttk.Checkbutton(advanced_frame, text="调试模式（显示更多日志）", variable=self.debug_mode)
        debug_check.pack(anchor=tk.W, padx=5, pady=2)

        # 进度区域
        progress_frame = ttk.Frame(main_frame)
        progress_frame.pack(fill=tk.X, pady=10)

        self.compress_progress_var = tk.DoubleVar()
        self.compress_progress_bar = ttk.Progressbar(progress_frame, variable=self.compress_progress_var, maximum=100)
        self.compress_progress_bar.pack(fill=tk.X, side=tk.LEFT, expand=True, padx=5)

        self.compress_percent_label = ttk.Label(progress_frame, text="0%")
        self.compress_percent_label.pack(side=tk.LEFT, padx=5)

        # 状态标签
        self.compress_status_label = ttk.Label(main_frame, text="就绪", foreground="blue")
        self.compress_status_label.pack(anchor=tk.W, pady=(0, 10))

        # 压缩按钮
        compress_btn = ttk.Button(main_frame, text="生成自解压EXE", command=self.start_compression)
        compress_btn.pack(pady=10)

    def create_decompress_tab(self):
        # 解压标签页内容
        main_frame = ttk.Frame(self.decompress_tab, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 选择文件区域
        file_frame = ttk.Frame(main_frame)
        file_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(file_frame, text="选择要解压的文件:").pack(side=tk.LEFT, padx=5)
        self.decompress_file_entry = ttk.Entry(file_frame)
        self.decompress_file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        browse_btn = ttk.Button(file_frame, text="浏览", command=self.browse_decompress_file)
        browse_btn.pack(side=tk.LEFT, padx=5)

        # 输出目录
        output_frame = ttk.Frame(main_frame)
        output_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(output_frame, text="解压到:").pack(side=tk.LEFT, padx=5)
        self.decompress_output_entry = ttk.Entry(output_frame)
        self.decompress_output_entry.insert(0, os.path.join(os.path.expanduser('~'), "Documents", "extracted_files"))
        self.decompress_output_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # 修复了这里的变量名错误，将browse_output_output_btn改为browse_output_btn
        browse_output_btn = ttk.Button(output_frame, text="浏览", command=self.browse_decompress_output)
        browse_output_btn.pack(side=tk.LEFT, padx=5)

        # 预览区域
        preview_frame = ttk.LabelFrame(main_frame, text="预览", padding="10")
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        self.preview_text = scrolledtext.ScrolledText(preview_frame, wrap=tk.WORD, height=10)
        self.preview_text.pack(fill=tk.BOTH, expand=True)
        self.preview_text.config(state=tk.DISABLED)

        # 进度区域
        progress_frame = ttk.Frame(main_frame)
        progress_frame.pack(fill=tk.X, pady=10)

        self.decompress_progress_var = tk.DoubleVar()
        self.decompress_progress_bar = ttk.Progressbar(progress_frame, variable=self.decompress_progress_var,
                                                       maximum=100)
        self.decompress_progress_bar.pack(fill=tk.X, side=tk.LEFT, expand=True, padx=5)

        self.decompress_percent_label = ttk.Label(progress_frame, text="0%")
        self.decompress_percent_label.pack(side=tk.LEFT, padx=5)

        # 状态标签
        self.decompress_status_label = ttk.Label(main_frame, text="就绪", foreground="blue")
        self.decompress_status_label.pack(anchor=tk.W, pady=(0, 10))

        # 解压按钮
        decompress_btn = ttk.Button(main_frame, text="开始解压", command=self.start_decompression)
        decompress_btn.pack(pady=10)

    def create_about_tab(self):
        # 关于标签页内容
        main_frame = ttk.Frame(self.about_tab, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text="文件压缩解压工具", font=('SimHei', 16, 'bold')).pack(pady=10)

        about_text = """
这是一个图形化界面的文件压缩解压工具，具有以下功能：

1. 将多个文件或文件夹压缩成自解压的EXE文件
2. 自定义解压过程中显示的图片
3. 解压由本工具生成的自解压EXE文件（支持双击自动解压）
4. 直观的进度显示和操作反馈

使用说明：
- 在"压缩文件"标签页添加需要压缩的文件/文件夹，选择解压图片和输出目录，点击"生成自解压EXE"
- 生成的EXE文件可双击直接解压，也可在"解压文件"标签页选择解压

版本: 1.3.1
        """

        text_widget = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, font=('SimHei', 10))
        text_widget.pack(fill=tk.BOTH, expand=True)
        text_widget.insert(tk.END, about_text)
        text_widget.config(state=tk.DISABLED)

    # 压缩相关方法
    def add_files(self):
        files = filedialog.askopenfilenames(title="选择文件")
        if files:
            for file in files:
                if file not in self.compress_files:
                    self.compress_files.append(file)
                    self.file_listbox.insert(tk.END, file)

    def add_directory(self):
        directory = filedialog.askdirectory(title="选择文件夹")
        if directory and directory not in self.compress_files:
            self.compress_files.append(directory)
            self.file_listbox.insert(tk.END, directory)

    def remove_selected(self):
        selected_indices = sorted(self.file_listbox.curselection(), reverse=True)
        for index in selected_indices:
            self.file_listbox.delete(index)
            del self.compress_files[index]

    def clear_file_list(self):
        self.file_listbox.delete(0, tk.END)
        self.compress_files = []

    def browse_compress_image(self):
        file_path = filedialog.askopenfilename(
            title="选择图片",
            filetypes=[("图片文件", "*.png;*.jpg;*.jpeg;*.bmp;*.gif")]
        )
        if file_path:
            self.image_path = file_path
            self.compress_image_entry.delete(0, tk.END)
            self.compress_image_entry.insert(0, file_path)

    def browse_compress_output(self):
        directory = filedialog.askdirectory(title="选择输出目录")
        if directory:
            self.output_dir = directory
            self.compress_output_entry.delete(0, tk.END)
            self.compress_output_entry.insert(0, directory)

    def update_compress_progress(self, value):
        self.compress_progress_var.set(value)
        self.compress_percent_label.config(text=f"{int(value)}%")
        self.root.update_idletasks()

    def update_compress_status(self, text, is_error=False):
        self.compress_status_label.config(text=text, foreground="red" if is_error else "blue")
        self.root.update_idletasks()

    # 解压相关方法
    def browse_decompress_file(self):
        file_path = filedialog.askopenfilename(
            title="选择要解压的文件",
            filetypes=[("EXE文件", "*.exe")]
        )
        if file_path:
            self.extract_file = file_path
            self.decompress_file_entry.delete(0, tk.END)
            self.decompress_file_entry.insert(0, file_path)
            self.preview_archive()

    def browse_decompress_output(self):
        directory = filedialog.askdirectory(title="选择解压目录")
        if directory:
            self.decompress_output_entry.delete(0, tk.END)
            self.decompress_output_entry.insert(0, directory)

    def update_decompress_progress(self, value):
        self.decompress_progress_var.set(value)
        self.decompress_percent_label.config(text=f"{int(value)}%")
        self.root.update_idletasks()

    def update_decompress_status(self, text, is_error=False):
        self.decompress_status_label.config(text=text, foreground="red" if is_error else "blue")
        self.root.update_idletasks()

    def preview_archive(self):
        try:
            self.preview_text.config(state=tk.NORMAL)
            self.preview_text.delete(1.0, tk.END)

            if not self.extract_file or not os.path.exists(self.extract_file):
                self.preview_text.insert(tk.END, "请选择有效的EXE文件")
                self.preview_text.config(state=tk.DISABLED)
                return

            # 先验证是否为有效的ZIP或自解压文件
            if not self.is_valid_zip(self.extract_file):
                self.preview_text.insert(tk.END, "所选文件不是有效的自解压文件")
                self.preview_text.config(state=tk.DISABLED)
                return

            # 尝试预览压缩包内容
            with zipfile.ZipFile(self.extract_file, 'r') as zip_ref:
                self.preview_text.insert(tk.END, "压缩包内容预览:\n\n")
                for file_info in zip_ref.infolist():
                    if not file_info.filename.endswith('/'):  # 只显示文件，不显示目录
                        self.preview_text.insert(tk.END, f"- {file_info.filename}\n")

            self.preview_text.config(state=tk.DISABLED)
        except Exception as e:
            self.preview_text.insert(tk.END, f"无法预览压缩包内容: {str(e)}")
            self.preview_text.config(state=tk.DISABLED)

    # 核心功能实现
    def start_compression(self):
        if not self.compress_files:
            messagebox.showwarning("警告", "请添加要压缩的文件或文件夹")
            return

        if not self.image_path or not os.path.exists(self.image_path):
            messagebox.showwarning("警告", "请选择有效的图片文件")
            return

        output_dir = self.compress_output_entry.get()
        if not output_dir or not os.path.exists(output_dir):
            messagebox.showwarning("警告", "请选择有效的输出目录")
            return

        # 检查输出目录权限
        if not os.access(output_dir, os.W_OK):
            messagebox.showerror("权限错误", f"没有写入权限: {output_dir}\n请选择其他目录")
            return

        archive_name = self.archive_name_entry.get().strip()
        if not archive_name:
            messagebox.showwarning("警告", "请输入压缩文件名")
            return

        output_path = os.path.join(output_dir, f"{archive_name}.exe")

        # 确认是否覆盖已有文件
        if os.path.exists(output_path):
            if not messagebox.askyesno("确认", f"文件 {output_path} 已存在，是否覆盖?"):
                return

        # 清空之前的日志
        self.clear_log()
        self.append_log("开始压缩流程...")

        # 在新线程中执行压缩，避免界面卡顿
        threading.Thread(target=self.perform_compression, args=(output_path,), daemon=True).start()

    def perform_compression(self, output_path):
        try:
            self.update_compress_status("准备压缩...")
            self.update_compress_progress(0)
            self.append_log("准备压缩...")

            # 创建临时目录
            with tempfile.TemporaryDirectory() as temp_dir:
                self.append_log(f"创建临时目录: {temp_dir}")
                self.update_compress_status("创建临时文件...")
                self.update_compress_progress(5)

                # 创建ZIP文件名称
                zip_name = "packed_files"
                zip_path = os.path.join(temp_dir, f"{zip_name}.zip")

                # 打包文件
                self.update_compress_status("正在打包文件...")
                self.update_compress_progress(10)
                self.append_log("开始打包文件...")

                total_items = self.count_items(self.compress_files)
                processed_items = 0
                self.append_log(f"总计需要处理 {total_items} 个文件")

                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for item in self.compress_files:
                        if os.path.isfile(item):
                            # 添加文件
                            rel_path = os.path.basename(item)
                            zipf.write(item, arcname=f"{zip_name}/{rel_path}")
                            processed_items += 1
                            progress = 10 + (processed_items / total_items * 30)
                            self.update_compress_progress(progress)
                            self.update_compress_status(f"正在打包: {os.path.basename(item)}")
                            self.append_log(f"添加文件: {item}")
                        elif os.path.isdir(item):
                            # 添加文件夹
                            for root_dir, dirs, files in os.walk(item):
                                for file in files:
                                    file_path = os.path.join(root_dir, file)
                                    rel_path = os.path.relpath(file_path, os.path.dirname(item))
                                    zipf.write(file_path, arcname=f"{zip_name}/{os.path.basename(item)}/{rel_path}")
                                    processed_items += 1
                                    progress = 10 + (processed_items / total_items * 30)
                                    self.update_compress_progress(progress)
                                    self.update_compress_status(f"正在打包: {os.path.basename(file_path)}")
                                    self.append_log(f"添加文件: {file_path}")

                self.update_compress_progress(40)
                self.append_log(f"ZIP文件创建完成: {zip_path}")

                # 复制图片到临时目录
                image_name = os.path.basename(self.image_path)
                temp_image_path = os.path.join(temp_dir, image_name)
                shutil.copy2(self.image_path, temp_image_path)
                self.append_log(f"复制图片到临时目录: {temp_image_path}")

                # 创建解压程序脚本
                self.update_compress_status("创建解压程序...")
                self.update_compress_progress(50)
                self.append_log("创建解压程序脚本...")

                extractor_script = self.create_extractor_script(temp_dir, zip_name, image_name)
                self.append_log(f"解压程序脚本创建完成: {extractor_script}")

                # 使用pyinstaller打包解压程序
                self.update_compress_status("正在生成EXE文件...")
                self.update_compress_progress(60)
                self.append_log("开始生成EXE文件...")

                # 构建pyinstaller命令
                sep = ';' if sys.platform.startswith('win') else ':'
                cmd = [
                    sys.executable,  # 使用当前Python解释器
                    "-m", "PyInstaller",  # 确保使用正确的PyInstaller模块
                    "--onefile",
                    f"--add-data={zip_path}{sep}.",
                    f"--add-data={temp_image_path}{sep}.",
                    f"--distpath={os.path.dirname(output_path)}",
                    f"--name={os.path.basename(output_path).replace('.exe', '')}",
                    "--noconsole",
                    extractor_script
                ]

                # 如果是调试模式，添加详细输出参数
                if self.debug_mode.get():
                    cmd.insert(2, "--debug=all")

                self.append_log(f"执行PyInstaller命令: {' '.join(cmd)}")

                # 执行pyinstaller命令
                try:
                    # 使用Popen实时获取输出
                    process = subprocess.Popen(
                        cmd,
                        cwd=temp_dir,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,  # 合并stdout和stderr
                        text=True,
                        encoding="utf-8",
                        bufsize=1
                    )

                    # 实时读取输出并添加到日志
                    while process.poll() is None:
                        line = process.stdout.readline()
                        if line:
                            self.append_log(line.strip())
                            # 更新进度（模拟，因为无法直接获取PyInstaller的进度）
                            current_progress = self.compress_progress_var.get()
                            if current_progress < 90:
                                self.update_compress_progress(current_progress + 0.01)

                    # 读取剩余输出
                    remaining_output = process.stdout.read()
                    if remaining_output:
                        self.append_log(remaining_output.strip())

                    self.update_compress_progress(90)

                    if process.returncode != 0:
                        self.append_log(f"PyInstaller执行失败，返回代码: {process.returncode}")
                        self.update_compress_status(f"生成EXE失败，返回代码: {process.returncode}", is_error=True)
                        messagebox.showerror(
                            "错误",
                            f"生成EXE时出错，返回代码: {process.returncode}\n"
                            f"请查看'运行日志'标签页获取详细信息"
                        )
                        return
                except Exception as e:
                    self.append_log(f"执行PyInstaller时出错: {str(e)}")
                    self.append_log(traceback.format_exc())
                    self.update_compress_status(f"执行PyInstaller失败: {str(e)}", is_error=True)
                    messagebox.showerror("错误", f"执行PyInstaller时出错:\n{str(e)}")
                    return

                # 检查输出文件是否存在
                if not os.path.exists(output_path):
                    self.append_log(f"生成的EXE文件未找到: {output_path}")
                    messagebox.showerror("错误", "生成EXE失败，文件未找到")
                    return

                self.append_log(f"EXE文件生成成功: {output_path}")
                self.update_compress_progress(100)
                self.update_compress_status("压缩完成!")
                messagebox.showinfo("成功", f"自解压EXE已生成:\n{output_path}\n\n可双击该文件直接解压")

        except Exception as e:
            self.append_log(f"压缩过程出错: {str(e)}")
            self.append_log(traceback.format_exc())
            self.update_compress_status(f"压缩失败: {str(e)}", is_error=True)
            messagebox.showerror("错误", f"压缩过程中发生错误:\n{str(e)}\n请查看'运行日志'标签页获取详细信息")

    def count_items(self, items):
        """计算要压缩的项目总数（文件数量）"""
        count = 0
        for item in items:
            if os.path.isfile(item):
                count += 1
            elif os.path.isdir(item):
                for root_dir, dirs, files in os.walk(item):
                    count += len(files)
        return count

    def create_extractor_script(self, temp_dir, zip_name, image_name):
        """创建包含自启动解压逻辑的脚本"""
        extractor_code = f"""
import os
import sys
import zipfile
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import tempfile
import shutil
import time

class ExtractorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("正在解压...")
        self.root.geometry("600x400")
        self.root.resizable(False, False)

        # 设置中文字体
        self.setup_fonts()

        # 使用用户文档目录作为解压路径（避免权限问题）
        self.extract_path = os.path.join(os.path.expanduser('~'), "Documents", "extracted_files")

        # 创建界面
        self.create_widgets()

        # 开始解压
        self.start_extraction()

    def setup_fonts(self):
        default_font = ('SimHei', 10)
        self.root.option_add("*Font", default_font)

    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 显示图片
        image_frame = ttk.Frame(main_frame)
        image_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        try:
            # 获取pyinstaller打包后的资源路径
            if getattr(sys, 'frozen', False):
                base_path = sys._MEIPASS
            else:
                base_path = os.path.abspath('.')
            image_path = os.path.join(base_path, "{image_name}")
            image = Image.open(image_path)
            # 调整图片大小适应窗口
            image.thumbnail((560, 300))
            photo = ImageTk.PhotoImage(image)

            self.image_label = ttk.Label(image_frame, image=photo)
            self.image_label.image = photo  # 保持引用
            self.image_label.pack()
        except Exception as e:
            ttk.Label(
                image_frame, 
                text=f"无法加载图片: {{str(e)}}\\n将使用默认界面",
                justify=tk.CENTER
            ).pack(expand=True)

        # 进度条
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, pady=5)

        # 状态标签
        self.status_label = ttk.Label(main_frame, text="准备解压...")
        self.status_label.pack(pady=5)

        # 解压路径显示
        path_frame = ttk.Frame(main_frame)
        path_frame.pack(fill=tk.X, pady=5)

        ttk.Label(path_frame, text="解压到:").pack(side=tk.LEFT)
        self.path_label = ttk.Label(path_frame, text=self.extract_path)
        self.path_label.pack(side=tk.LEFT, padx=5)

        # 取消按钮
        cancel_btn = ttk.Button(main_frame, text="取消", command=self.cancel_extraction)
        cancel_btn.pack(pady=10)

        self.cancelled = False

    def cancel_extraction(self):
        self.cancelled = True
        self.status_label.config(text="正在取消...")

    def update_progress(self, value):
        self.progress_var.set(value)
        self.root.update_idletasks()

    def update_status(self, text):
        self.status_label.config(text=text)
        self.root.update_idletasks()

    def start_extraction(self):
        try:
            # 创建解压目录
            os.makedirs(self.extract_path, exist_ok=True)

            # 获取打包的ZIP文件路径
            if getattr(sys, 'frozen', False):
                base_path = sys._MEIPASS
                zip_path = os.path.join(base_path, "{zip_name}.zip")
            else:
                zip_path = "{zip_name}.zip"

            # 检查ZIP文件是否存在
            if not os.path.exists(zip_path):
                raise Exception(f"未找到压缩数据: {{zip_path}}")

            # 从ZIP文件中解压
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # 获取所有文件列表
                file_list = zip_ref.namelist()

                # 过滤出属于我们打包的文件
                target_files = [f for f in file_list if f.startswith("{zip_name}/")]

                if not target_files:
                    raise Exception("未找到可解压的文件")

                # 解压文件
                total_files = len(target_files)
                for i, file in enumerate(target_files):
                    if self.cancelled:
                        self.update_status("解压已取消")
                        # 清理可能的部分文件
                        if os.path.exists(self.extract_path):
                            shutil.rmtree(self.extract_path, ignore_errors=True)
                        messagebox.showinfo("取消", "解压已被取消")
                        self.root.destroy()
                        return

                    # 更新进度
                    progress = (i + 1) / total_files * 100
                    self.update_progress(progress)
                    self.update_status(f"正在解压: {{os.path.basename(file)}}")

                    # 解压文件
                    zip_ref.extract(file, tempfile.gettempdir())

                    # 移动到目标目录
                    temp_path = os.path.join(tempfile.gettempdir(), file)
                    target_path = os.path.join(self.extract_path, os.path.relpath(file, "{zip_name}/"))

                    # 确保目标目录存在
                    os.makedirs(os.path.dirname(target_path), exist_ok=True)

                    # 移动文件
                    if os.path.exists(target_path):
                        os.remove(target_path)
                    shutil.move(temp_path, target_path)
                    time.sleep(0.01)  # 稍微延迟，让用户能看到进度

            self.update_status("解压完成!")
            messagebox.showinfo("成功", f"文件已成功解压到:\\n{self.extract_path}")
            self.root.destroy()

            # 打开解压目录
            try:
                os.startfile(self.extract_path)
            except:
                pass  # 忽略打开目录失败的情况

        except Exception as e:
            self.update_status(f"解压失败: {{str(e)}}")

if __name__ == "__main__":
    # 实现双击自动解压逻辑
    if len(sys.argv) > 1 and sys.argv[1] == "--extract":
        # 命令行模式（供外部调用）
        extract_path = os.path.join(os.path.expanduser('~'), "Documents", "extracted_files")
        os.makedirs(extract_path, exist_ok=True)

        try:
            # 获取打包的ZIP文件路径
            if getattr(sys, 'frozen', False):
                base_path = sys._MEIPASS
                zip_path = os.path.join(base_path, "{zip_name}.zip")
            else:
                zip_path = "{zip_name}.zip"

            if not os.path.exists(zip_path):
                raise Exception(f"未找到压缩数据: {{zip_path}}")

            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                file_list = zip_ref.namelist()
                target_files = [f for f in file_list if f.startswith("{zip_name}/")]

                if not target_files:
                    raise Exception("未找到可解压的文件")

                for file in target_files:
                    temp_path = zip_ref.extract(file, tempfile.gettempdir())
                    target_path = os.path.join(extract_path, os.path.relpath(file, "{zip_name}/"))
                    os.makedirs(os.path.dirname(target_path), exist_ok=True)

                    if os.path.exists(target_path):
                        if os.path.isfile(target_path):
                            os.remove(target_path)
                        else:
                            shutil.rmtree(target_path)
                    shutil.move(temp_path, target_path)

            messagebox.showinfo("成功", f"文件已解压到:\\n{self.extract_path}")
            try:
                os.startfile(extract_path)
            except:
                pass
        except Exception as e:
            messagebox.showerror("错误", f"解压失败: {{str(e)}}")
    else:
        # 图形界面模式
        root = tk.Tk()
        app = ExtractorApp(root)
        root.mainloop()
        """

        # 将解压程序代码写入临时文件
        extractor_script_path = os.path.join(temp_dir, "extractor.py")
        with open(extractor_script_path, "w", encoding="utf-8") as f:
            f.write(extractor_code)

        return extractor_script_path

    # 解压相关方法
    def start_decompression(self):
        if not self.extract_file or not os.path.exists(self.extract_file):
            messagebox.showwarning("警告", "请选择有效的EXE文件")
            return

        output_dir = self.decompress_output_entry.get()
        if not output_dir:
            messagebox.showwarning("警告", "请选择解压目录")
            return

        # 创建解压目录
        try:
            os.makedirs(output_dir, exist_ok=True)
        except Exception as e:
            messagebox.showerror("错误", f"无法创建解压目录: {str(e)}")
            return

        # 验证文件是否有效
        if not self.is_valid_zip(self.extract_file):
            messagebox.showerror("错误", "所选文件不是有效的自解压文件，无法解压")
            return

        # 启动解压窗口
        self.create_extraction_window(output_dir)

    def create_extraction_window(self, extract_path):
        # 创建新窗口显示解压过程
        extract_window = tk.Toplevel(self.root)
        extract_window.title("正在解压...")
        extract_window.geometry("600x400")
        extract_window.resizable(False, False)
        extract_window.transient(self.root)  # 设置为主窗口的子窗口
        extract_window.grab_set()  # 模态窗口

        # 设置中文字体
        default_font = ('SimHei', 10)
        extract_window.option_add("*Font", default_font)

        main_frame = ttk.Frame(extract_window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 尝试显示图片（如果存在）
        image_frame = ttk.Frame(main_frame)
        image_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        image_loaded = False
        try:
            # 对于自解压EXE，先找到真正的ZIP数据
            if getattr(sys, 'frozen', False):
                # 从资源目录读取
                base_path = sys._MEIPASS
                with zipfile.ZipFile(os.path.join(base_path, "packed_files.zip"), 'r') as zip_ref:
                    image_files = [f for f in zip_ref.namelist() if
                                   f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif'))]
            else:
                # 直接读取EXE文件
                with zipfile.ZipFile(self.extract_file, 'r') as zip_ref:
                    image_files = [f for f in zip_ref.namelist() if
                                   f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif'))]

            if image_files:
                # 提取第一张图片
                temp_image_path = os.path.join(tempfile.gettempdir(), os.path.basename(image_files[0]))
                with open(temp_image_path, 'wb') as f:
                    if getattr(sys, 'frozen', False):
                        with zipfile.ZipFile(os.path.join(base_path, "packed_files.zip"), 'r') as zip_ref:
                            f.write(zip_ref.read(image_files[0]))
                    else:
                        with zipfile.ZipFile(self.extract_file, 'r') as zip_ref:
                            f.write(zip_ref.read(image_files[0]))

                # 显示图片
                image = Image.open(temp_image_path)
                image.thumbnail((560, 300))
                photo = ImageTk.PhotoImage(image)

                image_label = ttk.Label(image_frame, image=photo)
                image_label.image = photo  # 保持引用
                image_label.pack()
                image_loaded = True
        except Exception as e:
            print(f"无法加载图片: {e}")

        if not image_loaded:
            ttk.Label(
                image_frame,
                text="未找到预览图片或无法加载图片",
                justify=tk.CENTER
            ).pack(expand=True)

        # 进度条
        progress_var = tk.DoubleVar()
        progress_bar = ttk.Progressbar(main_frame, variable=progress_var, maximum=100)
        progress_bar.pack(fill=tk.X, pady=5)

        # 状态标签
        status_label = ttk.Label(main_frame, text="准备解压...")
        status_label.pack(pady=5)

        # 解压路径显示
        path_frame = ttk.Frame(main_frame)
        path_frame.pack(fill=tk.X, pady=5)

        ttk.Label(path_frame, text="解压到:").pack(side=tk.LEFT)
        path_label = ttk.Label(path_frame, text=extract_path)
        path_label.pack(side=tk.LEFT, padx=5)

        # 取消按钮
        cancelled = [False]  # 使用列表来允许内部函数修改

        def cancel_extraction():
            cancelled[0] = True
            status_label.config(text="正在取消...")

        cancel_btn = ttk.Button(main_frame, text="取消", command=cancel_extraction)
        cancel_btn.pack(pady=10)

        # 开始解压
        extract_window.after(100, self.perform_decompression, extract_path, progress_var, status_label, extract_window,
                             cancelled)

    def perform_decompression(self, extract_path, progress_var, status_label, window, cancelled):
        try:
            # 获取ZIP文件路径
            if getattr(sys, 'frozen', False):
                # 从资源目录读取
                base_path = sys._MEIPASS
                zip_path = os.path.join(base_path, "packed_files.zip")
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    file_list = zip_ref.namelist()
            else:
                # 直接读取EXE文件
                with zipfile.ZipFile(self.extract_file, 'r') as zip_ref:
                    file_list = zip_ref.namelist()

            # 过滤出属于我们打包的文件
            zip_name = "packed_files"
            target_files = [f for f in file_list if f.startswith(f"{zip_name}/")]

            if not target_files:
                raise Exception("未找到可解压的文件，可能不是本工具生成的自解压文件")

            # 解压文件
            total_files = len(target_files)
            for i, file in enumerate(target_files):
                if cancelled[0]:
                    status_label.config(text="解压已取消")
                    # 清理可能的部分文件
                    if os.path.exists(extract_path):
                        shutil.rmtree(extract_path, ignore_errors=True)
                    messagebox.showinfo("取消", "解压已被取消")
                    window.destroy()
                    return

                # 更新进度
                progress = (i + 1) / total_files * 100
                progress_var.set(progress)
                status_label.config(text=f"正在解压: {os.path.basename(file)}")
                window.update_idletasks()

                # 解压文件到临时目录
                if getattr(sys, 'frozen', False):
                    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                        temp_file_path = zip_ref.extract(file, tempfile.gettempdir())
                else:
                    with zipfile.ZipFile(self.extract_file, 'r') as zip_ref:
                        temp_file_path = zip_ref.extract(file, tempfile.gettempdir())

                # 构建目标路径
                relative_path = os.path.relpath(file, f"{zip_name}/")
                target_path = os.path.join(extract_path, relative_path)

                # 确保目标目录存在
                os.makedirs(os.path.dirname(target_path), exist_ok=True)

                # 移动文件
                if os.path.exists(target_path):
                    if os.path.isfile(target_path):
                        os.remove(target_path)
                    else:
                        shutil.rmtree(target_path)
                shutil.move(temp_file_path, target_path)

            progress_var.set(100)
            status_label.config(text="解压完成!")
            window.update_idletasks()
            messagebox.showinfo("成功", f"文件已成功解压到:\n{extract_path}")
            window.destroy()

            # 打开解压目录
            try:
                if sys.platform.startswith('win'):
                    os.startfile(extract_path)
                elif sys.platform.startswith('darwin'):  # macOS
                    subprocess.run(['open', extract_path])
                else:  # Linux
                    subprocess.run(['xdg-open', extract_path])
            except Exception as e:
                print(f"无法打开目录: {e}")

        except Exception as e:
            error_msg = str(e)
            # 更友好的错误提示
            if "not a zip file" in error_msg.lower():
                error_msg = "所选文件不是有效的压缩文件，无法解压。请确保选择的是由本工具生成的自解压EXE文件。"
            status_label.config(text=f"解压失败: {error_msg}", foreground="red")
            messagebox.showerror("错误", f"解压过程中发生错误:\n{error_msg}")
            window.destroy()

    def is_valid_zip(self, file_path):
        """验证文件是否为有效的ZIP或自解压EXE格式"""
        try:
            if not os.path.exists(file_path) or not os.path.isfile(file_path):
                return False

            # 对于自解压EXE，检查其是否包含我们打包的ZIP文件
            if getattr(sys, 'frozen', False):
                # 运行时检查
                return True
            else:
                # 开发环境检查
                with open(file_path, 'rb') as f:
                    content = f.read(1024 * 10)  # 读取前10KB内容查找ZIP签名
                    zip_signatures = [b'PK\x03\x04', b'PK\x05\x06', b'PK\x07\x08']
                    return any(sig in content for sig in zip_signatures)
        except Exception as e:
            print(f"验证文件时出错: {e}")
            return False


if __name__ == "__main__":
    # 补全依赖检查
    required_packages = ['pyinstaller']
    missing_packages = []

    for package in required_packages:
        try:
            __import__(package if package != 'pyinstaller' else 'PyInstaller')
        except ImportError:
            missing_packages.append(package)

    if missing_packages:
        print(f"缺少必要的库，请先安装: {', '.join(missing_packages)}")
        print("可以使用以下命令安装:")
        print(f"pip install {' '.join(missing_packages)}")
        sys.exit(1)

    # 检查是否以管理员权限运行（Windows）
    if sys.platform.startswith('win'):
        try:
            import ctypes

            if not ctypes.windll.shell32.IsUserAnAdmin():
                print("警告: 建议以管理员权限运行，否则可能导致生成EXE失败")
        except:
            pass

    root = tk.Tk()
    app = FileCompressorDecompressor(root)
    root.mainloop()
