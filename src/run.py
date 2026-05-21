import uvicorn
import webview

from open_agent.application import app

config = uvicorn.Config(app, host="localhost", port=8080, workers=1, access_log=False, log_level="info")
server = uvicorn.Server(config)


def run_uvicorn():
    server.run()


def close_uvicorn():
    server.should_exit = True


if __name__ == "__main__":
    window = webview.create_window('OpenAgent', "http://localhost:8080/", maximized=True)
    window.events.closed += close_uvicorn
    webview.start(run_uvicorn)
