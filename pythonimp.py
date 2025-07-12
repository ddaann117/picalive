import cv2
import numpy as np
import os
from moviepy.editor import ImageSequenceClip
import tkinter as tk
from tkinter import filedialog, Scale
from PIL import Image, ImageTk

class EvolvingVideoCreator:
    def __init__(self):
        # Default parameters
        self.fps = 30
        self.duration = 10
        self.evolution_strength = 0.05
        self.output_size = (512, 512)
        
    def create_evolving_video(self, image_path, output_path):
        """Creates an evolving video that overwrites itself in a loop"""
        # Load and resize the image
        img = cv2.imread(image_path)
        img = cv2.resize(img, self.output_size)
        
        # Calculate total frames
        total_frames = int(self.fps * self.duration)
        frames = []
        
        # Initialize with the original image
        current_frame = img.astype(np.float32) / 255.0
        
        print("Generating frames...")
        for i in range(total_frames):
            # Create evolution effect
            evolved_frame = self.evolve_frame(current_frame, i/total_frames)
            
            # Apply the overwriting effect - new content gradually replaces old
            overwrite_position = int((i / total_frames) * self.output_size[1])
            overwrite_width = max(1, int(self.output_size[1] / total_frames * 2))
            
            # Circular overwrite - the end connects back to the beginning
            if overwrite_position + overwrite_width > self.output_size[1]:
                # Handle the wrap-around case
                overflow = (overwrite_position + overwrite_width) - self.output_size[1]
                current_frame[:, overwrite_position:] = evolved_frame[:, overwrite_position:]
                current_frame[:, :overflow] = evolved_frame[:, :overflow]
            else:
                # Normal case
                current_frame[:, overwrite_position:overwrite_position+overwrite_width] = \
                    evolved_frame[:, overwrite_position:overwrite_position+overwrite_width]
            
            # Convert back to uint8 for saving
            frame_to_save = (current_frame * 255).astype(np.uint8)
            frames.append(frame_to_save)
            
            if i % 10 == 0:
                print(f"Generated frame {i}/{total_frames}")
        
        # Create video from frames
        print("Creating video...")
        clip = ImageSequenceClip([frame[:, :, ::-1] for frame in frames], fps=self.fps)
        clip.write_videofile(output_path, codec='libx264')
        print(f"Video saved to {output_path}")
        
        return output_path
    
    def evolve_frame(self, frame, progress):
        """Apply various transformations to evolve the frame"""
        evolved = frame.copy()
        
        # Color shift based on progress
        hue_shift = np.sin(progress * 2 * np.pi) * 0.1
        saturation_factor = 1.0 + np.sin(progress * 3 * np.pi) * 0.1
        
        # Convert to HSV for easier color manipulation
        hsv = cv2.cvtColor(evolved, cv2.COLOR_RGB2HSV)
        
        # Apply hue shift
        hsv[:, :, 0] = (hsv[:, :, 0] + hue_shift * 180) % 180
        
        # Apply saturation change
        hsv[:, :, 1] = np.clip(hsv[:, :, 1] * saturation_factor, 0, 1)
        
        # Convert back to RGB
        evolved = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)
        
        # Add some noise based on evolution strength
        noise = np.random.normal(0, self.evolution_strength, evolved.shape)
        evolved = np.clip(evolved + noise, 0, 1)
        
        # Apply subtle blur
        evolved = cv2.GaussianBlur(evolved, (3, 3), 0)
        
        return evolved

# Create the GUI
def create_gui():
    creator = EvolvingVideoCreator()
    
    root = tk.Tk()
    root.title("Evolving Video Creator")
    root.geometry("600x400")
    
    # Variables
    input_path = tk.StringVar()
    output_path = tk.StringVar()
    
    # Functions
    def select_input():
        path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.jpeg *.png")])
        if path:
            input_path.set(path)
            # Show preview
            img = Image.open(path)
            img.thumbnail((200, 200))
            preview_img = ImageTk.PhotoImage(img)
            preview_label.config(image=preview_img)
            preview_label.image = preview_img
    
    def select_output():
        path = filedialog.asksaveasfilename(defaultextension=".mp4", 
                                           filetypes=[("MP4 files", "*.mp4")])
        if path:
            output_path.set(path)
    
    def start_creation():
        if not input_path.get() or not output_path.get():
            status_label.config(text="Please select input and output files")
            return
        
        # Update parameters from sliders
        creator.duration = duration_slider.get()
        creator.fps = fps_slider.get()
        creator.evolution_strength = evolution_slider.get()
        
        status_label.config(text="Creating video... Please wait")
        root.update()
        
        try:
            creator.create_evolving_video(input_path.get(), output_path.get())
            status_label.config(text="Video created successfully!")
        except Exception as e:
            status_label.config(text=f"Error: {str(e)}")
    
    # Layout
    frame = tk.Frame(root, padx=20, pady=20)
    frame.pack(fill=tk.BOTH, expand=True)
    
    # Input section
    tk.Label(frame, text="Select Input Image:").grid(row=0, column=0, sticky="w")
    tk.Entry(frame, textvariable=input_path, width=40).grid(row=0, column=1, padx=5)
    tk.Button(frame, text="Browse", command=select_input).grid(row=0, column=2)
    
    # Preview
    preview_frame = tk.Frame(frame)
    preview_frame.grid(row=1, column=0, columnspan=3, pady=10)
    preview_label = tk.Label(preview_frame)
    preview_label.pack()
    
    # Output section
    tk.Label(frame, text="Save Video As:").grid(row=2, column=0, sticky="w")
    tk.Entry(frame, textvariable=output_path, width=40).grid(row=2, column=1, padx=5)
    tk.Button(frame, text="Browse", command=select_output).grid(row=2, column=2)
    
    # Parameters
    param_frame = tk.Frame(frame)
    param_frame.grid(row=3, column=0, columnspan=3, pady=10)
    
    tk.Label(param_frame, text="Duration (seconds):").grid(row=0, column=0, sticky="w")
    duration_slider = Scale(param_frame, from_=5, to=30, orient=tk.HORIZONTAL, length=200)
    duration_slider.set(10)
    duration_slider.grid(row=0, column=1)
    
    tk.Label(param_frame, text="Frames per second:").grid(row=1, column=0, sticky="w")
    fps_slider = Scale(param_frame, from_=15, to=60, orient=tk.HORIZONTAL, length=200)
    fps_slider.set(30)
    fps_slider.grid(row=1, column=1)
    
    tk.Label(param_frame, text="Evolution strength:").grid(row=2, column=0, sticky="w")
    evolution_slider = Scale(param_frame, from_=0.01, to=0.2, resolution=0.01, orient=tk.HORIZONTAL, length=200)
    evolution_slider.set(0.05)
    evolution_slider.grid(row=2, column=1)
    
    # Create button
    tk.Button(frame, text="Create Evolving Video", command=start_creation, 
              bg="#4CAF50", fg="white", height=2).grid(row=4, column=0, columnspan=3, pady=10)
    
    # Status
    status_label = tk.Label(frame, text="Ready", bd=1, relief=tk.SUNKEN, anchor=tk.W)
    status_label.grid(row=5, column=0, columnspan=3, sticky="we")
    
    root.mainloop()

if __name__ == "__main__":
    create_gui()
