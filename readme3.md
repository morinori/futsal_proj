# Readme.md


## Running the Application

```bash
# Install dependencies
pip install -r requirements.txt

# Run the Streamlit application
streamlit run app.py
```

The application will be available at `http://localhost:8501`.

## Project Architecture

This is a Korean futsal team management platform built with Streamlit that follows a clean architecture pattern with complete separation of concerns.

### Architecture Layers

**Repository Pattern (database/)**
- `models.py`: Dataclass models for all entities (Player, Match, Field, Attendance, etc.)
- `repositories.py`: Data access layer with individual repository classes
- `connection.py`: Database connection management with context managers
- `migrations.py`: Database schema initialization and migration functions

**Service Layer (services/)**
- Business logic layer that orchestrates repositories and applies business rules
- Each service handles one domain: `match_service.py`, `player_service.py`, `attendance_service.py`, etc.
- Services validate data, format responses, and manage complex workflows

**UI Layer (ui/)**
- `components/`: Reusable UI components (`calendar.py`, `metrics.py`)
- `pages/`: Individual page modules for each main feature
- Complete separation from business logic - pages only handle UI rendering

**Configuration (config/)**
- `settings.py`: Application settings using dataclasses for different environments

**Utilities (utils/)**
- `validators.py`: Input validation functions with ValidationResult dataclass
- `formatters.py`: Data formatting and display utilities

### Key Design Patterns

**Clean Architecture**: Dependencies point inward (UI → Services → Repositories → Database)

**Single Responsibility**: Each class/module has one clear purpose

**Dependency Injection**: Services receive repositories as dependencies, UI components receive services

### Database Schema

SQLite database with the following main entities:
- `players`: Team member information with active/inactive status
- `matches`: Game scheduling with field and opponent details
- `attendance`: Player attendance tracking per match with status (present/absent/pending)
- `fields`: Futsal field/venue information
- `finances`: Team financial records (income/expense)
- `news`: Team announcements and news
- `gallery`: Photo gallery with optional match association
- `admins`: Administrator accounts with bcrypt hashed passwords and role management

### Key Features Implemented

**Attendance Management System**
- Automatic attendance record creation when matches are created
- Individual player attendance status management
- Calendar integration for quick attendance access
- Real-time attendance summaries and statistics

**Match Management**
- Full CRUD operations with validation
- Calendar view integration
- Field scheduling and conflict detection
- Automatic attendance data generation

**Player Management**
- Complete player lifecycle (CRUD with soft delete)
- Statistics tracking and performance evaluation
- Position-based organization

**Admin Authentication System**
- bcrypt-based secure password hashing and verification
- Role-based access control with session state management
- Dropdown-style admin menu integration in sidebar
- Complete separation between public and admin-only features
- Admin account management (create, deactivate, password change)
- Secure session cleanup and logout functionality

## Critical Implementation Details

### Session State Management
The app uses Streamlit session state extensively for:
- Page navigation (`current_page`)
- Selected match tracking (`selected_match_id`) - deprecated after calendar click simplification
- Database initialization flags (`db_initialized`)
- Attendance creation tracking (prevents infinite loops)
- Admin authentication state (`is_admin`, `admin_id`, `admin_username`, `admin_name`, `admin_role`)
- Admin menu dropdown state (`admin_menu_expanded`)
- Attendance processing locks (prevents race conditions)

### Attendance System Flow
1. Match creation → Automatic attendance records for all active players
2. Calendar click → Redirects to attendance page (simplified flow without specific match selection)
3. Individual status changes → Real-time database updates with user feedback
4. Race condition prevention → Double-check system with processing locks to prevent duplicate data creation

### Error Handling Patterns
- Try-catch blocks with user-friendly error messages
- Validation at service layer before database operations
- Safe dictionary access with `.get()` method
- Session state cleanup to prevent infinite rerun loops

### UI Component Reusability
- `metrics_component`: Renders dashboard metrics, performance indicators, quick stats
- `calendar_component`: Interactive calendar with match integration and attendance navigation
- `auth_component`: Admin authentication UI with login form and dropdown menu management

## Important Conventions

**File Organization**: Each major feature has its own page module in `ui/pages/` with corresponding service in `services/`

**Database Operations**: Always go through repositories, never direct database calls from UI or services

**Session State Keys**: Use descriptive names and clean up when no longer needed to prevent memory leaks

**Error Messages**: Always provide user-friendly Korean error messages in the UI

**Key Uniqueness**: All Streamlit widgets must have unique keys when multiple instances exist (use format like `f"{context}_{entity_id}_{field}"`)

## Admin Authentication System

### Architecture Overview

The platform implements a secure admin authentication system with complete separation between public and admin-only features.

### Access Control Structure

**Public Pages (No Authentication Required):**
- 🏠 메인 대시보드: Team overview and statistics
- 📈 선수 통계: Player performance and leaderboards
- 📋 출석 관리: View attendance and individual check-in ("누구세요?" dropdown)
- 📰 팀 소식: Team news and announcements
- 📸 갤러리: Photo gallery and match photos

**Admin-Only Pages (Authentication Required):**
- 📅 일정 관리: Match scheduling and management (schedule.py)
- 👥 선수 관리: Player CRUD operations (players.py)
- 💰 재정 관리: Financial management and reporting (finance.py)
- ⚙️ 관리자 설정: Admin account management (admin_settings.py)

### Security Implementation

**Password Security:**
- All passwords hashed using bcrypt with salt
- No plain-text password storage or display
- Password strength validation in admin creation

**Session Management:**
- Secure session state management with integrity checks
- Automatic cleanup of corrupted sessions
- Complete logout with all admin keys removed

**Access Control:**
- `require_admin_access()` function protects all admin pages
- Session integrity validation in `is_admin_logged_in()`
- Automatic logout on session corruption detection

### Database Schema

**Admin Table:**
```sql
CREATE TABLE admins(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    name TEXT NOT NULL,
    role TEXT DEFAULT 'admin',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    last_login TEXT DEFAULT NULL,
    is_active INTEGER DEFAULT 1
);
```

### Key Files

**Authentication Core:**
- `services/auth_service.py`: Authentication business logic, password hashing, login/logout
- `utils/auth_utils.py`: Authentication utilities and access control functions
- `database/repositories.py`: AdminRepository for database operations
- `database/models.py`: Admin dataclass model

**UI Components:**
- `ui/components/auth.py`: Login form and admin dropdown menu
- `ui/pages/admin_settings.py`: Admin account management interface
- `app.py`: Main routing with admin page integration

### Security Features Implemented

1. **Secure Password Handling**: bcrypt hashing, no plain-text display
2. **Session Integrity**: Validation of required session keys
3. **Access Control**: Page-level protection with clear error messages
4. **Dropdown UI**: Intuitive toggle menu (👤 Name ⬇️/⬆️) in sidebar
5. **Account Management**: Create, deactivate, password change functionality
6. **Race Condition Prevention**: Safe attendance data creation with locking

### Recent Security Fixes Applied

**2025-10-01: Critical Security Vulnerability Remediation**

1. **Unauthorized Admin Session Restoration (Critical - CVE-level)**
   - **Issue**: URL parameter manipulation allowed unauthorized admin access
   - **Fix**: Completely removed sessionStorage-based session restoration
   - **Impact**: Users must re-login after page refresh (enhanced security)
   - **Files**: `app.py` (152 lines removed), `ui/components/auth.py`
   - **Details**: Removed `check_session_restoration()`, `add_browser_session_control()`, and all sessionStorage JavaScript code

2. **Untrusted eval() Execution (Critical)**
   - **Issue**: `eval()` on FFprobe video metadata enabled arbitrary code execution
   - **Fix**: Replaced with safe fraction string parsing
   - **Impact**: No functional change (fps value not used in production)
   - **Files**: `services/video_service.py:98-108`
   - **Implementation**: Manual split/parse `"30/1"` → `float(30)/float(1)` with exception handling

3. **XSS Vulnerability in JavaScript Embedding (High)**
   - **Issue**: Admin usernames inserted into JavaScript without escaping
   - **Fix**: Resolved by removing sessionStorage code (item #1)
   - **Impact**: XSS attack vector eliminated
   - **Files**: `ui/components/auth.py`

4. **SQL Injection Prevention (High)**
   - **Issue**: String interpolation in LIMIT clause vulnerable to injection
   - **Fix**: Implemented parameter binding with range validation
   - **Impact**: No functional change (limit parameter not currently used)
   - **Files**: `database/repositories.py:789-794`
   - **Implementation**: `query += " LIMIT ?"` with `params = (limit,)` and `max(1, min(int(limit), 1000))` validation

5. **Import Error Fix**
   - **Issue**: `UnboundLocalError` from duplicate datetime import in function scope
   - **Fix**: Moved all imports to module level
   - **Files**: `utils/auth_utils.py:3`

**Previous Security Fixes:**
- Removed hard-coded credential display from login forms
- Fixed plain-text password exposure in admin creation
- Enhanced session state validation and cleanup
- Improved page navigation consistency
- Added processing locks to prevent race conditions

### Usage Notes

- Admin accounts must be created through the web interface by existing admins
- Calendar clicks now redirect to attendance page without specific match selection
- Debugging information in attendance management is commented out for production use
- All admin operations are logged and include proper error handling

## Video Management System

### Architecture Overview

Complete video upload, transcoding, and streaming system with HLS (HTTP Live Streaming) support.

### Key Components

**Video Processing Pipeline:**
- `services/video_service.py`: Video upload, HLS transcoding, thumbnail generation
- `ui/pages/video_upload.py`: Admin video upload interface with progress tracking
- `ui/pages/video_gallery.py`: Public video gallery with grid layout
- `database/repositories.py`: VideoRepository for video metadata management

### Features Implemented

**Video Upload & Processing (Admin Only):**
- Multi-format video upload support (mp4, mov, avi, mkv, webm, m4v)
- Automatic HLS transcoding with multiple quality levels (720p, 480p, 360p)
- Automatic thumbnail generation from video first frame
- Real-time upload progress tracking with status updates
- Background processing with status management (pending → processing → completed/failed)
- Retry mechanism for failed videos
- Video metadata editing (description, linked match)

**Video Gallery (Public):**
- Responsive grid layout (4 columns desktop, 2 columns mobile)
- Direct video player embedding (no thumbnails, players show video posters)
- Pagination (12 videos per page)
- **Match Filter Dropdown**: Filter videos by match (only shows matches with videos)
  - "전체 영상": Show all videos
  - Match options: `YYYY-MM-DD vs Opponent @Venue` (sorted by date, newest first)
  - "정보 없음": Videos without match association
- Video information display:
  - Title and duration (shows "⏱️ -" if missing)
  - Match information (shows "🏆 경기 정보 없음" if not linked)
  - Upload date and time (shows "📅 -" if missing)
- Dynamic player height calculation based on thumbnail aspect ratio
- Consistent 3-line layout for all video cards

**HLS Streaming:**
- Nginx-based HLS video serving
- Multi-quality adaptive streaming (master.m3u8 with 720p/480p/360p variants)
- CORS support for cross-origin requests
- Video.js player integration with autoplay support
- Thumbnail as video poster image

### Database Schema

**Videos Table:**
```sql
CREATE TABLE videos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    original_filename TEXT NOT NULL,
    file_size INTEGER NOT NULL,
    duration INTEGER,
    status TEXT DEFAULT 'pending',
    hls_path TEXT,
    thumbnail_path TEXT,
    match_id INTEGER,
    uploaded_by INTEGER,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    processed_at TEXT,
    FOREIGN KEY (match_id) REFERENCES matches(id),
    FOREIGN KEY (uploaded_by) REFERENCES admins(id)
);
```

### Video Processing Workflow

1. **Upload**: Admin uploads video file → Video metadata created in DB (status: pending)
2. **Storage**: Original video temporarily saved to `uploads/videos/original/{video_id}.ext`
3. **Transcoding**: FFmpeg generates HLS streams in `uploads/videos/hls/{video_id}/`
   - master.m3u8 (playlist)
   - 720p.m3u8 + segments (single quality for efficiency)
4. **Thumbnail**: Generated from first frame → `uploads/thumbnails/{video_id}.jpg`
5. **Cleanup**: Original file deleted after successful HLS processing (storage optimization)
6. **Completion**: DB updated with hls_path, thumbnail_path, duration (status: completed)

**Note**: Currently using 720p single quality for optimal storage efficiency. Original files are deleted after HLS transcoding to save ~50% storage space. Can add 480p variant if network issues arise.

### Video Gallery Implementation Details

**Grid Layout:**
- CSS media queries for responsive design
- Streamlit columns API (4 columns per row)
- Dynamic height calculation based on video thumbnail aspect ratio
- Pagination with top/bottom navigation

**Player Integration:**
- Video.js library for HLS playback
- Poster image from thumbnail
- Manual playback (no autoplay on page load)
- Full player controls (play, pause, seek, volume, fullscreen)

**Match Association:**
- Videos can be linked to specific matches
- Match information displayed with venue details
- Format: `YYYY-MM-DD vs Opponent @ Venue Name`
- Gallery filter shows only matches with uploaded videos
- Unlinked videos accessible via "정보 없음" filter option

### Nginx Configuration

**HLS Streaming Setup:**
```nginx
location /uploads/ {
    alias /app/uploads/;
    add_header Access-Control-Allow-Origin *;
    add_header Access-Control-Allow-Methods 'GET, OPTIONS';
    types {
        application/vnd.apple.mpegurl m3u8;
        video/mp2t ts;
        image/jpeg jpg;
    }
    expires 1d;
}
```

### File Structure

```
uploads/
├── videos/
│   ├── original/       # Temporary storage (deleted after processing)
│   └── hls/            # HLS transcoded streams (final storage)
│       └── {video_id}/
│           ├── master.m3u8
│           ├── 720p.m3u8
│           └── segments/
│               └── 720p_*.ts
└── thumbnails/         # Video thumbnails
    └── {video_id}.jpg
```

### Video Service Methods

**VideoService Key Methods:**
- `process_video_complete()`: Complete upload → transcode → thumbnail pipeline
- `transcode_to_hls()`: FFmpeg HLS transcoding with multiple quality levels
- `generate_thumbnail()`: Extract thumbnail from video first frame
- `get_video_info()`: Extract video metadata (duration, resolution, codec)
- `delete_video_files()`: Clean up all video-related files

### Recent Enhancements

**2025-10-01: Match Filter & UI Improvements**
- **Match Filter Dropdown**: Added gallery filter by match with venue information
  - Only shows matches that have uploaded videos
  - Format: `YYYY-MM-DD vs Opponent @Venue`
  - "정보 없음" option for unlinked videos
  - Auto-sorted by date (newest first)
- **Consistent Video Card Layout**: All cards show 3 lines of info
  - Duration, match info, upload date always displayed
  - Placeholder text when information missing (prevents layout shifts)
- **Video Logging Simplified**: Removed Flask API dependency
  - Browser console logging only (no server-side video event logs)
  - Reduced system complexity and eliminated 403 errors

**2025-09-30: Video Gallery Improvements**
- Removed thumbnail-based approach, replaced with direct player grid
- Players use video thumbnails as poster images
- Responsive grid layout (4 columns desktop, 2 columns mobile)
- Dynamic player height based on thumbnail aspect ratio
- Pagination optimized to 12 videos per page

**2025-09-30: Video Metadata Enhancements**
- Added match time to video display
- Added venue/field information to match association
- Enhanced upload page match selector: `YYYY-MM-DD HH:MM - Opponent @ Venue`
- Video edit functionality: Update description and linked match

**Video Edit Feature:**
- Edit mode toggle in video list (✏️ button)
- Update description and match association
- Repository method: `VideoRepository.update_info()`
- Session state management for edit mode

### Implementation Notes

**Performance Considerations:**
- HLS transcoding is CPU-intensive (runs in background)
- Multiple quality levels provide adaptive streaming
- Nginx serves static HLS files efficiently
- Video.js handles client-side playback

**Storage Requirements:**
- HLS 720p stream: ~50-350MB per video
- Thumbnails: ~50-200KB per video
- Total storage: HLS(720p) + Thumbnail (~50-350MB per video)
- Original files deleted after processing for 50% storage savings

**Browser Compatibility:**
- Video.js supports all modern browsers
- HLS playback via MSE (Media Source Extensions)
- Fallback to native HLS on iOS/Safari

**Security:**
- Admin-only upload access via `require_admin_access()`
- File validation and sanitization
- MIME type checking
- Maximum file size limit (2GB default)

### Common Issues & Solutions

**Issue**: Video not playing in gallery
- **Check**: Nginx HLS path configuration
- **Solution**: Ensure `/uploads/` location is properly configured in Nginx

**Issue**: Thumbnail not displaying
- **Check**: PIL/Pillow library installation
- **Solution**: Use `Image.open()` to read from file system, not web URLs

**Issue**: Transcoding fails
- **Check**: FFmpeg installation and PATH
- **Solution**: Verify FFmpeg binary is accessible in Docker container

**Issue**: Player height incorrect
- **Check**: Thumbnail aspect ratio calculation
- **Solution**: Dynamic height based on thumbnail dimensions (width × aspect_ratio)

**Issue**: Video.js warns about playlist problems
- **Check**: master.m3u8 format (RESOLUTION parameter)
- **Solution**: Remove invalid `RESOLUTION=?x720` from master.m3u8, use BANDWIDTH only

**Issue**: Videos not loading on external domain
- **Check**: Nginx location configuration for `/futsal/uploads/`
- **Solution**: Add static file location block before Streamlit proxy in domain config

## Security Deployment & Verification (2025-10-01)

### Deployment Process

**No Dependencies Changed - Restart Only:**
```bash
./run.sh restart
docker logs --tail 50 futsal-team-platform
```

**Code Changes Summary:**
- `app.py`: Removed 152 lines (session restoration functions)
- `ui/components/auth.py`: Removed sessionStorage code
- `services/video_service.py`: Replaced eval() with safe parsing
- `database/repositories.py`: Added SQL parameter binding
- `utils/auth_utils.py`: Fixed import error

### Verification Checklist

**Security Validation:**
- ✅ No `eval()` or `exec()` in codebase
- ✅ No `sessionStorage` or `restore_session` references
- ✅ No SQL string interpolation with f-strings
- ✅ Admin login requires authentication (no URL bypass)
- ✅ Video upload processes without errors

**Functional Testing:**
- ✅ Admin login/logout works
- ✅ Video upload and transcoding functions
- ✅ Video gallery displays correctly
- ✅ Match scheduling operates normally
- ✅ Player management accessible
- ⚠️ **Known Change**: Page refresh requires re-login (security enhancement)

### Version Control Workflow

- Git 저장소는 `/futsal_proj` 루트에서 `git init` 후 `git remote add origin https://github.com/morinori/futsal_proj` 형태로 구성합니다.
- `.gitignore`에는 DB(`*.db`), 업로드(`uploads/`), 세션 임시파일(`/tmp/futsal_sessions/`), 백업(`backup/`), `.claude/` 등 민감한 데이터를 반드시 포함하세요.
- 초기 가져오기나 주요 변경 시 `git status` → `.gitignore` 검토 → `git add` → `git commit -m "..."` 순으로 정리하고, 배포 전 `git push -u origin master`로 원격을 최신화합니다.
- 커밋 전에 `docs/vuln.md`와 `claude_guardrails.md`가 최신 보안 지침을 반영하는지 확인하고, 변경했다면 동일 커밋에 포함하세요.

### Backup Information

**Backup Created:** 2025-10-01 18:17
- **Location:** `~/backup/20251001_backup.tar.gz`
- **Size:** 39MB
- **Contents:** Full project (code, DB, uploads, config)
- **Restore:** `cd / && tar -xzf ~/backup/20251001_backup.tar.gz`

### Security Guardrails Added

**Prohibited Patterns:**
- ❌ `eval()` / `exec()` on external input
- ❌ Query parameter-based authorization
- ❌ JavaScript variable injection without JSON serialization
- ❌ SQL string interpolation (`f" LIMIT {limit}"`)

**Mandatory Checks:**
- ✅ All external input validated
- ✅ SQL queries use parameter binding (`?` placeholders)
- ✅ Admin access requires `require_admin_access()` decorator
- ✅ File uploads have MIME type validation
- ✅ Module-level imports (no function-scope import shadowing)
