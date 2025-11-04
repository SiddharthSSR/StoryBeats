# 🚀 StoryBeats Complete Setup Guide

Step-by-step instructions to get StoryBeats running on your machine. This guide covers everything from prerequisites to running the full application.

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [System Requirements](#system-requirements)
3. [Getting API Keys](#getting-api-keys)
4. [Backend Setup](#backend-setup)
5. [Frontend Setup](#frontend-setup)
6. [Running the Application](#running-the-application)
7. [Testing the Setup](#testing-the-setup)
8. [Troubleshooting](#troubleshooting)
9. [Next Steps](#next-steps)

---

## Prerequisites

### Required Software

- **Python**: Version 3.9 or higher
  - Check: `python --version` or `python3 --version`
  - Download: [python.org](https://www.python.org/downloads/)

- **Node.js**: Version 16 or higher
  - Check: `node --version`
  - Download: [nodejs.org](https://nodejs.org/)

- **npm**: Usually comes with Node.js
  - Check: `npm --version`

- **Git**: For cloning the repository
  - Check: `git --version`
  - Download: [git-scm.com](https://git-scm.com/)

### Required Accounts

- **Spotify Account** (free or premium)
- **OpenAI Account** (for GPT-4o) OR **Anthropic Account** (for Claude)

### Operating System Support

- macOS (tested)
- Linux (should work)
- Windows (with minor command adjustments)

---

## System Requirements

### Minimum
- 4GB RAM
- 2GB free disk space
- Internet connection

### Recommended
- 8GB RAM
- 5GB free disk space (for dependencies and virtual environments)
- Stable internet connection (for API calls)

---

## Getting API Keys

### 1. Spotify API Setup

#### 1.1 Create Spotify Developer App

1. **Go to Spotify Developer Dashboard**
   - Visit: [https://developer.spotify.com/dashboard](https://developer.spotify.com/dashboard)
   - Log in with your Spotify account (create one if needed)

2. **Create a New App**
   - Click the **"Create app"** button (green button on the right)

3. **Fill in App Details**
   ```
   App name: StoryBeats
   App description: AI-powered music recommendations for Instagram stories
   Website: http://127.0.0.1:3000
   Redirect URIs: http://127.0.0.1:3000/callback
   ```

4. **Select API/SDKs**
   - Check: **"Web API"**

5. **Agree to Terms**
   - Check: "I understand and agree with Spotify's Developer Terms of Service and Design Guidelines"

6. **Click "Save"**

#### 1.2 Get Your Credentials

1. **Open Your App**
   - Click on your newly created "StoryBeats" app

2. **Go to Settings**
   - Click the **"Settings"** button (top right)

3. **Copy Client ID**
   - You'll see **Client ID** displayed
   - Click to copy or manually copy the value
   - **Save this somewhere safe** (you'll need it for the .env file)

4. **Copy Client Secret**
   - Click **"View client secret"**
   - Copy the revealed secret
   - **Save this somewhere safe** (you'll need it for the .env file)

5. **Verify Redirect URIs**
   - Make sure `http://127.0.0.1:3000/callback` is listed
   - Add it if missing (click "Add" after entering)

#### Important Notes on Spotify Configuration

**CRITICAL**: Spotify requires explicit loopback IP addresses:
- ✅ **ALLOWED**: `http://127.0.0.1:3000/callback`
- ❌ **NOT ALLOWED**: `http://localhost:3000/callback`

This is per [Spotify's official redirect URI documentation](https://developer.spotify.com/documentation/web-api/concepts/redirect_uri). HTTP is permitted ONLY for loopback addresses (127.0.0.1 or [::1]). For production, you MUST use HTTPS.

---

### 2. LLM API Setup

Choose **ONE** of the following options:

#### Option A: OpenAI (Recommended)

**Why OpenAI?**
- GPT-4o vision model is highly accurate
- Fast response times
- Better JSON formatting consistency

**Setup Steps:**

1. **Create OpenAI Account**
   - Visit: [https://platform.openai.com/signup](https://platform.openai.com/signup)
   - Sign up with email or Google/Microsoft account

2. **Add Payment Method**
   - Go to: [https://platform.openai.com/settings/organization/billing/overview](https://platform.openai.com/settings/organization/billing/overview)
   - Add a credit card (required for API access)
   - Consider setting usage limits in billing settings

3. **Create API Key**
   - Go to: [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)
   - Click **"Create new secret key"**
   - Give it a name: `StoryBeats`
   - Click **"Create secret key"**
   - **Copy the key immediately** (you won't be able to see it again!)
   - **Save this somewhere safe**

4. **Verify Access to GPT-4o**
   - GPT-4o should be available by default
   - If not, check your account tier at [https://platform.openai.com/settings/organization/limits](https://platform.openai.com/settings/organization/limits)

**Cost Estimate:**
- GPT-4o vision: ~$0.01-0.02 per image analysis
- Expect ~$0.50-1.00 for 50-100 image analyses

#### Option B: Anthropic Claude

**Why Anthropic?**
- Claude 3.5 Sonnet has excellent vision capabilities
- Good alternative if you prefer Anthropic
- Competitive pricing

**Setup Steps:**

1. **Create Anthropic Account**
   - Visit: [https://console.anthropic.com/](https://console.anthropic.com/)
   - Sign up with email

2. **Add Payment Method** (if required)
   - Navigate to billing settings
   - Add payment information

3. **Create API Key**
   - Go to: [https://console.anthropic.com/settings/keys](https://console.anthropic.com/settings/keys)
   - Click **"Create Key"**
   - Give it a name: `StoryBeats`
   - Click **"Create Key"**
   - **Copy the key immediately**
   - **Save this somewhere safe**

**Cost Estimate:**
- Claude 3.5 Sonnet: ~$0.01-0.015 per image analysis
- Similar costs to OpenAI

---

## Backend Setup

### Step 1: Navigate to Backend Directory

```bash
cd StoryBeats/backend
```

### Step 2: Verify Virtual Environment

The project comes with a pre-configured virtual environment. Verify it exists:

```bash
ls venv
```

If `venv/` doesn't exist, create it:

**macOS/Linux:**
```bash
python3 -m venv venv
```

**Windows:**
```bash
python -m venv venv
```

### Step 3: Activate Virtual Environment

**macOS/Linux:**
```bash
source venv/bin/activate
```

**Windows (Command Prompt):**
```bash
venv\Scripts\activate
```

**Windows (PowerShell):**
```bash
venv\Scripts\Activate.ps1
```

You should see `(venv)` appear at the start of your command prompt.

### Step 4: Install Python Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- Flask (web framework)
- OpenAI SDK (version 1.12.0)
- Anthropic SDK
- Pillow (image processing)
- httpx, requests (HTTP clients)
- python-dotenv (environment variables)
- Other dependencies

**Expected output:**
```
Successfully installed flask-3.x.x openai-1.12.0 anthropic-x.x.x ...
```

### Step 5: Configure Environment Variables

1. **Verify .env file exists:**
   ```bash
   ls .env
   ```

2. **Open .env file in your text editor:**

   **macOS/Linux:**
   ```bash
   nano .env
   ```

   **Or use VS Code:**
   ```bash
   code .env
   ```

3. **Update with your credentials:**

   ```env
   # Spotify API
   SPOTIFY_CLIENT_ID=your_spotify_client_id_here
   SPOTIFY_CLIENT_SECRET=your_spotify_client_secret_here
   SPOTIFY_REDIRECT_URI=http://127.0.0.1:3000/callback

   # LLM Provider ('openai' or 'anthropic')
   LLM_PROVIDER=openai

   # OpenAI (if using OpenAI)
   OPENAI_API_KEY=your_openai_api_key_here
   OPENAI_MODEL=gpt-4o

   # Anthropic (if using Anthropic)
   ANTHROPIC_API_KEY=your_anthropic_api_key_here
   ANTHROPIC_MODEL=claude-3-5-sonnet-20241022

   # App Settings
   DEBUG=True
   PORT=5001
   HOST=0.0.0.0
   ```

4. **Replace placeholder values:**
   - Replace `your_spotify_client_id_here` with your actual Spotify Client ID
   - Replace `your_spotify_client_secret_here` with your actual Spotify Client Secret
   - Replace `your_openai_api_key_here` with your OpenAI API key (if using OpenAI)
   - Replace `your_anthropic_api_key_here` with your Anthropic API key (if using Anthropic)

5. **Choose your LLM provider:**
   - If using OpenAI: Set `LLM_PROVIDER=openai` and fill in `OPENAI_API_KEY`
   - If using Anthropic: Set `LLM_PROVIDER=anthropic` and fill in `ANTHROPIC_API_KEY`

6. **Save and close the file**
   - In nano: Press `Ctrl+X`, then `Y`, then `Enter`
   - In vim: Press `Esc`, type `:wq`, press `Enter`
   - In VS Code: Press `Cmd+S` (Mac) or `Ctrl+S` (Windows/Linux)

### Step 6: Verify Backend Configuration

```bash
python -c "from config import Config; print('Config loaded successfully!')"
```

If you see "Config loaded successfully!", your environment is configured correctly.

If you see errors about missing API keys, double-check your .env file.

### Step 7: Test Backend Startup

```bash
python app.py
```

**Expected output:**
```
 * Running on http://0.0.0.0:5001
 * Restarting with stat
 * Debugger is active!
```

**Important Notes:**
- The app runs on port **5001** (not 5000) to avoid conflicts with macOS AirPlay
- Press `Ctrl+C` to stop the server

---

## Frontend Setup

### Step 1: Open New Terminal Window

Keep the backend running in the first terminal. Open a **new terminal window** or tab.

### Step 2: Navigate to Frontend Directory

```bash
cd StoryBeats/frontend
```

### Step 3: Install Node Dependencies

```bash
npm install
```

This will install:
- React 19
- Vite 7
- Other dependencies

**Expected output:**
```
added XXX packages in XXs
```

This may take 2-5 minutes depending on your internet speed.

### Step 4: Verify Frontend Configuration

Check that `vite.config.js` has the correct proxy settings:

```bash
cat vite.config.js
```

Should include:
```javascript
server: {
  port: 3000,
  proxy: {
    '/api': {
      target: 'http://127.0.0.1:5001',
      changeOrigin: true
    }
  }
}
```

---

## Running the Application

### Terminal Setup

You'll need **TWO terminal windows**:

#### Terminal 1: Backend (Flask)

```bash
cd StoryBeats/backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
python app.py
```

**Expected output:**
```
 * Running on http://0.0.0.0:5001
 * Restarting with stat
 * Debugger is active!
```

#### Terminal 2: Frontend (React + Vite)

```bash
cd StoryBeats/frontend
npm run dev
```

**Expected output:**
```
  VITE v7.x.x  ready in XXX ms

  ➜  Local:   http://localhost:3000/
  ➜  Network: http://192.168.x.x:3000/
```

### Access the Application

Open your web browser and go to:
```
http://localhost:3000
```

You should see the StoryBeats interface with:
- Dark Spotify-inspired theme
- Green accent colors (#1db954)
- Photo upload area

---

## Testing the Setup

### Test 1: Backend Health Check

**Terminal 3** (or use curl):
```bash
curl http://127.0.0.1:5001/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "service": "StoryBeats API"
}
```

### Test 2: Upload a Test Photo

1. **Open the app**: `http://localhost:3000`

2. **Upload a photo**:
   - Click the upload area or drag a photo
   - Use any Instagram-style photo (landscape, portrait, food, selfie, etc.)

3. **Wait for analysis** (5-10 seconds):
   - You should see a loading state
   - Backend will analyze the photo with LLM
   - Backend will fetch matching songs from Spotify

4. **View results**:
   - Photo analysis card with mood, themes, energy, valence
   - 5 song recommendations with:
     - Album artwork
     - Song name and artist
     - Audio preview player (if available)
     - "Open in Spotify" link
   - Mix of English and Hindi/Indian songs based on photo's cultural vibe

5. **Test "Get 5 More Songs"**:
   - Click the "Get 5 More Songs" button
   - Should get 5 new songs matching the same vibe
   - No duplicates from the previous results
   - Can click multiple times for more variety

### Test 3: Verify API Keys

**Check backend terminal** for logs like:

**OpenAI:**
```
[OpenAI] Starting image analysis with model: gpt-4o
[OpenAI] Client initialized successfully
[OpenAI] API call successful!
```

**Anthropic:**
```
[ImageAnalyzer] Using Anthropic
[ImageAnalyzer] analyze_image called with provider: anthropic
```

**Spotify:**
```
[Spotify] Getting recommendations...
[Spotify] Found XX English tracks
[Spotify] Found XX Hindi tracks
```

---

## Troubleshooting

### Common Issues and Solutions

#### Issue 1: Backend won't start - "Address already in use"

**Problem**: Port 5001 is already in use

**Solution 1**: Kill the process on port 5001
```bash
# macOS/Linux
lsof -ti:5001 | xargs kill -9

# Windows
netstat -ano | findstr :5001
taskkill /PID <PID> /F
```

**Solution 2**: Change the port in `.env`
```env
PORT=5002
```

#### Issue 2: "Configuration errors: SPOTIFY_CLIENT_ID is required"

**Problem**: Environment variables not loaded

**Solutions**:
1. Check `.env` file exists in `backend/` directory
2. Verify no extra spaces or quotes around values
3. Restart the backend server
4. Check for typos in variable names

**Correct format:**
```env
SPOTIFY_CLIENT_ID=abc123xyz789
```

**Incorrect formats:**
```env
SPOTIFY_CLIENT_ID = abc123xyz789  # Extra spaces
SPOTIFY_CLIENT_ID="abc123xyz789"  # Quotes (remove them)
```

#### Issue 3: "No API key found for LLM_PROVIDER"

**Problem**: LLM provider mismatch

**Solution**: Verify `LLM_PROVIDER` matches your API key:

If using OpenAI:
```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
```

If using Anthropic:
```env
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
```

#### Issue 4: Spotify returns 401 Unauthorized

**Problem**: Invalid Spotify credentials

**Solutions**:
1. Verify Client ID and Secret are correct (no typos)
2. Check for extra spaces or hidden characters
3. Regenerate Client Secret in Spotify Dashboard if needed
4. Make sure you're using credentials from the correct app

#### Issue 5: "Invalid redirect URI"

**Problem**: Redirect URI mismatch

**Solutions**:
1. Check `.env` has: `SPOTIFY_REDIRECT_URI=http://127.0.0.1:3000/callback`
2. Verify Spotify Dashboard has **exact same URI**
3. Make sure it's `127.0.0.1` NOT `localhost`
4. Check for trailing slashes (should not have one)

#### Issue 6: OpenAI JSONDecodeError

**Problem**: Can't parse OpenAI response

**Solutions**:
1. Verify you're using `gpt-4o` model (not `gpt-4-vision-preview`)
2. Check OpenAI API key is valid
3. Ensure you have credits/quota remaining
4. This should be fixed in current version (has markdown stripping)

#### Issue 7: "ModuleNotFoundError: No module named 'flask'"

**Problem**: Virtual environment not activated or dependencies not installed

**Solutions**:
1. Activate virtual environment:
   ```bash
   source venv/bin/activate  # macOS/Linux
   venv\Scripts\activate     # Windows
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

#### Issue 8: Frontend shows "Failed to fetch"

**Problem**: Backend not running or proxy misconfigured

**Solutions**:
1. Verify backend is running on port 5001
2. Check `vite.config.js` proxy points to `http://127.0.0.1:5001`
3. Restart frontend dev server
4. Check browser console for CORS errors

#### Issue 9: Songs not displaying

**Problem**: API response issues

**Solutions**:
1. Check backend terminal for Spotify API errors
2. Verify Spotify credentials are correct
3. Try uploading a different photo
4. Check internet connection
5. Look for 403/404 errors in backend logs

#### Issue 10: "No preview available" for all songs

**Problem**: Not all Spotify tracks have preview URLs

**Solution**: This is a Spotify limitation, not a bug. Try:
- Click "Get 5 More Songs" for different tracks
- Use "Open in Spotify" links to listen to full songs
- Some regions/tracks don't provide previews

#### Issue 11: Virtual environment creation fails

**Problem**: Python venv module not available

**Solutions**:

**Ubuntu/Debian:**
```bash
sudo apt-get install python3-venv
```

**macOS:**
```bash
brew install python3
```

**Windows:** Reinstall Python with "pip" option checked

#### Issue 12: Port 5000 conflicts on macOS

**Problem**: macOS AirPlay Receiver uses port 5000

**Solution**: App is already configured to use port 5001. If issues persist:
1. Disable AirPlay Receiver in System Settings > Sharing
2. Use a different port by changing `PORT=5002` in `.env`

### Debugging Tips

#### Enable Detailed Logging

In `backend/.env`:
```env
DEBUG=True
```

#### Check Backend Logs

Watch the backend terminal for detailed logs:
- API calls to OpenAI/Anthropic
- Spotify authentication
- Song search and filtering
- Errors and exceptions

#### Check Frontend Console

Open browser DevTools (F12):
- **Console tab**: Check for JavaScript errors
- **Network tab**: Check API calls to `/api/analyze` and `/api/more-songs`
- Look for 4xx/5xx HTTP errors

#### Test API Directly

Use curl or Postman to test the API:

```bash
curl -X POST http://127.0.0.1:5001/api/analyze \
  -F "photo=@/path/to/your/image.jpg"
```

---

## Security Best Practices

### API Key Security

1. **Never commit `.env` files**
   - Already in `.gitignore`
   - Double-check before `git add`

2. **Never share API keys**
   - In screenshots
   - In error messages
   - In public repositories

3. **Rotate keys if exposed**
   - Immediately regenerate compromised keys
   - Update `.env` with new keys

4. **Use environment variables in production**
   - Don't use `.env` files in production
   - Use platform-specific secret management:
     - Heroku: Config Vars
     - AWS: Secrets Manager
     - Vercel: Environment Variables

5. **Set usage limits**
   - OpenAI: Set monthly spending limits
   - Anthropic: Set budget alerts
   - Monitor usage regularly

### Production Deployment

For production, you'll need:

1. **HTTPS for redirect URIs**
   - Spotify requires HTTPS in production
   - Get SSL certificate (Let's Encrypt, Cloudflare)
   - Update redirect URI to `https://yourdomain.com/callback`

2. **Environment variable management**
   - Use platform-specific secret storage
   - Never hardcode API keys

3. **CORS configuration**
   - Restrict origins in Flask-CORS
   - Only allow your production domain

4. **Rate limiting**
   - Add rate limiting to API endpoints
   - Prevent abuse and excessive API costs

---

## Next Steps

### Development Workflow

1. **Make changes to backend**:
   - Edit Python files in `backend/`
   - Flask auto-reloads on file changes (if DEBUG=True)

2. **Make changes to frontend**:
   - Edit React components in `frontend/src/`
   - Vite provides instant hot-reload

3. **Test thoroughly**:
   - Test with various photo types
   - Check different moods and cultural vibes
   - Verify language mix is appropriate

### Feature Ideas

- Add user authentication
- Save favorite songs
- Create Spotify playlists from recommendations
- Share results to Instagram directly
- Support video analysis
- Add more languages (Spanish, French, etc.)

### Deployment Options

- **Heroku**: Simple Python + Node.js deployment
- **Vercel**: Great for React frontend (deploy backend separately)
- **AWS**: EC2 for backend, S3 + CloudFront for frontend
- **DigitalOcean**: App Platform supports both frontend and backend
- **Railway**: Easy full-stack deployment

---

## Additional Resources

### Documentation

- **Spotify Web API**: [https://developer.spotify.com/documentation/web-api](https://developer.spotify.com/documentation/web-api)
- **OpenAI API**: [https://platform.openai.com/docs](https://platform.openai.com/docs)
- **Anthropic API**: [https://docs.anthropic.com](https://docs.anthropic.com)
- **Flask**: [https://flask.palletsprojects.com/](https://flask.palletsprojects.com/)
- **React**: [https://react.dev/](https://react.dev/)
- **Vite**: [https://vitejs.dev/](https://vitejs.dev/)

### Community

- Open issues on GitHub for bugs
- Suggest features and improvements
- Contribute to the project

---

## Summary Checklist

Before considering your setup complete, verify:

- [ ] Python 3.9+ installed
- [ ] Node.js 16+ installed
- [ ] Spotify Developer App created
- [ ] Spotify Client ID and Secret obtained
- [ ] OpenAI OR Anthropic API key obtained
- [ ] Backend `.env` configured with all credentials
- [ ] Backend dependencies installed (`pip install -r requirements.txt`)
- [ ] Frontend dependencies installed (`npm install`)
- [ ] Backend running on http://127.0.0.1:5001
- [ ] Frontend running on http://localhost:3000
- [ ] Health check endpoint returns success
- [ ] Photo upload and analysis works
- [ ] Song recommendations display correctly
- [ ] "Get 5 More Songs" button works
- [ ] Audio previews play (when available)
- [ ] Spotify links open correctly

---

## Need Help?

If you're still experiencing issues after following this guide:

1. **Check terminal output** for specific error messages
2. **Review the [Troubleshooting](#troubleshooting) section** above
3. **Check browser console** (F12) for frontend errors
4. **Test API directly** with curl to isolate frontend vs backend issues
5. **Review API documentation** for any service-specific issues
6. **Open an issue** on GitHub with:
   - Detailed error messages
   - Steps to reproduce
   - Your OS and software versions
   - What you've tried so far

---

**Built with ❤️ for music lovers who want the perfect soundtrack for their stories!**
