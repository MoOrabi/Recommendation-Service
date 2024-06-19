import schedule
import time
from myapi.recommendationSer import train_and_store

# Define a flag to check if it's the first run
first_run = True


# Define a method to handle the first run logic
def on_first_run():
    global first_run
    if first_run:
        train_and_store()
        first_run = False


# Schedule the task to run at specific times
schedule.every().day.at("09:00").do(train_and_store())  # Example: Run every day at 9 AM

# Main loop to check for scheduled tasks and first run
while True:
    on_first_run()  # Check if it's the first run
    schedule.run_pending()  # Run any pending scheduled tasks
    time.sleep(1)  # Sleep for a second before checking again
