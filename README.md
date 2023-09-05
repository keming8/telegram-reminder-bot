# telegram-reminder-bot
A reminder bot on Telegram that sends reminder messages specified by the user at a specified time.

The bot operates on the following commands:
/remindme <time> will then prompt for a message to be reminded at <time>. The user can specify the following:
- 'at <time>' will send the reminder message at a specific time on the same day
- 'in <time>' will send the reminder message at a specific time delta from when the message was sent
- 'on <time>' will send the reminder message on a specific day/date, time can be specified
  
/remindmeevery <time> will then prompt for a message to be reminded at every <time>. This is a recurring reminder. The user can specify the following:
- A time delta (Eg. 5 seconds) to be sent a reminder message at those intervals
- A day of the week
- After specifying these, the user can specify when to stop the recurring reminders. The default is 6 months from when the message is sent.

/list will list all active reminders that the user has.

/clear will clear all scheduled reminders for the user.

/cancel will cancel the most recently defined job. This can be used multiple times consecutively. 

/help will list all possible functions available to the user.
