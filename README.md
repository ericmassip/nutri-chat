# NutriChat

A web application that enables nutritionists to share nutritional plans with their clients through an interactive chat interface.

### Overview

NutriChat allows nutritionists to upload their clients' nutritional plans in various document formats. Clients can then access and interact with their personalized plans through a conversational AI interface, making nutritional guidance more accessible and engaging.

### Key Features

* Document Upload: Nutritionists can upload nutritional plans in multiple formats (PDF, DOCX, etc.)
* Interactive Chat: Clients interact with their nutritional plans through an AI-powered chat interface
* Secure Access: Client-specific access to their personalized nutritional information

### Tech Stack

* Package manager: uv
* Backend: Django
* Frontend: HTMX
* AI/Chat: LangGraph

### Project Status

🚧 In Planning Phase - Architecture and features are still being defined.

### Getting Started

Documentation for setup and installation will be added as the project develops.

#### Running the Application

You have two options for serving static files:

**Environment variables:**

Create a `.env` file in the project root:
```bash
GOOGLE_API_KEY=your-google-api-key
```

**Option 1: Development mode (recommended for development)**
```bash
# Terminal 1: Start Vite dev server with hot reload
npm run dev

# Terminal 2: Start Django ASGI server
uvicorn webappconf.asgi:application --host 0.0.0.0 --port 8000 --reload
```

**Option 2: Production-like mode**
```bash
# Build static files and collect them
npm run build
python manage.py collectstatic

# Start Django ASGI server
uvicorn webappconf.asgi:application --host 0.0.0.0 --port 8000
```

> **Note:** The chat feature uses async views with SSE streaming, which requires an ASGI server.
> `python manage.py runserver` (WSGI) still works for non-chat pages, but `uvicorn` is needed for full functionality.

#### Testing on Other Devices (Same WiFi Network)

To test the app on any device connected to the same WiFi network as your laptop:

1. Build and collect static files (required - Vite dev server isn't accessible from other devices):
   ```bash
   npm run build
   python manage.py collectstatic
   ```

2. Find your laptop's local IP address:
   ```bash
   # macOS/Linux
   ipconfig getifaddr en0
   ```

3. Run the ASGI server with `0.0.0.0` to accept connections from any IP:
   ```bash
   uvicorn webappconf.asgi:application --host 0.0.0.0 --port 8000
   ```

4. Update `ALLOWED_HOSTS` in `webappconf/settings.py`:
   ```python
   ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'your-local-ip']
   ```

5. Access the app from any device on your network:
   ```
   http://your-local-ip:8000
   ```

---

_Built for nutritionists and their clients_
