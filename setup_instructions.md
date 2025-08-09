# Script Management Dashboard Setup

## Overview
A beautiful, production-ready dashboard for managing Python scripts with real-time monitoring, log streaming, and Telegram notifications.

## Quick Start

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Telegram (Optional but Recommended)**
   - Create a Telegram bot by messaging `@BotFather`
   - Get your chat ID by messaging `@userinfobot`
   - Update the `.env` file with your credentials:
   ```
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   TELEGRAM_CHAT_ID=your_chat_id_here
   ```

3. **Run the Application**
   ```bash
   python main.py
   ```
   Or using uvicorn:
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

4. **Access the Dashboard**
   Open your browser to `http://localhost:8000`

## Features

### ✨ Core Features
- **Real-time Script Management**: Start/stop Python scripts with live status updates
- **Multi-script Support**: Run multiple scripts simultaneously with process isolation
- **Live Log Streaming**: View real-time output from running scripts
- **Telegram Notifications**: Get notified when scripts complete or fail
- **Beautiful UI**: Modern, responsive design with smooth animations

### 🎯 Technical Features
- **HTMX Integration**: Dynamic updates without JavaScript complexity
- **Process Management**: Robust subprocess handling with graceful termination
- **Error Handling**: Comprehensive error management and user feedback
- **Auto-refresh**: Scripts list and logs update automatically
- **Mobile Responsive**: Works perfectly on all device sizes

## File Structure
```
app/
├── main.py                 # FastAPI application
├── config.py              # Configuration management
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables
├── templates/
│   ├── base.html         # Base template
│   ├── dashboard.html    # Main dashboard
│   └── components/
│       └── script_list.html  # Script list component
└── scripts/              # Your Python scripts go here
    ├── example_counter.py
    ├── example_data_processor.py
    ├── example_web_scraper.py
    └── example_failing_script.py
```

## Usage

### Adding Scripts
1. Place your Python scripts in the `scripts/` directory
2. Make sure they have a `.py` extension
3. Scripts should include proper logging with `print()` statements
4. The dashboard will automatically detect new scripts

### Managing Scripts
- **Start**: Click the green "Start" button next to any script
- **Stop**: Click the red "Stop" button for running scripts
- **View Logs**: Click "Logs" to see real-time output in a modal
- **Status**: Watch the colored status indicators (green=running, gray=stopped)

### Telegram Integration
Once configured, you'll receive notifications for:
- ✅ Script started
- 🎉 Script completed successfully
- ❌ Script failed with error
- ⏹️ Script manually stopped

## Configuration Options

Edit `.env` file to customize:
- `TELEGRAM_BOT_TOKEN`: Your Telegram bot token
- `TELEGRAM_CHAT_ID`: Your Telegram chat ID
- `SCRIPTS_DIR`: Directory containing scripts (default: "scripts")
- `MAX_LOG_LINES`: Maximum log lines to store (default: 1000)
- `DEBUG`: Enable debug mode (default: False)

## API Endpoints

- `GET /` - Main dashboard
- `GET /scripts` - Get script list (HTMX)
- `POST /scripts/{name}/start` - Start a script
- `POST /scripts/{name}/stop` - Stop a script
- `GET /scripts/{name}/logs` - Get script logs
- `GET /scripts/{name}/status` - Get script status

## Troubleshooting

### Common Issues
1. **Scripts not appearing**: Ensure they're in the `scripts/` directory with `.py` extension
2. **Telegram not working**: Verify bot token and chat ID in `.env`
3. **Port conflicts**: Change the port in `main.py` if needed
4. **Permission errors**: Ensure scripts are readable and executable

### Best Practices
- Add proper logging to your scripts using `print()` statements
- Handle errors gracefully in your scripts
- Use meaningful script names
- Test scripts manually before adding them to the dashboard
- Keep scripts focused on single tasks for better monitoring

## Development

To run in development mode:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The application will automatically reload when you make changes to the code.

## Security Notes
- The dashboard runs on all interfaces (0.0.0.0) by default
- In production, consider running behind a reverse proxy
- Telegram credentials should be kept secure
- Scripts run with the same permissions as the web server

Enjoy managing your Python scripts with this beautiful dashboard! 🚀