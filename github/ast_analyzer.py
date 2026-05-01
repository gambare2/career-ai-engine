import ast
import os
import re
from collections import defaultdict

class PythonASTAnalyzer(ast.NodeVisitor):
    def __init__(self):
        self.imports = set()
        self.used_names = set()
        self.functions = []
        self.classes = []
        self.large_functions = []
        self.complexity_issues = []
        
    def visit_Import(self, node):
        for alias in node.names:
            self.imports.add(alias.name)
        self.generic_visit(node)
        
    def visit_ImportFrom(self, node):
        for alias in node.names:
            self.imports.add(alias.name)
        self.generic_visit(node)
        
    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load):
            self.used_names.add(node.id)
        self.generic_visit(node)
        
    def visit_FunctionDef(self, node):
        self.functions.append(node.name)
        
        # Check function size
        lines = getattr(node, 'end_lineno', node.lineno) - node.lineno
        if lines > 50:
            self.large_functions.append({"name": node.name, "lines": lines})
            
        # Check complexity (nested logic - simple proxy: count depth of loops/ifs)
        # For simplicity, we just count if/for/while nodes
        complexity = sum(1 for _ in ast.walk(node) if isinstance(_, (ast.If, ast.For, ast.While, ast.Try)))
        if complexity > 10:
            self.complexity_issues.append({"name": node.name, "complexity": complexity})
            
        self.generic_visit(node)

def analyze_python_ast(file_path, content):
    try:
        tree = ast.parse(content)
        analyzer = PythonASTAnalyzer()
        analyzer.visit(tree)
        
        unused_imports = list(analyzer.imports - analyzer.used_names)
        unused_functions = [f for f in analyzer.functions if f not in analyzer.used_names and not f.startswith("__")]
        
        return {
            "unused_imports": unused_imports,
            "unused_functions": unused_functions,
            "large_functions": analyzer.large_functions,
            "complexity_issues": analyzer.complexity_issues
        }
    except Exception:
        return None

def analyze_js_heuristic(file_path, content):
    """Simple regex based JS parsing strategy for AST-like analysis"""
    large_functions = []
    complexity_issues = []
    
    # Very basic duplicate logic detection using repeated blocks
    # Simplified large function detection
    lines = content.splitlines()
    func_regex = re.compile(r'(function\s+\w+|const\s+\w+\s*=\s*(async\s*)?\([^)]*\)\s*=>|^\s*async\s+\w+\s*\([^)]*\))')
    
    current_func = None
    func_start = 0
    nesting = 0
    
    for i, line in enumerate(lines):
        if func_regex.search(line) and "{" in line:
            current_func = line.strip()
            func_start = i
            nesting = line.count("{") - line.count("}")
        elif current_func:
            nesting += line.count("{") - line.count("}")
            if nesting <= 0:
                length = i - func_start
                if length > 50:
                    large_functions.append({"name": current_func[:30] + "...", "lines": length})
                current_func = None
                
    return {
        "large_functions": large_functions,
        "complexity_issues": [], # Too complex for simple regex
        "unused_imports": [],
        "unused_functions": []
    }

def run_ast_analysis(repo_path, files):
    results = {
        "dead_code": {"unused_imports": [], "unused_functions": []},
        "duplicate_logic": [],
        "bad_architecture": [],
        "large_functions": [],
        "complexity_problems": []
    }
    
    folder_structure = set()
    has_controllers = False
    has_services = False
    
    # Track blocks for duplicate logic
    code_blocks = defaultdict(list)
    
    for file_path in files:
        ext = os.path.splitext(file_path)[1].lower()
        rel_path = os.path.relpath(file_path, repo_path)
        
        # Architecture Checks
        folder_name = os.path.basename(os.path.dirname(file_path)).lower()
        folder_structure.add(folder_name)
        if "controller" in folder_name or "controller" in file_path.lower():
            has_controllers = True
            # Business logic in controller check (heuristic: controller is too long or imports db directly)
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    if len(content.splitlines()) > 200 or "db.query" in content or "mongoose.model" in content:
                        results["bad_architecture"].append(f"Business logic might be inside controller: {rel_path}")
            except: pass
            
        if "service" in folder_name or "service" in file_path.lower():
            has_services = True

        if ext in ['.py', '.js', '.ts', '.tsx']:
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    
                    # Duplicate logic check (hash every 10 lines)
                    lines = content.splitlines()
                    for i in range(0, len(lines) - 10, 5):
                        block = "".join(lines[i:i+10]).strip()
                        if len(block) > 100:
                            code_blocks[block].append(rel_path)
                            
                    # AST/Heuristic analysis
                    if ext == '.py':
                        analysis = analyze_python_ast(file_path, content)
                    else:
                        analysis = analyze_js_heuristic(file_path, content)
                        
                    if analysis:
                        if analysis.get("unused_imports"):
                            results["dead_code"]["unused_imports"].append({"file": rel_path, "imports": analysis["unused_imports"]})
                        if analysis.get("unused_functions"):
                            results["dead_code"]["unused_functions"].append({"file": rel_path, "functions": analysis["unused_functions"]})
                        for lf in analysis.get("large_functions", []):
                            lf["file"] = rel_path
                            results["large_functions"].append(lf)
                        for ci in analysis.get("complexity_issues", []):
                            ci["file"] = rel_path
                            results["complexity_problems"].append(ci)
            except Exception:
                pass

    if has_controllers and not has_services:
        results["bad_architecture"].append("Missing service layer: Controllers found without a corresponding services directory.")
    if len(folder_structure) < 3 and len(files) > 10:
        results["bad_architecture"].append("Poor folder structure: Too many files in too few directories.")
        
    for block, locations in code_blocks.items():
        if len(set(locations)) > 1:
            results["duplicate_logic"].append(f"Repeated code found across: {', '.join(set(locations))}")
            if len(results["duplicate_logic"]) >= 5: # Limit to 5
                break

    return results
