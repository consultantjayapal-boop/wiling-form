from fastapi import FastAPI, HTTPException, Depends, File, UploadFile, Form, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
import os
import json
import uuid
import hashlib
import jwt
from datetime import datetime, timedelta
from dotenv import load_dotenv
import asyncio
from pathlib import Path
import shutil
import mimetypes

load_dotenv()

app = FastAPI(title="Will Writing App", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

# File storage paths
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
USER_DATA_DIR = Path("user_data")
USER_DATA_DIR.mkdir(exist_ok=True)

# In-memory storage (replace with database in production)
users_db = {}
wills_db = {}
files_db = {}

# Pydantic models
class UserSignup(BaseModel):
    email: EmailStr
    mobile: str
    password: str
    confirm_password: str

class UserLogin(BaseModel):
    username: str  # email or mobile
    password: str

class WillCreate(BaseModel):
    title: str
    language: str  # telugu, english, hindi
    content: Optional[str] = ""
    ai_assisted: Optional[bool] = False

class MessageSend(BaseModel):
    recipient_name: str
    recipient_email: EmailStr
    recipient_phone: str
    message_text: str
    preference: str  # whatsapp, email, call
    will_id: Optional[str] = None

class AIAssistRequest(BaseModel):
    query: str
    language: str
    will_context: Optional[str] = ""

# Utility functions
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    return hash_password(password) == hashed

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def create_user_directory(user_id: str):
    user_dir = USER_DATA_DIR / user_id
    user_dir.mkdir(exist_ok=True)
    (user_dir / "audio").mkdir(exist_ok=True)
    (user_dir / "video").mkdir(exist_ok=True)
    (user_dir / "documents").mkdir(exist_ok=True)
    return user_dir

def get_ai_assistance(query: str, language: str, context: str = "") -> str:
    """Get AI assistance for will writing"""
    try:
        # Import emergentintegrations
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        
        # Get API key from environment
        api_key = os.getenv('EMERGENT_LLM_KEY')
        if not api_key:
            return "AI assistance is currently unavailable. Please contact support."
        
        # Create system message based on language
        system_messages = {
            "english": "You are a legal assistant specializing in will writing. Provide clear, helpful advice for creating wills. Always remind users to consult with a qualified attorney for final legal advice.",
            "hindi": "आप वसीयत लेखन में विशेषज्ञ एक कानूनी सहायक हैं। वसीयत बनाने के लिए स्पष्ट, सहायक सलाह प्रदान करें। हमेशा उपयोगकर्ताओं को अंतिम कानूनी सलाह के लिए एक योग्य वकील से सलाह लेने की याद दिलाएं।",
            "telugu": "మీరు వీలునామా రాయడంలో ప్రత్యేకత కలిగిన న్యాయ సహాయకుడు. వీలునామాలు రూపొందించడానికి స్పష్టమైన, సహాయకరమైన సలహా అందించండి. చివరి న్యాయ సలహా కోసం అర్హత కలిగిన న్యాయవాదిని సంప్రదించాలని వినియోగదారులకు ఎల్లప్పుడూ గుర్తు చేయండి."
        }
        
        system_message = system_messages.get(language.lower(), system_messages["english"])
        
        # Create chat instance
        chat = LlmChat(
            api_key=api_key,
            session_id=f"will_assist_{datetime.now().timestamp()}",
            system_message=system_message
        ).with_model("openai", "gpt-4o-mini")
        
        # Prepare user message
        full_query = f"Context: {context}\n\nQuery: {query}" if context else query
        user_message = UserMessage(text=full_query)
        
        # Get response
        response = asyncio.run(chat.send_message(user_message))
        return response
        
    except Exception as e:
        print(f"AI assistance error: {e}")
        return "AI assistance is currently unavailable. Please try again later."

# API Routes

@app.post("/api/auth/signup")
async def signup(user_data: UserSignup):
    # Validate passwords match
    if user_data.password != user_data.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")
    
    # Check if user already exists
    user_id = f"{user_data.email}_{user_data.mobile}"
    if user_id in users_db:
        raise HTTPException(status_code=400, detail="User already exists")
    
    # Create user
    hashed_password = hash_password(user_data.password)
    users_db[user_id] = {
        "id": user_id,
        "email": user_data.email,
        "mobile": user_data.mobile,
        "password": hashed_password,
        "created_at": datetime.now().isoformat()
    }
    
    # Create user directory
    create_user_directory(user_id)
    
    # Create access token
    access_token = create_access_token({"sub": user_id})
    
    return {
        "success": True,
        "message": "User created successfully",
        "access_token": access_token,
        "user_id": user_id
    }

@app.post("/api/auth/login")
async def login(login_data: UserLogin):
    # Find user by email or mobile
    user = None
    for user_id, user_info in users_db.items():
        if user_info["email"] == login_data.username or user_info["mobile"] == login_data.username:
            user = user_info
            break
    
    if not user or not verify_password(login_data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Create access token
    access_token = create_access_token({"sub": user["id"]})
    
    return {
        "success": True,
        "message": "Login successful",
        "access_token": access_token,
        "user_id": user["id"]
    }

@app.get("/api/user/profile")
async def get_profile(current_user: str = Depends(get_current_user)):
    user = users_db.get(current_user)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "user_id": user["id"],
        "email": user["email"],
        "mobile": user["mobile"],
        "created_at": user["created_at"]
    }

@app.post("/api/wills/create")
async def create_will(will_data: WillCreate, current_user: str = Depends(get_current_user)):
    will_id = str(uuid.uuid4())
    
    # Get AI assistance if requested
    ai_content = ""
    if will_data.ai_assisted and will_data.content:
        ai_query = f"Help me improve this will content: {will_data.content}"
        ai_content = get_ai_assistance(ai_query, will_data.language)
    
    will_info = {
        "id": will_id,
        "user_id": current_user,
        "title": will_data.title,
        "language": will_data.language,
        "content": will_data.content,
        "ai_suggestions": ai_content,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    wills_db[will_id] = will_info
    
    return {
        "success": True,
        "message": "Will created successfully",
        "will_id": will_id,
        "ai_suggestions": ai_content if will_data.ai_assisted else None
    }

@app.get("/api/wills/list")
async def list_wills(current_user: str = Depends(get_current_user)):
    user_wills = [will for will in wills_db.values() if will["user_id"] == current_user]
    return {
        "success": True,
        "wills": user_wills
    }

@app.get("/api/wills/{will_id}")
async def get_will(will_id: str, current_user: str = Depends(get_current_user)):
    will_data = wills_db.get(will_id)
    if not will_data or will_data["user_id"] != current_user:
        raise HTTPException(status_code=404, detail="Will not found")
    
    return {
        "success": True,
        "will": will_data
    }

@app.put("/api/wills/{will_id}")
async def update_will(will_id: str, will_data: WillCreate, current_user: str = Depends(get_current_user)):
    will_info = wills_db.get(will_id)
    if not will_info or will_info["user_id"] != current_user:
        raise HTTPException(status_code=404, detail="Will not found")
    
    # Get AI assistance if requested
    ai_content = ""
    if will_data.ai_assisted and will_data.content:
        ai_query = f"Help me improve this will content: {will_data.content}"
        ai_content = get_ai_assistance(ai_query, will_data.language)
    
    will_info.update({
        "title": will_data.title,
        "language": will_data.language,
        "content": will_data.content,
        "ai_suggestions": ai_content if will_data.ai_assisted else will_info.get("ai_suggestions", ""),
        "updated_at": datetime.now().isoformat()
    })
    
    return {
        "success": True,
        "message": "Will updated successfully",
        "ai_suggestions": ai_content if will_data.ai_assisted else None
    }

@app.post("/api/files/upload/{will_id}")
async def upload_file(
    will_id: str,
    file: UploadFile = File(...),
    file_type: str = Form(...),  # audio, video, document
    current_user: str = Depends(get_current_user)
):
    # Check if will belongs to user
    will_data = wills_db.get(will_id)
    if not will_data or will_data["user_id"] != current_user:
        raise HTTPException(status_code=404, detail="Will not found")
    
    # Create user directory
    user_dir = create_user_directory(current_user)
    file_dir = user_dir / file_type
    
    # Generate unique filename
    file_extension = Path(file.filename).suffix
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = file_dir / unique_filename
    
    # Save file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Store file info
    file_id = str(uuid.uuid4())
    file_info = {
        "id": file_id,
        "user_id": current_user,
        "will_id": will_id,
        "filename": file.filename,
        "stored_filename": unique_filename,
        "file_type": file_type,
        "file_path": str(file_path),
        "size": file_path.stat().st_size,
        "created_at": datetime.now().isoformat()
    }
    
    files_db[file_id] = file_info
    
    return {
        "success": True,
        "message": "File uploaded successfully",
        "file_id": file_id,
        "filename": file.filename,
        "size": file_info["size"]
    }

@app.get("/api/files/list/{will_id}")
async def list_files(will_id: str, current_user: str = Depends(get_current_user)):
    # Check if will belongs to user
    will_data = wills_db.get(will_id)
    if not will_data or will_data["user_id"] != current_user:
        raise HTTPException(status_code=404, detail="Will not found")
    
    # Get files for this will
    will_files = [file for file in files_db.values() 
                  if file["will_id"] == will_id and file["user_id"] == current_user]
    
    return {
        "success": True,
        "files": will_files
    }

@app.get("/api/files/download/{file_id}")
async def download_file(file_id: str, current_user: str = Depends(get_current_user)):
    file_info = files_db.get(file_id)
    if not file_info or file_info["user_id"] != current_user:
        raise HTTPException(status_code=404, detail="File not found")
    
    file_path = Path(file_info["file_path"])
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on disk")
    
    return FileResponse(
        path=file_path,
        filename=file_info["filename"],
        media_type=mimetypes.guess_type(file_info["filename"])[0]
    )

@app.delete("/api/files/{file_id}")
async def delete_file(file_id: str, current_user: str = Depends(get_current_user)):
    file_info = files_db.get(file_id)
    if not file_info or file_info["user_id"] != current_user:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Delete physical file
    file_path = Path(file_info["file_path"])
    if file_path.exists():
        file_path.unlink()
    
    # Remove from database
    del files_db[file_id]
    
    return {
        "success": True,
        "message": "File deleted successfully"
    }

@app.post("/api/ai/assist")
async def ai_assist(request: AIAssistRequest, current_user: str = Depends(get_current_user)):
    try:
        response = get_ai_assistance(request.query, request.language, request.will_context)
        return {
            "success": True,
            "response": response
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/api/messages/send")
async def send_message(message: MessageSend, current_user: str = Depends(get_current_user)):
    # For now, just store the message (in production, integrate with email service)
    message_id = str(uuid.uuid4())
    
    # Create message record
    message_record = {
        "id": message_id,
        "sender_id": current_user,
        "recipient_name": message.recipient_name,
        "recipient_email": message.recipient_email,
        "recipient_phone": message.recipient_phone,
        "message_text": message.message_text,
        "preference": message.preference,
        "will_id": message.will_id,
        "sent_at": datetime.now().isoformat(),
        "status": "pending"  # In production: sent, delivered, failed
    }
    
    # Here you would integrate with email service, SMS service, etc.
    # For now, we'll just return success
    
    return {
        "success": True,
        "message": f"Message queued for delivery via {message.preference}",
        "message_id": message_id
    }

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)