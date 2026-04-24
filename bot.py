import threading
from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running"

def start_bot():
    run()  # your main loop

if __name__ == "__main__":
    threading.Thread(target=start_bot).start()
    app.run(host="0.0.0.0", port=5000)
