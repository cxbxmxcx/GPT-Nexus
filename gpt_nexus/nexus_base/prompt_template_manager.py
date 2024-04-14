from typing import List

import yaml
from lark import Lark, Token, Transformer, Tree, v_args

from gpt_nexus.nexus_base.chat_models import PromptTemplate, db


class TemplateTransformer(Transformer):
    def __init__(self, parser, context, agent, helpers=None, manager=None):
        self.parser = parser
        self.context = context
        self.agent = agent
        self.manager = manager

    # @v_args(inline=True)
    # def variable(self, token):
    #     value = self.context.get(str(token), "")
    #     return value
    @v_args(inline=True)
    def variable(self, items):
        if isinstance(items, list):
            name = items[0].value
        elif isinstance(items, str):
            name = items
        value = self.context.get(name, "")
        #     print(f"Variable '{name}': {value}")
        return value

    # @v_args(inline=True)
    # def partial(self, items):
    #     partial_template = self.get_prompt_template(partial_name)
    #     partial_result = ""
    #     if partial_template:
    #         partial_result = self.execute_template(
    #             self.agent,
    #             partial_template.content,
    #             self.context,
    #             partial_template.outputs,
    #             partial_execution=True,
    #         )
    #     return partial_result

    @v_args(inline=True)
    def partial(self, *items):
        name = items[0].value
        args = items[1:]
        # Process arguments for partials
        processed_args = [self.transform(arg) for arg in args]
        # Convert all elements to strings
        args_str = "".join(self.convert_to_string(arg) for arg in processed_args)

        partial_template = self.manager.get_prompt_template(name)

        if partial_template:
            partial_result = self.manager.execute_template(
                self.agent,
                partial_template.content,
                self.context,
                partial_template.outputs,
                partial_execution=True,
            )
        return partial_result
        # print(f"Partial '{name}' with args: {args_str}")
        # return f"<Partial: {name} Args: {args_str}>"

    # @v_args(inline=True)
    # def helper(self, token, *args):
    #     # Placeholder for helper function logic
    #     return f"<Helper: {token} - Args: {args}>"

    @v_args(inline=True)
    def helper(self, items):
        name = items[0].value
        args = items[1:]
        # Process arguments for helpers
        processed_args = [self.transform(self.parser.parse(arg)) for arg in args]
        # Convert all elements to strings
        args_str = "".join(self.convert_to_string(arg) for arg in processed_args)
        print(f"Helper '{name}' with args: {args_str}")
        return f"<Helper: {name} Args: {args_str}>"

    # def if_statement(self, items):
    #     condition = str(items[0])
    #     content = items[1:]
    #     if self.context.get(condition, False):
    #         result = "".join(self.transform(self.parser.parse(c)) for c in content)
    #         return result
    #     return ""

    def if_statement(self, items):
        args = items[0]
        content = items[1:]
        processed_args = [self.transform(self.parser.parse(arg)) for arg in args]
        condition = processed_args[0]

        print(f"If statement with condition '{condition}'")
        if self.context.get(condition, False):
            result = "".join(self.transform(c) for c in content)
            return result
        return ""

    def loop_statement(self, items):
        var_name = items[0].value
        content = items[1:]
        print(f"Loop statement for '{var_name}'")
        output = ""
        collection = self.context.get(var_name, [])
        for item in collection:
            loop_context = {**self.context, **item}
            output += "".join(self.transform(self.parser.parse(c)) for c in content)
        return output

    @v_args(inline=True)
    def text(self, items):
        text_value = "".join(items)
        print(f"Text: {text_value}")
        return text_value

    @v_args(inline=True)
    def template(self, *items):
        if isinstance(items, str):
            return items
        if isinstance(items, list) or isinstance(items, tuple):
            return "".join(items)
        result = "".join(self.transform(self.parser.parse(c)) for c in items)
        print(f"Template result: {result}")
        return result

    def convert_to_string(self, item):
        if isinstance(item, Tree):
            return "".join(self.convert_to_string(child) for child in item.children)
        elif isinstance(item, Token):
            return str(item)
        else:
            return str(item)


class PromptTemplateManager:
    def __init__(self, nexus):
        self.nexus = nexus
        self.parser = self.init_template_parser()

    def init_template_parser(self):
        template_grammar = """
        ?start: template

        ?template: (text | variable | partial | helper | if_statement | loop_statement)*

        variable: "{{" VAR "}}"
        partial: "{{>" VAR "}}" template "{{/" VAR "}}"
        helper: "{{#" VAR "}}" template "{{/" VAR "}}"
        if_statement: "{{#if" VAR "}}" template "{{/if}}"
        loop_statement: "{{#each" VAR "}}" template "{{/each}}"

        VAR: /[a-zA-Z_][a-zA-Z0-9_]*/
        text: /[^{}]+/

        %ignore " "
        
        """

        template_grammar = """
        ?start: template

        template: (text | variable | partial | helper | if_statement | loop_statement)*

        text: /[^{{]+/

        variable: "{{" VAR "}}"
        partial: "{{>" VAR partial_args "}}"
        partial_args: (variable | text)*
        helper: "{{#" VAR helper_args "}}"
        helper_args: (variable | text)*
        if_statement: "{{#if" if_args "}}" template "{{/if}}"
        if_args: (variable | text)*
        loop_statement: "{{#each" VAR "}}" template "{{/each}}"

        %import common.CNAME -> VAR
        %import common.WS_INLINE
        %ignore WS_INLINE
        """
        template_grammar = """        
        ?start: template

        template: (text | variable | partial | helper | if_statement | loop_statement)*

        text: /[^\\{\\}]+/

        variable: "{{" VAR "}}"
        partial: "{{>" VAR partial_args "}}"
        partial_args: (variable | text)*
        helper: "{{#" VAR helper_args "}}"
        helper_args: (variable | text)*
        if_statement: "{{#if" if_args "}}" template "{{/if}}"
        if_args: (variable | text)*
        loop_statement: "{{#each" VAR "}}" template "{{/each}}"

        %import common.CNAME -> VAR
        %import common.WS_INLINE
        %ignore WS_INLINE
        """
        return Lark(template_grammar, start="start")

    def add_prompt_template(
        self, template_name, template_content, template_inputs, template_outputs
    ):
        if isinstance(template_inputs, List):
            template_inputs = ",".join(template_inputs)
        if isinstance(template_outputs, List):
            template_outputs = ",".join(template_outputs)
        with db.atomic():
            if (
                PromptTemplate.select()
                .where(PromptTemplate.name == template_name)
                .exists()
            ):
                raise ValueError("Template name already exists")
            PromptTemplate.create(
                name=template_name,
                content=template_content,
                inputs=template_inputs,
                outputs=template_outputs,
            )
            print(f"Prompt template '{template_name}' added.")
            return True

    def get_prompt_template(self, template_name):
        try:
            return PromptTemplate.get(PromptTemplate.name == template_name)
        except PromptTemplate.DoesNotExist:
            return None

    def update_prompt_template(
        self, template_name, template_content, template_inputs, template_outputs
    ):
        if isinstance(template_inputs, List):
            template_inputs = ",".join(template_inputs)
        if isinstance(template_outputs, List):
            template_outputs = ",".join(template_outputs)
        with db.atomic():
            template = PromptTemplate.get(PromptTemplate.name == template_name)
            template.content = template_content
            template.inputs = template_inputs
            template.outputs = template_outputs
            template.save()
            print(f"Prompt template '{template_name}' updated.")
            return True

    def delete_prompt_template(self, template_name):
        with db.atomic():
            query = PromptTemplate.delete().where(PromptTemplate.name == template_name)
            return query.execute()

    def get_prompt_template_names(self):
        return [template.name for template in PromptTemplate.select()]

    def _extract_set_variables(self, template_data, invars):
        variables = {}
        for key, value in template_data.items():
            if key == "template" or key == "type":
                continue
            if isinstance(value, str):
                variables[key] = value
            elif isinstance(value, dict):
                variables[key] = invars.get(key, value.get("default", ""))
        return variables

    def execute_template(
        self, agent, content, inputs, outputs, partial_execution=False
    ):
        nexus = self.nexus

        template_data = yaml.safe_load(content)

        # ttype = template_data.get("type", "prompt")  # prompt, function/action, semantic
        tinputs = template_data.get("inputs", {})
        toutputs = template_data.get("outputs", {})
        thelpers = template_data.get("helpers", {})

        einputs = self._extract_set_variables(tinputs, inputs)

        helpers = {}
        for name, code in thelpers.items():
            exec(code, locals())  # load the helper functions into the locals namespace
            helpers[name] = locals()[
                f"{name}"
            ]  # add the helper function to the helpers dictionary

        input_prompt = tinputs.get("template", "")
        outputs = {}
        iprompt = None
        oprompt = None
        result = None

        if input_prompt:
            # iprompt = self._execute_partials(input_prompt, agent, einputs)

            # compiler = Compiler()
            # template = compiler.compile(iprompt)
            # iprompt = template(einputs, helpers=helpers)
            parsed_tree = self.parser.parse(input_prompt)

            # Transform the parsed tree
            transformer = TemplateTransformer(
                self.parser,
                einputs,
                agent,
                helpers=helpers,
                manager=self,
            )
            iprompt = transformer.transform(parsed_tree)

            if tinputs.get("type") == "prompt":
                output = agent.get_semantic_response(agent.profile.persona, iprompt)
                outputs["output"] = output
            elif tinputs.get("type") == "function":
                outputs["output"] = iprompt
            else:
                outputs["output"] = iprompt
            result = outputs["output"]

        eoutputs = self._extract_set_variables(toutputs, outputs)
        output_prompt = toutputs.get("template", "")
        if output_prompt and eoutputs:
            # oprompt = self._execute_partials(output_prompt, agent, eoutputs)

            parsed_tree = self.parser.parse(output_prompt)

            # Transform the parsed tree
            transformer = TemplateTransformer(
                self.parser,
                eoutputs,
                agent,
                helpers=helpers,
                manager=self,
            )
            oprompt = transformer.transform(parsed_tree)

            if toutputs.get("type") == "prompt":
                result = agent.get_semantic_response(agent.profile.persona, oprompt)
            elif toutputs.get("type") == "function":
                result = oprompt
            else:
                result = oprompt

        if partial_execution:
            return result
        return iprompt, oprompt, result
