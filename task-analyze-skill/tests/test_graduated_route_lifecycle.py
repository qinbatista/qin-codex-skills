import importlib.util
import unittest
from pathlib import Path
SPEC=importlib.util.spec_from_file_location("current_model_policy",Path(__file__).resolve().parents[1]/"scripts/selected_model_policy.py")
MODULE=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

class GoalOwnershipTests(unittest.TestCase):
    def test_governed_child_keeps_pair_even_when_marked_independent(self):
        node={"skill":"code-skill","skill_independent":True,"model":"cheap","effort":"low"}
        MODULE.bind_node(node,"gpt-6-astra","ultra")
        self.assertEqual((node["model"],node["effort"]),("gpt-6-astra","ultra"))
    def test_independent_script_retains_its_adaptive_pair(self):
        node={"task_type":"script","skill_independent":True,"model":"gpt-5.6-luna","effort":"low"}
        MODULE.bind_node(node,"gpt-6-astra","ultra")
        self.assertEqual((node["model"],node["effort"]),("gpt-5.6-luna","low"))
