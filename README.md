# 🚀 Two-Factor Authentication (2FA) with Email - FastAPI Project

## 📚 Overview

This project demonstrates how to implement **Two-Factor Authentication (2FA)** using **FastAPI**, **SMTP** for email, and **Python**. The application runs entirely in the terminal and is designed for educational purposes to show how 2FA works with email as the second factor.

- **Register a User**: Users can register with their username, password, and email.
- **Login with OTP**: After logging in, users receive an OTP (One-Time Passcode) via email.
- **OTP Verification**: Users must enter the OTP to successfully log in.

## 🚀 Features

- **User Registration**: Register a user with username, password, and email.
- **Login Process**: User provides credentials, and an OTP is sent to their email.
- **OTP Authentication**: User enters the OTP from their email to authenticate and gain access.

## ⚙️ Tech Stack

- **Backend**: FastAPI
- **Password Hashing**: bcrypt
- **Email Service**: SMTP (Gmail for demo purposes)
- **Database**: In-memory storage (for demo)
- **Environment Variables**: dotenv for email credentials

## 🛠 Installation

### Prerequisites
- **Python 3.7+** installed on your machine.
- Gmail or another SMTP-compatible email account for sending OTPs.

### Steps to Set Up

1. **Clone the repository**:
    ```bash
    git clone https://github.com/yourusername/2fa-fastapi-email.git
    cd 2fa-fastapi-email
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

4. **Create a `.env` file** in the root directory and add your email credentials:
    ```
    SENDER_EMAIL=your-email@gmail.com
    SENDER_PASSWORD=your-email-password
    ```

5. **Run the FastAPI server**:
    ```bash
    uvicorn app.main:app --reload
    ```

6. **Run the terminal client** to interact with the API:
    ```bash
    python run.py
    ```

## 🚶‍♂️ Usage

### 1. Register a User
- Choose option `1` in the terminal.
- Enter a **username**, **password**, and **email**.

### 2. Log In with OTP
- Choose option `2` to log in.
- Enter your **username** and **password**.
- An OTP will be sent to the registered email address.
- Enter the OTP to complete the login process.

### 3. OTP Verification
- If the OTP is valid, you will be logged in successfully. If not, you'll get an error message.

## 🌟 Example Flow

1. **Register**:
    ```bash
    Enter your username: johndoe
    Enter your password: ********
    Enter your email: johndoe@example.com
    User registered successfully
    ```

2. **Login**:
    ```bash
    Enter your username: johndoe
    Enter your password: ********
    OTP sent to email
    Enter the OTP: 123456
    Login successful
    ```

## 🔐 Security Considerations

- **Password Hashing**: Passwords are hashed using **bcrypt** to ensure security.
- **OTP Expiry**: OTPs should be implemented with an expiration time (currently not implemented).
- **Rate Limiting**: To prevent abuse, consider implementing rate limiting for OTP requests.

## 📧 Email Configuration

- The project uses **Gmail's SMTP server** to send OTP emails.
- Make sure to enable **Less Secure Apps** or set up **App Passwords** if you're using Gmail.

## 🚧 TODO

- [ ] Implement **OTP expiration** (e.g., OTP expires after 5 minutes).
- [ ] Integrate a **real database** (e.g., SQLite or PostgreSQL) for persistent storage.
- [ ] Add **rate limiting** for OTP requests.
- [ ] Implement **frontend** for a better user experience.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 💬 Contributing

Feel free to fork the repository and submit a pull request with your improvements! Contributions are welcome.

---

🎉 **Enjoy exploring Two-Factor Authentication with FastAPI!** 🎉
