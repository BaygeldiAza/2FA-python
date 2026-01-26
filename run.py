import sys
import time
import json
import requests

BASE_URL = "http://127.0.0.1:8000"
TIMEOUT = 10
OTP_LEN = 6


def safe_password(prompt: str = "Enter password: ") -> str:
    # Best masking available on Windows
    try:
        from pwinput import pwinput
        return pwinput(prompt)
    except Exception:
        pass

    try:
        from getpass import getpass
        return getpass(prompt)
    except Exception:
        return input(prompt)


def api_request(method: str, path: str, payload: dict | None = None, retries: int = 2):
    """
    Robust API request wrapper:
    - retries on connection errors/timeouts
    - prints clean error messages (including FastAPI 422 details)
    """
    url = f"{BASE_URL}{path}"
    last_err = None

    for attempt in range(retries + 1):
        try:
            r = requests.request(method, url, json=payload, timeout=TIMEOUT)

            # Try parse JSON
            try:
                data = r.json()
            except Exception:
                data = r.text

            # FastAPI validation errors (422)
            if r.status_code == 422:
                print("\n[422] Validation error:")
                if isinstance(data, dict) and "detail" in data:
                    for item in data["detail"]:
                        loc = ".".join(str(x) for x in item.get("loc", []))
                        msg = item.get("msg", "")
                        print(f" - {loc}: {msg}")
                else:
                    print(data)
                return r.status_code, data

            # Other errors
            if r.status_code >= 400:
                print(f"\n[{r.status_code}] Error response:")
                print(data)
                return r.status_code, data

            return r.status_code, data

        except (requests.Timeout, requests.ConnectionError) as e:
            last_err = e
            if attempt < retries:
                sleep_s = 0.7 * (attempt + 1)
                print(f"[WARN] {type(e).__name__}: {e}. Retrying in {sleep_s:.1f}s...")
                time.sleep(sleep_s)
            else:
                print(f"[ERROR] Request failed after retries: {repr(last_err)}")
                return 0, None

        except Exception as e:
            print(f"[ERROR] Unexpected error: {repr(e)}")
            return 0, None

    return 0, None


def health_check():
    code, data = api_request("GET", "/")
    if code == 200:
        print("[OK] API:", data)
        return True
    print("[FAIL] API not reachable.")
    return False


def register_user():
    username = input("Enter username: ").strip()
    email = input("Enter email: ").strip()
    password = safe_password()

    payload = {"username": username, "email": email, "password": password}
    code, data = api_request("POST", "/register/", payload)

    if code == 200:
        print("[SUCCESS]", data)
    else:
        print("[FAILED]")


def login_user():
    email = input("Enter email: ").strip()
    password = safe_password()

    payload = {"email": email, "password": password}
    code, data = api_request("POST", "/login/", payload)

    if code != 200:
        print("[FAILED]")
        return

    print("[SUCCESS]", data)

    # IMPORTANT: If SMTP is blocked in your network, you won't receive OTP.
    # You can still test flow by reading OTP from server logs or storing OTP in dev mode.
    otp = input("Enter OTP (6 digits): ").strip()

    if not (otp.isdigit() and len(otp) == OTP_LEN):
        print(f"[ERROR] OTP must be exactly {OTP_LEN} digits.")
        return

    verify_otp(email, otp)


def verify_otp(email: str, otp: str):
    payload = {"email": email, "otp": otp}
    code, data = api_request("POST", "/verify_otp/", payload)

    if code == 200:
        print("[SUCCESS]", data)
    else:
        print("[FAILED]")


def main():
    print("=== Email OTP 2FA Demo Client ===")
    health_check()

    while True:
        print("\n1) Register")
        print("2) Login (Email + Password -> OTP)")
        print("3) Exit")

        choice = input("Choose (1/2/3): ").strip()

        if choice == "1":
            register_user()
        elif choice == "2":
            login_user()
        elif choice == "3":
            print("Bye!")
            sys.exit(0)
        else:
            print("Invalid choice.")


if __name__ == "__main__":
    main()
