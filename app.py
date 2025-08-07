from flask import Flask, request, render_template, jsonify, session, Response, stream_template, redirect, url_for, flash
import os
import requests
import json
from datetime import datetime
import uuid
import time
from functools import wraps
from dotenv import load_dotenv
import re

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-here')

# Hardcoded login credentials
ADMIN_CREDENTIALS = {
    'user_id': 'sulaiman',
    'password': 'admin'
}

# In-memory storage for resumes and chat history
resumes_storage = {}

# DeepSeek API configuration
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

# Check if API key is configured on startup
if not DEEPSEEK_API_KEY:
    print("WARNING: DEEPSEEK_API_KEY not found in environment variables!")
    print("Please add your API key to the .env file")

# -----------------------------------------------------------------------------
# Portfolio content (sourced from user's resume)
# -----------------------------------------------------------------------------
PORTFOLIO_DATA = {
    "name": "Sulaiman Conain Mohammed",
    "title": "AI-Enabled Full-Stack Developer & Data Systems Analyst",
    "contact": {
        "phone": "+1 (514) 746-9977",
        "email": "mohammedsulaimanconain@gmail.com",
        # Links can be added here if available, e.g., "github": "https://github.com/<username>",
    },
    "experience": [
        {
            "company": "Advance AI Lab",
            "location": "Toronto, ON",
            "role": "Software Developer",
            "period": "Sep 2023 - Present",
            "highlights": [
                "Designed and developed a web-based multilingual translation platform for providers and patients across 20+ languages.",
                "Built backend services using FastAPI with async support for real-time translation at scale.",
                "Integrated DeepSeek AI API with caching and fallback logic for resilience and performance.",
                "Implemented OAuth2, JWT, and secure password hashing with passlib.",
                "Designed normalized SQLite schemas and optimized queries for translation data handling.",
                "Developed RESTful APIs for translation, multilingual chat, batch processing, and medical summaries.",
                "Implemented email verification and password reset flows using FastAPI BackgroundTasks and secure tokens.",
                "Created responsive UI with Jinja2, Bootstrap, and vanilla JavaScript.",
                "Focused on accessibility, data privacy, and scalability; explored cloud deployment patterns."
            ]
        },
        {
            "company": "IO Solutions inc",
            "location": "Montreal, QC",
            "role": "Python Software Developer",
            "period": "Aug 2022 – Oct 2023",
            "highlights": [
                "Designed and deployed a scalable REST API backend using Django REST Framework for a job-matching platform.",
                "Built a real-time applicant tracking dashboard with Flask and Socket.IO.",
                "Implemented JWT auth and role-based permissions; created reusable components and middleware.",
                "Automated resume parsing and keyword extraction with spaCy/NLTK into PostgreSQL.",
                "Integrated Celery and Redis for background tasks, improving response times by 60%.",
                "Deployed on Heroku and AWS EC2 with Nginx and Gunicorn; set up CI/CD with GitHub Actions.",
                "Ensured GDPR-compliant data handling and dynamic localization for recruiters and job seekers."
            ]
        },
        {
            "company": "Concordia University",
            "location": "Montreal, QC",
            "role": "Programmer on Duty (TA)",
            "period": "Sept 2022 – Dec 2022",
            "highlights": [
                "Conducted POD sessions for COEN 6711 – Microprocessor-based systems.",
                "Guided students on interrupts, PWM, sensor interfacing, and serial protocols (I2C, UART, SPI).",
                "Mentored projects: obstacle-avoidance robot, IoT home automation, Raspberry Pi self-driving car."
            ]
        }
    ],
    "technical_summary": [
        "Backend & Full-Stack: C#.NET, ASP.NET Core, Entity Framework, Python, Flask, Django; REST APIs; JWT/session auth; RBAC; Frontend with AngularJS, Bootstrap, JS.",
        "Database: SQL Server, PostgreSQL; complex queries and stored procedures; ORM (EF, Django ORM); Redis caching.",
        "Cloud & DevOps: IIS, Heroku, AWS EC2; Docker; Nginx/Gunicorn; CI/CD with GitHub Actions; secure config via .env/Azure Key Vault.",
        "ETL & Automation: Python, Celery; async tasks (email, language detection, resume parsing); translation caching; batch/concurrent processing.",
        "AI & NLP: LLM API integrations; spaCy, langdetect; conversation summarization; language detection; multilingual chat.",
        "Security & Testing: Auth flows, account verification, password recovery; logging, exception handling, middleware validation."
    ],
    "education": [
        {"degree": "MEng, Electrical and Computer Engineering", "school": "Concordia University, Montreal", "period": "Jan 2021 – Dec 2022"},
        {"degree": "BEng, Electronics and Computer Engineering", "school": "Osmania University, Hyderabad", "period": "Jun 2015 – Jul 2019"}
    ],
    "skills": [
        "Python", "C#", "JavaScript", "ASP.NET", ".NET Core", "Shell", "Matlab", "SSIS", "MySQL", "TSQL",
        "Azure", "GitHub", "Git", "Hadoop HDFS", "NumPy", "Pandas", "Spark", "AWS", "Hive", "Kafka",
        "Plotly", "ADF", "Power BI", "Databricks", "Snowflake", "Jupyter", "Glue", "Tableau", "PowerShell"
    ],
    "achievements": [
        "Regular Student award (2015).",
        "DP-203: Microsoft Certified Azure Data Engineer."
    ]
}

def require_login(f):
    """Decorator to require login for certain routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session or not session['logged_in']:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login"""
    if request.method == 'POST':
        user_id = request.form.get('user_id', '').strip()
        password = request.form.get('password', '').strip()
        
        if user_id == ADMIN_CREDENTIALS['user_id'] and password == ADMIN_CREDENTIALS['password']:
            session['logged_in'] = True
            session['user_id'] = user_id
            flash('Login successful! Welcome back, Sulaiman.', 'success')
            return redirect(url_for('admin_upload'))
        else:
            flash('Invalid credentials. Please try again.', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Handle user logout"""
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('public_chat'))

@app.route('/')
def portfolio():
    """Public portfolio landing page with arcade feel"""
    return render_template('portfolio.html', data=PORTFOLIO_DATA)

@app.route('/admin/upload')
@require_login
def admin_upload():
    """Main upload page - requires login"""
    return render_template('index.html')

@app.route('/public')
def public_chat():
    """Public chat page - accessible to everyone"""
    # Check if there's any resume uploaded
    if not resumes_storage:
        return render_template('no_resume.html')
    
    # Get the latest resume (assuming single resume for now)
    latest_session = list(resumes_storage.keys())[-1] if resumes_storage else None
    
    if latest_session:
        # Set session for public users to use the latest resume
        session['public_session_id'] = latest_session
        return render_template('public_chat.html', 
                             resume_info=resumes_storage[latest_session])
    else:
        return render_template('no_resume.html')

@app.route('/upload', methods=['POST'])
@require_login
def upload_resume():
    """Handle resume upload - protected route"""
    try:
        print(f"Upload request received. Form data: {request.form}")
        print(f"Session logged_in: {session.get('logged_in')}")
        print(f"Session user_id: {session.get('user_id')}")
        
        resume_text = request.form.get('resumeText', '').strip()
        
        if not resume_text:
            print("Error: No resume text provided")
            return jsonify({'error': 'Please provide resume text'}), 400
        
        if len(resume_text) < 50:
            print(f"Error: Resume too short. Length: {len(resume_text)}")
            return jsonify({'error': 'Resume text seems too short. Please provide a complete resume.'}), 400
        
        # Generate session ID and store resume
        session_id = str(uuid.uuid4())
        session['session_id'] = session_id
        
        resumes_storage[session_id] = {
            'resume_text': resume_text,
            'upload_timestamp': datetime.now().isoformat(),
            'chat_history': [],
            'uploader': session['user_id']
        }
        
        print(f"Resume uploaded successfully. Session ID: {session_id}")
        
        return jsonify({
            'success': True,
            'message': 'Resume uploaded successfully!',
            'session_id': session_id,
            'admin_chat_url': '/chat',
            'public_chat_url': '/public'
        })
        
    except Exception as e:
        print(f"Upload error: {str(e)}")
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

@app.route('/chat')
@require_login
def chat():
    """Private chat page for admin"""
    session_id = session.get('session_id')
    if not session_id or session_id not in resumes_storage:
        flash('No resume found. Please upload a resume first.', 'warning')
        return redirect(url_for('index'))
    
    return render_template('chat.html', is_admin=True)

@app.route('/chat/message', methods=['POST'])
def chat_message():
    """Handle chat messages and get AI responses (non-streaming fallback) - works for both admin and public"""
    try:
        # Check if user is admin or public
        session_id = session.get('session_id') or session.get('public_session_id')
        
        if not session_id or session_id not in resumes_storage:
            return jsonify({'error': 'No active session. Please access the chat properly.'}), 400
        
        user_message = request.json.get('message', '').strip()
        if not user_message:
            return jsonify({'error': 'Please provide a message'}), 400
        
        resume_data = resumes_storage[session_id]
        resume_text = resume_data['resume_text']
        
        # Create context for the AI
        system_prompt = f"""You are an AI assistant representing a job candidate based on their resume. 
        You should answer questions as if you are the candidate, using the information from their resume.
        Be professional, confident, and elaborate on the experiences mentioned in the resume.
        
        CANDIDATE'S RESUME:
        {resume_text}
        
        Instructions:
        - Answer as the candidate in first person
        - Be specific about experiences mentioned in the resume
        - If asked about something not in the resume, politely mention it's not covered in your background
        - Be enthusiastic and professional
        - Provide detailed responses that showcase the candidate's qualifications"""
        
        # Prepare messages for DeepSeek API
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        
        # Add chat history for context
        for chat in resume_data['chat_history'][-5:]:  # Last 5 exchanges for context
            messages.append({"role": "user", "content": chat['user_message']})
            messages.append({"role": "assistant", "content": chat['ai_response']})
        
        messages.append({"role": "user", "content": user_message})
        
        # Call DeepSeek API
        response = call_deepseek_api(messages)
        
        if response:
            # Store chat history (even if it's an error message from API)
            resume_data['chat_history'].append({
                'user_message': user_message,
                'ai_response': response,
                'timestamp': datetime.now().isoformat()
            })
            
            return jsonify({'response': response})
        else:
            # This means the API call completely failed (returned None)
            return jsonify({'error': 'Failed to get AI response. Please check your internet connection and try again.'}), 500
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/chat/stream', methods=['POST'])
def chat_stream():
    """Handle chat messages with streaming responses - works for both admin and public"""
    try:
        # Check if user is admin or public
        session_id = session.get('session_id') or session.get('public_session_id')
        
        if not session_id or session_id not in resumes_storage:
            return jsonify({'error': 'No active session. Please access the chat properly.'}), 400
        
        user_message = request.json.get('message', '').strip()
        if not user_message:
            return jsonify({'error': 'Please provide a message'}), 400
        
        def generate_response():
            try:
                resume_data = resumes_storage[session_id]
                resume_text = resume_data['resume_text']
                
                # Create context for the AI
                system_prompt = f"""You are an AI assistant representing a job candidate based on their resume. 
                You should answer questions as if you are the candidate, using the information from their resume.
                Be professional, confident, and elaborate on the experiences mentioned in the resume.
                
                CANDIDATE'S RESUME:
                {resume_text}
                
                Instructions:
                - Answer as the candidate in first person
                - Be specific about experiences mentioned in the resume
                - If asked about something not in the resume, politely mention it's not covered in your background
                - Be enthusiastic and professional
                - Provide detailed responses that showcase the candidate's qualifications"""
                
                # Prepare messages for DeepSeek API
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ]
                
                # Add chat history for context
                for chat in resume_data['chat_history'][-5:]:  # Last 5 exchanges for context
                    messages.append({"role": "user", "content": chat['user_message']})
                    messages.append({"role": "assistant", "content": chat['ai_response']})
                
                messages.append({"role": "user", "content": user_message})
                
                # Stream response from DeepSeek API
                full_response = ""
                for chunk in call_deepseek_api_streaming(messages):
                    if chunk:
                        full_response += chunk
                        # Send chunk as Server-Sent Event
                        yield f"data: {json.dumps({'chunk': chunk, 'type': 'chunk'})}\n\n"
                
                # Store complete response in chat history
                if full_response:
                    resume_data['chat_history'].append({
                        'user_message': user_message,
                        'ai_response': full_response,
                        'timestamp': datetime.now().isoformat()
                    })
                    
                # Send completion signal
                yield f"data: {json.dumps({'type': 'complete', 'full_response': full_response})}\n\n"
                
            except Exception as e:
                print(f"Error in streaming: {str(e)}")
                yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
        
        return Response(
            generate_response(),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'Access-Control-Allow-Origin': '*',
                'X-Accel-Buffering': 'no'  # Disable nginx buffering
            }
        )
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def retry_api_call(max_retries=3, delay=1):
    """Retry decorator for API calls with exponential backoff"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                    if attempt == max_retries - 1:  # Last attempt
                        print(f"API call failed after {max_retries} attempts: {str(e)}")
                        return None
                    
                    wait_time = delay * (2 ** attempt)  # Exponential backoff
                    print(f"API timeout (attempt {attempt + 1}/{max_retries}), retrying in {wait_time}s...")
                    time.sleep(wait_time)
                except Exception as e:
                    print(f"Unexpected error in API call: {str(e)}")
                    return None
            return None
        return wrapper
    return decorator

@retry_api_call(max_retries=3, delay=2)
def call_deepseek_api(messages):
    """Call DeepSeek API to get AI response with retry logic"""
    try:
        # Validate API key
        if not DEEPSEEK_API_KEY or DEEPSEEK_API_KEY == 'your-deepseek-api-key':
            print("Error: DeepSeek API key not configured properly")
            return "I apologize, but the AI service is not properly configured. Please check the API key settings."
        
        headers = {
            'Authorization': f'Bearer {DEEPSEEK_API_KEY}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        payload = {
            'model': 'deepseek-chat',
            'messages': messages,
            'temperature': 0.7,
            'max_tokens': 1500,
            'top_p': 0.9,
            'frequency_penalty': 0.1,
            'presence_penalty': 0.1
        }
        
        print(f"Making API request to DeepSeek with {len(messages)} messages...")
        
        # Increased timeout and added connection timeout
        response = requests.post(
            DEEPSEEK_API_URL, 
            headers=headers, 
            json=payload, 
            timeout=(10, 60)  # (connection timeout, read timeout)
        )
        
        print(f"API response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if 'choices' in data and len(data['choices']) > 0:
                content = data['choices'][0]['message']['content']
                print(f"API response received: {len(content)} characters")
                return content
            else:
                print("Error: No choices in API response")
                return "I apologize, but I couldn't generate a proper response. Please try again."
                
        elif response.status_code == 401:
            print("Error: Invalid API key")
            return "I apologize, but there's an authentication issue. Please check the API key configuration."
            
        elif response.status_code == 429:
            print("Error: Rate limit exceeded")
            return "I apologize, but the service is currently experiencing high demand. Please try again in a moment."
            
        else:
            print(f"DeepSeek API error: {response.status_code} - {response.text}")
            return f"I apologize, but I'm experiencing technical difficulties (Error {response.status_code}). Please try again."
    
    except requests.exceptions.Timeout:
        print("Error: Request timed out")
        raise  # Let the retry decorator handle this
    
    except requests.exceptions.ConnectionError:
        print("Error: Connection failed")
        raise  # Let the retry decorator handle this
        
    except Exception as e:
        print(f"Unexpected error calling DeepSeek API: {str(e)}")
        return "I apologize, but I encountered an unexpected error. Please try again."

def call_deepseek_api_streaming(messages):
    """Call DeepSeek API with streaming support"""
    try:
        # Validate API key
        if not DEEPSEEK_API_KEY or DEEPSEEK_API_KEY == 'your-deepseek-api-key':
            print("Error: DeepSeek API key not configured properly")
            yield "I apologize, but the AI service is not properly configured. Please check the API key settings."
            return
        
        headers = {
            'Authorization': f'Bearer {DEEPSEEK_API_KEY}',
            'Content-Type': 'application/json',
            'Accept': 'text/event-stream'
        }
        
        payload = {
            'model': 'deepseek-chat',
            'messages': messages,
            'temperature': 0.7,
            'max_tokens': 1500,
            'top_p': 0.9,
            'frequency_penalty': 0.1,
            'presence_penalty': 0.1,
            'stream': True  # Enable streaming
        }
        
        print(f"Making streaming API request to DeepSeek with {len(messages)} messages...")
        
        # Make streaming request
        response = requests.post(
            DEEPSEEK_API_URL, 
            headers=headers, 
            json=payload, 
            stream=True,
            timeout=(10, 60)
        )
        
        print(f"Streaming API response status: {response.status_code}")
        
        if response.status_code == 200:
            # Process streaming response
            for line in response.iter_lines(decode_unicode=True):
                if line:
                    # Handle Server-Sent Events format
                    if line.startswith('data: '):
                        data_str = line[6:]  # Remove 'data: ' prefix
                        
                        # Handle end of stream
                        if data_str.strip() == '[DONE]':
                            break
                        
                        try:
                            # Parse JSON chunk
                            chunk_data = json.loads(data_str)
                            
                            # Extract content from the chunk
                            if 'choices' in chunk_data and len(chunk_data['choices']) > 0:
                                delta = chunk_data['choices'][0].get('delta', {})
                                content = delta.get('content', '')
                                
                                if content:
                                    yield content
                                    
                        except json.JSONDecodeError:
                            # Skip invalid JSON chunks
                            continue
                        
        elif response.status_code == 401:
            print("Error: Invalid API key")
            yield "I apologize, but there's an authentication issue. Please check the API key configuration."
            
        elif response.status_code == 429:
            print("Error: Rate limit exceeded")
            yield "I apologize, but the service is currently experiencing high demand. Please try again in a moment."
            
        else:
            print(f"DeepSeek API error: {response.status_code} - {response.text}")
            yield f"I apologize, but I'm experiencing technical difficulties (Error {response.status_code}). Please try again."
    
    except requests.exceptions.Timeout:
        print("Error: Streaming request timed out")
        yield "I apologize, but the request timed out. Please try again."
    
    except requests.exceptions.ConnectionError:
        print("Error: Streaming connection failed")
        yield "I apologize, but there was a connection error. Please check your internet connection and try again."
        
    except Exception as e:
        print(f"Unexpected error in streaming API call: {str(e)}")
        yield "I apologize, but I encountered an unexpected error. Please try again."

@app.route('/reset')
def reset_session():
    """Reset the current session"""
    session_id = session.get('session_id')
    if session_id and session_id in resumes_storage:
        del resumes_storage[session_id]
    session.clear()
    return jsonify({'success': True})

@app.route('/health')
def health_check():
    """Health check endpoint to verify API configuration"""
    try:
        # Basic health check
        status = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'api_configured': bool(DEEPSEEK_API_KEY and DEEPSEEK_API_KEY != 'your-deepseek-api-key'),
            'active_sessions': len(resumes_storage)
        }
        
        # Test API connectivity (optional)
        if status['api_configured']:
            try:
                test_messages = [
                    {"role": "system", "content": "You are a test assistant."},
                    {"role": "user", "content": "Say 'API test successful' in exactly 3 words."}
                ]
                
                # Quick test with minimal timeout
                headers = {
                    'Authorization': f'Bearer {DEEPSEEK_API_KEY}',
                    'Content-Type': 'application/json'
                }
                
                payload = {
                    'model': 'deepseek-chat',
                    'messages': test_messages,
                    'max_tokens': 10
                }
                
                response = requests.post(
                    DEEPSEEK_API_URL, 
                    headers=headers, 
                    json=payload, 
                    timeout=5
                )
                
                status['api_test'] = 'success' if response.status_code == 200 else f'failed_{response.status_code}'
                
            except Exception as e:
                status['api_test'] = f'error_{str(e)[:50]}'
        else:
            status['api_test'] = 'not_configured'
        
        return jsonify(status)
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

if __name__ == '__main__':
    # Check configuration on startup
    print("=" * 50)
    print("HR Resume Assistant Starting Up")
    print("=" * 50)
    
    if not DEEPSEEK_API_KEY or DEEPSEEK_API_KEY == 'your-deepseek-api-key':
        print("⚠️  WARNING: DeepSeek API key not configured!")
        print("   Please set DEEPSEEK_API_KEY in your .env file")
        print("   Get your API key at: https://platform.deepseek.com/api_keys")
    else:
        print(f"✅ DeepSeek API key configured (ends with: ...{DEEPSEEK_API_KEY[-4:]})")
    
    print(f"🌐 Server will start at: http://localhost:5000")
    print(f"🔧 Debug mode: {'ON' if app.debug else 'OFF'}")
    print("=" * 50)
    
    app.run(debug=True, host='0.0.0.0', port=5000) 