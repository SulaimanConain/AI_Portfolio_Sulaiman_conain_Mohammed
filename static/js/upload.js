/**
 * Upload functionality for HR Resume Assistant
 * Handles resume upload form submission and validation
 */

class ResumeUploader {
    constructor() {
        this.form = document.getElementById('uploadForm');
        this.textarea = document.getElementById('resumeText');
        this.uploadBtn = document.getElementById('uploadBtn');
        this.resultDiv = document.getElementById('uploadResult');
        
        this.init();
    }

    init() {
        if (!this.form || !this.textarea || !this.uploadBtn) {
            console.error('Upload form elements not found');
            return;
        }

        this.setupEventListeners();
        this.setupFormValidation();
        console.log('Resume uploader initialized');
    }

    setupEventListeners() {
        // Form submission
        this.form.addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleUpload();
        });

        // Real-time character count and validation
        this.textarea.addEventListener('input', () => {
            this.updateCharacterCount();
            this.validateInput();
        });

        // Paste detection for better UX
        this.textarea.addEventListener('paste', (e) => {
            setTimeout(() => {
                this.validateInput();
                window.resumeAssistant.showToast('Resume content pasted! Please review and submit.', 'info');
            }, 100);
        });

        // Auto-resize textarea
        this.textarea.addEventListener('input', this.autoResizeTextarea.bind(this));
    }

    setupFormValidation() {
        // Add character count display
        this.addCharacterCounter();
        
        // Initial validation
        this.validateInput();
    }

    addCharacterCounter() {
        const counterDiv = document.createElement('div');
        counterDiv.className = 'character-counter mt-2';
        counterDiv.innerHTML = `
            <small class="text-muted">
                <span id="charCount">0</span> characters
                <span class="text-success ms-2" id="validationStatus">
                    <i class="fas fa-info-circle"></i> Please enter resume content
                </span>
            </small>
        `;
        
        this.textarea.parentNode.appendChild(counterDiv);
        this.charCountSpan = document.getElementById('charCount');
        this.validationStatus = document.getElementById('validationStatus');
    }

    updateCharacterCount() {
        const count = this.textarea.value.length;
        if (this.charCountSpan) {
            this.charCountSpan.textContent = count.toLocaleString();
        }
    }

    validateInput() {
        const content = this.textarea.value.trim();
        const minLength = 100; // Minimum meaningful resume length
        
        this.updateCharacterCount();

        if (!content) {
            this.setValidationStatus('Please enter resume content', 'info', 'fa-info-circle');
            this.uploadBtn.disabled = true;
            return false;
        }

        if (content.length < minLength) {
            this.setValidationStatus(`Too short - need at least ${minLength} characters`, 'warning', 'fa-exclamation-triangle');
            this.uploadBtn.disabled = true;
            return false;
        }

        // Check for basic resume components
        const hasBasicInfo = this.checkResumeContent(content);
        if (hasBasicInfo.score > 2) {
            this.setValidationStatus('Resume looks good! Ready to upload', 'success', 'fa-check-circle');
            this.uploadBtn.disabled = false;
            return true;
        } else {
            this.setValidationStatus('Consider adding more details (experience, skills, etc.)', 'warning', 'fa-exclamation-circle');
            this.uploadBtn.disabled = false; // Still allow upload but with warning
            return true;
        }
    }

    checkResumeContent(content) {
        const lowerContent = content.toLowerCase();
        let score = 0;
        const found = [];

        // Check for common resume sections
        const patterns = {
            contact: /(?:email|phone|@|contact)/,
            experience: /(?:experience|work|job|position|role|employed)/,
            education: /(?:education|degree|university|college|school)/,
            skills: /(?:skills|technologies|proficient|expert)/,
            projects: /(?:project|built|developed|created)/
        };

        Object.keys(patterns).forEach(key => {
            if (patterns[key].test(lowerContent)) {
                score++;
                found.push(key);
            }
        });

        return { score, found };
    }

    setValidationStatus(message, type, icon) {
        if (!this.validationStatus) return;

        const colors = {
            success: 'text-success',
            warning: 'text-warning',
            danger: 'text-danger',
            info: 'text-info'
        };

        this.validationStatus.className = colors[type] || colors.info;
        this.validationStatus.innerHTML = `<i class="fas ${icon}"></i> ${message}`;
    }

    autoResizeTextarea() {
        // Reset height to auto to get the scroll height
        this.textarea.style.height = 'auto';
        
        // Set the height to the scroll height, with min and max limits
        const minHeight = 200;
        const maxHeight = 500;
        const scrollHeight = Math.max(minHeight, Math.min(maxHeight, this.textarea.scrollHeight));
        
        this.textarea.style.height = scrollHeight + 'px';
    }

    async handleUpload() {
        const resumeText = this.textarea.value.trim();

        if (!resumeText) {
            window.resumeAssistant.showToast('Please enter resume content', 'error');
            return;
        }

        const originalBtnText = this.uploadBtn.querySelector('.btn-text').textContent;
        
        try {
            // Show loading state
            window.resumeAssistant.showLoading(this.uploadBtn, 'Processing Resume...');

            // Make upload request using FormData for proper form submission
            const formData = new FormData();
            formData.append('resumeText', resumeText);
            
            const response = await window.resumeAssistant.makeAPICall('/upload', {
                method: 'POST',
                body: formData
            });

            if (response.success) {
                this.showSuccessResult(response);
                window.resumeAssistant.showToast('Resume uploaded successfully!', 'success');
                
                // Save upload timestamp for analytics
                window.resumeAssistant.setLocalStorage('lastUpload', new Date().toISOString());
                
                // Scroll to success message
                this.resultDiv.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }

        } catch (error) {
            console.error('Upload error:', error);
            window.resumeAssistant.showToast(error.message || 'Failed to upload resume', 'error');
            
        } finally {
            // Hide loading state
            window.resumeAssistant.hideLoading(this.uploadBtn, originalBtnText);
        }
    }

    showSuccessResult(response) {
        // Update the success result with both chat options
        this.resultDiv.innerHTML = `
            <div class="alert alert-success">
                <h5 class="alert-heading">
                    <i class="fas fa-check-circle me-2"></i>Resume Uploaded Successfully!
                </h5>
                <p class="mb-3">Sulaiman's resume is now loaded and the AI assistant is ready to represent him in interviews.</p>
                <hr>
                <div class="row">
                    <div class="col-md-6 mb-2">
                        <a href="${response.admin_chat_url}" class="btn btn-primary w-100" id="adminChatBtn">
                            <i class="fas fa-shield-alt me-2"></i>Admin Chat
                            <br><small class="opacity-75">Private management interface</small>
                        </a>
                    </div>
                    <div class="col-md-6 mb-2">
                        <a href="${response.public_chat_url}" class="btn btn-success w-100" id="publicChatBtn">
                            <i class="fas fa-globe me-2"></i>Public Chat
                            <br><small class="opacity-75">Share this with interviewers</small>
                        </a>
                    </div>
                </div>
                <div class="mt-3 text-center">
                    <small class="text-muted">
                        <i class="fas fa-info-circle me-1"></i>
                        Public link: <code>${window.location.origin}${response.public_chat_url}</code>
                    </small>
                </div>
            </div>
        `;

        // Show success message with animation
        this.resultDiv.classList.remove('d-none');
        this.resultDiv.style.opacity = '0';
        this.resultDiv.style.transform = 'translateY(20px)';
        
        setTimeout(() => {
            this.resultDiv.style.transition = 'all 0.5s ease';
            this.resultDiv.style.opacity = '1';
            this.resultDiv.style.transform = 'translateY(0)';
        }, 100);

        // Add click handlers for both chat links
        const adminChatBtn = document.getElementById('adminChatBtn');
        const publicChatBtn = document.getElementById('publicChatBtn');
        
        if (adminChatBtn) {
            adminChatBtn.addEventListener('click', (e) => {
                e.preventDefault();
                const originalText = adminChatBtn.innerHTML;
                adminChatBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Loading Admin Chat...';
                setTimeout(() => window.location.href = response.admin_chat_url, 500);
            });
        }
        
        if (publicChatBtn) {
            publicChatBtn.addEventListener('click', (e) => {
                e.preventDefault();
                const originalText = publicChatBtn.innerHTML;
                publicChatBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Loading Public Chat...';
                setTimeout(() => window.location.href = response.public_chat_url, 500);
            });
        }
    }

    // Utility methods for better UX
    clearForm() {
        this.textarea.value = '';
        this.resultDiv.classList.add('d-none');
        this.validateInput();
        this.autoResizeTextarea();
    }

    loadSampleResume() {
        const sampleResume = `John Smith
Software Engineer
Email: john.smith@email.com
Phone: (555) 123-4567

PROFESSIONAL SUMMARY
Experienced software engineer with 5+ years developing web applications and leading technical teams. Proven track record of delivering scalable solutions and improving system performance.

EXPERIENCE

Senior Software Engineer | TechCorp Inc. | 2020-2023
• Developed and maintained full-stack web applications using Python, JavaScript, and React
• Led a team of 5 developers in implementing new features and optimizing existing systems
• Improved system performance by 40% through database optimization and code refactoring
• Collaborated with product managers and designers to deliver user-centered solutions

Software Developer | StartupXYZ | 2018-2020
• Built RESTful APIs and microservices using Python Flask and Node.js
• Implemented automated testing and CI/CD pipelines, reducing deployment time by 60%
• Worked closely with frontend developers to integrate APIs and ensure smooth user experience

EDUCATION
Bachelor of Science in Computer Science
University of Technology | 2018

TECHNICAL SKILLS
• Programming Languages: Python, JavaScript, TypeScript, Java
• Frameworks: React, Node.js, Flask, Django
• Databases: PostgreSQL, MongoDB, Redis
• Cloud Services: AWS, Docker, Kubernetes
• Tools: Git, Jenkins, JIRA, Agile/Scrum

PROJECTS
E-commerce Platform - Led development of a scalable e-commerce solution handling 10,000+ daily users
Real-time Chat Application - Built using WebSocket technology with Redis for session management`;

        this.textarea.value = sampleResume;
        this.validateInput();
        this.autoResizeTextarea();
        window.resumeAssistant.showToast('Sample resume loaded for testing', 'info');
    }
}

// Initialize uploader when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.resumeUploader = new ResumeUploader();
    
    // Add sample resume button for testing (development only)
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        const sampleBtn = document.createElement('button');
        sampleBtn.type = 'button';
        sampleBtn.className = 'btn btn-outline-secondary btn-sm mt-2';
        sampleBtn.innerHTML = '<i class="fas fa-file-text me-1"></i>Load Sample Resume';
        sampleBtn.onclick = () => window.resumeUploader.loadSampleResume();
        
        const textarea = document.getElementById('resumeText');
        if (textarea && textarea.parentNode) {
            textarea.parentNode.appendChild(sampleBtn);
        }
    }
}); 