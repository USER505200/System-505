import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
PREFIX = "!"
DB_PATH = "bot.db"

EMOJIS = {
    "success": "<:80012verified:1485901284719460403>",
    "error": "<:6426error:1485901393075376179>",
    "warning": "<:3warnings:1485901486511624262>",
    "loading": "<:3536timeout:1485901553490595870>",
    "ban": "<:ban:1485901519525253173>",
    "kick": "<:Kick:1485901574344806550>",
    "mute": "<:servermute:1485901606464520312>",
    "unmute": "<:6859unmute:1485901623128752189>",
    "jail": "<:142Jail:1485901641520779366>",
    "timeout": "<:3536timeout:1485901553490595870>",
    "warn_1": "<:1warning:1485901428328501308>",
    "warn_2": "<:2warnings:1485901458179362916>",
    "warn_3": "<:3warnings:1485901486511624262>",
    "warns": "<:warnings:1485901661099659325>",
    "clear": "<:Clear:1485901795824898078>",
    "save": "<:save:1485901739994513429>",
    "security": "<:security:1485901778896556063>",
    "pause": "<:pause:1485901706880614515>",
    "marry": "<:Marry:1485901683027480596>",
    "request_marry": "<:Request_Marry:1485901761892847636>",
    "info": "<:warnings:1485901661099659325>",
}

COLORS = {
    "default": 0x000000, "success": 0x00FF00, "error": 0xFF0000,
    "warning": 0xFFA500, "ban": 0xFF0000, "kick": 0xFF0000,
    "unban": 0x00FF00, "unmute": 0x00FF00, "unjail": 0x00FF00, "info": 0x000000,
}

DELETE_RESPONSE_DELAY = 10

COMMAND_PERMISSIONS = {
    "ban": {"allowed_roles": ["admin_only"]}, "kick": {"allowed_roles": ["admin_only"]},
    "mute": {"allowed_roles": ["admin_only"]}, "unmute": {"allowed_roles": ["admin_only"]},
    "clear": {"allowed_roles": ["admin_only"]}, "clearuser": {"allowed_roles": ["admin_only"]},
    "warn": {"allowed_roles": ["admin_only"]}, "checkwarn": {"allowed_roles": []},
    "removewarn": {"allowed_roles": ["admin_only"]}, "resetwarn": {"allowed_roles": ["admin_only"]},
    "jail": {"allowed_roles": ["admin_only"]}, "unjail": {"allowed_roles": ["admin_only"]},
    "saveroles": {"allowed_roles": ["admin_only"]}, "restoreroles": {"allowed_roles": ["admin_only"]},
    "lock": {"allowed_roles": ["admin_only"]}, "unlock": {"allowed_roles": ["admin_only"]},
    "lockdown": {"allowed_roles": ["admin_only"]}, "unlockdown": {"allowed_roles": ["admin_only"]},
    "block": {"allowed_roles": ["admin_only"]}, "unblock": {"allowed_roles": ["admin_only"]},
    "addrole": {"allowed_roles": ["admin_only"]}, "removerole": {"allowed_roles": ["admin_only"]},
    "addallowedrole": {"allowed_roles": ["admin_only"]}, "removeallowedrole": {"allowed_roles": ["admin_only"]},
    "marry": {"allowed_roles": []}, "divorce": {"allowed_roles": []},
    "goodnight": {"allowed_roles": []}, "ez": {"allowed_roles": ["admin_only"]},
    "setgif": {"allowed_roles": ["admin_only"]}, "avatar": {"allowed_roles": []},
    "banner": {"allowed_roles": []}, "userinfo": {"allowed_roles": []},
    "serverinfo": {"allowed_roles": []}, "roleinfo": {"allowed_roles": []},
    "botinfo": {"allowed_roles": []}, "nickname": {"allowed_roles": ["admin_only"]},
    "help": {"allowed_roles": []}, "timeout": {"allowed_roles": ["admin_only"]},
    "ipban": {"allowed_roles": ["admin_only"]}, "hwidban": {"allowed_roles": ["admin_only"]},
    "unban": {"allowed_roles": ["admin_only"]},
}

def get_command_permission(command_name: str) -> list:
    return COMMAND_PERMISSIONS.get(command_name, {}).get("allowed_roles", [])

def is_command_allowed(command_name: str, user_roles: list) -> bool:
    permissions = get_command_permission(command_name)
    if not permissions:
        return True
    if "admin_only" in permissions:
        return "admin_only"
    for role in user_roles:
        if str(role.id) in permissions:
            return True
    return False