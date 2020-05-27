__all__ = ["setup_logging", "run", "main"]
import os
import sys
import argparse
import json
from aiohttp import web
import asyncio
import websockets
import logging
from aiotesttoolkit_remoteviewer.app import Application
from aiotesttoolkit_remoteviewer import configuration
sys.path.append("C:/Users/jeremy/Documents/Projects/aiotesttoolkit")
import aiotesttoolkit
from aiotesttoolkit import reporting


def setup_logging(
    *,
    access_logfile=None,
    access_maxbytes=None,
    access_backupcount=None,
    error_logfile=None,
    error_maxbytes=None,
    error_backupcount=None
):
    """Setup logging handlers.

    This setup two `RotatingFileHandler` for `aiohttp.access` and `aiohttp.server` logs.

    :param access_logfile: path for access logfile or `None`
    :param access_maxbytes: max bytes per access logfile
    :param access_backupcount: max number of access logfile to keep
    :param error_logfile: path for error logfile or `None`
    :param error_maxbytes: max bytes per error logfile
    :param error_backupcount: max number of error logfile to keep
    """
    from logging.handlers import RotatingFileHandler

    if access_logfile:
        logging.getLogger("aiohttp.access").addHandler(
            RotatingFileHandler(
                access_logfile,
                maxBytes=access_maxbytes,
                backupCount=access_backupcount,
            )
        )
    if error_logfile:
        logging.getLogger("aiohttp.server").addHandler(
            RotatingFileHandler(
                error_logfile, maxBytes=error_maxbytes, backupCount=error_backupcount,
            )
        )


def run(*, base_url: str, port: int, jinja2_templates_dir:str, static_dir:str, master:dict):
    clients = []

    async def handle_client(websocket, path):
        clients.append(websocket)
        while True:
            await asyncio.sleep(0)

    async def handle_stat(stat):
        for _ in clients:
            await _.send(json.dumps(stat))

    reporter = reporting.MasterReporter("0.0.0.0", 8081, handle_stat=handle_stat)
    asyncio.get_event_loop().run_until_complete(reporter.start())
    socket = asyncio.get_event_loop().run_until_complete(websockets.serve(handle_client, "0.0.0.0", 8082))
    print(socket)
    app = Application(base_url=base_url, jinja2_templates_dir=jinja2_templates_dir, static_dir=static_dir)
    web.run_app(app, port=port)


def main(argv=None):
    parser = argparse.ArgumentParser(prog="Service", description="Help")
    parser.add_argument("directory", type=str, help="config directory")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbosity level")
    args = parser.parse_args(args=argv)

    config_dir = args.directory
    if not os.path.isdir(config_dir):
        raise NotADirectoryError(config_dir)

    config = configuration.load(os.path.join(config_dir, "config.cnf"))

    logging.basicConfig(level=logging.INFO)

    setup_logging(
        access_logfile=config["logging"].get("access-logfile", None),
        access_maxbytes=int(config["logging"].get("access-maxbytes", None)),
        access_backupcount=int(config["logging"].get("access-backupcount", None)),
        error_logfile=config["logging"].get("error-logfile", None),
        error_maxbytes=int(config["logging"].get("error-maxbytes", None)),
        error_backupcount=int(config["logging"].get("error-backupcount", None)),
    )

    run(
        base_url=config["service"]["base-url"],
        port=int(config["service"]["port"]),
        jinja2_templates_dir=config["service"]["jinja2-templates-dir"],
        static_dir=config["service"]["static_dir"],
        master={
            "host": config["master"]["host"],
            "port": int(config["master"]["port"])
        }
    )


if __name__ == "__main__":
    main(sys.argv)