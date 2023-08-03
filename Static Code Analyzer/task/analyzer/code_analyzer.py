import os
import re
import sys
import ast


class CodeLinter:
    def __init__(self, fp):
        self.fp = str(fp)
        self.blank_counter = 0
        self.errors = []

    # S001
    def lint_s001(self, line, i):
        if len(line) > 79:
            self.errors.append((i, 'S001', 'Too long'))

    # S002
    def lint_s002(self, line, i):
        j = 0
        while j < len(line) and line[j] == " ":
            j += 1
        if j % 4 != 0:
            self.errors.append((i, 'S002', 'Indentation is not a multiple of four'))

    @staticmethod
    def find_comm(line):
        if "#" in line:
            return line.split("#")[0]
        else:
            return line

    # S003
    def lint_s003(self, line, i):
        new_line = self.find_comm(line).rstrip()
        if str(new_line).endswith(";"):
            self.errors.append((i, 'S003', 'Unnecessary semicolon'))

    # S004
    def lint_s004(self, line, i):
        if "#" in line and line.index("#") != 0:
            new_line = self.find_comm(line)
            if len(new_line) < 2 or new_line[-1] + new_line[-2] != "  ":
                self.errors.append((i, 'S004', 'At least two spaces required before inline comments'))

    # S005
    def lint_s005(self, line, i):
        if '#' in line:
            comment_index = line.index('#')
            if "todo" in line[comment_index:].lower():
                self.errors.append((i, 'S005', 'TODO found'))

    # S006
    def lint_s006(self, i):
        if self.blank_counter > 2:
            self.errors.append((i, 'S006', 'More than two blank lines used before this line'))
            self.blank_counter = 0  # reset counter once the warning is issued

    # S007
    def lint_s007(self, line, i):
        if re.search(r'\bdef\s{2,}', line):
            self.errors.append((i, 'S007', 'Too many spaces after keyword "def"'))
        if re.search(r'\bclass\s{2,}', line):
            self.errors.append((i, 'S007', 'Too many spaces after keyword "class"'))

    # S008
    def lint_s008(self, line, i):
        match = re.search(r'^\s*class\s+([A-Za-z\d_]+)', line)
        if match:
            class_name = match.group(1)
            if not class_name[0].isupper() or "_" in class_name:
                self.errors.append((i, 'S008', 'Class name \'{}\' should use CamelCase'.format(class_name)))

    def lint_s009(self, node):
        function_name = node.name
        if function_name.startswith('__') and function_name.endswith('__'):
            # Ignore 'magic' methods
            return
        if not function_name.islower() or "__" in function_name or function_name.endswith('_'):
            self.errors.append((node.lineno, 'S009', 'Function name \'{}\' should use snake_case'.format(function_name)))

    # S010
    def lint_s010(self, node):
        for arg in node.args.args:
            if not re.match('(_*[a-z]+[a-z0-9_]*|[a-z][a-z0-9_]*)$', arg.arg):
                self.errors.append((node.lineno, 'S010', 'Argument name \'{}\' should be snake_case'.format(arg.arg)))

    # S011
    def lint_s011(self, node):
        if isinstance(node.targets[0], ast.Name):
            var_name = node.targets[0].id
            if not re.match('(_*[a-z]+[a-z0-9_]*|[a-z][a-z0-9_]*)$', var_name):
                self.errors.append((node.lineno, 'S011', 'Variable \'{}\' in function should be snake_case'.format(var_name)))

    # S012
    def lint_s012(self, node):
        for arg in node.args.defaults:
            if isinstance(arg, (ast.List, ast.Dict, ast.Set)):
                self.errors.append((node.lineno, 'S012', 'Default argument value is mutable'))
                break  # print this once per function definition

    def analyze(self):
        with open(self.fp, 'r') as file:
            source = file.read()
            self.lines = source.splitlines()
            tree = ast.parse(source)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    self.lint_s009(node)  # validate function names when traversing the AST
                    self.lint_s010(node)
                    self.lint_s012(node)
                elif isinstance(node, ast.Assign):
                    self.lint_s011(node)
                elif isinstance(node, ast.ClassDef):
                    pass

            for i, line in enumerate(source.splitlines(), start=1):
                self.lint_s001(line, i)
                self.lint_s002(line, i)
                self.lint_s003(line, i)
                self.lint_s004(line, i)
                self.lint_s005(line, i)
                self.lint_s007(line, i)
                self.lint_s008(line, i)

                if line == "\n" or line == "":
                    self.blank_counter += 1
                else:
                    self.lint_s006(i)
                    self.blank_counter = 0  # reset counter on non-blank line

        self.errors.sort()  # sort errors by line number

        # print the errors in correct order
        for i, error_code, error_message in self.errors:
            print(f'{self.fp}: Line {i}: {error_code} {error_message}')


def main():
    path = sys.argv[1]
    if os.path.isfile(path) and path.endswith('.py'):
        cl = CodeLinter(path)
        cl.analyze()
    elif os.path.isdir(path):
        for fname in sorted(os.listdir(path)):
            if fname.endswith('.py'):
                cl = CodeLinter(os.path.join(path, fname))
                cl.analyze()


if __name__ == '__main__':
    main()
