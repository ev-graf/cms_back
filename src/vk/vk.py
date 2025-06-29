import asyncio
import os
from datetime import datetime
from typing import List

from fastapi import HTTPException
from requests import request
from sqlalchemy.orm import Session

from src import vk_app, VK_GROUP_ID, UPLOAD_DIR, SITE_DIR
from src.models import VKAlbums, Images, UploadItem
from src.parsers.parser import get_author_url


async def vk_send_post(text: str, image_paths: list[str], links: list[str], schedule_time: datetime):
    async def upload_one(idx: int, img_path: str) -> str:
        def _sync_upload() -> str:
            upload_url = vk_app.photos.getWallUploadServer(group_id=VK_GROUP_ID)["upload_url"]

            with open(img_path, "rb") as f:
                upl_resp = request(method="POST", url=upload_url, files={"photo": f}).json()

            save = vk_app.photos.saveWallPhoto(
                group_id=int(VK_GROUP_ID),
                photo=upl_resp["photo"],
                server=upl_resp["server"],
                hash=upl_resp["hash"],
                caption=links[idx].strip() if idx < len(links) and links[idx].strip() else None,
            )[0]

            return f"photo{save['owner_id']}_{save['id']}"

        return await asyncio.to_thread(_sync_upload)

    sem = asyncio.Semaphore(5)

    async def bounded_upload(i, p):
        async with sem:
            return await upload_one(i, p)

    attachments = await asyncio.gather(*(bounded_upload(i, path) for i, path in enumerate(image_paths)))

    def _sync_post():
        vk_app.wall.post(
            owner_id=-int(VK_GROUP_ID),  # «минус» — публикация от имени сообщества
            from_group=1,
            message=(text or "").strip(),
            attachments=",".join(attachments),
            publish_date=int(schedule_time.timestamp()),
        )

    await asyncio.to_thread(_sync_post)


async def vk_save_actual_albums(db: Session):
    def _sync_job():
        try:
            albums = vk_app.photos.getAlbums(
                owner_id=-int(VK_GROUP_ID),
                need_covers=0,
                photo_sizes=0,
            )["items"]

            db.query(VKAlbums).delete()

            for album in albums:
                db.add(
                    VKAlbums(
                        album_id=album["id"],
                        title=album["title"],
                        size=album["size"],
                        created=album["created"],
                    )
                )
            db.commit()
            return {"status": "ok", "count": len(albums)}

        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Ошибка VK API: {str(e)}")

    return await asyncio.to_thread(_sync_job)


def sync_vk_upload(album_id: int, image_path: str, caption: str):
    upload_url = vk_app.photos.getUploadServer(
        album_id=album_id,
        group_id=int(VK_GROUP_ID)
    )["upload_url"]

    with open(image_path, "rb") as img:
        upload_response = request("POST", upload_url, files={"file1": img}).json()

    saved = vk_app.photos.save(
        album_id=album_id,
        group_id=int(VK_GROUP_ID),
        server=upload_response["server"],
        photos_list=upload_response["photos_list"],
        hash=upload_response["hash"],
        caption=caption
    )[0]

    return saved["id"]


def get_caption(image_path: str, db: Session):
    row = db.query(Images).filter(Images.src == image_path).first()
    if not row:
        return "l\n\na"
    link = row.link or "l"
    author = get_author_url(link) or "a"
    return f"{link}\n\n{author}"


def get_album_id_cached(title: str, db: Session, cache: dict) -> int:
    if title in cache:
        return cache[title]
    album = db.query(VKAlbums).filter(VKAlbums.title == title).first()
    if not album:
        raise ValueError(f"Album {title} not found")
    cache[title] = album.album_id
    return cache[title]


async def vk_save_in_albums(items: List[UploadItem], db: Session):
    album_cache: dict[str, int] = {}

    async def process(item: UploadItem):
        image_path = str(item.filename).replace(SITE_DIR, UPLOAD_DIR)
        if not os.path.isfile(image_path):
            return {"filename": item.filename, "status": "error", "detail": "File not found"}

        try:
            album_id = get_album_id_cached(item.album, db, album_cache)
            caption = get_caption(image_path, db)
            photo_id = await asyncio.to_thread(sync_vk_upload, album_id, image_path, caption)
            return {"filename": item.filename, "status": "ok", "photo_id": photo_id}
        except Exception as e:
            return {"filename": item.filename, "status": "error", "detail": str(e)}

    sem = asyncio.Semaphore(5)

    async def bounded(item):
        async with sem:
            return await process(item)

    results = await asyncio.gather(*(bounded(i) for i in items))
    return {"results": results}
