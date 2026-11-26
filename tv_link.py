"""An SSH endpoint exclusively for the paired TV. It has no Windows login or shell."""
import argparse
import asyncio
import base64
from concurrent.futures import Future
from contextlib import contextmanager
import hashlib
import hmac
import json
from pathlib import Path
import secrets
import socket
import threading
import time

import asyncssh

from app import lan_ip, write_json
from operations import maker_lock


LINK_PORT = 5022


class Pairing:
    def __init__(self, root):
        self.directory = root / ".pub-tv"
        self.state = self.directory / "pairing.json"
        self.host_key = self.directory / "host_key"

    def read(self):
        return json.loads(self.state.read_text(encoding="utf-8")) if self.state.exists() else {}

    def save(self, data):
        if not write_json(self.state, data):
            raise OSError("Could not save TV pairing")

    def issue(self):
        self.directory.mkdir(exist_ok=True)
        with maker_lock(self.directory, "pairing.lock"):
            if not self.host_key.exists():
                key = asyncssh.generate_private_key("ssh-ed25519")
                pending = self.host_key.with_suffix(".tmp")
                key.write_private_key(pending)
                pending.replace(self.host_key)
            token = secrets.token_hex(24)
            state = self.read()
            state.update(ticket=hashlib.sha256(token.encode()).hexdigest(), expires=time.time() + 86400)
            self.save(state)
        return token

    def allowed(self, username, key, consume=False):
        public = key.export_public_key().decode().strip()
        with maker_lock(self.directory, "pairing.lock"):
            state = self.read()
            if username == "tv":
                return public == state.get("player")
            if not username.startswith("pair-") or state.get("expires", 0) < time.time():
                return False
            digest = hashlib.sha256(username[5:].encode()).hexdigest()
            if not hmac.compare_digest(digest, state.get("ticket", "")):
                return False
            if consume:
                self.save({"player": public})
            return True


class CheckSession(asyncssh.SSHServerSession):
    def connection_made(self, chan):
        self.channel = chan

    def exec_requested(self, command):
        return command == "check"

    def session_started(self):
        self.channel.write("Pub Karaoke TV\n")
        self.channel.exit(0)


class TVConnection(asyncssh.SSHServer):
    def __init__(self, pairing, port):
        self.pairing = pairing
        self.port = port
        self.verified = False

    def connection_made(self, conn):
        self.connection = conn

    def public_key_auth_supported(self):
        return True

    def validate_public_key(self, username, key):
        self.username, self.key = username, key
        return key.get_algorithm() == "ssh-ed25519" and self.pairing.allowed(username, key)

    def auth_completed(self):
        # The earlier key probe is unsigned. Consume the ticket only after proof of possession.
        self.verified = self.pairing.allowed(self.username, self.key, consume=True)
        if not self.verified:
            self.connection.close()

    def session_requested(self):
        return CheckSession() if self.verified else False

    def connection_requested(self, dest_host, dest_port, orig_host, orig_port):
        return (self.verified and self.username == "tv" and dest_host == "127.0.0.1"
                and dest_port == self.port and self.pairing.allowed("tv", self.key))


async def listen(pairing, tv_port, host="", port=LINK_PORT):
    return await asyncssh.create_server(lambda: TVConnection(pairing, tv_port), host, port,
                                        server_host_keys=[str(pairing.host_key)], config=None,
                                        agent_forwarding=False, allow_pty=False, login_timeout=12)


@contextmanager
def running_link(root, port):
    pairing = Pairing(root)
    loop = asyncio.new_event_loop()
    started = Future()

    def run():
        try:
            server = loop.run_until_complete(listen(pairing, port, "0.0.0.0"))  # private venue firewall rule
            started.set_result(True)
            loop.run_forever()
            server.close()
            loop.run_until_complete(server.wait_closed())
        except Exception as exc:
            if not started.done():
                started.set_exception(exc)
            else:
                raise
        finally:
            loop.close()

    thread = threading.Thread(target=run, name="TV link", daemon=True)
    thread.start()
    started.result()
    try:
        yield
    finally:
        loop.call_soon_threadsafe(loop.stop)
        thread.join()


def make_installer(root, destination):
    pairing = Pairing(root)
    token = pairing.issue()
    settings = json.loads((root / "settings.json").read_text(encoding="utf-8-sig"))
    key = asyncssh.read_private_key(pairing.host_key)
    config = dict(host=socket.gethostname(), address=lan_ip(), ssh_port=LINK_PORT,
                  tv_port=settings.get("port", 5000), identity=key.get_fingerprint(),
                  host_key=key.export_public_key().decode().strip(), ticket=token)
    # '--' keeps the BAT portion independent of the USB drive's path and of any paired values.
    template = (root / "windows" / "laptop-bootstrap.bat").read_text(encoding="ascii")
    player = (root / "windows" / "laptop.ps1").read_bytes()
    encoded = [base64.b64encode(data).decode() for data in (player, json.dumps(config).encode())]
    pending = destination.with_suffix(".tmp")
    pending.write_text(template.rstrip() + "\n" + "\n".join(encoded) + "\n", encoding="ascii", newline="\r\n")
    pending.replace(destination)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create the pub's single-use TV installer")
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    make_installer(Path(__file__).resolve().parent, args.destination)
