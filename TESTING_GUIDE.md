# 🚀 SecureShare - Complete Testing Guide

**Status**: ✅ Server Running on `http://localhost:8000`

---

## 🎯 Quick Start (5 Minutes)

### 1. **Access the Application**
Open your browser and go to:
```
http://localhost:8000
```

You should see the SecureShare login page with:
- 🛡️ Shield icon
- "Secure File Sharing" title
- Login and Register tabs

---

## 📋 Step-by-Step Testing Guide

### **PHASE 1: Authentication (5 minutes)**

#### Step 1️⃣: Register a New User
1. Click **"Register"** tab
2. Enter details:
   - **Username**: `testuser1` (min 3 chars, alphanumeric + _ -)
   - **Email**: `test@example.com` (valid format)
   - **Password**: `SecurePass123` (8+ chars, uppercase, numbers)
3. Click **"Create Account"** button
4. ✅ You should see: **Green toast** "Registration successful! Please log in."
5. Observe: Form switches to Login tab automatically

#### Step 2️⃣: Test Form Validation (Error Handling)
1. Go to **Register** tab
2. Try entering:
   - **Username**: `ab` (too short) → Red border + error message
   - **Email**: `invalidemail` → Red border + error message
   - **Password**: `short` → Red border + error message
3. ✅ Observe: Real-time validation feedback

#### Step 3️⃣: Login with Your Account
1. Click **Login** tab (or it should auto-switch)
2. Enter:
   - **Username**: `testuser1`
   - **Password**: `SecurePass123`
3. Click **"Login"** button
4. 🔄 Observe: Button shows loading spinner
5. ✅ Success! You're logged in, see: **Dashboard page**

#### Step 4️⃣: Create Multiple Test Accounts
Repeat steps 1-3 to create 2-3 more accounts:
- `user2` / `User2Password123`
- `john_doe` / `JohnPassword123`

---

### **PHASE 2: File Operations (10 minutes)**

#### Step 5️⃣: Upload a File
1. Click **"Upload"** in navigation (or menu)
2. You see:
   - 📁 **Drag & Drop zone** with cloud icon
   - "Files are encrypted with AES-256-GCM before storage"

3. Click on **upload zone** or drag a file:
   - Create test file: `test_document.txt` with content "Hello SecureShare"
   - Or use any existing file on your computer

4. File preview shows:
   - 📄 File icon
   - Filename: `test_document.txt`
   - File size: (e.g., "0.5 KB")

5. (Optional) Check **"Sign file with digital signature"** box

6. Click **"Encrypt & Upload"** button

7. 🔄 Observe progress stages:
   - 10% "Preparing file..."
   - 30% "Encrypting with AES-256-GCM..."
   - 60% "Uploading to server..."
   - 90% "Verifying integrity..."
   - 100% "Complete!"

8. ✅ Success message shows:
   - ✓ Green box: "File encrypted and uploaded successfully!"
   - File hash preview: `b94d27b9934d3e08a5...` (first 32 chars)
   - Auto-redirects to Dashboard in 2 seconds

#### Step 6️⃣: View Files on Dashboard
1. You're on **Dashboard** page, see:
   - 📊 **Stats cards**: My Files, Shared, Uploads, Downloads
   - 📋 **Recent Uploads** section (your file appears)
   - 📋 **Recent Activity** section

2. Click **"My Files"** tab in navigation

3. See your uploaded file in **grid view**:
   - 📄 File icon (matches file type)
   - Filename: `test_document.txt`
   - Size & date: `0.5 KB · Jun 4, 2:30 PM`
   - 4 action buttons below

#### Step 7️⃣: Test File Actions

**Download File:**
1. Click **"Download"** button on file card
2. 🔄 Toast shows: "Downloading file..."
3. ✅ File downloads as `test_document.txt` (decrypted)
4. ✅ Toast shows: "✓ File downloaded and decrypted successfully"

**View File Details:**
1. Click **"Info"** button on file card
2. Modal opens showing:
   - 📄 **Filename**: test_document.txt
   - 💾 **File Size**: 0.5 KB
   - 🏷️ **File Type**: text/plain
   - 🔐 **Hash**: b94d27b9...
   - 👤 **Owner**: You (testuser1)
   - 📅 **Created**: Jun 4, 2:30 PM
   - ✅ **Signature Status**: (if signed)

3. Press **Escape** or click **X** to close modal
4. ✅ Modal closes smoothly

**Share File:**
1. Click **"Share"** button on file card
2. Share modal opens:
   - 📤 "Sharing: test_document.txt"
   - Input field: "Enter username to share with"
   - Checkbox: "Allow recipient to download"

3. Enter: `user2` (one of your test users)
4. Check/uncheck **download permission** checkbox
5. Click **"Share"** button
6. 🔄 Button shows loading spinner
7. ✅ Toast: "File shared with user2 successfully!"
8. Modal closes automatically

**Delete File:**
1. Click **"Delete"** (trash icon) on file card
2. ⚠️ Professional confirmation dialog appears:
   - ⚠️ Icon
   - Title: "Delete File?"
   - Message: "Are you sure you want to delete..."
   - Buttons: [Cancel] [Delete]

3. Click **[Cancel]** → Dialog closes
4. Click **[Delete]** again and this time click **[Delete]** → File deleted
5. ✅ Toast: "File deleted successfully"
6. File disappears from grid
7. ✅ Empty state message appears: "No files uploaded yet"

---

### **PHASE 3: Search & Filter (5 minutes)**

#### Step 8️⃣: Upload More Files
Upload 3-4 different file types:
- `document.pdf` (or `.txt`)
- `image.jpg` (or any image)
- `video.mp4` (or `.avi`)
- `archive.zip` (or `.rar`)

#### Step 9️⃣: Test Search
1. Go to **My Files** page
2. See search bar: 🔍 "Search my files..."
3. Type: `document` in search
4. ✅ Only matching files appear
5. Type: `pdf` → Files with "pdf" in name appear
6. Clear search → All files appear
7. 🔍 Try keyboard shortcut: Press `/` → Search bar focuses automatically

#### Step 1️⃣0️⃣: Test Filters
1. Click **"Show Filters"** button (toggle)
2. Filter panel appears with:
   - 📁 **File Type**: Documents, Images, Videos, Audio, Archives
   - 💾 **File Size**: Small (<1MB), Medium (1-50MB), Large (>50MB)
   - 📅 **Date Range**: Today, This Week, This Month, This Year

3. Select **File Type**: "Images"
4. ✅ Only image files show
5. Select **File Size**: "Small"
6. ✅ Only small image files show
7. Click **"Clear Filters"** → All files appear again
8. Toggle **"Hide Filters"** → Panel collapses

---

### **PHASE 4: Sharing Features (5 minutes)**

#### Step 1️⃣1️⃣: Share File with Another User
1. Upload a file as `testuser1`
2. Click **Share** button
3. Share modal opens
4. Enter: `user2` (your second test account)
5. Check **"Allow recipient to download"**
6. Click **"Share"**
7. ✅ "File shared with user2 successfully!"

#### Step 1️⃣2️⃣: View Shared Files
1. **Logout** from current user:
   - Click username in top-right corner
   - Click **"Logout"** button
   - ✅ Back to login page

2. **Login as `user2`**:
   - Username: `user2`
   - Password: `User2Password123`
   - Click **Login**

3. Go to **"Shared"** tab (navigation)
4. ✅ See file shared by `testuser1`:
   - File card shows: "From: testuser1"
   - You can download it
   - You can view details
   - You CANNOT delete it (only owner can)

---

### **PHASE 5: Keyboard Shortcuts (3 minutes)**

#### Step 1️⃣3️⃣: Test Keyboard Navigation

**Shortcut `/` - Focus Search:**
1. Press `/` on keyboard
2. ✅ Search bar gets focus (cursor appears)
3. Type: `test`
4. 🔍 Files filter in real-time

**Shortcut `D` - Download First File:**
1. Go to **My Files**
2. Press `D` on keyboard
3. ✅ Toast: "⬇️ Downloading first file..."
4. First file downloads

**Shortcut `S` - Share First File:**
1. Press `S` on keyboard
2. ✅ Share modal opens for first file
3. Toast: "📤 Share modal opened for first file..."

**Shortcut `Delete` - Delete First File:**
1. Press `Delete` key
2. ✅ Confirmation dialog appears for first file
3. Toast: "🗑️ Delete prompt opened for first file..."

**Shortcut `Esc` - Close Modals:**
1. Open any modal (Share, Details, etc.)
2. Press `Esc` key
3. ✅ Modal closes smoothly
4. Toast: "Modals closed"

**Shortcut `?` or `H` - Show Keyboard Help:**
1. Press `?` or `H` key
2. ✅ Help dialog appears showing all shortcuts:
   - `/` → Focus search bar
   - `D` → Download first file
   - `S` → Share first file
   - `Delete` → Delete first file
   - `Esc` → Close modals
   - `?` → Show this help
3. Read through shortcuts
4. Click **"Got it!"** or press `Esc` to close

---

### **PHASE 6: Audit Logs (3 minutes)**

#### Step 1️⃣4️⃣: View Security Audit Logs
1. Click **"Audit Logs"** in navigation
2. See table with columns:
   - 📅 **Timestamp**: When action occurred
   - 🏷️ **Event Type**: LOGIN_ATTEMPT, FILE_UPLOAD, etc.
   - 📝 **Description**: What happened
   - 🌐 **IP Address**: Your IP (127.0.0.1)
   - ✅ **Status**: Success/Failed

3. Filter logs by event type:
   - Click **"Logins"** → Only login events
   - Click **"Uploads"** → Only upload events
   - Click **"All Events"** → All events
4. ✅ Logs show all your activities

---

### **PHASE 7: Mobile Responsiveness (3 minutes)**

#### Step 1️⃣5️⃣: Test on Mobile Screen
1. Open **Browser DevTools**: Press `F12` or `Ctrl+Shift+I`
2. Click **"Toggle device toolbar"** (mobile icon) or press `Ctrl+Shift+M`
3. Select mobile device: **iPhone 12** (390px width)
4. Reload page: `F5`

5. ✅ Observe responsive design:
   - Navigation stacks properly
   - File grid becomes single column
   - Buttons are touch-friendly (larger)
   - Stats cards stack vertically
   - Modals fit on screen
   - Toast notifications fit width

6. Try **landscape mode** (DevTools menu)
7. ✅ Layout adapts to landscape

8. Try **tablet size**: iPad (768px width)
9. ✅ Two-column grid, optimized layout

---

### **PHASE 8: Error Handling (5 minutes)**

#### Step 1️⃣6️⃣: Test Error Scenarios

**Too Large File:**
1. Go to **Upload** page
2. Try uploading a file > 500MB
3. ✅ Toast error: "File size exceeds 500MB limit"

**Invalid Username Share:**
1. Click **Share** on any file
2. Enter: `nonexistentuser123456`
3. Click **Share**
4. ✅ Toast error: "Failed to share file: User not found" (or similar)

**Session Timeout Simulation:**
1. Login successfully
2. Open **Browser DevTools** (F12)
3. Go to **Application** tab → **Local Storage**
4. Delete the `token` key (right-click → Delete)
5. Try to upload a file
6. ✅ You get logged out automatically
7. ✅ Toast: "Session expired. Please log in again."
8. ✅ Redirected to login page

**Network Error (Offline):**
1. Open **DevTools** (F12)
2. Go to **Network** tab
3. Click **"Offline"** checkbox to simulate offline
4. Try to upload a file
5. ✅ See network error message
6. Uncheck **Offline** to restore

---

### **PHASE 9: Empty States (2 minutes)**

#### Step 1️⃣7️⃣: Test Empty State Messages

**No Files:**
1. Create new account `emptyuser` / `EmptyPass123`
2. Go to **My Files**
3. ✅ See helpful message:
   - 📁 Icon
   - "No files uploaded yet"
   - "Start by uploading a file from the Upload page."

**No Shared Files:**
1. Go to **"Shared"** tab
2. ✅ See message:
   - 📥 Icon
   - "No files shared with you yet"
   - "When someone shares a file with you, it will appear here."

**Filters Match Nothing:**
1. Go to **My Files** with uploaded files
2. Select filter: File Type = "Videos"
3. If you have no videos:
4. ✅ See message:
   - 🔍 Icon
   - "No files match your filters"
   - "Try adjusting your search or filter settings."

---

### **PHASE 10: UI/UX Polish (3 minutes)**

#### Step 1️⃣8️⃣: Check Visual Improvements

**Hover Effects:**
1. Hover over file cards
2. ✅ Card lifts up slightly (transform: translateY(-2px))
3. ✅ Border color changes to blue

**Button States:**
1. Hover over buttons
2. ✅ Color changes on hover
3. Click button
4. ✅ Slight visual feedback

**Focus Indicators:**
1. Press **Tab** key repeatedly
2. ✅ See blue outline around focused elements
3. ✅ Each interactive element is reachable

**Animations:**
1. Upload file
2. ✅ Smooth progress bar animation
3. Open modal
4. ✅ Smooth fade-in animation
5. Toast notification
6. ✅ Smooth slide-in animation

**Dark Theme:**
1. Note the dark background colors
2. ✅ Professional dark theme throughout
3. ✅ Good contrast for readability

---

## 📊 Expected Results Summary

| Test | Expected Result | Your Result |
|------|-----------------|-------------|
| ✅ Register | Account created, success message | |
| ✅ Login | Logged in, see dashboard | |
| ✅ Upload | File encrypted, uploaded, hash shown | |
| ✅ Download | File decrypted, downloads to computer | |
| ✅ Share | File visible to other user | |
| ✅ Delete | Confirmation dialog, file removed | |
| ✅ Search | Files filter in real-time | |
| ✅ Filters | Files filter by type/size/date | |
| ✅ Audit Logs | All activities logged | |
| ✅ Mobile | Responsive on all sizes | |
| ✅ Keyboard | All shortcuts work | |
| ✅ Errors | Clear error messages | |
| ✅ Empty States | Helpful guidance shown | |

---

## 🔗 Useful URLs

```
Application URL:     http://localhost:8000
API Documentation:   http://localhost:8000/api/docs
API RedDoc:          http://localhost:8000/api/redoc
Login/Register:      http://localhost:8000
Dashboard:           http://localhost:8000 (after login)
```

---

## 💡 Pro Tips

1. **Developer Mode**: Open DevTools (F12) to see:
   - Console for any errors
   - Network tab for API calls
   - Application tab for stored data

2. **Multiple Users**: Keep 2-3 browser windows open:
   - Window 1: testuser1
   - Window 2: user2
   - Test sharing between them

3. **Multiple Browsers**: Test in different browsers:
   - Chrome/Edge (Chromium)
   - Firefox (Mozilla)
   - Safari (if on Mac)

4. **File Types**: Upload different file types to test:
   - Text (`.txt`, `.md`)
   - Images (`.jpg`, `.png`)
   - Documents (`.pdf`, `.docx`)
   - Archives (`.zip`, `.rar`)

5. **Keyboard Shortcuts**: Use `/` to quickly search files

---

## ⚠️ Known Features

- **Max File Size**: 500MB (configurable in settings)
- **Session Timeout**: 30 minutes of inactivity
- **Database**: SQLite (local file-based)
- **Encryption**: AES-256-GCM for files
- **Storage**: `/app/uploads` directory

---

## 🆘 Troubleshooting

### Issue: "Cannot connect to localhost:8000"
**Solution**: Make sure server is running. Check terminal for:
```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### Issue: "Email is not valid"
**Solution**: Use valid email format: `user@example.com` (with @)

### Issue: "File not uploading"
**Solution**: Check file size (max 500MB) and browser console for errors

### Issue: "Cannot share with user"
**Solution**: Verify username exists and is spelled correctly

### Issue: "Session expired"
**Solution**: Log out and log back in to get a new session token

---

## 🎯 Testing Checklist

Use this checklist to track your testing progress:

```
AUTHENTICATION
[ ] Register new account
[ ] Test form validation
[ ] Login with account
[ ] Logout

FILE OPERATIONS
[ ] Upload file with encryption
[ ] View uploaded file
[ ] Download file
[ ] View file details
[ ] Share file with another user
[ ] Delete file with confirmation

SHARING
[ ] Share file
[ ] Login as different user
[ ] See shared files
[ ] Download shared file

SEARCH & FILTER
[ ] Search files by name
[ ] Filter by file type
[ ] Filter by file size
[ ] Filter by date
[ ] Clear filters

NAVIGATION
[ ] Test keyboard shortcut /
[ ] Test keyboard shortcut D
[ ] Test keyboard shortcut S
[ ] Test keyboard shortcut Delete
[ ] Test keyboard shortcut Esc
[ ] Test keyboard shortcut ? or H
[ ] Test Tab navigation
[ ] Test Escape key

AUDIT LOGS
[ ] View all audit logs
[ ] Filter by event type
[ ] See login activities
[ ] See upload activities

MOBILE
[ ] Test on mobile view
[ ] Test on tablet view
[ ] Test on landscape mode

ERRORS
[ ] Try file > 500MB
[ ] Try invalid username
[ ] Simulate offline
[ ] Test session timeout

EMPTY STATES
[ ] See empty state for new user
[ ] See filter no-match state
[ ] See helpful guidance messages

UI/UX
[ ] Check hover effects
[ ] Check button states
[ ] Check focus indicators
[ ] Check animations
[ ] Check dark theme
```

---

## 📸 Testing Recommendations

1. **Screenshot**: Take before/after screenshots of key features
2. **Notes**: Write down any issues or improvements
3. **Timing**: Note how long operations take
4. **Performance**: Monitor for lag or slowdowns
5. **Feedback**: Think about what could be improved

---

## 🎉 Success Criteria

You'll know the app is working perfectly when:

✅ All authentication flows work  
✅ Files upload and download successfully  
✅ Sharing between users works  
✅ All keyboard shortcuts respond  
✅ Mobile view is responsive  
✅ Error messages are clear and helpful  
✅ All animations are smooth  
✅ No console errors appear  
✅ Performance is fast  
✅ UI looks professional  

---

**Happy Testing! 🚀**

For detailed improvements, see: `IMPROVEMENTS.md`

