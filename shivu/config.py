from telegram import Update    
from telegram.ext import Updater, CommandHandler, CallbackContext    

class Development:    
    api_id = 26344421  
    api_hash = "4bbcf08096c88dfa79c1e8e03af3ab3a"    
    TOKEN = "8474933953:AAHFAqTJGkSiN7ltZUexXV7syiwdZ6YsiPg"    
    GROUP_ID =    
    CHARA_CHANNEL_ID =   
    mongo_url = "mongodb+srv://rajrajbarman02:rajrajkumar02@rajrajkumar.fywl2ol.mongodb.net/"

    PHOTO_URL = [    
        "https://telegra.ph/file/c74151f4c2b56a107a24b.jpg",    
        "https://telegra.ph/file/6a81a91aa4a660a73194b.jpg"    
    ]    
    SUPPORT_CHAT = ""    
    UPDATE_CHAT = ""    
    BOT_USERNAME = "@Saber_gaming_bot"    
    OWNER_ID = "7639271205"    
    JOINLOGS =    
    LEAVELOGS =   

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
