import ssl
import asyncio
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import aiohttp
import MajorLoginReq_pb2
import MajorLoginRes_pb2
import GetLoginDataRes_pb2
import DecodeWhisperMsg_pb2
import GenWhisperMsg_pb2
from datetime import datetime
import recieved_chat_pb2
import Team_msg_pb2
import spam_join_pb2
import json
from protobuf_decoder.protobuf_decoder import Parser
import bot_mode_pb2
import bot_invite_pb2
import base64
from flask import Flask
import random_pb2
from threading import Thread
import Clan_Startup_pb2
import Team_msg_pb2
import clan_msg_pb2
import recieved_chat_pb2
import Team_Chat_Startup_pb2
import wlxd_spam_pb2
import random
import pytz
import time
import re
import telebot
from telebot import types
import asyncio

# Initialize Telegram bot
bot = telebot.TeleBot("8341069129:AAFzsl1Tk2lfEC6GHPdlnobWnn7TXbKo19c")

app = Flask(__name__)

# <--- FIX: Make writers globally accessible --->
online_writer = None
whisper_writer = None
spam_room = False
spammer_uid = None
spam_chat_id = None
spam_uid = None
# <------------------------------------------>

headers = {
    'User-Agent': "Dalvik/2.1.0 (Linux; U; Android 11; ASUS_Z01QD Build/PI)",
    'Connection': "Keep-Alive",
    'Accept-Encoding': "gzip",
    'Content-Type': "application/x-www-form-urlencoded",
    'Expect': "100-continue",
    'X-Unity-Version': "2018.4.11f1",
    'X-GA': "v1 1",
    'ReleaseVersion': "OB51"
}

TOKEN_EXPIRY = 7 * 60 * 60

# --- Helper function for random colors ---
def get_random_color():
    colors = [
        "[FF0000]", "[00FF00]", "[0000FF]", "[FFFF00]", "[FF00FF]", "[00FFFF]", "[FFFFFF]", "[FFA500]",
        "[A52A2A]", "[800080]", "[000000]", "[808080]", "[C0C0C0]", "[FFC0CB]", "[FFD700]", "[ADD8E6]",
        "[90EE90]", "[D2691E]", "[DC143C]", "[00CED1]", "[9400D3]", "[F08080]", "[20B2AA]", "[FF1493]",
        "[7CFC00]", "[B22222]", "[FF4500]", "[DAA520]", "[00BFFF]", "[00FF7F]", "[4682B4]", "[6495ED]",
        "[5F9EA0]", "[DDA0DD]", "[E6E6FA]", "[B0C4DE]", "[556B2F]", "[8FBC8F]", "[2E8B57]", "[3CB371]",
        "[6B8E23]", "[808000]", "[B8860B]", "[CD5C5C]", "[8B0000]", "[FF6347]", "[FF8C00]", "[BDB76B]",
        "[9932CC]", "[8A2BE2]", "[4B0082]", "[6A5ACD]", "[7B68EE]", "[4169E1]", "[1E90FF]", "[191970]",
        "[00008B]", "[000080]", "[008080]", "[008B8B]", "[B0E0E6]", "[AFEEEE]", "[E0FFFF]", "[F5F5DC]",
        "[FAEBD7]"
    ]
    return random.choice(colors)

# <--- FIX: The avatar IDs were strings but needed to be integers for the protobuf messages. --->
def get_random_avatar():
    avatars = [
        902050001, 902000060, 902000061, 902000065, 902000073, 902000074, 902000075, 902000076, 902000082, 902000083, 902000084, 902000087, 902000090, 902000091, 902000112, 902000104, 902000190, 902000191, 902000207, 902048021, 902047018, 902042011
    ]
    return random.choice(avatars)
# <-------------------------------------------------------------------------------------------->

async def encrypted_proto(encoded_hex):
    key = b'Yg&tc%DEuh6%Zc^8'
    iv = b'6oyZDr22E3ychjM%'
    cipher = AES.new(key, AES.MODE_CBC, iv)
    padded_message = pad(encoded_hex, AES.block_size)
    encrypted_payload = cipher.encrypt(padded_message)
    return encrypted_payload

async def get_random_user_agent():
    versions = [
        '4.0.18P6', '4.0.19P7', '4.0.20P1', '4.1.0P3', '4.1.5P2', '4.2.1P8',
        '4.2.3P1', '5.0.1B2', '5.0.2P4', '5.1.0P1', '5.2.0B1', '5.2.5P3',
        '5.3.0B1', '5.3.2P2', '5.4.0P1', '5.4.3B2', '5.5.0P1', '5.5.2P3'
    ]
    models = [
        'SM-A125F', 'SM-A225F', 'SM-A325M', 'SM-A515F', 'SM-A725F', 'SM-M215F', 'SM-M325FV',
        'Redmi 9A', 'Redmi 9C', 'POCO M3', 'POCO M4 Pro', 'RMX2185', 'RMX3085',
        'moto g(9) play', 'CPH2239', 'V2027', 'OnePlus Nord', 'ASUS_Z01QD',
    ]
    android_versions = ['9', '10', '11', '12', '13', '14']
    languages = ['en-US', 'es-MX', 'pt-BR', 'id-ID', 'ru-RU', 'hi-IN']
    countries = ['USA', 'MEX', 'BRA', 'IDN', 'RUS', 'IND']
    version = random.choice(versions)
    model = random.choice(models)
    android = random.choice(android_versions)
    lang = random.choice(languages)
    country = random.choice(countries)
    return f"GarenaMSDK/{version}({model};Android {android};{lang};{country};)"

async def get_access_token(uid, password):
    url = "https://100067.connect.garena.com/oauth/guest/token/grant"
    headers = {
        "Host": "100067.connect.garena.com",
        "User-Agent": (await get_random_user_agent()),
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "close"
    }
    data = {
        "uid": 4584323899,
        "password": F318FFB942A4F64DDA1136FC9D83BA5369429233A5E2B1CB219BC829EC63D4DE,
        "response_type": "token",
        "client_type": "2",
        "client_secret": "2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3",
        "client_id": "100067"
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, data=data) as response:
            if response.status != 200:
                return "Failed to get access token"
            data = await response.json()
            open_id = data.get("open_id")
            access_token = data.get("access_token")
            return (open_id, access_token) if open_id and access_token else (None, None)

async def MajorLoginProto_Encode(open_id, access_token):
    major_login = MajorLoginReq_pb2.MajorLogin()
    major_login.event_time = "2025-06-04 19:48:07"
    major_login.game_name = "free fire"
    major_login.platform_id = 1
    major_login.client_version = "1.118.1"
    major_login.system_software = "Android OS 9 / API-28 (PQ3B.190801.10101846/G9650ZHU2ARC6)"
    major_login.system_hardware = "Handheld"
    major_login.telecom_operator = "Verizon"
    major_login.network_type = "WIFI"
    major_login.screen_width = 1920
    major_login.screen_height = 1080
    major_login.screen_dpi = "280"
    major_login.processor_details = "ARM64 FP ASIMD AES VMH | 2865 | 4"
    major_login.memory = 3003
    major_login.gpu_renderer = "Adreno (TM) 640"
    major_login.gpu_version = "OpenGL ES 3.1 v1.46"
    major_login.unique_device_id = "Google|34a7dcdf-a7d5-4cb6-8d7e-3b0e448a0c57"
    major_login.client_ip = "223.191.51.89"
    major_login.language = "en"
    major_login.open_id = open_id
    major_login.open_id_type = "4"
    major_login.device_type = "Handheld"
    memory_available = major_login.memory_available
    memory_available.version = 55
    memory_available.hidden_value = 81
    major_login.access_token = access_token
    major_login.platform_sdk_id = 1
    major_login.network_operator_a = "Verizon"
    major_login.network_type_a = "WIFI"
    major_login.client_using_version = "7428b253defc164018c604a1ebbfebdf"
    major_login.external_storage_total = 36235
    major_login.external_storage_available = 31335
    major_login.internal_storage_total = 2519
    major_login.internal_storage_available = 703
    major_login.game_disk_storage_available = 25010
    major_login.game_disk_storage_total = 26628
    major_login.external_sdcard_avail_storage = 32992
    major_login.external_sdcard_total_storage = 36235
    major_login.login_by = 3
    major_login.library_path = "/data/app/com.dts.freefireth-YPKM8jHEwAJlhpmhDhv5MQ==/lib/arm64"
    major_login.reg_avatar = 1
    major_login.library_token = "5b892aaabd688e571f688053118a162b|/data/app/com.dts.freefireth-YPKM8jHEwAJlhpmhDhv5MQ==/base.apk"
    major_login.channel_type = 3
    major_login.cpu_type = 2
    major_login.cpu_architecture = "64"
    major_login.client_version_code = "2029123000"
    major_login.graphics_api = "OpenGLES2"
    major_login.supported_astc_bitset = 16383
    major_login.login_open_id_type = 4
    major_login.analytics_detail = b"FwQVTgUPX1UaUllDDwcWCRBpWAUOUgsvA1snWlBaO1kFYg=="
    major_login.loading_time = 13564
    major_login.release_channel = "android"
    major_login.extra_info = "KqsHTymw5/5GB23YGniUYN2/q47GATrq7eFeRatf0NkwLKEMQ0PK5BKEk72dPflAxUlEBir6Vtey83XqF593qsl8hwY="
    major_login.android_engine_init_flag = 110009
    major_login.if_push = 1
    major_login.is_vpn = 1
    major_login.origin_platform_type = "4"
    major_login.primary_platform_type = "4"
    string = major_login.SerializeToString()
    return  await encrypted_proto(string)

async def MajorLogin(payload):
    url = "https://loginbp.common.ggbluefox.com/MajorLogin"
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=payload, headers=headers, ssl=ssl_context) as response:
            if response.status == 200:
                return await response.read()
            return None

async def GetLoginData(base_url, payload, token):
    url = f"{base_url}/GetLoginData"
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    headers['Authorization']= f"Bearer {token}"
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=payload, headers=headers, ssl=ssl_context) as response:
            if response.status == 200:
                return await response.read()
            return None

API_KEYS = [
    "AIzaSyA8IiZS4SgA1DocEG1GA318a4baKvEWYBc",
    "AIzaSyCCr2sq-s1bWEwuK0ZIv8ITkqccxzMMCDI",
    "AIzaSyCLF8o66saIX9lKRzWt8RW9HjFZ1N8W6H0",
    "AIzaSyCM7zVQ9FM_BKI15O6Hgc6NN5F3RK3Xa0o",
    "AIzaSyCkiYnzLsWomUiRo4v6zWMx3X3yuoObRRM"
]

chat_history = [
    {
        "role": "user",
        "parts": [{"text": "You are a helpful assistant."}]
    }
]

key_index = 0

async def Get_AI_Response(user_input):
    global key_index

    # Append user message with extra instruction
    chat_history.append({
        "role": "user",
        "parts": [
            {"text": user_input},
            {"text": "Remove markdown and HTML from the output"}
        ]
    })

    headers = {"Content-Type": "application/json"}

    for _ in range(len(API_KEYS)):
        api_key = API_KEYS[key_index]
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        payload = {"contents": chat_history}

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as response:
                result = await response.json()

                if "candidates" in result:
                    reply = result["candidates"][0]["content"]["parts"][0]["text"]
                    chat_history.append({
                        "role": "model",
                        "parts": [{"text": reply}]
                    })
                    return reply
                elif result.get("error", {}).get("code") == 429:
                    key_index = (key_index + 1) % len(API_KEYS)
                    print("⚠️ Switching API key due to rate limit.")
                    await asyncio.sleep(1)
                else:
                    return "Failed to get response: " + str(result)

    return "All keys reached rate limit."

async def MajorLogin_Decode(MajorLoginResponse):
    proto = MajorLoginRes_pb2.MajorLoginRes()
    proto.ParseFromString(MajorLoginResponse)
    return proto

async def GetLoginData_Decode(GetLoginDataResponse):
    proto = GetLoginDataRes_pb2.GetLoginData()
    proto.ParseFromString(GetLoginDataResponse)
    return proto

async def decode_team_packet(hex_packet):
    packet = bytes.fromhex(hex_packet)
    proto = recieved_chat_pb2.recieved_chat()
    proto.ParseFromString(packet)
    return proto

async def DecodeWhisperMessage(hex_packet):
    try:
        packet = bytes.fromhex(hex_packet)
        proto = DecodeWhisperMsg_pb2.DecodeWhisper()
        proto.ParseFromString(packet)
        return proto
    except Exception as e:
        print(f"[DecodeWhisperMessage Error] {e}")
        return None

async def base_to_hex(timestamp):
    timestamp_result = hex(timestamp)
    result = str(timestamp_result)[2:]
    if len(result) == 1:
        result = "0" + result
    return result

async def parse_results(parsed_results):
    result_dict = {}
    for result in parsed_results:
        field_data = {}
        field_data["wire_type"] = result.wire_type
        if result.wire_type == "varint":
            field_data["data"] = result.data
        if result.wire_type == "string":
            field_data["data"] = result.data
        if result.wire_type == "bytes":
            field_data["data"] = result.data
        elif result.wire_type == "length_delimited":
            field_data["data"] = await parse_results(result.data.results)
        result_dict[result.field] = field_data
    return result_dict

async def split_text_by_words(text, max_length=200):
    def insert_c_in_number(word):
        if word.isdigit():
            mid = len(word) // 2
            return word[:mid] + "[C]" + word[mid:]
        return word

    words = text.split()
    words = [insert_c_in_number(word) for word in words]

    chunks = []
    current = ""

    for word in words:
        if len(current) + len(word) + (1 if current else 0) <= max_length:
            current += (" " if current else "") + word
        else:
            chunks.append(current)
            current = word

    if current:
        chunks.append(current)

    return chunks

async def get_available_room(input_text):
    try:
        parsed_results = Parser().parse(input_text)
        parsed_results_objects = parsed_results
        parsed_results_dict = await parse_results(parsed_results_objects)
        json_data = json.dumps(parsed_results_dict)
        return json_data
    except Exception as e:
        print(f"error {e}")
        return None

async def team_chat_startup(player_uid, team_session, key, iv):
    proto = Team_Chat_Startup_pb2.team_chat_startup()
    proto.field1 = 3
    proto.details.uid = player_uid
    proto.details.language = "en"
    proto.details.team_packet = team_session

    packet = proto.SerializeToString().hex()
    encrypted_packet = await encrypt_packet(packet, key, iv)
    packet_length = len(encrypted_packet) // 2
    packet_length_hex = await base_to_hex(packet_length)

    if len(packet_length_hex) == 2:
        final_packet = "1201000000" + packet_length_hex + encrypted_packet
    elif len(packet_length_hex) == 3:
        final_packet = "120100000" + packet_length_hex + encrypted_packet
    elif len(packet_length_hex) == 4:
        final_packet = "12010000" + packet_length_hex + encrypted_packet
    elif len(packet_length_hex) == 5:
        final_packet = "1201000" + packet_length_hex + encrypted_packet
    else:
        print("something went wrong, please check clan startup function.")
    if whisper_writer: # <--- FIX: Check if writer is available
        whisper_writer.write(bytes.fromhex(final_packet))
        await whisper_writer.drain()

async def encrypt_packet(packet, key, iv):
    bytes_packet = bytes.fromhex(packet)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    cipher_text = cipher.encrypt(pad(bytes_packet, AES.block_size))
    return cipher_text.hex()

async def create_clan_startup(clan_id, clan_compiled_data, key, iv):
    proto = Clan_Startup_pb2.ClanPacket()
    proto.Clan_Pos = 3
    proto.Data.Clan_ID = int(clan_id)
    proto.Data.Clan_Type = 1
    proto.Data.Clan_Compiled_Data = clan_compiled_data
    packet = proto.SerializeToString().hex()
    encrypted_packet = await encrypt_packet(packet, key, iv)
    packet_length = len(encrypted_packet) // 2
    packet_length_hex = await base_to_hex(packet_length)
    if len(packet_length_hex) == 2:
        final_packet = "1201000000" + packet_length_hex + encrypted_packet
    elif len(packet_length_hex) == 3:
        final_packet = "120100000" + packet_length_hex + encrypted_packet
    elif len(packet_length_hex) == 4:
        final_packet = "12010000" + packet_length_hex + encrypted_packet
    elif len(packet_length_hex) == 5:
        final_packet = "1201000" + packet_length_hex + encrypted_packet
    else:
        print("something went wrong, please check clan startup function.")
    if whisper_writer: # <--- FIX: Check if writer is available
        whisper_writer.write(bytes.fromhex(final_packet))
        await whisper_writer.drain()

async def create_group(key, iv):
    packet = "080112bc04120101180120032a02656e420d0a044944433110661a03494e444801520601090a121920580168017288040a403038303230303032433733464233454430323031303030303030303030303030303030303030303030303030303030303137424236333544303930303030303010151a8f0375505d5413070448565556000b5009070405500303560a08030354550007550f02570d03550906521702064e76544145491e0418021e11020b4d1a42667e58544776725757486575441f5a584a065b46426a5a65650e14034f7e5254047e005a7b7c555c0d5562637975670a7f765b0102537906091702044e72747947457d0d6267456859587b596073435b7205046048447d080b170c4f584a6b007e4709740661625c545b0e7458405f5e4e427f486652420c13070c484b597a717a5a5065785d4343535d7c7a6450675a787e05736418010c12034a475b71717a566360437170675a6b1c740748796065425e017e4f5d0e1a034d09660358571843475c774b5f524d47670459005a4870780e795e7a0a110a457e5e5a00776157597069094266014f716d7246754a60506b747404091005024f7e765774035967464d687c724703075d4e76616f7a184a7f057a6f0917064b5f797d05434250031b0555717b0d00611f59027e60077b4a0a5c7c0d1500480143420b5a65746803636e41556a511269087e4f5f7f675c0440600c22047c5c5754300b3a1a16024a424202050607021316677178637469785d51745a565a5a4208312e3130392e3136480650029801c902aa01024f52"
    encrypted_packet = await encrypt_packet(packet, key, iv)
    packet_length = len(encrypted_packet) // 2
    packet_length_hex = await base_to_hex(packet_length)
    if len(packet_length_hex) == 2:
        final_packet = "0514000000" + packet_length_hex + encrypted_packet
    elif len(packet_length_hex) == 3:
        final_packet = "051400000" + packet_length_hex + encrypted_packet
    elif len(packet_length_hex) == 4:
        final_packet = "05140000" + packet_length_hex + encrypted_packet
    elif len(packet_length_hex) == 5:
        final_packet = "05140000" + packet_length_hex + encrypted_packet
    else:
        print("something went wrong, please check create_group function.")
    if online_writer: # <--- FIX: Check if writer is available
        online_writer.write(bytes.fromhex(final_packet))
        await online_writer.drain()
        
async def wlxd_skwad(uid, key, iv):
    packet = wlxd_spam_pb2.invite_uid()
    #packet.field1 = 33

    #details = packet.field2
    details.user_id = int(uid)
    details.country_code = "IND"
    details.status1 = 1
    details.status2 = 1
    details.numbers = bytes([16, 21, 8, 10, 11, 19, 12, 15, 17, 4, 7, 2, 3, 13, 14, 18, 1, 5, 6])
    details.empty1 = ""
    details.rank = 330
    details.field8 = 6000
    details.field9 = 100
    details.region_code = "IND"
    details.uuid = bytes([
                55, 52, 50, 56, 98, 50, 53, 51, 100, 101, 102, 99,
                49, 54, 52, 48, 49, 56, 99, 54, 48, 52, 97, 49,
                101, 98, 98, 102, 101, 98, 100, 102
            ])
    details.field12 = 1
    details.repeated_uid = int(uid)
    details.field16 = 1
    details.field18 = 228
    details.field19 = 22

    nested = details.field20
    nested.server = "IDC1"
    nested.ping = 3000
    nested.country = "IND"

    details.field23 = bytes([16, 1, 24, 1])
    details.avatar = int(get_random_avatar())

    # field26 and field28 are empty messages
    details.field26.SetInParent()
    details.field28.SetInParent()

    # Serialize, encrypt, and send the packet
    serialized = packet.SerializeToString().hex()
    encrypted_packet = await encrypt_packet(serialized, key, iv)

    packet_length = len(encrypted_packet) // 2
    packet_length_hex = await base_to_hex(packet_length)

    if len(packet_length_hex) == 2:
        final_packet = "0514000000" + packet_length_hex + encrypted_packet
    elif len(packet_length_hex) == 3:
        final_packet = "051400000" + packet_length_hex + encrypted_packet
    elif len(packet_length_hex) == 4:
        final_packet = "05140000" + packet_length_hex + encrypted_packet
    elif len(packet_length_hex) == 5:
        final_packet = "05140000" + packet_length_hex + encrypted_packet
    else:
        print("❌ Packet length formatting failed.")
        return

    online_writer.write(bytes.fromhex(final_packet))
    await online_writer.drain()

async def modify_team_player(team, key, iv):
    bot_mode = bot_mode_pb2.BotMode()
    bot_mode.key1 = 17
    bot_mode.key2.uid = 7669969208
    bot_mode.key2.key2 = 1
    bot_mode.key2.key3 = int(team)
    bot_mode.key2.key4 = 62
    bot_mode.key2.byte = base64.b64decode("Gg==")
    bot_mode.key2.key8 = 5
    bot_mode.key2.key13 = 227
    packet = bot_mode.SerializeToString().hex()
    encrypted_packet = await encrypt_packet(packet, key, iv)
    packet_length = len(encrypted_packet) // 2
    packet_length_hex = await base_to_hex(packet_length)
    if len(packet_length_hex) == 2:
        final_packet = "0514000000" + packet_length_hex + encrypted_packet
    elif len(packet_length_hex) == 3:
        final_packet = "051400000" + packet_length_hex + encrypted_packet
    elif len(packet_length_hex) == 4:
        final_packet = "05140000" + packet_length_hex + encrypted_packet
    elif len(packet_length_hex) == 5:
        final_packet = "05140000" + packet_length_hex + encrypted_packet
    else:
        print("something went wrong, please check create_group function.")
    if online_writer: # <--- FIX: Check if writer is available
        online_writer.write(bytes.fromhex(final_packet))
        await online_writer.drain()

async def invite_target(uid, key, iv):
    invite = bot_invite_pb2.invite_uid()
    invite.num = 2
    invite.Func.uid = int(uid)
    invite.Func.region = "IND"
    invite.Func.number = 1
    packet = invite.SerializeToString().hex()
    encrypted_packet = await encrypt_packet(packet, key, iv)
    packet_length = len(encrypted_packet) // 2
    packet_length_hex = await base_to_hex(packet_length)
    if len(packet_length_hex) == 2:
        final_packet = "0514000000" + packet_length_hex + encrypted_packet
    elif len(packet_length_hex) == 3:
        final_packet = "051400000" + packet_length_hex + encrypted_packet
    elif len(packet_length_hex) == 4:
        final_packet = "05140000" + packet_length_hex + encrypted_packet
    elif len(packet_length_hex) == 5:
        final_packet = "05140000" + packet_length_hex + encrypted_packet
    else:
        print("something went wrong, please check create_group function.")
    if online_writer: # <--- FIX: Check if writer is available
        online_writer.write(bytes.fromhex(final_packet))
        await online_writer.drain()

async def left_group(key, iv):
    packet = "0807120608da89d98d27"
    encrypted_packet = await encrypt_packet(packet, key, iv)
    packet_length = len(encrypted_packet) // 2
    packet_length_hex = await base_to_hex(packet_length)
    if len(packet_length_hex) == 2:
        final_packet = "0514000000" + packet_length_hex + encrypted_packet
    elif len(packet_length_hex) == 3:
        final_packet = "051400000" + packet_length_hex + encrypted_packet
    elif len(packet_length_hex) == 4:
        final_packet = "05140000" + packet_length_hex + encrypted_packet
    elif len(packet_length_hex) == 5:
        final_packet = "05140000" + packet_length_hex + encrypted_packet
    else:
        print("something went wrong, please check create_group function.")
    if online_writer: # <--- FIX: Check if writer is available
        online_writer.write(bytes.fromhex(final_packet))
        await online_writer.drain()

async def join_room(uid, room_id, key, iv):
    root = spam_join_pb2.spam_join()
    root.field_1 = 78
    root.field_2.field_1 = int(room_id)
    root.field_2.name = "[C][B][FF0000]TEAM-[00FF00]DEV"
    root.field_2.field_3.field_2 = 1
    root.field_2.field_3.field_3 = 1
    root.field_2.field_4 = 330
    root.field_2.field_5 = 6000
    root.field_2.field_6 = 201
    root.field_2.field_10 = get_random_avatar()
    root.field_2.field_11 = int(uid)
    root.field_2.field_12 = 1
    packet = root.SerializeToString().hex()
    packet_encrypt = await encrypt_packet(packet, key, iv)
    base_len = await base_to_hex(int(len(packet_encrypt) // 2))
    if len(base_len) == 2:
        header = "0e15000000"
    elif len(base_len) == 3:
        header = "0e1500000"
    elif len(base_len) == 4:
        header = "0e150000"
    elif len(base_len) == 5:
        header = "0e15000"
    final_packet = header + base_len + packet_encrypt
    online_writer.write(bytes.fromhex(final_packet))
    await online_writer.drain()

async def send_clan_msg(msg, chat_id, key, iv):
    root = clan_msg_pb2.clan_msg()
    root.type = 1
    nested_object = root.data
    nested_object.uid = 9119828499
    nested_object.chat_id = chat_id
    nested_object.chat_type = 1
    nested_object.msg = msg
    nested_object.timestamp = int(datetime.now().timestamp())
    nested_object.language = "en"
    nested_object.empty_field.SetInParent()
    nested_details = nested_object.field9
    nested_details.Player_Name = "Ɗᴇᴠ-ʙᴏᴛ"
    nested_details.avatar_id = get_random_avatar()
    nested_details.banner_id = 901000173
    nested_details.rank = 330
    nested_details.badge = 102000015
    nested_details.Clan_Name = "BOTSㅤARMY"
    nested_details.field10 = 1
    nested_details.rank_point = 1
    nested_badge = nested_details.field13
    nested_badge.value = 2
    nested_prime = nested_details.field14
    nested_prime.prime_uid = 1158053040
    nested_prime.prime_level = 8
    nested_prime.prime_hex = "\u0010\u0015\b\n\u000b\u0015\f\u000f\u0011\u0004\u0007\u0002\u0003\r\u000e\u0012\u0001\u0005\u0006"
    nested_options = nested_object.field13
    nested_options.url = "https://graph.facebook.com/v9.0/147045590125499/picture?width=160&height=160"
    nested_options.url_type = 1
    nested_options.url_platform = 1
    packet = root.SerializeToString().hex()
    encrypted_packet = await encrypt_packet(packet, key, iv)
    packet_length = len(encrypted_packet) // 2
    hex_length = await base_to_hex(packet_length)
    if len(hex_length) == 2:
        final_packet = "1215000000" + hex_length + encrypted_packet
    elif len(hex_length) == 3:
        final_packet = "121500000" + hex_length + encrypted_packet
    elif len(hex_length) == 4:
        final_packet = "12150000" + hex_length + encrypted_packet
    elif len(hex_length) == 5:
        final_packet = "1215000" + hex_length + encrypted_packet
    return bytes.fromhex(final_packet)

# <--- CORRECTED FUNCTION as requested--->
async def join_teamcode(room_id, key, iv):
    room_id_hex = ''.join(format(ord(c), 'x') for c in room_id)
    packet = f"080412b305220601090a1219202a07{room_id_hex}300640014ae8040a80013038304639324231383633453135424630323031303130303030303030303034303031363030303130303131303030323944373931333236303930303030353934313732323931343030303030303030303030303030303030303030303030303030303030303030303030303030666630303030303030306639396130326538108f011abf0377505d571709004d0b060b070b5706045c53050f065004010902060c09065a530506010851070a081209064e075c5005020808530d0604090b05050d0901535d030204005407000c5653590511000b4d5e570e02627b6771616a5560614f5e437f7e5b7f580966575b04010514034d7d5e5b465078697446027a7707506c6a5852526771057f5260504f0d1209044e695f0161074e46565a5a6144530174067a43694b76077f4a5f1d6d05130944664456564351667454766b464b7074065a764065475f04664652010f1709084d0a4046477d4806661749485406430612795b724e7a567450565b010c1107445e5e72780708765b460c5e52024c5f7e5349497c056e5d6972457f0c1a034e60757840695275435f651d615e081e090e75457e7464027f5656750a1152565f545d5f1f435d44515e57575d444c595e56565e505b555340594c5708740b57705c5b5853670957656a03007c04754c627359407c5e04120b4861037b004f6b744001487d506949796e61406a7c44067d415b0f5c0f120c4d54024c6a6971445f767d4873076e5f48716f537f695a7365755d520514064d515403717b72034a027d736b6053607e7553687a61647d7a686c610d22047c5b5655300b3a0816647b776b721c144208312e3130382e3134480350025a0c0a044944433110731a0242445a0c0a044944433210661a0242445a0c0a044944433310241a0242446a02656e8201024f52"
    encrypted_packet = await encrypt_packet(packet, key, iv)
    packet_length = len(encrypted_packet) // 2
    packet_length_hex = await base_to_hex(packet_length)

    if len(packet_length_hex) == 2:
        final_packet = "0519000000" + packet_length_hex + encrypted_packet
    elif len(packet_length_hex) == 3:
        final_packet = "051900000" + packet_length_hex + encrypted_packet
    elif len(packet_length_hex) == 4:
        final_packet = "05190000" + packet_length_hex + encrypted_packet
    elif len(packet_length_hex) == 5:
        final_packet = "05190000" + packet_length_hex + encrypted_packet
    else:
        print("Damm Something went wrong, please check join teamcode function")
    if online_writer: # <--- FIX: Check if writer is available
        online_writer.write(bytes.fromhex(final_packet))
        await online_writer.drain()

async def send_team_msg(msg, chat_id, key, iv):
     root = Team_msg_pb2.clan_msg()
     root.type = 1
     nested_object = root.data
     nested_object.uid = 9119828499
     nested_object.chat_id = chat_id
     nested_object.msg = msg
     nested_object.timestamp = int(datetime.now().timestamp())
     nested_object.chat_type = 2
     nested_object.language = "en"
     nested_details = nested_object.field9
     nested_details.Player_Name = "Ɗᴇᴠ-ʙᴏᴛ"
     nested_details.avatar_id = get_random_avatar()
     nested_details.rank = 330
     #nested_details.badge = 102000015
     nested_details.Clan_Name = "BOTSㅤARMY"
     nested_details.field10 = 1
     #nested_details.global_rank_pos = 1
     #nested_details.badge_info.value = 2  # Example value
     #nested_details.prime_info.prime_uid = 1158053040
     #nested_details.prime_info.prime_level = 8
     #nested_details.prime_info.prime_hex = "\u0010\u0015\b\n\u000b\u0015\f\u000f\u0011\u0004\u0007\u0002\u0003\r\u000e\u0012\u0001\u0005\u0006"
     nested_options = nested_object.field13
     nested_options.url_type = 2
     nested_options.url_platform = 1
     nested_object.empty_field.SetInParent()
     packet = root.SerializeToString().hex()
     encrypted_packet = await encrypt_packet(packet, key, iv)
     packet_length = len(encrypted_packet) // 2
     hex_length = await base_to_hex(packet_length)
     packet_prefix = "121500" + "0" * (6 - len(hex_length))
     final_packet = packet_prefix + hex_length + encrypted_packet
     return bytes.fromhex(final_packet)

async def send_msg(msg, chat_id, key, iv):
     root = GenWhisperMsg_pb2.GenWhisper()
     root.type = 1
     nested_object = root.data
     nested_object.uid = 9119828499
     nested_object.chat_id = chat_id
     nested_object.chat_type = 2
     nested_object.msg = msg
     nested_object.timestamp = int(datetime.now().timestamp())
     nested_details = nested_object.field9
     nested_details.Nickname = "Ɗᴇᴠ-ʙᴏᴛ"
     nested_details.avatar_id = get_random_avatar()
     nested_details.banner_id = 901000173
     nested_details.rank = 330
     nested_details.badge = 102000015
     nested_details.Clan_Name = "BOTSㅤARMY"
     nested_details.field10 = 1
     nested_details.global_rank_pos = 1
     nested_badge = nested_details.field13
     nested_badge.value = 2  # Example value
     nested_prime = nested_details.field14
     nested_prime.prime_uid = 1158053040
     nested_prime.prime_level = 8
     nested_prime.prime_hex = "\u0010\u0015\b\n\u000b\u0015\f\u000f\u0011\u0004\u0007\u0002\u0003\r\u000e\u0012\u0001\u0005\u0006"
     nested_options = nested_object.field13
     nested_object.language = "en"
     nested_options = nested_object.field13
     nested_options.url = "https://graph.facebook.com/v9.0/147045590125499/picture?width=160&height=160"
     nested_options.url_type = 2
     nested_options.url_platform = 1
     root.data.Celebrity = 1919408565318037500
     root.data.empty_field.SetInParent()
     packet = root.SerializeToString().hex()
     encrypted_packet = await encrypt_packet(packet, key, iv)
     packet_length = len(encrypted_packet) // 2
     hex_length = await base_to_hex(packet_length)

     if len(hex_length) == 2:
         final_packet = "1215000000" + hex_length + encrypted_packet
     elif len(hex_length) == 3:
         final_packet = "121500000" + hex_length + encrypted_packet
     elif len(hex_length) == 4:
         final_packet = "12150000" + hex_length + encrypted_packet
     elif len(hex_length) == 5:
         final_packet = "1215000" + hex_length + encrypted_packet

     return bytes.fromhex(final_packet)

async def get_encrypted_startup(AccountUID, token, timestamp, key, iv):
    uid_hex = hex(AccountUID)[2:]
    uid_length = len(uid_hex)
    encrypted_timestamp = await base_to_hex(timestamp)
    encrypted_account_token = token.encode().hex()
    encrypted_packet = await encrypt_packet(encrypted_account_token, key, iv)
    encrypted_packet_length = hex(len(encrypted_packet) // 2)[2:]

    if uid_length == 7:
        headers = '000000000'
    elif uid_length == 8:
        headers = '00000000'
    elif uid_length == 9:
        headers = '0000000'
    elif uid_length == 10:
        headers = '000000'
    elif uid_length == 11:
        headers = '00000'
    else:
        print('Unexpected length, Please Try again')
        headers = '0000000' # Default fallback

    packet = f"0115{headers}{uid_hex}{encrypted_timestamp}00000{encrypted_packet_length}{encrypted_packet}"
    return packet

async def Encrypt(number):
    number = int(number)
    encoded_bytes = []

    while True:
        byte = number & 0x7F
        number >>= 7
        if number:
            byte |= 0x80

        encoded_bytes.append(byte)
        if not number:
            break
    return bytes(encoded_bytes).hex()

async def uid_status(uid, key, iv):
    uid_text = {await Encrypt(uid)}
    uid_hex = next(iter(uid_text))
    packet = f"080112e8010ae301afadaea327bfbd809829a8fe89db07eda4c5f818f8a485850eefb3a39e06{uid_hex}ecb79fd623e4b3c0f506c6bdc48007d4efbc7ce688be8709c99ef7bc02e0a8bcd607d6ebe8e406dcc9a6ae07bfdab0e90a8792c28d08b58486f528cfeff0c61b95fcee8b088f96da8903effce2b726b684fbe10abfe984db28bbfebca528febd8dba28ecb98cb00baeb08de90583f28a9317a5ced6ab01d3de8c71d3a1b1be01ede292e907e5ecd0b903b2cafeae04c098fae5048cfcc0cd18d798b5f401cd9cbb61e8dce3c00299b895de1184e9c9ee11c28ed0d803f8b7ffec02a482babd011001"

    encrypted_packet = await encrypt_packet(packet, key, iv)
    header_length = len(encrypted_packet) // 2

    header_length_hex = await base_to_hex(header_length)

    if len(header_length_hex) == 2:
        final_packet = "0f15000000" + header_length_hex + encrypted_packet
    elif len(header_length_hex) == 3:
        final_packet = "0f1500000" + header_length_hex + encrypted_packet
    elif len(header_length_hex) == 4:
        final_packet = "0f150000" + header_length_hex + encrypted_packet
    elif len(header_length_hex) == 5:
        final_packet = "0f150000" + header_length_hex + encrypted_packet
    else:
        raise ValueError("error 505")

    if online_writer: # <--- FIX: Check if writer is available
        online_writer.write(bytes.fromhex(final_packet))
        await online_writer.drain()

async def handle_tcp_online_connection(ip, port, key, iv, encrypted_startup, reconnect_delay=0):
    global online_writer, spam_room, whisper_writer, spammer_uid, spam_chat_id, spam_uid
    while True:
        try:
            reader, writer = await asyncio.open_connection(ip, int(port))
            online_writer = writer

            bytes_payload = bytes.fromhex(encrypted_startup)
            online_writer.write(bytes_payload)
            await online_writer.drain()

            while True:
                data = await reader.read(9999)
                if not data:
                    break
                if data.hex().startswith("0f00"):
                    if spam_room:
                        try:
                            json_result = await get_available_room(data.hex()[10:])
                            if json_result:
                                parsed_data = json.loads(json_result)
                                if "5" in parsed_data and "data" in parsed_data["5"] and \
                                   "1" in parsed_data["5"]["data"] and "data" in parsed_data["5"]["data"]["1"] and \
                                   "15" in parsed_data["5"]["data"]["1"]["data"] and "data" in parsed_data["5"]["data"]["1"]["data"]["15"]:

                                    room_id = parsed_data["5"]["data"]["1"]["data"]["15"]["data"]
                                    uid = parsed_data["5"]["data"]["1"]["data"]["1"]["data"]
                                    spam_room = False
                                    message = f"Spamming on\n\nRoom ID: {str(room_id)[:5]}[C]{str(room_id)[5:]}\nUID: {str(uid)[:5]}[C]{str(uid)[5:]}"
                                    if spam_chat_id == 1:
                                        msg_packet = await send_team_msg(message, spam_uid, key, iv)
                                    elif spam_chat_id == 2:
                                        msg_packet = await send_clan_msg(message, spam_uid, key, iv)
                                    else:
                                        msg_packet = await send_msg(message, spam_uid, key, iv)
                                    if whisper_writer:
                                        whisper_writer.write(msg_packet)
                                        await whisper_writer.drain()
                                    
                                    # Add 1-minute delay with 0.1 second intervals
                                    start_time = time.time()
                                    while time.time() - start_time < 300:  # 120 seconds = 1 minute
                                        await join_room(uid, room_id, key, iv)
                                        await asyncio.sleep(0.25)  # 0.01 second delay
                                    
                                else:
                                    message = "Player not in room"
                                    if spam_chat_id == 1:
                                        msg_packet = await send_team_msg(message, spam_uid, key, iv)
                                    elif spam_chat_id == 2:
                                        msg_packet = await send_clan_msg(message, spam_uid, key, iv)
                                    else:
                                        msg_packet = await send_msg(message, spam_uid, key, iv)
                                    if whisper_writer:
                                        whisper_writer.write(msg_packet)
                                        await whisper_writer.drain()
                                    spam_room = False
                        except Exception as e:
                            print(f"Error processing room data: {e}")
                            spam_room = False

                elif data.hex().startswith("0500000"):
                    try:
                        response = await decode_team_packet(data.hex()[10:])
                        if response.packet_type == 6:
                            await team_chat_startup(response.details.player_uid, response.details.team_session, key, iv)
                    except Exception as e:
                        pass

            online_writer.close()
            await online_writer.wait_closed()
            online_writer = None

        except Exception as e:
            print(f"Error with {ip}:{port} - {e}")
            online_writer = None

        await asyncio.sleep(reconnect_delay)

async def handle_tcp_connection(ip, port, encrypted_startup, key_param, iv_param, Decode_GetLoginData, ready_event, reconnect_delay=0.5):    
    global spam_room, whisper_writer, spammer_uid, spam_chat_id, spam_uid, online_writer, key, iv    
    key = key_param    
    iv = iv_param    
    
    async def send_response(message, uid, chat_id, chat_type):
        """Helper function to send responses based on chat type"""
        if chat_type == 0:  # Team chat
            msg_packet = await send_team_msg(message, uid, key, iv)
        elif chat_type == 1:  # Clan chat
            msg_packet = await send_clan_msg(message, chat_id, key, iv)
        else:  # Private message
            msg_packet = await send_msg(message, uid, key, iv)
        
        if whisper_writer:
            whisper_writer.write(msg_packet)
            await whisper_writer.drain()

    async def send_chunk(text, uid, chat_id, chat_type, delay=0.3):
        """Send long messages in chunks with delay"""
        chunks = [text[i:i+200] for i in range(0, len(text), 200)]
        for chunk in chunks:
            await send_response(chunk, uid, chat_id, chat_type)
            await asyncio.sleep(delay)

    while True:
        try:
            reader, writer = await asyncio.open_connection(ip, int(port))
            whisper_writer = writer  # Assign to the global writer

            # Send startup packet
            bytes_payload = bytes.fromhex(encrypted_startup)
            whisper_writer.write(bytes_payload)
            await whisper_writer.drain()
            ready_event.set()
            
            # Handle clan startup if needed
            if Decode_GetLoginData.Clan_ID:
                clan_id = Decode_GetLoginData.Clan_ID
                clan_compiled_data = Decode_GetLoginData.Clan_Compiled_Data
                await create_clan_startup(clan_id, clan_compiled_data, key, iv)

            # Main message handling loop
            while True:
                data = await reader.read(9999)
                if not data:
                    break
                    
                if data.hex().startswith("120000"):
                    response = await DecodeWhisperMessage(data.hex()[10:])
                    received_msg = response.Data.msg.lower()
                    uid = response.Data.uid
                    user_name = response.Data.Details.Nickname
                    chat_id = response.Data.Chat_ID
                    # Safe access: try direct, then inside Details, else default to 0
                    chat_type = getattr(response.Data, "chat_type", None) or getattr(response.Data.Details, "chat_type", 0)

                    # Command handling
                    if received_msg == "hi":
                        await send_response(f"Hello {user_name}!", uid, chat_id, chat_type)

                    elif received_msg == "/help":
                        # Welcome message
                        welcome = (
                            f"[C][B][FFD700]Hey {user_name} Welcome to DEV TEAM BOT!\n\n"
                            "[C][B][FFFFFF]Type commands to interact with me.\n"
                            "[C][B][00FF00]Below are all available commands:"
                        )
                        await send_response(welcome, uid, chat_id, chat_type)
                        await asyncio.sleep(0.3)
                        
                        # Group Creation Commands
                        group_commands = (
                            "[C][B][FFD700]🔹 Group Creation 🔹\n\n"
                            "[B][C][FFFFFF]/2 [00FF00]- Create 2 Player Group\n"
                            "[B][C][FFFFFF]/3 [00FF00]- Create 3 Player Group\n"
                            "[B][C][FFFFFF]/4 [00FF00]- Create 4 Player Group\n"
                            "[B][C][FFFFFF]/5 [00FF00]- Create 5 Player Group\n"
                            "[B][C][FFFFFF]/6 [00FF00]- Create 6 Player Group\n"
                            "[B][C][FFFFFF]/team [00FF00]- Create Lag Team Player Group\n"
                            "[B][C][FFFFFF]/join_tc [code] [00FF00]- Join Team by Code\n"
                            "[B][C][FFFFFF]/exit [00FF00]- Leave Current Group"
                        )
                        await send_response(group_commands, uid, chat_id, chat_type)
                        await asyncio.sleep(0.3)
                        
                        # Spam/Interaction Commands
                        spam_commands = (
                            "[C][B][FFD700]🔹 Spam & Interaction 🔹\n\n"
                            "[B][C][FFFFFF]/room [uid] [00FF00]- Spam Room Invites\n"
                            "[B][C][FFFFFF]/spam_inv [uid] [00FF00]- Spam Team Invites\n"
                            "[B][C][FFFFFF]/spam_req [uid] [00FF00]- Spam Join Requests\n"
                            "[B][C][FFFFFF]/lag [team-code] [00FF00]- Lag Team Server\n"
                            "[B][C][FFFFFF]/ms [text] [00FF00]- Send Typing Message"
                        )
                        await send_response(spam_commands, uid, chat_id, chat_type)
                        await asyncio.sleep(0.3)
                        
                        # Player Info Commands
                        info_commands = (
                            "[C][B][FFD700]🔹 Player Information 🔹\n\n"
                            "[B][C][FFFFFF]/info [uid] [00FF00]- Get Player Details\n"
                            "[B][C][FFFFFF]/region [uid] [00FF00]- Check Account Region\n"
                            "[B][C][FFFFFF]/check [uid] [00FF00]- Check Ban Status\n"
                            "[B][C][FFFFFF]/like [uid] [00FF00]- Send Like to Player\n"
                            "[B][C][FFFFFF]/visit [uid] [00FF00]- Send 1000 Visit to Player\n"
                            "[B][C][FFFFFF]/spam [uid] [00FF00]- Spam Friend Requests"
                        )
                        await send_response(info_commands, uid, chat_id, chat_type)
                        await asyncio.sleep(0.3)
                        
                        # Utility Commands
                        utility_commands = (
                            "[C][B][FFD700]🔹 Utility Commands 🔹\n\n"
                            "[B][C][FFFFFF]/ai [question] [00FF00]- Ask AI Anything\n"
                            "[B][C][FFFFFF]/help [00FF00]- Show This Menu Again"
                        )
                        await send_response(utility_commands, uid, chat_id, chat_type)

                    elif received_msg.startswith("/spam_req"):
                        parts = received_msg.strip().split()
                        if len(parts) == 2 and parts[1].isdigit():
                            target_uid = parts[1]
                            await send_response("[C][B][FFFFFF]Joining Request Spam Started", uid, chat_id, chat_type)

                            if online_writer:
                                try:
                                    await start_spam_invite(int(target_uid))
                                    final_message = "[C][B][00FF00]Join Request Spam\n [FF0000]Successful"
                                except Exception as e:
                                    final_message = f"[C][B][FF0000]Error during spam: {str(e)}"
                            else:
                                final_message = "[C][B][FF0000]Error: Bot is not connected to the server."
                            
                            await send_response(final_message, uid, chat_id, chat_type)
                        else:
                            await send_response("[C][B][FF0000]Invalid format. Use /spam_req [uid]", uid, chat_id, chat_type)
                                
                    elif received_msg == "/team":
                        await send_response("Please Accept My Invitation to Join Group.", uid, chat_id, chat_type)
                        await execute_team_spam(uid)
                        await send_response("Request complete", uid, chat_id, chat_type)
                        await left_group(key, iv)
                                
                    elif received_msg.startswith("/lag"):
                        parts = received_msg.strip().split()
                        if len(parts) == 2 and parts[1].isdigit():
                            team_code = parts[1]
                            await send_response("[C][B][FFFFFF]Lag Spam Started", uid, chat_id, chat_type)

                            if online_writer:
                                try:
                                    await perform_lag_attack(team_code, key, iv)
                                    final_message = "[C][B][00FF00]Lag Spam\n [FF0000]Successful"
                                except Exception as e:
                                    final_message = f"[C][B][FF0000]Error during spam: {str(e)}"
                            else:
                                final_message = "[C][B][FF0000]Error: Bot is not connected to the server."
                            
                            await send_response(final_message, uid, chat_id, chat_type)
                        else:
                            await send_response("[C][B][FF0000]Invalid format. Use /lag [code]", uid, chat_id, chat_type)
                                
                    elif received_msg.startswith("/spam_inv"):
                        parts = received_msg.strip().split()
                        if len(parts) == 2 and parts[1].isdigit():
                            target_uid = parts[1]
                            await send_response("[C][B][FFFFFF]Invite Request Spam Started", uid, chat_id, chat_type)

                            if online_writer:
                                try:
                                    await handle_group_spam_invite(int(target_uid))
                                    final_message = "[C][B][00FF00]Invite Request Spam\n [FF0000]Successful"
                                except Exception as e:
                                    final_message = f"[C][B][FF0000]Error during spam: {str(e)}"
                            else:
                                final_message = "[C][B][FF0000]Error: Bot is not connected to the server."
                            
                            await send_response(final_message, uid, chat_id, chat_type)
                        else:
                            await send_response("[C][B][FF0000]Invalid format. Use /spam_inv [uid]", uid, chat_id, chat_type)
                            
                    elif received_msg.startswith("/ms "):
                        raw_message = response.Data.msg[4:].strip()
                        if raw_message:
                            cleaned_message = re.sub(r'[^\x20-\x7E]', '', raw_message).replace("(J,", "")
                            cleaned_message = " ".join(cleaned_message.split())
                            for i in range(1, len(cleaned_message) + 1):
                                partial_message = cleaned_message[:i]
                                colored = f"[C][B]{get_random_color()}{partial_message}"
                                await send_response(colored, uid, chat_id, chat_type)
                                await asyncio.sleep(0.3)
                        else:
                            await send_response("[C][B][FF0000]Invalid format. Use /ms [message]", uid, chat_id, chat_type)

                    elif received_msg.startswith("/info "):
                        parts = received_msg.strip().split()
                        if len(parts) == 2 and parts[1].isdigit():
                            target_uid = parts[1]
                            await send_response("[C][B][FFFFFF]Please wait, fetching info...", uid, chat_id, chat_type)

                            try:
                                url = f"https://ffm-info-bot-info-apis.vercel.app/player-info?uid={target_uid}&region=ind"
                                async with aiohttp.ClientSession() as session:
                                    async with session.get(url) as resp:
                                        if resp.status == 200:
                                            data = await resp.json()
                                            player_data = data.get("player_info", {})
                                            if not player_data:
                                                await send_response("[C][B][FF0000]Player not found or API error.", uid, chat_id, chat_type)
                                            else:
                                                basic = player_data.get("basicInfo", {})
                                                social = player_data.get("socialInfo", {})
                                                clan = player_data.get("clanBasicInfo", {})
                                                captain = player_data.get("captainBasicInfo", {})

                                                # Basic Info
                                                nickname = basic.get('nickname', 'N/A')
                                                account_id = basic.get('accountId', 'N/A')
                                                level = basic.get('level', 'N/A')
                                                likes = basic.get('liked', 'N/A')
                                                signature = social.get('signature', 'N/A')
                                                
                                                # Mask UID properly
                                                uid_display = f"{str(account_id)[:5]}[C]{str(account_id)[5:]}" if len(str(account_id)) > 5 else account_id

                                                # Send Player Info
                                                player_info = (
                                                    f"[C][B]-┌ [FFD700]Player Info:\n"
                                                    f"[FFFFFF]-├─ Name: {nickname}\n"
                                                    f"- ├─ UID: {uid_display}\n"
                                                    f"- ├─ Level: {level}\n"
                                                    f"- ├─ Likes: {likes}\n"
                                                    f"- └─ Bio: {signature}"
                                                )
                                                await send_response(player_info, uid, chat_id, chat_type)
                                                await asyncio.sleep(0.25)

                                                # Clan Info
                                                if clan:
                                                    clan_id = clan.get('clanId', 'N/A')
                                                    clan_name = clan.get('clanName', 'N/A')
                                                    clan_level = clan.get('clanLevel', 'N/A')
                                                    capacity = clan.get('capacity', 'N/A')
                                                    members = clan.get('memberNum', 'N/A')
                                                    
                                                    clan_id_display = f"{str(clan_id)[:5]}[C]{str(clan_id)[5:]}" if len(str(clan_id)) > 5 else clan_id
                                                    
                                                    clan_info = (
                                                        f"[C][B]-┌ [00FF00]Clan Info:\n"
                                                        f"[FFFFFF]-├─ Name: {clan_name}\n"
                                                        f"- ├─ ID: {clan_id_display}\n"
                                                        f"- ├─ Level: {clan_level}\n"
                                                        f"- └─ Members: {members}/{capacity}"
                                                    )
                                                    await send_response(clan_info, uid, chat_id, chat_type)
                                                    await asyncio.sleep(0.25)

                                                    # Clan Leader Info
                                                    if captain:
                                                        captain_name = captain.get('nickname', 'N/A')
                                                        captain_uid = clan.get('captainId', 'N/A')
                                                        captain_level = captain.get('level', 'N/A')
                                                        captain_likes = captain.get('liked', 'N/A')
                                                        
                                                        captain_uid_display = f"{str(captain_uid)[:5]}[C]{str(captain_uid)[5:]}" if len(str(captain_uid)) > 5 else captain_uid
                                                        captain_info = (
                                                            f"[C][B]-┌ [FF69B4]Clan Leader:\n"
                                                            f"[FFFFFF]-├─ Name: {captain_name}\n"
                                                            f"- ├─ UID: {captain_uid_display}\n"
                                                            f"- ├─ Level: {captain_level}\n"
                                                            f"- └─ Likes: {captain_likes}"
                                                        )
                                                        await send_response(captain_info, uid, chat_id, chat_type)
                                        else:
                                            await send_response("[C][B][FF0000]Failed to fetch player info (API Error).", uid, chat_id, chat_type)
                            except Exception as e:
                                await send_response(f"[C][B][FF0000]Error: {str(e)}", uid, chat_id, chat_type)
                        else:
                            await send_response("[C][B][FF0000]Usage: /info [uid]", uid, chat_id, chat_type)

                    elif received_msg.startswith("/check "):
                        parts = received_msg.strip().split()
                        if len(parts) == 2 and parts[1].isdigit():
                            target_uid = parts[1]
                            await send_response("[C][B][FFFFFF]Checking ban status...", uid, chat_id, chat_type)

                            try:
                                url = f"https://ffm-bancheck-bot-info-apis.vercel.app/bancheck?uid={target_uid}"
                                async with aiohttp.ClientSession() as session:
                                    async with session.get(url) as resp:
                                        if resp.status == 200:
                                            data = await resp.json()
                                            message = (
    f"[C][B]-┌ [FFD700]Ban Check Result:\n"
    f"[FFFFFF]-├─ Name: {data.get('nickname', 'N/A')}\n"
    f"- ├─ UID: {str(data.get('uid', 'N/A'))[:5]}[C]{str(data.get('uid', 'N/A'))[5:]}\n"
    f"- ├─ Region: {data.get('region', 'N/A')}\n"
    f"- ├─ Level: {data.get('level', 'N/A')}\n"
    f"- ├─ Likes: {data.get('likes', 'N/A')}\n"
    f"- ├─ Status: {data.get('ban_status', 'N/A')}\n"
    f"- └─ Since: {data.get('banned_since', 'N/A')}"
)
                                        else:
                                            message = "[C][B][FF0000]Failed to check ban status (API Error)."
                            except Exception as e:
                                message = f"[C][B][FF0000]Error: {e}"

                            await send_response(message, uid, chat_id, chat_type)
                        else:
                            await send_response("[C][B][FF0000]Usage: /check [uid]", uid, chat_id, chat_type)

                    elif received_msg.startswith("/region "):
                        parts = received_msg.strip().split()
                        if len(parts) == 2 and parts[1].isdigit():
                            target_uid = parts[1]
                            await send_response("[C][B][FFFFFF]Checking account region...", uid, chat_id, chat_type)

                            try:
                                url = f"https://ffm-region-bot-info-apis.vercel.app/region?uid={target_uid}"
                                async with aiohttp.ClientSession() as session:
                                    async with session.get(url) as resp:
                                        if resp.status == 200:
                                            data = await resp.json()
                                            message = (
    f"[C][B]-┌ [FFD700]Region Check Result:\n"
    f"[FFFFFF]-├─ Name: {data.get('nickname', 'N/A')}\n"
    f"- ├─ UID: {str(data.get('uid', 'N/A'))[:5]}[C]{str(data.get('uid', 'N/A'))[5:]}\n"
    f"- ├─ Region: {data.get('region', 'N/A')}\n"
    f"- ├─ Level: {data.get('level', 'N/A')}\n"
    f"- └─ Likes: {data.get('likes', 'N/A')}"
)
                                        else:
                                            message = "[C][B][FF0000]Failed to check account region (API Error)."
                            except Exception as e:
                                message = f"[C][B][FF0000]Error: {e}"

                            await send_response(message, uid, chat_id, chat_type)
                        else:
                            await send_response("[C][B][FF0000]Usage: /region [uid]", uid, chat_id, chat_type)

                    elif received_msg.startswith("/room") or received_msg.startswith("/spam_room"):
                        parts = response.Data.msg.strip().split(maxsplit=1)
                        if len(parts) == 2 and parts[1].isdigit():
                            target_uid = parts[1]
                            await send_response("Please Wait", uid, chat_id, chat_type)
                            
                            global spam_room, spammer_uid, spam_chat_id, spam_uid
                            if chat_type == 0:
                                spam_chat_id = 1
                                spam_uid = uid
                            elif chat_type == 1:
                                spam_uid = chat_id
                                spam_chat_id = 2
                            else:
                                spam_uid = uid
                                spam_chat_id = 3
                                
                            await uid_status(int(target_uid), key, iv)
                            spam_room = True
                            spammer_uid = uid
                        else:
                            await send_response("[C][B][FF0000]Invalid format. Use /room [uid]", uid, chat_id, chat_type)

                    elif received_msg.startswith("/spam "):
                        parts = received_msg.strip().split()
                        if len(parts) == 2 and parts[1].isdigit():
                            target_uid = parts[1]
                            await send_response("[C][B][FFFFFF]Sending spam, please wait...", uid, chat_id, chat_type)

                            try:
                                url = f"https://ffm-spam-api-bot-aditya-apis.vercel.app/send_requests?uid={target_uid}"
                                async with aiohttp.ClientSession() as session:
                                    async with session.get(url) as resp:
                                        if resp.status == 200:
                                            data = await resp.json()
                                            message = (
                                                f"[C][B][FFD700]Player {data.get('PlayerNickname', 'N/A')} "
                                                f"(UID: {str(data.get('UID', 'N/A'))[:5]}[C]{str(data.get('UID', 'N/A'))[5:]}) "
                                                f"has achieved a total of {data.get('success_count', 'N/A')} successful sends."
                                            )
                                        else:
                                            message = "[C][B][FF0000]Failed to send spam (API error)."
                            except Exception as e:
                                message = f"[C][B][FF0000]Error: {e}"

                            await send_response(message, uid, chat_id, chat_type)
                        else:
                            await send_response("[C][B][FF0000]Usage: /spam [uid]", uid, chat_id, chat_type)

                    elif received_msg.startswith("/visit "):
                        parts = received_msg.strip().split()
                        if len(parts) == 2 and parts[1].isdigit():
                            target_uid = parts[1]
                            await send_response("[C][B][FFFFFF]Sending visit, please wait...", uid, chat_id, chat_type)

                            try:
                                url = f"https://ffm-visit-api-bot-aditya-apis.vercel.app/visit?uid={target_uid}&region=ind"
                                async with aiohttp.ClientSession() as session:
                                    async with session.get(url) as resp:
                                        if resp.status == 200:
                                            data = await resp.json()
                                            message = (
                                                    f"[C][B][FFD700]Player {data.get('nickname', 'N/A')} "
                                                    f"(UID: {str(data.get('uid', 'N/A'))[:5]}[C]{str(data.get('uid', 'N/A'))[5:]}) "
                                                    f"has successfully sent {data.get('success', 'N/A')} visits. "
                                                    f"Please restart the game."
                                            )
                                        else:
                                            message = "[C][B][FF0000]Failed to send visit (API error)."
                            except Exception as e:
                                message = f"[C][B][FF0000]Error: {e}"

                            await send_response(message, uid, chat_id, chat_type)
                        else:
                            await send_response("[C][B][FF0000]Usage: /visit [uid]", uid, chat_id, chat_type)

                    elif received_msg.startswith("/like "):
                        parts = received_msg.strip().split()
                        if len(parts) == 2 and parts[1].isdigit():
                            target_uid = parts[1]
                            await send_response("[C][B][FFFFFF]Sending like, please wait...", uid, chat_id, chat_type)

                            try:
                                url = f"https://ffm-like-apis-bot-aditya.vercel.app/like?uid={target_uid}&server_name=ind&key=360"
                                async with aiohttp.ClientSession() as session:
                                    async with session.get(url) as resp:
                                        if resp.status == 200:
                                            data = await resp.json()
                                            likes_given = data.get('LikesGivenByAPI', 0)
                                            if likes_given > 0:
                                                message = (
                                                    f"[C][B]-┌ [FFD700]Like Sent Successfully:\n"
                                                    f"[FFFFFF]-├─ Name: {data.get('PlayerNickname', 'N/A')}\n"
                                                    f"- ├─ UID: {str(data.get('UID', 'N/A'))[:5]}[C]{str(data.get('UID', 'N/A'))[5:]}\n"
                                                    f"- ├─ Likes Before: {data.get('LikesbeforeCommand', 'N/A')}\n"
                                                    f"- ├─ Likes Given: {data.get('LikesGivenByAPI', 'N/A')}\n"
                                                    f"- └─ Likes After: {data.get('LikesafterCommand', 'N/A')}"
                                                    )
                                            else:
                                                message = f"[C][B][FFA500]Max likes already sent to {data.get('PlayerNickname', 'this player')} for today. Try again tomorrow."
                                        else:
                                            message = "[C][B][FF0000]Failed to send like (API error)."
                            except Exception as e:
                                message = f"[C][B][FF0000]Error: {e}"

                            await send_response(message, uid, chat_id, chat_type)
                        else:
                            await send_response("[C][B][FF0000]Usage: /like [uid]", uid, chat_id, chat_type)

                    elif received_msg == "/2":
                        await send_response("Please Accept My Invitation to Join Group.", uid, chat_id, chat_type)
                        await create_group(key, iv)
                        await asyncio.sleep(0.4)
                        await modify_team_player("1", key, iv)
                        await asyncio.sleep(0.1)
                        await invite_target(uid, key, iv)
                        await asyncio.sleep(10)
                        await left_group(key, iv)
                        
                    elif received_msg == "/3":
                        await send_response("Please Accept My Invitation to Join Group.", uid, chat_id, chat_type)
                        await create_group(key, iv)
                        await asyncio.sleep(0.4)
                        await modify_team_player("2", key, iv)
                        await asyncio.sleep(0.1)
                        await invite_target(uid, key, iv)
                        await asyncio.sleep(10)
                        await left_group(key, iv)

                    elif received_msg == "/4":
                        await send_response("Please Accept My Invitation to Join Group.", uid, chat_id, chat_type)
                        await create_group(key, iv)
                        await asyncio.sleep(0.4)
                        await modify_team_player("3", key, iv)
                        await asyncio.sleep(0.1)
                        await invite_target(uid, key, iv)
                        await asyncio.sleep(10)
                        await left_group(key, iv)

                    elif received_msg == "/5":
                        await send_response("Please Accept My Invitation to Join Group.", uid, chat_id, chat_type)
                        await create_group(key, iv)
                        await asyncio.sleep(0.4)
                        await modify_team_player("4", key, iv)
                        await asyncio.sleep(0.1)
                        await invite_target(uid, key, iv)
                        await asyncio.sleep(10)
                        await left_group(key, iv)

                    elif received_msg == "/6":
                        await send_response("Please Accept My Invitation to Join Group.", uid, chat_id, chat_type)
                        await create_group(key, iv)
                        await asyncio.sleep(0.4)
                        await modify_team_player("5", key, iv)
                        await asyncio.sleep(0.1)
                        await invite_target(uid, key, iv)
                        await asyncio.sleep(10)
                        await left_group(key, iv)

                    elif received_msg.startswith("/join_tc "):
                        parts = received_msg.strip().split()
                        if len(parts) == 2 and parts[1].isdigit():
                            team_code = parts[1]
                            await send_response("Request received. Joining team...", uid, chat_id, chat_type)
                            await join_teamcode(team_code, key, iv)
                        else:
                            await send_response("[C][B][FF0000]Invalid format. Use /join_tc [team_code]", uid, chat_id, chat_type)

                    elif received_msg == "/exit":
                        await send_response("Leaving group...", uid, chat_id, chat_type)
                        await left_group(key, iv)

                    elif received_msg.startswith("/ai "):
                        user_input = response.Data.msg[len("/ai"):].strip()
                        if user_input:
                            ai_response = await Get_AI_Response(user_input)
                            parts = await split_text_by_words(ai_response)
                            for message in parts:
                                await asyncio.sleep(1)
                                await send_response(message, uid, chat_id, chat_type)
                        else:
                            await send_response("[C][B][FF0000]Please provide a question. Ex: /ai How are you?", uid, chat_id, chat_type)

            whisper_writer.close()
            await whisper_writer.wait_closed()
            whisper_writer = None # <--- FIX: Clear global writer on disconnect

        except Exception as e:
            print(f"Error with {ip}:{port} - {e}")
            whisper_writer = None # <--- FIX: Clear global writer on error

        await asyncio.sleep(reconnect_delay)

async def main(uid, password):
    open_id, access_token = await get_access_token(uid, password)
    if not open_id or not access_token:
        print("Invalid Account")
        return None
    payload = await MajorLoginProto_Encode(open_id, access_token)
    MajorLoginResponse = await MajorLogin(payload)
    if not MajorLoginResponse:
        print("Account has been banned or doesn't registered")
        return None
    Decode_MajorLogin = await MajorLogin_Decode(MajorLoginResponse)
    base_url = Decode_MajorLogin.url
    token = Decode_MajorLogin.token
    AccountUID = Decode_MajorLogin.account_uid
    print(f"Account has been online with UID: {AccountUID}")
    key = Decode_MajorLogin.key
    iv = Decode_MajorLogin.iv
    timestamp = Decode_MajorLogin.timestamp
    GetLoginDataResponse = await GetLoginData(base_url, payload, token)
    if not GetLoginDataResponse:
        print("Dam Something went Wrong, Please Check GetLoginData")
        return None
    Decode_GetLoginData = await GetLoginData_Decode(GetLoginDataResponse)
    Online_IP_Port = Decode_GetLoginData.Online_IP_Port
    AccountIP_Port = Decode_GetLoginData.AccountIP_Port
    online_ip, online_port = Online_IP_Port.split(":")
    account_ip, account_port = AccountIP_Port.split(":")
    encrypted_startup = await get_encrypted_startup(int(AccountUID), token, int(timestamp), key, iv)

    ready_event = asyncio.Event()
    task1 = asyncio.create_task(
        handle_tcp_connection(account_ip, account_port, encrypted_startup, key, iv, Decode_GetLoginData, ready_event)
    )

    await ready_event.wait()
    await asyncio.sleep(2)

    task2 = asyncio.create_task(
        handle_tcp_online_connection(online_ip, online_port, key, iv, encrypted_startup)
    )

    await asyncio.gather(task1, task2)

@app.route('/')
async def index():
    return 'running!'

async def run_async(coro):
    """Helper function to run async coroutines in sync context"""
    loop = asyncio.get_event_loop()
    return await loop.create_task(coro)

key = b'Yg&tc%DEuh6%Zc^8'
iv = b'6oyZDr22E3ychjM%'

event_loop = asyncio.new_event_loop()

def run_async_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()

# Start the event loop in a separate thread
async_thread = Thread(target=run_async_loop, args=(event_loop,), daemon=True)
async_thread.start()

@bot.message_handler(commands=["start"])
def handle_start_command(message):
    help_text = """
<b>🔥 FREE FIRE BOT COMMANDS 🔥</b>

<b><u>📌 BASIC TEAM COMMANDS</u></b>
<b>/2 [UID]</b> - CREATE 2-PLAYER TEAM
<b>/3 [UID]</b> - CREATE 3-PLAYER TEAM 
<b>/4 [UID]</b> - CREATE 4-PLAYER TEAM
<b>/5 [UID]</b> - CREATE 5-PLAYER TEAM
<b>/6 [UID]</b> - CREATE 6-PLAYER TEAM
<b>/join_tc [CODE]</b> - JOIN SPECIFIC TEAM

<b><u>💣 SPAM FUNCTIONS</u></b>  
<b>/spam_inv [UID]</b> - SEND MULTIPLE GROUP INVITES
<b>/spam_req [UID]</b> - SEND MULTIPLE JOIN REQUESTS 
<b>/team [UID]</b> - RAPID TEAM SWITCHING
<b>/lag [CODE]</b> - TEAM CODE SPAM

<b>📝 IMPORTANT NOTES:</b>
<b>1. UID MUST BE 8-11 DIGITS</b>
<b>2. TEAM CODES MUST BE 7 DIGITS</b>  
<b>3. INVITES LAST 8 SECONDS</b>
<b>4. MAY TRIGGER COOLDOWNS</b>
<b>5. DON'T SPAM THE SAME TARGET REPEATEDLY</b>
    """
    
    bot.reply_to(message, help_text, parse_mode="HTML")

@bot.message_handler(commands=["2", "3", "4", "5", "6"])
def handle_team_command(message):
    try:
        parts = message.text.split()
        if len(parts) < 2:
            command = parts[0]
            bot.reply_to(message, 
                        f"<b>⚠️ MISSING UID</b>\n"
                        f"<b>USAGE: {command} [UID]</b>\n"
                        f"<b>EXAMPLE: {command} 7669969208</b>\n"
                        f"<b>CREATES {command[1:]}-PLAYER TEAM</b>",
                        parse_mode="HTML")
            return
            
        command = parts[0]
        uid = parts[1]
        
        if not uid.isdigit() or len(uid) < 8 or len(uid) > 11:
            bot.reply_to(message, 
                        "<b>❌ INVALID UID FORMAT</b>\n"
                        "<b>• MUST BE 8-11 DIGITS</b>\n"
                        "<b>• EXAMPLE: 7669969208</b>",
                        parse_mode="HTML")
            return
            
        if not all([whisper_writer, online_writer, key, iv]):
            bot.reply_to(message, 
                        "<b>⚠️ CONNECTION ERROR</b>\n"
                        "<b>BOT NOT CONNECTED TO FREE FIRE</b>\n"
                        "<b>PLEASE TRY AGAIN LATER</b>",
                        parse_mode="HTML")
            return
            
        team_size = int(command[1:]) - 1
        masked_uid = f"{uid}"
            
        processing_msg = bot.reply_to(message,
                                    f"<b>🔄 CREATING {team_size+1}-PLAYER TEAM...</b>\n"
                                    f"<b>• FOR UID: {masked_uid}</b>\n"
                                    f"<b>• PLEASE WAIT</b>",
                                    parse_mode="HTML")
        
        asyncio.run_coroutine_threadsafe(
            handle_group_invite(int(uid), team_size, message.chat.id, processing_msg.message_id),
            event_loop
        )
        
    except Exception as e:
        bot.reply_to(message,
                    f"<b>❌ UNEXPECTED ERROR</b>\n"
                    f"<b>PLEASE TRY AGAIN LATER</b>\n"
                    f"<b>ERROR: {str(e)}</b>",
                    parse_mode="HTML")

@bot.message_handler(commands=["spam_inv"])
def handle_spam_inv_command(message):
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, 
                        "<b>⚠️ MISSING UID</b>\n"
                        "<b>USAGE: /spam_inv [UID]</b>\n"
                        "<b>EXAMPLE: /spam_inv 7669969208</b>",
                        parse_mode="HTML")
            return
            
        uid = parts[1]
        
        if not uid.isdigit() or len(uid) < 8 or len(uid) > 11:
            bot.reply_to(message, 
                        "<b>❌ INVALID UID</b>\n"
                        "<b>MUST BE 8-11 DIGITS</b>",
                        parse_mode="HTML")
            return
            
        if not all([whisper_writer, online_writer, key, iv]):
            bot.reply_to(message, 
                        "<b>⚠️ BOT OFFLINE</b>\n"
                        "<b>NOT CONNECTED TO FREE FIRE</b>",
                        parse_mode="HTML")
            return

        # Store the initial message for editing later
        sent_msg = bot.reply_to(message, 
                    f"<b>🚀 SPAM INVITE STARTED</b>\n"
                    f"<b>• TARGET: {uid}</b>\n"
                    f"<b>• DURATION: 60 SECONDS</b>\n"
                    f"<b>• STATUS: RUNNING...</b>",
                    parse_mode="HTML")

        async def perform_spam_invite():
            start_time = time.time()
            success_count = 0
            while time.time() - start_time < 60:
                try:
                    await handle_group_spam_invite(int(uid))
                    success_count += 1
                    await asyncio.sleep(0.1)
                except Exception as e:
                    print(f"Error in spam invite: {str(e)[:50]}")
                    await asyncio.sleep(0.5)
            
            # Edit the original message when complete
            bot.edit_message_text(
                f"<b>✅ SPAM INVITE COMPLETED</b>\n"
                f"<b>• TARGET: {uid}</b>",
                chat_id=sent_msg.chat.id,
                message_id=sent_msg.message_id,
                parse_mode="HTML"
            )

        asyncio.run_coroutine_threadsafe(perform_spam_invite(), event_loop)
        
    except Exception as e:
        bot.reply_to(message,
                    f"<b>❌ ERROR</b>\n"
                    f"<b>{str(e)}</b>",
                    parse_mode="HTML")

@bot.message_handler(commands=["spam_req"])
def handle_spam_req_command(message):
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message,
                        "<b>⚠️ MISSING UID</b>\n"
                        "<b>USAGE: /spam_req [UID]</b>\n"
                        "<b>EXAMPLE: /spam_req 7669969208</b>",
                        parse_mode="HTML")
            return
            
        uid = parts[1]
        
        if not uid.isdigit() or len(uid) < 8 or len(uid) > 11:
            bot.reply_to(message,
                        "<b>❌ INVALID UID</b>\n"
                        "<b>• MUST BE 8-11 DIGITS</b>\n"
                        "<b>• EXAMPLE: 7669969208</b>",
                        parse_mode="HTML")
            return
            
        if not all([whisper_writer, online_writer, key, iv]):
            bot.reply_to(message,
                        "<b>⚠️ BOT OFFLINE</b>\n"
                        "<b>NOT CONNECTED TO FREE FIRE</b>",
                        parse_mode="HTML")
            return

        # Store the initial message for editing later
        sent_msg = bot.reply_to(message,
                    f"<b>🌀 JOIN REQUEST SPAM STARTED</b>\n"
                    f"<b>• TARGET: {uid}</b>\n"
                    f"<b>• DURATION: 60 SECONDS</b>\n"
                    f"<b>• STATUS: RUNNING...</b>",
                    parse_mode="HTML")

        async def perform_spam_req():
            start_time = time.time()
            success_count = 0
            while time.time() - start_time < 60:
                try:
                    await start_spam_invite(int(uid))
                    success_count += 1
                    await asyncio.sleep(0.1)
                except Exception as e:
                    print(f"Error in spam request: {str(e)[:50]}")
                    await asyncio.sleep(0.5)
            
            # Edit the original message when complete
            bot.edit_message_text(
                f"<b>✅ JOIN REQUEST SPAM COMPLETED</b>\n"
                f"<b>• TARGET: {uid}</b>",
                chat_id=sent_msg.chat.id,
                message_id=sent_msg.message_id,
                parse_mode="HTML"
            )

        asyncio.run_coroutine_threadsafe(perform_spam_req(), event_loop)
        
    except Exception as e:
        bot.reply_to(message,
                    f"<b>❌ COMMAND ERROR</b>\n"
                    f"<b>{str(e)[:100]}</b>",
                    parse_mode="HTML")

@bot.message_handler(commands=["lag"])
def handle_lag_command(message):
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message,
                        "<b>⚠️ MISSING TEAM CODE</b>\n"
                        "<b>USAGE: /lag [7-DIGIT-CODE]</b>\n"
                        "<b>EXAMPLE: /lag 1234567</b>",
                        parse_mode="HTML")
            return

        team_code = parts[1]
        
        if not team_code.isdigit() or len(team_code) != 7:
            bot.reply_to(message,
                        "<b>❌ INVALID CODE</b>\n"
                        "<b>• MUST BE 7 DIGITS</b>\n"
                        "<b>• EXAMPLE: 1234567</b>",
                        parse_mode="HTML")
            return

        if not all([whisper_writer, online_writer, key, iv]):
            bot.reply_to(message,
                        "<b>⚠️ BOT OFFLINE</b>\n"
                        "<b>NOT CONNECTED TO FREE FIRE</b>",
                        parse_mode="HTML")
            return

        sent_msg = bot.reply_to(message,
                    f"<b>💣 LAG ATTACK INITIATED</b>\n"
                    f"<b>• TARGET CODE: {team_code}</b>\n"
                    f"<b>• DURATION: 60 SECONDS</b>\n"
                    f"<b>• STATUS: RUNNING...</b>",
                    parse_mode="HTML")

        async def execute_attack():
            success_count = await perform_lag_attack(team_code, key, iv)
            bot.edit_message_text(
                f"<b>💣 LAG ATTACK COMPLETED</b>\n"
                f"<b>• TARGET CODE: {team_code}</b>",
                chat_id=sent_msg.chat.id,
                message_id=sent_msg.message_id,
                parse_mode="HTML"
            )
            print(f"🔥 LAG ATTACK COMPLETE: {success_count} joins in 60 seconds")

        asyncio.run_coroutine_threadsafe(execute_attack(), event_loop)
        
    except Exception as e:
        bot.reply_to(message,
                    f"<b>❌ COMMAND ERROR</b>\n"
                    f"<b>{str(e)[:100]}</b>",
                    parse_mode="HTML")

@bot.message_handler(commands=["join_tc"])
def handle_join_tc_command(message):
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message,
                        "<b>⚠️ MISSING TEAM CODE</b>\n"
                        "<b>USAGE: /join_tc [7-DIGIT-CODE]</b>\n"
                        "<b>EXAMPLE: /join_tc 1234567</b>",
                        parse_mode="HTML")
            return

        team_code = parts[1]
        
        if not team_code.isdigit() or len(team_code) != 7:
            bot.reply_to(message,
                        "<b>❌ INVALID CODE FORMAT</b>\n"
                        "<b>• MUST BE 7 DIGITS</b>\n"
                        "<b>• EXAMPLE: 1234567</b>",
                        parse_mode="HTML")
            return

        if not all([whisper_writer, online_writer, key, iv]):
            bot.reply_to(message,
                        "<b>⚠️ CONNECTION ERROR</b>\n"
                        "<b>BOT NOT CONNECTED TO GAME</b>",
                        parse_mode="HTML")
            return

        status_msg = bot.reply_to(message,
                                f"<b>🔍 ATTEMPTING TO JOIN TEAM...</b>\n"
                                f"<b>CODE: {team_code}</b>",
                                parse_mode="HTML")

        async def join_and_notify():
            try:
                result = await join_teamcode(team_code, key, iv)
                bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=status_msg.message_id,
                    text=f"<b>✅ JOINED TEAM SUCCESSFULLY</b>\n"
                         f"<b>CODE: {team_code}</b>",
                    parse_mode="HTML"
                )
            except Exception as e:
                bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=status_msg.message_id,
                    text=f"<b>❌ FAILED TO JOIN TEAM</b>\n"
                         f"<b>CODE: {team_code}</b>\n"
                         f"<b>ERROR: {str(e)[:50]}</b>",
                    parse_mode="HTML"
                )

        asyncio.run_coroutine_threadsafe(join_and_notify(), event_loop)
        
    except Exception as e:
        bot.reply_to(message,
                    f"<b>❌ COMMAND ERROR</b>\n"
                    f"<b>{str(e)[:100]}</b>",
                    parse_mode="HTML")

@bot.message_handler(commands=["team"])
def handle_team_spam_command(message):
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message,
                        "<b>⚠️ MISSING UID</b>\n"
                        "<b>USAGE: /team [UID]</b>\n"
                        "<b>EXAMPLE: /team 7669969208</b>",
                        parse_mode="HTML")
            return
            
        uid = parts[1]
        
        if not uid.isdigit() or len(uid) < 8 or len(uid) > 11:
            bot.reply_to(message,
                        "<b>❌ INVALID UID</b>\n"
                        "<b>• MUST BE 8-11 DIGITS</b>\n"
                        "<b>• EXAMPLE: 7669969208</b>",
                        parse_mode="HTML")
            return
            
        if not all([whisper_writer, online_writer, key, iv]):
            bot.reply_to(message,
                        "<b>⚠️ BOT OFFLINE</b>\n"
                        "<b>NOT CONNECTED TO FREE FIRE</b>",
                        parse_mode="HTML")
            return

        status_msg = bot.reply_to(message,
                                "<b>🌀 STARTING TEAM SPAM</b>\n"
                                f"<b>• TARGET: {uid}</b>\n"
                                "<b>• DURATION: 60 SECONDS</b>",
                                parse_mode="HTML")

        def run_async():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                loop.run_until_complete(execute_team_spam(int(uid)))
                bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=status_msg.message_id,
                    text="<b>✅ TEAM SPAM COMPLETE</b>\n"
                         f"<b>• Target: {uid}</b>",
                    parse_mode="HTML"
                )
            except Exception as e:
                bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=status_msg.message_id,
                    text=f"<b>❌ TEAM SPAM FAILED</b>\n"
                         f"<b>• Error: {str(e)[:50]}</b>",
                    parse_mode="HTML"
                )
            finally:
                loop.close()

        thread = threading.Thread(target=run_async)
        thread.start()

    except Exception as e:
        bot.reply_to(message,
                    f"<b>❌ COMMAND ERROR</b>\n"
                    f"<b>{str(e)[:100]}</b>",
                    parse_mode="HTML")

async def handle_group_invite(target_uid, team_size, chat_id, msg_id):
    try:
        uid_str = str(target_uid)
        masked_uid = f"{uid_str}"
        team_count = team_size + 1
        
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=msg_id,
            text=f"<b>🔄 STARTING {team_count}-PLAYER TEAM</b>\n"
                 f"<b>• FOR: {masked_uid}</b>\n"
                 f"<b>• STATUS: CREATING GROUP...</b>",
            parse_mode="HTML"
        )
        await create_group(key, iv)
        await asyncio.sleep(0.5)

        bot.edit_message_text(
            chat_id=chat_id,
            message_id=msg_id,
            text=f"<b>🔄 CONFIGURING TEAM</b>\n"
                 f"<b>• FOR: {masked_uid}</b>\n"
                 f"<b>• STATUS: SETTING {team_count}-PLAYER MODE...</b>",
            parse_mode="HTML"
        )
        await modify_team_player(str(team_size), key, iv)
        await asyncio.sleep(0.3)

        bot.edit_message_text(
            chat_id=chat_id,
            message_id=msg_id,
            text=f"<b>📩 INVITATION SENT!</b>\n"
                 f"<b>• TO: {masked_uid}</b>\n"
                 f"<b>• TEAM SIZE: {team_count}</b>\n"
                 f"<b>• EXPIRES IN: 8 SECONDS</b>",
            parse_mode="HTML"
        )
        await invite_target(target_uid, key, iv)

        for remaining in [7, 6, 5, 4, 3, 2, 1]:
            await asyncio.sleep(1)
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=msg_id,
                text=f"<b>⏳ INVITATION ACTIVE</b>\n"
                     f"<b>• TO: {masked_uid}</b>\n"
                     f"<b>• EXPIRES IN: {remaining} SECONDS</b>\n"
                     f"<b>• ACCEPT QUICKLY!</b>",
                parse_mode="HTML"
            )

        await left_group(key, iv)
        await asyncio.sleep(1)

        bot.edit_message_text(
            chat_id=chat_id,
            message_id=msg_id,
            text=f"<b>⌛ INVITATION EXPIRED</b>\n"
                 f"<b>• TO: {masked_uid}</b>\n"
                 f"<b>• TEAM SIZE: {team_count}</b>\n"
                 f"<b>• DURATION: 8 SECONDS</b>\n"
                 f"<b>• SEND NEW INVITE IF NEEDED</b>",
            parse_mode="HTML"
        )

    except Exception as e:
        try:
            await left_group(key, iv)
        except:
            pass
            
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=msg_id,
            text=f"<b>❌ FAILED</b>\n"
                 f"<b>• FOR: {masked_uid}</b>\n"
                 f"<b>• ERROR: {str(e)[:50]}</b>\n"
                 f"<b>• TRY AGAIN OR CHECK UID</b>",
            parse_mode="HTML"
        )

async def perform_lag_attack(team_code, key, iv):
    start_time = time.time()
    success_count = 0
    while time.time() - start_time < 60:
        try:
            await join_teamcode(team_code, key, iv)
            await asyncio.sleep(0.001)
            await left_group(key, iv)
            success_count += 1
            await asyncio.sleep(0)
        except Exception as e:
            print(f"❌ Error: {str(e)[:50]}")
            await asyncio.sleep(0.1)
    return success_count

async def execute_team_spam(target_uid):
    start_time = time.time()
    try:
        await create_group(key, iv)
        await asyncio.sleep(0.4)
        await modify_team_player("4", key, iv)
        await asyncio.sleep(3)
        await invite_target(target_uid, key, iv)
        
        while time.time() - start_time < 60:
            try:
                await modify_team_player("4", key, iv)
                await asyncio.sleep(0.1)
                await modify_team_player("3", key, iv)
                await asyncio.sleep(0)
            except Exception as loop_error:
                print(f"⚠️ Loop error: {str(loop_error)[:50]}")
                await asyncio.sleep(0.5)
                continue
        
        await left_group(key, iv)
        
    except Exception as main_error:
        print(f"❌ Critical error in team spam: {str(main_error)[:50]}")
        try:
            await left_group(key, iv)
        except:
            pass
        raise

async def handle_group_spam_invite(target_uid):
    start_time = time.time()
    uid_str = str(target_uid)
    invite_count = 0
    
    while time.time() - start_time < 60:
        try:
            await create_group(key, iv)
            await asyncio.sleep(0.1)
            await modify_team_player("3", key, iv)
            await asyncio.sleep(0.1)
            await invite_target(target_uid, key, iv)
            invite_count += 1
            await asyncio.sleep(0.1)
            await left_group(key, iv)
            await asyncio.sleep(0.1)
        except Exception as e:
            print(f"❌ Error: {str(e)[:50]}")
            await asyncio.sleep(0.5)
    
    print(f"🔥 COMPLETED: {invite_count} invites in 60 seconds")

async def start_spam_invite(target_uid):
    try:
        uid_str = str(target_uid)
        start_time = time.time()
        request_count = 0
        
        while time.time() - start_time < 60:
            try:
                await wlxd_skwad(target_uid, key, iv)
                request_count += 1
                await asyncio.sleep(0.1)
            except Exception as e:
                print(f"❌ Error: {str(e)[:50]}")
                await asyncio.sleep(0.5)
        
        print(f"🔥 COMPLETED: {request_count} requests in 60 seconds")
    except Exception as e:
        print(f"❌ Fatal error: {e}")

async def start_bot(uid, password):
    try:
        await asyncio.wait_for(main(uid, password), timeout=TOKEN_EXPIRY)
    except asyncio.TimeoutError:
        print("Token expired after 7 hours. Restarting...")
    except Exception as e:
        print(f"TCP Error: {e}. Restarting...")

async def run_forever(uid, password):
    while True:
        await start_bot(uid, password)

def run_bot():
    asyncio.run(run_forever(
        "4327906078",
        "CA41C90FFC940D005F286CFB998B8DC09AE5320E02DD1E6476DFAA203619CC58"
    ))

if __name__ == '__main__':
    import threading
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()
    bot.infinity_polling()
    app.run(host='0.0.0.0', port=8080)


if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
