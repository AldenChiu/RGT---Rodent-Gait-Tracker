"""
RODENT GAIT TRACKER (RGT)
"""

import cv2
import numpy as np
import time
import threading
import mss
import pyautogui
import tkinter as tk
from tkinter import messagebox, ttk
import sys
import json
import os
import smtplib
from email.message import EmailMessage

# CONFIGURATION
# Camera
FRAME_RATE = 500  # Photron camera frame rate
FRAME_SKIP = 25  # Determines fps (FRAME_RATE/FRAME_SKIP)
RESOLUTION = (640, 480)  # Downscale resolution (set to None for original)
# Speed/tracking
SPEED_RANGE_PERCENT = 50  # 50% range for speed trigger
IN_RANGE_DURATION = 0.5  # Seconds to maintain speed range before click
# Files
COORDINATES_FILE = "coordinates.json" # File to store coordinates
CONFIG_FILE = "config.json" # File to store email settings

SPEEDS_CAP = 30  # Max entries for speeds

time_expired_event = threading.Event() # Initialize as a threading.Event
send_email_flag = False

# Screen capture/clicking
sct = mss.mss()
MONITOR_SIDEVIEW = {}
CLICK_POSITION = (0, 0)
pyautogui.FAILSAFE = True  # Move mouse to top-left corner to abort
pyautogui.PAUSE = 0.01  # Small delay for each action

initial_settings = {}



"""
FUNCTIONS
"""

# RODENT SELECTION

RODENT_CONFIGS = {
    "Black Rat": {
        "MIN_AREA": 500, # Minimum contour area for mouse
        "LOWER_GREEN": np.array([40, 50, 50]), # HSV range for green screen
        "UPPER_GREEN": np.array([80, 255, 255]),
        "VALUE_THRESHOLD": 180, # Max Value (HSV) to exclude lighter tail
        "MIN_CLICK_INTERVAL": 4  # Minimum seconds between clicks
    },
    "White Rat": {
        "MIN_AREA": 500,
        "LOWER_GREEN": np.array([40, 50, 50]),
        "UPPER_GREEN": np.array([80, 255, 255]),
        "VALUE_THRESHOLD": 150,
        "MIN_CLICK_INTERVAL": 4
    },
    "Black and White Rat": {
        "MIN_AREA": 500,
        "LOWER_GREEN": np.array([40, 50, 50]),
        "UPPER_GREEN": np.array([80, 255, 255]),
        "VALUE_THRESHOLD": 180,
        "MIN_CLICK_INTERVAL": 4
    },
    "Brown Rat": {
        "MIN_AREA": 500,
        "LOWER_GREEN": np.array([35, 50, 50]),
        "UPPER_GREEN": np.array([85, 255, 255]),
        "VALUE_THRESHOLD": 170,
        "MIN_CLICK_INTERVAL": 4
    },
    "Black Mouse": {
        "MIN_AREA": 200,
        "LOWER_GREEN": np.array([40, 50, 50]),
        "UPPER_GREEN": np.array([80, 255, 255]),
        "VALUE_THRESHOLD": 180,
        "MIN_CLICK_INTERVAL": 2.5
    },
    "White Mouse": {
        "MIN_AREA": 200,
        "LOWER_GREEN": np.array([40, 50, 50]),
        "UPPER_GREEN": np.array([80, 255, 255]),
        "VALUE_THRESHOLD": 150,
        "MIN_CLICK_INTERVAL": 2.5
    },
    "Brown Mouse": {
        "MIN_AREA": 200,
        "LOWER_GREEN": np.array([35, 50, 50]),
        "UPPER_GREEN": np.array([85, 255, 255]),
        "VALUE_THRESHOLD": 170,
        "MIN_CLICK_INTERVAL": 2.5
    },
    "Black and White Mouse": {
        "MIN_AREA": 200,
        "LOWER_GREEN": np.array([40, 50, 50]),
        "UPPER_GREEN": np.array([80, 255, 255]),
        "VALUE_THRESHOLD": 180,
        "MIN_CLICK_INTERVAL": 2.5
    }
}

# Create pop-up window for rodent selection
def create_rodent_selection_popup():
    popup = tk.Toplevel()
    popup.title("Rodent Selection")
    center_x, center_y = center_window(popup, 300, 200)
    popup.geometry(f"300x200+{center_x}+{center_y}")
    popup.resizable(False, False)
    popup.iconbitmap(icon_path)

    tk.Label(popup, text="Select Rodent Type and Color:").pack(pady=10)
    
    rodent_var = tk.StringVar()
    rodent_options = ["Black Rat", "White Rat", "Black and White Rat", "Brown Rat", "Black Mouse", "White Mouse", "Black and White Mouse", "Brown Mouse"]
    rodent_dropdown = ttk.Combobox(popup, textvariable=rodent_var, values=rodent_options, state="readonly")
    rodent_dropdown.set("Black Rat")
    rodent_dropdown.pack(pady=10)

    def on_ok():
        selected_rodent = rodent_var.get()
        popup.destroy()
        popup.result = selected_rodent
        print(f"Selected rodent: {selected_rodent}")

    def on_cancel():
        popup.destroy()
        popup.result = None
    
    button_frame = tk.Frame(popup)
    button_frame.pack(expand=True, fill=None, pady=5)
    
    tk.Button(button_frame, text="OK", command=on_ok).pack(side=tk.LEFT, padx=5)
    tk.Button(button_frame, text="Cancel", command=on_cancel).pack(side=tk.LEFT, padx=5)
    
    popup.bind('<Return>', lambda event: on_ok())

    popup.grab_set()
    root.wait_window(popup)
    return getattr(popup, 'result', None) # Return the result or None if cancelled



# SCREEN READING

# Create pop-up to choose between saved or new coordinates
def create_coordinate_choice_popup(saved_coords):
    popup = tk.Toplevel()
    popup.title("Coordinate Selection")
    center_x, center_y = center_window(popup, 370, 270)
    popup.geometry(f"370x270+{center_x}+{center_y}")
    popup.resizable(False, False)
    popup.iconbitmap(icon_path)
    
    tk.Label(popup, text="Coordinate Selection", font=("Arial", 12, "bold")).pack(pady=10)
    if saved_coords:
        top_left, bottom_right, click = saved_coords
        tk.Label(popup, text=f"Saved Coordinates:\nTop-Left: {top_left}\nBottom-Right: {bottom_right}\nClick: {click}", wraplength=350).pack(pady=5)
    else:
        tk.Label(popup, text="No saved coordinates found.\nSelect new coordinates.").pack(pady=5)
    
    choice = tk.StringVar(value="new" if not saved_coords else "")
    
    def on_use_saved():
        choice.set("saved")
        popup.destroy()
    
    def on_select_new():
        choice.set("new")
        popup.destroy()
    
    def on_cancel():
        choice.set("cancel")
        popup.destroy()
    
    popup.protocol("WM_DELETE_WINDOW", on_cancel)
    
    button_frame = tk.Frame(popup)
    button_frame.pack(expand=True, fill=None, pady=5)
    
    if saved_coords:
        tk.Button(button_frame, text="Use Saved", command=on_use_saved).pack(side=tk.LEFT, padx=5)
    tk.Button(button_frame, text="Select New", command=on_select_new).pack(side=tk.LEFT, padx=5)
    tk.Button(button_frame, text="Cancel", command=on_cancel).pack(side=tk.LEFT, padx=5)
    
    popup.grab_set()
    root.wait_window(popup)
    return choice.get()

# Load saved coordinates
def load_coordinates():
    if not os.path.exists(COORDINATES_FILE):
        return None
    try:
        with open(COORDINATES_FILE, 'r') as f:
            data = json.load(f)
        # Validate structure
        required_keys = ["top_left", "bottom_right", "click"]
        if not all(key in data for key in required_keys):
            return None
        top_left = tuple(data["top_left"])
        bottom_right = tuple(data["bottom_right"])
        click = tuple(data["click"])
        # Validate values
        if not (isinstance(top_left, (list, tuple)) and isinstance(bottom_right, (list, tuple)) and isinstance(click, (list, tuple))):
            return None
        if len(top_left) != 2 or len(bottom_right) != 2 or len(click) != 2:
            return None
        if bottom_right[0] <= top_left[0] or bottom_right[1] <= top_left[1]:
            return None
        return top_left, bottom_right, click if all([top_left, bottom_right, click]) else None
    except Exception as e:
        print(f"Error loading coordinates: {e}")
        return None

# Create pop-up window for choosing coordinates
def create_side_view_and_click_selection_popup():
    popup = tk.Toplevel()
    popup.title("Side View and Click Selection")
    center_x, center_y = center_window(popup, 300, 200)
    popup.geometry(f"300x200+{center_x}+{center_y}")
    popup.resizable(False, False)
    popup.iconbitmap(icon_path)
    popup.focus_set()
    
    instruction_label = tk.Label(popup, text="Move mouse to the top-left corner of PFV4 side view.", wraplength=250)
    instruction_label.pack(pady=10)
    
    top_left = [None]
    bottom_right = [None]
    click = [None]
    
    def update_instruction(text):
        instruction_label.config(text=text)
        popup.update()
    
    def get_top_left():
        update_instruction("Click OK, then move mouse to top-left corner of PFV4 side view. Press 't' to capture.")
        def on_ok_left():
            popup.unbind("<t>")
            popup.bind("<t>", lambda e: save_top_left())
            ok_button.config(state="disabled")
        def save_top_left():
            top_left[0] = pyautogui.position()
            print(f"Top-left: {top_left[0]}")
            update_instruction(f"Captured top-left: {top_left[0]}. Click OK to proceed to bottom-right.")
            ok_button.config(command=get_bottom_right, state="normal")
            popup.bind('<Return>', lambda event: get_bottom_right())
        ok_button.config(command=on_ok_left)
        popup.bind('<Return>', lambda event: on_ok_left())
    
    def get_bottom_right():
        update_instruction("Click OK, then move mouse to bottom-right corner of PFV4 side view. Press 'b' to capture.")
        def on_ok_right():
            popup.unbind("<b>")
            popup.bind("<b>", lambda e: save_bottom_right())
            ok_button.config(state="disabled")
        def save_bottom_right():
            bottom_right[0] = pyautogui.position()
            print(f"Bottom-right: {bottom_right[0]}")
            update_instruction(f"Captured bottom-right: {bottom_right[0]}. Click OK to proceed to click position.")
            ok_button.config(command=get_click, state="normal")
            popup.bind('<Return>', lambda event: get_click())
        ok_button.config(command=on_ok_right)
        popup.bind('<Return>', lambda event: on_ok_right())
    
    def get_click():
        update_instruction("Click OK, then move mouse to PFV4 'Record' button. Press 'c' to capture.")
        def on_ok_click():
            popup.unbind("<c>")
            popup.bind("<c>", lambda e: save_click())
            ok_button.config(state="disabled")
        def save_click():
            click[0] = pyautogui.position()
            print(f"Click position: {click[0]}")
            update_instruction(f"Captured click: {click[0]}. Click OK to finish.")
            ok_button.config(command=finish, state="normal")
            popup.bind('<Return>', lambda event: finish())
        ok_button.config(command=on_ok_click)
        popup.bind('<Return>', lambda event: on_ok_click())
    
    def finish():
        popup.destroy()
    
    button_frame = tk.Frame(popup)
    button_frame.pack(expand=True, fill=None, pady=5)
    
    ok_button = tk.Button(button_frame, text="OK", command=get_top_left)
    ok_button.pack(side=tk.LEFT, padx=5)
    
    popup.bind('<Return>', lambda event: get_top_left())
        
    popup.grab_set()
    root.wait_window(popup)
    
    if not (top_left[0] and bottom_right[0] and click[0]):
        print("Selection incomplete")
        root.destroy()
        sys.exit(1)

    return top_left[0], bottom_right[0], click[0]

# Save coordinates
def save_coordinates(top_left, bottom_right, click):
    try:
        data = {
            "top_left": list(top_left),
            "bottom_right": list(bottom_right),
            "click": list(click)
        }
        with open(COORDINATES_FILE, 'w') as f:
            json.dump(data, f, indent=4)
        print(f"Coordinates saved to {COORDINATES_FILE}")
    except Exception as e:
        print(f"Error saving coordinates: {e}")



# CLICK LIMIT

# Create pop-up window for click limit
def create_click_limit_popup():
    popup = tk.Toplevel()
    popup.title("Click Limit")    
    center_x, center_y = center_window(popup, 300, 200)
    popup.geometry(f"300x200+{center_x}+{center_y}")
    popup.resizable(False, False)
    popup.iconbitmap(icon_path)
    
    tk.Label(popup, text="Enter a click limit:").pack(pady=10)
    
    # Validate that an integer with inputted
    def validate_entry(text):
        if text == "":
            return True
        try:
            int(text)
            return True
        except ValueError:
            return False
    validate_cmd = popup.register(validate_entry)
    
    click_var = tk.IntVar(value=20)
    click_entry = tk.Entry(popup, textvariable=click_var, validate="key", validatecommand=(validate_cmd, "%P"), width=15)
    click_entry.pack(pady=5)
    
    def on_ok():
        try:
            click_value = click_var.get()
            if click_value <= 0:
                raise ValueError("Click limit must be positive")
            popup.result = click_value
            popup.destroy()
            print(f"Click limit set for {click_value} clicks")
        except tk.TclError:
            messagebox.showerror("RGT", "Please enter a valid click limit amount.")
        except ValueError as e:
            messagebox.showerror("RGT", str(e))
    
    def on_skip():
        popup.destroy()
        print("Click limit option skipped")
    
    def on_cancel():
        popup.result = "cancel"
        popup.destroy()
    
    popup.protocol("WM_DELETE_WINDOW", on_cancel)
    
    button_frame = tk.Frame(popup)
    button_frame.pack(expand=True, fill=None, pady=5)
    
    tk.Button(button_frame, text="OK", command=on_ok).pack(side=tk.LEFT, padx=5)
    tk.Button(button_frame, text="Skip", command=on_skip).pack(side=tk.LEFT, padx=5)
    
    click_entry.bind('<Return>', lambda event: on_ok())
    
    popup.focus_set()
    popup.grab_set()
    popup.focus_set()
    popup.update()
    popup.after(100, lambda: click_entry.focus_set())
    
    root.wait_window(popup)
    return getattr(popup, 'result', None) # Return the result or None if cancelled

# Send email when click limit reached
def click_limit_exceeded(event):
    print("Sending click limit email")
    email_subject = f"RGT Click Limit Reached at {time.ctime()}"
    email_body = f"RGT has recorded {initial_settings['click_value']} videos.\nRGT has stopped recording, so you will need to restart the program."
    send_email(email_subject, email_body)
    event.set() # Set the event to signal expiration



# TIMER SELECTION

# Create pop-up window for a timer
def create_timer_popup():
    popup = tk.Toplevel()
    popup.title("Timer Selection")
    center_x, center_y = center_window(popup, 300, 200)
    popup.geometry(f"300x200+{center_x}+{center_y}")
    popup.resizable(False, False)
    popup.iconbitmap(icon_path)
    
    tk.Label(popup, text="Enter a timer amount in minutes:").pack(pady=10)
    
    # Validate that an integer with inputted
    def validate_entry(text):
        if text == "":
            return True
        try:
            int(text)
            return True
        except ValueError:
            return False
    validate_cmd = popup.register(validate_entry)
    
    timer_var = tk.IntVar(value=10)
    timer_entry = tk.Entry(popup, textvariable=timer_var, validate="key", validatecommand=(validate_cmd, "%P"), width=15)
    timer_entry.pack(pady=5)
    
    def on_ok():
        try:
            timer_value = timer_var.get()
            if timer_value <= 0:
                raise ValueError("Timer amount must be positive")
            popup.result = timer_value
            popup.destroy()
            print(f"Timer set for {timer_value} minutes")
        except tk.TclError:
            messagebox.showerror("RGT", "Please enter a valid time amount.")
        except ValueError as e:
            messagebox.showerror("RGT", str(e))
    
    def on_skip():
        popup.destroy()
        print("Timer option skipped")
    
    def on_cancel():
        popup.result = "cancel"
        popup.destroy()
    
    popup.protocol("WM_DELETE_WINDOW", on_cancel)
    
    button_frame = tk.Frame(popup)
    button_frame.pack(expand=True, fill=None, pady=5)
    
    tk.Button(button_frame, text="OK", command=on_ok).pack(side=tk.LEFT, padx=5)
    tk.Button(button_frame, text="Skip", command=on_skip).pack(side=tk.LEFT, padx=5)
    
    timer_entry.bind('<Return>', lambda event: on_ok())
    
    popup.focus_set()
    popup.grab_set()
    popup.focus_set()
    popup.update()
    popup.after(100, lambda: timer_entry.focus_set())
    
    root.wait_window(popup)
    return getattr(popup, 'result', None) # Return the result or None if cancelled

# Send email when timer expires
def time_expiration(event):
    if send_email_flag:
        print("Sending time expiration email")
        email_subject = f"RGT Time Limit Reached at {time.ctime()}"
        email_body = f"Your {initial_settings['timer_value']} minute timer has expired.\nRGT has stopped recording, so you will need to restart the program."
        send_email(email_subject, email_body)
    event.set() # Set the event to signal expiration



# EMAIL SELECTION

def create_email_selection_popup(config):
    popup = tk.Toplevel()
    popup.title("Email Alert Setup")
    center_x, center_y = center_window(popup, 400, 250)
    popup.geometry(f"400x250+{center_x}+{center_y}")
    popup.resizable(False, False)
    popup.iconbitmap(icon_path)

    recipient_email = config["recipient_email"]
    tk.Label(popup, text="Enter email for getting alerts:").pack(pady=10)
    tk.Label(popup, text=f"Saved Email:\n{recipient_email}", wraplength=300).pack(pady=5)

    new_email = tk.StringVar()

    email_entry = tk.Entry(popup, textvariable=new_email, width=30)
    email_entry.pack(pady=5)

    # Create buttons
    def on_use_saved():
        if recipient_email and "@" in recipient_email and "." in recipient_email:
            popup.result = config["recipient_email"]
            popup.destroy()
            print(f"Email set for alerts: {recipient_email}")
        else:
            popup.destroy()
            messagebox.showinfo("RGT", "Email error encountered.")
            root.destroy()
            sys.exit(0)

    def on_enter_new():
        email = new_email.get().strip()
        if email and "@" in email and "." in email:
            save_email(config, email)
            popup.result = config["recipient_email"]
            popup.destroy()
            print(f"Email set for alerts: {email}")
        else:
            messagebox.showerror("RGT", "Please enter a valid email address.")
            email_entry.delete(0, tk.END)
    
    def on_skip():
        global send_email_flag
        send_email_flag = False
        popup.destroy()
        print("Email option skipped")
    
    def on_cancel():
        popup.result = "cancel"
        popup.destroy()
    
    popup.protocol("WM_DELETE_WINDOW", on_cancel)

    button_frame = tk.Frame(popup)
    button_frame.pack(expand=True, fill=None, pady=5)
    
    tk.Button(button_frame, text="Use Saved", command=on_use_saved).pack(side=tk.LEFT, padx=5)
    tk.Button(button_frame, text="Enter New", command=on_enter_new).pack(side=tk.LEFT, padx=5)
    tk.Button(button_frame, text="Skip", command=on_skip).pack(side=tk.LEFT, padx=5)
    
    popup.grab_set()
    root.wait_window(popup)
    return getattr(popup, 'result', None) # Return the result or None if cancelled

# Load email configuration
def load_email_config():
    if not os.path.exists(CONFIG_FILE):
        print(f"Error: {CONFIG_FILE} not found. Please create it with email settings.")
        return None
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
        required_keys = ["sender_email", "app_password", "recipient_email"]
        if not all(key in config for key in required_keys):
            print(f"Error: {CONFIG_FILE} missing required keys: {required_keys}")
            return None
        return config
    except Exception as e:
        print(f"Error loading {CONFIG_FILE}: {e}")
        return None

# Save email
def save_email(config, new_email):
    try:
        config["recipient_email"] = new_email
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)
        print(f"{config["recipient_email"]} saved to {CONFIG_FILE}")
    except Exception as e:
        print(f"Error saving email: {e}")

# Send email notification
def send_email(subject, body):
    config = load_email_config()
    if not config:
        print("Email not sent: No valid email configuration")
        return None
    try:
        msg = EmailMessage()
        msg.set_content(body)
        msg['Subject'] = subject
        msg['From'] = config["sender_email"]
        msg['To'] = config["recipient_email"]
        
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(config["sender_email"], config["app_password"])
            server.send_message(msg)
        print("Email sent successfully")
    except Exception as e:
        print(f"Error sending email: {e}")



# RESTART WINDOW

def create_restart_window(ending):
    popup = tk.Toplevel()
    popup.title(f"{ending}")
    center_x, center_y = center_window(popup, 400, 200)
    popup.geometry(f"300x200+{center_x}+{center_y}")
    popup.resizable(False, False)
    popup.iconbitmap(icon_path)
    
    tk.Label(popup, text="Your program has finished!\nClick Restart to go again,\nor Cancel to close RGT.", wraplength=250).pack(pady=10)
    
    # Create buttons
    def on_restart():
        print("Restart initiated")
        popup.destroy()
        # Save settings and restart
        with open("rgt_settings.json", "w") as f:
            json.dump(initial_settings, f)
        os.execl(sys.executable, sys.executable, *sys.argv)
        
    def on_cancel():
        print("\"Cancel\" selected, deleting settings and exiting")
        if os.path.exists("rgt_settings.json"):
            os.remove("rgt_settings.json")
            print("rgt_settings.json deleted")
        global should_stop
        should_stop = True
        if 'timer' in globals():
            timer.cancel()
        popup.destroy()

    button_frame = tk.Frame(popup)
    button_frame.pack(expand=True, fill=None, pady=5)
    
    tk.Button(button_frame, text="Restart", command=on_restart).pack(side=tk.LEFT, padx=5)
    tk.Button(button_frame, text="Cancel", command=on_cancel).pack(side=tk.LEFT, padx=5)
    
    popup.grab_set()
    root.wait_window(popup)
    return None



# STOP BUTTON

# Create stop button window
def create_stop_button_window():
    stop_window = tk.Toplevel()
    stop_window.title("Stop")
    stop_window.iconbitmap(icon_path)
    stop_window.attributes('-topmost', True)
    
    # Get screen dimensions
    screen_width = stop_window.winfo_screenwidth()
    screen_height = stop_window.winfo_screenheight()
    
    # Set window position to bottom-right corner with a small offset
    offset_x = 30
    offset_y = 70
    window_width = 150
    window_height = 150
    x_position = screen_width - window_width - offset_x
    y_position = screen_height - window_height - offset_y
    stop_window.geometry(f"{window_width}x{window_height}+{int(x_position)}+{int(y_position)}")
    
    def on_stop():
        global should_stop
        print("Stop button clicked")
        should_stop = True
        if os.path.exists("rgt_settings.json"):
            os.remove("rgt_settings.json")
            print("rgt_settings.json deleted")
        stop_window.destroy()
    
    def on_adjust():
        create_control_panel()
    
    def on_cancel():
        stop_window.destroy()
        print("Stop window closed — recreating...")
        create_stop_button_window()
    
    stop_window.protocol("WM_DELETE_WINDOW", on_cancel)

    stop_button = tk.Button(stop_window, text="Stop", command=on_stop, bg="red", fg="white", font=("Arial", 12))
    stop_button.pack(side=tk.TOP, pady=10)
    adjust_button = tk.Button(stop_window, text="Adjust", command=on_adjust, bg="yellow", fg="black", font=("Arial", 12))
    adjust_button.pack(side=tk.TOP, pady=10)

    stop_window.update()  # Force window to render
    print("Stop window created")



# CONTROL PANEL

def create_control_panel():
    control_panel = tk.Toplevel()
    control_panel.title("Control Panel")
    control_panel.attributes('-topmost', True)
    control_panel.resizable(False, False)
    
    # Set window position to bottom-right corner with a small offset
    screen_width = control_panel.winfo_screenwidth()
    screen_height = control_panel.winfo_screenheight()
    offset_x = 180
    offset_y = 70
    window_width = 300
    window_height = 150
    x_position = screen_width - window_width - offset_x
    y_position = screen_height - window_height - offset_y
    control_panel.geometry(f"{window_width}x{window_height}+{int(x_position)}+{int(y_position)}")
    control_panel.iconbitmap(icon_path)
    
    duration_frame = tk.Frame(control_panel)
    duration_frame.pack()
    speed_duration = tk.StringVar(value=str(IN_RANGE_DURATION))
    tk.Label(duration_frame, text="Speed Duration (sec):").pack(pady=10, side='left')
    tk.Entry(duration_frame, textvariable=speed_duration, width=4).pack(pady=2, padx=5, side='left')
    
    tolerance_frame = tk.Frame(control_panel)
    tolerance_frame.pack()
    speed_tolerance = tk.StringVar(value=str(SPEED_RANGE_PERCENT))
    tk.Label(tolerance_frame, text="Speed Range %:").pack(pady=5, side='left')
    tk.Entry(tolerance_frame, textvariable=speed_tolerance, width=4).pack(pady=2, padx=5, side='left')
    
    def on_save(save_button):
        try:
            new_duration_value = float(speed_duration.get())
            new_tolerance_value = float(speed_tolerance.get())
            if new_duration_value <= 0 or new_tolerance_value < 0 or new_tolerance_value > 100:
                raise ValueError("• All values must be positive\n• Duration must be greater than 0\n• % must be between 0-100")
            global IN_RANGE_DURATION, SPEED_RANGE_PERCENT
            IN_RANGE_DURATION = new_duration_value
            SPEED_RANGE_PERCENT = new_tolerance_value
            print(f"IN_RANGE_DURATION set for {new_duration_value} seconds")
            print(f"SPEED_RANGE_PERCENT set for {new_tolerance_value} percent")
            save_button.config(bg="green", fg="white")
            root.after(200, lambda: save_button.config(bg="white", fg="black"))
        except ValueError as e:
            messagebox.showerror("RGT", str(e))
    
    save_button = tk.Button(control_panel, text="Save", command=lambda: on_save(save_button))
    save_button.pack(pady=10)

    control_panel.update()
    return control_panel



# TKINTER STUFF

# Initialize tkinter root
try:
    print("Initializing tkinter root")
    root = tk.Tk()
    root.withdraw()
    print("Tkinter root initialized")
except Exception as e:
    print(f"Tkinter initialization error: {e}")
    sys.exit(1)

# Get the icon to show on every window
if hasattr(sys, '_MEIPASS'):
    icon_path = os.path.join(sys._MEIPASS, 'RGT_Logo.ico')
else:
    icon_path = 'RGT_Logo.ico'

# Centers pop-up windows on the screen
def center_window(popup, window_width, window_height):
    # Get screen dimensions
    screen_width = popup.winfo_screenwidth()
    screen_height = popup.winfo_screenheight()
    
    # Calculate center coordinates
    center_x = int((screen_width - window_width) / 2)
    center_y = int((screen_height - window_height) / 2)
    
    return center_x, center_y



# GAIT TRACKER FUNCTION

def gait_tracker():
    global should_stop, timer
    time_expired_event.clear()
    
    # Camera variables
    frame_count = 0
    last_centroid = None
    # Speed/tracking variables
    speeds = []
    last_click_time = 0
    in_range_timestamps = []
    is_in_range_for_duration = False
    click_counter = 0
    
    # Start timer if set
    if initial_settings.get("timer_value", 0) > 0:
        timer_duration = initial_settings["timer_value"] * 60
        timer = threading.Timer(timer_duration, lambda: time_expiration(time_expired_event))
        timer.start()
    
    while not should_stop:
        # Check to see if timer has expired
        if time_expired_event.is_set():
            should_stop = True
            try:
                stop_window.destroy()
                create_restart_window("Timer Expired")
            except NameError:
                root.quit()
                root.destroy()
                break
        
        # Format side view
        side_view = np.array(sct.grab(MONITOR_SIDEVIEW))
        side_view = cv2.cvtColor(side_view, cv2.COLOR_RGBA2BGR)

        # Reduce frame count
        frame_count += 1
        if frame_count % FRAME_SKIP != 0:
            continue

        # Downscale side_view if specified
        if RESOLUTION:
            side_view = cv2.resize(side_view, RESOLUTION)

        # Green screen segmentation on side view
        hsv = cv2.cvtColor(side_view, cv2.COLOR_BGR2HSV)
        lower_green = np.array(initial_settings["LOWER_GREEN"], dtype=np.uint8)
        upper_green = np.array(initial_settings["UPPER_GREEN"], dtype=np.uint8)
        mask = cv2.inRange(hsv, lower_green, upper_green)
        mask = cv2.bitwise_not(mask)  # Invert to keep mouse
        # Filter out lighter tail based on Value channel
        value_mask = cv2.inRange(hsv[:, :, 2], 0, initial_settings["VALUE_THRESHOLD"])
        mask = cv2.bitwise_and(mask, value_mask)
        # Morphological operations to remove tail
        kernel = np.ones((3, 3), np.uint8)
        mask = cv2.erode(mask, kernel, iterations=5)  # Aggressive erosion for thin tail
        mask = cv2.dilate(mask, kernel, iterations=2)  # Restore body shape

        # Find mouse contour and centroid in side view
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        centroid = None
        if contours:
            largest = max(contours, key=cv2.contourArea)
            area = cv2.contourArea(largest)
            if area > initial_settings["MIN_AREA"]:
                x, y, w, h = cv2.boundingRect(largest)
                centroid = (x + w//2, y + h//2)
                # Uncomment if you want to see the window showing the green box around the rat (1/2)
                # cv2.rectangle(side_view, (x, y), (x+w, y+h), (0, 255, 0), 2)
        # Calculate speed
        speed = 0
        current_time = time.time()
        if centroid and last_centroid is not None:
            dx = centroid[0] - last_centroid[0]
            speed = abs(dx) * FRAME_RATE / FRAME_SKIP
            speeds.append(speed)
            speeds = [s for s in speeds if current_time - time.time() <= IN_RANGE_DURATION and s < 4000]
            if len(speeds) > SPEEDS_CAP:
                speeds.pop(0)
        else:
            speeds = []

        # Calculate average speed
        avg_speed = np.mean(speeds) if speeds else 0.0

        # Check if all speed measurements are within SPEED_RANGE_PERCENT
        lower_bound = avg_speed * (1 - (SPEED_RANGE_PERCENT / 100))
        upper_bound = avg_speed * (1 + (SPEED_RANGE_PERCENT / 100))

        all_within_range = all(lower_bound <= speed <= upper_bound for speed in speeds) if speeds else False
        all_significant = all(50 <= speed for s in speeds) if speeds else False

        if all_significant and all_within_range:
            in_range_timestamps.append(current_time)
            # Check if speed has been in range for IN_RANGE_DURATION
            if in_range_timestamps and (current_time - in_range_timestamps[0]) >= IN_RANGE_DURATION:
                is_in_range_for_duration = True
            # Remove timestamps older than IN_RANGE_DURATION
            in_range_timestamps = [t for t in in_range_timestamps if current_time - t <= IN_RANGE_DURATION]
        else:
            # Speed is out of range, clear timestamps to reset timer
            in_range_timestamps = []
            # Simulate click if speed was in range for IN_RANGE_DURATION and there's been MIN_CLICK_INTERVAL seconds between clicks
            if is_in_range_for_duration and (current_time - last_click_time) >= initial_settings["MIN_CLICK_INTERVAL"]:
                print(f"Avg speed {avg_speed:.2f} outside range [{lower_bound:.2f}, {upper_bound:.2f}] - Simulating click")
                pyautogui.click(x=CLICK_POSITION[0], y=CLICK_POSITION[1])
                last_click_time = current_time
                is_in_range_for_duration = False  # Reset flag after click
                click_counter += 1
                if click_counter == initial_settings['click_value'] and send_email_flag:  # Send email if click limit is reached
                    print("Sending click limit email")
                    email_subject = f"RGT Video Limit Reached at {time.ctime()}"
                    email_body = f"{initial_settings['click_value']} videos recorded at {time.ctime()}.\nRGT has stopped recording, so you will need to process those videos then restart the program."
                    send_email(email_subject, email_body)
                if click_counter >= initial_settings.get("click_value", float('inf')):  # Pause program if click limit is reached
                    should_stop = True
                    try:
                        stop_window.destroy()
                        if 'timer' in globals():
                            timer.cancel()
                        create_restart_window("Click Limit Reached")
                    except (NameError, tk.TclError):
                        root.quit()
                        root.destroy()
                        break

        last_centroid = centroid
        
        # Uncomment if you want to see the window showing the green box around the rat (2/2)
        # # Display speed, average speed, set speed range, and in-range status on side view
        # cv2.putText(side_view, f"Speed: {speed:.2f} px/s", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        # cv2.putText(side_view, f"Avg Speed: {avg_speed:.2f} px/s", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        # status_text = "In Range for 2.0s: Yes" if is_in_range_for_duration else "In Range for 2.0s: No"
        # cv2.putText(side_view, status_text, (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        # cv2.imshow('Mouse Speed Tracker (Side View)', side_view)
        
        try:
            if not should_stop:
                root.update()
        except Exception as e:
            print(f"Tkinter update error: {e}")
            break
        
        if cv2.waitKey(1) & 0xFF == ord('q'):  # Emergency off button
            should_stop = True
            try:
                stop_window.destroy()
                if 'timer' in globals():
                    timer.cancel()
            except (NameError, tk.TclError):
                pass
            break



"""
MAIN PROGRAM STARTS
"""

if __name__ == "__main__":
    global should_stop
    should_stop = False

    # Load or create settings
    if os.path.exists("rgt_settings.json"):
        with open("rgt_settings.json", "r") as f:
            initial_settings = json.load(f)
    else:
        selected_rodent = create_rodent_selection_popup()
        if selected_rodent is None:
            print("Program cancelled at rodent selection")
            root.destroy()
            sys.exit(0)
        initial_settings["MIN_AREA"] = RODENT_CONFIGS[selected_rodent]["MIN_AREA"]
        initial_settings["LOWER_GREEN"] = RODENT_CONFIGS[selected_rodent]["LOWER_GREEN"].tolist()
        initial_settings["UPPER_GREEN"] = RODENT_CONFIGS[selected_rodent]["UPPER_GREEN"].tolist()
        initial_settings["VALUE_THRESHOLD"] = RODENT_CONFIGS[selected_rodent]["VALUE_THRESHOLD"]
        initial_settings["MIN_CLICK_INTERVAL"] = RODENT_CONFIGS[selected_rodent]["MIN_CLICK_INTERVAL"]

        saved_coords = load_coordinates()
        choice = create_coordinate_choice_popup(saved_coords)
        if choice == "cancel":
            print("Program cancelled at coordinate selection")
            root.destroy()
            sys.exit(0)
        elif choice == "saved":
            initial_settings["top_left"], initial_settings["bottom_right"], initial_settings["click"] = saved_coords
        else:
            initial_settings["top_left"], initial_settings["bottom_right"], initial_settings["click"] = create_side_view_and_click_selection_popup()
            save_coordinates(initial_settings["top_left"], initial_settings["bottom_right"], initial_settings["click"])
        MONITOR_SIDEVIEW = {"top": initial_settings["top_left"][1], "left": initial_settings["top_left"][0],
                           "width": initial_settings["bottom_right"][0] - initial_settings["top_left"][0],
                           "height": initial_settings["bottom_right"][1] - initial_settings["top_left"][1]}
        CLICK_POSITION = initial_settings["click"]
        
        initial_settings["click_value"] = create_click_limit_popup()
        if initial_settings["click_value"] == "cancel":
            print("Program cancelled at click limit selection")
            root.destroy()
            sys.exit(0)
        initial_settings["timer_value"] = create_timer_popup()
        if initial_settings["timer_value"] == "cancel":
            print("Program cancelled at timer value selection")
            root.destroy()
            sys.exit(0)
        email_config = load_email_config()
        email = create_email_selection_popup(email_config)
        if email == "cancel":
            print("Program cancelled at email selection")
            root.destroy()
            sys.exit(0)
        else:
            initial_settings["recipient_email"] = email
    stop_window = create_stop_button_window()
    MONITOR_SIDEVIEW = {"top": initial_settings["top_left"][1], "left": initial_settings["top_left"][0],
                       "width": initial_settings["bottom_right"][0] - initial_settings["top_left"][0],
                       "height": initial_settings["bottom_right"][1] - initial_settings["top_left"][1]}
    CLICK_POSITION = initial_settings["click"]

    # Run gait tracker
    gait_tracker()
    
    # Cleanup
    try:
        if 'stop_window' in globals() and stop_window is not None and stop_window.winfo_exists():
            stop_window.destroy()
        if 'timer' in globals():
            timer.cancel()
        if os.path.exists("rgt_settings.json"):
            os.remove("rgt_settings.json")
        root.quit()
        root.destroy()
    except Exception as e:
        print(f"Error during cleanup: {e}")
        root.quit()
        root.destroy()
    print("Cleaned up")
    cv2.destroyAllWindows()
    sys.exit(0)