# main.py — ZENIX Sorgu Botu
import io
import os
import json
import asyncio
import datetime
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Optional
from urllib.parse import urlencode

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands

# ==================== HEALTH CHECK SERVER ====================
# Render Web Service için port dinleyen basit sunucu
def run_health_server():
    port = int(os.getenv("PORT", 10000))

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"ZENIX CHECKER - AKTIF")

        def do_HEAD(self):
            self.send_response(200)
            self.end_headers()

        def log_message(self, format, *args):
            pass  # Konsolu kirletmesin

    server = HTTPServer(("0.0.0.0", port), Handler)
    print(f"🌐 Health check {port} portunda çalışıyor")
    server.serve_forever()

# Arka planda başlat
threading.Thread(target=run_health_server, daemon=True).start()


# ==================== ENV'DEN OKUMA ====================
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "")
SEARCH_KEY    = os.getenv("SEARCH_API_KEY", "91e2c5dfa0de4a22e2afbe5b")

# API Endpoint'leri
WAZELY       = "https://wazely.vercel.app/api"
WAZELY_API   = "https://wazelyapi.vercel.app/api"
SOLIDARK     = "https://solidarksystems.alwaysdata.net"
SEARCHULP    = "https://searchulp.xyz/api"
ID_API       = "https://prox0959.netlify.app/api/search"

LOGO_URL = os.getenv(
    "LOGO_URL",
    "https://media.discordapp.net/attachments/1547608436726824990/1557810396914651217/image.png?ex=6ac9277d&is=6ac7d5fd&hm=cd53b64f969a5b8c89b88f7375dd6cd5ae7d120b8f711ca778f349215a24da54&=&format=webp&quality=lossless"
)

COLOR_OK   = 0x10b981
COLOR_ERR  = 0xe11d48
COLOR_Z    = 0x8b5cf6

# ==================== FİLTRE KURALLARI ====================
BLOCKED_PATTERNS = [
    "arastirguncel",
    "iptal edilmiştir",
    "iptal edilmistir",
    "lutfen telegram",
    "lütfen telegram",
    "kanalimiza tekrar",
    "anahtariniz iptal",
    "anahtarınız iptal",
]

CLEANUP_WORDS = [
    "@arastirguncel",
    "arastirguncel",
    "t.me/arastirguncel",
    "telegram kanalimiza",
    "telegram kanalımıza",
]

# ==================== BOT ====================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)


# ==================== YARDIMCILAR ====================
async def fetch_json(url: str, timeout: int = 25):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=timeout)) as r:
                text = await r.text()
                try:
                    return json.loads(text)
                except Exception:
                    return {"error": "invalid_response", "raw": text[:200]}
    except asyncio.TimeoutError:
        return {"error": "timeout"}
    except Exception:
        return {"error": "connection_failed"}


def contains_blocked(text: str) -> bool:
    if not isinstance(text, str):
        return False
    low = text.lower()
    for pat in BLOCKED_PATTERNS:
        if pat in low:
            return True
    return False


def scrub_text(text: str) -> str:
    if not isinstance(text, str):
        return text
    result = text
    for word in CLEANUP_WORDS:
        result = result.replace(word, "")
        result = result.replace(word.title(), "")
        result = result.replace(word.upper(), "")
    return result.strip()


def clean_data(data, depth: int = 0):
    if depth > 10:
        return data
    if isinstance(data, str):
        if contains_blocked(data):
            return None
        return scrub_text(data)
    if isinstance(data, dict):
        err = data.get("error")
        if err and isinstance(err, str) and contains_blocked(err):
            return None
        cleaned = {}
        for k, v in data.items():
            if k.lower() == "dev":
                continue
            cleaned_v = clean_data(v, depth + 1)
            if cleaned_v is not None:
                cleaned[k] = cleaned_v
        return cleaned if cleaned else None
    if isinstance(data, list):
        cleaned = [clean_data(x, depth + 1) for x in data]
        cleaned = [x for x in cleaned if x is not None]
        return cleaned if cleaned else None
    return data


def chunk_text(text: str, size: int = 1900):
    return [text[i:i + size] for i in range(0, len(text), size)]


async def send_result(interaction: discord.Interaction, data):
    cleaned = clean_data(data)
    if cleaned is None:
        embed = discord.Embed(color=COLOR_ERR, description="```\nSonuç bulunamadı.\n```")
        embed.set_thumbnail(url=LOGO_URL)
        await interaction.followup.send(embed=embed)
        return

    if isinstance(cleaned, (dict, list)):
        pretty = json.dumps(cleaned, indent=2, ensure_ascii=False)
    else:
        pretty = str(cleaned)

    if pretty.strip() in ("{}", "[]", "null", ""):
        embed = discord.Embed(color=COLOR_ERR, description="```\nSonuç bulunamadı.\n```")
        embed.set_thumbnail(url=LOGO_URL)
        await interaction.followup.send(embed=embed)
        return

    if len(pretty) > 3800:
        file = discord.File(io.BytesIO(pretty.encode("utf-8")), filename="zenix.json")
        embed = discord.Embed(color=COLOR_OK)
        embed.description = f"```json\n{pretty[:3800]}\n```"
        embed.set_thumbnail(url=LOGO_URL)
        await interaction.followup.send(embed=embed, file=file)
        return

    chunks = chunk_text(f"```json\n{pretty}\n```")
    for i, chunk in enumerate(chunks):
        if i == 0:
            embed = discord.Embed(color=COLOR_OK, description=chunk)
            embed.set_thumbnail(url=LOGO_URL)
            await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send(chunk)


def build_welcome_embed() -> discord.Embed:
    embed = discord.Embed(
        title="✨  HOŞ GELDİNİZ  ✨",
        description=(
            "**ZENIX CHECKER**\n\n"
            "🔎  Gelişmiş sorgulama sistemleri\n"
            "⚡  Hızlı ve güvenilir sonuçlar\n"
            "🎯  Tek komutla her şeye erişim\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "**Başlamak için:** `/yardim`"
        ),
        color=COLOR_Z,
        timestamp=datetime.datetime.utcnow()
    )
    embed.set_thumbnail(url=LOGO_URL)
    embed.set_image(url=LOGO_URL)
    return embed


# ==================== HAZIRLIK ====================
@bot.event
async def on_ready():
    print(f"✅ ZENIX aktif: {bot.user}")
    print(f"🌐 {len(bot.guilds)} sunucuda çalışıyor")
    try:
        synced = await bot.tree.sync()
        print(f"🔁 {len(synced)} komut yüklendi.")
    except Exception as e:
        print(f"❌ Sync hatası: {e}")
    await bot.change_presence(
        activity=discord.Activity(type=discord.ActivityType.watching, name="zenix.bond")
    )


@bot.event
async def on_member_join(member: discord.Member):
    channel = None
    for ch in member.guild.text_channels:
        if ch.permissions_for(member.guild.me).send_messages:
            channel = ch
            break
    if channel:
        try:
            await channel.send(
                content=f"{member.mention} sunucuya katıldı! 🎉",
                embed=build_welcome_embed()
            )
        except Exception:
            pass


# ==================== GRUPLAR ====================
zenix_group  = app_commands.Group(name="zenix",  description="ZENIX - Genel Sorgular")
zenix2_group = app_commands.Group(name="zenix2", description="ZENIX - TC & Kimlik Sorguları")
zenix3_group = app_commands.Group(name="zenix3", description="ZENIX - Ad/Soyad & Adres")


# ==================== /zenix — GENEL ====================
@zenix_group.command(name="bedrock", description="Minecraft Bedrock sunucu durumu")
@app_commands.describe(adres="Sunucu adresi")
async def z_bedrock(interaction: discord.Interaction, adres: str):
    await interaction.response.defer()
    data = await fetch_json(f"{WAZELY_API}/bedrock?adres={adres}")
    await send_result(interaction, data)


@zenix_group.command(name="ccgen", description="Rastgele kart üretir")
async def z_ccgen(interaction: discord.Interaction):
    await interaction.response.defer()
    data = await fetch_json(f"{WAZELY_API}/ccgen")
    await send_result(interaction, data)


@zenix_group.command(name="cccheck", description="Kart geçerlilik kontrolü")
@app_commands.describe(data="Kart verisi")
async def z_cccheck(interaction: discord.Interaction, data: str):
    await interaction.response.defer()
    res = await fetch_json(f"{WAZELY_API}/check?data={data}")
    await send_result(interaction, res)


@zenix_group.command(name="dctoken", description="Discord bot token testi")
@app_commands.describe(token="Bot token")
async def z_dctoken(interaction: discord.Interaction, token: str):
    await interaction.response.defer(ephemeral=True)
    res = await fetch_json(f"{WAZELY_API}/dcbottokencheck?token={token}")
    await send_result(interaction, res)


@zenix_group.command(name="tgtoken", description="Telegram bot token testi")
@app_commands.describe(token="Bot token")
async def z_tgtoken(interaction: discord.Interaction, token: str):
    await interaction.response.defer(ephemeral=True)
    res = await fetch_json(f"{WAZELY_API}/tgtokencheck?token={token}")
    await send_result(interaction, res)


@zenix_group.command(name="trlog", description="Türkiye log sorgusu")
@app_commands.describe(site="Site adı")
async def z_trlog(interaction: discord.Interaction, site: str):
    await interaction.response.defer()
    data = await fetch_json(f"{WAZELY}/trlog?site={site}")
    await send_result(interaction, data)


@zenix_group.command(name="log", description="Site log sorgusu")
@app_commands.describe(url="Domain")
async def z_log(interaction: discord.Interaction, url: str):
    await interaction.response.defer()
    data = await fetch_json(f"{SOLIDARK}/log.php?url={url}")
    await send_result(interaction, data)


@zenix_group.command(name="eczane", description="Eczane sorgusu")
@app_commands.describe(ad="Eczane adı")
async def z_eczane(interaction: discord.Interaction, ad: str):
    await interaction.response.defer()
    data = await fetch_json(f"{WAZELY}/eczane?ad={ad}")
    await send_result(interaction, data)


@zenix_group.command(name="ipinfo", description="IP adresi bilgisi")
@app_commands.describe(ip="IP adresi")
async def z_ipinfo(interaction: discord.Interaction, ip: str):
    await interaction.response.defer()
    data = await fetch_json(f"{WAZELY}/ipinfo?ip={ip}")
    await send_result(interaction, data)


@zenix_group.command(name="dns", description="Domain DNS kayıtları")
@app_commands.describe(domain="Domain")
async def z_dns(interaction: discord.Interaction, domain: str):
    await interaction.response.defer()
    data = await fetch_json(f"{WAZELY}/dns?domain={domain}")
    await send_result(interaction, data)


@zenix_group.command(name="bahis", description="Bahis kaydı sorgusu")
@app_commands.describe(isimsoyisim="İsim Soyisim")
async def z_bahis(interaction: discord.Interaction, isimsoyisim: str):
    await interaction.response.defer()
    data = await fetch_json(f"{WAZELY}/bahis?isimsoyisim={isimsoyisim}")
    await send_result(interaction, data)


@zenix_group.command(name="exxengen", description="Exxen hesap oluşturucu")
async def z_exxengen(interaction: discord.Interaction):
    await interaction.response.defer()
    data = await fetch_json(f"{WAZELY}/exxengen")
    await send_result(interaction, data)


@zenix_group.command(name="nitrogen", description="Rastgele Nitro kodları")
@app_commands.describe(count="Adet (varsayılan: 10)")
async def z_nitro(interaction: discord.Interaction, count: Optional[int] = 10):
    await interaction.response.defer()
    data = await fetch_json(f"{WAZELY}/fakeNitro?count={count}")
    await send_result(interaction, data)


@zenix_group.command(name="pingtest", description="Ping testi")
@app_commands.describe(target="Hedef")
async def z_pingtest(interaction: discord.Interaction, target: str):
    await interaction.response.defer()
    data = await fetch_json(f"{WAZELY}/ping?target={target}")
    await send_result(interaction, data)


@zenix_group.command(name="plaka", description="Plaka sorgusu")
@app_commands.describe(plate="Plaka")
async def z_plaka(interaction: discord.Interaction, plate: str):
    await interaction.response.defer()
    data = await fetch_json(f"{WAZELY}/plaka?plate={plate}")
    await send_result(interaction, data)


@zenix_group.command(name="predunyam", description="Predunyam hesap oluşturucu")
async def z_predunyam(interaction: discord.Interaction):
    await interaction.response.defer()
    data = await fetch_json(f"{WAZELY}/predunyam")
    await send_result(interaction, data)


@zenix_group.command(name="useragent", description="Rastgele User-Agent")
async def z_useragent(interaction: discord.Interaction):
    await interaction.response.defer()
    data = await fetch_json(f"{WAZELY}/randomuseragent")
    await send_result(interaction, data)


# ==================== /zenix2 — TC/KİMLİK ====================
@zenix2_group.command(name="tc", description="TC kimlik sorgusu")
@app_commands.describe(tc="TC")
async def z2_tc(interaction: discord.Interaction, tc: str):
    await interaction.response.defer()
    data = await fetch_json(f"{SOLIDARK}/tc.php?tc={tc}")
    if clean_data(data) is None:
        data = await fetch_json(f"{SEARCHULP}/tc/{tc}?key={SEARCH_KEY}")
    await send_result(interaction, data)


@zenix2_group.command(name="tcpro", description="TC Pro detaylı sorgu")
@app_commands.describe(tc="TC")
async def z2_tcpro(interaction: discord.Interaction, tc: str):
    await interaction.response.defer()
    data = await fetch_json(f"{SOLIDARK}/tcpro.php?tc={tc}")
    if clean_data(data) is None:
        data = await fetch_json(f"{SEARCHULP}/tc/{tc}?key={SEARCH_KEY}")
    await send_result(interaction, data)


@zenix2_group.command(name="aile", description="Aile sorgusu")
@app_commands.describe(tc="TC")
async def z2_aile(interaction: discord.Interaction, tc: str):
    await interaction.response.defer()
    data = await fetch_json(f"{SEARCHULP}/aile/{tc}?key={SEARCH_KEY}")
    await send_result(interaction, data)


@zenix2_group.command(name="ailepro", description="Aile Pro sorgusu")
@app_commands.describe(tc="TC")
async def z2_ailepro(interaction: discord.Interaction, tc: str):
    await interaction.response.defer()
    data = await fetch_json(f"{SOLIDARK}/ailepro.php?tc={tc}")
    await send_result(interaction, data)


@zenix2_group.command(name="sulale", description="Sülale sorgusu")
@app_commands.describe(tc="TC")
async def z2_sulale(interaction: discord.Interaction, tc: str):
    await interaction.response.defer()
    data = await fetch_json(f"{SEARCHULP}/sulale/{tc}?key={SEARCH_KEY}")
    await send_result(interaction, data)


@zenix2_group.command(name="cocuk", description="Çocuk sorgusu")
@app_commands.describe(tc="TC")
async def z2_cocuk(interaction: discord.Interaction, tc: str):
    await interaction.response.defer()
    data = await fetch_json(f"{SEARCHULP}/cocuk/{tc}?key={SEARCH_KEY}")
    await send_result(interaction, data)


@zenix2_group.command(name="adres", description="Adres sorgusu")
@app_commands.describe(tc="TC")
async def z2_adres(interaction: discord.Interaction, tc: str):
    await interaction.response.defer()
    data = await fetch_json(f"{SEARCHULP}/adres/{tc}?key={SEARCH_KEY}")
    await send_result(interaction, data)


@zenix2_group.command(name="gsmtc", description="GSM → TC sorgusu")
@app_commands.describe(gsm="GSM")
async def z2_gsmtc(interaction: discord.Interaction, gsm: str):
    await interaction.response.defer()
    data = await fetch_json(f"{SEARCHULP}/gsmtc/{gsm}?key={SEARCH_KEY}")
    await send_result(interaction, data)


@zenix2_group.command(name="tcgsm", description="TC → GSM sorgusu")
@app_commands.describe(tc="TC")
async def z2_tcgsm(interaction: discord.Interaction, tc: str):
    await interaction.response.defer()
    data = await fetch_json(f"{SEARCHULP}/tcgsm/{tc}?key={SEARCH_KEY}")
    await send_result(interaction, data)


@zenix2_group.command(name="isyeri", description="İşyeri sorgusu")
@app_commands.describe(tc="TC")
async def z2_isyeri(interaction: discord.Interaction, tc: str):
    await interaction.response.defer()
    data = await fetch_json(f"{SEARCHULP}/isyeri/{tc}?key={SEARCH_KEY}")
    await send_result(interaction, data)


@zenix2_group.command(name="vesika", description="Vesika sorgusu")
@app_commands.describe(tc="TC")
async def z2_vesika(interaction: discord.Interaction, tc: str):
    await interaction.response.defer()
    data = await fetch_json(f"{SOLIDARK}/vesika.php?tc={tc}")
    await send_result(interaction, data)


@zenix2_group.command(name="sgk", description="SGK sorgusu")
@app_commands.describe(tc="TC")
async def z2_sgk(interaction: discord.Interaction, tc: str):
    await interaction.response.defer()
    data = await fetch_json(f"{SOLIDARK}/sgk.php?tc={tc}")
    await send_result(interaction, data)


@zenix2_group.command(name="idsorgu", description="ID ile e-posta/log sorgusu")
@app_commands.describe(id="ID (örn: 92433932011724800)")
async def z2_idsorgu(interaction: discord.Interaction, id: str):
    await interaction.response.defer()
    data = await fetch_json(f"{ID_API}?id={id}")
    await send_result(interaction, data)


# ==================== /zenix3 — AD/SOYAD ====================
@zenix3_group.command(name="adsoyad", description="Ad soyad arama")
@app_commands.describe(
    ad="Ad",
    soyad="Soyad",
    il="İl",
    ilce="İlçe",
    dogumtarihi="Doğum tarihi"
)
async def z3_adsoyad(
    interaction: discord.Interaction,
    ad: str,
    soyad: Optional[str] = None,
    il: Optional[str] = None,
    ilce: Optional[str] = None,
    dogumtarihi: Optional[str] = None
):
    await interaction.response.defer()
    params = {"ad": ad, "key": SEARCH_KEY}
    if soyad:        params["soyad"] = soyad
    if il:           params["il"] = il
    if ilce:         params["ilce"] = ilce
    if dogumtarihi:  params["dogumtarihi"] = dogumtarihi
    url = f"{SEARCHULP}/adsoyad?{urlencode(params)}"
    data = await fetch_json(url)
    await send_result(interaction, data)


@zenix3_group.command(name="adsoyadil", description="Ad soyad il ilçe sorgusu")
@app_commands.describe(ad="Ad", soyad="Soyad", il="İl", ilce="İlçe")
async def z3_adsoyadil(interaction: discord.Interaction, ad: str, soyad: str, il: str, ilce: str):
    await interaction.response.defer()
    data = await fetch_json(f"{SOLIDARK}/adsoyad.php?ad={ad}&soyad={soyad}&il={il}&ilce={ilce}")
    await send_result(interaction, data)


@zenix3_group.command(name="adililce", description="Ad il ilçe sorgusu")
@app_commands.describe(ad="Ad", il="İl", ilce="İlçe")
async def z3_adililce(interaction: discord.Interaction, ad: str, il: str, ilce: str):
    await interaction.response.defer()
    data = await fetch_json(f"{SOLIDARK}/adililce.php?ad={ad}&il={il}&ilce={ilce}")
    await send_result(interaction, data)


# ==================== GENEL ====================
@bot.tree.command(name="ping", description="Bot gecikmesi")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"```\n{round(bot.latency * 1000)}ms\n```")


@bot.tree.command(name="yardim", description="ZENIX komutları")
async def yardim(interaction: discord.Interaction):
    g1 = [c.name for c in zenix_group.commands]
    g2 = [c.name for c in zenix2_group.commands]
    g3 = [c.name for c in zenix3_group.commands]

    embed = discord.Embed(
        title="✨  ZENIX CHECKER  ✨",
        description=(
            "🔎  Tüm sorgulama komutları aşağıda listelenmiştir.\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━"
        ),
        color=COLOR_Z,
        timestamp=datetime.datetime.utcnow()
    )
    embed.add_field(
        name="⚡ `/zenix` — Genel",
        value="`" + "` `".join(sorted(g1)) + "`",
        inline=False
    )
    embed.add_field(
        name="🪪 `/zenix2` — TC & Kimlik",
        value="`" + "` `".join(sorted(g2)) + "`",
        inline=False
    )
    embed.add_field(
        name="👤 `/zenix3` — Ad/Soyad",
        value="`" + "` `".join(sorted(g3)) + "`",
        inline=False
    )
    embed.set_thumbnail(url=LOGO_URL)
    embed.set_image(url=LOGO_URL)
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="hosgeldin", description="ZENIX Checker hoş geldin mesajını gösterir")
async def hosgeldin(interaction: discord.Interaction):
    await interaction.response.send_message(embed=build_welcome_embed())


# ==================== KAYIT ====================
bot.tree.add_command(zenix_group)
bot.tree.add_command(zenix2_group)
bot.tree.add_command(zenix3_group)


# ==================== ÇALIŞTIR ====================
if __name__ == "__main__":
    if not DISCORD_TOKEN:
        print("❌ DISCORD_TOKEN bulunamadı!")
        exit(1)
    print("🚀 ZENIX başlatılıyor...")
    bot.run(DISCORD_TOKEN)
