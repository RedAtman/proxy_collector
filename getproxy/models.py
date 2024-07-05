from __future__ import annotations

from dataclasses import dataclass, field
import logging
from typing import List


# from typing_extensions import Unpack


logger = logging.getLogger()


@dataclass
class Proxy:
    type: str = field(default_factory=str)
    host: str = field(default_factory=str)
    port: int = field(default_factory=int)
    export_address: List[str] = field(default_factory=list)
    anonymity: str = field(default_factory=str)
    country: str = field(default_factory=str)
    country_zh: str = field(default_factory=str)
    response_time: float = field(default_factory=float)
    source: str = field(default_factory=str)
    validate: bool = field(default_factory=bool)

    @property
    def hash(self):
        return "%s://%s:%s" % (self.type, self.host, self.port)

    # def __new__(cls, id: str = "", **kwargs):
    #     if not id:
    #         id = uuid4().hex

    #     if id not in Note.mapper_id_note:
    #         instance = super().__new__(cls)
    #         Note.mapper_id_note[id] = instance
    #         return instance
    #     instance = Note.mapper_id_note[id]
    #     # kwargs["_content"] = getattr(instance, "_content", "")
    #     kwargs["_filename"] = getattr(instance, "_filename", "")
    #     # kwargs["_filepath"] = getattr(instance, "_filepath", "")
    #     logger.info((getattr(instance, "_filename", "")))
    #     logger.info((instance, kwargs))
    #     instance.__dict__.update(kwargs)
    #     logger.info((instance, kwargs))
    #     return instance

    # def _add_extra_fields(self):
    #     self.modifydate = self.d.modificationDate
    #     self.createdate = self.d.creationDate
    #     self.systemtags = self.d.systemTags
    #     _content = self._content
    #     logger.info((id(self), self))
    #     self._content = self.d.content
    #     # if _content != self.d.content:
    #     #     _ = self.filepath
    #     logger.info((id(self), self))

    # def __post_init__(self):
    #     if isinstance(self.d, dict):
    #         d = _Note(**self.d)
    #         self.d = d
    #     self._add_extra_fields()


if __name__ == "__main__":
    proxy = Proxy()
    print(proxy)
    print(proxy.__dict__)
