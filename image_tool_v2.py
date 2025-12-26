import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from PIL import Image

# --- 核心处理逻辑 ---
def resize_image_content(img, max_edge):
    """辅助函数：等比缩放图片"""
    w, h = img.size
    long_edge = max(w, h)
    if long_edge > max_edge:
        scale = max_edge / float(long_edge)
        new_w = int(w * scale)
        new_h = int(h * scale)
        # 使用 LANCZOS 算法保证缩放质量
        return img.resize((new_w, new_h), Image.LANCZOS), f"{w}x{h}->{new_w}x{new_h}"
    else:
        return img, "原尺寸"

def process_images(input_folder, output_folder, max_size, quality, delete_original, make_thumb, thumb_size, log_func):
    supported_formats = ('.jpg', '.jpeg', '.png', '.bmp', '.tiff')
    
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
        
        # 主图文件名
        output_name_main = os.path.splitext(filename)[0] + ".webp"
        output_path_main = os.path.join(output_folder, output_name_main)

        try:
            # 打开原图
            original_img = Image.open(input_path)
            
            # 处理颜色模式 (处理透明背景)
            if original_img.mode in ("RGBA", "LA"):
                original_img = original_img.convert("RGBA")
            else:
                original_img = original_img.convert("RGB")

            # --- 1. 生成主图 (大图) ---
            img_main, resize_info = resize_image_content(original_img, max_size)
            img_main.save(
                output_path_main,
                format="WEBP",
                quality=quality,
                method=6,
                lossless=False,
                optimize=True
            )
            log_msg = f"[{index+1}/{total}] ✅ 主图: {filename} ({resize_info})"

            # --- 2. 生成缩略图 (小图) ---
            if make_thumb:
                # 缩略图文件名 (加 _thumb 后缀)
                output_name_thumb = os.path.splitext(filename)[0] + "_thumb.webp"
                output_path_thumb = os.path.join(output_folder, output_name_thumb)
                
                # 基于原图进行缩放 (保证清晰度)
                img_thumb, thumb_info = resize_image_content(original_img, thumb_size)
                img_thumb.save(
                    output_path_thumb,
                    format="WEBP",
                    quality=quality, # 缩略图通常也可以用同样的质量，或者更低
                    method=6
                )
                log_msg += f" | ➕ 缩略图 ({thumb_info})"

            log_func(log_msg)

            # --- 3. 删除原文件 ---
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
        self.root.title("图片转WebP + 缩略图生成器 v2.0")
        self.root.geometry("520x650") # 窗口加大一点

        # 1. 选择输入文件夹
        tk.Label(root, text="第一步：选择图片所在的文件夹", font=("Arial", 10, "bold")).pack(pady=(10, 5))
        self.input_entry = tk.Entry(root, width=50)
        self.input_entry.pack(pady=5)
        tk.Button(root, text="📂 浏览文件夹...", command=self.select_input).pack()

        # 2. 主图设置
        tk.Label(root, text="第二步：主图设置", font=("Arial", 10, "bold")).pack(pady=(20, 5))
        frame_main = tk.Frame(root)
        frame_main.pack(pady=5)

        tk.Label(frame_main, text="最大边长(px):").grid(row=0, column=0, padx=5)
        self.size_entry = tk.Entry(frame_main, width=8)
        self.size_entry.insert(0, "1600")
        self.size_entry.grid(row=0, column=1, padx=5)

        tk.Label(frame_main, text="画质(1-100):").grid(row=0, column=2, padx=5)
        self.quality_entry = tk.Entry(frame_main, width=8)
        self.quality_entry.insert(0, "75")
        self.quality_entry.grid(row=0, column=3, padx=5)

        # 3. 缩略图设置 (新增区域)
        tk.Label(root, text="第三步：缩略图设置 (可选)", font=("Arial", 10, "bold")).pack(pady=(20, 5))
        frame_thumb = tk.Frame(root)
        frame_thumb.pack(pady=5)

        self.thumb_var = tk.BooleanVar()
        self.thumb_var.set(False) # 默认不开启
        tk.Checkbutton(frame_thumb, text="同时生成缩略图", variable=self.thumb_var, command=self.toggle_thumb_entry).grid(row=0, column=0, padx=5)

        tk.Label(frame_thumb, text="缩略图尺寸(px):").grid(row=0, column=1, padx=5)
        self.thumb_size_entry = tk.Entry(frame_thumb, width=8, state='disabled') # 默认禁用
        self.thumb_size_entry.insert(0, "300")
        self.thumb_size_entry.grid(row=0, column=2, padx=5)

        # 4. 其他选项
        tk.Label(root, text="第四步：其他", font=("Arial", 10, "bold")).pack(pady=(20, 5))
        self.del_var = tk.BooleanVar()
        tk.Checkbutton(root, text="处理完成后删除原图 (慎重勾选!)", variable=self.del_var, fg="red").pack(pady=5)

        # 5. 开始按钮
        tk.Button(root, text="🚀 开始转换", command=self.start_thread, bg="#2196F3", fg="white", font=("Arial", 12, "bold"), height=2, width=20).pack(pady=20)

        # 6. 日志区域
        self.log_text = scrolledtext.ScrolledText(root, width=65, height=12, state='disabled', font=("Consolas", 9))
        self.log_text.pack(padx=10, pady=(0, 10))

    def toggle_thumb_entry(self):
        """根据勾选状态启用/禁用输入框"""
        if self.thumb_var.get():
            self.thumb_size_entry.config(state='normal')
        else:
            self.thumb_size_entry.config(state='disabled')

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
            
            make_thumb = self.thumb_var.get()
            thumb_size = 300 # 默认值
            if make_thumb:
                thumb_size = int(self.thumb_size_entry.get())

        except ValueError:
            messagebox.showerror("错误", "尺寸和质量必须是数字！")
            return

        output_folder = os.path.join(input_folder, "output_webp")
        delete_original = self.del_var.get()

        self.log("🚀 正在启动...")
        
        threading.Thread(target=process_images, args=(
            input_folder, output_folder, max_size, quality, delete_original, 
            make_thumb, thumb_size, self.log
        )).start()

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageToolApp(root)
    root.mainloop()