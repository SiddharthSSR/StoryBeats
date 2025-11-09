# 🚀 Deployment Ready - Quick Start Guide

Your StoryBeats project is now **production-ready** with HTTPS support!

---

## ✅ What's Been Prepared

### Code Changes Made:
1. ✅ **Backend CORS** - Configured for production domains
2. ✅ **Frontend API URL** - Uses environment variables for backend URL
3. ✅ **Security** - Proper origin restrictions
4. ✅ **Deployment Guide** - Complete step-by-step instructions

---

## 🎯 Recommended Deployment Strategy

**Best Option: Vercel (Frontend) + Railway (Backend)**

### Why This Combo?
- ✅ Both provide **automatic HTTPS**
- ✅ **Free tier** for frontend (Vercel)
- ✅ **~$5/month** for backend (Railway)
- ✅ **GitHub auto-deploy** on every push
- ✅ **15-30 minute** setup time
- ✅ **Easy management** with great dashboards

---

## 📝 Quick Deployment Steps

### 1. Deploy Backend to Railway (10-15 min)

1. **Sign up**: [railway.app](https://railway.app) with GitHub
2. **New Project** → Deploy from GitHub → Select "StoryBeats"
3. **Settings**:
   - Root Directory: `backend`
   - Start Command: `python app.py`
4. **Add Environment Variables**:
   ```
   SPOTIFY_CLIENT_ID=your_value
   SPOTIFY_CLIENT_SECRET=your_value
   SPOTIFY_REDIRECT_URI=https://your-frontend.vercel.app/callback (update later)
   LLM_PROVIDER=openai
   OPENAI_API_KEY=your_value
   OPENAI_MODEL=gpt-4o
   DEBUG=False
   PORT=5001
   HOST=0.0.0.0
   ```
5. **Generate Domain** → Get URL like: `https://your-app.up.railway.app`

### 2. Deploy Frontend to Vercel (10-15 min)

1. **Sign up**: [vercel.com](https://vercel.com) with GitHub
2. **New Project** → Import "StoryBeats"
3. **Settings**:
   - Framework: Vite
   - Root Directory: `frontend`
   - Build Command: `npm run build`
   - Output Directory: `dist`
4. **Add Environment Variable**:
   ```
   VITE_API_URL=https://your-app.up.railway.app
   ```
5. **Deploy** → Get URL like: `https://storybeats.vercel.app`

### 3. Update Spotify Redirect URI (2 min)

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Open your StoryBeats app → Settings
3. Add Redirect URI: `https://your-frontend.vercel.app/callback`
4. Save

### 4. Update Backend CORS (2 min)

1. Edit `backend/app.py`:
   ```python
   ALLOWED_ORIGINS = [
       'http://localhost:3000',
       'http://127.0.0.1:3000',
       'https://your-frontend.vercel.app',  # Add this line
   ]
   ```
2. Commit and push:
   ```bash
   git add .
   git commit -m "Add production frontend URL to CORS"
   git push
   ```
3. Railway and Vercel will auto-deploy!

### 5. Update Railway Redirect URI (1 min)

1. Go to Railway → Your Project → Variables
2. Update `SPOTIFY_REDIRECT_URI` to: `https://your-frontend.vercel.app/callback`
3. Railway will redeploy automatically

### 6. Test! (5 min)

1. Visit: `https://your-frontend.vercel.app`
2. Upload a photo
3. Get song recommendations
4. Test "Get 5 More Songs"
5. Verify HTTPS lock icon in browser

---

## 🔑 Environment Variables Quick Reference

### Backend (Railway):
```bash
SPOTIFY_CLIENT_ID=<your_spotify_client_id>
SPOTIFY_CLIENT_SECRET=<your_spotify_client_secret>
SPOTIFY_REDIRECT_URI=https://<your-frontend>.vercel.app/callback
LLM_PROVIDER=openai
OPENAI_API_KEY=<your_openai_key>
OPENAI_MODEL=gpt-4o
DEBUG=False
PORT=5001
HOST=0.0.0.0
```

### Frontend (Vercel):
```bash
VITE_API_URL=https://<your-backend>.up.railway.app
```

---

## 💰 Expected Costs

| Service | Cost | Notes |
|---------|------|-------|
| Vercel (Frontend) | **$0/month** | Free tier is sufficient |
| Railway (Backend) | **$5/month** | Usage-based pricing |
| OpenAI API | **$5-20/month** | Depends on usage (~$0.01-0.02 per image) |
| **Total** | **~$10-25/month** | Varies with traffic |

**Free Trial Credits:**
- Railway: $5 credit to start
- Vercel: Free forever for personal projects

---

## 🎯 Deployment Checklist

Before going live:

- [ ] Backend deployed to Railway
- [ ] Frontend deployed to Vercel
- [ ] Both URLs use HTTPS
- [ ] Environment variables configured
- [ ] Spotify redirect URI updated
- [ ] CORS configuration updated
- [ ] Code changes committed and pushed
- [ ] Test photo upload works
- [ ] Test "Get More Songs" works
- [ ] Verify no CORS errors in console
- [ ] Test on mobile browser
- [ ] Set OpenAI usage limits

---

## 🆘 Quick Troubleshooting

### "CORS policy" error
→ Update `ALLOWED_ORIGINS` in `backend/app.py` with your Vercel URL

### "Network error"
→ Check `VITE_API_URL` is set in Vercel environment variables

### "Invalid redirect URI"
→ Spotify redirect URI must exactly match Vercel URL + `/callback`

### Backend not responding
→ Check Railway logs and verify environment variables

### Songs not loading
→ Verify OpenAI/Spotify API keys are correct

---

## 📚 Full Documentation

For detailed step-by-step instructions, see:
- **DEPLOYMENT_GUIDE.md** - Complete deployment guide with all options
- **SETUP_GUIDE.md** - Local development setup
- **README.md** - Project overview and features

---

## 🚀 Ready to Deploy?

1. Read the **DEPLOYMENT_GUIDE.md** for full instructions
2. Follow Option 1 (Vercel + Railway) for easiest setup
3. Total time: **30-45 minutes** from start to live!

**Good luck with your deployment! 🎉**

---

## 📞 Need Help?

- Check DEPLOYMENT_GUIDE.md troubleshooting section
- Review platform documentation:
  - [Vercel Docs](https://vercel.com/docs)
  - [Railway Docs](https://docs.railway.app)
- Test locally first to verify code works
- Check browser console for errors
- Review backend logs in Railway dashboard

---

**Your app is ready for the world! 🌍**
