import logging
logger = logging.getLogger(__name__)

from pylatexenc.macrospec import MacroSpec, EnvironmentSpec, MacroStandardArgsParser
from pylatexenc.latexwalker import LatexMacroNode, LatexEnvironmentNode


class MacroSubstHelper:
    def __init__(self,
                 macros={},
                 environments={},
                 argspecfldname='argspec',
                 args_parser_class=MacroStandardArgsParser,
                 context={}):
        self.macros = macros
        self.environments = environments

        self.argspecfldname = argspecfldname
        self.args_parser_class = args_parser_class

        self.context = context # additional fields provided to repl text

    def get_specs(self):
        return dict(
            macros=[
                MacroSpec(m, args_parser=self.args_parser_class(mconfig[self.argspecfldname]))
                for m, mconfig in self.macros.items()
                if not isinstance(mconfig, str) and self.argspecfldname in mconfig
            ],
            environments=[
                EnvironmentSpec(e, args_parser=self.args_parser_class(mconfig[self.argspecfldname]))
                for e, econfig in self.environments.items()
                if not isinstance(econfig, str) and self.argspecfldname in econfig
            ]
        )

    def get_macro_cfg(self, macroname):
        return self.macros.get(macroname, None)

    def get_environment_cfg(self, environmentname):
        return self.environments.get(environmentname, None)

    def get_node_cfg(self, n):
        if n is None:
            return None
        if n.isNodeType(LatexMacroNode):
            return self.get_macro_cfg(n.macroname)
        if n.isNodeType(LatexEnvironmentNode):
            return self.get_environment_cfg(n.environmentname)


    def eval_subst(self, c, n, lpp, *, argoffset=0, context={}):
        """
        If `argoffset` is nonzero, then the first `argoffset` arguments are skipped
        and the arguments `argoffset+1, argoffset+2, ...` are exposed to the
        replacement string as `%(1)s, %(2)s, ...`.
        """
        if isinstance(c, str):
            repl = c
        else:
            repl = c.get('repl')
            
        q = dict(self.context)

        q.update(dict(
                (str(1+k), v)
                for k, v in enumerate(
                        lpp.latexpp_group_contents(n) if n is not None else ''
                        for n in n.nodeargd.argnlist[argoffset:]
                )
            ))

        if n.isNodeType(LatexMacroNode):
            q.update(macroname=n.macroname)
        if n.isNodeType(LatexEnvironmentNode):
            q.update(environmentname=n.environmentname,
                     body=lpp.latexpp(n.nodelist))
        
        q.update(context)

        text = repl % q
        #logger.debug("Performing substitution %s -> %s", n.latex_verbatim(), text)
        return text