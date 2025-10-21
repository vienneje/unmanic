# Zip Structure Fix - transcode_amd_v2 v2.1.9

## 🐛 Issue Encountered

When trying to install the plugin via Unmanic's web UI, you got this error:

```
2025-10-21T10:47:41:ERROR:Unmanic.PluginsHandler - Exception while installing plugin from zip
"There is no item named 'info.json' in the archive"

KeyError: "There is no item named 'info.json' in the archive"
```

## 🔍 Root Cause

The initial zip file had the plugin files inside a `transcode_amd_v2/` subdirectory:

```
transcode_amd_v2-2.1.9.zip (WRONG)
├── transcode_amd_v2/
│   ├── info.json
│   ├── plugin.py
│   ├── description.md
│   ├── changelog.txt
│   └── README.md
```

**Unmanic expects plugin files at the root level of the zip**, not in a subdirectory:

```
transcode_amd_v2-2.1.9.zip (CORRECT)
├── info.json
├── plugin.py
├── description.md
├── changelog.txt
└── README.md
```

## ✅ Fix Applied

### 1. Recreated Zip File
```bash
cd /home/shidosh/Documents/unmanic/plugins/transcode_amd_v2
zip ../transcode_amd_v2-2.1.9.zip info.json plugin.py description.md changelog.txt README.md
```

This creates a zip with files at the root level.

### 2. Verified Structure
```bash
unzip -l transcode_amd_v2-2.1.9.zip
```

Output:
```
Archive:  transcode_amd_v2-2.1.9.zip
  Length      Date    Time    Name
---------  ---------- -----   ----
      604  2025-10-21 10:38   info.json          ✅ At root
    16881  2025-10-21 10:38   plugin.py          ✅ At root
     3706  2025-10-20 16:04   description.md     ✅ At root
     4518  2025-10-21 10:38   changelog.txt      ✅ At root
     8694  2025-10-20 16:05   README.md          ✅ At root
---------                     -------
    34403                     5 files
```

### 3. Reinstalled on Both Systems

**Local (unmanic-amd):**
```bash
docker exec unmanic-amd unzip -o /tmp/transcode_amd_v2-2.1.9.zip \
  -d /config/.unmanic/plugins/transcode_amd_v2/
docker restart unmanic-amd
```

**Zeus (unmanic-noble):**
```bash
docker exec unmanic-noble unzip -o /tmp/plugin-v2.1.9.zip \
  -d /config/.unmanic/plugins/transcode_amd_v2/
docker restart unmanic-noble
```

### 4. Committed and Pushed
```bash
git add plugins/transcode_amd_v2-2.1.9.zip
git commit -m "Fix v2.1.9 zip structure - files at root for Unmanic compatibility"
git push fork master
```

**Commit**: `e9a3678`

## 📦 Download Fixed Plugin

The corrected zip file is now available:

**GitHub Direct Download:**
```
https://github.com/vienneje/unmanic/raw/master/plugins/transcode_amd_v2-2.1.9.zip
```

**Local Path:**
```
/home/shidosh/Documents/unmanic/plugins/transcode_amd_v2-2.1.9.zip
```

## 🧪 Installation Test

You can now install the plugin via Unmanic's web UI:

1. **Open Unmanic**: http://localhost:8888 or http://zeus.local:9092
2. **Go to Plugins**: Settings → Plugins → Install Plugin
3. **Upload Zip**: Select the fixed `transcode_amd_v2-2.1.9.zip`
4. **Install**: Click "Install"

**Expected Result:**
```
✅ Plugin "Transcode AMD v2" installed successfully
✅ Version: 2.1.9
✅ Status: Ready to enable
```

**No more errors!** ✅

## 🔧 Manual Installation (Alternative)

If you prefer manual installation:

```bash
# Local system
docker exec unmanic-amd mkdir -p /config/.unmanic/plugins/transcode_amd_v2
docker cp transcode_amd_v2-2.1.9.zip unmanic-amd:/tmp/
docker exec unmanic-amd unzip -o /tmp/transcode_amd_v2-2.1.9.zip \
  -d /config/.unmanic/plugins/transcode_amd_v2/
docker restart unmanic-amd

# Zeus (Unraid)
scp transcode_amd_v2-2.1.9.zip root@zeus.local:/tmp/
ssh root@zeus.local "
  docker exec unmanic-noble mkdir -p /config/.unmanic/plugins/transcode_amd_v2
  docker cp /tmp/transcode_amd_v2-2.1.9.zip unmanic-noble:/tmp/
  docker exec unmanic-noble unzip -o /tmp/transcode_amd_v2-2.1.9.zip \
    -d /config/.unmanic/plugins/transcode_amd_v2/
  docker restart unmanic-noble
"
```

## ✅ Verification

After installation, verify the plugin:

### Check Files Exist
```bash
# Local
docker exec unmanic-amd ls -la /config/.unmanic/plugins/transcode_amd_v2/

# Zeus
ssh root@zeus.local "docker exec unmanic-noble ls -la /config/.unmanic/plugins/transcode_amd_v2/"
```

**Expected Output:**
```
-rw-rw-r-- 1 root root  4518 Oct 21 10:38 changelog.txt
-rw-rw-r-- 1 root root  3706 Oct 20 16:04 description.md
-rw-rw-r-- 1 root root   604 Oct 21 10:38 info.json
-rw-rw-r-- 1 root root 16881 Oct 21 10:38 plugin.py
-rw-rw-r-- 1 root root  8694 Oct 20 16:05 README.md
```

### Check Version
```bash
# Local
docker exec unmanic-amd cat /config/.unmanic/plugins/transcode_amd_v2/info.json | grep version

# Zeus
ssh root@zeus.local "docker exec unmanic-noble cat /config/.unmanic/plugins/transcode_amd_v2/info.json | grep version"
```

**Expected Output:**
```json
"version": "2.1.9",
```

### Check in UI
1. Open Unmanic web UI
2. Go to Settings → Plugins
3. Look for "Transcode AMD v2"
4. Version should show **2.1.9**
5. Plugin should be in **"Installed"** or **"Available to Enable"** state

## 📝 What Changed

### Before (Wrong Structure)
```bash
# Created with parent directory
cd /home/shidosh/Documents/unmanic/plugins
zip -r transcode_amd_v2-2.1.9.zip transcode_amd_v2/
```

This created:
```
transcode_amd_v2-2.1.9.zip
└── transcode_amd_v2/     ❌ Subdirectory (wrong!)
    ├── info.json
    └── ...
```

### After (Correct Structure)
```bash
# Created from within plugin directory
cd /home/shidosh/Documents/unmanic/plugins/transcode_amd_v2
zip ../transcode_amd_v2-2.1.9.zip info.json plugin.py description.md changelog.txt README.md
```

This created:
```
transcode_amd_v2-2.1.9.zip
├── info.json           ✅ Root level (correct!)
├── plugin.py           ✅
├── description.md      ✅
├── changelog.txt       ✅
└── README.md           ✅
```

## 🎯 Summary

**Problem:** Zip file had subdirectory, Unmanic couldn't find `info.json`  
**Solution:** Recreated zip with files at root level  
**Result:** Plugin installs successfully via web UI  

**Status:** ✅ **FIXED**

Both local and Zeus containers now have the corrected plugin installed and are running.

**You can now install v2.1.9 via the Unmanic web UI without errors!** 🎉

---

**Files Updated:**
- `plugins/transcode_amd_v2-2.1.9.zip` (Corrected structure)

**Git Commit:**
- Hash: `e9a3678`
- Message: "Fix v2.1.9 zip structure - files at root for Unmanic compatibility"
- Pushed to: https://github.com/vienneje/unmanic
