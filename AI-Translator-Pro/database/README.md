# Database

MongoDB is used for persistence. Schema is implemented in `backend/app/database/db.py`.

## Collections

### users
- `_id`: ObjectId
- `email`: string (unique)
- `hashed_password`: string
- `full_name`: string

### translations (history)
- `_id`: ObjectId
- `user_id`: string (reference to user)
- `original_text`: string
- `translated_text`: string
- `src_lang`: string
- `target_lang`: string
- `timestamp`: ISO8601 string
- `audio_ref`: string (optional, path or ID of TTS file)

## Indexes
- `users`: unique index on `email`
- `translations`: compound index on `(user_id, timestamp)` for history queries

## Fallback
If MongoDB is not available, the app uses an in-memory store so you can run without a database.
