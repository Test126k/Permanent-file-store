from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pymongo import MongoClient
import datetime
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

# Configurations
MONGO_URI = "mongodb+srv://username:password@cluster.mongodb.net/database_name"
DB_NAME = "file_store_bot"
BLOG_ID = "your_blog_id"
SCOPES = ["https://www.googleapis.com/auth/blogger"]
CREDENTIALS_FILE = "path_to_service_account.json"

# MongoDB Setup
mongo_client = MongoClient(MONGO_URI)
db = mongo_client[DB_NAME]
files_collection = db["files"]

# Initialize Blogspot API
credentials = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
blogger_service = build("blogger", "v3", credentials=credentials)

# Short link generator
BLOG_URL = "https://filescrazy.blogspot.com/2024/06/only-botz.html"
BOT_USERNAME = "Crazybotz"

# Function to generate short links
def generate_short_link(file_id):
    encoded_file_id = f"{BOT_USERNAME}_{file_id}"
    short_link = f"{BLOG_URL}?link={encoded_file_id}"
    return short_link

# Function to update Blogspot HTML
def update_blog_html(new_username):
    post = blogger_service.posts().get(blogId=BLOG_ID, postId="post_id").execute()
    html_content = post["content"]
    updated_html = html_content.replace(BOT_USERNAME, new_username)
    post["content"] = updated_html
    blogger_service.posts().update(blogId=BLOG_ID, postId="post_id", body=post).execute()

# Save files and generate short link
@Client.on_message(filters.document | filters.video | filters.photo)
async def save_file(client, message):
    file_id = message.document.file_id if message.document else (
        message.video.file_id if message.video else message.photo.file_id
    )
    file_name = message.document.file_name if message.document else (
        message.video.file_name if message.video else "photo.jpg"
    )

    # Save to MongoDB
    file_data = {
        "file_id": file_id,
        "file_name": file_name,
        "uploaded_by": message.from_user.id,
        "uploaded_at": datetime.datetime.utcnow(),
    }
    files_collection.insert_one(file_data)

    # Generate short link
    short_link = generate_short_link(file_id)
    await message.reply(f"File saved! Short link:\n{short_link}")

# Command to update blog HTML if username changes
@Client.on_message(filters.command("update_username") & filters.user("your_user_id"))
async def update_username(client, message):
    global BOT_USERNAME
    new_username = message.text.split(" ", 1)[1]
    update_blog_html(new_username)
    BOT_USERNAME = new_username
    await message.reply("Blogspot HTML updated successfully!")

# Start Bot
if __name__ == "__main__":
    app = Client("bot", api_id="YOUR_API_ID", api_hash="YOUR_API_HASH", bot_token="YOUR_BOT_TOKEN")
    app.run()
