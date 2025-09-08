from telegram import Update    
from telegram.ext import Updater, CommandHandler, CallbackContext    

class Development:    
    api_id = 20160788   
    api_hash = "192838ffc9ddeaf78ef96cb48aec7aa5"    
    TOKEN = "8297483839:AAFDdDIX-jHiHQMD7TzJrs9ruo9k8Ux7FOI"    
    GROUP_ID = -1002097449198    
    CHARA_CHANNEL_ID = -1002749526772    
    mongo_url = "mongodb+srv://pabitrabarman0002:rajrajkumar02@rajrajkumar.rrwa7zy.mongodb.net/?retryWrites=true&w=majority&appName=Rajrajkumar"

    PHOTO_URL = [    
        "https://telegra.ph/file/c74151f4c2b56a107a24b.jpg",    
        "https://telegra.ph/file/6a81a91aa4a660a73194b.jpg"    
    ]    
    SUPPORT_CHAT = "+roNC_pDAtQxhNWVl"    
    UPDATE_CHAT = "The_Moon_Network"    
    BOT_USERNAME = "ZeroTwo_Games_bot"    
    OWNER_ID = "7598384653"    
    JOINLOGS = -1002097449198    
    LEAVELOGS = -1002097449198    

    # ✅ Added sudo_users
    sudo_users = [7598384653]  # Add more user IDs if needed

# Optional: Example command to test sudo access
def start(update: Update, context: CallbackContext):    
    user_id = update.effective_user.id
    if user_id in Development.sudo_users:
        update.message.reply_text("✅ You are a SUDO user.")
    else:
        update.message.reply_text("❌ You are not a SUDO user.")

def main():    
    updater = Updater(Development.TOKEN, use_context=True)    
    dp = updater.dispatcher

    # Add command handler
    dp.add_handler(CommandHandler("start", start))

    # Start the bot
    updater.start_polling()      
    updater.idle()    

if __name__ == "__main__":    
    main()
