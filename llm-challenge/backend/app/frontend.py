import streamlit as st
import requests

BACKEND_URL = "http://127.0.0.1:8000"

# ------------------ Signup ------------------
def signup():
    st.title("Sign Up")
    username = st.text_input("Username")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Sign Up"):
        if not username or not password or not email:
            st.error("Please enter username, email, and password.")
            return

        try:
            response = requests.post(f"{BACKEND_URL}/register", json={
                "username": username,
                "password": password,
                "email": email
            })
            try:
                data = response.json()
            except requests.exceptions.JSONDecodeError:
                st.error(f"Signup failed. Server response: {response.text}")
                return

            if response.status_code == 200:
                st.success(data.get("message", "User registered successfully!"))
                st.info("Go to Login to access the app.")
            else:
                st.error(data.get("detail", f"Error: {response.status_code}"))
        except Exception as e:
            st.error(f"Request failed: {e}")


# ------------------ Login ------------------
def login():
    st.title("Login")
    username = st.text_input("Username", key="login_user")
    password = st.text_input("Password", type="password", key="login_pass")

    if st.button("Login"):
        if not username or not password:
            st.error("Please enter both username and password.")
            return

        try:
            response = requests.post(f"{BACKEND_URL}/login", data={
                "username": username,
                "password": password
            })

            try:
                data = response.json()
            except requests.exceptions.JSONDecodeError:
                st.error(f"Login failed. Server response: {response.text}")
                return

            if response.status_code == 200:
                st.success("Login successful!")
                st.session_state["token"] = data["access_token"]
            else:
                st.error(data.get("detail", f"Error: {response.status_code}"))
        except Exception as e:
            st.error(f"Request failed: {e}")


# ------------------ Chat ------------------
def chat():
    st.title("Chat with LLM")
    token = st.session_state.get("token")
    if not token:
        st.warning("Please login first.")
        return

    message = st.text_input("Your message:")
    if st.button("Send"):
        try:
            response = requests.post(
                f"{BACKEND_URL}/chat",
                headers={"Authorization": f"Bearer {token}"},
                json={"message": message}
            )
            try:
                data = response.json()
            except requests.exceptions.JSONDecodeError:
                st.error(f"Chat failed. Server response: {response.text}")
                return

            if response.status_code == 200:
                st.write(f"**You:** {data['message']}")
                st.write(f"**Bot:** {data['response']}")
            else:
                st.error(data.get("detail", f"Error: {response.status_code}"))
        except Exception as e:
            st.error(f"Request failed: {e}")


# ------------------ Upload Document ------------------
def upload_document():
    st.title("Upload Document")
    token = st.session_state.get("token")
    if not token:
        st.warning("Please login first.")
        return

    uploaded_file = st.file_uploader("Choose a file")
    if uploaded_file and st.button("Upload"):
        try:
            files = {"file": (uploaded_file.name, uploaded_file)}
            response = requests.post(
                f"{BACKEND_URL}/upload",
                headers={"Authorization": f"Bearer {token}"},
                files=files
            )
            try:
                data = response.json()
            except requests.exceptions.JSONDecodeError:
                st.error(f"Upload failed. Server response: {response.text}")
                return

            if response.status_code == 200:
                st.success(f"File uploaded: {data['filename']}")
                st.write(f"URL: {data['url']}")
            else:
                st.error(data.get("detail", f"Error: {response.status_code}"))
        except Exception as e:
            st.error(f"Request failed: {e}")


# ------------------ Chat History ------------------
def chat_history():
    st.title("Chat History")
    token = st.session_state.get("token")
    if not token:
        st.warning("Please login first.")
        return

    try:
        response = requests.get(
            f"{BACKEND_URL}/history",
            headers={"Authorization": f"Bearer {token}"}
        )
        try:
            data = response.json()
        except requests.exceptions.JSONDecodeError:
            st.error(f"Failed to fetch history. Server response: {response.text}")
            return

        if response.status_code == 200:
            for chat in data:
                st.write(f"**You:** {chat['message']}")
                st.write(f"**Bot:** {chat['response']}")
                st.write(f"*{chat['timestamp']}*")
                st.markdown("---")
        else:
            st.error(data.get("detail", f"Error: {response.status_code}"))
    except Exception as e:
        st.error(f"Request failed: {e}")


# ------------------ Main App ------------------
menu = ["Login", "Sign Up", "Chat", "Upload Document", "Chat History"]
choice = st.sidebar.selectbox("Menu", menu)

if choice == "Sign Up":
    signup()
elif choice == "Login":
    login()
elif choice == "Chat":
    chat()
elif choice == "Upload Document":
    upload_document()
elif choice == "Chat History":
    chat_history()
