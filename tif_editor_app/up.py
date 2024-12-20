import os
import django
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
from django.core.files import File

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tif_editor_project.settings')
django.setup()

# Import your model after Django setup
from apps.mainadmin.models import InspirationPDF

class PDFUploaderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF Uploader")
        self.root.geometry("800x600")
        
        # Variables
        self.pdf_path = tk.StringVar()
        self.image_path = tk.StringVar()
        self.title = tk.StringVar()
        
        self.create_widgets()
        
    def create_widgets(self):
        # Main Frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title Section
        ttk.Label(main_frame, text="PDF Title:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.title, width=50).grid(row=0, column=1, columnspan=2, sticky=tk.W, pady=5)
        
        # PDF File Section
        ttk.Label(main_frame, text="PDF File:").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.pdf_path, width=50).grid(row=1, column=1, sticky=tk.W, pady=5)
        ttk.Button(main_frame, text="Browse", command=self.browse_pdf).grid(row=1, column=2, sticky=tk.W, pady=5, padx=5)
        
        # Preview Image Section
        ttk.Label(main_frame, text="Preview Image:").grid(row=2, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.image_path, width=50).grid(row=2, column=1, sticky=tk.W, pady=5)
        ttk.Button(main_frame, text="Browse", command=self.browse_image).grid(row=2, column=2, sticky=tk.W, pady=5, padx=5)
        
        # Image Preview
        self.preview_label = ttk.Label(main_frame)
        self.preview_label.grid(row=3, column=0, columnspan=3, pady=10)
        
        # Upload Button
        ttk.Button(main_frame, text="Upload PDF", command=self.upload_pdf).grid(row=4, column=0, columnspan=3, pady=20)
        
        # Status Label
        self.status_label = ttk.Label(main_frame, text="")
        self.status_label.grid(row=5, column=0, columnspan=3, pady=5)
        
    def browse_pdf(self):
        filename = filedialog.askopenfilename(
            filetypes=[("PDF files", "*.pdf")]
        )
        if filename:
            self.pdf_path.set(filename)
    
    def browse_image(self):
        filename = filedialog.askopenfilename(
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp")]
        )
        if filename:
            self.image_path.set(filename)
            self.show_preview(filename)
    
    def show_preview(self, image_path):
        try:
            # Open and resize image for preview
            image = Image.open(image_path)
            image.thumbnail((200, 200))  # Resize image
            photo = ImageTk.PhotoImage(image)
            
            # Update preview label
            self.preview_label.configure(image=photo)
            self.preview_label.image = photo  # Keep a reference
        except Exception as e:
            messagebox.showerror("Error", f"Cannot load preview image: {str(e)}")
    
    def upload_pdf(self):
        if not self.validate_inputs():
            return
        
        try:
            # Create new InspirationPDF instance
            pdf_instance = InspirationPDF(title=self.title.get())
            
            # Open and attach PDF file
            with open(self.pdf_path.get(), 'rb') as pdf_file:
                pdf_instance.pdf_file.save(
                    os.path.basename(self.pdf_path.get()),
                    File(pdf_file)
                )
            
            # Open and attach preview image
            with open(self.image_path.get(), 'rb') as img_file:
                pdf_instance.preview_image.save(
                    os.path.basename(self.image_path.get()),
                    File(img_file)
                )
            
            # Save the instance
            pdf_instance.save()
            
            self.status_label.config(text="Upload successful!", foreground="green")
            self.clear_fields()
            messagebox.showinfo("Success", "PDF uploaded successfully!")
            
        except Exception as e:
            self.status_label.config(text=f"Upload failed: {str(e)}", foreground="red")
            messagebox.showerror("Error", f"Upload failed: {str(e)}")
    
    def validate_inputs(self):
        if not self.title.get():
            messagebox.showerror("Error", "Please enter a title")
            return False
        if not self.pdf_path.get():
            messagebox.showerror("Error", "Please select a PDF file")
            return False
        if not self.image_path.get():
            messagebox.showerror("Error", "Please select a preview image")
            return False
        return True
    
    def clear_fields(self):
        self.title.set("")
        self.pdf_path.set("")
        self.image_path.set("")
        self.preview_label.configure(image="")

def main():
    root = tk.Tk()
    app = PDFUploaderGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()