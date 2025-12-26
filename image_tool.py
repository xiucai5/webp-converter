import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from PIL import Image

# --- 核心处理逻辑 (和你原来的代码基本一样) ---
def process_images(input_folder, output_folder, max_size, quality, delete_original, log_func):
    supported_formats = ('.jpg', '.jpeg', '.png', '.bmp', '.tiff')
    
    # 确保输出目录存在
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    files = [f for f in os.listdir(input_folder) if f.lower().endswith(supported_formats)]
    total = len(files)
    
    if total == 0:
        log_func("❌ 文件夹里没有找到支持的图片！")
        return

    log_func(f"📂 找到 {total} 张图片，开始处理...\n")

    for index, filename in enumerate(files):
        input_path = os.path.join(input_folder, filename)
        output_name = os.path.splitext(filename)[0] + ".webp"
        output_path = os.path.join(output_folder, output_name)

        try:
            img = Image.open(input_path)

            # 1. 等比缩放
            w, h = img.size
            long_edge = max(w, h)
            if long_edge > max_size:
                scale = max_size / float(long_edge)
                new_w = int(w * scale)
                new_h = int(h * scale)
                img = img.resize((new_w, new_h), Image.LANCZOS)
                resize_info = f"{w}x{h} -> {new_w}x{new_h}"
            else:
                resize_info = "保持原大"

            # 2. 颜色模式转换
            if img.mode in ("RGBA", "LA"):
                img = img.convert("RGBA")
            else:
                img = img.convert("RGB")

            # 3. 保存 WebP
            img.save(
                output_path,
                format="WEBP",
                quality=quality,
                method=6,
                lossless=False,
                optimize=True
            )

            log_func(f"[{index+1}/{total}] ✅ {filename} ({resize_info})")

            # 4. 删除原文件逻辑
            if delete_original:
                os.remove(input_path)
                log_func(f"   🗑 已删除原文件: {filename}")

        except Exception as e:
            log_func(f"❌ 失败: {filename}, 错误: {e}")

    log_func("\n🎉 全部处理完成！")
    messagebox.showinfo("完成", "所有图片处理完毕！")

# --- 图形界面逻辑 ---
class ImageToolApp:
    def __init__(self, root):
        self.root = root
        self.root.title("图片转WebP压缩工具")
        self.root.geometry("500x550")

        # 1. 选择输入文件夹
        tk.Label(root, text="第一步：选择图片所在的文件夹").pack(pady=(10, 0))
        self.input_entry = tk.Entry(root, width=50)
        self.input_entry.pack(pady=5)
        tk.Button(root, text="浏览...", command=self.select_input).pack()

        # 2. 设置参数
        tk.Label(root, text="第二步：设置参数").pack(pady=(15, 0))
        
        frame_params = tk.Frame(root)
        frame_params.pack(pady=5)

        tk.Label(frame_params, text="最大边长(px):").grid(row=0, column=0, padx=5)
        self.size_entry = tk.Entry(frame_params, width=10)
        self.size_entry.insert(0, "1600")
        self.size_entry.grid(row=0, column=1, padx=5)

        tk.Label(frame_params, text="WebP质量(1-100):").grid(row=0, column=2, padx=5)
        self.quality_entry = tk.Entry(frame_params, width=10)
        self.quality_entry.insert(0, "75")
        self.quality_entry.grid(row=0, column=3, padx=5)

        # 删除原文件选项
        self.del_var = tk.BooleanVar()
        tk.Checkbutton(root, text="处理后删除原图 (慎选!)", variable=self.del_var, fg="red").pack(pady=5)

        # 3. 开始按钮
        tk.Button(root, text="🚀 开始转换", command=self.start_thread, bg="#4CAF50", fg="white", font=("Arial", 12, "bold"), height=2, width=20).pack(pady=15)

        # 4. 日志区域
        tk.Label(root, text="处理日志:").pack(anchor="w", padx=20)
        self.log_text = scrolledtext.ScrolledText(root, width=60, height=15, state='disabled')
        self.log_text.pack(padx=20, pady=(0, 20))

    def select_input(self):
        path = filedialog.askdirectory()
        if path:
            self.input_entry.delete(0, tk.END)
            self.input_entry.insert(0, path)

    def log(self, message):
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')

    def start_thread(self):
        input_folder = self.input_entry.get()
        if not input_folder:
            messagebox.showwarning("提示", "请先选择文件夹！")
            return
        
        try:
            max_size = int(self.size_entry.get())
            quality = int(self.quality_entry.get())
        except ValueError:
            messagebox.showerror("错误", "尺寸和质量必须是数字！")
            return

        # 自动创建输出文件夹 (在原文件夹下的 output_webp 目录)
        output_folder = os.path.join(input_folder, "output_webp")
        delete_original = self.del_var.get()

        # 禁用按钮防止重复点击
        self.log("🚀 正在启动...")
        
        # 在新线程运行，防止界面卡死
        threading.Thread(target=process_images, args=(input_folder, output_folder, max_size, quality, delete_original, self.log)).start()

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageToolApp(root)
    root.mainloop()