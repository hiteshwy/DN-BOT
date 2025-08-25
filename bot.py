#!/usr/bin/env python3
"""
Discord VPS Bot (Docker + tmate, Persistent Storage)
----------------------------------------------------
User cmds:
  /start /stop /restart /delete /list /regen-ssh /tips /ping /help /node
Admin cmds:
  /deploy /nodedmin /delete-all /sendvps
"""

import os, json, asyncio, logging, random, string, subprocess
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import discord
from discord import app_commands
from discord.ext import tasks
import psutil

# -------- Config --------
TOKEN = "YOUR_DISCORD_BOT_TOKEN"   # <--- put your bot token here
ADMIN_IDS = {123456789012345678}   # <--- replace with your Discord user IDs
PUBLIC_IP = "1.2.3.4"              # optional, shows in /node
DB_FILE = "database.jsonl"
MAX_RAM_GB = 32
MAX_CPU = 8
TMATE_CAPTURE_TIMEOUT = 25
OS_IMAGE = {
    "ubuntu": "ubuntu-22.04-with-tmate",
    "debian": "debian-with-tmate",
}

# Persistent VPS data root
VPS_DATA_ROOT = "/var/lib/vpsdata"

intents = discord.Intents.default()
bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s:%(name)s: %(message)s")
log = logging.getLogger("vps-bot")

_db_lock = asyncio.Lock()

# -------- DB helpers --------
def now() -> datetime: return datetime.utcnow()

async def db_all() -> List[Dict]:
    if not os.path.exists(DB_FILE): return []
    async with _db_lock:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return [json.loads(l) for l in f if l.strip()]

async def db_for_user(uid: int) -> List[Dict]:
    return [r for r in await db_all() if r.get("user_id") == uid]

async def db_find(container: str) -> Optional[Dict]:
    for r in await db_all():
        if r.get("container") == container: return r
    return None

async def db_append(r: Dict):
    async with _db_lock:
        with open(DB_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(r) + "\n")

async def db_delete(container: str):
    async with _db_lock:
        tmp = DB_FILE + ".tmp"
        with open(DB_FILE,"r",encoding="utf-8") as fin, open(tmp,"w",encoding="utf-8") as fout:
            for line in fin:
                if json.loads(line).get("container") != container:
                    fout.write(line)
        os.replace(tmp, DB_FILE)

async def db_update(container: str, **updates):
    async with _db_lock:
        rows = await db_all()
        tmp = DB_FILE + ".tmp"
        with open(tmp,"w",encoding="utf-8") as fout:
            for r in rows:
                if r["container"] == container: r.update(updates)
                fout.write(json.dumps(r)+"\n")
        os.replace(tmp, DB_FILE)

# -------- Helpers --------
def rand_name(): return "vps_"+"".join(random.choices(string.ascii_lowercase+string.digits,k=6))

async def run_cmd(*a,check=True): 
    return await asyncio.to_thread(subprocess.run,a,check=check,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)

async def start_tmate(container: str, timeout=TMATE_CAPTURE_TIMEOUT) -> Optional[str]:
    await run_cmd("docker","exec",container,"bash","-lc","command -v tmate || apt update && apt install -y tmate",check=False)
    proc = await asyncio.create_subprocess_exec("docker","exec",container,"tmate","-F",stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.STDOUT)
    start=asyncio.get_event_loop().time()
    try:
        while True:
            if proc.stdout is None: break
            try: line=await asyncio.wait_for(proc.stdout.readline(),timeout=1.0)
            except asyncio.TimeoutError:
                if asyncio.get_event_loop().time()-start>timeout: proc.kill(); return None
                continue
            if not line: break
            txt=line.decode(errors="ignore").strip()
            if "ssh session:" in txt: return txt.split("ssh session:")[1].strip()
    finally: proc.kill()
    return None

def parse_expiry(s: str)->Optional[str]:
    if not s: return None
    units={"s":1,"m":60,"h":3600,"d":86400,"M":2592000,"y":31536000}
    try:
        if s[-1] in units: sec=int(s[:-1])*units[s[-1]]
        else: sec=int(s)*86400
        return (now()+timedelta(seconds=sec)).strftime("%Y-%m-%d %H:%M:%S")
    except: return None

# -------- Presence & Cleanup --------
@tasks.loop(seconds=15)
async def presence_task():
    await bot.change_presence(activity=discord.Game(name=f"VPS Online: {len(await db_all())}"))

@tasks.loop(minutes=5)
async def gc_task():
    for r in await db_all():
        if r.get("expiry") and now()>datetime.strptime(r["expiry"],"%Y-%m-%d %H:%M:%S"):
            await run_cmd("docker","rm","-f",r["container"],check=False)
            await db_delete(r["container"])

@bot.event
async def on_ready():
    log.info("Bot ready as %s", bot.user)
    await tree.sync(); presence_task.start(); gc_task.start()

# -------- Embeds --------
COLOR_OK, COLOR_INFO, COLOR_ERR = 0x2ecc71, 0x2b6cb0, 0xe74c3c
def emb_ok(t,d=""): return discord.Embed(title=t,description=d,color=COLOR_OK)
def emb_info(t,d=""): return discord.Embed(title=t,description=d,color=COLOR_INFO)
def emb_err(t,d=""): return discord.Embed(title=t,description=d,color=COLOR_ERR)

# -------- Commands --------
@tree.command(name="ping",description="Ping bot")
async def ping(i): await i.response.send_message(f"Pong! {round(bot.latency*1000)}ms")

@tree.command(name="help",description="Help menu")
async def help_cmd(i):
    e=emb_info("DarkNodes™ | VPS GEN — Help")
    e.add_field(name="User",value="`/start /stop /restart /delete`\n`/list /regen-ssh`\n`/tips /ping /help /node`",inline=False)
    e.add_field(name="Admin",value="`/deploy /nodedmin /delete-all /sendvps`",inline=False)
    await i.response.send_message(embed=e)

@tree.command(name="node",description="Show host stats")
async def node_cmd(i):
    ram, disk = psutil.virtual_memory(), psutil.disk_usage("/")
    uptime=str(timedelta(seconds=int((datetime.now()-datetime.fromtimestamp(psutil.boot_time())).total_seconds())))
    e=emb_info("🖥️ Node Status")
    e.add_field(name="CPU",value=f"{psutil.cpu_percent()}%",inline=True)
    e.add_field(name="RAM",value=f"{ram.used//(1024**2)}/{ram.total//(1024**2)} MB",inline=True)
    e.add_field(name="Disk",value=f"{disk.used//(1024**3)}/{disk.total//(1024**3)} GB",inline=True)
    e.add_field(name="Uptime",value=uptime,inline=False)
    if PUBLIC_IP: e.set_footer(text=f"Host: {PUBLIC_IP}")
    await i.response.send_message(embed=e)

# -------- Admin Deploy --------
@tree.command(name="deploy",description="Deploy VPS for a user")
@app_commands.describe(user="Target user",os="OS image",ram="RAM (GB)",cpu="CPU cores",expiry="Expiry (e.g. 1d,7d,1M)")
async def deploy(i,user:discord.Member,os:str,ram:int,cpu:int,expiry:str):
    if i.user.id not in ADMIN_IDS: return await i.response.send_message(embed=emb_err("No permission"))
    if os not in OS_IMAGE: return await i.response.send_message(embed=emb_err("Invalid OS"))
    if ram>MAX_RAM_GB or cpu>MAX_CPU: return await i.response.send_message(embed=emb_err("Exceeds limits"))
    cname=rand_name()
    exp=parse_expiry(expiry)

    # Make persistent directory
    vps_data_dir = f"{VPS_DATA_ROOT}/{cname}"
    os.makedirs(vps_data_dir, exist_ok=True)

    # Run container with persistence + auto-restart
    await run_cmd(
        "docker","run","-d",
        "--name",cname,
        "--memory",f"{ram}g",
        "--cpus",str(cpu),
        "--restart","always",
        "-v",f"{vps_data_dir}:/root",
        OS_IMAGE[os],
        "sleep","infinity"
    )

    ssh=await start_tmate(cname)
    record={"user_id":user.id,"container":cname,"os":os,"ram":ram,"cpu":cpu,"expiry":exp,"ssh":ssh}
    await db_append(record)
    e=emb_ok("🚀 VPS Deployed")
    e.add_field(name="User",value=f"{user.mention}")
    e.add_field(name="Container",value=cname)
    e.add_field(name="OS",value=os)
    e.add_field(name="RAM/CPU",value=f"{ram}GB/{cpu}")
    if exp: e.add_field(name="Expiry",value=exp)
    if ssh: e.add_field(name="SSH",value=f"```{ssh}```",inline=False)
    await i.response.send_message(embed=e)

# (rest of user/admin commands stay unchanged — start/stop/restart/delete/list/regen-ssh/tips/nodedmin/delete-all/sendvps)

# -------- Run --------
if __name__=="__main__":
    if not TOKEN: print("❌ Missing DISCORD_TOKEN in file")
    else: bot.run(TOKEN)
