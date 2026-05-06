"""
YAML Diff and Comparison Module
Provides functionality to compare and visualize differences between YAML files
"""

import yaml
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
import json


@dataclass
class DiffLine:
    """Represents a single line in a diff"""
    type: str  # 'added', 'removed', 'unchanged', 'modified'
    path: str
    old_value: Any = None
    new_value: Any = None
    line_number: int = 0


class YAMLDiffer:
    """Compares two YAML documents and generates diffs"""

    @staticmethod
    def parse_yaml(yaml_content: str) -> Dict[str, Any]:
        """Parse YAML content safely"""
        try:
            return yaml.safe_load(yaml_content) or {}
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML: {str(e)}")

    @staticmethod
    def _flatten_dict(d: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
        """Flatten nested dictionary"""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(YAMLDiffer._flatten_dict(v, new_key, sep).items())
            elif isinstance(v, list):
                items.append((new_key, json.dumps(v)))
            else:
                items.append((new_key, v))
        return dict(items)

    def compare_dicts(self, old_dict: Dict[str, Any], new_dict: Dict[str, Any]) -> List[DiffLine]:
        """Compare two dictionaries and return differences"""
        diffs = []
        
        # Flatten for easy comparison
        old_flat = self._flatten_dict(old_dict)
        new_flat = self._flatten_dict(new_dict)
        
        all_keys = set(old_flat.keys()) | set(new_flat.keys())
        
        for key in sorted(all_keys):
            old_val = old_flat.get(key)
            new_val = new_flat.get(key)
            
            if key not in old_flat:
                diffs.append(DiffLine(
                    type='added',
                    path=key,
                    new_value=new_val
                ))
            elif key not in new_flat:
                diffs.append(DiffLine(
                    type='removed',
                    path=key,
                    old_value=old_val
                ))
            elif old_val != new_val:
                diffs.append(DiffLine(
                    type='modified',
                    path=key,
                    old_value=old_val,
                    new_value=new_val
                ))
        
        return diffs

    def compare_yaml(self, old_yaml: str, new_yaml: str) -> List[DiffLine]:
        """Compare two YAML strings"""
        old_dict = self.parse_yaml(old_yaml)
        new_dict = self.parse_yaml(new_yaml)
        return self.compare_dicts(old_dict, new_dict)

    def generate_diff_summary(self, diffs: List[DiffLine]) -> Dict[str, Any]:
        """Generate summary statistics of differences"""
        summary = {
            'total_changes': len(diffs),
            'added': len([d for d in diffs if d.type == 'added']),
            'removed': len([d for d in diffs if d.type == 'removed']),
            'modified': len([d for d in diffs if d.type == 'modified']),
            'unchanged': len([d for d in diffs if d.type == 'unchanged'])
        }
        return summary

    def format_diff_html(self, diffs: List[DiffLine]) -> str:
        """Format diff as HTML for web display"""
        html = """
        <table class="diff-table" style="width: 100%; border-collapse: collapse;">
            <tr style="background-color: #f0f0f0;">
                <th style="border: 1px solid #ddd; padding: 8px;">Type</th>
                <th style="border: 1px solid #ddd; padding: 8px;">Path</th>
                <th style="border: 1px solid #ddd; padding: 8px;">Old Value</th>
                <th style="border: 1px solid #ddd; padding: 8px;">New Value</th>
            </tr>
        """
        
        for diff in diffs:
            color = {
                'added': '#d4edda',
                'removed': '#f8d7da',
                'modified': '#fff3cd',
                'unchanged': '#ffffff'
            }.get(diff.type, '#ffffff')
            
            html += f"""
            <tr style="background-color: {color};">
                <td style="border: 1px solid #ddd; padding: 8px;">{diff.type}</td>
                <td style="border: 1px solid #ddd; padding: 8px; font-family: monospace;">{diff.path}</td>
                <td style="border: 1px solid #ddd; padding: 8px; font-family: monospace;">{diff.old_value or '-'}</td>
                <td style="border: 1px solid #ddd; padding: 8px; font-family: monospace;">{diff.new_value or '-'}</td>
            </tr>
            """
        
        html += "</table>"
        return html

    def format_diff_json(self, diffs: List[DiffLine]) -> str:
        """Format diff as JSON"""
        json_diffs = []
        for diff in diffs:
            json_diffs.append({
                'type': diff.type,
                'path': diff.path,
                'old_value': diff.old_value,
                'new_value': diff.new_value
            })
        return json.dumps(json_diffs, indent=2)
