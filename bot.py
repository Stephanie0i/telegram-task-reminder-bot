import json
import requests
import csv
import db
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler, MessageHandler, filters
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import os
from dotenv import load_dotenv
import datetime
import zoneinfo
import asyncio
load_dotenv()
NVIDIA_llm = os.getenv("NVIDIA_API_KEY")

MODEL="nvidia/nemotron-3.5-bolt-e4b"
URL="https://integrate.api.nvidia.com/v1/chat/completions"
SYSTEM_PROMPT="You are a general assistant. Answer briefly."
DAILY_LIMIT = 20
def ask_ai(messages):
    try:
        body = {"model": MODEL, "max_tokens": 200, "messages": [{"role": "system", "content": SYSTEM_PROMPT}] + messages}
        r = requests.post(URL, json=body, timeout=30, headers={"Authorization": f"Bearer {NVIDIA_llm}"})
    except requests.exceptions.RequestException as e:
        return "no connection"

    if r.status_code == 200:
        return r.json()["choices"][0]["message"]["content"]
    else:
        return f"request_failed due to {r.status_code} error"

def load_tasks():
    try:
        with open("tasks.json", "r") as sf:
            tasks = json.load(sf)
    except FileNotFoundError:
        tasks = {}
    return tasks
def save_tasks(tasks):
    with open("tasks.json", "w") as sf:
        json.dump(tasks, sf)

def get_cat_fact():
    try:
        r = requests.get("https://catfact.ninja/fact", timeout=10)
    except requests.exceptions.RequestException:
        return "no connection"
    if r.status_code == 200:
        fact = r.json()
        return fact["fact"]
    else:
        return f"request_failed due to {r.status_code} error"

token = os.getenv("TOKEN")

def can_use_ai(user_id):
    return db.use_ai(user_id, DAILY_LIMIT, str(datetime.date.today()))

def build_task_view(user_id):
    todo = db.get_tasks(user_id, "todo")
    if todo == []:
        return "No TODO tasks. Use /add", None
    keyboard = []
    for task_id, task in todo:
        keyboard.append([InlineKeyboardButton(f"✅ {task}", callback_data=f"done:{task_id}"), InlineKeyboardButton("🗑", callback_data=f"remove:{task_id}")])
    return "Tap ✅ to finish a task or 🗑 to delete it:", InlineKeyboardMarkup(keyboard)

async def start(update, context):
    await update.message.reply_text(f"Hello {update.message.from_user.first_name} how can i help u!")
    await update.message.reply_text(f"u can use\n1). '/ask' for AI using\n2). '/add' to save a task\n3). '/remove' to remove a task u add\n4). '/tasks' to see ur tasks list\n5). '/done' to put a tasks in the done list\n6). '/stats' to see ur stats percentage\n7). '/remind' to set a reminder for a task\n8). '/fact' to get a fact about cats\n9). '/list' to modify ur tasks easily.\n10). '/export' to get ur tasks on a file")

async def add_command(update, context):
    task = " ".join(context.args)
    user_id = str(update.message.from_user.id)
    if task == "":
        context.user_data["waiting"] = True
        await update.message.reply_text("what is the task you want to add?")
    elif db.add_task(user_id, task):
        await update.message.reply_text(f"You added: {task}")
    else:
        await update.message.reply_text(f"{task} already exist in ur to do list")

async def fact_command(update, context):
    cat_fact = await asyncio.to_thread(get_cat_fact)
    await update.message.reply_text(cat_fact)

async def remove_command(update, context):
    task = " ".join(context.args)
    user_id = str(update.message.from_user.id)
    if db.remove_task(user_id, task):
        await update.message.reply_text(f"Just removed {task} from the list")
    else:
        await update.message.reply_text("this task is not on the list try '/add' or '/tasks'.")

async def tasks_command(update, context):
    user_id = str(update.message.from_user.id)
    todo = db.get_tasks(user_id, "todo")
    done = db.get_tasks(user_id, "done")
    if todo == [] and done == []:
        await update.message.reply_text("no todo tasks yet, use /add")
        return
    message = ""
    count = 0
    for task_id, task in todo:
        count = count + 1
        message = message + f"{count}). {task}: TODO\n"
    for task_id, task in done:
        count = count + 1
        message = message + f"{count}). {task}: DONE\n"
    await update.message.reply_text(message)

async def ask_command(update, context):
    question = " ".join(context.args)
    if question == "":
        context.user_data["chatting"] = True
        await update.message.reply_text(f"AI chat is on. Drop your questions")
        start_timer(update, context)
    else:
        if not can_use_ai(str(update.message.from_user.id)):
            await update.message.reply_text(f"You reached today’s AI limit, try tomorrow")
            return
        answer = await asyncio.to_thread(ask_ai, [{"role": "user", "content": question}])
        await update.message.reply_text(answer)

async def done_command(update, context):
    task = " ".join(context.args)
    user_id = str(update.message.from_user.id)
    if task == "":
        await update.message.reply_text("You can not add an empty name")
    elif db.mark_done(user_id, task):
        await update.message.reply_text(f"the {task} task is done")
    else:
        await update.message.reply_text("this task does not exist yet, try /Add")

async def reminder(context):
    user_id = str(context.job.chat_id)
    todo = db.get_tasks(user_id, "todo")
    if todo == []:
        await context.bot.send_message(chat_id=context.job.chat_id, text="no tasks yet, use /add")
    else:
        count = 0
        message = ""
        for task_id, task in todo:
            count = count + 1
            message = message + f"{count}). {task}\n"
        await context.bot.send_message(chat_id=context.job.chat_id, text="u have tasks to consider\n" + message)

async def remind(update, context):
    task = " ".join(context.args)
    try:
        when = task.split(":")
        hour = int(when[0])
        minute = int(when[1])
    except (ValueError, IndexError):
        await update.message.reply_text('set the time in the right shape. 00:00')
        return
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        await update.message.reply_text('set the time in the right shape. 00:00')
        return
    user_id = str(update.message.from_user.id)
    db.set_reminder(user_id, f"{hour:02d}:{minute:02d}")
    await update.message.reply_text(f"Reminder set for {hour:02d}:{minute:02d}")
    for job in context.job_queue.get_jobs_by_name(user_id):
        job.schedule_removal()
    context.job_queue.run_daily(reminder, time=datetime.time(hour, minute, tzinfo=zoneinfo.ZoneInfo("Africa/Algiers")), chat_id=update.message.chat_id, name=user_id)

async def stats_command(update, context):
    user_id = str(update.message.from_user.id)
    done = db.count_tasks(user_id, "done")
    todo = db.count_tasks(user_id, "todo")
    total = done + todo
    if total == 0:
        await update.message.reply_text("You have no stats yet. full you'r lists first")
    elif done == 0:
        await update.message.reply_text(f"you have done no tasks yet")
    else:
        percent = round(done / total * 100)
        await update.message.reply_text(f"You have done {done} of {total} tasks.\n{percent}% of the work is done. ")

async def export_command(update, context):
    user_id = str(update.message.from_user.id)
    todo = db.get_tasks(user_id, "todo")
    done = db.get_tasks(user_id, "done")
    if todo == [] and done == []:
        await update.message.reply_text("Nothing to export yet, use /add to fill ur file")
        return
    filename = f"tasks_{user_id}.csv"
    with open(filename, "w", newline="", encoding="utf-8-sig") as cf:
        writer = csv.writer(cf, delimiter=";")
        writer.writerow(["task", "status",])
        for task_id, task in todo:
            writer.writerow([task, "TODO"])
        for task_id, task in done:
            writer.writerow([task, "DONE"])
    with open(filename, "rb") as cf:
        await update.message.reply_document(document=cf, filename="tasks.csv")
    os.remove(filename)

async def list_command(update, context):
    text, markup = build_task_view(str(update.message.from_user.id))
    await update.message.reply_text(text, reply_markup=markup)

async def button_handler(update, context):
    query = update.callback_query
    await query.answer()
    action, task_id = query.data.split(":")
    task_id = int(task_id)
    user_id = str(query.from_user.id)
    if action == "done":
        db.mark_done_by_id(user_id, task_id)
    elif action == "remove":
        db.remove_by_id(user_id, task_id)
    text, markup = build_task_view(user_id)
    await query.edit_message_text(text, reply_markup=markup)

async def handle_text(update, context):
    if context.user_data.get("waiting") is True:
        task = update.message.text
        user_id = str(update.message.from_user.id)
        if db.add_task(user_id, task):
            await update.message.reply_text(f"You added: {task}")
        else:
            await update.message.reply_text(f"{task} already exist in ur to do list")
        context.user_data["waiting"] = False
    elif context.user_data.get("chatting") is True:
        if not can_use_ai(str(update.message.from_user.id)):
            await update.message.reply_text(f"You reached today’s AI limit, try tomorrow")
            return
        history = context.user_data.setdefault("history", [])
        history.append({"role": "user", "content": update.message.text})
        answer = await asyncio.to_thread(ask_ai, history[-10:])
        history.append({"role": "assistant", "content": answer})
        await update.message.reply_text(answer)
        start_timer(update, context)

def stop_timer(update, context):
    name = f"chat_{update.message.from_user.id}"
    for job in context.job_queue.get_jobs_by_name(name):
        job.schedule_removal()

async def chat_timeout(context):
    context.user_data["chatting"] = False
    await context.bot.send_message(chat_id=context.job.chat_id, text="AI chat ended, we can't chat forever.")

def start_timer(update, context):
    stop_timer(update, context)
    name = f"chat_{update.message.from_user.id}"
    context.job_queue.run_once(chat_timeout, 60, chat_id=update.message.chat_id, user_id=update.message.from_user.id, name=name)

async def end_chat(update, context):
    if not update.message.text.startswith("/ask"):
        context.user_data["chatting"] = False
        stop_timer(update, context)
app = ApplicationBuilder().token(token).build()
app.add_handler(CommandHandler("remind", remind))
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("ask", ask_command))
app.add_handler(CommandHandler("fact", fact_command))
app.add_handler(CommandHandler("stats", stats_command))
app.add_handler(CommandHandler("add", add_command))
app.add_handler(CommandHandler("done", done_command))
app.add_handler(CommandHandler("tasks", tasks_command))
app.add_handler(CommandHandler("remove", remove_command))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
app.add_handler(MessageHandler(filters.COMMAND, end_chat), group=-1)
app.add_handler(CommandHandler("list", list_command))
app.add_handler(CallbackQueryHandler(button_handler))
app.add_handler(CommandHandler("export", export_command))
db.init_db()
for user_id, remind_time in db.get_reminders():
    time = remind_time.split(":")
    hour = int(time[0])
    minute = int(time[1])
    app.job_queue.run_daily(reminder, time=datetime.time(hour, minute, tzinfo=zoneinfo.ZoneInfo("Africa/Algiers")), chat_id=int(user_id), name=user_id)
app.run_polling()