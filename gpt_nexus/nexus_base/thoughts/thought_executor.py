from lark import Lark

from gpt_nexus.nexus_base.thoughts.template_tranformer import ThoughtTemplateTransformer


class ThoughtExecutor:
    def __init__(self):
        self.parser = self.init_template_parser()

    def init_template_parser(self):
        template_grammar = """        
            ?start: template

            template: (text | variable | partial | helper | start_lone_brace | end_lone_brace | lone_double_brace)*

            text: /[^\\{\\}]+/
            start_lone_brace: "{" 
            end_lone_brace: "}"  // Rule to handle single braces
            lone_double_brace: "}}" // Rule to handle lone closing double braces

            variable: "{{" VAR "}}"
            partial: "{{>" VAR partial_args "}}"
            partial_args: (variable | text)*
            helper: "{{#" VAR helper_args "}}"
            helper_args: (variable | text)*        

            %import common.CNAME -> VAR
           
        """
        return Lark(
            template_grammar,
            start="start",
            parser="lalr",
        )

    def execute_action(self, action, context):
        parsed_tree = self.parser.parse(action)

        # Transform the parsed tree
        transformer = ThoughtTemplateTransformer(
            context,
        )
        action = transformer.transform(parsed_tree)

        print(action)
