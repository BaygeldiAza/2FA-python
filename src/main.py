from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
import bcrypt
from contextlib import asynccontextmanager

from .schemas import UserRegistration, UserLogin, OTPVerification, Token, GoogleAuthRequest, UserResponse
from .crud import create_user, get_user_by_email, generate_otp, create_oauth_user, get_user_by_oauth
from .utils import send_otp_email, send_login_notification_email 
from .auth import create_access_token, verify_google_token
from .config import settings
from .db import SessionLocal, engine
from .models import Base

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database initialized")

    yield
    print("Closing database connections... ")
    engine.dispose()
    print("Shutdown complete")

app = FastAPI(
    title="User Authentication API",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware for OAuth popup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the login page with Google OAuth popup"""
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Login - OAuth 2.0</title>
        <script src="https://accounts.google.com/gsi/client" async defer></script>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
                padding: 20px;
            }
            
            .container {
                background: white;
                border-radius: 16px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.2);
                padding: 40px;
                max-width: 400px;
                width: 100%;
            }
            
            h1 {
                text-align: center;
                color: #333;
                margin-bottom: 30px;
                font-size: 28px;
            }
            
            .form-group {
                margin-bottom: 20px;
            }
            
            label {
                display: block;
                margin-bottom: 8px;
                color: #555;
                font-weight: 500;
            }
            
            input {
                width: 100%;
                padding: 12px;
                border: 2px solid #e1e8ed;
                border-radius: 8px;
                font-size: 14px;
                transition: border-color 0.3s;
            }
            
            input:focus {
                outline: none;
                border-color: #667eea;
            }
            
            button {
                width: 100%;
                padding: 12px;
                background: #667eea;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                font-weight: 600;
                cursor: pointer;
                transition: background 0.3s;
                margin-top: 10px;
            }
            
            button:hover {
                background: #5568d3;
            }
            
            .divider {
                display: flex;
                align-items: center;
                text-align: center;
                margin: 30px 0;
                color: #999;
            }
            
            .divider::before,
            .divider::after {
                content: '';
                flex: 1;
                border-bottom: 1px solid #e1e8ed;
            }
            
            .divider span {
                padding: 0 15px;
                font-size: 14px;
            }
            
            .google-btn {
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 10px;
                background: white;
                color: #444;
                border: 2px solid #e1e8ed;
                padding: 12px;
                border-radius: 8px;
                font-size: 16px;
                font-weight: 500;
                cursor: pointer;
                transition: all 0.3s;
            }
            
            .google-btn:hover {
                background: #f8f9fa;
                border-color: #667eea;
            }
            
            .google-icon {
                width: 20px;
                height: 20px;
            }
            
            .message {
                padding: 12px;
                border-radius: 8px;
                margin-bottom: 20px;
                display: none;
            }
            
            .message.success {
                background: #d4edda;
                color: #155724;
                border: 1px solid #c3e6cb;
                display: block;
            }
            
            .message.error {
                background: #f8d7da;
                color: #721c24;
                border: 1px solid #f5c6cb;
                display: block;
            }
            
            .tabs {
                display: flex;
                margin-bottom: 30px;
                border-bottom: 2px solid #e1e8ed;
            }
            
            .tab {
                flex: 1;
                padding: 12px;
                text-align: center;
                cursor: pointer;
                border-bottom: 3px solid transparent;
                margin-bottom: -2px;
                transition: all 0.3s;
                color: #666;
                font-weight: 500;
            }
            
            .tab.active {
                color: #667eea;
                border-bottom-color: #667eea;
            }
            
            .tab-content {
                display: none;
            }
            
            .tab-content.active {
                display: block;
            }
            
            .user-info {
                background: #f8f9fa;
                padding: 20px;
                border-radius: 8px;
                text-align: center;
            }
            
            .user-info img {
                width: 80px;
                height: 80px;
                border-radius: 50%;
                margin-bottom: 15px;
            }
            
            .logout-btn {
                background: #dc3545;
                margin-top: 20px;
            }
            
            .logout-btn:hover {
                background: #c82333;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔐 Authentication</h1>
            
            <div id="message" class="message"></div>
            
            <div id="auth-section">
                <div class="tabs">
                    <div class="tab active" onclick="switchTab('login')">Login</div>
                    <div class="tab" onclick="switchTab('register')">Register</div>
                </div>
                
                <!-- Login Tab -->
                <div id="login-tab" class="tab-content active">
                    <form id="loginForm" onsubmit="handleLogin(event)">
                        <div class="form-group">
                            <label>Email</label>
                            <input type="email" id="login-email" required>
                        </div>
                        <div class="form-group">
                            <label>Password</label>
                            <input type="password" id="login-password" required>
                        </div>
                        <button type="submit">Login</button>
                    </form>
                    
                    <div class="divider">
                        <span>OR</span>
                    </div>
                    
                    <button class="google-btn" onclick="handleGoogleLogin()">
                        <svg class="google-icon" viewBox="0 0 24 24">
                            <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                            <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                            <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                            <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                        </svg>
                        Continue with Google
                    </button>
                </div>
                
                <!-- Register Tab -->
                <div id="register-tab" class="tab-content">
                    <form id="registerForm" onsubmit="handleRegister(event)">
                        <div class="form-group">
                            <label>Username</label>
                            <input type="text" id="register-username" minlength="3" maxlength="25" required>
                        </div>
                        <div class="form-group">
                            <label>Email</label>
                            <input type="email" id="register-email" required>
                        </div>
                        <div class="form-group">
                            <label>Password</label>
                            <input type="password" id="register-password" minlength="8" required>
                        </div>
                        <button type="submit">Register</button>
                    </form>
                    
                    <div class="divider">
                        <span>OR</span>
                    </div>
                    
                    <button class="google-btn" onclick="handleGoogleLogin()">
                        <svg class="google-icon" viewBox="0 0 24 24">
                            <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                            <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                            <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                            <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                        </svg>
                        Continue with Google
                    </button>
                </div>
            </div>
            
            <!-- User Dashboard (shown after successful login) -->
            <div id="dashboard-section" style="display: none;">
                <div class="user-info">
                    <img id="user-avatar" src="" alt="User Avatar">
                    <h2 id="user-name"></h2>
                    <p id="user-email"></p>
                    <button class="logout-btn" onclick="handleLogout()">Logout</button>
                </div>
            </div>
        </div>
        
        <script>
            const API_BASE = window.location.origin;
            let currentUser = null;
            
            // Google OAuth Configuration
            const GOOGLE_CLIENT_ID = '""" + settings.GOOGLE_CLIENT_ID + """';
            
            // Initialize Google Sign-In
            function initGoogleSignIn() {
                google.accounts.id.initialize({
                    client_id: GOOGLE_CLIENT_ID,
                    callback: handleGoogleCallback,
                    auto_select: false,
                });
            }
            
            // Handle Google Sign-In callback
            async function handleGoogleCallback(response) {
                try {
                    showMessage('Processing Google login...', 'success');
                    
                    const res = await fetch(`${API_BASE}/auth/google`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ token: response.credential })
                    });
                    
                    const data = await res.json();
                    
                    if (res.ok) {
                        localStorage.setItem('access_token', data.access_token);
                        currentUser = data.user;
                        showDashboard(data.user);
                        showMessage('Successfully logged in with Google!', 'success');
                    } else {
                        showMessage(data.detail || 'Google login failed', 'error');
                    }
                } catch (error) {
                    showMessage('Error: ' + error.message, 'error');
                }
            }
            
            // Handle Google Login Button Click
            function handleGoogleLogin() {
                google.accounts.id.prompt((notification) => {
                    if (notification.isNotDisplayed() || notification.isSkippedMoment()) {
                        // Fallback to popup if prompt doesn't work
                        google.accounts.id.renderButton(
                            document.createElement('div'),
                            { theme: 'outline', size: 'large' }
                        );
                    }
                });
            }
            
            // Traditional Login
            async function handleLogin(event) {
                event.preventDefault();
                
                const email = document.getElementById('login-email').value;
                const password = document.getElementById('login-password').value;
                
                try {
                    const res = await fetch(`${API_BASE}/login/`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ email, password })
                    });
                    
                    const data = await res.json();
                    
                    if (res.ok) {
                        showMessage(data.message, 'success');
                        // Redirect to OTP verification page or show OTP input
                        setTimeout(() => {
                            const otp = prompt('Enter the OTP sent to your email:');
                            if (otp) {
                                verifyOTP(email, otp);
                            }
                        }, 1000);
                    } else {
                        showMessage(data.detail, 'error');
                    }
                } catch (error) {
                    showMessage('Error: ' + error.message, 'error');
                }
            }
            
            // Register
            async function handleRegister(event) {
                event.preventDefault();
                
                const username = document.getElementById('register-username').value;
                const email = document.getElementById('register-email').value;
                const password = document.getElementById('register-password').value;
                
                try {
                    const res = await fetch(`${API_BASE}/register/`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ username, email, password })
                    });
                    
                    const data = await res.json();
                    
                    if (res.ok) {
                        showMessage(data.message + ' - Please login now.', 'success');
                        switchTab('login');
                        document.getElementById('registerForm').reset();
                    } else {
                        showMessage(data.detail, 'error');
                    }
                } catch (error) {
                    showMessage('Error: ' + error.message, 'error');
                }
            }
            
            // Verify OTP
            async function verifyOTP(email, otp) {
                try {
                    const res = await fetch(`${API_BASE}/verify_otp/`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ email, otp })
                    });
                    
                    const data = await res.json();
                    
                    if (res.ok) {
                        showMessage('Login successful!', 'success');
                        // Here you would typically receive and store a JWT token
                        // For now, just show a success message
                    } else {
                        showMessage(data.detail, 'error');
                    }
                } catch (error) {
                    showMessage('Error: ' + error.message, 'error');
                }
            }
            
            // Switch tabs
            function switchTab(tab) {
                document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
                document.querySelectorAll('.tab-content').forEach(tc => tc.classList.remove('active'));
                
                if (tab === 'login') {
                    document.querySelectorAll('.tab')[0].classList.add('active');
                    document.getElementById('login-tab').classList.add('active');
                } else {
                    document.querySelectorAll('.tab')[1].classList.add('active');
                    document.getElementById('register-tab').classList.add('active');
                }
            }
            
            // Show message
            function showMessage(msg, type) {
                const messageDiv = document.getElementById('message');
                messageDiv.textContent = msg;
                messageDiv.className = `message ${type}`;
                messageDiv.style.display = 'block';
                
                setTimeout(() => {
                    messageDiv.style.display = 'none';
                }, 5000);
            }
            
            // Show dashboard
            function showDashboard(user) {
                document.getElementById('auth-section').style.display = 'none';
                document.getElementById('dashboard-section').style.display = 'block';
                document.getElementById('user-avatar').src = user.profile_picture || 'https://via.placeholder.com/80';
                document.getElementById('user-name').textContent = user.username;
                document.getElementById('user-email').textContent = user.email;
            }
            
            // Logout
            function handleLogout() {
                localStorage.removeItem('access_token');
                currentUser = null;
                document.getElementById('auth-section').style.display = 'block';
                document.getElementById('dashboard-section').style.display = 'none';
                showMessage('Logged out successfully', 'success');
            }
            
            // Initialize on page load
            window.onload = function() {
                initGoogleSignIn();
                
                // Check if user is already logged in
                const token = localStorage.getItem('access_token');
                if (token) {
                    // Verify token and show dashboard
                    // This would require a /me endpoint
                }
            };
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.post("/register/")
async def register(user: UserRegistration, db: Session = Depends(get_db)):
    email = user.email.lower().strip()
    
    # Check if user already exists
    if get_user_by_email(db, email):
        raise HTTPException(status_code=409, detail="Email already registered")

    # Hash password and create user
    hashed_password = bcrypt.hashpw(user.password.encode("utf-8"), bcrypt.gensalt())
    create_user(db, user.username, email, hashed_password.decode('utf-8'))

    return {"message": "User registered successfully"}

@app.post("/login/")
async def login(user: UserLogin, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    email = user.email.lower().strip()
    db_user = get_user_by_email(db, email)

    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    if not db_user.hashed_password:
        raise HTTPException(status_code=400, detail="Please use Google Sign-In for this account")

    if not bcrypt.checkpw(user.password.encode("utf-8"), db_user.hashed_password.encode("utf-8")):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    # Generate OTP and send it
    otp = generate_otp(db, email)
    background_tasks.add_task(send_otp_email, db_user.email, otp)

    return {"message": f"OTP sent to email (expires in {settings.OTP_TTL_SECONDS} seconds)"}

@app.post("/verify_otp/", response_model=Token)
async def verify_otp(otp_data: OTPVerification, db: Session = Depends(get_db)):
    from datetime import datetime
    email = otp_data.email.lower().strip()
    db_user = get_user_by_email(db, email)
    
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not db_user.otp_expires_at or db_user.otp_expires_at < datetime.utcnow():
        db_user.otp = None
        db_user.otp_expires_at = None
        db.commit()
        raise HTTPException(status_code=400, detail="OTP expired! Login again.")
    
    if db_user.otp != otp_data.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")
    
    # Clear OTP
    db_user.otp = None
    db_user.otp_expires_at = None
    db.commit()
    
    # Create access token
    access_token = create_access_token(data={"sub": db_user.email, "user_id": db_user.id})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": db_user.id,
            "username": db_user.username,
            "email": db_user.email,
            "profile_picture": db_user.profile_picture,
            "is_verified": db_user.is_verified
        }
    }

@app.post("/auth/google", response_model=Token)
async def google_auth(auth_data: GoogleAuthRequest, db: Session = Depends(get_db)):
    """Handle Google OAuth authentication"""
    # Verify the Google token
    google_user = verify_google_token(auth_data.token)
    
    if not google_user:
        raise HTTPException(status_code=400, detail="Invalid Google token")
    
    email = google_user['email'].lower()
    
    # Check if user exists
    db_user = get_user_by_email(db, email)
    
    if not db_user:
        # Check if OAuth user exists
        db_user = get_user_by_oauth(db, 'google', google_user['google_id'])
    
    if not db_user:
        # Create new user
        db_user = create_oauth_user(
            db=db,
            email=email,
            username=google_user['name'],
            oauth_provider='google',
            oauth_id=google_user['google_id'],
            profile_picture=google_user.get('picture')
        )
    else:
        # Update existing user with OAuth info if not set
        if not db_user.oauth_provider:
            db_user.oauth_provider = 'google'
            db_user.oauth_id = google_user['google_id']
            db_user.profile_picture = google_user.get('picture')
            db_user.is_verified = True
            db.commit()
            db.refresh(db_user)
    
    # Create access token
    access_token = create_access_token(data={"sub": db_user.email, "user_id": db_user.id})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": db_user.id,
            "username": db_user.username,
            "email": db_user.email,
            "oauth_provider": db_user.oauth_provider,
            "profile_picture": db_user.profile_picture,
            "is_verified": db_user.is_verified
        }
    }

@app.get("/auth/me", response_model=UserResponse)
async def get_current_user(db: Session = Depends(get_db)):
    """Get current user info (requires authentication)"""
    # This is a placeholder - you would implement proper JWT verification here
    raise HTTPException(status_code=501, detail="Not implemented yet")