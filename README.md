# Script Management Dashboard

A simple, beautiful dashboard for managing Python scripts with real-time monitoring and Telegram notifications.

## Features

- **Real-time Script Management**: Start/stop Python scripts with live status updates
- **Multi-script Support**: Run multiple scripts simultaneously 
- **Live Log Streaming**: View real-time output from running scripts
- **Telegram Notifications**: Get notified when scripts complete or fail
- **Beautiful UI**: Modern, responsive design with smooth animations

## Quick Start

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Telegram (Optional)**
   - Create a Telegram bot by messaging `@BotFather`
   - Get your chat ID by messaging `@userinfobot`
   - Update the `.env` file with your credentials

3. **Run the Application**
   ```bash
   python main.py
   ```

4. **Access the Dashboard**
   Open your browser to `http://localhost:8000`

## Usage

- Add Python scripts to the `scripts/` directory
- Use the dashboard to start/stop scripts and view logs
- Scripts will send Telegram notifications when they complete or fail

## File Structure
```
├── main.py              # FastAPI application
├── config.py           # Configuration management
├── requirements.txt    # Python dependencies
├── .env               # Environment variables
├── templates/         # HTML templates
│   ├── base.html
│   ├── dashboard.html
│   └── components/
└── scripts/          # Your Python scripts go here
```

That's it! Simple, clean, and functional.