import os
import pathlib
import sys

import uvicorn

# 启动服务
if __name__ == "__main__":
    src_dir = str(pathlib.Path(__file__).parent)
    project_dir = str(pathlib.Path(__file__).parent.parent)
    os.chdir(project_dir)
    if src_dir not in sys.path:
        sys.path.append(src_dir)
    uvicorn.run("open_agent.application:app", host="localhost", port=8080, workers=1, access_log=False)
