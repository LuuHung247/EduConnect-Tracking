# Tracking Service - EduConnect Microservice

**Simple user lesson tracking for chatbot context.**

## Overview

Tracking Service theo dõi lesson hiện tại mà user đang học. Điều này giúp AI Chatbot biết context và có thể trả lời câu hỏi về bài học hiện tại.

**Use Case:**

- User vào trang lesson → Frontend gọi `/lesson/enter` → Tracking Service lưu lesson hiện tại
- User hỏi chatbot về bài học → Chatbot gọi `/user/{id}/current` → Biết user đang học lesson nào
- Chatbot lấy thông tin lesson từ Backend → Trả lời câu hỏi dựa trên nội dung lesson
- User rời khỏi lesson → Frontend gọi `/lesson/exit` → Clear tracking
- Nếu user không ở trong lesson nào → Chatbot response: "Bạn hãy vào một bài học để tôi có thể giúp bạn"

## Architecture

```
Frontend → Tracking Service → MongoDB
              ↓
           Chatbot
              ↓
           Backend (get lesson info)
```

## API Endpoints

### Track Current Lesson

- `POST /api/tracking/lesson/enter` - Set current lesson (user enters lesson page)
- `POST /api/tracking/lesson/exit` - Clear current lesson (user exits lesson page)

### Get Current Lesson (for Chatbot)

- `GET /api/tracking/user/{user_id}/current` - Get user's current lesson

### Health Check

- `GET /health` - Service health check

## Data Model

### MongoDB Collection: current_lesson_tracking

```javascript
{
  user_id: String (unique),    // Primary key
  lesson_id: String,           // Lesson đang học
  serie_id: String,            // Serie của lesson
  lesson_title: String,        // Title của lesson (optional)
  last_updated: DateTime       // Lần cuối update
}
```

**Simple Schema:**

- Mỗi user chỉ có 1 record (hoặc không có)
- Nếu có record = user đang trong lesson
- Nếu không có record = user không ở trong lesson nào

## Usage Examples

### 1. User vào lesson page (Frontend)

```javascript
// Khi user click vào lesson
await fetch("/api/tracking/lesson/enter", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    user_id: currentUser.id,
    lesson_id: lesson.id,
    serie_id: serie.id,
    lesson_title: lesson.title,
  }),
});
```

### 2. Chatbot kiểm tra user đang học gì

```javascript
// Chatbot service
const response = await fetch(`/api/tracking/user/${userId}/current`);
const data = await response.json();

if (!data.is_in_lesson) {
  return "Bạn chưa vào bài học nào. Hãy chọn một bài học để tôi có thể giúp bạn!";
}

// User đang trong lesson -> lấy thông tin lesson từ Backend
const lessonInfo = await fetch(`/api/v1/lessons/${data.lesson_id}`);
// Chatbot có thể trả lời câu hỏi dựa trên lessonInfo
```

### 3. User rời khỏi lesson (Frontend)

```javascript
// Khi user navigate ra khỏi lesson page
await fetch("/api/tracking/lesson/exit", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    user_id: currentUser.id,
  }),
});
```

## Response Examples

### User đang trong lesson:

```json
GET /api/tracking/user/user123/current

{
  "user_id": "user123",
  "lesson_id": "lesson456",
  "serie_id": "serie789",
  "lesson_title": "Introduction to Python",
  "last_updated": "2025-12-15T10:30:00Z",
  "is_in_lesson": true
}
```

### User KHÔNG trong lesson nào:

```json
GET /api/tracking/user/user123/current

{
  "user_id": "user123",
  "lesson_id": null,
  "serie_id": null,
  "lesson_title": null,
  "last_updated": null,
  "is_in_lesson": false
}
```

## Integration Flow

### Chatbot Integration

```
1. User asks chatbot: "Giải thích cho tôi về biến trong Python"

2. Chatbot calls: GET /api/tracking/user/{user_id}/current

3a. If is_in_lesson = false:
    → Response: "Bạn hãy vào một bài học trước nhé!"

3b. If is_in_lesson = true:
    → Chatbot calls: GET /api/v1/lessons/{lesson_id} (Backend)
    → Get lesson content, video transcript, etc.
    → Answer user's question with context
```

### Frontend Integration

```
On Lesson Page Mount:
  → POST /api/tracking/lesson/enter

On Lesson Page Unmount:
  → POST /api/tracking/lesson/exit

On User Navigate Away:
  → POST /api/tracking/lesson/exit
```

## Running Locally

```bash
cd Tracking-Service
pip install -r requirements.txt
uvicorn main:app --reload --port 8002
```

Service runs on http://localhost:8002

### 📚 API Documentation (Swagger UI)

After starting the service, access:

- **Swagger UI**: http://localhost:8002/docs
- **ReDoc**: http://localhost:8002/redoc

Swagger UI allows you to:

- 🧪 Test all endpoints interactively
- 📝 See request/response examples
- ✅ Validate your API calls
- 📖 Read full API documentation

#### Testing Flow in Swagger UI:

1. **Open Swagger**: http://localhost:8002/docs
2. **Test Enter Lesson**:

   - Click `POST /api/tracking/lesson/enter`
   - Click "Try it out"
   - Use example payload or customize:

   ```json
   {
     "user_id": "user123",
     "lesson_id": "lesson456",
     "serie_id": "serie789",
     "lesson_title": "Introduction to Python"
   }
   ```

   - Click "Execute"
   - Check response (should be 200 OK)

3. **Test Get Current**:

   - Click `GET /api/tracking/user/{user_id}/current`
   - Click "Try it out"
   - Enter user_id: `user123`
   - Click "Execute"
   - Should return lesson info with `is_in_lesson: true`

4. **Test Exit Lesson**:

   - Click `POST /api/tracking/lesson/exit`
   - Click "Try it out"
   - Use payload: `{"user_id": "user123"}`
   - Click "Execute"
   - Check response

5. **Verify Cleared**:
   - Call `GET /api/tracking/user/user123/current` again
   - Should return `is_in_lesson: false`

### 🧪 Quick Test Script

Run the automated test script:

```bash
./test_api.sh
```

This will test all endpoints automatically and show results.

## Running with Docker Compose

```bash
docker-compose up tracking-service
```

Then access:

- **API**: http://localhost:8002
- **Swagger UI**: http://localhost:8002/docs
- **ReDoc**: http://localhost:8002/redoc

## Configuration

Environment variables (`.env.example`):

- `MONGODB_URI` - MongoDB connection string
- `MONGODB_NAME` - Database name (default: edu-connect)
- `PORT` - Service port (default: 8002)

## Technology Stack

- **Framework**: FastAPI (async)
- **Server**: Uvicorn
- **Database**: MongoDB (PyMongo)
- **Data Validation**: Pydantic

## Why This is Simple & Effective

✅ **No complex progress tracking** - Just know: Is user in a lesson or not?
✅ **No session management** - One record per user, simple CRUD
✅ **No video position** - Don't need it for chatbot context
✅ **Perfect for chatbot** - Chatbot knows exactly what lesson user is studying
✅ **Fast queries** - Unique index on user_id, O(1) lookup

## Future Enhancements (Optional)

- [ ] Track lesson access history for analytics
- [ ] Auto-clear stale records (user_id not accessed in 24 hours)
- [ ] Add WebSocket for real-time chatbot updates
