# RODENT GAIT TRACKER (RGT)

The **Rodent Gait Tracker (RGT)** is a Python application designed to monitor and analyze the gait of rodents using computer vision techniques. It captures video input, detects rodent movement, calculates speed, and automates mouse clicks based on predefined conditions. The tool includes a graphical user interface (GUI) for configuration, live adjustments, and stopping the tracking process.

## Features
- Real-time rodent gait tracking using OpenCV.
- Customizable parameters (e.g., speed range, click limit).
- GUI for initial setup (rodent selection, screen viewing coordinates, click limit, timer, email notifications).
- Live adjustment window to tweak settings during tracking.
- Restart and stop functionality with settings persistence.
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

## Installation
1. Clone the repository or download the script:
   ```bash
   git clone https://github.com/AldenChiu/RGT---Rodent-Gait-Tracker.git
   ```

2. Install the required dependencies:
   ```bash
   pip install opencv-python numpy mss pyautogui
   ```
   Note: `tkinter` is typically included with Python; ensure it’s available.

3. Configure email settings:
   - Edit the file named `config.json` in the project directory with your email credentials:
     ```json
     {
       "sender_email": "your_email@gmail.com",
       "app_password": "your_app_specific_password",
       "recipient_email": "recipient_email@gmail.com"
     }
     ```
   - Set sender_email as the email address you'd like to send reminder emails to.
   - Use an app-specific password for Gmail or your email provider’s security settings. Look this up if you don't know where to find it.
   - Leave recipient_email untouched, as you can adjust it during the program.

## Usage
1. Run the script:
   ```bash
   python rodent_gait_tracker.py
   ```

2. Follow the setup prompts:
   - Select the rodent type (e.g., Black Rat, White Mouse).
   - Choose or define the area of the screen with the mouse and click coordinates. When doing so, confine your selection to only the side view of the rodent.
   - Set a click limit (or skip for no limit).
   - Set a timer duration (in minutes, or skip).
   - Configure the recipient email for notifications.

3. During tracking:
   - A stop window appears with "Stop Program" and "Adjust Settings" buttons.
   - Click "Adjust Settings" to open a live adjustment window for speed duration and speed range.
   - The program functions such that when it simulates a click when the rodent's speed over a set time (Speed Duration) is within a certain percent (Speed Range %) of the average speed over that time.
   - Click "Stop Program" to end the session and delete saved settings.

4. End conditions:
   - The program stops when the timer expires, the click limit is reached, or the stop button is pressed.
   - If selected, an email notification is automatically sent when the timer expires or click limit is reached.
   - Choose "Restart" to continue with the same settings or "Cancel" to exit and reset.

## Configuration
- **Settings File**: The script saves settings to `rgt_settings.json` for reuse. Deleting this file forces a new setup.
- **Coordinates File**: `coordinates.json` stores saved tracking coordinates.

## Known Issues
- Sometimes misclicks when the rodent gets on its hind legs, turns around, or at the very beginning when it pops out its nose. In the testing I've done, about 50% of videos recorded are good.
- Settings for different rodent types have not all been tested. I've only tested with black mice and black and white rats.
- Manually clicking doesn't add to the click counter, so doing so will result in more videos recorded than originally set.

## Contributing
Feel free to fork this repository, submit issues, or send pull requests. Improvements like additional rodent types, better performance optimization, or enhanced GUI features are welcome!

## Acknowledgments
- Built with help from xAI's Grok 3.
- Utilizes OpenCV, Tkinter, and other open-source libraries.
