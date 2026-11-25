"""Simple QR code scanner.

Two ways to load an image:
  1. Drag and drop an image file onto the window.
  2. Click "Chọn ảnh..." (or type/paste a path and press Enter).
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import cv2
import numpy as np
from PIL import Image, ImageOps, ImageTk

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    HAS_DND = True
except ImportError:
    HAS_DND = False

IMAGE_TYPES = [
    ("Ảnh", "*.png *.jpg *.jpeg *.bmp *.gif *.webp *.tif *.tiff"),
    ("Tất cả", "*.*"),
]
PREVIEW_SIZE = (360, 360)


def load_image(path):
    """Load an image as a BGR numpy array. Works with non-ASCII (Vietnamese) paths."""
    with Image.open(path) as img:
        img = ImageOps.exif_transpose(img).convert("RGB")
        return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)


def decode_qr(bgr):
    """Return a list of decoded QR strings. Tries a few preprocessing steps."""
    detector = cv2.QRCodeDetector()
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)

    candidates = [bgr, gray]
    h, w = gray.shape
    if max(h, w) < 1000:
        candidates.append(cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC))
    candidates.append(cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1])

    for img in candidates:
        ok, texts, _, _ = detector.detectAndDecodeMulti(img)
        found = [t for t in texts if t] if ok else []
        if found:
            return found
        text, _, _ = detector.detectAndDecode(img)
        if text:
            return [text]
    return []


class QRScannerApp:
    def __init__(self, root):
        self.root = root
        self.preview_photo = None
        root.title("Scan QR Code")
        root.geometry("640x640")
        root.minsize(480, 520)

        # --- Path row ---
        top = ttk.Frame(root, padding=10)
        top.pack(fill="x")
        self.path_var = tk.StringVar()
        entry = ttk.Entry(top, textvariable=self.path_var)
        entry.pack(side="left", fill="x", expand=True)
        entry.bind("<Return>", lambda e: self.scan(self.path_var.get()))
        ttk.Button(top, text="Chọn ảnh...", command=self.browse).pack(side="left", padx=(8, 0))
        ttk.Button(top, text="Scan", command=lambda: self.scan(self.path_var.get())).pack(side="left", padx=(8, 0))

        # --- Drop zone / preview ---
        hint = "Kéo thả ảnh QR vào đây" if HAS_DND else (
            "Kéo thả chưa bật (pip install tkinterdnd2)\nHãy bấm \"Chọn ảnh...\"")
        self.drop_zone = tk.Label(
            root, text=hint, relief="groove", bd=2, bg="#f4f6f8", fg="#555",
            font=("Segoe UI", 12), height=14,
        )
        self.drop_zone.pack(fill="both", expand=True, padx=10)
        self.drop_zone.bind("<Button-1>", lambda e: self.browse())

        if HAS_DND:
            self.drop_zone.drop_target_register(DND_FILES)
            self.drop_zone.dnd_bind("<<Drop>>", self.on_drop)

        # --- Result ---
        bottom = ttk.Frame(root, padding=10)
        bottom.pack(fill="x")
        header = ttk.Frame(bottom)
        header.pack(fill="x")
        ttk.Label(header, text="Kết quả:").pack(side="left")
        ttk.Button(header, text="Copy", command=self.copy_result).pack(side="right")
        self.status = ttk.Label(header, text="", foreground="#888")
        self.status.pack(side="right", padx=8)

        self.result = tk.Text(bottom, height=6, wrap="word", font=("Consolas", 11))
        self.result.pack(fill="x", pady=(6, 0))

    # --- Actions ---
    def browse(self):
        path = filedialog.askopenfilename(title="Chọn ảnh QR", filetypes=IMAGE_TYPES)
        if path:
            self.scan(path)

    def on_drop(self, event):
        files = self.root.tk.splitlist(event.data)
        if files:
            self.scan(files[0])

    def scan(self, path):
        path = path.strip().strip('"')
        if not path:
            return
        self.path_var.set(path)
        try:
            bgr = load_image(path)
        except Exception as exc:
            messagebox.showerror("Lỗi", f"Không mở được ảnh:\n{exc}")
            return

        self.show_preview(bgr)
        results = decode_qr(bgr)
        self.result.delete("1.0", "end")
        if results:
            self.result.insert("1.0", "\n\n".join(results))
            self.status.config(text=f"Tìm thấy {len(results)} mã QR", foreground="green")
        else:
            self.status.config(text="Không tìm thấy mã QR", foreground="red")

    def show_preview(self, bgr):
        img = Image.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))
        img.thumbnail(PREVIEW_SIZE)
        self.preview_photo = ImageTk.PhotoImage(img)
        self.drop_zone.config(image=self.preview_photo, text="", height=0)

    def copy_result(self):
        text = self.result.get("1.0", "end").strip()
        if text:
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            self.status.config(text="Đã copy", foreground="green")


def main():
    root = TkinterDnD.Tk() if HAS_DND else tk.Tk()
    QRScannerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
