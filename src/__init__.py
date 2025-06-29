import configparser
import os

from pyrogram import Client
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from vk_api import VkApi

config = configparser.RawConfigParser()
config.read(os.path.join(os.path.dirname(__file__), "..", "config.ini"))

UPLOAD_DIR = config["os"]["upload_dir"]
STATIC_DIR = config["os"]["static_dir"]
SITE_DIR = config["os"]["site_dir"]

DATABASE_URL = config["db"]["database_url"]

TG_CHANNEL = config["tg"]["channel"]
TG_API_ID = config["tg"]["api_id"]
TG_API_HASH = config["tg"]["api_hash"]
TG_SESSION_NAME = config["tg"]["session_name"]

VK_TOKEN = config["vk"]["token"]
VK_API_VERSION = config["vk"]["api_version"]
VK_GROUP_ID = config["vk"]["group_id"]

os.makedirs(UPLOAD_DIR, exist_ok=True)

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

tg_app = Client(name=TG_SESSION_NAME, api_id=TG_API_ID, api_hash=TG_API_HASH)

vk_session = VkApi(token=VK_TOKEN, api_version=VK_API_VERSION)
vk_app = vk_session.get_api()
