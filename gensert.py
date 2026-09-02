import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk, ImageDraw, ImageFont
import pandas as pd


class CertificateGenerator:
    def __init__(self, root):
        self.root = root
        self.root.title("Certificate Generator")

        self.canvas = tk.Canvas(root)
        self.scroll_y = tk.Scrollbar(root, orient="vertical", command=self.canvas.yview)
        self.scroll_x = tk.Scrollbar(root, orient="horizontal", command=self.canvas.xview)

        self.scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)

        self.canvas.configure(yscrollcommand=self.scroll_y.set, xscrollcommand=self.scroll_x.set)

        self.frame = tk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.frame, anchor="nw")

        self.frame.bind("<Configure>", self.on_frame_configure)

        self.load_button = tk.Button(root, text="Load Image", command=self.load_image)
        self.load_button.pack(side=tk.LEFT)

        self.load_excel_button = tk.Button(root, text="Load Excel", command=self.load_excel)
        self.load_excel_button.pack(side=tk.LEFT)

        self.generate_button = tk.Button(root, text="Generate Certificates", command=self.generate_certificates)
        self.generate_button.pack(side=tk.LEFT)

        self.image = None
        self.excel_data = None
        self.text_positions = []
        self.font = ImageFont.truetype("arial.ttf", 30)  # You may need to provide the full path to a .ttf file

        self.canvas.bind("<Button-1>", self.get_click_position)

    def on_frame_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def load_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("PNG files", "*.png")])
        if file_path:
            self.image = Image.open(file_path)
            self.display_image()

    def display_image(self):
        img_width, img_height = self.image.size
        max_width, max_height = self.canvas.winfo_width(), self.canvas.winfo_height()

        # Scale image to fit within window if necessary
        if img_width > max_width or img_height > max_height:
            scale = min(max_width / img_width, max_height / img_height)
            new_width, new_height = int(img_width * scale), int(img_height * scale)
            self.image = self.image.resize((new_width, new_height), Image.LANCZOS)

        self.tk_image = ImageTk.PhotoImage(self.image)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)
        self.canvas.config(scrollregion=self.canvas.bbox(tk.ALL))

    def load_excel(self):
        file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx")])
        if file_path:
            self.excel_data = pd.read_excel(file_path)
            messagebox.showinfo("Success", "Excel file loaded successfully")

    def get_click_position(self, event):
        x, y = event.x, event.y
        self.text_positions.append((x, y))
        self.canvas.create_text(x, y, text="X", fill="red", font=("Arial", 20))

    def generate_certificates(self):
        if self.image and self.excel_data is not None and len(self.text_positions) == 2:
            for index, row in self.excel_data.iterrows():
                cert_image = self.image.copy()
                draw = ImageDraw.Draw(cert_image)
                draw.text(self.text_positions[0], row[0], font=self.font, fill="black")
                draw.text(self.text_positions[1], row[1], font=self.font, fill="black")
                cert_image.save(f"certificate_{index + 1}.png")
            messagebox.showinfo("Success", "Certificates generated successfully")
        else:
            messagebox.showerror("Error", "Please load image, Excel file and select text positions")


if __name__ == "__main__":
    root = tk.Tk()
    app = CertificateGenerator(root)
    root.mainloop()
