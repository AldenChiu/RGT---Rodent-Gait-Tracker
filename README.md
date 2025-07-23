# RODENT GAIT TRACKER (RGT)

The **Rodent Gait Tracker (RGT)** is a Python application designed to monitor and analyze the gait of rodents using computer vision techniques. It captures video input, detects rodent movement, calculates speed, and automates mouse clicks based on predefined conditions. The tool includes a graphical user interface (GUI) for configuration, live adjustments, and stopping the tracking process.

## Features
- Real-time rodent gait tracking using OpenCV.
- Customizable parameters (minimum speed, speed range, click limit).
- GUI for initial setup (rodent selection, screen viewing coordinates, click limit, timer, email notifications).
- Live adjustment window to tweak settings during tracking.
- Email notifications when the timer expires.

## Requirements
- **Python 3.6+**
- **Libraries**:
  - `opencv-python` (for computer vision)
  - `numpy` (for array operations)
  - `tkinter` (for GUI, included with Python)
  - `mss` (for screen capture)
  - `pyautogui` (for mouse automation)
  - `smtplib` (for email notifications, with app-specific password setup)
  - `PIL` (for images)

## Installation
1. Clone the repository or download the script:
   ```bash
   git clone https://github.com/AldenChiu/RGT---Rodent-Gait-Tracker.git
   ```

2. Change to the project directory:
   ```bash
   cd RGT---Rodent-Gait-Tracker
   ```

3. Install the required dependencies:
   ```bash
   pip install opencv-python numpy mss pyautogui Pillow
   ```
   Note: `tkinter` is typically included with Python; ensure it’s available. All other libraries are included with Python.

4. Configure email settings:
   - Edit the file named `config.json` in the project directory with your email credentials:
     ```json
     {
       "sender_email": "your_email@gmail.com",
       "app_password": "your_app_specific_password",
       "recipient_email": "recipient_email@gmail.com"
     }
     ```
   - Set sender_email as the email address you'd like to be the sender of reminder emails.
   - Use an app-specific password for Gmail or your email provider’s security settings. Look this up if you don't know where to find it.
   - Leave recipient_email untouched, as you can adjust it during the program. This will be the email you want to receive reminder emails.

## Usage
If the user wants to use RGT as an application that can be pinned to the taskbar, do the following:
1. Start in the project directory:
   ```bash
   cd RGT---Rodent-Gait-Tracker
   ```
   
2. Run the script:
   ```
   pyinstaller --onefile --windowed --add-data "RGT_Logo.ico;." --add-data "config.json;." --add-data "RGT_Logo.png;." rodent_gait_tracker.py
   ```

3. Once created, make sure `config.json`, `RGT_Logo.ico`, and `RGT_Logo.png` are moved to the `dist` folder.

4. Open the application in the `dist` folder and pin it to your taskbar.

For those using the terminal:
1. Run the script:
   ```bash
   python rodent_gait_tracker.py
   ```

2. Follow the setup prompts:
   - Select the rodent type (e.g., Black Rat, White Mouse).
   - Define the coordinates containing the side view of the rodent, and where you want clicks to be.
   - Set a click limit (or skip for no limit).
   - Set a timer duration (in minutes, or skip).
   - Configure the recipient email for notifications.

3. During tracking:
   - A window will appear with "Stop Program" and "Adjust Settings" buttons.
   - Click "Adjust Settings" to open a live adjustment window for minimum tracking speed, speed duration, and speed range.
   - The program simulates a click when the rodent's speed over a set time (Speed Duration) is within a certain percent (Speed Range %) of the average speed over that time (providing it's always above Speed Min).

4. End conditions:
   - The program stops when the timer expires, the click limit is reached, or the stop button is pressed.
   - If selected, an email notification is automatically sent when a limit is reached.
   - Settings are saved and can be used the next time program is run.

## Configuration
- **Settings File**: `rgt_settings.json` stores all settings for reuse.
- **Coordinates File**: `coordinates.json` stores specifically saved tracking coordinates.

## Known Issues
- RGT currently clicks more frequently than it should, with about a 50% yield. Recording twice as many as needed is advised.
- Incorrectly captured videos are often caused by the rodent standing on its hind legs, turning around anywhere in the arena, or sticking its nose out from offscreen. These mistakes can be reduced by setting the coordinates to exclude the top and some of the edges of the area.
- Only the settings for black mice and black + white rats have been tested.
- Manually clicking the record button doesn't add to the click counter. Doing so will result in more videos recorded than originally set.

## Contributing
Feel free to fork this repository, submit issues, or send pull requests. Improvements like better performance optimization or enhanced GUI features are welcome!

## Acknowledgments
- Built with help from xAI's Grok 3.
- Utilizes OpenCV, Tkinter, and other open-source libraries.

Last updated 2025/07/23