import os
import re

class CorlanTemplateEngine:
    def __init__(self, template_folder="public", cache_templates=True):
        self.template_folder = template_folder
        self.blocks = {}
        self.macros = {}
        self.filters = {}
        self.environment = {}
        self.global_context = {}
        self.template_cache = {} if cache_templates else None

    def render(self, template_name, context=None):
        if context is None:
            context = {}

        if not os.path.exists(self.template_folder):
            raise FileNotFoundError(f"Template Folder '{self.template_folder}' not found")

        template_path = os.path.join(self.template_folder, template_name)
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Template '{template_name}' not found")

        if self.template_cache:
            if template_name in self.template_cache:
                template_content = self.template_cache[template_name]
            else:
                with open(template_path, "r") as template_file:
                    template_content = template_file.read()
                self.template_cache[template_name] = template_content
        else:
            with open(template_path, "r") as template_file:
                template_content = template_file.read()

        self.environment = context
        rendered_content = self._render_template(template_content)
        return rendered_content

    def _render_template(self, template):
        template = self._render_includes(template)
        template = self._render_extends(template)
        template = self._render_blocks(template)
        template = self._render_macros(template)
        template = self._render_for_loops(template)
        template = self._render_filters(template)
        template = self._render_conditionals(template)
        template = self._render_expressions(template)
        template = self._strip_template_comments(template)  # Remove comments
        template = self._control_whitespace(template)
        return template

    def _render_includes(self, template):
        def include(match):
            included_template_name = match.group(1).strip()
            included_template_path = os.path.join(self.template_folder, included_template_name)
            if not os.path.exists(included_template_path):
                return f"Include Error: Template '{included_template_name}' not found"
            
            with open(included_template_path, "r") as included_template_file:
                included_template_content = included_template_file.read()

            return self._render_template(included_template_content)

        return re.sub(r'\[\[:\s*include\s+(.*?)\s*:\s*\]\]', include, template)

    def _render_extends(self, template):
        def extend(match):
            extended_template_name = match.group(1).strip()
            extended_template_path = os.path.join(self.template_folder, extended_template_name)
            if not os.path.exists(extended_template_path):
                return f"Extend Error: Template '{extended_template_name}' not found"
            
            with open(extended_template_path, "r") as extended_template_file:
                extended_template_content = extended_template_file.read()

            # Store the blocks from the extended template
            self.blocks = self._extract_blocks(extended_template_content)

            return re.sub(r'\[\[:\s*extends\s+(.*?)\s*:\s*\]\]', '', template)

        return re.sub(r'\[\[:\s*extends\s+(.*?)\s*:\s*\]\]', extend, template)

    def _render_blocks(self, template):
        for block_name, block_content in self.blocks.items():
            block_pattern = re.compile(r'\[\[:\s*block\s+' + re.escape(block_name) + r'\s*:\s*\]\](.*?)\[\[:\s*endblock\s*:\s*\]\]', re.DOTALL)
            match = block_pattern.search(template)
            if match:
                template = template.replace(match.group(0), block_content)

        return template

    def _extract_blocks(self, template):
        blocks = {}
        block_pattern = re.compile(r'\[\[:\s*block\s+(.*?)\s*:\s*\]\](.*?)\[\[:\s*endblock\s*:\s*\]\]', re.DOTALL)
        for match in block_pattern.finditer(template):
            block_name = match.group(1).strip()
            block_content = match.group(2)
            blocks[block_name] = block_content
        return blocks

    def _render_macros(self, template):
        def macro(match):
            macro_name = match.group(1).strip()
            macro_content = match.group(2)
            self.macros[macro_name] = macro_content
            return ""

        template = re.sub(r'\[\[:\s*macro\s+(.*?)\s*:\s*\]\](.*?)\[\[:\s*endmacro\s*:\s*\]\]', macro, template, flags=re.DOTALL)
        return template

    def _render_for_loops(self, template):
        def render_loop(match):
            loop_variable = match.group(1).strip()
            loop_list = match.group(2).strip()
            loop_body = match.group(3)

            try:
                loop_list = eval(loop_list, self.environment)
                if isinstance(loop_list, list):
                    rendered_loop = ""
                    for index, item in enumerate(loop_list):
                        loop_context = self.environment.copy()
                        loop_context[loop_variable] = item
                        loop_context["loop"] = {
                            "index": index + 1,
                            "index0": index,
                            "first": index == 0,
                            "last": index == len(loop_list) - 1,
                        }
                        rendered_loop += self._render_template(loop_body)
                    return rendered_loop
                else:
                    return f"For Loop Error: {loop_list} is not iterable"
            except Exception as e:
                return f"For Loop Error: {str(e)}"

        return re.sub(r'\[\[:\s*for\s+(.*?)\s+in\s+(.*?)\s*:\s*\]\](.*?)\[\[:\s*endfor\s*:\s*\]\]', render_loop, template, flags=re.DOTALL)

    def _render_filters(self, template):
        def apply_filter(match):
            expression = match.group(1).strip()
            filter_name = match.group(2).strip()
            try:
                value = eval(expression, self.environment)
                if filter_name in self.filters:
                    return self.filters[filter_name](value)
                else:
                    return f"Filter Error: Unknown filter '{filter_name}'"
            except Exception as e:
                return f"Filter Error: {str(e)}"

        return re.sub(r'\[\[\s*(.*?)\s*\|\s*(.*?)\s*\]\]', apply_filter, template)

    def _render_conditionals(self, template):
        def render_conditional(match):
            condition = match.group(1).strip()
            true_block = match.group(2)
            false_block = match.group(3)

            try:
                if eval(condition, self.environment):
                    return true_block
            except NameError:
                return false_block

        template = re.sub(r'\[\[:\s*if\s+(.*?)\s*:\s*\]\](.*?)\[\[:\s*else\s*:\s*\]\](.*?)\[\[:\s*endif\s*:\s*\]\]',
                          render_conditional, template, flags=re.DOTALL)

        return template

    def _render_expressions(self, template):
        def render_expression(match):
            expression = match.group(1).strip()
            try:
                return str(eval(expression, self.environment))
            except Exception as e:
                return f"Expression Error: {str(e)}"

        template = re.sub(r'\[\[\s*(.*?)\s*\]\]', render_expression, template)
        return template

    def add_filter(self, name, filter_func):
        self.filters[name] = filter_func

    def _strip_template_comments(self, template):
        return re.sub(r'\[\[:\s*#.*?\s*:\s*\]\]', '', template)  # Remove comments

    def _control_whitespace(self, template):
        template = re.sub(r'[\n\t]+', ' ', template)  # Replace newline and tabs with a single space
        template = re.sub(r'\s{2,}', ' ', template)   # Replace multiple spaces with a single space
        template = template.strip()                   # Remove leading/trailing spaces
        return template