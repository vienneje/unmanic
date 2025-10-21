# Library Setup Guide for Unmanic Noble

## 🔍 Issue Found

The database file `/config/unmanic.db` is **empty** (0 bytes), which means Unmanic hasn't been initialized yet. Libraries need to be configured through the web UI first.

## ✅ Solution: Configure Libraries via Web UI

### Step 1: Access Unmanic Web UI
Open your browser to: **http://zeus.local:9092**

### Step 2: Configure Your First Library

#### A. Navigate to Libraries
1. Click **Settings** (gear icon) in the left menu
2. Click **Libraries**

#### B. Add Movies Library
1. Click **"Add Library"** button
2. Configure:
   - **Name**: `Movies`
   - **Path**: `/library/movies`
   - **Enable Scanner**: ✅ Check this box
   - **Enable Inotify**: ✅ Check this box (optional, for monitoring new files)
3. Click **"Save"**

#### C. Add TV Shows Library
1. Click **"Add Library"** button again
2. Configure:
   - **Name**: `TV Shows`
   - **Path**: `/library/tvshows`  
   - **Enable Scanner**: ✅ Check this box
   - **Enable Inotify**: ✅ Check this box
3. Click **"Save"**

### Step 3: Configure Plugin Flow

For each library:

#### A. Select Library
1. In Libraries page, click on **"Movies"** library
2. Go to **"Plugin Flow"** tab

#### B. Add Plugin to Flow
1. Click **"Add Plugin"** button
2. Select **"Transcode AMD v2"** from the list
3. Click **"Add"**
4. **Configure plugin settings** (optional):
   - Encoding Mode: **Auto** (recommended)
   - Target Codec: **HEVC** (H.265)
   - Video Quality: **Balanced**
   - Bitrate: **4M**
   - Max Bitrate: **6M**
5. Click **"Save"**

#### C. Repeat for TV Shows Library
1. Go back to Libraries list
2. Click on **"TV Shows"** library
3. Go to **"Plugin Flow"** tab
4. Add **"Transcode AMD v2"** plugin
5. Save

### Step 4: Run Library Scan

#### Option A: Manual Scan
1. Go to **Dashboard** (home icon)
2. Look for your library in the list
3. Click the **"Scan"** button (🔄 icon) next to the library name

#### Option B: Automatic Scan
- Unmanic will automatically scan libraries periodically
- Default scan interval: every 6 hours
- You can change this in Settings → Libraries → (library) → Scan Settings

### Step 5: Verify Files Are Found

#### A. Check Pending Tasks
1. Go to **"Pending"** page (in left menu)
2. You should see files appear in the list
3. Files will be queued based on plugin rules

#### B. What You Should See
```
Pending Tasks: 1,234 items

File: /library/movies/10.Cloverfield.Lane.2016.mkv
Status: Queued
Library: Movies
Plugin: Transcode AMD v2
```

### Step 6: Start Processing

#### A. Check Workers
1. Go to **"Workers"** page
2. You should see at least 1 worker
3. Status should be **"Idle"** or **"Processing"**

#### B. Processing Will Start Automatically
- Workers will pick up pending tasks
- You'll see progress, percentage, and **ETC** (with the fixed frontend!)
- Completed files go to **"History"** page

## 🐛 Troubleshooting

### No Files in Pending List

**Check 1: Files Exist in Mount**
```bash
ssh root@zeus.local "docker exec unmanic-noble ls /library/movies/ | head -10"
# Should show movie files
```

**Check 2: Library Path is Correct**
- In UI, check Settings → Libraries → (library) → Path
- Must match exactly: `/library/movies` and `/library/tvshows`

**Check 3: Plugin is in Flow**
- Settings → Libraries → (library) → Plugin Flow
- Should show **"Transcode AMD v2"**

**Check 4: Scanner is Enabled**
- Settings → Libraries → (library)
- **Enable Scanner** must be checked ✅

**Check 5: Check Logs**
```bash
ssh root@zeus.local "docker logs unmanic-noble | grep -i 'scan\|library\|error' | tail -20"
```

### Database Still Empty

If the database remains empty even after accessing the UI:

```bash
# Check database
ssh root@zeus.local "docker exec unmanic-noble ls -lh /config/unmanic.db"
# Should be larger than 0 bytes after UI access

# If still 0, restart container
ssh root@zeus.local "docker restart unmanic-noble"
```

### Can't Access Web UI

```bash
# Check if container is running
ssh root@zeus.local "docker ps | grep unmanic-noble"

# Check if Unmanic process is running
ssh root@zeus.local "docker exec unmanic-noble ps aux | grep unmanic"

# Check logs
ssh root@zeus.local "docker logs unmanic-noble --tail 50"

# Try accessing from Zeus itself
ssh root@zeus.local "curl -I http://localhost:9092"
```

## 📊 Expected Library Scan Results

### Movies Directory
- **Total files**: ~53,000+ files
- **Video files**: Depends on file types (mkv, mp4, avi, etc.)
- **After scan**: Files matching plugin criteria will be added to pending

### TV Shows Directory  
- **Total files**: ~41,000+ files
- **After scan**: Episode files matching criteria will be added to pending

**Note**: Not all files will be added to pending - only those that need transcoding based on your plugin rules.

## 📝 Summary

1. ✅ Access http://zeus.local:9092
2. ✅ Add Libraries (Movies, TV Shows)
3. ✅ Add Plugin to Library Flow (Transcode AMD v2)
4. ✅ Run Scan (manual or wait for automatic)
5. ✅ Check Pending Tasks page
6. ✅ Watch Workers process files with progress and ETC!

**The database will initialize automatically when you first access the web UI and configure libraries.**

---

**Once libraries are configured, you should see files appear in the Pending Tasks list!** 🎉
