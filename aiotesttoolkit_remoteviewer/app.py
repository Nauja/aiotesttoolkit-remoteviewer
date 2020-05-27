import json
from aiohttp import web
import aiohttp_cors
import aiohttp_jinja2
import jinja2
from typing import Callable, Any, List


def validate_required_params(_fun=None, *, names):
    """Validate that a query has all required parameters.

    Role of this decorator is to force returning a `web.HTTPForbidden`
    with an explicit message when one of required query parameters
    is missing.

    This will call the wrapped function with a dict containing
    all required parameters values.

    :param names: list of required parameters
    :return: result of wrapped function or `web.HTTPForbidden`
    """

    def wrapper(fun):
        async def run(self: web.View, *args, **kwargs):
            # Note that `self` is a `web.View` object.
            query = self.request.rel_url.query
            # Decode POST parameters
            if self.request.body_exists and self.request.content_type.endswith("json"):
                data = await self.request.json()
            else:
                data = {}
            # Check and get all parameters
            vals = {}
            for name in names:
                val = data.get(name, None) or query.get(name, None)
                if not val:
                    raise web.HTTPForbidden(
                        reason="{} parameter is required".format(name)
                    )
                vals[name] = val
            # Forward parameters to wrapped functions
            return await fun(self, *args, required_params=vals, **kwargs)

        return run

    return wrapper if not _fun else wrapper(_fun)


def IndexView() -> web.View:
    class Wrapper(web.View):
        @aiohttp_jinja2.template('index.html')
        async def get(self, **_):
            return {}

    return Wrapper


def Application(
    *args, jinja2_templates_dir: str, static_dir:str, base_url: str = None, **kwargs
):
    app = web.Application(*args, **kwargs)

    aiohttp_jinja2.setup(
        app,
        loader=jinja2.FileSystemLoader(jinja2_templates_dir)
    )

    base_url = base_url or "/"
    if base_url[-1] != '/':
        base_url += '/'

    cors = aiohttp_cors.setup(app, defaults={
        "allow_cors_origin": aiohttp_cors.ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*",
        )
    })
    
    cors.add(app.router.add_static(base_url + "static", static_dir))

    app.router.add_view(base_url, IndexView())

    return app
