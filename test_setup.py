#!/usr/bin/env python3
"""
Setup test script for HR Resume Assistant
Run this to verify your installation and API configuration
"""

import os
import sys
import requests
from dotenv import load_dotenv
import json

def print_header(title):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def print_step(step, message):
    print(f"\n{step}. {message}")

def print_success(message):
    print(f"   ✅ {message}")

def print_warning(message):
    print(f"   ⚠️  {message}")

def print_error(message):
    print(f"   ❌ {message}")

def test_python_modules():
    print_step(1, "Testing Python modules...")
    
    required_modules = {
        'flask': 'Flask',
        'requests': 'requests',
        'python-dotenv': 'dotenv'
    }
    
    all_good = True
    
    for module_name, import_name in required_modules.items():
        try:
            __import__(import_name.lower())
            print_success(f"{module_name} is installed")
        except ImportError:
            print_error(f"{module_name} is missing - run: pip install {module_name}")
            all_good = False
    
    return all_good

def test_environment_file():
    print_step(2, "Checking environment configuration...")
    
    # Load environment variables
    load_dotenv()
    
    # Check if .env file exists
    if os.path.exists('.env'):
        print_success(".env file found")
    else:
        print_warning(".env file not found - you can still use environment variables")
    
    # Check API key
    api_key = os.environ.get('DEEPSEEK_API_KEY')
    secret_key = os.environ.get('SECRET_KEY')
    
    if api_key and api_key != 'your-deepseek-api-key':
        print_success(f"DeepSeek API key is configured (ends with: ...{api_key[-4:]})")
        api_key_ok = True
    else:
        print_error("DeepSeek API key is not configured")
        print("   Please set DEEPSEEK_API_KEY in your .env file")
        print("   Get your API key at: https://platform.deepseek.com/api_keys")
        api_key_ok = False
    
    if secret_key and secret_key != 'your-secret-key-change-this':
        print_success("Flask secret key is configured")
    else:
        print_warning("Flask secret key not set - using default (not secure for production)")
    
    return api_key_ok, api_key

def test_deepseek_api(api_key):
    print_step(3, "Testing DeepSeek API connection...")
    
    if not api_key:
        print_error("Cannot test API - no API key configured")
        return False
    
    try:
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'model': 'deepseek-chat',
            'messages': [
                {"role": "system", "content": "You are a test assistant."},
                {"role": "user", "content": "Say 'Test successful' in exactly 2 words."}
            ],
            'max_tokens': 10,
            'temperature': 0
        }
        
        print("   Connecting to DeepSeek API...")
        response = requests.post(
            'https://api.deepseek.com/v1/chat/completions',
            headers=headers,
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'choices' in data and len(data['choices']) > 0:
                reply = data['choices'][0]['message']['content']
                print_success(f"API connection successful!")
                print_success(f"Test response: '{reply}'")
                return True
            else:
                print_error("API response format unexpected")
                return False
        elif response.status_code == 401:
            print_error("Invalid API key - check your DeepSeek API key")
            return False
        elif response.status_code == 429:
            print_warning("Rate limit exceeded - try again in a moment")
            return False
        else:
            print_error(f"API error: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print_error("API request timed out - check your internet connection")
        return False
    except requests.exceptions.ConnectionError:
        print_error("Connection error - check your internet connection")
        return False
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        return False

def test_flask_setup():
    print_step(4, "Testing Flask setup...")
    
    try:
        from flask import Flask
        app = Flask(__name__)
        print_success("Flask can be imported and initialized")
        return True
    except Exception as e:
        print_error(f"Flask setup error: {str(e)}")
        return False

def main():
    print_header("HR Resume Assistant - Setup Test")
    print("This script will verify your installation and configuration.")
    
    # Test 1: Python modules
    modules_ok = test_python_modules()
    
    # Test 2: Environment file
    env_ok, api_key = test_environment_file()
    
    # Test 3: DeepSeek API
    api_ok = test_deepseek_api(api_key) if api_key else False
    
    # Test 4: Flask setup
    flask_ok = test_flask_setup()
    
    # Summary
    print_header("Test Results Summary")
    
    if modules_ok and env_ok and api_ok and flask_ok:
        print_success("All tests passed! Your setup is ready.")
        print("\n🎉 You can now run the application with: python app.py")
    else:
        print("\n⚠️  Some issues were found:")
        
        if not modules_ok:
            print_error("Python modules missing - run: pip install -r requirements.txt")
        
        if not env_ok:
            print_error("Environment not configured properly")
            print("   Create a .env file with your DeepSeek API key")
        
        if not api_ok and api_key:
            print_error("API connection failed")
            print("   Check your API key and internet connection")
        
        if not flask_ok:
            print_error("Flask setup issue")
        
        print("\n📖 See README.md for detailed setup instructions")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main() 