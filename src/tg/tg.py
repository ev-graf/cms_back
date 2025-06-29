from datetime import datetime

from pyrogram.types import InputMediaPhoto

from src import tg_app, TG_CHANNEL


async def tg_send_post(text: str, image_paths: list[str], links: list[str], schedule_time: datetime):
    caption = (text or "").strip()
    sources = []

    for i, link in enumerate(links):
        if l := link.strip():
            sources.append(f"[Source]({l})" if len(links) == 1 else f"[S{i + 1}]({l})")

    if sources:
        caption += "\n" + " ".join(sources)

    async with tg_app:
        if len(image_paths) == 1:
            with open(image_paths[0], "rb") as photo:
                await tg_app.send_photo(
                    chat_id=TG_CHANNEL,
                    photo=photo,
                    caption=caption,
                    schedule_date=schedule_time,
                )

        elif len(image_paths) > 1:
            files = [open(path, "rb") for path in image_paths]

            try:
                media = [InputMediaPhoto(media=f, caption=caption if i == 0 else None) for i, f in enumerate(files)]

                await tg_app.send_media_group(
                    chat_id=TG_CHANNEL,
                    media=media,
                    schedule_date=schedule_time,
                )
            finally:
                for f in files:
                    f.close()
