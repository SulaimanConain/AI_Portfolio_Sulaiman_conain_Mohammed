from flask import Flask, request, render_template, jsonify, session, Response, redirect, url_for
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
    "title": "Data Engineer / Analyst",
    "contact": {
        "phone": "+91-7997059620",
        "email": "mohammedsulaimanconain@gmail.com",
        "github": "https://github.com/SulaimanConain?tab=repositories",
        "portfolio": "https://sulaimanconain.github.io/sulaimanconainmohammed/index.html"
    },
    "experience": [
        {
            "company": "Advance AI Lab",
            "location": "Toronto, ON",
            "role": "Data Engineer",
            "period": "Jun 2024 - Aug 2025",
            "highlights": [
                "Designed and implemented end-to-end Azure Data Engineering pipelines using Azure Data Factory, Azure Databricks, and Azure SQL DB with Medallion Architecture.",
                "Developed scalable data pipelines using audit logging and metadata-driven configuration, improving ingestion across hospitals and insurance providers.",
                "Engineered Delta Lake data models with SCD2 and CDM standards for historical accuracy and data lineage.",
                "Automated data quality validation and quarantine workflows within Silver layer, ensuring high-quality analytical data, reducing discrepancies.",
                "Enhanced data security via Azure Key Vault and streamlined governance with Unity Catalog.",
                "Optimized Azure Data Factory pipelines for parallel execution, cutting data processing time and latency.",
                "Implemented retry mechanisms and active/inactive flags for maintainable and scalable data architecture.",
                "Delivered fact and dimension tables enabling actionable revenue cycle KPIs."
            ]
        },
        {
            "company": "Advance AI Lab",
            "location": "Toronto, ON",
            "role": "Software Developer Intern",
            "period": "Sep 2023 - Jan 2024",
            "highlights": [
                "Developed and deployed full-stack Universal Translation application with Flask, SQLAlchemy, and MySQL.",
                "Implemented robust authentication with email verification, JWT, and role-based access control.",
                "Engineered RESTful APIs supporting real-time translation across 19+ languages.",
                "Integrated AI-powered contextual chat functionality.",
                "Containerized app deployment using Azure App Service and Gunicorn for scalability and high availability.",
                "Designed error handling system with detailed logging, achieving 99.9% uptime."
            ]
        },
        {
            "company": "IO-Solutions",
            "location": "Montreal, Canada",
            "role": "Voice and Non Voice Associate",
            "period": "Aug 2022 - Dec 2023",
            "highlights": [
                "Managed incoming sales inquiries converting leads effectively, enhancing revenue.",
                "Utilized CRM Maestro for customer interaction tracking and sales reporting.",
                "Collaborated with sales teams to upsell and cross-sell products, exceeding goals."
            ]
        },
        {
            "company": "Concordia University",
            "location": "Montreal, Canada",
            "role": "Programmer on Duty (Teaching Assistant)",
            "period": "Sept 2022 - Dec 2022",
            "highlights": [
                "Conducted POD sessions for COEN 6711 - Microprocessor-based systems."
            ]
        }
    ],
    "technical_summary": [
        "Data Engineering & Cloud Integration: Experienced in Azure Data Factory, Databricks, SQL technologies for scalable ETL workflows.",
        "Backend & Full-Stack Development: Skilled with Flask, FastAPI, Django, RESTful APIs, JWT authentication, and role-based access.",
        "Database Management & Optimization: Expertise in MySQL, T-SQL, SQLAlchemy; query optimization and indexing.",
        "Cloud Platforms & Deployment: Proficient with MS Azure services, Docker, Gunicorn deployment.",
        "Big Data & Analytics: Knowledge of Spark, Hive, Kafka; proficient in Pandas, Numpy, Plotly for data visualization."
    ],
    "education": [
        {"degree": "Master of Electrical and Computer Engineering", "school": "Concordia University, Montreal", "period": "Jan 2021 - Dec 2022"},
        {"degree": "Bachelor of Electronics and Communication Engineering", "school": "Osmania University, Hyderabad", "period": "Jun 2015 - Jul 2019"}
    ],
    "skills": [
        "C", "C++", "Python", "Matlab", "SSIS", "MySQL", "TSQL", "Microsoft Azure", "GitHub", "Git",
        "Hadoop HDFS", "Numpy", "Pandas", "Spark", "AWS", "Apache Hive", "Kafka", "Plotly",
        "Azure Data Factory", "Power BI", "Azure Databricks", "Snowflake", "Jupyter Notebook",
        "Glue", "Tableau", "PowerShell"
    ],
    "achievements": [
        "Received Regular Student award during the year 2015 at MJCET."
    ]
}

# Resume file configuration
RESUME_FILE_PATH = os.getenv('RESUME_FILE', os.path.join(os.path.dirname(__file__), 'content', 'resume.txt'))

def load_resume_from_file(file_path: str) -> str:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except Exception as e:
        print(f"Failed to load resume from {file_path}: {e}")
        return ""

def initialize_public_resume():
    resume_text = load_resume_from_file(RESUME_FILE_PATH)
    if resume_text:
        resumes_storage['public'] = {
            'resume_text': resume_text,
            'upload_timestamp': datetime.now().isoformat(),
            'chat_history': [],
            'uploader': 'system'
        }
        print(f"Public resume loaded from {RESUME_FILE_PATH} ({len(resume_text)} chars)")
    else:
        print(f"No resume loaded. Ensure resume exists at {RESUME_FILE_PATH}")

# Initialize at import time
initialize_public_resume()

@app.route('/')
def portfolio():
    """Public portfolio landing page with arcade feel"""
    return render_template('portfolio.html', data=PORTFOLIO_DATA)

@app.route('/public')
def public_chat():
    """Public chat page - accessible to everyone"""
    # Ensure default public session is set
    if 'public' not in resumes_storage or not resumes_storage['public'].get('resume_text'):
        return jsonify({'error': 'Resume not found. Please ensure content/resume.txt exists.'}), 500
    session['public_session_id'] = 'public'
    return render_template('public_chat.html')

@app.route('/upload', methods=['POST'])
def upload_resume():
    """Upload is disabled (admin removed)."""
    return jsonify({'error': 'Upload disabled'}), 403

# Removed admin chat. Public chat is the only mode.

@app.route('/chat/message', methods=['POST'])
def chat_message():
    """Handle chat messages and get AI responses (non-streaming fallback) - works for both admin and public"""
    try:
        # Public session only
        session_id = session.get('public_session_id') or 'public'
        
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
        # Public session only
        session_id = session.get('public_session_id') or 'public'
        
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
    """Reset only chat history for public session"""
    if 'public' in resumes_storage:
        resumes_storage['public']['chat_history'] = []
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
    print("Portfolio & Questions to Sulaiman Starting Up")
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
