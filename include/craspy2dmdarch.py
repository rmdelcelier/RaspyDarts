#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
Raspy2DMD on a 64 bits system : its engine is protected by PyArmor, whose runtime
(pyarmor_runtime.so) is loaded inside Python. A 64 bits Python cannot load a 32 bits one :
its engine does not start. Its releases are checked before it is installed (a few parts of its
archive read, not the whole archive), and the one installed when it is started
'''

import glob
import io
import os
import platform
import re
import zipfile

RUNTIME = 'pyarmor_runtime.so'


def system_64bits():
    '''
    A 64 bits system (Raspberry Pi OS arm64)
    '''
    return platform.machine() in ('aarch64', 'arm64')


def elf_64bits(head):
    '''
    The first bytes of a library : True 64 bits, False 32 bits, None not a library
    '''
    if len(head) < 5 or head[:4] != b'\x7fELF':
        return None
    return head[4] == 2


def installed_fits(root='/Raspy2DMD'):
    '''
    Its version installed can run here : True / False ; None : no runtime found
    '''
    if not system_64bits():
        return True
    kinds = []
    for path in glob.glob(os.path.join(root, 'pyarmor_runtime_*', '**', RUNTIME), recursive=True):
        try:
            with open(path, 'rb') as file:
                kinds.append(elf_64bits(file.read(5)))
        except OSError:
            pass
    if not kinds:
        return None
    return any(kinds)


class HttpRangeFile(io.RawIOBase):
    '''
    A file on the web read by parts (HTTP Range) : enough for zipfile to read the list of an
    archive and the beginning of a file in it
    '''
    BLOCK = 256 * 1024

    def __init__(self, session, url, timeout=15):
        super().__init__()
        self.session = session
        self.timeout = timeout
        response = session.head(url, allow_redirects=True, timeout=timeout)
        response.raise_for_status()
        self.url = response.url
        self.size = int(response.headers['Content-Length'])
        self.position = 0
        self.blocks = {}

    def readable(self):
        return True

    def seekable(self):
        return True

    def tell(self):
        return self.position

    def seek(self, offset, whence=io.SEEK_SET):
        if whence == io.SEEK_SET:
            self.position = offset
        elif whence == io.SEEK_CUR:
            self.position += offset
        else:
            self.position = self.size + offset
        self.position = max(0, min(self.position, self.size))
        return self.position

    def block(self, index):
        '''
        A block of the file, downloaded once
        '''
        if index not in self.blocks:
            start = index * self.BLOCK
            end = min(start + self.BLOCK, self.size) - 1
            response = self.session.get(self.url, headers={'Range': f'bytes={start}-{end}'}, timeout=self.timeout)
            response.raise_for_status()
            if response.status_code != 206:
                raise OSError('the server does not send parts of the file')
            self.blocks[index] = response.content
        return self.blocks[index]

    def readinto(self, buffer):
        wanted = min(len(buffer), self.size - self.position)
        done = 0
        while done < wanted:
            index, offset = divmod(self.position, self.BLOCK)
            data = self.block(index)[offset:offset + wanted - done]
            if not data:
                break
            buffer[done:done + len(data)] = data
            done += len(data)
            self.position += len(data)
        return done


def release_fits(releases_url, logs=None):
    '''
    Its last release (tag vX.Y.Z.W, not a draft, as its installer chooses it) can run here :
    True / False ; None : not known (no internet, no runtime in it...)
    '''
    if not system_64bits():
        return True
    try:
        import requests    # pylint: disable=import-outside-toplevel
        session = requests.Session()
        response = session.get(releases_url, headers={'Accept': 'application/vnd.github.v3+json'}, timeout=10)
        response.raise_for_status()
        archive = None
        for release in response.json():
            if re.match(r'^v\d+\.\d+\.\d+\.\d+$', str(release.get('tag_name', ''))) and not release.get('draft'):
                archive = next((asset.get('browser_download_url') for asset in release.get('assets', [])
                                if str(asset.get('name', '')).endswith('.zip')), None)
                break
        if archive is None:
            return None
        with zipfile.ZipFile(HttpRangeFile(session, archive)) as content:
            kinds = []
            for name in content.namelist():
                if os.path.basename(name) == RUNTIME and 'pyarmor_runtime_' in name:
                    with content.open(name) as file:
                        kinds.append(elf_64bits(file.read(5)))
        if logs is not None:
            logs.info(f"Raspy2DMD : {archive} : runtimes {kinds}")
        if not kinds:
            return None
        return any(kinds)
    except Exception as error:    # pylint: disable=broad-except
        if logs is not None:
            logs.warning(f"Raspy2DMD : its release not checked for 64 bits : {error}")
        return None
