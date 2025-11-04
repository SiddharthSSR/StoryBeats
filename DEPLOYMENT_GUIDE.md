# 🚀 StoryBeats Deployment Guide

Complete guide to deploy StoryBeats to production with HTTPS for both frontend and backend.

**Successfully Deployed Example:**
- **Frontend**: https://story-beats.vercel.app
- **Backend**: https://storybeats-backend.up.railway.app
- **Platform**: Vercel (Frontend) + Railway (Backend)
- **Deployment Time**: ~30-45 minutes
- **Status**: ✅ Live and working!

---

## 📋 Table of Contents

1. [Real Deployment Experience](#real-deployment-experience)
2. [Deployment Options](#deployment-options)
3. [Pre-Deployment Checklist](#pre-deployment-checklist)
4. [Option 1: Vercel + Railway (Recommended)](#option-1-vercel--railway-recommended)
5. [Option 2: Netlify + Render](#option-2-netlify--render)
6. [Option 3: All-in-One with Railway](#option-3-all-in-one-with-railway)
7. [Post-Deployment Steps](#post-deployment-steps)
8. [Troubleshooting](#troubleshooting)
9. [Common Issues We Encountered](#common-issues-we-encountered)

---

## Real Deployment Experience

This section documents the actual deployment process we completed, including all the issues encountered and how they were resolved.

### Timeline & Steps Taken

**Total Time**: ~45 minutes
**Platform**: Vercel + Railway
**Result**: Successfully deployed and working

### Phase 1: Backend Deployment to Railway (15 minutes)

**Steps:**
1. Created Railway account with GitHub
2. Created new project from StoryBeats repository
3. Configured backend service:
   - Root Directory: `backend`
   - Build Command: Automatic (Railway detected Python)
   - Start Command: `python app.py`
4. Generated public domain: `https://storybeats-backend.up.railway.app`

**Issue Encountered #1: Pillow Build Error**
```
ERROR: Getting requirements to build wheel did not run successfully.
KeyError: '__version__'
```

**Root Cause**: Railway uses Python 3.13.9, but Pillow 10.1.0 has compatibility issues with Python 3.13.

**Solution**: Updated `requirements.txt`:
```python
# Changed from:
pillow==10.1.0
openai==1.54.0

# Changed to:
pillow==10.4.0      # Python 3.13 compatible
openai==1.12.0      # Stable version with httpx 0.27.2
httpx==0.27.2       # Added explicitly
```

**Issue Encountered #2: Environment Variables Missing**
```
spotipy.oauth2.SpotifyOauthError: No client_id.
Pass it or set a SPOTIPY_CLIENT_ID environment variable.
```

**Root Cause**: Forgot to add environment variables in Railway dashboard.

**Solution**: Added all required environment variables in Railway:
```bash
SPOTIFY_CLIENT_ID=<your_value>
SPOTIFY_CLIENT_SECRET=<your_value>
SPOTIFY_REDIRECT_URI=http://127.0.0.1:3000/callback  # Updated later
LLM_PROVIDER=openai
OPENAI_API_KEY=<your_value>
OPENAI_MODEL=gpt-4o
DEBUG=False
PORT=5001
HOST=0.0.0.0
```

**Verification**: Tested health endpoint successfully
```bash
curl https://storybeats-backend.up.railway.app/health
# Response: {"service":"StoryBeats API","status":"healthy"}
```

### Phase 2: Frontend Deployment to Vercel (10 minutes)

**Steps:**
1. Created Vercel account with GitHub
2. Imported StoryBeats repository
3. Configured project:
   - Framework Preset: Vite
   - Root Directory: `frontend`
   - Build Command: `npm run build`
   - Output Directory: `dist`
4. Added environment variable:
   ```
   VITE_API_URL=https://storybeats-backend.up.railway.app
   ```
5. Deployed successfully
6. Got URL: `https://story-beats.vercel.app`

**No Issues**: Frontend deployed successfully on first try!

### Phase 3: Configuration Updates (15 minutes)

**Step 1: Update Backend CORS**

Updated `backend/app.py` to allow production frontend:
```python
ALLOWED_ORIGINS = [
    'http://localhost:3000',
    'http://127.0.0.1:3000',
    'https://story-beats.vercel.app',  # Added
]
```

Committed and pushed:
```bash
git add backend/app.py
git commit -m "Add production Vercel URL to CORS allowed origins"
git push origin main
```

Railway auto-deployed the update.

**Step 2: Update Spotify Redirect URI**

1. Went to Spotify Developer Dashboard
2. Opened StoryBeats app → Settings
3. Added redirect URI: `https://story-beats.vercel.app/callback`
4. Kept existing `http://127.0.0.1:3000/callback` for local dev
5. Clicked Save

**Step 3: Update Railway Environment Variable**

1. Went to Railway dashboard → Variables
2. Updated `SPOTIFY_REDIRECT_URI`:
   - From: `http://127.0.0.1:3000/callback`
   - To: `https://story-beats.vercel.app/callback`
3. Railway auto-redeployed (took 2 minutes)

### Phase 4: Testing (5 minutes)

**Tests Performed:**
1. ✅ Visited `https://story-beats.vercel.app`
2. ✅ Uploaded test photo
3. ✅ Received 5 song recommendations
4. ✅ Verified language mix (English + Hindi)
5. ✅ Tested "Get 5 More Songs" button
6. ✅ Verified no duplicates
7. ✅ Tested audio previews
8. ✅ Tested Spotify links
9. ✅ Verified HTTPS lock icons on both URLs

**Result**: All tests passed! ✅

### Key Learnings

**What Worked Well:**
- GitHub integration with both platforms
- Auto-deployment on git push
- Automatic HTTPS certificates
- Environment variable management
- Vercel's instant deployments

**Gotchas to Watch For:**
1. **Python 3.13 compatibility** - Check package versions
2. **Environment variables** - Must be set in platform dashboards
3. **CORS configuration** - Must include production URL
4. **Spotify redirect URI** - Must use HTTPS in production
5. **Railway auto-redeploy** - Triggered on env var changes

**Costs:**
- Vercel: $0 (free tier)
- Railway: ~$5/month (usage-based)
- OpenAI API: ~$5-20/month (depends on usage)
- **Total**: ~$10-25/month

### Files Modified for Deployment

**backend/requirements.txt**:
```diff
- pillow==10.1.0
+ pillow==10.4.0
- openai==1.54.0
+ openai==1.12.0
+ httpx==0.27.2
```

**backend/app.py**:
```diff
  ALLOWED_ORIGINS = [
      'http://localhost:3000',
      'http://127.0.0.1:3000',
+     'https://story-beats.vercel.app',
  ]
```

**No changes needed** to frontend code - already had environment variable support!

### Deployment Checklist Used

- [x] Code pushed to GitHub
- [x] Railway account created
- [x] Backend deployed to Railway
- [x] Environment variables added in Railway
- [x] Backend health check verified
- [x] Vercel account created
- [x] Frontend deployed to Vercel
- [x] Environment variable added in Vercel
- [x] CORS updated in backend
- [x] Spotify redirect URI updated
- [x] Railway env var updated
- [x] Production app tested end-to-end
- [x] Changes committed to GitHub

---

---

## Deployment Options

### Quick Comparison

| Platform Combo | Frontend | Backend | Cost | Difficulty | HTTPS | Auto-Deploy |
|----------------|----------|---------|------|------------|-------|-------------|
| **Vercel + Railway** | Vercel | Railway | $5/mo | Easy | ✅ | ✅ |
| **Netlify + Render** | Netlify | Render | Free* | Easy | ✅ | ✅ |
| **Railway (Both)** | Railway | Railway | $10/mo | Medium | ✅ | ✅ |
| **Vercel + Heroku** | Vercel | Heroku | $7/mo | Medium | ✅ | ✅ |

*Render free tier has limitations (spins down after inactivity)

### Our Recommendation: **Vercel + Railway**

**Why?**
- ✅ Automatic HTTPS on both frontend and backend
- ✅ Easy setup with GitHub integration
- ✅ Excellent performance and CDN
- ✅ Generous free tier for frontend
- ✅ Reliable backend hosting
- ✅ Great developer experience
- ✅ Automatic deployments on git push

---

## Pre-Deployment Checklist

Before deploying, ensure you have:

### Required Accounts
- [ ] GitHub account (code already pushed)
- [ ] Vercel account ([vercel.com](https://vercel.com))
- [ ] Railway account ([railway.app](https://railway.app))
- [ ] Spotify Developer account (already have)
- [ ] OpenAI or Anthropic API key (already have)

### Code Preparation
- [ ] Code pushed to GitHub
- [ ] `.env` file **NOT** pushed (check `.gitignore`)
- [ ] `.env.example` file present
- [ ] `requirements.txt` up to date
- [ ] `package.json` up to date

### API Keys Ready
- [ ] Spotify Client ID
- [ ] Spotify Client Secret
- [ ] OpenAI API Key (or Anthropic)

---

## Option 1: Vercel + Railway (Recommended)

### Part A: Deploy Backend to Railway

#### Step 1: Create Railway Account

1. **Go to Railway**
   - Visit: [https://railway.app](https://railway.app)
   - Click **"Login"** or **"Start a New Project"**

2. **Sign up with GitHub**
   - Click **"Login with GitHub"**
   - Authorize Railway to access your repositories

#### Step 2: Create New Project

1. **Start New Project**
   - Click **"New Project"**
   - Select **"Deploy from GitHub repo"**

2. **Select Repository**
   - Find and select **"StoryBeats"**
   - Railway will detect your repository

3. **Configure Service**
   - Railway will ask which folder to deploy
   - Click **"Add Service"** → **"GitHub Repo"**

#### Step 3: Configure Backend Service

1. **Set Root Directory**
   - In your service settings, go to **"Settings"**
   - Set **Root Directory**: `backend`
   - Set **Build Command**: `pip install -r requirements.txt`
   - Set **Start Command**: `python app.py`

2. **Add Environment Variables**
   - Go to **"Variables"** tab
   - Click **"New Variable"**
   - Add each variable:

   ```
   SPOTIFY_CLIENT_ID=your_spotify_client_id
   SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
   SPOTIFY_REDIRECT_URI=https://your-frontend-url.vercel.app/callback
   LLM_PROVIDER=openai
   OPENAI_API_KEY=your_openai_api_key
   OPENAI_MODEL=gpt-4o
   DEBUG=False
   PORT=5001
   HOST=0.0.0.0
   ```

   **Important**: We'll update `SPOTIFY_REDIRECT_URI` after deploying frontend

3. **Enable Public Networking**
   - Go to **"Settings"** → **"Networking"**
   - Click **"Generate Domain"**
   - Railway will give you a URL like: `https://your-app.up.railway.app`
   - **Save this URL** - this is your backend URL!

#### Step 4: Deploy Backend

1. **Trigger Deployment**
   - Railway automatically deploys when you connect
   - Watch the logs in the **"Deployments"** tab
   - Wait for deployment to complete (2-5 minutes)

2. **Verify Backend**
   - Once deployed, visit: `https://your-app.up.railway.app/health`
   - You should see:
     ```json
     {
       "status": "healthy",
       "service": "StoryBeats API"
     }
     ```

   - If you see an error, check the logs in Railway dashboard

---

### Part B: Deploy Frontend to Vercel

#### Step 1: Create Vercel Account

1. **Go to Vercel**
   - Visit: [https://vercel.com](https://vercel.com)
   - Click **"Sign Up"**

2. **Sign up with GitHub**
   - Select **"Continue with GitHub"**
   - Authorize Vercel

#### Step 2: Import Project

1. **Add New Project**
   - Click **"Add New..."** → **"Project"**
   - Click **"Import"** next to your **StoryBeats** repository

2. **Configure Project**
   - **Framework Preset**: Vite
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`

#### Step 3: Configure Frontend

1. **Environment Variables**

   Vercel needs to know where your backend is. Add this variable:

   - Click **"Environment Variables"**
   - Add variable:
     ```
     VITE_API_URL=https://your-app.up.railway.app
     ```

   Replace `your-app.up.railway.app` with your actual Railway backend URL

2. **Update vite.config.js for Production**

   We need to update the Vite config to use the environment variable in production:

   ```javascript
   // frontend/vite.config.js
   import { defineConfig } from 'vite'
   import react from '@vitejs/plugin-react'

   export default defineConfig({
     plugins: [react()],
     server: {
       port: 3000,
       proxy: {
         '/api': {
           target: process.env.VITE_API_URL || 'http://127.0.0.1:5001',
           changeOrigin: true
         }
       }
     }
   })
   ```

3. **Update Frontend Code for Production API**

   We need to update `App.jsx` to use the correct backend URL:

   ```javascript
   // frontend/src/App.jsx
   // At the top of the file, add:
   const API_URL = import.meta.env.VITE_API_URL || '';

   // Then in handlePhotoUpload:
   const response = await fetch(`${API_URL}/api/analyze`, {
     method: 'POST',
     body: formData
   })

   // And in handleGetMoreSongs:
   const response = await fetch(`${API_URL}/api/more-songs`, {
     method: 'POST',
     headers: {
       'Content-Type': 'application/json'
     },
     body: JSON.stringify({
       analysis: results.analysis,
       offset: offset,
       session_id: sessionId
     })
   })
   ```

#### Step 4: Deploy Frontend

1. **Click "Deploy"**
   - Vercel will build and deploy your frontend
   - Takes 2-5 minutes
   - Watch the build logs

2. **Get Your Frontend URL**
   - Once deployed, Vercel gives you a URL like:
   - `https://story-beats.vercel.app`
   - Or `https://your-project-name.vercel.app`
   - **Save this URL!**

---

### Part C: Update Spotify Redirect URI

Now that we have both URLs, we need to update Spotify settings:

1. **Go to Spotify Developer Dashboard**
   - Visit: [https://developer.spotify.com/dashboard](https://developer.spotify.com/dashboard)
   - Open your **StoryBeats** app
   - Click **"Settings"**

2. **Add Production Redirect URI**
   - Under **"Redirect URIs"**, click **"Add"**
   - Add: `https://your-frontend-url.vercel.app/callback`
   - Replace with your actual Vercel URL
   - Click **"Save"**

3. **Update Railway Environment Variable**
   - Go back to Railway dashboard
   - Go to **"Variables"**
   - Update `SPOTIFY_REDIRECT_URI` to:
     ```
     https://your-frontend-url.vercel.app/callback
     ```
   - This will trigger a re-deployment

---

### Part D: Enable CORS for Production

We need to update the Flask backend to allow requests from your Vercel domain:

1. **Update `backend/app.py`**

   Find the CORS configuration and update it:

   ```python
   from flask_cors import CORS

   # Allow both localhost (for development) and production domain
   ALLOWED_ORIGINS = [
       'http://localhost:3000',
       'http://127.0.0.1:3000',
       'https://your-frontend-url.vercel.app'  # Add your Vercel URL
   ]

   CORS(app, resources={
       r"/api/*": {
           "origins": ALLOWED_ORIGINS,
           "methods": ["GET", "POST"],
           "allow_headers": ["Content-Type"]
       }
   })
   ```

2. **Commit and Push Changes**
   ```bash
   git add .
   git commit -m "Add production CORS configuration and API URL handling"
   git push origin main
   ```

3. **Automatic Redeployment**
   - Railway will automatically redeploy backend
   - Vercel will automatically redeploy frontend
   - Wait 2-5 minutes for both to complete

---

### Part E: Test Production Deployment

1. **Visit Your Production Frontend**
   - Go to: `https://your-frontend-url.vercel.app`

2. **Test Photo Upload**
   - Upload a test photo
   - Wait for analysis (may take 10-15 seconds first time)
   - Verify you get song recommendations

3. **Test "Get More Songs"**
   - Click the button
   - Verify you get new recommendations

4. **Check HTTPS**
   - Verify the lock icon in browser address bar
   - Both frontend and backend should use HTTPS

---

## Option 2: Netlify + Render

### Part A: Deploy Backend to Render

#### Step 1: Create Render Account

1. **Go to Render**
   - Visit: [https://render.com](https://render.com)
   - Click **"Get Started"**
   - Sign up with GitHub

#### Step 2: Create New Web Service

1. **New Web Service**
   - Click **"New"** → **"Web Service"**
   - Connect your GitHub repository
   - Select **StoryBeats**

2. **Configure Service**
   ```
   Name: storybeats-backend
   Region: Choose closest to your users
   Branch: main
   Root Directory: backend
   Runtime: Python 3
   Build Command: pip install -r requirements.txt
   Start Command: python app.py
   ```

3. **Choose Plan**
   - **Free tier**: Available but spins down after 15 minutes of inactivity
   - **Starter**: $7/month, always on
   - Choose based on your needs

4. **Environment Variables**

   Click **"Advanced"** → **"Add Environment Variable"**

   Add all your environment variables:
   ```
   SPOTIFY_CLIENT_ID=your_value
   SPOTIFY_CLIENT_SECRET=your_value
   SPOTIFY_REDIRECT_URI=https://your-netlify-url.netlify.app/callback
   LLM_PROVIDER=openai
   OPENAI_API_KEY=your_value
   OPENAI_MODEL=gpt-4o
   DEBUG=False
   PORT=10000
   HOST=0.0.0.0
   ```

   **Note**: Render uses port 10000 by default

5. **Create Web Service**
   - Click **"Create Web Service"**
   - Render will deploy (5-10 minutes)
   - Your backend URL: `https://storybeats-backend.onrender.com`

### Part B: Deploy Frontend to Netlify

#### Step 1: Create Netlify Account

1. **Go to Netlify**
   - Visit: [https://netlify.com](https://netlify.com)
   - Click **"Sign up"**
   - Sign up with GitHub

#### Step 2: Import Project

1. **Add New Site**
   - Click **"Add new site"** → **"Import an existing project"**
   - Select **"Deploy with GitHub"**
   - Choose **StoryBeats** repository

2. **Configure Build Settings**
   ```
   Base directory: frontend
   Build command: npm run build
   Publish directory: frontend/dist
   ```

3. **Environment Variables**

   Click **"Show advanced"** → **"New variable"**

   Add:
   ```
   VITE_API_URL=https://storybeats-backend.onrender.com
   ```

4. **Deploy Site**
   - Click **"Deploy site"**
   - Netlify will build and deploy (2-5 minutes)
   - Your frontend URL: `https://your-site-name.netlify.app`

### Part C: Update Spotify and CORS

Follow the same steps as Option 1:
- Update Spotify redirect URIs
- Update backend CORS configuration
- Commit and push changes

---

## Option 3: All-in-One with Railway

Deploy both frontend and backend on Railway:

### Step 1: Deploy Backend (Same as Option 1)

Follow Part A from Option 1

### Step 2: Deploy Frontend on Railway

1. **Add New Service**
   - In your Railway project, click **"New Service"**
   - Select **"GitHub Repo"** → **StoryBeats**

2. **Configure Frontend Service**
   ```
   Root Directory: frontend
   Build Command: npm install && npm run build
   Start Command: npm install -g serve && serve -s dist -p $PORT
   ```

3. **Environment Variables**
   ```
   VITE_API_URL=https://your-backend.up.railway.app
   ```

4. **Generate Domain**
   - Settings → Networking → Generate Domain
   - Get URL like: `https://your-frontend.up.railway.app`

5. **Deploy and Test**

---

## Post-Deployment Steps

### 1. Custom Domain (Optional)

#### For Vercel:
1. Buy domain from Namecheap, Google Domains, etc.
2. In Vercel: Settings → Domains → Add Domain
3. Follow DNS configuration instructions
4. Update Spotify redirect URI with custom domain

#### For Railway:
1. Settings → Networking → Custom Domain
2. Add your domain
3. Update DNS records at your domain provider

### 2. Environment Variable Security

✅ **Do's:**
- Store all secrets in platform environment variables
- Never commit `.env` files
- Use different API keys for dev and production
- Rotate keys regularly

❌ **Don'ts:**
- Hardcode API keys in code
- Share API keys in screenshots or logs
- Use production keys in development

### 3. Monitoring Setup

**Set up monitoring for:**
- Uptime monitoring: [UptimeRobot](https://uptimerobot.com) (free)
- Error tracking: [Sentry](https://sentry.io) (free tier)
- Analytics: [Google Analytics](https://analytics.google.com) (free)

### 4. Cost Management

**Set usage limits:**
- OpenAI: Set monthly spending limit in billing
- Anthropic: Set budget alerts
- Monitor Railway/Render usage

**Expected Monthly Costs:**
- Vercel: $0 (free tier sufficient)
- Railway: $5-10
- OpenAI API: $5-20 (depends on usage)
- **Total**: ~$10-30/month

---

## Troubleshooting

### Issue 1: Backend Not Responding

**Check:**
- Backend deployment logs in Railway/Render
- Environment variables are set correctly
- Health endpoint returns 200: `https://your-backend/health`

**Common fixes:**
- Verify `PORT` environment variable
- Check `requirements.txt` is complete
- Ensure API keys are valid

### Issue 2: CORS Errors

**Symptoms:** Console shows "CORS policy" error

**Fix:**
1. Verify backend CORS configuration includes frontend URL
2. Ensure frontend URL is exact (no trailing slash)
3. Redeploy backend after CORS changes

### Issue 3: Spotify Redirect URI Error

**Symptoms:** "Invalid redirect URI" or "redirect_uri_mismatch"

**Fix:**
1. Go to Spotify Dashboard → Settings
2. Verify redirect URI exactly matches: `https://your-frontend-url/callback`
3. No typos, no trailing slash
4. Wait 5 minutes for Spotify to update

### Issue 4: Frontend Can't Reach Backend

**Check:**
1. `VITE_API_URL` environment variable is set in Vercel/Netlify
2. Backend is deployed and accessible
3. Frontend code uses `${API_URL}/api/analyze`

**Fix:**
1. Re-check environment variables
2. Redeploy frontend
3. Clear browser cache

### Issue 5: Build Failures

**Frontend Build Fails:**
- Check `package.json` is in `frontend/` directory
- Verify all dependencies are listed
- Check build logs for specific errors

**Backend Build Fails:**
- Check `requirements.txt` is in `backend/` directory
- Verify Python version compatibility
- Check for missing dependencies

### Issue 6: OpenAI/Anthropic API Errors

**Check:**
- API key is valid
- Account has available credits
- Model name is correct (`gpt-4o`, not `gpt-4-vision-preview`)

### Issue 7: Railway/Render Sleeping

**Render Free Tier Issue:**
- Free tier spins down after 15 min inactivity
- First request takes 30-60 seconds to wake up

**Solution:**
- Upgrade to paid plan ($7/month)
- Or use Railway instead

---

## Production Checklist

Before announcing your app is live:

- [ ] Both frontend and backend deployed with HTTPS
- [ ] Spotify redirect URIs updated
- [ ] Test photo upload and analysis
- [ ] Test "Get More Songs" feature
- [ ] Verify CORS is working
- [ ] Check all API calls return expected results
- [ ] Test on mobile browser
- [ ] Set up uptime monitoring
- [ ] Set up error tracking
- [ ] Configure API usage limits
- [ ] Add custom domain (optional)
- [ ] Test from different networks/devices
- [ ] Monitor costs and usage

---

## Deployment Commands Summary

### Required Code Changes Before Deployment

1. **Update `backend/app.py` for CORS:**
   ```python
   ALLOWED_ORIGINS = [
       'http://localhost:3000',
       'https://your-frontend-url.vercel.app'
   ]
   ```

2. **Update `frontend/src/App.jsx` for API URL:**
   ```javascript
   const API_URL = import.meta.env.VITE_API_URL || '';
   ```

3. **Commit and push:**
   ```bash
   git add .
   git commit -m "Configure for production deployment"
   git push origin main
   ```

---

## Next Steps After Deployment

1. **Share Your App:**
   - Share URL on social media
   - Add to portfolio
   - Post on Product Hunt

2. **Gather Feedback:**
   - Ask friends to test
   - Monitor error logs
   - Collect user feedback

3. **Monitor Performance:**
   - Watch API costs
   - Check response times
   - Monitor uptime

4. **Plan Improvements:**
   - Based on user feedback
   - Add features from roadmap
   - Optimize performance

---

## Common Issues We Encountered

This section documents real issues encountered during deployment and their solutions.

### Issue 1: Pillow Build Failure on Railway

**Error Message:**
```
ERROR: Getting requirements to build wheel did not run successfully.
exit code: 1
KeyError: '__version__'
```

**Context**: Railway was using Python 3.13.9 by default.

**Root Cause**: Pillow 10.1.0 has a bug that prevents it from building on Python 3.13.x.

**Solution**: Update to Pillow 10.4.0 which is Python 3.13 compatible:
```bash
# In backend/requirements.txt
pillow==10.4.0  # Changed from 10.1.0
```

**Prevention**: Always check package compatibility with latest Python versions before deploying.

---

### Issue 2: OpenAI Version Incompatibility

**Error Message:**
```
TypeError: __init__() got an unexpected keyword argument 'proxies'
```

**Context**: After updating Pillow, OpenAI SDK had version conflicts.

**Root Cause**: OpenAI 1.54.0 had breaking changes with httpx library versions.

**Solution**: Downgrade to stable versions:
```bash
# In backend/requirements.txt
openai==1.12.0    # Downgraded from 1.54.0
httpx==0.27.2     # Added explicit version
```

**Prevention**: Pin all dependency versions in production to avoid breaking changes.

---

### Issue 3: Missing Environment Variables

**Error Message:**
```
spotipy.oauth2.SpotifyOauthError: No client_id.
Pass it or set a SPOTIPY_CLIENT_ID environment variable.
```

**Context**: Backend deployed successfully but crashed on startup.

**Root Cause**: Forgot to add environment variables in Railway dashboard.

**Solution**: Add all required environment variables in Railway:
1. Go to Railway project → Backend service
2. Click "Variables" tab
3. Add each variable manually
4. Railway auto-redeploys after saving

**Required Variables:**
```
SPOTIFY_CLIENT_ID
SPOTIFY_CLIENT_SECRET
SPOTIFY_REDIRECT_URI
LLM_PROVIDER
OPENAI_API_KEY
OPENAI_MODEL
DEBUG
PORT
HOST
```

**Prevention**: Create a checklist of all environment variables before deploying.

---

### Issue 4: CORS Errors in Production

**Error Message (Browser Console):**
```
Access to fetch at 'https://storybeats-backend.up.railway.app/api/analyze'
from origin 'https://story-beats.vercel.app' has been blocked by CORS policy
```

**Context**: Frontend deployed but couldn't communicate with backend.

**Root Cause**: Backend CORS configuration didn't include production frontend URL.

**Solution**: Update `backend/app.py`:
```python
ALLOWED_ORIGINS = [
    'http://localhost:3000',
    'http://127.0.0.1:3000',
    'https://story-beats.vercel.app',  # Add production URL
]
```

Then commit and push to trigger auto-deployment.

**Prevention**: Add production URL placeholder in CORS config before deploying, then update after getting frontend URL.

---

### Issue 5: Spotify Redirect URI Mismatch

**Error Message:**
```
INVALID_CLIENT: Invalid redirect URI
```

**Context**: After deploying, Spotify OAuth didn't work.

**Root Cause**: Spotify redirect URI in dashboard didn't match production URL.

**Solution**:
1. Go to Spotify Developer Dashboard
2. Add: `https://story-beats.vercel.app/callback`
3. Update Railway env var `SPOTIFY_REDIRECT_URI` to same URL
4. Keep development URI (`http://127.0.0.1:3000/callback`) for local dev

**Prevention**: Update Spotify settings immediately after getting production URL.

---

### Issue 6: Vercel Environment Variable Not Applied

**Symptom**: Frontend making API calls to `undefined/api/analyze`.

**Root Cause**: Forgot to add `VITE_API_URL` environment variable in Vercel.

**Solution**:
1. Vercel dashboard → Project → Settings → Environment Variables
2. Add: `VITE_API_URL=https://storybeats-backend.up.railway.app`
3. Redeploy (Vercel → Deployments → Three dots → Redeploy)

**Note**: Environment variables added after initial deployment require a redeploy to take effect.

**Prevention**: Add all environment variables before first deployment.

---

### Issue 7: Railway Auto-Redeploy Loop

**Symptom**: Railway kept redeploying every few minutes.

**Root Cause**: Changing environment variables triggers automatic redeployment.

**Solution**: This is expected behavior! Each env var change triggers a redeploy:
- Wait for deployment to complete before testing
- Batch multiple env var changes when possible
- Monitor "Deployments" tab for status

**Prevention**: Understand that this is normal Railway behavior, not a bug.

---

### Issue 8: First API Call Takes Long Time

**Symptom**: First image upload takes 15-20 seconds, subsequent ones are faster.

**Root Cause**: Railway containers may "cold start" after inactivity.

**Solution**: This is normal for serverless/container platforms:
- First request "wakes up" the container
- Subsequent requests are fast
- Railway paid tier has always-on option

**Prevention**: For critical apps, consider Railway's always-on feature or use a cron job to ping health endpoint every 5 minutes.

---

### Best Practices Learned

1. **Test Locally First**: Ensure everything works locally before deploying
2. **One Platform at a Time**: Deploy backend first, verify it works, then deploy frontend
3. **Environment Variables**: Document all required variables before deployment
4. **Version Pinning**: Pin all dependencies to specific versions in production
5. **Health Checks**: Implement health endpoints for easy verification
6. **Git Commits**: Use descriptive commit messages for deployment changes
7. **Documentation**: Document any deployment-specific configurations
8. **Monitoring**: Set up error tracking from day one

---

**Ready to deploy? Start with Option 1 (Vercel + Railway) for the easiest experience!** 🚀

**Questions?** Check the [Real Deployment Experience](#real-deployment-experience) section for a complete walkthrough of our successful deployment!
