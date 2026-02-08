# HTB Desktop Client

### Installation with pipx (Recommended)

To install globally in an isolated environment:

```bash
# From source directory
pipx install .

# Or directly from GitHub
pipx install git+https://github.com/Goultarde/htb-gui-pipx.git
```

After installation, you can run the application from anywhere using:
```bash
htb-gui
```

### Development Setup

1. Clone the repository:
```bash
git clone https://github.com/L1nvx/htb-simple-gui.git
cd htb-simple-gui
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure your API token (optional for dev):
Create a `.env` file in the project root:
```bash
cp .env.example .env
```
Edit `.env` and add your HackTheBox API token.
Alternatively, the application will prompt you for the token on first run and save it to `~/.htb_client/config.json`.

4. Run the application:
```bash
python -m htb_gui.main
# or
python htb_gui/main.py
```

## Requirements

- Python 3.10+
- PySide6
- requests
- python-dotenv

## Screenshots

![](./image.png)

