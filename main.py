# main.py — ZENIX Sorgu Botu (42 Modül)
import io
import os
import json
import asyncio
import datetime
import threading
import time
import secrets
import re
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Optional
from urllib.parse import urlencode

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands

from smsapi import SmsBomber, SERVICE_NAMES

# ==================== HEALTH CHECK ====================
def run_health_server():
    port = int(os.getenv("PORT", 10000))
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"ZENIX CHECKER - AKTIF")
        def do_HEAD(self):
            self.send_response(200); self.end_headers()
        def log_message(self, *args): pass
    server = HTTPServer(("0.0.0.0", port), Handler)
    print(f"🌐 Health check {port} portunda")
    server.serve_forever()

threading.Thread(target=run_health_server, daemon=True).start()

# ==================== ENV ====================
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError: pass

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "")
SEARCH_KEY    = os.getenv("SEARCH_API_KEY", "91e2c5dfa0de4a22e2afbe5b")

ADMIN_ID = 1538810452308533308
MAIN_GUILD_ID = 1546912458793287725

WAZELY       = "https://wazely.vercel.app/api"
WAZELY_API   = "https://wazelyapi.vercel.app/api"
SOLIDARK     = "https://solidarksystems.alwaysdata.net"
SEARCHULP    = "https://searchulp.xyz/api"
ID_API       = "https://prox0959.netlify.app/api/search"
DISCORD_API_BASE = "https://kekeburasine-production-cb45.up.railway.app"

LOGO_URL = os.getenv("LOGO_URL", "https://media.discordapp.net/attachments/1547608436726824990/1557810396914651217/image.png?ex=6ac9277d&is=6ac7d5fd&hm=cd53b64f969a5b8c89b88f7375dd6cd5ae7d120b8f711ca778f349215a24da54&=&format=webp&quality=lossless")

COLOR_OK, COLOR_ERR, COLOR_Z = 0x10b981, 0xe11d48, 0x8b5cf6

# ==================== JSON DB ====================
DB_FILE = "zenix_data.json"

def load_db():
    if not os.path.exists(DB_FILE):
        return {"keys": {}, "user_keys": {}, "guilds": [MAIN_GUILD_ID]}
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        data.setdefault("keys", {}); data.setdefault("user_keys", {})
        data.setdefault("guilds", [MAIN_GUILD_ID])
        if MAIN_GUILD_ID not in data["guilds"]:
            data["guilds"].append(MAIN_GUILD_ID)
        return data
    except Exception:
        return {"keys": {}, "user_keys": {}, "guilds": [MAIN_GUILD_ID]}

def save_db():
    try:
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(DB, f, ensure_ascii=False, indent=2)
    except Exception as e: print(f"❌ DB: {e}")

DB = load_db()

def generate_key():
    p = lambda: secrets.token_hex(2).upper()
    return f"ZENIX-{p()}-{p()}-{p()}"

def user_has_key(uid): return str(uid) in DB["user_keys"]
def get_user_key(uid): return DB["user_keys"].get(str(uid))
def register_key(uid, key):
    DB["keys"][key] = {"user_id": uid, "created_at": datetime.datetime.utcnow().isoformat()}
    DB["user_keys"][str(uid)] = key
    save_db()
def is_allowed_guild(gid): return gid is not None and gid in DB["guilds"]
def is_admin(uid): return uid == ADMIN_ID

# ==================== FİLTRE ====================
HARD_BLOCK = [
    "arastirguncel", "iptal edilmiştir", "iptal edilmistir",
    "lutfen telegram", "lütfen telegram", "kanalimiza tekrar",
    "anahtariniz iptal", "anahtarınız iptal",
    "jessy_php", "@jessy", "jessy",
    "@wazelybaba", "wazelybaba", "wazely",
    "@ato.asd", "ato.asd", "atoasd",
    "@coder", "coder_",
]
SOFT_CLEAN = [
    "@arastirguncel", "arastirguncel", "t.me/arastirguncel",
    "telegram kanalimiza", "telegram kanalımıza",
    "@jessy_php", "jessy_php", "@jessy",
    "@wazelybaba", "wazelybaba",
    "@ato.asd", "ato.asd",
]
STRIP_KEYS = {
    "dev", "auth", "author", "developer", "credit", "credits",
    "owner", "made_by", "madeby", "creator", "source", "powered_by",
    "poweredby", "signature", "sign", "vendor", "provider_tag",
    "tg", "telegram", "contact", "sig", "watermark",
    "coder", "ig", "instagram", "message", "msg", "note",
    "not", "info_text", "info_message", "bio", "bio_text",
    "author_info", "signature_text", "sign_text", "extra",
    "extras", "meta", "meta_info", "developer_info",
}
REGEX_PATTERNS = [
    re.compile(r'ig\s*:\s*@?\w+', re.IGNORECASE),
    re.compile(r'instagram\s*:\s*@?\w+', re.IGNORECASE),
    re.compile(r'tg\s*:\s*@?\w+', re.IGNORECASE),
    re.compile(r'telegram\s*:\s*@?\w+', re.IGNORECASE),
    re.compile(r'auth\s*:\s*@?\w+', re.IGNORECASE),
    re.compile(r'coder\s*:\s*@?\w+', re.IGNORECASE),
    re.compile(r'dev\s*:\s*@?\w+', re.IGNORECASE),
    re.compile(r'credits?\s*:\s*@?\w+', re.IGNORECASE),
    re.compile(r'by\s+@\w+', re.IGNORECASE),
    re.compile(r'@[a-zA-Z0-9_.]+'),
]

def contains_hard_block(t):
    if not isinstance(t, str): return False
    low = t.lower()
    return any(p in low for p in HARD_BLOCK)

def scrub_text(t):
    if not isinstance(t, str): return t
    r = t
    for w in SOFT_CLEAN:
        r = r.replace(w, "").replace(w.title(), "").replace(w.upper(), "")
    for p in REGEX_PATTERNS:
        r = p.sub("", r)
    r = re.sub(r'\s{2,}', ' ', r).strip()
    return r.strip("|:-\t ")

def clean_data(data, depth=0):
    if depth > 10: return data
    if isinstance(data, str):
        if contains_hard_block(data): return None
        return scrub_text(data)
    if isinstance(data, dict):
        err = data.get("error")
        if err and isinstance(err, str) and contains_hard_block(err): return None
        c = {}
        for k, v in data.items():
            if k.lower() in STRIP_KEYS: continue
            cv = clean_data(v, depth+1)
            if cv is not None: c[k] = cv
        return c if c else None
    if isinstance(data, list):
        c = [clean_data(x, depth+1) for x in data]
        c = [x for x in c if x is not None]
        return c if c else None
    return data

def chunk_text(text, size=1900):
    return [text[i:i+size] for i in range(0, len(text), size)]

async def send_result(interaction, data):
    cleaned = clean_data(data)
    if cleaned is None:
        e = discord.Embed(color=COLOR_ERR, description="```\nSonuç bulunamadı.\n```")
        e.set_thumbnail(url=LOGO_URL)
        await interaction.followup.send(embed=e); return
    pretty = json.dumps(cleaned, indent=2, ensure_ascii=False) if isinstance(cleaned, (dict, list)) else str(cleaned)
    if pretty.strip() in ("{}", "[]", "null", ""):
        e = discord.Embed(color=COLOR_ERR, description="```\nSonuç bulunamadı.\n```")
        e.set_thumbnail(url=LOGO_URL)
        await interaction.followup.send(embed=e); return
    if len(pretty) > 3800:
        f = discord.File(io.BytesIO(pretty.encode("utf-8")), filename="zenix.json")
        e = discord.Embed(color=COLOR_OK, description=f"```json\n{pretty[:3800]}\n```")
        e.set_thumbnail(url=LOGO_URL)
        await interaction.followup.send(embed=e, file=f); return
    for i, c in enumerate(chunk_text(f"```json\n{pretty}\n```")):
        if i == 0:
            e = discord.Embed(color=COLOR_OK, description=c)
            e.set_thumbnail(url=LOGO_URL)
            await interaction.followup.send(embed=e)
        else: await interaction.followup.send(c)

def build_welcome_embed():
    e = discord.Embed(title="✨  HOŞ GELDİNİZ  ✨",
        description="**ZENIX CHECKER**\n\n🔎 Gelişmiş sorgulama sistemleri\n⚡ Hızlı ve güvenilir sonuçlar\n🎯 Tek komutla her şeye erişim\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n🔑 **Anahtar:** `/anahtargir`\n📖 **Komutlar:** `/yardim`",
        color=COLOR_Z, timestamp=datetime.datetime.utcnow())
    e.set_thumbnail(url=LOGO_URL); e.set_image(url=LOGO_URL)
    return e

async def fetch_json(url, timeout=25):
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(url, timeout=aiohttp.ClientTimeout(total=timeout)) as r:
                txt = await r.text()
                try: return json.loads(txt)
                except: return {"error": "invalid_response", "raw": txt[:200]}
    except asyncio.TimeoutError: return {"error": "timeout"}
    except Exception: return {"error": "connection_failed"}

async def precheck(interaction):
    if interaction.guild is None:
        await interaction.response.send_message("❌ **DM'den kullanamazsın.**", ephemeral=True); return False
    if not is_allowed_guild(interaction.guild.id):
        await interaction.response.send_message("❌ **Bu sunucuda izin yok.**", ephemeral=True); return False
    if not is_admin(interaction.user.id) and not user_has_key(interaction.user.id):
        await interaction.response.send_message("🔑 **Anahtar gerekli!** `/anahtargir`", ephemeral=True); return False
    return True

# ==================== BOT ====================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ==================== READY ====================
@bot.event
async def on_ready():
    print(f"✅ ZENIX aktif: {bot.user}")
    print(f"🌐 {len(bot.guilds)} sunucuda")
    print(f"🏠 İzinli: {DB['guilds']}")
    try:
        s = await bot.tree.sync()
        print(f"🔁 {len(s)} komut yüklendi.")
    except Exception as e: print(f"❌ Sync: {e}")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="zenix.bond"))

@bot.event
async def on_member_join(member):
    if not is_allowed_guild(member.guild.id): return
    for ch in member.guild.text_channels:
        if ch.permissions_for(member.guild.me).send_messages:
            try: await ch.send(content=f"{member.mention} katıldı! 🎉", embed=build_welcome_embed())
            except: pass
            break

# ==================== ANAHTAR ====================
@bot.tree.command(name="anahtargir", description="ZENIX anahtarını gir")
@app_commands.describe(anahtar="ZENIX-XXXX-XXXX-XXXX")
async def anahtargir(interaction, anahtar: str):
    if interaction.guild is None:
        await interaction.response.send_message("❌ Sunucuda kullan.", ephemeral=True); return
    if not is_allowed_guild(interaction.guild.id):
        await interaction.response.send_message("❌ İzin yok.", ephemeral=True); return
    anahtar = anahtar.strip().upper()
    if user_has_key(interaction.user.id):
        await interaction.response.send_message(f"✅ Zaten: `{get_user_key(interaction.user.id)}`", ephemeral=True); return
    if anahtar not in DB["keys"]:
        await interaction.response.send_message("❌ Geçersiz.", ephemeral=True); return
    ki = DB["keys"][anahtar]
    if ki.get("user_id") and ki["user_id"] != interaction.user.id:
        await interaction.response.send_message("❌ Başkasına ait.", ephemeral=True); return
    register_key(interaction.user.id, anahtar)
    e = discord.Embed(title="✅ Anahtar Aktif", description=f"Hoş geldin {interaction.user.mention}!", color=COLOR_OK, timestamp=datetime.datetime.utcnow())
    e.add_field(name="🔑 Anahtarın", value=f"`{anahtar}`", inline=False)
    e.set_thumbnail(url=LOGO_URL)
    await interaction.response.send_message(embed=e, ephemeral=True)

@bot.tree.command(name="anahtarolustur", description="[ADMIN] Yeni anahtar")
@app_commands.describe(kullanici="Kullanıcı")
async def anahtarolustur(interaction, kullanici: discord.Member):
    if not is_admin(interaction.user.id):
        await interaction.response.send_message("❌ Admin değilsin.", ephemeral=True); return
    nk = generate_key()
    while nk in DB["keys"]: nk = generate_key()
    DB["keys"][nk] = {"user_id": None, "created_at": datetime.datetime.utcnow().isoformat()}
    save_db()
    e = discord.Embed(title="🔑 Yeni Anahtar", description=f"Kullanıcı: {kullanici.mention}", color=COLOR_OK, timestamp=datetime.datetime.utcnow())
    e.add_field(name="Anahtar", value=f"`{nk}`", inline=False)
    e.add_field(name="Kullanım", value=f"`/anahtargir anahtar:{nk}`", inline=False)
    e.set_thumbnail(url=LOGO_URL)
    await interaction.response.send_message(embed=e, ephemeral=True)
    try: await kullanici.send(f"🔑 **ZENIX Anahtarın:** `{nk}`\n`/anahtargir` ile aktif et.")
    except: pass

@bot.tree.command(name="anahtarsil", description="[ADMIN] Anahtar sil")
@app_commands.describe(kullanici="Kullanıcı")
async def anahtarsil(interaction, kullanici: discord.Member):
    if not is_admin(interaction.user.id):
        await interaction.response.send_message("❌ Admin değilsin.", ephemeral=True); return
    uid = str(kullanici.id)
    if uid not in DB["user_keys"]:
        await interaction.response.send_message("❌ Yok.", ephemeral=True); return
    k = DB["user_keys"].pop(uid)
    if k in DB["keys"]: DB["keys"].pop(k)
    save_db()
    await interaction.response.send_message(f"✅ {kullanici.mention} silindi.", ephemeral=True)

@bot.tree.command(name="anahtarlistesi", description="[ADMIN] Anahtarlar")
async def anahtarlistesi(interaction):
    if not is_admin(interaction.user.id):
        await interaction.response.send_message("❌ Admin değilsin.", ephemeral=True); return
    if not DB["keys"]:
        await interaction.response.send_message("📭 Boş.", ephemeral=True); return
    lines = [f"✅ `{k}` → <@{v.get('user_id')}>" if v.get("user_id") else f"🆓 `{k}` → boşta" for k, v in DB["keys"].items()]
    t = "\n".join(lines)
    if len(t) > 1900: t = t[:1900] + "\n..."
    e = discord.Embed(title=f"🔑 Anahtarlar ({len(DB['keys'])})", description=t, color=COLOR_Z)
    e.set_thumbnail(url=LOGO_URL)
    await interaction.response.send_message(embed=e, ephemeral=True)

# ==================== SUNUCU ====================
@bot.tree.command(name="sunucuekle", description="[ADMIN] Sunucu ekle + davet linki")
@app_commands.describe(sunucu_id="Sunucu ID")
async def sunucuekle(interaction, sunucu_id: str):
    if not is_admin(interaction.user.id):
        await interaction.response.send_message("❌ Admin değilsin.", ephemeral=True); return
    try: gid = int(sunucu_id.strip())
    except: await interaction.response.send_message("❌ Geçersiz ID.", ephemeral=True); return
    if gid in DB["guilds"]:
        await interaction.response.send_message(f"ℹ️ Zaten ekli: `{gid}`", ephemeral=True); return
    DB["guilds"].append(gid); save_db()
    url = discord.utils.oauth_url(bot.user.id, permissions=discord.Permissions(administrator=True), scopes=("bot", "applications.commands"), guild=discord.Object(id=gid))
    e = discord.Embed(title="✅ Sunucu Eklendi", description=f"`{gid}` eklendi.", color=COLOR_OK)
    e.add_field(name="🔗 Davet Linki", value=f"[Tıkla]({url})", inline=False)
    e.add_field(name="📋 Kopyala", value=f"```\n{url}\n```", inline=False)
    e.set_thumbnail(url=LOGO_URL)
    await interaction.response.send_message(embed=e, ephemeral=True)

@bot.tree.command(name="sunuculistesi", description="[ADMIN] Sunucular")
async def sunuculistesi(interaction):
    if not is_admin(interaction.user.id):
        await interaction.response.send_message("❌ Admin değilsin.", ephemeral=True); return
    e = discord.Embed(title=f"🏠 İzinli ({len(DB['guilds'])})", description="\n".join(f"• `{g}`" for g in DB["guilds"]), color=COLOR_Z)
    e.set_thumbnail(url=LOGO_URL)
    await interaction.response.send_message(embed=e, ephemeral=True)

@bot.tree.command(name="sunucusil", description="[ADMIN] Sunucu sil")
@app_commands.describe(sunucu_id="Sunucu ID")
async def sunucusil(interaction, sunucu_id: str):
    if not is_admin(interaction.user.id):
        await interaction.response.send_message("❌ Admin değilsin.", ephemeral=True); return
    try: gid = int(sunucu_id.strip())
    except: await interaction.response.send_message("❌ Geçersiz ID.", ephemeral=True); return
    if gid == MAIN_GUILD_ID:
        await interaction.response.send_message("❌ Ana sunucu silinemez.", ephemeral=True); return
    if gid not in DB["guilds"]:
        await interaction.response.send_message("❌ Listede yok.", ephemeral=True); return
    DB["guilds"].remove(gid); save_db()
    await interaction.response.send_message(f"✅ `{gid}` çıkarıldı.", ephemeral=True)

# ==================== GRUPLAR ====================
zg  = app_commands.Group(name="zenix",  description="ZENIX - Genel")
zg2 = app_commands.Group(name="zenix2", description="ZENIX - TC/Kimlik")
zg3 = app_commands.Group(name="zenix3", description="ZENIX - Ad/Soyad")

# ==================== /zenix ====================
@zg.command(name="bedrock", description="MC Bedrock")
@app_commands.describe(adres="Adres")
async def zb(interaction, adres: str):
    if not await precheck(interaction): return
    await interaction.response.defer()
    await send_result(interaction, await fetch_json(f"{WAZELY_API}/bedrock?adres={adres}"))

@zg.command(name="ccgen", description="Rastgele kart")
async def zcc(interaction):
    if not await precheck(interaction): return
    await interaction.response.defer()
    await send_result(interaction, await fetch_json(f"{WAZELY_API}/ccgen"))

@zg.command(name="cccheck", description="Kart kontrol")
@app_commands.describe(data="Kart")
async def zccc(interaction, data: str):
    if not await precheck(interaction): return
    await interaction.response.defer()
    await send_result(interaction, await fetch_json(f"{WAZELY_API}/check?data={data}"))

@zg.command(name="dctoken", description="Discord token test")
@app_commands.describe(token="Token")
async def zdt(interaction, token: str):
    if not await precheck(interaction): return
    await interaction.response.defer(ephemeral=True)
    await send_result(interaction, await fetch_json(f"{WAZELY_API}/dcbottokencheck?token={token}"))

@zg.command(name="tgtoken", description="Telegram token test")
@app_commands.describe(token="Token")
async def ztt(interaction, token: str):
    if not await precheck(interaction): return
    await interaction.response.defer(ephemeral=True)
    await send_result(interaction, await fetch_json(f"{WAZELY_API}/tgtokencheck?token={token}"))

@zg.command(name="trlog", description="TR log")
@app_commands.describe(site="Site")
async def ztl(interaction, site: str):
    if not await precheck(interaction): return
    await interaction.response.defer()
    await send_result(interaction, await fetch_json(f"{WAZELY}/trlog?site={site}"))

@zg.command(name="log", description="Site log")
@app_commands.describe(url="Domain")
async def zl(interaction, url: str):
    if not await precheck(interaction): return
    await interaction.response.defer()
    await send_result(interaction, await fetch_json(f"{SOLIDARK}/log.php?url={url}"))

@zg.command(name="logglobal", description="Global log")
@app_commands.describe(domain="Domain")
async def zlg(interaction, domain: str):
    if not await precheck(interaction): return
    await interaction.response.defer()
    await send_result(interaction, await fetch_json(f"{DISCORD_API_BASE}/log/global?domain={domain}"))

@zg.command(name="eczane", description="Eczane")
@app_commands.describe(ad="Ad")
async def ze(interaction, ad: str):
    if not await precheck(interaction): return
    await interaction.response.defer()
    await send_result(interaction, await fetch_json(f"{WAZELY}/eczane?ad={ad}"))

@zg.command(name="ipinfo", description="IP bilgi")
@app_commands.describe(ip="IP")
async def zip(interaction, ip: str):
    if not await precheck(interaction): return
    await interaction.response.defer()
    await send_result(interaction, await fetch_json(f"{WAZELY}/ipinfo?ip={ip}"))

@zg.command(name="dns", description="DNS")
@app_commands.describe(domain="Domain")
async def zd(interaction, domain: str):
    if not await precheck(interaction): return
    await interaction.response.defer()
    await send_result(interaction, await fetch_json(f"{WAZELY}/dns?domain={domain}"))

@zg.command(name="bahis", description="Bahis")
@app_commands.describe(isimsoyisim="İsim")
async def zba(interaction, isimsoyisim: str):
    if not await precheck(interaction): return
    await interaction.response.defer()
    await send_result(interaction, await fetch_json(f"{WAZELY}/bahis?isimsoyisim={isimsoyisim}"))

@zg.command(name="exxengen", description="Exxen hesap")
async def zex(interaction):
    if not await precheck(interaction): return
    await interaction.response.defer()
    await send_result(interaction, await fetch_json(f"{WAZELY}/exxengen"))

@zg.command(name="nitrogen", description="Nitro kodları")
@app_commands.describe(count="Adet")
async def zn(interaction, count: Optional[int] = 10):
    if not await precheck(interaction): return
    await interaction.response.defer()
    await send_result(interaction, await fetch_json(f"{WAZELY}/fakeNitro?count={count}"))

@zg.command(name="pingtest", description="Ping test")
@app_commands.describe(target="Hedef")
async def zpt(interaction, target: str):
    if not await precheck(interaction): return
    await interaction.response.defer()
    await send_result(interaction, await fetch_json(f"{WAZELY}/ping?target={target}"))

@zg.command(name="plaka", description="Plaka")
@app_commands.describe(plate="Plaka")
async def zpl(interaction, plate: str):
    if not await precheck(interaction): return
    await interaction.response.defer()
    await send_result(interaction, await fetch_json(f"{WAZELY}/plaka?plate={plate}"))

@zg.command(name="predunyam", description="Predunyam hesap")
async def zpr(interaction):
    if not await precheck(interaction): return
    await interaction.response.defer()
    await send_result(interaction, await fetch_json(f"{WAZELY}/predunyam"))

@zg.command(name="useragent", description="Rastgele UA")
async def zua(interaction):
    if not await precheck(interaction): return
    await interaction.response.defer()
    await send_result(interaction, await fetch_json(f"{WAZELY}/randomuseragent"))

@zg.command(name="discord", description="Discord ID sorgu")
@app_commands.describe(id="Discord ID")
async def zdis(interaction, id: str):
    if not await precheck(interaction): return
    await interaction.response.defer()
    await send_result(interaction, await fetch_json(f"{ID_API}?id={id}"))

@zg.command(name="smsbomber", description="SMS Bomber - Normal")
@app_commands.describe(numara="Telefon", adet="Tur (max 10)", mail="Mail (ops.)")
async def zsb(interaction, numara: str, adet: Optional[int] = 1, mail: Optional[str] = None):
    if not await precheck(interaction): return
    await interaction.response.defer()
    adet = max(1, min(adet, 10))
    b = SmsBomber(numara, mail or "")
    start = time.time()
    e = discord.Embed(title="💣 SMS BOMBER - NORMAL", description=f"📱 `{numara}` | 🔁 {adet} | ⏳ Çalışıyor...", color=COLOR_Z, timestamp=datetime.datetime.utcnow())
    e.set_thumbnail(url=LOGO_URL)
    msg = await interaction.followup.send(embed=e)
    await b.run_normal_async(adet)
    el = round(time.time() - start, 2)
    ok = sum(1 for _, v in b.results if v)
    fl = len(b.results) - ok
    summary = {}
    for n, s in b.results:
        summary.setdefault(n, {"ok": 0, "fail": 0})
        if s: summary[n]["ok"] += 1
        else: summary[n]["fail"] += 1
    lines = [f"{'✅' if s['ok']>0 else '❌'} `{n}` → {s['ok']}✅ / {s['fail']}❌" for n, s in summary.items()]
    full = "\n".join(lines)
    e = discord.Embed(title="💣 SMS BOMBER - NORMAL", description=f"📱 `{numara}` | 🔁 {adet} | ⏱️ {el}s", color=COLOR_OK, timestamp=datetime.datetime.utcnow())
    e.add_field(name="📊 Özet", value=f"✅ **{ok}** | ❌ **{fl}**", inline=False)
    e.set_thumbnail(url=LOGO_URL)
    if len(full) > 1000:
        f = discord.File(io.BytesIO(full.encode("utf-8")), filename="zenix_sms.txt")
        await msg.edit(embed=e)
        await interaction.followup.send(file=f)
    else:
        e.add_field(name="🔍 Detay", value=full or "Yok", inline=False)
        await msg.edit(embed=e)

@zg.command(name="turbo", description="SMS Bomber - Turbo")
@app_commands.describe(numara="Telefon", adet="Tur (max 10)", mail="Mail (ops.)")
async def ztb(interaction, numara: str, adet: Optional[int] = 1, mail: Optional[str] = None):
    if not await precheck(interaction): return
    await interaction.response.defer()
    adet = max(1, min(adet, 10))
    b = SmsBomber(numara, mail or "")
    start = time.time()
    e = discord.Embed(title="🚀 SMS BOMBER - TURBO", description=f"📱 `{numara}` | 🔁 {adet} | ⚡ Paralel...", color=COLOR_Z, timestamp=datetime.datetime.utcnow())
    e.set_thumbnail(url=LOGO_URL)
    msg = await interaction.followup.send(embed=e)
    await b.run_turbo(adet)
    el = round(time.time() - start, 2)
    ok = sum(1 for _, v in b.results if v)
    fl = len(b.results) - ok
    summary = {}
    for n, s in b.results:
        summary.setdefault(n, {"ok": 0, "fail": 0})
        if s: summary[n]["ok"] += 1
        else: summary[n]["fail"] += 1
    lines = [f"{'✅' if s['ok']>0 else '❌'} `{n}` → {s['ok']}✅ / {s['fail']}❌" for n, s in summary.items()]
    full = "\n".join(lines)
    e = discord.Embed(title="🚀 SMS BOMBER - TURBO", description=f"📱 `{numara}` | 🔁 {adet} | ⏱️ {el}s", color=COLOR_OK, timestamp=datetime.datetime.utcnow())
    e.add_field(name="📊 Özet", value=f"✅ **{ok}** | ❌ **{fl}**", inline=False)
    e.set_thumbnail(url=LOGO_URL)
    if len(full) > 1000:
        f = discord.File(io.BytesIO(full.encode("utf-8")), filename="zenix_turbo.txt")
        await msg.edit(embed=e)
        await interaction.followup.send(file=f)
    else:
        e.add_field(name="🔍 Detay", value=full or "Yok", inline=False)
        await msg.edit(embed=e)

@zg.command(name="servisler", description="SMS servis listesi")
async def zsv(interaction):
    if not await precheck(interaction): return
    e = discord.Embed(title="📋 SMS Servisler", description=f"Toplam **{len(SERVICE_NAMES)}** servis", color=COLOR_Z)
    half = len(SERVICE_NAMES) // 2
    e.add_field(name="Servisler (1)", value="\n".join(f"• `{s}`" for s in SERVICE_NAMES[:half]), inline=True)
    e.add_field(name="Servisler (2)", value="\n".join(f"• `{s}`" for s in SERVICE_NAMES[half:]), inline=True)
    e.set_thumbnail(url=LOGO_URL)
    await interaction.response.send_message(embed=e)

# ==================== /zenix2 — TC/KİMLİK ====================
@zg2.command(name="tc", description="TC sorgu")
@app_commands.describe(tc="TC")
async def z2tc(interaction, tc: str):
    if not await precheck(interaction): return
    await interaction.response.defer()
    d = await fetch_json(f"{SOLIDARK}/tc.php?tc={tc}")
    if clean_data(d) is None: d = await fetch_json(f"{SEARCHULP}/tc/{tc}?key={SEARCH_KEY}")
    await send_result(interaction, d)

@zg2.command(name="tcpro", description="TC Pro")
@app_commands.describe(tc="TC")
async def z2tcp(interaction, tc: str):
    if not await precheck(interaction): return
    await interaction.response.defer()
    d = await fetch_json(f"{SOLIDARK}/tcpro.php?tc={tc}")
    if clean_data(d) is None: d = await fetch_json(f"{SEARCHULP}/tc/{tc}?key={SEARCH_KEY}")
    await send_result(interaction, d)

@zg2.command(name="aile", description="Aile")
@app_commands.describe(tc="TC")
async def z2a(interaction, tc: str):
    if not await precheck(interaction): return
    await interaction.response.defer()
    await send_result(interaction, await fetch_json(f"{SEARCHULP}/aile/{tc}?key={SEARCH_KEY}"))

@zg2.command(name="ailepro", description="Aile Pro")
@app_commands.describe(tc="TC")
async def z2ap(interaction, tc: str):
    if not await precheck(interaction): return
    await interaction.response.defer()
    await send_result(interaction, await fetch_json(f"{SOLIDARK}/ailepro.php?tc={tc}"))

@zg2.command(name="sulale", description="Sülale")
@app_commands.describe(tc="TC")
async def z2s(interaction, tc: str):
    if not await precheck(interaction): return
    await interaction.response.defer()
    await send_result(interaction, await fetch_json(f"{SEARCHULP}/sulale/{tc}?key={SEARCH_KEY}"))

@zg2.command(name="cocuk", description="Çocuk")
@app_commands.describe(tc="TC")
async def z2c(interaction, tc: str):
    if not await precheck(interaction): return
    await interaction.response.defer()
    await send_result(interaction, await fetch_json(f"{SEARCHULP}/cocuk/{tc}?key={SEARCH_KEY}"))

@zg2.command(name="adres", description="Adres")
@app_commands.describe(tc="TC")
async def z2ad(interaction, tc: str):
    if not await precheck(interaction): return
    await interaction.response.defer()
    await send_result(interaction, await fetch_json(f"{SEARCHULP}/adres/{tc}?key={SEARCH_KEY}"))

@zg2.command(name="gsmtc", description="GSM → TC")
@app_commands.describe(gsm="GSM")
async def z2g(interaction, gsm: str):
    if not await precheck(interaction): return
    await interaction.response.defer()
    await send_result(interaction, await fetch_json(f"{SEARCHULP}/gsmtc/{gsm}?key={SEARCH_KEY}"))

@zg2.command(name="tcgsm", description="TC → GSM")
@app_commands.describe(tc="TC")
async def z2tg(interaction, tc: str):
    if not await precheck(interaction): return
    await interaction.response.defer()
    await send_result(interaction, await fetch_json(f"{SEARCHULP}/tcgsm/{tc}?key={SEARCH_KEY}"))

@zg2.command(name="isyeri", description="İşyeri")
@app_commands.describe(tc="TC")
async def z2i(interaction, tc: str):
    if not await precheck(interaction): return
    await interaction.response.defer()
    await send_result(interaction, await fetch_json(f"{SEARCHULP}/isyeri/{tc}?key={SEARCH_KEY}"))

@zg2.command(name="vesika", description="Vesika")
@app_commands.describe(tc="TC")
async def z2v(interaction, tc: str):
    if not await precheck(interaction): return
    await interaction.response.defer()
    await send_result(interaction, await fetch_json(f"{SOLIDARK}/vesika.php?tc={tc}"))

@zg2.command(name="sgk", description="SGK")
@app_commands.describe(tc="TC")
async def z2sg(interaction, tc: str):
    if not await precheck(interaction): return
    await interaction.response.defer()
    await send_result(interaction, await fetch_json(f"{SOLIDARK}/sgk.php?tc={tc}"))

@zg2.command(name="idsorgu", description="ID sorgu")
@app_commands.describe(id="ID")
async def z2id(interaction, id: str):
    if not await precheck(interaction): return
    await interaction.response.defer()
    await send_result(interaction, await fetch_json(f"{ID_API}?id={id}"))

@zg2.command(name="toplutc", description="Toplu TC sorgu")
@app_commands.describe(tcler="Her satıra bir TC (11 hane)")
async def z2tt(interaction, tcler: str):
    if not await precheck(interaction): return
    await interaction.response.defer()
    tclist = [t.strip() for t in tcler.split("\n") if len(t.strip()) == 11]
    if not tclist:
        await send_result(interaction, {"error": "Geçerli TC bulunamadı"}); return
    results = {}
    for tc in tclist[:20]:
        d = await fetch_json(f"{SOLIDARK}/tcpro.php?tc={tc}")
        if clean_data(d) is None:
            d = await fetch_json(f"{SEARCHULP}/tc/{tc}?key={SEARCH_KEY}")
        results[tc] = clean_data(d) or "Bulunamadı"
    await send_result(interaction, results)

@zg2.command(name="profil", description="Kişi profili (5'li)")
@app_commands.describe(tc="TC")
async def z2p(interaction, tc: str):
    if not await precheck(interaction): return
    await interaction.response.defer()
    profile = {}
    profile["Kimlik"] = await fetch_json(f"{SEARCHULP}/tc/{tc}?key={SEARCH_KEY}")
    profile["Aile"] = await fetch_json(f"{SEARCHULP}/aile/{tc}?key={SEARCH_KEY}")
    profile["Adres"] = await fetch_json(f"{SEARCHULP}/adres/{tc}?key={SEARCH_KEY}")
    profile["GSM"] = await fetch_json(f"{SEARCHULP}/tcgsm/{tc}?key={SEARCH_KEY}")
    profile["İşyeri"] = await fetch_json(f"{SEARCHULP}/isyeri/{tc}?key={SEARCH_KEY}")
    await send_result(interaction, profile)

# ==================== /zenix3 — AD/SOYAD ====================
@zg3.command(name="adsoyad", description="Ad soyad arama")
@app_commands.describe(ad="Ad", soyad="Soyad", il="İl", ilce="İlçe", dogumtarihi="Doğum")
async def z3as(interaction, ad: str, soyad: Optional[str] = None, il: Optional[str] = None, ilce: Optional[str] = None, dogumtarihi: Optional[str] = None):
    if not await precheck(interaction): return
    await interaction.response.defer()
    p = {"ad": ad, "key": SEARCH_KEY}
    if soyad: p["soyad"] = soyad
    if il: p["il"] = il
    if ilce: p["ilce"] = ilce
    if dogumtarihi: p["dogumtarihi"] = dogumtarihi
    await send_result(interaction, await fetch_json(f"{SEARCHULP}/adsoyad?{urlencode(p)}"))

@zg3.command(name="adsoyadil", description="Ad soyad il ilçe")
@app_commands.describe(ad="Ad", soyad="Soyad", il="İl", ilce="İlçe")
async def z3asi(interaction, ad: str, soyad: str, il: str, ilce: str):
    if not await precheck(interaction): return
    await interaction.response.defer()
    await send_result(interaction, await fetch_json(f"{SOLIDARK}/adsoyad.php?ad={ad}&soyad={soyad}&il={il}&ilce={ilce}"))

@zg3.command(name="adililce", description="Ad il ilçe")
@app_commands.describe(ad="Ad", il="İl", ilce="İlçe")
async def z3ai(interaction, ad: str, il: str, ilce: str):
    if not await precheck(interaction): return
    await interaction.response.defer()
    await send_result(interaction, await fetch_json(f"{SOLIDARK}/adililce.php?ad={ad}&il={il}&ilce={ilce}"))

# ==================== GENEL ====================
@bot.tree.command(name="ping", description="Ping")
async def ping(interaction):
    await interaction.response.send_message(f"```\n{round(bot.latency * 1000)}ms\n```")

@bot.tree.command(name="yardim", description="ZENIX komutlar")
async def yardim(interaction):
    if interaction.guild is None:
        await interaction.response.send_message("❌ Sunucuda kullan.", ephemeral=True); return
    g1 = [c.name for c in zg.commands]
    g2 = [c.name for c in zg2.commands]
    g3 = [c.name for c in zg3.commands]
    e = discord.Embed(title="✨  ZENIX CHECKER  ✨", description="🔎 Tüm komutlar\n━━━━━━━━━━━━━━━━━━━━━━━━━━", color=COLOR_Z, timestamp=datetime.datetime.utcnow())
    e.add_field(name="⚡ `/zenix`", value="`" + "` `".join(sorted(g1)) + "`", inline=False)
    e.add_field(name="🪪 `/zenix2`", value="`" + "` `".join(sorted(g2)) + "`", inline=False)
    e.add_field(name="👤 `/zenix3`", value="`" + "` `".join(sorted(g3)) + "`", inline=False)
    e.add_field(name="🔑 Anahtar", value="`/anahtargir`", inline=False)
    e.add_field(name="👑 Admin", value="`/anahtarolustur` `/anahtarsil` `/anahtarlistesi` `/sunucuekle` `/sunuculistesi` `/sunucusil`", inline=False)
    e.set_thumbnail(url=LOGO_URL); e.set_image(url=LOGO_URL)
    await interaction.response.send_message(embed=e)

@bot.tree.command(name="hosgeldin", description="Hoş geldin")
async def hosgeldin(interaction):
    await interaction.response.send_message(embed=build_welcome_embed())

# ==================== KAYIT ====================
bot.tree.add_command(zg)
bot.tree.add_command(zg2)
bot.tree.add_command(zg3)

# ==================== ÇALIŞTIR ====================
if __name__ == "__main__":
    if not DISCORD_TOKEN:
        print("❌ DISCORD_TOKEN yok!"); exit(1)
    print("🚀 ZENIX başlatılıyor...")
    bot.run(DISCORD_TOKEN)
