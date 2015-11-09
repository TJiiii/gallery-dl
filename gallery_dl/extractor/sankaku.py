# -*- coding: utf-8 -*-

# Copyright 2014, 2015 Mike Fährmann
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.

"""Extract images from https://chan.sankakucomplex.com/"""

from .common import AsynchronousExtractor, Message
from .. import text
import os.path

info = {
    "category": "sankaku",
    "extractor": "SankakuExtractor",
    "directory": ["{category}", "{tags}"],
    "filename": "{category}_{id}_{md5}.{extension}",
    "pattern": [
        r"(?:https?://)?chan\.sankakucomplex\.com/\?tags=([^&]+)",
    ],
}

class SankakuExtractor(AsynchronousExtractor):

    url = "https://chan.sankakucomplex.com/"

    def __init__(self, match):
        AsynchronousExtractor.__init__(self)
        self.tags = text.unquote(match.group(1))
        self.session.headers["User-Agent"] = (
            "Mozilla/5.0 Gecko/20100101 Firefox/40.0"
        )

    def items(self):
        data = self.get_job_metadata()
        yield Message.Version, 1
        yield Message.Headers, self.session.headers
        yield Message.Directory, data
        for image in self.get_images():
            image.update(data)
            yield Message.Url, image["file-url"], image

    def get_job_metadata(self):
        """Collect metadata for extractor-job"""
        return {
            "category": info["category"],
            "tags": self.tags,
        }

    def get_images(self):
        params = {
            "tags": self.tags,
            "page": 1,
        }
        while True:
            count = 0
            page = self.request(self.url, params=params).text
            pos = text.extract(page, '<div id=more-popular-posts-link>', '')[1]
            while True:
                image_id, pos = text.extract(page,
                    '<span class="thumb blacklisted" id=p', '>', pos)
                if not image_id:
                    break
                image = self.get_image_metadata(image_id)
                count += 1
                yield image
            if count < 20:
                return
            params["page"] += 1

    def get_image_metadata(self, image_id):
        url = "https://chan.sankakucomplex.com/post/show/" + image_id
        page = self.request(url).text
        image_url, pos = text.extract(page, '<li>Original: <a href="', '"')
        width    , pos = text.extract(page, '>', 'x', pos)
        height   , pos = text.extract(page, '', ' ', pos)
        filename = text.filename_from_url(image_url)
        name, ext = os.path.splitext(filename)
        return {
            "id": image_id,
            "file-url": "https:" + image_url,
            "width": width,
            "height": height,
            "md5": name,
            "name": name,
            "extension": ext[1:],
        }
