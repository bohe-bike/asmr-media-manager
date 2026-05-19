AUDIO_EXTENSIONS = {"mp3", "flac", "wav", "m4a", "opus", "ogg"}
VIDEO_EXTENSIONS = {"mp4", "mkv", "avi", "mov", "webm"}
MEDIA_EXTENSIONS = AUDIO_EXTENSIONS | VIDEO_EXTENSIONS

COVER_FILENAMES = {"cover.jpg", "cover.jpeg", "cover.png", "folder.jpg", "folder.jpeg", "front.jpg"}

MEDIA_TYPE_AUDIO = "audio"
MEDIA_TYPE_VIDEO = "video"

STATUS_PENDING = "pending"
STATUS_PROCESSED = "processed"
STATUS_RENAMED = "renamed"
STATUS_ERROR = "error"

SCAN_STATUS_PENDING = "pending"
SCAN_STATUS_RUNNING = "running"
SCAN_STATUS_COMPLETED = "completed"
SCAN_STATUS_FAILED = "failed"
