# 🚀 Two-Factor Authentication (2FA) with Email + Google OAuth 2.0 - FastAPI Project

## 📚 Overview

This project demonstrates how to implement **Two-Factor Authentication (2FA)** and **Google OAuth 2.0** using **FastAPI**, **SMTP** for email, and **Python**. The application provides multiple authentication methods:

- **Traditional 2FA**: Register with email/password, login with OTP verification via email
- **Google OAuth 2.0**: One-click sign-in with Google account using popup authentication
- **JWT Tokens**: Secure session management after successful authentication

The application includes both a web interface and REST API endpoints for flexible integration.

## ✨ Features

### Authentication Methods

- **User Registration**: Register with username, password, and email
- **Login with OTP**: After login, receive an OTP (One-Time Passcode) via email for verification
- **Google OAuth 2.0**: Sign in with Google account using popup-based authentication
- **OTP Authentication**: Verify email-based OTP to complete login
- **JWT Tokens**: Secure token-based session management

### Security Features

- **Password Hashing**: Secure password storage with bcrypt
- **OTP Expiration**: Time-limited OTPs (120 seconds by default)
- **Token Verification**: Google ID tokens verified server-side
- **JWT Sessions**: Stateless authentication with expiring tokens
- **CORS Protection**: Configurable cross-origin request handling

### User Experience

- **Modern Web UI**: Clean, responsive login interface with tabs
- **Popup OAuth**: Non-intrusive Google sign-in popup
- **Profile Pictures**: Automatic avatar sync from Google accounts
- **User Dashboard**: Profile display after successful login
- **Dual Authentication**: Choose between traditional or OAuth login

## ⚙️ Tech Stack

- **Backend**: FastAPI 0.115.0
- **Database**: MySQL with SQLAlchemy ORM
- **Password Hashing**: bcrypt
- **Authentication**: 
  - JWT tokens (python-jose)
  - Google OAuth 2.0 (google-auth)
- **Email Service**: SMTP (Gmail)
- **Validation**: Pydantic with email validation
- **Environment Variables**: python-dotenv

## 🛠 Installation

### Prerequisites
- **Python 3.8+** installed on your machine
- **MySQL 5.7+** or **MySQL 8.0+**
- Gmail account (for sending OTP emails)
- Google Cloud account (for OAuth 2.0 credentials)

### Steps to Set Up

1. **Clone the repository**:
    ```bash
    git clone https://github.com/yourusername/2fa-oauth-fastapi.git
    cd 2fa-oauth-fastapi
    ```

2. **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate   # On Windows: venv\Scripts\activate
    ```

3. **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4. **Setup MySQL Database**:
    ```bash
    mysql -u root -p
    CREATE DATABASE auth_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    EXIT;
    ```

5. **Setup Google OAuth 2.0** (5 minutes):
    - Go to [Google Cloud Console](https://console.cloud.google.com/)
    - Create a new project
    - Enable Google+ API
    - Create OAuth 2.0 credentials:
      - Application type: Web application
      - Authorized JavaScript origins: `http://localhost:8000`
      - Authorized redirect URIs: `http://localhost:8000/auth/google/callback`
    - Copy your Client ID and Client Secret

6. **Setup Gmail App Password**:
    - Go to Google Account → Security
    - Enable 2-Step Verification
    - Generate App Password for "Mail"
    - Copy the 16-character password

7. **Create a `.env` file** in the root directory:
    ```env
    # Database Configuration
    DATABASE_URL=mysql+mysqlconnector://root:your_password@localhost/auth_db
    
    # Email Configuration (Gmail)
    SENDER_EMAIL=your-email@gmail.com
    SENDER_PASSWORD=your-gmail-app-password
    
    # Google OAuth 2.0 Credentials
    GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
    GOOGLE_CLIENT_SECRET=your-client-secret
    GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback
    
    # JWT Configuration
    SECRET_KEY=generate-with-openssl-rand-hex-32
    ALGORITHM=HS256
    ACCESS_TOKEN_EXPIRE_MINUTES=30
    ```

8. **Generate a strong SECRET_KEY**:
    ```bash
    openssl rand -hex 32
    # Copy the output to your .env file
    ```

9. **Run the FastAPI server**:
    ```bash
    uvicorn main:app --reload
    # Or if in app directory:
    uvicorn app.main:app --reload
    ```

10. **Access the application**:
    - Open browser: `http://localhost:8000`
    - You'll see the login/register page with both traditional and Google OAuth options

## 🚶‍♂️ Usage

### Method 1: Traditional 2FA with OTP

#### 1. Register a User
- Open `http://localhost:8000`
- Click the **"Register"** tab
- Enter **username**, **email**, and **password** (minimum 8 characters)
- Click **"Register"**
- Success message will appear

#### 2. Log In with OTP
- Switch to the **"Login"** tab
- Enter your **email** and **password**
- Click **"Login"**
- Check your email for the OTP (6-digit code)
- Enter the OTP when prompted
- Upon successful verification, you'll be logged in with a JWT token

#### 3. OTP Verification
- OTP expires in 120 seconds (2 minutes)
- If expired, login again to receive a new OTP
- OTP is sent via email using Gmail SMTP

### Method 2: Google OAuth 2.0 (One-Click)

#### 1. Sign In with Google
- Open `http://localhost:8000`
- Click **"Continue with Google"** button
- Google popup will appear
- Select your Google account
- Grant permissions (if first time)
- Automatically logged in with JWT token
- Profile picture and info displayed on dashboard

#### 2. Automatic Profile Sync
- Username: Taken from Google account name
- Email: Google account email
- Profile Picture: Google account avatar
- Verified Status: Automatically verified (no OTP needed)

## 🌟 Example Flows

### Traditional 2FA Flow
```
1. User Registration
   ├─ Enter username: johndoe
   ├─ Enter email: johndoe@example.com
   ├─ Enter password: ********
   └─ ✅ User registered successfully

2. Login Process
   ├─ Enter email: johndoe@example.com
   ├─ Enter password: ********
   ├─ 📧 OTP sent to email
   ├─ Check email for 6-digit code
   ├─ Enter OTP: 123456
   └─ ✅ Login successful - JWT token received

3. Authenticated Access
   └─ Use JWT token for protected endpoints
```

### Google OAuth Flow
```
1. Click "Continue with Google"
   ├─ 🌐 Google popup opens
   ├─ Select Google account
   ├─ Grant permissions
   └─ ✅ Automatically logged in

2. Profile Loaded
   ├─ Username: From Google
   ├─ Email: From Google
   ├─ Profile Picture: From Google
   └─ ✅ Verified status: True

3. Dashboard Displayed
   └─ JWT token stored in localStorage
```

## 📡 API Endpoints

### Authentication Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/` | Serve login/register page | No |
| POST | `/register/` | Register new user | No |
| POST | `/login/` | Login (sends OTP to email) | No |
| POST | `/verify_otp/` | Verify OTP and get JWT token | No |
| POST | `/auth/google` | Google OAuth authentication | No |
| GET | `/auth/me` | Get current user info | Yes (JWT) |

### API Usage Examples

#### Register User
```bash
curl -X POST http://localhost:8000/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "johndoe",
    "email": "john@example.com",
    "password": "SecurePass123!"
  }'
```

#### Login (Sends OTP)
```bash
curl -X POST http://localhost:8000/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "SecurePass123!"
  }'
```

#### Verify OTP
```bash
curl -X POST http://localhost:8000/verify_otp/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "otp": "123456"
  }'
```

#### Google OAuth (Frontend)
```javascript
// Handled by Google Sign-In library
// Token automatically sent to /auth/google endpoint
// Returns JWT token and user info
```

## 🗄️ Database Schema

```sql
users
├─ id (INT, PRIMARY KEY, AUTO_INCREMENT)
├─ username (VARCHAR(255), NOT NULL)
├─ email (VARCHAR(255), UNIQUE, NOT NULL)
├─ hashed_password (VARCHAR(255), NULLABLE) -- Null for OAuth users
├─ oauth_provider (VARCHAR(50), NULLABLE)   -- 'google', 'github', etc.
├─ oauth_id (VARCHAR(255), NULLABLE)        -- Provider's user ID
├─ profile_picture (VARCHAR(500), NULLABLE) -- Avatar URL
├─ is_verified (BOOLEAN, DEFAULT FALSE)     -- Auto-true for OAuth
├─ otp (VARCHAR(6), NULLABLE)               -- Current OTP
├─ otp_expires_at (DATETIME, NULLABLE)      -- OTP expiration time
├─ otp_attempts (INT, DEFAULT 0)            -- Failed OTP attempts
└─ user_created_time (DATETIME, DEFAULT NOW())
```

## 🔐 Security Considerations

### Implemented Security Features

✅ **Password Hashing**: Passwords hashed with bcrypt (salt rounds: 12)  
✅ **OTP Expiry**: OTPs expire after 120 seconds  
✅ **Token Verification**: Google ID tokens verified server-side  
✅ **JWT Expiration**: Access tokens expire after 30 minutes  
✅ **CORS Protection**: Configurable allowed origins  
✅ **Input Validation**: Pydantic schemas validate all inputs  
✅ **SQL Injection Prevention**: SQLAlchemy ORM with parameterized queries  
✅ **Environment Variables**: Sensitive data stored in .env (not in code)  
✅ **HTTPS Ready**: Configure for production deployment  

### Best Practices

- **Never commit `.env` file** - Add to `.gitignore`
- **Use strong SECRET_KEY** - Generate with `openssl rand -hex 32`
- **Enable HTTPS in production** - Required for OAuth
- **Update CORS origins** - Specify exact domains in production
- **Implement rate limiting** - Prevent brute force attacks
- **Monitor failed login attempts** - Add account lockout mechanism
- **Regular security audits** - Keep dependencies updated

## 📧 Email Configuration

### Gmail SMTP Setup

1. **Enable 2-Step Verification**:
   - Go to Google Account → Security
   - Enable 2-Step Verification

2. **Generate App Password**:
   - Security → App passwords
   - Select "Mail" and "Other (Custom name)"
   - Enter "FastAPI Auth"
   - Copy the 16-character password

3. **Add to `.env`**:
   ```env
   SENDER_EMAIL=your-email@gmail.com
   SENDER_PASSWORD=xxxx xxxx xxxx xxxx  # No spaces in .env
   ```

### Email Templates

- **OTP Email**: Sent during login with 6-digit code
- **Login Notification**: (Optional) Alert for new login attempts
- **Welcome Email**: (Future) Welcome new users

## 🎯 Architecture

### Authentication Flow Comparison

| Feature | Traditional 2FA | Google OAuth 2.0 |
|---------|----------------|------------------|
| **Steps** | 3 steps | 1 step |
| **Password** | Required | Not required |
| **Email Verification** | OTP via email | Auto-verified |
| **Profile Picture** | Not included | Auto-synced |
| **Setup Time** | User registration | Instant |
| **Security** | High (bcrypt + OTP) | Very High (Google) |
| **User Experience** | Multiple steps | One-click |

### Component Architecture

```
┌─────────────────────────────────────────────────────┐
│                   User Browser                       │
│  ┌────────────────┐         ┌────────────────┐     │
│  │ Login/Register │         │ Google OAuth   │     │
│  │     Forms      │         │     Popup      │     │
│  └────────┬───────┘         └────────┬───────┘     │
└───────────┼──────────────────────────┼─────────────┘
            │                          │
            ▼                          ▼
┌───────────────────────────────────────────────────┐
│              FastAPI Backend                       │
│  ┌──────────────┐  ┌──────────────────────────┐  │
│  │ /register/   │  │ /auth/google             │  │
│  │ /login/      │  │  - Verify Google token   │  │
│  │ /verify_otp/ │  │  - Create/find user      │  │
│  └──────┬───────┘  │  - Generate JWT          │  │
│         │          └────────┬─────────────────┘  │
│         ▼                   │                     │
│  ┌──────────────┐          │                     │
│  │ Email Utils  │◄─────────┘                     │
│  │ - Send OTP   │                                 │
│  └──────────────┘                                 │
└───────────┬────────────────────────────────────┬──┘
            │                                    │
            ▼                                    ▼
┌─────────────────────┐              ┌──────────────────┐
│   MySQL Database    │              │  Google OAuth    │
│  - Users table      │              │  - Token verify  │
│  - OTP storage      │              │  - User info     │
└─────────────────────┘              └──────────────────┘
```

## 📚 Documentation

### Included Documentation Files

- **README.md** - This file (project overview)
- **SETUP_GUIDE.md** - Detailed setup instructions
- **OAUTH_FLOW.md** - OAuth 2.0 flow diagrams and explanations
- **TROUBLESHOOTING.md** - Common issues and solutions
- **.env.example** - Environment variable template

### Quick Links

- [Detailed Setup Guide](SETUP_GUIDE.md)
- [OAuth Flow Documentation](OAUTH_FLOW.md)
- [Troubleshooting Guide](TROUBLESHOOTING.md)

## 🚧 TODO / Roadmap

### High Priority
- [x] Implement OTP expiration (✅ Completed - 120 seconds)
- [x] Integrate real database (✅ Completed - MySQL)
- [x] Add Google OAuth 2.0 (✅ Completed)
- [x] Implement JWT tokens (✅ Completed)
- [x] Add refresh token mechanism
- [ ] Implement rate limiting for OTP requests
- [ ] Add account lockout after failed attempts

### Medium Priority
- [ ] Password reset via email
- [ ] Email verification for new registrations
- [ ] Profile editing functionality
- [ ] Session management dashboard
- [ ] Two-Factor Authentication with TOTP (Google Authenticator)
- [ ] Multiple OAuth providers (GitHub, Facebook, Microsoft)

### Low Priority
- [ ] User profile management
- [ ] Account deletion
- [ ] Login history/audit logs
- [ ] Export user data
- [ ] Admin dashboard
- [ ] Separate React/Vue frontend
- [ ] Docker containerization
- [ ] Kubernetes deployment

### Security Enhancements
- [ ] Rate limiting middleware
- [ ] CAPTCHA for registration
- [ ] IP-based blocking
- [ ] Suspicious activity detection
- [ ] Account recovery options
- [ ] Security notifications
- [ ] Passwordless authentication

## 📞 Support

- 📧 **Email**: baygeldi0718@gmail.com
- 🐛 **Issues**: [GitHub Issues](https://github.com/yourusername/2fa-oauth-fastapi/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/yourusername/2fa-oauth-fastapi/discussions)
- 📖 **Documentation**: [Wiki](https://github.com/yourusername/2fa-oauth-fastapi/wiki)

## 📊 Project Stats

- **Version**: 2.0.0
- **Status**: Active Development 🟢
- **Last Updated**: February 2026
- **Python Version**: 3.8+
- **Database**: MySQL 5.7+

---

<div align="center">

Made with ❤️ using FastAPI, Google OAuth 2.0, and Python

⭐ **Star this repo if you find it helpful!** ⭐

</div>
