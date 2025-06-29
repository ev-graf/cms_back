import json
import logging
import os
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List
from uuid import uuid4

from fastapi import APIRouter, UploadFile, File, Form, Depends, Body, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from src import UPLOAD_DIR, SITE_DIR, SessionLocal, engine
from .models import Base, Images, VKAlbums, UploadItem, Storage
from .tg.tg import tg_send_post
from .vk.vk import vk_send_post, vk_save_actual_albums, vk_save_in_albums

logging.basicConfig(level=logging.INFO)

Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


router = APIRouter(prefix="/api/v1")


@router.post("/auth")
async def get_autn_token(login: str, password: str):
    if login == "login" and password == "password":
        return 200, {"access_token": str(uuid4())}
    return {"error", "Wrong login or password"}


@router.get("/data/get_last_posts")
async def get_last_posts():
    # posts = [{"id": i, "src": f"https://placehold.co/600x400?text=Post+{i}", "text": f"Post {i}"} for i in range(1, 8)]
    yesterday = datetime.now(timezone.utc) - timedelta(days=1)
    date = yesterday.strftime('%Y_%m_%d')
    folder_path = Path(UPLOAD_DIR) / date
    current_dir = f"{SITE_DIR}/{date}"
    posts = []
    for i, file in enumerate(folder_path.iterdir()):
        if file.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}:
            filename = f"{current_dir}/{file.name}"
            posts.append({"id": i + 1, "src": filename, "text": f"Post {i + 1}"})
    return {"posts": posts, "total_count": len(posts)}


@router.post("/upload")
async def upload_post(
    text: str = Form(...),
    schedule_date: str = Form(...),
    schedule_time: str = Form(...),
    images: List[UploadFile] = File(...),
    links: List[str] = Form(...),
    db: Session = Depends(get_db)
):
    logging.info(f"Текст поста: {text}")
    logging.info(f"Запланировано на дату: {schedule_date}, время: {schedule_time}")

    links_tg = [l for link in links if (l := str(link).strip())]
    links_tg_new = []
    for link in links_tg.copy():
        if link not in links_tg_new:
            links_tg_new.append(link)
    links_tg = links_tg_new

    current_link = links[0]
    links_vk = []
    for link in links.copy():
        if l := str(link or "").strip():
            current_link = str(l)
        links_vk.append(current_link)
    links = links_vk

    try:
        schedule_time_ = datetime.strptime(f"{schedule_date} {schedule_time}", "%Y-%m-%d %H:%M")
    except ValueError:
        return {"error": "Неверный формат даты или времени"}

    for i, file in enumerate(images):
        filename = file.filename
        current_dir = f"{UPLOAD_DIR}/{schedule_date}".replace("-", "_")

        if not os.path.exists(current_dir):
            os.makedirs(current_dir)

        save_path = f"{current_dir}/{filename}"

        text_ = text.replace("#", "")
        for word in get_fandom_words(db):
            text_ = text_.replace(word, "")
        text_ = text_.replace(" ", "_")

        with open(save_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        logging.info(f"Сохранено изображение: {filename}")
        if i < len(links):
            logging.info(f"Ссылка на источник: {links[i]}")
        else:
            logging.info("Ссылка на источник: (не указана)")

        db_image = Images(
            dir=text_,
            src=save_path,
            link=links[i] if i < len(links) else None
        )
        try:
            db.add(db_image)
            db.commit()
        except Exception as e:
            db.rollback()
            logging.error(f"Ошибка при сохранении изображения: {e}")

    images_ = [os.path.join(current_dir, file.filename) for file in images]

    await tg_send_post(text, images_, links_tg, schedule_time_)
    ban_words = get_ban_words(db)
    for word in ban_words:
        text = text.replace(word, "").strip()
    await vk_send_post(text, images_, links, schedule_time_)

    return {"status": "ok", "saved_files": [file.filename for file in images]}


def get_fandom_words(db: Session) -> list:
    uuid = "ffddb249-b654-4263-8d39-d3e5e97cdbe5"
    row = db.query(Storage).filter(Storage.uuid == uuid).first()
    return list(json.loads(row.data)) if row else []


def get_ban_words(db: Session) -> list:
    uuid = "2d673799-2f0d-400d-8d78-eb745ca12f93"
    row = db.query(Storage).filter(Storage.uuid == uuid).first()
    return list(json.loads(row.data)) if row else []


@router.get("/update-vk-albums")
async def update_vk_albums(db: Session = Depends(get_db)):
    return await vk_save_actual_albums(db)


def get_names_albums(name_file: str, date: str, db: Session) -> list | None:
    current_dir = f"{UPLOAD_DIR}/{date}".replace("-", "_")
    path_file = f"{current_dir}/{name_file}"
    row = db.query(Images).filter(Images.src == path_file).first()
    return str(row.dir).split("_") if row else None


def get_general_words(db: Session) -> list:
    uuid = "ee9bed86-f69f-49d3-be67-42da3e250fec"
    row = db.query(Storage).filter(Storage.uuid == uuid).first()
    return list(json.loads(row.data)) if row else []


def get_all_albums_names(db: Session) -> list | None:
    albums = db.query(VKAlbums).all()
    if not albums:
        return None
    albums_names = [album.title for album in albums]
    return albums_names


def get_albums(name_file: str, date: str, db: Session) -> list:
    res = []
    all_albums = get_all_albums_names(db)

    names = get_names_albums(name_file, date, db)
    for album in all_albums:
        for name in names:
            if name in album and album not in res:
                res.append(album)
    return res + get_general_words(db)


def get_album(name_file: str, date: str, db: Session):
    albums = get_albums(name_file, date, db)
    names = get_names_albums(name_file, date, db)
    if len(names) == 2:
        for album in albums:
            if names[0] in album and names[1] in album:
                return album, albums
    return albums[0], albums


@router.post("/get-images-for-date")
async def get_images_for_date(date: str = Form(...), db: Session = Depends(get_db)):
    date = date.replace("-", "_")
    folder_path = Path(UPLOAD_DIR) / date
    current_dir = f"{SITE_DIR}/{date}"
    if not folder_path.exists() or not folder_path.is_dir():
        raise HTTPException(status_code=404, detail="Folder not found")

    idx = 0
    images = []
    for file in folder_path.iterdir():
        if file.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}:
            idx += 1
            filename = f"{current_dir}/{file.name}"
            album, albums = get_album(file.name, date, db)

            images.append({
                "id": idx,
                "filename": filename,
                "preview_url": filename,
                "suggested_album": album,
                "available_albums": albums,
            })
    return JSONResponse(content={"images": images})


@router.post("/upload-to-vk-albums")
async def upload_to_vk_albums(items: List[UploadItem] = Body(...), db: Session = Depends(get_db)):
    if not items:
        raise HTTPException(status_code=400, detail="Empty upload list")
    return await vk_save_in_albums(items, db)
