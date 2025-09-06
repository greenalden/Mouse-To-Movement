import tkinter as tk
from tkinter import ttk, messagebox
import pyautogui
import threading
import time
import math
import vgamepad as vg
from pynput import keyboard
import numpy as np
from scipy import interpolate
import platform
import json
import os
from pathlib import Path

pyautogui.FAILSAFE = False

class MouseToGamepadGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Mouse to Xbox Controller - Advanced")
        
        # Settings file path
        self.settings_file = Path.home() / "mouse_gamepad_settings.json"
        
        # Default settings
        self.default_settings = {
            'sensitivity': 50,
            'decay_rate': 0.85,
            'deadzone': 0.05,
            'smoothing': 0.3,  # Increased default for more noticeable effect
            'x_axis_enabled': True,
            'y_axis_enabled': True,
            'invert_x': False,
            'invert_y': False,
            'control_points': [(0, 0), (0.25, 0.25), (0.5, 0.5), (0.75, 0.75), (1.0, 1.0)]
        }
        
        # Get screen dimensions and set appropriate window size
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Set window to 90% of screen height, max 900px wide
        window_width = min(900, int(screen_width * 0.8))
        window_height = min(700, int(screen_height * 0.85))
        
        # Center the window
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.root.configure(bg='#1e1e1e')
        
        # Make window resizable
        self.root.minsize(750, 500)
        
        # Initialize gamepad
        self.gamepad = vg.VX360Gamepad()
        
        # Control variables - will be loaded from settings
        self.running = False
        self.paused = False
        self.sensitivity = tk.DoubleVar()
        self.decay_rate = tk.DoubleVar()
        self.deadzone = tk.DoubleVar()
        self.smoothing = tk.DoubleVar()  # Added smoothing variable
        self.x_axis_enabled = tk.BooleanVar()
        self.y_axis_enabled = tk.BooleanVar()
        self.invert_x = tk.BooleanVar()
        self.invert_y = tk.BooleanVar()
        
        # Joystick position tracking
        self.joystick_x = 0.0
        self.joystick_y = 0.0
        self.raw_x = 0.0
        self.raw_y = 0.0
        
        # Smoothing buffers
        self.smooth_x = 0.0
        self.smooth_y = 0.0
        
        # Mouse tracking
        self.screen_w, self.screen_h = pyautogui.size()
        self.center_x = self.screen_w // 2
        self.center_y = self.screen_h // 2
        self.last_mx = self.center_x
        self.last_my = self.center_y
        
        # Response curve control points - will be loaded from settings
        self.control_points = []
        self.selected_point = None
        self.spline = None
        
        # Load settings first
        self.load_settings()
        
        # Setup GUI with proper scrolling
        self.setup_gui()
        
        # Calculate initial spline after a short delay to ensure GUI is ready
        self.root.after(100, self.initialize_curve)
        
        # Start update loop for display
        self.update_display()
        
        # Keyboard listener
        self.keyboard_listener = None
        
        # Auto-save timer
        self.auto_save_after_id = None
        
    def load_settings(self):
        """Load settings from file, use defaults if file doesn't exist"""
        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)
                
                # Validate and apply settings
                self.sensitivity.set(settings.get('sensitivity', self.default_settings['sensitivity']))
                self.decay_rate.set(settings.get('decay_rate', self.default_settings['decay_rate']))
                self.deadzone.set(settings.get('deadzone', self.default_settings['deadzone']))
                self.smoothing.set(settings.get('smoothing', self.default_settings['smoothing']))  # Added smoothing
                self.x_axis_enabled.set(settings.get('x_axis_enabled', self.default_settings['x_axis_enabled']))
                self.y_axis_enabled.set(settings.get('y_axis_enabled', self.default_settings['y_axis_enabled']))
                self.invert_x.set(settings.get('invert_x', self.default_settings['invert_x']))
                self.invert_y.set(settings.get('invert_y', self.default_settings['invert_y']))
                
                # Load control points with validation
                control_points = settings.get('control_points', self.default_settings['control_points'])
                if len(control_points) >= 2 and all(isinstance(p, list) and len(p) == 2 for p in control_points):
                    self.control_points = [(float(p[0]), float(p[1])) for p in control_points]
                else:
                    self.control_points = self.default_settings['control_points'].copy()
                    
                print(f"Settings loaded from {self.settings_file}")
            else:
                # Use default settings
                self.apply_default_settings()
                print("No settings file found, using defaults")
        except Exception as e:
            print(f"Error loading settings: {e}")
            self.apply_default_settings()
    
    def apply_default_settings(self):
        """Apply default settings to variables"""
        self.sensitivity.set(self.default_settings['sensitivity'])
        self.decay_rate.set(self.default_settings['decay_rate'])
        self.deadzone.set(self.default_settings['deadzone'])
        self.smoothing.set(self.default_settings['smoothing'])  # Added smoothing
        self.x_axis_enabled.set(self.default_settings['x_axis_enabled'])
        self.y_axis_enabled.set(self.default_settings['y_axis_enabled'])
        self.invert_x.set(self.default_settings['invert_x'])
        self.invert_y.set(self.default_settings['invert_y'])
        self.control_points = self.default_settings['control_points'].copy()
    
    def save_settings(self):
        """Save current settings to file"""
        try:
            settings = {
                'sensitivity': self.sensitivity.get(),
                'decay_rate': self.decay_rate.get(),
                'deadzone': self.deadzone.get(),
                'smoothing': self.smoothing.get(),  # Added smoothing
                'x_axis_enabled': self.x_axis_enabled.get(),
                'y_axis_enabled': self.y_axis_enabled.get(),
                'invert_x': self.invert_x.get(),
                'invert_y': self.invert_y.get(),
                'control_points': [[p[0], p[1]] for p in self.control_points]
            }
            
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f, indent=2)
                
            print(f"Settings saved to {self.settings_file}")
        except Exception as e:
            print(f"Error saving settings: {e}")
    
    def schedule_auto_save(self):
        """Schedule an auto-save after a delay"""
        if self.auto_save_after_id:
            self.root.after_cancel(self.auto_save_after_id)
        self.auto_save_after_id = self.root.after(1000, self.save_settings)  # Save after 1 second delay
    
    def reset_to_defaults(self):
        """Reset all settings to defaults"""
        if messagebox.askyesno("Reset Settings", 
                             "Are you sure you want to reset all settings to defaults?\n\nThis will:\n- Reset all sliders\n- Reset axis settings\n- Reset response curve\n- This cannot be undone!"):
            self.apply_default_settings()
            self.update_spline()
            self.draw_curve()
            self.draw_joystick_background()
            self.schedule_auto_save()
            print("Settings reset to defaults")
    
    def initialize_curve(self):
        """Initialize the curve after GUI is ready"""
        self.update_spline()
        self.draw_curve()
        
    def setup_gui(self):
        # Create main container with scrollbar
        main_container = tk.Frame(self.root, bg='#1e1e1e')
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Create canvas and scrollbar for scrolling
        canvas = tk.Canvas(main_container, bg='#1e1e1e', highlightthickness=0)
        v_scrollbar = ttk.Scrollbar(main_container, orient="vertical", command=canvas.yview)
        
        # Create frame inside canvas
        scrollable_frame = tk.Frame(canvas, bg='#1e1e1e')
        
        # Configure canvas scrolling
        canvas_frame = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        
        def configure_scroll_region(event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))
            # Make canvas frame fill width
            canvas_width = canvas.winfo_width()
            canvas.itemconfig(canvas_frame, width=canvas_width)
        
        scrollable_frame.bind('<Configure>', configure_scroll_region)
        canvas.bind('<Configure>', lambda e: canvas.itemconfig(canvas_frame, width=e.width))
        
        canvas.configure(yscrollcommand=v_scrollbar.set)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        v_scrollbar.pack(side="right", fill="y")
        
        # Bind mousewheel events
        def _on_mousewheel(event):
            if platform.system() == 'Darwin':  # macOS
                canvas.yview_scroll(int(-1 * event.delta), "units")
            else:  # Windows and Linux
                canvas.yview_scroll(int(-1 * (event.delta/120)), "units")
        
        def _on_linux_scroll_up(event):
            canvas.yview_scroll(-1, "units")
        
        def _on_linux_scroll_down(event):
            canvas.yview_scroll(1, "units")
        
        if platform.system() == 'Linux':
            canvas.bind_all("<Button-4>", _on_linux_scroll_up)
            canvas.bind_all("<Button-5>", _on_linux_scroll_down)
        else:
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Build the interface inside scrollable_frame
        self.build_interface(scrollable_frame)
        
        # Update scroll region after building interface
        self.root.after(100, configure_scroll_region)
        
    def build_interface(self, parent):
        # Main container with padding
        main_frame = tk.Frame(parent, bg='#1e1e1e')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        
        # Title
        title_label = tk.Label(main_frame, text="Mouse → Xbox Controller", 
                              bg='#1e1e1e', fg='#ffffff', font=('Arial', 14, 'bold'))
        title_label.pack(pady=(0, 10))
        
        # Top section - Three columns
        top_frame = tk.Frame(main_frame, bg='#1e1e1e')
        top_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Configure grid weights
        top_frame.grid_columnconfigure(0, weight=1)
        top_frame.grid_columnconfigure(1, weight=1)
        top_frame.grid_columnconfigure(2, weight=1)
        
        # LEFT: Main Controls
        control_frame = tk.LabelFrame(top_frame, text="Main Controls", bg='#2a2a2a', fg='#ffffff', 
                                     font=('Arial', 10, 'bold'), padx=8, pady=8)
        control_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        
        # Start/Stop button
        self.toggle_btn = tk.Button(control_frame, text="▶ START", command=self.toggle_control,
                                    bg='#4CAF50', fg='white', font=('Arial', 11, 'bold'),
                                    width=12, height=2, relief=tk.RAISED, bd=2)
        self.toggle_btn.pack(pady=3)
        
        # Status
        self.status_label = tk.Label(control_frame, text="⚫ Stopped", 
                                     bg='#2a2a2a', fg='#ff5555', font=('Arial', 9, 'bold'))
        self.status_label.pack(pady=2)
        
        # Hotkeys
        hotkey_frame = tk.LabelFrame(control_frame, text="Hotkeys", 
                                     bg='#2a2a2a', fg='#aaaaaa', font=('Arial', 9))
        hotkey_frame.pack(pady=5, fill=tk.X, padx=3)
        
        # Pause
        pause_frame = tk.Frame(hotkey_frame, bg='#2a2a2a')
        pause_frame.pack(pady=2, fill=tk.X)
        self.pause_btn = tk.Button(pause_frame, text="⏸ PAUSE", command=self.toggle_pause,
                                   bg='#FFA500', fg='white', font=('Arial', 9),
                                   width=10, state=tk.DISABLED)
        self.pause_btn.pack(side=tk.LEFT, padx=3)
        tk.Label(pause_frame, text="[`]", bg='#2a2a2a', fg='#777', 
                font=('Arial', 8)).pack(side=tk.LEFT)
        
        # Sensitivity
        sens_btn_frame = tk.Frame(hotkey_frame, bg='#2a2a2a')
        sens_btn_frame.pack(pady=2, fill=tk.X)
        tk.Button(sens_btn_frame, text="◀-", command=lambda: self.adjust_sensitivity(-2),
                 bg='#555', fg='white', font=('Arial', 8), width=3).pack(side=tk.LEFT, padx=1)
        tk.Label(sens_btn_frame, text="Sens", bg='#2a2a2a', fg='#888', 
                font=('Arial', 8)).pack(side=tk.LEFT, padx=2)
        tk.Button(sens_btn_frame, text="+▶", command=lambda: self.adjust_sensitivity(2),
                 bg='#555', fg='white', font=('Arial', 8), width=3).pack(side=tk.LEFT, padx=1)
        tk.Label(sens_btn_frame, text="[/]", bg='#2a2a2a', fg='#777', 
                font=('Arial', 8)).pack(side=tk.LEFT, padx=3)
        
        # Reset and Quit buttons
        reset_quit_frame = tk.Frame(hotkey_frame, bg='#2a2a2a')
        reset_quit_frame.pack(pady=3, fill=tk.X)
        
        tk.Button(reset_quit_frame, text="🔄 RESET", command=self.reset_to_defaults,
                 bg='#FF9800', fg='white', font=('Arial', 8),
                 width=7).pack(side=tk.LEFT, padx=1)
        
        tk.Button(reset_quit_frame, text="❌ QUIT", command=self.quit_app,
                 bg='#f44336', fg='white', font=('Arial', 8),
                 width=7).pack(side=tk.LEFT, padx=1)
        
        # MIDDLE: Axis Control
        axis_frame = tk.LabelFrame(top_frame, text="Axis Control", bg='#2a2a2a', fg='#ffffff', 
                                  font=('Arial', 10, 'bold'), padx=8, pady=8)
        axis_frame.grid(row=0, column=1, sticky="nsew", padx=5)
        
        tk.Label(axis_frame, text="Enable:", bg='#2a2a2a', fg='#aaa', 
                font=('Arial', 9)).pack(pady=2)
        
        self.x_check = tk.Checkbutton(axis_frame, text="X-Axis", 
                                      variable=self.x_axis_enabled, bg='#2a2a2a', fg='#0f0',
                                      activebackground='#2a2a2a', selectcolor='#1a1a1a',
                                      font=('Arial', 9), command=self.on_axis_toggle)
        self.x_check.pack(pady=2)
        
        self.y_check = tk.Checkbutton(axis_frame, text="Y-Axis", 
                                      variable=self.y_axis_enabled, bg='#2a2a2a', fg='#0f0',
                                      activebackground='#2a2a2a', selectcolor='#1a1a1a',
                                      font=('Arial', 9), command=self.on_axis_toggle)
        self.y_check.pack(pady=2)
        
        tk.Label(axis_frame, text="Invert:", bg='#2a2a2a', fg='#aaa', 
                font=('Arial', 9)).pack(pady=(10, 2))
        
        tk.Checkbutton(axis_frame, text="Invert X", variable=self.invert_x,
                      bg='#2a2a2a', fg='#fa0', activebackground='#2a2a2a',
                      selectcolor='#1a1a1a', font=('Arial', 9),
                      command=self.schedule_auto_save).pack(pady=2)
        
        tk.Checkbutton(axis_frame, text="Invert Y", variable=self.invert_y,
                      bg='#2a2a2a', fg='#fa0', activebackground='#2a2a2a',
                      selectcolor='#1a1a1a', font=('Arial', 9),
                      command=self.schedule_auto_save).pack(pady=2)
        
        # RIGHT: Joystick visualization
        joystick_frame = tk.LabelFrame(top_frame, text="Joystick Position", bg='#2a2a2a', fg='#ffffff', 
                                       font=('Arial', 10, 'bold'))
        joystick_frame.grid(row=0, column=2, sticky="nsew", padx=(5, 0))
        
        self.joystick_canvas = tk.Canvas(joystick_frame, width=180, height=180, bg='#1a1a1a', 
                                         highlightthickness=0)
        self.joystick_canvas.pack(padx=8, pady=8)
        
        self.draw_joystick_background()
        
        pos_frame = tk.Frame(joystick_frame, bg='#2a2a2a')
        pos_frame.pack(pady=(0, 8))
        
        self.x_label = tk.Label(pos_frame, text="X: 0.00", bg='#2a2a2a', fg='#0f0', 
                               font=('Courier', 9, 'bold'))
        self.x_label.pack(side=tk.LEFT, padx=8)
        
        self.y_label = tk.Label(pos_frame, text="Y: 0.00", bg='#2a2a2a', fg='#0f0', 
                               font=('Courier', 9, 'bold'))
        self.y_label.pack(side=tk.LEFT, padx=8)
        
        # Parameters section (more compact)
        params_frame = tk.LabelFrame(main_frame, text="Parameters", bg='#2a2a2a', fg='#ffffff', 
                                     font=('Arial', 10, 'bold'))
        params_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Create a grid for parameters
        param_grid = tk.Frame(params_frame, bg='#2a2a2a')
        param_grid.pack(padx=10, pady=8)
        
        # Sensitivity
        tk.Label(param_grid, text="Sensitivity:", bg='#2a2a2a', fg='#fff', 
                font=('Arial', 9), width=10, anchor='w').grid(row=0, column=0, sticky='w')
        self.sens_slider = tk.Scale(param_grid, from_=2, to=100, orient=tk.HORIZONTAL, 
                                    variable=self.sensitivity, bg='#3a3a3a', fg='#fff',
                                    highlightthickness=0, length=200,
                                    command=lambda v: self.schedule_auto_save())
        self.sens_slider.grid(row=0, column=1, padx=5)
        self.sens_value = tk.Label(param_grid, text="50", bg='#2a2a2a', fg='#0f0', width=5)
        self.sens_value.grid(row=0, column=2)
        
        # Decay
        tk.Label(param_grid, text="Decay Rate:", bg='#2a2a2a', fg='#fff', 
                font=('Arial', 9), width=10, anchor='w').grid(row=1, column=0, sticky='w')
        self.decay_slider = tk.Scale(param_grid, from_=0.5, to=0.99, resolution=0.01, 
                                     orient=tk.HORIZONTAL, variable=self.decay_rate, 
                                     bg='#3a3a3a', fg='#fff', highlightthickness=0, length=200,
                                     command=lambda v: self.schedule_auto_save())
        self.decay_slider.grid(row=1, column=1, padx=5)
        self.decay_value = tk.Label(param_grid, text="0.85", bg='#2a2a2a', fg='#0f0', width=5)
        self.decay_value.grid(row=1, column=2)
        
        # Deadzone
        tk.Label(param_grid, text="Deadzone:", bg='#2a2a2a', fg='#fff', 
                font=('Arial', 9), width=10, anchor='w').grid(row=2, column=0, sticky='w')
        self.dead_slider = tk.Scale(param_grid, from_=0, to=0.2, resolution=0.01, 
                                    orient=tk.HORIZONTAL, variable=self.deadzone, 
                                    bg='#3a3a3a', fg='#fff', highlightthickness=0, length=200,
                                    command=lambda v: self.schedule_auto_save())
        self.dead_slider.grid(row=2, column=1, padx=5)
        self.dead_value = tk.Label(param_grid, text="0.05", bg='#2a2a2a', fg='#0f0', width=5)
        self.dead_value.grid(row=2, column=2)
        
        # Smoothing - Updated slider range
        tk.Label(param_grid, text="Smoothing:", bg='#2a2a2a', fg='#fff', 
                font=('Arial', 9), width=10, anchor='w').grid(row=3, column=0, sticky='w')
        self.smooth_slider = tk.Scale(param_grid, from_=0, to=0.95, resolution=0.01, 
                                    orient=tk.HORIZONTAL, variable=self.smoothing, 
                                    bg='#3a3a3a', fg='#fff', highlightthickness=0, length=200,
                                    command=lambda v: self.schedule_auto_save())
        self.smooth_slider.grid(row=3, column=1, padx=5)
        self.smooth_value = tk.Label(param_grid, text="0.30", bg='#2a2a2a', fg='#0f0', width=5)
        self.smooth_value.grid(row=3, column=2)
        
        # Response Curve Editor
        curve_container = tk.LabelFrame(main_frame, text="Response Curve Editor (Drag Points)", 
                                        bg='#2a2a2a', fg='#ffffff', font=('Arial', 10, 'bold'))
        curve_container.pack(fill=tk.BOTH, expand=True)
        
        # Preset buttons
        curve_btn_frame = tk.Frame(curve_container, bg='#2a2a2a')
        curve_btn_frame.pack(fill=tk.X, padx=10, pady=8)
        
        tk.Label(curve_btn_frame, text="Presets:", bg='#2a2a2a', fg='#aaa', 
                font=('Arial', 9)).pack(side=tk.LEFT, padx=3)
        
        for preset in [("Linear", 'linear'), ("Aggressive", 'aggressive'), 
                      ("Precise", 'precise'), ("S-Curve", 's-curve')]:
            tk.Button(curve_btn_frame, text=preset[0], 
                     command=lambda p=preset[1]: self.load_preset(p),
                     bg='#444', fg='white', font=('Arial', 8), 
                     width=10).pack(side=tk.LEFT, padx=2)
        
        # Curve canvas (compact size)
        self.curve_canvas = tk.Canvas(curve_container, width=350, height=280, bg='#1a1a1a', 
                                      highlightthickness=0)
        self.curve_canvas.pack(pady=8)
        
        # Bind mouse events
        self.curve_canvas.bind('<Button-1>', self.on_curve_click)
        self.curve_canvas.bind('<B1-Motion>', self.on_curve_drag)
        self.curve_canvas.bind('<ButtonRelease-1>', self.on_curve_release)
        
        self.draw_curve_background()
        
        # Info
        info_text = "Auto-saves settings • Scroll with mouse wheel • Drag curve points • All hotkeys work when unfocused"
        tk.Label(main_frame, text=info_text, bg='#1e1e1e', fg='#888', 
                font=('Arial', 8)).pack(pady=(5, 0))
    
    def draw_joystick_background(self):
        self.joystick_canvas.delete("all")
        
        # Grid lines
        self.joystick_canvas.create_line(90, 0, 90, 180, fill='#333', width=1)
        self.joystick_canvas.create_line(0, 90, 180, 90, fill='#333', width=1)
        
        # Circles
        self.joystick_canvas.create_oval(45, 45, 135, 135, outline='#444', width=1)
        self.joystick_canvas.create_oval(20, 20, 160, 160, outline='#333', width=1)
        self.joystick_canvas.create_oval(5, 5, 175, 175, outline='#2a2a2a', width=2)
        
        # Disabled indicators
        if not self.x_axis_enabled.get():
            self.joystick_canvas.create_text(90, 170, text="X OFF", fill='#f55', 
                                            font=('Arial', 7, 'bold'))
        if not self.y_axis_enabled.get():
            self.joystick_canvas.create_text(10, 90, text="Y\nOFF", fill='#f55', 
                                            font=('Arial', 7, 'bold'))
        
        self.joystick_dot = self.joystick_canvas.create_oval(85, 85, 95, 95, 
                                                             fill='#0f0', outline='#0a0', width=2)
    
    def draw_curve_background(self):
        w, h = 350, 280
        margin = 35
        
        # Clear and redraw background
        self.curve_canvas.delete("background")
        
        # Axes
        self.curve_canvas.create_line(margin, h-margin, w-margin, h-margin, fill='#666', width=2, tags="background")
        self.curve_canvas.create_line(margin, h-margin, margin, margin, fill='#666', width=2, tags="background")
        
        # Grid
        for i in range(6):
            x = margin + i * (w - 2*margin) / 5
            y = h - margin - i * (h - 2*margin) / 5
            
            self.curve_canvas.create_line(x, h-margin, x, margin, fill='#333', width=1, dash=(2, 4), tags="background")
            self.curve_canvas.create_line(margin, y, w-margin, y, fill='#333', width=1, dash=(2, 4), tags="background")
            
            if i % 2 == 0:
                val = i / 5
                self.curve_canvas.create_text(x, h-margin+10, text=f"{val:.1f}", 
                                             fill='#888', font=('Arial', 7), tags="background")
                self.curve_canvas.create_text(margin-10, y, text=f"{val:.1f}", 
                                             fill='#888', font=('Arial', 7), tags="background")
        
        # Labels
        self.curve_canvas.create_text(w/2, h-5, text="Input", fill='#aaa', font=('Arial', 8), tags="background")
        self.curve_canvas.create_text(15, h/2, text="Out", fill='#aaa', font=('Arial', 8), angle=90, tags="background")
        
        self.deadzone_line = self.curve_canvas.create_line(0, 0, 0, 0, fill='#f55', width=1, dash=(3, 3), tags="background")
    
    def update_spline(self):
        if len(self.control_points) >= 2:
            x_points = [p[0] for p in self.control_points]
            y_points = [p[1] for p in self.control_points]
            
            try:
                self.spline = interpolate.interp1d(x_points, y_points, kind='cubic', 
                                                   bounds_error=False, fill_value='extrapolate')
            except:
                self.spline = interpolate.interp1d(x_points, y_points, kind='linear', 
                                                   bounds_error=False, fill_value='extrapolate')
    
    def draw_curve(self):
        # Don't delete background elements
        self.curve_canvas.delete("curve")
        self.curve_canvas.delete("points")
        
        w, h = 350, 280
        margin = 35
        
        # Update deadzone line
        dz = self.deadzone.get()
        if dz > 0:
            dz_x = margin + dz * (w - 2*margin)
            self.curve_canvas.coords(self.deadzone_line, dz_x, margin, dz_x, h-margin)
        
        # Draw curve
        if self.spline:
            points = []
            for i in range(101):
                x = i / 100.0
                try:
                    y = float(self.spline(x))
                    y = max(0, min(1, y))
                except:
                    y = x
                
                px = margin + x * (w - 2*margin)
                py = h - margin - y * (h - 2*margin)
                points.extend([px, py])
            
            if len(points) > 2:
                self.curve_canvas.create_line(points, fill='#0f0', width=2, 
                                             smooth=True, tags="curve")
        
        # Draw control points
        for i, (x, y) in enumerate(self.control_points):
            px = margin + x * (w - 2*margin)
            py = h - margin - y * (h - 2*margin)
            
            color = '#f55' if i == 0 or i == len(self.control_points) - 1 else '#ff0'
            
            self.curve_canvas.create_oval(px-5, py-5, px+5, py+5, 
                                         fill=color, outline='#fff', width=2, tags="points")
    
    def on_curve_click(self, event):
        w, h = 350, 280
        margin = 35
        
        for i, (x, y) in enumerate(self.control_points):
            px = margin + x * (w - 2*margin)
            py = h - margin - y * (h - 2*margin)
            
            if ((event.x - px)**2 + (event.y - py)**2)**0.5 < 10:
                if i != 0 and i != len(self.control_points) - 1:
                    self.selected_point = i
                return
    
    def on_curve_drag(self, event):
        if self.selected_point is not None:
            w, h = 350, 280
            margin = 35
            
            x = (event.x - margin) / (w - 2*margin)
            y = 1.0 - (event.y - margin) / (h - 2*margin)
            
            x = max(0.01, min(0.99, x))
            y = max(0, min(1, y))
            
            if self.selected_point > 0:
                x = max(x, self.control_points[self.selected_point - 1][0] + 0.01)
            if self.selected_point < len(self.control_points) - 1:
                x = min(x, self.control_points[self.selected_point + 1][0] - 0.01)
            
            self.control_points[self.selected_point] = (x, y)
            self.update_spline()
            self.draw_curve()
    
    def on_curve_release(self, event):
        if self.selected_point is not None:
            self.schedule_auto_save()
        self.selected_point = None
    
    def load_preset(self, preset_name):
        if preset_name == 'linear':
            self.control_points = [(0, 0), (0.25, 0.25), (0.5, 0.5), (0.75, 0.75), (1.0, 1.0)]
        elif preset_name == 'aggressive':
            self.control_points = [(0, 0), (0.25, 0.1), (0.5, 0.3), (0.75, 0.65), (1.0, 1.0)]
        elif preset_name == 'precise':
            self.control_points = [(0, 0), (0.25, 0.35), (0.5, 0.6), (0.75, 0.82), (1.0, 1.0)]
        elif preset_name == 's-curve':
            self.control_points = [(0, 0), (0.25, 0.15), (0.5, 0.5), (0.75, 0.85), (1.0, 1.0)]
        
        self.update_spline()
        self.draw_curve()
        self.schedule_auto_save()
    
    def apply_response_curve(self, value):
        abs_value = abs(value)
        sign = 1 if value >= 0 else -1
        
        if abs_value < self.deadzone.get():
            return 0
        
        normalized = (abs_value - self.deadzone.get()) / (1 - self.deadzone.get())
        
        if self.spline:
            try:
                result = float(self.spline(normalized))
                result = max(0, min(1, result))
            except:
                result = normalized
        else:
            result = normalized
        
        return sign * result
    
    def apply_smoothing(self, current_x, current_y):
        """Apply exponential smoothing to joystick values"""
        smooth_factor = self.smoothing.get()
        
        # Invert the factor so higher values = more smoothing
        # This feels more intuitive to users
        alpha = 1.0 - smooth_factor  # alpha is the weight for new values
        
        # Exponential moving average
        # Higher smoothing value = slower response (more smoothing)
        self.smooth_x = self.smooth_x * smooth_factor + current_x * alpha
        self.smooth_y = self.smooth_y * smooth_factor + current_y * alpha
        
        return self.smooth_x, self.smooth_y
    
    def on_axis_toggle(self):
        self.draw_joystick_background()
        
        if not self.x_axis_enabled.get():
            self.joystick_x = 0
            self.raw_x = 0
            self.smooth_x = 0  # Reset smoothing buffer
        if not self.y_axis_enabled.get():
            self.joystick_y = 0
            self.raw_y = 0
            self.smooth_y = 0  # Reset smoothing buffer
            
        self.schedule_auto_save()
    
    def adjust_sensitivity(self, delta):
        new_val = max(2, min(100, self.sensitivity.get() + delta))
        self.sensitivity.set(new_val)
        self.schedule_auto_save()
    
    def toggle_control(self):
        if not self.running:
            self.running = True
            self.paused = False
            self.toggle_btn.config(text="⏹ STOP", bg='#f44336')
            self.pause_btn.config(state=tk.NORMAL)
            self.status_label.config(text="🟢 Active", fg='#0f0')
            
            self.control_thread = threading.Thread(target=self.control_loop, daemon=True)
            self.control_thread.start()
            
            self.keyboard_listener = keyboard.Listener(on_press=self.on_key_press)
            self.keyboard_listener.start()
        else:
            self.stop_control()
    
    def stop_control(self):
        self.running = False
        self.toggle_btn.config(text="▶ START", bg='#4CAF50')
        self.pause_btn.config(state=tk.DISABLED, text="⏸ PAUSE")
        self.status_label.config(text="⚫ Stopped", fg='#f55')
        
        self.gamepad.left_joystick_float(x_value_float=0.0, y_value_float=0.0)
        self.gamepad.update()
        
        # Reset smoothing buffers when stopping
        self.smooth_x = 0.0
        self.smooth_y = 0.0
        
        if self.keyboard_listener:
            self.keyboard_listener.stop()
    
    def toggle_pause(self):
        self.paused = not self.paused
        if self.paused:
            self.pause_btn.config(text="▶ RESUME", bg='#4CAF50')
            self.status_label.config(text="⏸ Paused", fg='#FFA500')
            self.gamepad.left_joystick_float(x_value_float=0.0, y_value_float=0.0)
            self.gamepad.update()
        else:
            self.pause_btn.config(text="⏸ PAUSE", bg='#FFA500')
            self.status_label.config(text="🟢 Active", fg='#0f0')
    
    def quit_app(self):
        if self.running:
            self.stop_control()
        self.on_closing()
    
    def on_key_press(self, key):
        if key == keyboard.Key.esc:
            self.root.after(0, self.quit_app)
            return False
        
        try:
            if hasattr(key, 'char'):
                if key.char == '`':
                    self.root.after(0, self.toggle_pause)
                elif key.char == '[':
                    self.root.after(0, lambda: self.adjust_sensitivity(-2))
                elif key.char == ']':
                    self.root.after(0, lambda: self.adjust_sensitivity(2))
        except AttributeError:
            pass
    
    def control_loop(self):
        """Improved control loop with jump detection"""
        pyautogui.MINIMUM_DURATION = 0
        pyautogui.MINIMUM_SLEEP = 0
        pyautogui.PAUSE = 0
        
        pyautogui.moveTo(self.center_x, self.center_y)
        self.last_mx, self.last_my = self.center_x, self.center_y
        
        # Add flags for recentering detection
        skip_next_frame = False
        recenter_threshold = 200  # Distance from center before recentering
        jump_threshold = 50  # Movement larger than this is likely a recenter jump
        
        while self.running:
            if not self.paused:
                mx, my = pyautogui.position()
                
                # Calculate raw deltas
                dx = mx - self.last_mx
                dy = my - self.last_my
                
                # Detect if this is likely a recentering jump
                movement_magnitude = (dx**2 + dy**2)**0.5
                
                # Skip this frame if we just recentered OR if we detect a suspicious jump
                if skip_next_frame or movement_magnitude > jump_threshold:
                    skip_next_frame = False
                    self.last_mx, self.last_my = mx, my
                    time.sleep(0.005)
                    continue
                
                self.last_mx, self.last_my = mx, my
                
                sens = self.sensitivity.get()
                decay = self.decay_rate.get()
                
                if self.x_axis_enabled.get():
                    self.raw_x += dx * sens * 0.0001
                    self.raw_x *= decay
                    self.raw_x = max(-1.0, min(1.0, self.raw_x))
                    
                    joystick_x = self.apply_response_curve(self.raw_x)
                    if self.invert_x.get():
                        joystick_x = -joystick_x
                else:
                    joystick_x = 0
                    self.raw_x = 0
                
                if self.y_axis_enabled.get():
                    self.raw_y += dy * sens * 0.0001
                    self.raw_y *= decay
                    self.raw_y = max(-1.0, min(1.0, self.raw_y))
                    
                    joystick_y = self.apply_response_curve(-self.raw_y)
                    if self.invert_y.get():
                        joystick_y = -joystick_y
                else:
                    joystick_y = 0
                    self.raw_y = 0
                
                # Apply smoothing to the final output
                self.joystick_x, self.joystick_y = self.apply_smoothing(joystick_x, joystick_y)
                
                self.gamepad.left_joystick_float(x_value_float=self.joystick_x, 
                                                y_value_float=self.joystick_y)
                self.gamepad.update()
                
                # Check if we need to recenter
                dist_from_center = ((mx - self.center_x) ** 2 + (my - self.center_y) ** 2) ** 0.5
                if dist_from_center > recenter_threshold:
                    # Set flag to skip next frame
                    skip_next_frame = True
                    pyautogui.moveTo(self.center_x, self.center_y)
                    # Don't update last_mx/my here - let the next frame do it
            
            time.sleep(0.005)
        
        self.gamepad.left_joystick_float(x_value_float=0.0, y_value_float=0.0)
        self.gamepad.update()
    
    def update_display(self):
        """Update the GUI display elements"""
        # Only update if GUI elements exist (prevents errors during initialization)
        try:
            # Update joystick visualization
            x_pos = 90 + self.joystick_x * 80
            y_pos = 90 - self.joystick_y * 80
            
            self.joystick_canvas.coords(self.joystick_dot, x_pos-5, y_pos-5, x_pos+5, y_pos+5)
            
            self.x_label.config(text=f"X: {self.joystick_x:+.2f}")
            self.y_label.config(text=f"Y: {self.joystick_y:+.2f}")
            
            magnitude = (self.joystick_x**2 + self.joystick_y**2)**0.5
            if magnitude < 0.1:
                color = '#0f0'
            elif magnitude < 0.5:
                color = '#ff0'
            elif magnitude < 0.8:
                color = '#f80'
            else:
                color = '#f00'
            
            self.joystick_canvas.itemconfig(self.joystick_dot, fill=color)
            
            # Update parameter value displays
            if hasattr(self, 'sens_value'):
                self.sens_value.config(text=f"{self.sensitivity.get():.0f}")
            if hasattr(self, 'decay_value'):
                self.decay_value.config(text=f"{self.decay_rate.get():.2f}")
            if hasattr(self, 'dead_value'):
                self.dead_value.config(text=f"{self.deadzone.get():.2f}")
            if hasattr(self, 'smooth_value'):
                self.smooth_value.config(text=f"{self.smoothing.get():.2f}")
            
            # Update deadzone line position
            if hasattr(self, 'curve_canvas'):
                self.draw_curve()
                
        except (AttributeError, tk.TclError):
            # GUI not ready yet, skip this update
            pass
        
        self.root.after(16, self.update_display)
    
    def on_closing(self):
        if self.running:
            self.stop_control()
        self.save_settings()  # Final save on exit
        self.gamepad.reset()
        self.root.destroy()

def main():
    try:
        import scipy
    except ImportError:
        print("Please install scipy: pip install scipy")
        input("Press Enter to exit...")
        return
    
    root = tk.Tk()
    app = MouseToGamepadGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    # Force initial scroll region update
    root.after(200, lambda: root.event_generate('<Configure>'))
    
    root.mainloop()

if __name__ == "__main__":
    main()