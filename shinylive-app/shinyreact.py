# shiny-react utility functions for Python (Shinylive version)
# License: MIT 2025, Posit Software, PBC

from __future__ import annotations

from shiny import ui, Session
from shiny.html_dependencies import shiny_deps
from shiny.types import Jsonifiable
from shiny.render.renderer import Renderer, ValueFn
from shiny.module import resolve_id
from typing import Any, Mapping, Optional, Sequence, Union


def page_bare(*args: ui.TagChild, title: str | None = None, lang: str = "en") -> ui.Tag:
    return ui.tags.html(
        ui.tags.head(ui.tags.title(title)),
        ui.tags.body(shiny_deps(False), *args),
        lang=lang,
    )


def page_react(
    *args: ui.TagChild,
    title: str | None = None,
    js_file: str | None = "main.js",
    css_file: str | None = "main.css",
    lang: str = "en",
) -> ui.Tag:
    head_items: list[ui.TagChild] = []
    if js_file:
        head_items.append(ui.tags.script(src=js_file, type="module"))
    if css_file:
        head_items.append(ui.tags.link(href=css_file, rel="stylesheet"))

    return page_bare(
        ui.head_content(*head_items),
        ui.div(id="root"),
        *args,
        title=title,
        lang=lang,
    )


class render_json(Renderer[Jsonifiable]):
    def __init__(self, _fn: Optional[ValueFn[Any]] = None) -> None:
        super().__init__(_fn)

    async def transform(self, value: Jsonifiable) -> Jsonifiable:
        return value


JsonifiableIn = Union[str, int, float, bool, None, Sequence["JsonifiableIn"], "JsonifiableMapping"]
JsonifiableMapping = Mapping[str, JsonifiableIn]


async def post_message(session: Session, type: str, data: JsonifiableIn):
    namespaced_type = resolve_id(type)
    await session.send_custom_message(
        "shinyReactMessage", {"type": namespaced_type, "data": data}
    )
