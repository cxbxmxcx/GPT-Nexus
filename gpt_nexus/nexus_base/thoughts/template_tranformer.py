from lark import Token, Transformer, Tree, v_args


class ThoughtTemplateTransformer(Transformer):
    # def __init__(self, parser, context, agent, helpers=None, manager=None):
    #     self.parser = parser
    #     self.context = context
    #     self.agent = agent
    #     self.manager = manager
    #     self.helpers = helpers
    def __init__(self, context):
        self.context = context

    @v_args(inline=True)
    def variable(self, items):
        if isinstance(items, list):
            name = items[0].value
        elif isinstance(items, str):
            name = items
        value = self.context.get(name, "")
        #     print(f"Variable '{name}': {value}")
        return value

    def VAR(self, items):
        if isinstance(items, list):
            name = items[0].value
        elif isinstance(items, str):
            name = items
        return name

    @v_args(inline=True)
    def partial(self, *items):
        name = items[0].value
        args = items[1:]
        # Process arguments for partials
        processed_args = [self.transform(arg) for arg in args]

        # Convert all elements to strings
        args_str = "".join(self.convert_to_string(arg) for arg in processed_args)
        if "," in args_str:
            args_str = args_str.split(",")
        elif " " in args_str:
            args_str = args_str.split(" ")
        else:
            args_str = [args_str]

        args = {}
        for arg in args_str:
            if isinstance(arg, str):
                earg = self.context.get(arg, "")
                if earg:
                    args[arg] = earg

        partial_template = self.manager.get_thought_template(name)

        if partial_template:
            partial_result = self.manager.execute_template(
                self.agent,
                partial_template.content,
                self.context,
                None,
                partial_execution=True,
            )
        return partial_result

    @v_args(inline=True)
    def helper(self, *items):
        name = items[0].value
        if name not in self.helpers:
            print(f"Helper '{name}' not found")
            return ""

        args = items[1:]
        # Process arguments for helpers
        processed_args = [self.transform(arg) for arg in args]

        # Convert all elements to strings
        args_str = "".join(self.convert_to_string(arg) for arg in processed_args)
        if "," in args_str:
            args_str = args_str.split(",")
        elif " " in args_str:
            args_str = args_str.split(" ")
        else:
            args_str = [args_str]

        args = []
        for arg in args_str:
            if isinstance(arg, str):
                earg = self.context.get(arg, "")
                if earg:
                    args.append(earg)

        helper_func = self.helpers[name]
        result = helper_func(*args)
        print(f"Helper '{name}' with args: {args}, result: {result}")
        return result

    @v_args(inline=True)
    def start_lone_brace(self, *items):
        return "{"

    @v_args(inline=True)
    def end_lone_brace(self, *items):
        return "}"

    @v_args(inline=True)
    def lone_double_brace(self, *items):
        return "}}"

    @v_args(inline=True)
    def text(self, items):
        text_value = "".join(items)
        # print(f"Text: {text_value}")
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
