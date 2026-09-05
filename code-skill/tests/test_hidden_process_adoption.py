"""Keep maintained runtime and test launches on the same invisible process policy."""
import ast
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LAUNCHES = {'run', 'Popen', 'call', 'check_call', 'check_output', 'getoutput', 'getstatusoutput'}


def uncovered_launches(source):
    tree = ast.parse(source)
    modules = {'subprocess'}
    functions = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.asname or alias.name for alias in node.names if alias.name == 'subprocess')
        elif isinstance(node, ast.ImportFrom) and node.module == 'subprocess':
            functions.update(alias.asname or alias.name for alias in node.names if alias.name in LAUNCHES)
    failures = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        launch = (isinstance(func, ast.Name) and func.id in functions) or (isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name) and func.value.id in modules and func.attr in LAUNCHES)
        if not launch:
            continue
        guarded = any(keyword.arg is None and isinstance(keyword.value, ast.Call) and (isinstance(keyword.value.func, ast.Name) and keyword.value.func.id == 'hidden_process_options' or isinstance(keyword.value.func, ast.Attribute) and keyword.value.func.attr == 'hidden_process_options') for keyword in node.keywords)
        if not guarded:
            failures.append(node.lineno)
    return failures


class HiddenProcessAdoptionTests(unittest.TestCase):
    def test_every_managed_runtime_and_test_launch_uses_hidden_options(self):
        failures = []
        count = 0
        catalog = json.loads((ROOT / 'management-skill/assets/global-skill-capability-catalog.json').read_text(encoding='utf-8'))
        for skill in (ROOT / name for name in catalog['managed_skills']):
            for area in ('scripts', 'tests'):
                for path in sorted((skill / area).rglob('*.py')):
                    count += 1
                    failures.extend(f'{path.relative_to(ROOT)}:{line}' for line in uncovered_launches(path.read_text(encoding='utf-8')))
        self.assertGreater(count, 100)
        self.assertEqual(failures, [])

    def test_guard_detects_aliases_and_allows_shared_helper(self):
        self.assertEqual(uncovered_launches('import subprocess as sp\nsp.run(cmd)'), [2])
        self.assertEqual(uncovered_launches('from subprocess import Popen as launch\nlaunch(cmd)'), [2])
        self.assertEqual(uncovered_launches('import subprocess as sp\nsp.run(cmd, **hidden_process_options())'), [])
        self.assertEqual(uncovered_launches('import subprocess\nsubprocess.run(cmd, **hidden_process.hidden_process_options())'), [])

    def test_standalone_installer_policy_matches_shared_helper(self):
        trees = [ast.parse(path.read_text(encoding="utf-8")) for path in (ROOT / 'code-skill/scripts/hidden_process.py', ROOT / 'management-skill/scripts/sync_global_skills.py')]
        functions = [next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'hidden_process_options') for tree in trees]
        self.assertEqual(ast.dump(functions[0]), ast.dump(functions[1]))


if __name__ == '__main__':
    unittest.main()
