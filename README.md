# HTB Desktop Client

## Installation

### 1. Clone the repository
```bash
git clone https://github.com/L1nvx/htb-simple-gui.git
cd htb-simple-gui
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure your API token

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` and add your HackTheBox API token:
```
HTB_API_TOKEN=your_api_token_here
HTB_DEBUG=false
```

> Get your API token from: https://app.hackthebox.com/profile/settings

### 4. Run the application
```bash
python main.py
```

## Requirements

- Python 3.10+
- PySide6
- requests
- python-dotenv

## Screenshots

![](./image.png)

