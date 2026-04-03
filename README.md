# **Technical Architecture & Integration Guide: Google OAuth2 (Django + React)**

## **1. Executive Summary & Architectural Mental Model**
This document outlines the implementation of a decoupled, token-based Google OAuth2 authentication flow utilizing a React frontend and a Django REST Framework (DRF) backend. The architecture leverages `django-allauth` for provider-level identity resolution and `dj-rest-auth` as the RESTful JSON gateway.

The authentication paradigm strictly follows a client-initiated, server-verified model:
* **Phase 1 (Client):** The React frontend authenticates the user directly against Google's OAuth 2.0 servers to obtain an `access_token`.
* **Phase 2 (Gateway):** React transmits this `access_token` via a POST request to the Django backend.
* **Phase 3 (Resolution):** Django, acting as a confidential client, utilizes `allauth` adapters to verify the token with Google, resolves the identity, maps it to the internal `auth.User` and `socialaccount.SocialAccount` models, and provisions a session token back to the frontend.

---

## **2. Local Environment Setup & Repository Initialization**

To replicate this environment locally, execute the following steps to ensure database consistency and dependency isolation.

### **Repository Cloning & Environment Activation**
* **Initialize Git:** Clone the target repository to your local machine.
    * `git clone <repository_url> && cd <repository_name>`
* **Virtual Environment:** Isolate Python dependencies to prevent global module conflicts.
    * `python -m venv venv`
    * `source venv/bin/activate` (Linux/Mac) OR `venv\Scripts\activate` (Windows)
* **Backend Dependencies:** Install the exact versions from the lockfile or requirements.
    * `pip install -r requirements.txt` (Ensuring `django-allauth`, `dj-rest-auth`, and `django-cors-headers` are present).
* **Frontend Dependencies:** Navigate to the React root and install Node modules.
    * `cd frontend && npm install`

### **Database Priming & Automated Configuration**
* **Apply Migrations:** Initialize the SQLite/PostgreSQL database. It is critical to run this to establish the `django_site` and `socialaccount` relational schemas.
    * `python manage.py migrate`
* **Automated Provider Configuration:** Run the custom management command to inject the Google OAuth credentials directly into the database, linking the `SocialApp` to the active `Site`.
    * `python manage.py setup_google_auth --id "YOUR_GOOGLE_CLIENT_ID" --secret "YOUR_GOOGLE_CLIENT_SECRET"`
* **Process Execution:**
    * Start Backend: `python manage.py runserver`
    * Start Frontend: `npm run dev`

---

## **3. Backend Infrastructure: Requirements & Configurations (Django)**

### **Core Package Dependencies**
* **`django-allauth`**: Handles the core heavy lifting of social authentication, including database modeling for social identities, bridging logic to external providers, and handling the OAuth handshake.
* **`dj-rest-auth`**: Provides a suite of REST API endpoints (login, logout, password reset) that wrap around standard Django and `allauth` views, enabling headless/SPA integration.
* **`djangorestframework` & `djangorestframework-authtoken`**: The foundational API engine and the provisioning system for token-based authorization.
* **`django-cors-headers`**: A critical security middleware required to allow the React development server (running on a different port) to make cross-origin requests to the Django API.

### **`settings.py` Configuration Directives**
* **`INSTALLED_APPS` Hierarchy:** The order of installed applications dictates template and command resolution.
    * `django.contrib.sites`: Required dependency for `allauth` to map social applications to specific domain spaces.
    * `rest_framework` & `rest_framework.authtoken`: API and token management.
    * `dj_rest_auth` & `dj_rest_auth.registration`: The headless endpoints.
    * `allauth`, `allauth.account`, `allauth.socialaccount`, `allauth.socialaccount.providers.google`: The identity resolution engine and specific provider plugin.
    * `corsheaders`: Must be installed to manage pre-flight `OPTIONS` requests.
* **Security & Middleware:**
    * `corsheaders.middleware.CorsMiddleware` must be placed at the absolute top of the `MIDDLEWARE` array to ensure CORS headers are injected before any Django view logic or permission checks process the incoming React request.
    * `CORS_ALLOWED_ORIGINS = ["http://localhost:5173"]`: Explicitly whitelists the Vite/React development port.
* **Site Configuration:**
    * `SITE_ID = 1`: Tells `allauth` which `django.contrib.sites.models.Site` object represents the current runtime environment.
* **Authentication Behavior Modifications:**
    * `ACCOUNT_EMAIL_VERIFICATION = 'none'`: Bypasses the mandatory email verification step, which is highly recommended for headless social-auth implementations where Google has already verified the email.
    * `ACCOUNT_LOGIN_METHODS = {'email', 'username'}`: Modern `allauth` syntax defining valid authentication identifiers.
    * `REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES']`: Configured to use `TokenAuthentication` as the primary authorization mechanism for protected endpoints.

---

## **4. Backend Architecture: Routing & Internal Mechanics**

### **URL Namespace Requirements (`urls.py`)**
* **The `accounts/` Namespace:** * `path('accounts/', include('allauth.urls'))`
    * **Architectural Note:** Even though the application is headless (React), `dj-rest-auth` internally utilizes Django's `reverse()` URL resolution to locate `allauth` views (such as email confirmation or password reset templates). If the `accounts/` plural namespace is omitted or singularized to `account/`, `dj-rest-auth` will trigger a `NoReverseMatch` server error during specific auth lifecycle events.
* **The API Namespaces:**
    * `path('api/v2/auth/', include('dj_rest_auth.urls'))`: Exposes standard endpoints like `/login/`, `/logout/`, `/user/`.
    * `path('api/v2/auth/registration/', include('dj_rest_auth.registration.urls'))`: Exposes standard local-signup endpoints.

### **Internal Database Mapping (The `allauth` Schema)**
* **`auth.User`**: The standard Django user model. Upon successful Google validation, a new record is generated here (or mapped to an existing one via email).
* **`socialaccount.SocialApp`**: Represents the Google OAuth configuration. Contains the `client_id`, `secret`, and `provider` name. It must have a Many-to-Many relationship established with the active `Site`.
* **`socialaccount.SocialAccount`**: The bridging table. It maps an `auth.User` to a specific provider (`google`) using the unique `uid` (Google's internal "sub" claim). This prevents duplicate accounts if a user changes their Google email.

---

## **5. Custom Backend Implementation: Classes & Commands**

### **The Gateway View (`GoogleLogin`)**
* **Implementation:** A custom class inheriting from `dj_rest_auth.registration.views.SocialLoginView`.
* **Adapter Definition:** `adapter_class = allauth.socialaccount.providers.google.views.GoogleOAuth2Adapter` tells the view exactly which provider logic to use to decode the incoming token.
* **Client Definition:** `client_class = allauth.socialaccount.providers.oauth2.client.OAuth2Client` manages the HTTP bindings for the external network request to Google's verification servers.
* **Routing:** Mapped to `api/v2/auth/google/`. This is the exact endpoint the React application POSTs the `access_token` to.

### **The Automation Command (`setup_google_auth.py`)**
* **Purpose:** Eliminates the human error associated with manual Django Admin configuration for OAuth apps, ensuring clean, scriptable CI/CD pipelines and developer onboarding.
* **Internal Logic:**
    * Locates or creates `Site` ID 1 and updates the domain to `localhost:8000`.
    * Utilizes `update_or_create` on the `SocialApp` model, explicitly passing the `provider='google'` string.
    * Establishes the `.sites.add(site)` Many-to-Many binding.
* **Extended Verification Logic (`--check` flag):** Queries the `SocialAccount` model filtering by `provider='google'` and traverses the foreign key to the `User` model to output a terminal report of successfully authenticated entities, aiding in integration debugging.

---

## **6. Frontend Infrastructure: Requirements & Configuration (React)**

### **Core NPM Dependencies**
* **`@react-oauth/google`**: The industry-standard wrapper for integrating the modern Google Identity Services SDK into a React component tree.
* **`axios`**: The HTTP client used for handling the asynchronous POST requests to the Django backend.

### **Environment Variable Management (`.env`)**
* `VITE_GOOGLE_CLIENT_ID`: The public identifier provisioned by the Google Cloud Console. *Critical Note: This must be a "Web Application" client ID with `http://localhost:5173` listed in the Authorized JavaScript Origins.*
* `VITE_API_BASE_URL`: Defines the network path to the Django instance (`http://localhost:8000/api/v2`).

---

## **7. Frontend Architecture: Components & API Handshake**

### **The Provider Wrapper (`main.jsx`)**
* **Implementation:** The entire application context is wrapped within the `<GoogleOAuthProvider clientId={...}>`.
* **Purpose:** This asynchronously injects the necessary Google JavaScript SDKs into the browser DOM and establishes a global context, ensuring that any child component can trigger the OAuth prompt without reloading external assets.

### **The Authentication Flow (`App.jsx` & `api.js`)**
* **The Implicit Flow Trigger:** Utilizing the `useGoogleLogin` hook, the React application bypasses the traditional server-side redirect flow. When triggered, it opens a secure browser pop-up.
* **Token Acquisition:** Upon user consent, Google directly provisions an `access_token` to the React state (`onSuccess` callback).
* **The Backend Handshake:**
    * React utilizes `axios` to POST a JSON payload: `{"access_token": "<token_string>"}` to the custom Django `GoogleLogin` view.
    * *Architectural Note:* `dj-rest-auth` specifically looks for the `access_token` key in the request body for Google validation.
* **Session Finalization:**
    * Django responds with a 200 OK containing a JSON payload with a `key` property (the DRF authorization token).
    * The frontend stores this token locally (e.g., in `localStorage` for this minimal implementation) and updates internal React state to conditionally render the "Logged In" UI.
    * All subsequent protected API calls must include this token in the header: `Authorization: Token <key>`.