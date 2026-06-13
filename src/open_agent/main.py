import asyncio
import threading
import webbrowser

import uvicorn

from open_agent import application

_config = uvicorn.Config(application.app, host="0.0.0.0", port=8080, workers=1, access_log=False, log_level="INFO")
_server = uvicorn.Server(_config)


def _run_server():
    _server.run()


def _close_server():
    _server.should_exit = True


async def _wait():
    await asyncio.Event().wait()


def main():
    server_thread = threading.Thread(target=_run_server, args=())
    server_thread.start()
    application.startup_event.wait()
    webbrowser.open("http://localhost:8080")
    try:
        asyncio.run(_wait())
    except KeyboardInterrupt:
        _close_server()
    server_thread.join()


if __name__ == "__main__":
    main()
