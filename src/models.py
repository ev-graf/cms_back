from pydantic import BaseModel
from sqlalchemy import Column, Integer, String

from src import Base


class Storage(Base):
    __tablename__ = "storage"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    uuid = Column(String, unique=True, nullable=False)
    data = Column(String, nullable=False)


class Images(Base):
    __tablename__ = "images"

    id = Column(Integer, primary_key=True, index=True)
    dir = Column(String)
    src = Column(String)
    link = Column(String)


class Authors(Base):
    __tablename__ = "authors"

    id = Column(Integer, primary_key=True, index=True)
    nickname = Column(String)


class SocialPlatforms(Base):
    __tablename__ = "social_platforms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)


class AuthorLinks(Base):
    __tablename__ = "author_links"

    id = Column(Integer, primary_key=True, index=True)
    author_id = Column(Integer)
    platform_id = Column(Integer)
    url = Column(String)


class VKAlbums(Base):
    __tablename__ = "vk_albums"

    id = Column(Integer, primary_key=True, index=True)
    album_id = Column(Integer, unique=True, index=True)
    title = Column(String, index=True)
    size = Column(Integer)
    created = Column(Integer)


class UploadItem(BaseModel):
    filename: str
    album: str
    date: str
