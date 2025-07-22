# HR Resume Assistant

A professional Flask application that allows users to upload their resumes, enabling HR managers to interact with an AI chatbot that represents the candidate and can answer questions on their behalf..

## Features

- **Resume Upload**: Simple interface for uploading candidate resumes in plain text
- **AI-Powered Chat**: Interactive chatbot powered by DeepSeek AI that responds as the candidate
- **Professional UI**: Modern, responsive design with Bootstrap and custom styling
- **Real-time Chat**: Smooth messaging experience with typing indicators and animations
- **Quick Questions**: Pre-defined interview questions for efficient screening
- **Session Management**: Secure session handling for multiple concurrent interviews

## Screenshots

### Upload Interface
Professional resume upload interface with validation and character counting.

### Chat Interface
Interactive chat with AI assistant representing the candidate.

## Setup Instructions

### 1. Prerequisites
- Python 3.8 or higher
- DeepSeek API account and API key

### 2. Installation

1. **Clone or download the project files**

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   
   Create a `.env` file in the project root:
   ```bash
   # DeepSeek API Configuration
   DEEPSEEK_API_KEY=your-deepseek-api-key-here
   
   # Flask Configuration
   SECRET_KEY=your-secret-key-for-sessions
   FLASK_ENV=development
   ```

   **To get your DeepSeek API key:**
   - Visit [DeepSeek API](https://platform.deepseek.com)
   - Sign up for an account
   - Navigate to API Keys section
   - Generate a new API key
   - Copy the key to your `.env` file

4. **Test your setup (recommended)**
   ```bash
   python test_setup.py
   ```
   This will verify your installation and API configuration.

5. **Run the application**
   ```bash
   python app.py
   ```

6. **Open your browser**
   - Navigate to `http://localhost:5000`
   - Start using the HR Resume Assistant!

## Usage Guide

### For HR Managers

1. **Upload a Resume**
   - Go to the home page
   - Paste the candidate's resume text into the form
   - Click "Upload & Start Interview Assistant"

2. **Start Interviewing**
   - Once uploaded, you'll be redirected to the chat interface
   - Ask questions about the candidate's experience, skills, and background
   - The AI will respond as if it were the candidate

3. **Interview Tips**
   - Use the suggested questions in the sidebar for common interview topics
   - Ask specific questions about technologies, projects, and experiences
   - The AI has access to all information in the uploaded resume

### Sample Questions

- "Tell me about your most recent work experience"
- "What programming languages are you most comfortable with?"
- "Describe a challenging project you worked on"
- "How do you approach learning new technologies?"
- "What motivates you in your work?"

## API Configuration

### DeepSeek API Integration

This application uses the DeepSeek API for natural language processing. The AI is configured to:

- Respond as the candidate based on their resume
- Provide detailed, professional answers
- Stay within the context of the provided resume information
- Maintain a professional, interview-appropriate tone

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DEEPSEEK_API_KEY` | Your DeepSeek API key | Yes |
| `SECRET_KEY` | Flask session secret key | Yes |
| `FLASK_ENV` | Flask environment (development/production) | No |

## Technical Architecture

### Backend (Flask)
- **app.py**: Main Flask application with API routes
- **Session Management**: In-memory storage for demo purposes
- **API Integration**: DeepSeek API for AI responses
- **Error Handling**: Comprehensive error handling and logging

### Frontend
- **HTML Templates**: Jinja2 templates with Bootstrap 5
- **CSS**: Custom professional styling with animations
- **JavaScript**: Modern ES6+ with classes and async/await
- **Responsive Design**: Mobile-first approach

### File Structure
```
hr-resume-assistant/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── .env                  # Environment variables (create this)
├── templates/            # HTML templates
│   ├── base.html         # Base template
│   ├── index.html        # Upload interface
│   ├── chat.html         # Chat interface
│   └── error.html        # Error page
└── static/               # Static assets
    ├── css/
    │   └── style.css     # Custom styling
    └── js/
        ├── main.js       # Common utilities
        ├── upload.js     # Upload functionality
        └── chat.js       # Chat functionality
```

## Features in Detail

### Resume Upload
- **Validation**: Real-time validation with character counting
- **Content Analysis**: Checks for common resume sections
- **Auto-resize**: Dynamic textarea sizing
- **Visual Feedback**: Clear success/error states

### Chat Interface
- **Real-time Messaging**: Smooth message sending and receiving
- **Typing Indicators**: Shows when AI is processing
- **Message Formatting**: Supports basic markdown formatting
- **Keyboard Shortcuts**: Enter to send, Shift+Enter for new line
- **Quick Questions**: One-click interview questions
- **Chat History**: Maintains conversation context

### Professional Design
- **Modern UI**: Clean, professional interface
- **Responsive**: Works on desktop, tablet, and mobile
- **Accessibility**: WCAG compliant design elements
- **Animations**: Subtle animations for better UX
- **Toast Notifications**: Non-intrusive status messages

## Customization

### Adding New Quick Questions
Edit `templates/chat.html` and add new buttons in the sidebar:

```html
<button class="btn btn-outline-primary btn-sm text-start quick-question"
        data-question="Your custom question here">
    <i class="fas fa-icon me-2"></i>Question Title
</button>
```

### Styling Changes
Modify `static/css/style.css` to customize:
- Colors (CSS custom properties in `:root`)
- Layout spacing and sizing
- Animation effects
- Responsive breakpoints

### API Customization
In `app.py`, you can modify the system prompt to change how the AI responds:
- Adjust the professional tone
- Add specific instructions
- Modify the response format

## Security Notes

- **Environment Variables**: Never commit `.env` files to version control
- **API Keys**: Keep your DeepSeek API key secure
- **Production**: Use a proper database and session storage in production
- **HTTPS**: Always use HTTPS in production environments

## Troubleshooting

### API Connection Issues

If you're experiencing timeout errors or connection issues:

1. **Test API Connection**
   - Use the "Test API" button in the chat interface
   - Check `/health` endpoint at `http://localhost:5000/health`
   - Look for detailed error messages in the Flask console

2. **Timeout Errors**
   - The app automatically retries failed requests up to 3 times
   - Timeout errors are common during high traffic periods
   - Wait a moment and try again
   - Check your internet connection stability

3. **DeepSeek API Status**
   - Visit [DeepSeek API Status](https://status.deepseek.com) to check for outages
   - Verify your API key at [platform.deepseek.com](https://platform.deepseek.com)
   - Check your account's API usage limits and credits

### Common Issues

1. **API Key Not Working**
   - Verify your DeepSeek API key is correct
   - Check that you have sufficient API credits
   - Ensure the key is properly set in the `.env` file
   - Use the "Test API" button to verify connectivity

2. **Connection Timeouts**
   - Error: `HTTPSConnectionPool(host='api.deepseek.com', port=443): Read timed out`
   - **Solution**: This is normal during high traffic. The app will retry automatically
   - Wait 10-30 seconds and try again
   - Use shorter messages to reduce processing time

3. **Module Not Found**
   - Run `pip install -r requirements.txt`
   - Ensure you're using the correct Python environment
   - Try upgrading pip: `pip install --upgrade pip`

4. **Chat Not Responding**
   - Check browser console for JavaScript errors
   - Verify the DeepSeek API is accessible using the Test API button
   - Check Flask logs for detailed error messages
   - Restart the Flask server

5. **Styling Issues**
   - Clear browser cache (Ctrl+F5 or Cmd+Shift+R)
   - Check that static files are being served correctly
   - Verify Bootstrap CDN is accessible
   - Check browser developer tools for CSS errors

### Debug Commands

```bash
# Test your configuration
curl http://localhost:5000/health

# Check if the server is responding
curl http://localhost:5000/

# Test with verbose output
python app.py
```

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Verify your environment setup matches the requirements
3. Check the Flask application logs for specific errors

## License

This project is provided as-is for educational and professional use.

---

**Built with ❤️ using Flask, Bootstrap, and DeepSeek AI** 
