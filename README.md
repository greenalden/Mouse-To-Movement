# Mouse-To-Movement

A Windows application that converts mouse movements into Xbox controller joystick inputs, enabling gamepad-style control using your mouse. Perfect for games that require analog stick precision or for users who prefer mouse control over traditional gamepad sticks.

![Python](https://img.shields.io/badge/python-3.11.9-blue.svg)
![Platform](https://img.shields.io/badge/platform-Windows-green.svg)
![License](https://img.shields.io/badge/license-MIT-orange.svg)

## 🎮 Features

### Core Functionality
- **Real-time mouse to joystick conversion** - Seamlessly translates mouse movements to left analog stick inputs
- **Virtual Xbox 360 controller** - Creates a virtual gamepad recognized by Windows and games
- **High-precision control** - Smooth, responsive input with minimal latency

### Advanced Controls
- **Adjustable sensitivity** - Fine-tune mouse-to-joystick responsiveness (2-100 range)
- **Decay rate control** - Configure how quickly the joystick returns to center (0.5-0.99)
- **Deadzone configuration** - Eliminate unwanted micro-movements (0-0.2)
- **Input smoothing** - Reduce jitter for smoother control (0-0.95)
- **Axis control** - Enable/disable and invert X/Y axes independently

### Response Curve Editor
- **Visual curve editor** - Drag control points to customize input response
- **Preset curves** - Quick access to Linear, Aggressive, Precise, and S-Curve profiles
- **Real-time preview** - See how your curve affects joystick behavior instantly

### User Interface
- **Live joystick visualization** - Monitor exact joystick position in real-time
- **Color-coded magnitude indicator** - Visual feedback for input intensity
- **Dark theme** - Easy on the eyes during extended gaming sessions
- **Scrollable interface** - Fully accessible on any screen size

### Quality of Life
- **Auto-save settings** - Your configuration persists between sessions
- **Global hotkeys** - Control the app even when it's not in focus
  - `` ` `` - Pause/Resume
  - `[` / `]` - Decrease/Increase sensitivity
  - `ESC` - Quit application
- **Jump detection** - Intelligent handling of mouse recentering

## 📋 Requirements

- Windows 10/11 (64-bit)
- ~500MB free disk space (for Python environment)
- Administrator privileges may be required for virtual gamepad driver

## 🚀 Installation

### Quick Install
1. Download the repository
2. Run `Setup.bat` (first-time setup)
3. Run `Run.bat` to start the application

### Manual Installation
If you prefer manual setup or have Python already installed:

```bash
# Install required packages
pip install pyautogui
pip install keyboard
pip install pynput
pip install vgamepad
pip install numpy
pip install scipy
```

## 🎯 Usage

### Getting Started
1. **Launch** the application using `Run.bat`
2. **Click START** to begin mouse-to-joystick conversion
3. **Move your mouse** - movements are translated to joystick input
4. **Adjust settings** in real-time using the GUI sliders

### Controls Overview
- **Sensitivity**: How much mouse movement affects joystick position
- **Decay Rate**: How quickly the joystick returns to center when you stop moving
- **Deadzone**: Minimum input required to register movement
- **Smoothing**: Reduces jitter for smoother control

### Tips for Best Experience
- Start with default settings and adjust gradually
- Use the "Precise" curve preset for accurate aiming
- Enable smoothing (0.3-0.5) for racing games
- Try the "Aggressive" curve for fast-paced action games
- Disable unused axes to prevent accidental input

## 🎨 Response Curve Presets

- **Linear**: Direct 1:1 input mapping
- **Aggressive**: Faster response for quick movements
- **Precise**: Enhanced control for small movements
- **S-Curve**: Balanced with smooth acceleration

## 💾 Settings Storage

Settings are automatically saved to: `%USERPROFILE%\mouse_gamepad_settings.json`

This includes:
- All slider values
- Axis configurations
- Custom response curves
- Window preferences

## 🛠️ Troubleshooting

### Virtual controller not detected
- Restart the application with administrator privileges
- Check if Windows Game Controllers shows the virtual device
- Ensure vgamepad driver is properly installed

### High CPU usage
- Increase smoothing value to reduce update frequency
- Check if decay rate is set too high (try 0.85)

### Erratic movement
- Increase deadzone to filter out micro-movements
- Enable smoothing (start with 0.3)
- Ensure no other mouse software is interfering

### Mouse gets stuck at screen edges
- This is normal - the app automatically recenters the mouse
- The recentering is filtered out and won't affect joystick input

## 🔧 Advanced Configuration

### Custom Response Curves
1. Click and drag control points on the curve editor
2. Add more precision where needed
3. Save automatically applies to current session

### Multi-Monitor Setup
- The app uses the primary monitor for mouse tracking
- Works best in fullscreen applications

### Game-Specific Profiles
While not built-in, you can:
1. Create copies of the settings file
2. Rename for different games
3. Swap files before launching

## 📚 Technical Details

- **Update Rate**: ~200Hz (5ms loop)
- **Input Method**: PyAutoGUI for mouse capture
- **Virtual Gamepad**: ViGEmBus driver via vgamepad
- **GUI Framework**: Tkinter with custom dark theme
- **Curve Interpolation**: Cubic spline via SciPy

## 🤝 Contributing

Contributions are welcome! Feel free to:
- Report bugs via GitHub Issues
- Suggest features or improvements
- Submit pull requests

## 📄 License

This project is released under the MIT License. See LICENSE file for details.

## 🙏 Acknowledgments

- **vgamepad** - Virtual gamepad implementation
- **PyAutoGUI** - Mouse tracking and control
- **ViGEmBus** - Virtual gamepad driver

## ⚠️ Disclaimer

This tool is intended for single-player games and personal use. Using input conversion tools may violate terms of service for some online games. Always check game policies before use.

## 🐛 Known Issues

- May not work with some anti-cheat systems
- UAC prompts might interrupt mouse tracking
- Some games may require exclusive fullscreen mode

---

**Note**: This tool modifies input methods and creates virtual devices. Use at your own discretion and ensure compatibility with your intended applications.