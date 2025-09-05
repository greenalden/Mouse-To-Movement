import pyautogui
import time
import threading
from pynput import keyboard
import ctypes
from ctypes import wintypes, windll
import vgamepad as vg  # Install with: pip install vgamepad

# Create virtual Xbox controller
gamepad = vg.VX360Gamepad()

# Global flag to control the main loop
running = True

# Pause/resume toggle
paused = False

# Sensitivity control
sensitivity = 50
min_sensitivity = 2
max_sensitivity = 100

def clamp(value, min_val=-1.0, max_val=1.0):
    return max(min_val, min(max_val, value))

def on_press(key):
    global running, sensitivity, paused
    
    # Check if ESC is pressed
    if key == keyboard.Key.esc:
        print("\nESC pressed - Quitting...")
        running = False
        return False  # Stop the keyboard listener
    
    # Check for pause/resume with backtick/grave key
    try:
        if hasattr(key, 'char'):
            if key.char == '`':
                paused = not paused
                if paused:
                    print("PAUSED - Mouse unlocked. Press ` to resume.")
                    # Reset controller to center when pausing
                    gamepad.left_joystick_float(x_value_float=0.0, y_value_float=0.0)
                    gamepad.update()
                else:
                    print("RESUMED - Mouse controlling gamepad.")
            elif key.char == '[':
                # Decrease sensitivity
                sensitivity = max(min_sensitivity, sensitivity - 2)
                print(f"Sensitivity decreased to: {sensitivity}")
            elif key.char == ']':
                # Increase sensitivity
                sensitivity = min(max_sensitivity, sensitivity + 2)
                print(f"Sensitivity increased to: {sensitivity}")
    except AttributeError:
        pass

def main():
    global running, sensitivity, paused
    
    # Disable pyautogui's built-in delays for smoother performance
    pyautogui.MINIMUM_DURATION = 0
    pyautogui.MINIMUM_SLEEP = 0
    pyautogui.PAUSE = 0
    
    # Start the keyboard listener in a separate thread
    keyboard_listener = keyboard.Listener(on_press=on_press)
    keyboard_listener.start()
    
    # Start cursor in center of screen
    screen_w, screen_h = pyautogui.size()
    center_x, center_y = screen_w // 2, screen_h // 2
    
    # Initial mouse position
    pyautogui.moveTo(center_x, center_y)
    last_mx, last_my = center_x, center_y
    
    # Joystick position tracking
    joystick_x, joystick_y = 0.0, 0.0  # Use floating point for accumulation
    decay_rate = 0.85  # How quickly the joystick returns to center (0-1)
    
    print("Mouse movement now controls virtual Xbox controller.")
    print("Press ESC to quit (works even if window not selected).")
    print("Press ` (backtick) to pause/resume mouse control.")
    print("Use [ and ] keys to adjust sensitivity (current: 50)")
    print("=========================================")

    try:
        while running:
            # Skip processing if paused
            if paused:
                time.sleep(0.01)
                continue
                
            # Get current mouse position
            mx, my = pyautogui.position()
            
            # Calculate delta from last position
            dx = mx - last_mx
            dy = my - last_my
            
            # Update last position
            last_mx, last_my = mx, my
            
            # Accumulate joystick movement
            joystick_x += dx * sensitivity * 0.0001  # Scale down for -1 to 1 range
            joystick_y += dy * sensitivity * 0.0001
            
            # Apply decay to gradually return to center
            joystick_x *= decay_rate
            joystick_y *= decay_rate
            
            # Clamp to Xbox controller range (-1 to 1)
            final_x = clamp(joystick_x)
            final_y = clamp(-joystick_y)  # Invert Y for proper controls
            
            # Update virtual Xbox controller left stick
            gamepad.left_joystick_float(x_value_float=final_x, y_value_float=final_y)
            gamepad.update()
            
            # Keep mouse near center without constant resets
            dist_from_center = ((mx - center_x) ** 2 + (my - center_y) ** 2) ** 0.5
            if dist_from_center > 200:  # Only reset when far from center
                pyautogui.moveTo(center_x, center_y)
                last_mx, last_my = center_x, center_y
            
            time.sleep(0.005)  # 200Hz update rate
            
    except KeyboardInterrupt:
        print("\nCtrl+C pressed - Quitting...")
        running = False
    finally:
        # Clean up - reset controller to center
        gamepad.left_joystick_float(x_value_float=0.0, y_value_float=0.0)
        gamepad.update()
        gamepad.reset()
        print("Controller reset to center position.")
        
        # Stop the listener if it's still running
        if keyboard_listener.is_alive():
            keyboard_listener.stop()

if __name__ == "__main__":
    main()