import logging

from jinja2 import Template as JinjaTemplate
from jinja2 import Environment, select_autoescape
from jinja2 import DictLoader, TemplateNotFound


class AssetContentMapping:
    def __init__(self, assets):
        self.assets = assets
    def __getitem__(self, name):
        return self.assets[name].content.decode('utf-8')
    def __contains__(self, name):
        return name in self.assets



def render_jinja(assets, tpl_name, **tpl_parms):

    env = Environment(
        loader = DictLoader(AssetContentMapping(assets)),
        autoescape=select_autoescape(['html', 'xml'])
    )
    tpl = env.get_template(tpl_name)
    return tpl.render(**tpl_parms)

