import subprocess
import sys
import os
import time
import threading
import datetime
import tkinter as tk
from tkinter import messagebox, Toplevel, Canvas, font
import platform  # Thêm thư viện để nhận diện hệ điều hành

# --- 1. TỰ ĐỘNG CÀI THƯ VIỆN ---
def auto_install(package_name, import_name=None):
    if not import_name: import_name = package_name
    try:
        __import__(import_name)
    except ImportError:
        try:
            print(f"⏳ Đang cài đặt thư viện: {package_name}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        except:
            print(f"❌ Không thể cài tự động {package_name}. Hãy cài thủ công.")

# Danh sách thư viện cần thiết
auto_install("Pillow", "PIL")
auto_install("google-generativeai", "google.generativeai")
auto_install("keyboard")
auto_install("deep_translator")
auto_install("pytesseract")

# Import sau khi đã đảm bảo cài đặt
import google.generativeai as genai
import keyboard
from PIL import Image, ImageTk, ImageGrab
from deep_translator import GoogleTranslator
import pytesseract

# --- 2. HÀM HỖ TRỢ FILE HỆ THỐNG ---
def resource_path(relative_path):
    """ Lấy đường dẫn tài nguyên (ảnh, icon) dùng cho cả Code và EXE """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

CONFIG_FILE = "api_key.txt"

def load_saved_keys():
    """ Đọc key từ file txt """
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return f.read().strip()
        except: pass
    return ""

def save_keys_to_file(content):
    """ Lưu key vào file txt """
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            f.write(content)
    except: pass

# --- 3. CẤU HÌNH GIAO DIỆN ---
APP_TITLE = "Vision Translator (AI + OCR)"
APP_WIDTH = 720
APP_HEIGHT = 680
APP_SIZE = f"{APP_WIDTH}x{APP_HEIGHT}"
COLOR_BG = "#1E1E1E" 
COLOR_BTN = "#4DA6FF"
COLOR_TEXT = "#CCCCCC"
MODEL_NAME = 'models/gemini-flash-latest'

# --- 4. TÌM TESSERACT (Hỗ trợ cả Windows và Mac) ---
def find_tesseract():
    system_os = platform.system()
    
    if system_os == "Windows":
        possible_paths = [
            r"D:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            os.path.join(os.getenv('LOCALAPPDATA'), r"Tesseract-OCR\tesseract.exe")
        ]
        for path in possible_paths:
            if os.path.exists(path): return path
            
    elif system_os == "Darwin": # MacOS
        # Các đường dẫn phổ biến trên Mac (Homebrew)
        possible_paths = [
            "/usr/local/bin/tesseract",
            "/opt/homebrew/bin/tesseract"
        ]
        for path in possible_paths:
            if os.path.exists(path): return path
        return "tesseract" # Thử gọi lệnh trực tiếp
        
    return None

tess_path = find_tesseract()
if tess_path: 
    pytesseract.pytesseract.tesseract_cmd = tess_path

# --- 5. HÀM GỌI AI ---
def call_gemini_single_key(api_key, image_path):
    genai.configure(api_key=api_key)
    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    ]
    model = genai.GenerativeModel(MODEL_NAME, safety_settings=safety_settings)
    
    prompt = """
    Bạn là chuyên gia dịch thuật.
    Nhiệm vụ: Dịch văn bản trong ảnh sang Tiếng Việt.
    Yêu cầu ĐỊNH DẠNG:
    1. Bảng (Table) -> Vẽ lại bằng Markdown.
    2. Code -> Giữ nguyên block code.
    3. Tiêu đề -> Viết IN HOA hoặc **In Đậm**.
    Chỉ trả về kết quả dịch.
    """
    
    with Image.open(image_path) as img:
        response = model.generate_content([prompt, img])
        return response.text

# --- 6. HÀM XỬ LÝ CHÍNH ---
def smart_process_rotation(keys_input, image_path):
    save_keys_to_file(keys_input) # Lưu key lại

    api_keys = [k.strip() for k in keys_input.split(',') if k.strip()]
    if not api_keys: return "❌ Lỗi: Bạn chưa nhập API Key nào!"

    # 1. Thử dùng AI trước
    for index, key in enumerate(api_keys):
        try:
            print(f"🔄 Đang thử Key {index + 1}...")
            result = call_gemini_single_key(key, image_path)
            if result:
                return f"✨ KẾT QUẢ TỪ AI (Key {index+1}):\n{'-'*40}\n{result}"
        except Exception as e:
            print(f"⚠️ Key {index + 1} lỗi: {e}")
            continue

    # 2. Nếu AI lỗi hết thì dùng Google Dịch truyền thống
    return fallback_google_translate(image_path)

def fallback_google_translate(image_path):
    try:
        # Kiểm tra Tesseract có tồn tại không
        if not tess_path or (platform.system() == "Windows" and not os.path.exists(tess_path)):
             return "⚠️ LỖI: Key AI hỏng và máy tính chưa cài Tesseract OCR!\nHãy cài Tesseract để dùng chế độ Offline."
             
        with Image.open(image_path) as img:
            raw_text = pytesseract.image_to_string(img, lang='eng')
        
        if not raw_text.strip(): return "⚠️ Ảnh không có chữ hoặc Tesseract không đọc được."
        
        translated = GoogleTranslator(source='auto', target='vi').translate(raw_text)
        return f"⚠️ CHẾ ĐỘ DỰ PHÒNG (GOOGLE DỊCH):\n{'-'*40}\n\n{translated}"
    except Exception as e:
        return f"❌ Lỗi hệ thống: {str(e)}"

# --- 7. CÔNG CỤ CHỤP ---
class SnippingTool:
    def __init__(self, master, callback):
        self.master = master; self.callback = callback
        self.start_x = None; self.start_y = None; self.rect = None
        
        self.top = Toplevel(master)
        self.top.attributes("-fullscreen", True)
        self.top.attributes("-alpha", 0.3)
        self.top.attributes("-topmost", True)
        self.top.configure(bg="black", cursor="cross")
        
        self.canvas = Canvas(self.top, bg="black", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_move)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<Escape>", self.on_cancel)
        
        # Ẩn cửa sổ chính đi
        self.master.withdraw()

    def on_press(self, event):
        self.start_x = event.x
        self.start_y = event.y
        self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, 1, 1, outline=COLOR_BTN, width=2)

    def on_move(self, event):
        self.canvas.coords(self.rect, self.start_x, self.start_y, event.x, event.y)

    def on_cancel(self, event=None):
        self.top.destroy()
        self.master.deiconify() # Hiện lại cửa sổ chính

    def on_release(self, event):
        x1, y1 = min(self.start_x, event.x), min(self.start_y, event.y)
        x2, y2 = max(self.start_x, event.x), max(self.start_y, event.y)
        
        self.top.destroy()
        
        if x2 - x1 < 10 or y2 - y1 < 10: # Nếu vùng chọn quá nhỏ thì hủy
            self.master.deiconify()
            return
            
        self.master.after(100, lambda: self.capture_and_process(x1, y1, x2, y2))

    def capture_and_process(self, x1, y1, x2, y2):
        # Tạo tên file tạm
        temp_file = f"snap_{datetime.datetime.now().strftime('%H%M%S')}.png"
        try:
            # Chụp màn hình vùng đã chọn
            img = ImageGrab.grab(bbox=(x1, y1, x2, y2))
            img.save(temp_file)
            self.callback(temp_file)
        except Exception as e:
            self.master.deiconify()
            messagebox.showerror("Lỗi", str(e))

# --- 8. GIAO DIỆN CHÍNH ---
class App:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry(APP_SIZE)
        self.root.configure(bg=COLOR_BG)
        # self.root.resizable(False, False) # Cho phép chỉnh kích thước nếu cần
        
        # Đăng ký phím tắt F2
        try: keyboard.add_hotkey('F2', self.start_snip)
        except: pass

        # HEADER
        header_height = 80
        self.canvas_header = tk.Canvas(root, height=header_height, bg=COLOR_BG, highlightthickness=0)
        self.canvas_header.pack(fill="x", side="top", pady=10)
        
        # Nếu có ảnh nền thì load, không thì thôi
        try:
            img_path = resource_path("header_bg.png")
            if os.path.exists(img_path):
                bg_img_pil = Image.open(img_path)
                bg_img_pil = bg_img_pil.resize((APP_WIDTH, header_height), Image.Resampling.LANCZOS)
                self.bg_image_tk = ImageTk.PhotoImage(bg_img_pil)
                self.canvas_header.create_image(0, 0, image=self.bg_image_tk, anchor="nw")
        except: pass
        
        title_font = font.Font(family="Segoe UI", size=20, weight="bold")
        self.canvas_header.create_text(APP_WIDTH/2, header_height/2, text="VISION TRANSLATOR", font=title_font, fill="white")

        # INPUT KEY AREA
        frame_key = tk.Frame(root, bg=COLOR_BG)
        frame_key.pack(fill="x", padx=20, pady=(0, 0))
        
        tk.Label(frame_key, text="API Key (Gemini):", bg=COLOR_BG, fg=COLOR_TEXT, anchor="w").pack(fill="x")
        self.txt_keys = tk.Text(frame_key, height=2, bg="#2D2D2D", fg="white", insertbackground="white", relief="flat", font=("Consolas", 10))
        self.txt_keys.pack(fill="x", pady=5)
        
        # Load key cũ
        saved_key = load_saved_keys()
        if saved_key: self.txt_keys.insert("1.0", saved_key)

        # RESULT AREA
        self.txt_result = tk.Text(root, bg="#252526", fg="#D4D4D4", font=("Consolas", 11), wrap="word", relief="flat", padx=10, pady=10)
        self.txt_result.pack(fill="both", expand=True, padx=20, pady=15)
        self.txt_result.insert("1.0", "👋 Xin chào! \n1. Nhập API Key vào ô bên trên.\n2. Bấm nút CHỤP (hoặc nhấn F2).\n3. Quét vùng văn bản trên màn hình để dịch.")

        # BUTTON AREA
        frame_btn = tk.Frame(root, bg=COLOR_BG)
        frame_btn.pack(fill="x", pady=(0, 20), padx=20)
        
        btn = tk.Button(frame_btn, text="📸 QUÉT MÀN HÌNH (F2)", bg=COLOR_BTN, fg="white", font=("Segoe UI", 11, "bold"), pady=10, command=self.start_snip, relief="flat", cursor="hand2")
        btn.pack(fill="x")

    def start_snip(self):
        # Tạo delay nhỏ để tránh xung đột phím
        self.root.after(10, lambda: SnippingTool(self.root, self.handle_image))
    
    def handle_image(self, image_path):
        self.root.deiconify() # Hiện lại app
        self.txt_result.delete("1.0", tk.END)
        self.txt_result.insert("1.0", "⏳ Đang gửi ảnh cho AI xử lý...\n")
        
        # Chạy xử lý ở luồng riêng để không đơ giao diện
        threading.Thread(target=self.run_process, args=(image_path,), daemon=True).start()

    def run_process(self, image_path):
        keys_text = self.txt_keys.get("1.0", tk.END).strip()
        
        # Gọi hàm xử lý
        result = smart_process_rotation(keys_text, image_path)
        
        # Xóa file ảnh tạm
        try: os.remove(image_path)
        except: pass
        
        # Cập nhật giao diện (cần dùng after vì đang ở thread khác)
        self.root.after(0, lambda: self.update_ui(result))
        
    def update_ui(self, text):
        self.txt_result.delete("1.0", tk.END)
        self.txt_result.insert("1.0", text)
        self.txt_result.see("1.0")

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()