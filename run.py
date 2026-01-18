import requests
from getpass import getpass

BASE_URL = "http://127.0.0.1:8000"

def register_user():
    username = input("Enter username: ").strip()
    email = input("Enter email: ").strip()
    password = getpass("Enter password: ")

    payload = {"username": username, "email": email, "password": password}

    r = requests.post(f"{BASE_URL}/register/", json=payload, timeout=10)
    try:
        print(r.status_code, r.json())
    except Exception:
        print(r.status_code, r.text)

def login_user():
    email = input("Enter email: ").strip()
    password = getpass("Enter password: ")

    payload = {"email": email, "password": password}

    r = requests.post(f"{BASE_URL}/login/", json=payload, timeout=10)
    try:
        data = r.json()
    except Exception:
        print(r.status_code, r.text)
        return

    print(r.status_code, data)

    if r.status_code == 200:
        otp = input("Enter OTP sent to your email: ").strip()
        verify_otp(email, otp)

def verify_otp(email: str, otp: str):
    payload = {"email": email, "otp": otp}

    r = requests.post(f"{BASE_URL}/verify_otp/", json=payload, timeout=10)
    try:
        print(r.status_code, r.json())
    except Exception:
        print(r.status_code, r.text)

def main():
    while True:
        print("\n=== Email OTP 2FA Demo ===")
        print("1) Register")
        print("2) Login (Email + Password -> OTP)")
        print("3) Exit")

        choice = input("Choose (1/2/3): ").strip()

        if choice == "1":
            register_user()
        elif choice == "2":
            login_user()
        elif choice == "3":
            print("Bye!")
            break
        else:
            print("Invalid choice.")

if __name__ == "__main__":
    main()
