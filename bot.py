import json
import requests
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
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

async def start(update, context):
    await update.message.reply_text(f"Hello {update.message.from_user.first_name} how can i help u!")
    await update.message.reply_text(f"u can use\n1). '/ask' for AI using\n2). '/add' to save a task\n3). '/remove' to remove a task u add\n4). '/tasks' to see ur tasks list\n5). '/done' to put a tasks in the done list\n6). '/stats' to see ur stats percentage\n7). '/remind' to set a reminder for a task ")

async def ask_command(update, context):
    question = " ".join(context.args)
    if question == "":
        context.user_data["chatting"] = True
        await update.message.reply_text(f"AI chat is on. Drop your questions")
        start_timer(update, context)
    else:
        answer = await asyncio.to_thread(ask_ai, [{"role": "user", "content": question}])
        await update.message.reply_text(answer)

async def fact_command(update, context):
    cat_fact = await asyncio.to_thread(get_cat_fact)
    await update.message.reply_text(cat_fact)

async def remove_command(update, context):
    task = " ".join(context.args)
    tasks = load_tasks()
    user_id = str(update.message.from_user.id)
    if user_id not in tasks:
        tasks[user_id] = {"todo": [], "done": []}
    if task in tasks[user_id]["todo"]:
        tasks[user_id]["todo"].remove(task)
        await update.message.reply_text(f"Just removed {task} from the list")
    elif task in tasks[user_id]["done"]:
        tasks[user_id]["done"].remove(task)
        await update.message.reply_text(f"Just removed {task} from the list")
    else: 
        await update.message.reply_text("this task is not on the list try '/add' or '/tasks'.")
    save_tasks(tasks)

async def tasks_command(update, context):
    tasks = load_tasks()
    user_id = str(update.message.from_user.id)
    if user_id not in tasks:
        tasks[user_id] = {"todo": [], "done": []}
    if tasks[user_id]["todo"] == [] and tasks[user_id]["done"] == []:
        await update.message.reply_text("no todo tasks yet, use /add")
    elif tasks[user_id]["todo"] == [] and tasks[user_id]["done"] != []:
        count = 0
        message = ""
        for dn in tasks[user_id]["done"]:
            count = count + 1
            message = message + f"{count}). {dn}\n"
        await update.message.reply_text(f"There is only done tasks:\n {message}")
    else:
        count = 0
        message = ""
        for td in tasks[user_id]["todo"]:
            count = count + 1
            message = message + f"{count}). {td}: TODO\n" 
        for dn in tasks[user_id]["done"]:
            count = count + 1
            message = message + f"{count}). {dn}: DONE\n"
        await update.message.reply_text(message)

async def add_command(update, context):
    task = " ".join(context.args)
    tasks = load_tasks()
    user_id = str(update.message.from_user.id)
    if user_id not in tasks:
        tasks[user_id] = {"todo": [], "done": []}
    if task == "":
       context.user_data["waiting"] = True
       await update.message.reply_text(f"what is the task you want to add?")
    elif task in tasks[user_id]["todo"]:
        await update.message.reply_text(f"{task} already exist in ur to do list")
    else:
        await update.message.reply_text(f"You added: {task}")
        tasks[user_id]["todo"].append(task)
        save_tasks(tasks)

async def done_command(update, context):
    task = " ".join(context.args)
    tasks = load_tasks()
    user_id = str(update.message.from_user.id)
    if user_id not in tasks:
        tasks[user_id] = {"todo": [], "done": []}
    if task == "":
        await update.message.reply_text(f"You can not add an empty name")
    elif task not in tasks[user_id]["todo"]:
        await update.message.reply_text(f"this task does not exist yet, try /Add")
    else:
        tasks[user_id]["todo"].remove(task)
        tasks[user_id]["done"].append(task)
        await update.message.reply_text(f"the {task} task is done")
        save_tasks(tasks)

async def reminder(context):
    tasks = load_tasks()
    if str(context.job.chat_id) not in tasks or tasks[str(context.job.chat_id)]["todo"] == []:
        await context.bot.send_message(chat_id=context.job.chat_id, text="no tasks yet, use /add")
    else:
        count = 0
        message = ""
        for num in tasks[str(context.job.chat_id)]["todo"]:
            count = count + 1
            message = message + f"{count}). {num}\n"
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
    tasks = load_tasks()
    user_id = str(update.message.from_user.id)
    if user_id not in tasks: 
        tasks[user_id] = {"todo": [], "done": []}
    tasks[user_id]["time"] = f"{hour}:{minute}"
    await update.message.reply_text(f"Reminder set for {hour}:{minute}")
    save_tasks(tasks)
    for job in context.job_queue.get_jobs_by_name(user_id):
        job.schedule_removal()
    context.job_queue.run_daily(reminder, time=datetime.time(hour, minute, tzinfo=zoneinfo.ZoneInfo("Africa/Algiers")), chat_id=update.message.chat_id, name=user_id)

async def stats_command(update, context):
    tasks = load_tasks()
    user_id = str(update.message.from_user.id)
    if user_id not in tasks:
        tasks[user_id] = {"todo": [], "done": []}
    done = len(tasks[user_id]["done"])
    todo = len(tasks[user_id]["todo"])
    total = done + todo
    if total == 0:
        await update.message.reply_text("You have no stats yet. full you'r lists first")
    elif done == 0:
        await update.message.reply_text(f"you have done no tasks yet")
    else:
        percent = round(done / total * 100)
        await update.message.reply_text(f"You have done {done} of {total} tasks.\n{percent}% of the work is done. ")

async def handle_text(update, context):
    if context.user_data.get("waiting") is True:
        task = update.message.text
        tasks = load_tasks()
        user_id = str(update.message.from_user.id)
        if user_id not in tasks:
            tasks[user_id] = {"todo": [], "done": []}
        if task in tasks[user_id]["todo"]:
            await update.message.reply_text(f"{task} already exist in ur to do list")
        else:
            await update.message.reply_text(f"You added: {task}")
            tasks[user_id]["todo"].append(task)
            save_tasks(tasks)
        context.user_data["waiting"] = False
    elif context.user_data.get("chatting") is True:
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
    await context.bot.send_message(chat_id=context.job.chat_id, text="AI chat ended, you were inactive for a minute.")

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
tasks = load_tasks()
for user_id, data in tasks.items():
    if "time" in data:
        time = data["time"].split(":")
        hour = int(time[0])
        minute = int(time[1])
        app.job_queue.run_daily(reminder, time=datetime.time(hour, minute, tzinfo=zoneinfo.ZoneInfo("Africa/Algiers")), chat_id=int(user_id), name=user_id)
app.run_polling()