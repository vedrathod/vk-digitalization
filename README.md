# VK Digitalization - Login + Database

Run:
1. `venv\Scripts\activate`
2. `pip install -r requirements.txt`
3. `python app.py`
4. Open `http://127.0.0.1:5000`

Owner demo:
- Email: owner@vkdigitalization.com
- Password: VKOwner@123

Customers register at `/register`, login, and submit company/project details. Owner sees customer accounts and submissions at `/owner`, and can update status and notes.

SQLite database `vk_digitalization.db` is created automatically.
Change the secret key and demo owner password before public deployment.
