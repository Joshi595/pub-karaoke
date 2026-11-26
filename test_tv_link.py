"""The paired TV link: a one-time ticket pairs one laptop key, which may then reach the TV port and nothing else."""
import asyncio

import asyncssh
import pytest

from tv_link import Pairing, listen


def test_pairing_then_tv_port_only(tmp_path):
    async def scenario():
        echo = await asyncio.start_server(lambda r, w: w.write(b"karaoke"), "127.0.0.1", 0)
        tv_port = echo.sockets[0].getsockname()[1]
        pairing = Pairing(tmp_path)
        ticket = pairing.issue()
        server = await listen(pairing, tv_port, "127.0.0.1", 0)
        port = server.sockets[0].getsockname()[1]
        laptop, stranger = (asyncssh.generate_private_key("ssh-ed25519") for _ in range(2))
        pinned = asyncssh.import_known_hosts(
            "[127.0.0.1]:%d %s" % (port, asyncssh.read_private_key(pairing.host_key).export_public_key().decode()))

        def connect(user, key):
            return asyncssh.connect("127.0.0.1", port, username=user, client_keys=[key], known_hosts=pinned,
                                    agent_path=None, config=None)

        with pytest.raises(asyncssh.PermissionDenied):
            await connect("tv", laptop)  # not paired yet
        async with connect("pair-" + ticket, laptop) as conn:
            assert (await conn.run("check")).stdout == "Pub Karaoke TV\n"
        with pytest.raises(asyncssh.PermissionDenied):
            await connect("pair-" + ticket, stranger)  # the ticket works once
        with pytest.raises(asyncssh.PermissionDenied):
            await connect("tv", stranger)
        async with connect("tv", laptop) as conn:
            reader, _ = await conn.open_connection("127.0.0.1", tv_port)
            assert await reader.read(7) == b"karaoke"
            with pytest.raises(asyncssh.ChannelOpenError):
                await conn.open_connection("127.0.0.1", tv_port + 1)
        server.close(); echo.close()

    asyncio.run(scenario())
