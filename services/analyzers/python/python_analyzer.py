import ast
import os
import json
import logging
from typing import Dict, List, Any
from pathlib import Path
import networkx as nx
from collections import defaultdict

logger = logging.getLogger(__name__)

class PythonAnalyzer:
    def __init__(self):
        self.supported_analysis_types = [
            "syntax_analysis",
            "dependency_analysis", 
            "complexity_analysis",
            "security_analysis",
            "architecture_analysis"
        ]
    
    def analyze_repository(self, repo_path: str, analysis_types: List[str]) -> Dict[str, Any]:
        """Analyze Python code in a repository"""
        results = {
            "language": "python",
            "repository_path": repo_path,
            "analysis_types": analysis_types,
            "files_analyzed": 0,
            "analysis_results": {}
        }
        
        # Find all Python files
        python_files = self.find_python_files(repo_path)
        results["files_analyzed"] = len(python_files)
        
        if not python_files:
            logger.warning(f"No Python files found in {repo_path}")
            return results
        
        # Perform requested analysis types
        for analysis_type in analysis_types:
            if analysis_type in self.supported_analysis_types:
                logger.info(f"Running {analysis_type} on {len(python_files)} files")
                results["analysis_results"][analysis_type] = self.run_analysis(
                    analysis_type, python_files, repo_path
                )
        
        return results
    
    def find_python_files(self, repo_path: str) -> List[str]:
        """Find all Python files in the repository"""
        python_files = []
        
        for root, dirs, files in os.walk(repo_path):
            # Skip common directories
            dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', '.pytest_cache', 'venv', 'env']]
            
            for file in files:
                if file.endswith('.py'):
                    python_files.append(os.path.join(root, file))
        
        return python_files
    
    def run_analysis(self, analysis_type: str, python_files: List[str], repo_path: str) -> Dict[str, Any]:
        """Run specific analysis type"""
        if analysis_type == "syntax_analysis":
            return self.syntax_analysis(python_files)
        elif analysis_type == "dependency_analysis":
            return self.dependency_analysis(python_files, repo_path)
        elif analysis_type == "complexity_analysis":
            return self.complexity_analysis(python_files)
        elif analysis_type == "security_analysis":
            return self.security_analysis(python_files)
        elif analysis_type == "architecture_analysis":
            return self.architecture_analysis(python_files, repo_path)
        else:
            return {"error": f"Unsupported analysis type: {analysis_type}"}
    
    def syntax_analysis(self, python_files: List[str]) -> Dict[str, Any]:
        """Analyze syntax and AST structure"""
        results = {
            "total_files": len(python_files),
            "valid_files": 0,
            "syntax_errors": [],
            "file_stats": {}
        }
        
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content, filename=file_path)
                results["valid_files"] += 1
                
                # Collect basic stats
                stats = self.collect_file_stats(tree, file_path)
                results["file_stats"][file_path] = stats
                
            except SyntaxError as e:
                results["syntax_errors"].append({
                    "file": file_path,
                    "line": e.lineno,
                    "message": str(e)
                })
            except Exception as e:
                results["syntax_errors"].append({
                    "file": file_path,
                    "error": str(e)
                })
        
        return results
    
    def collect_file_stats(self, tree: ast.AST, file_path: str) -> Dict[str, Any]:
        """Collect statistics from AST"""
        stats = {
            "classes": 0,
            "functions": 0,
            "imports": 0,
            "lines_of_code": 0,
            "classes_list": [],
            "functions_list": [],
            "imports_list": []
        }
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                stats["classes"] += 1
                stats["classes_list"].append(node.name)
            elif isinstance(node, ast.FunctionDef):
                stats["functions"] += 1
                stats["functions_list"].append(node.name)
            elif isinstance(node, ast.Import):
                stats["imports"] += 1
                for alias in node.names:
                    stats["imports_list"].append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                stats["imports"] += 1
                module = node.module or ""
                for alias in node.names:
                    stats["imports_list"].append(f"{module}.{alias.name}")
        
        # Count lines of code
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                stats["lines_of_code"] = len([line for line in lines if line.strip() and not line.strip().startswith('#')])
        except:
            pass
        
        return stats
    
    def dependency_analysis(self, python_files: List[str], repo_path: str) -> Dict[str, Any]:
        """Analyze dependencies between files"""
        dependencies = defaultdict(set)
        module_map = {}  # Map module names to file paths
        
        # Build module map
        for file_path in python_files:
            rel_path = os.path.relpath(file_path, repo_path)
            module_name = rel_path.replace('/', '.').replace('.py', '')
            module_map[module_name] = file_path
        
        # Analyze imports
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content, filename=file_path)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            dependencies[file_path].add(alias.name)
                    elif isinstance(node, ast.ImportFrom):
                        module = node.module or ""
                        if module:
                            dependencies[file_path].add(module)
                        for alias in node.names:
                            full_name = f"{module}.{alias.name}" if module else alias.name
                            dependencies[file_path].add(full_name)
            except:
                continue
        
        # Convert to serializable format
        dependency_graph = {}
        for file_path, deps in dependencies.items():
            dependency_graph[file_path] = list(deps)
        
        return {
            "dependency_graph": dependency_graph,
            "total_dependencies": sum(len(deps) for deps in dependencies.values()),
            "module_map": module_map
        }
    
    def complexity_analysis(self, python_files: List[str]) -> Dict[str, Any]:
        """Analyze code complexity"""
        results = {
            "file_complexity": {},
            "total_complexity": 0,
            "high_complexity_functions": []
        }
        
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content, filename=file_path)
                complexity = self.calculate_cyclomatic_complexity(tree)
                
                results["file_complexity"][file_path] = complexity
                results["total_complexity"] += complexity["total_complexity"]
                
                # Identify high complexity functions
                for func_info in complexity["functions"]:
                    if func_info["complexity"] > 10:  # Threshold for high complexity
                        results["high_complexity_functions"].append({
                            "file": file_path,
                            "function": func_info["name"],
                            "complexity": func_info["complexity"]
                        })
            except:
                continue
        
        return results
    
    def calculate_cyclomatic_complexity(self, tree: ast.AST) -> Dict[str, Any]:
        """Calculate cyclomatic complexity"""
        complexity_info = {
            "total_complexity": 1,  # Base complexity
            "functions": []
        }
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_complexity = self.function_complexity(node)
                complexity_info["functions"].append({
                    "name": node.name,
                    "complexity": func_complexity
                })
                complexity_info["total_complexity"] += func_complexity
        
        return complexity_info
    
    def function_complexity(self, func_node: ast.FunctionDef) -> int:
        """Calculate complexity for a single function"""
        complexity = 1  # Base complexity
        
        for node in ast.walk(func_node):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.Try, ast.With)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
        
        return complexity
    
    def security_analysis(self, python_files: List[str]) -> Dict[str, Any]:
        """Basic security analysis"""
        security_issues = []
        
        dangerous_functions = [
            'eval', 'exec', 'compile', '__import__',
            'input', 'raw_input', 'open'
        ]
        
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content, filename=file_path)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.Call):
                        if isinstance(node.func, ast.Name):
                            if node.func.id in dangerous_functions:
                                security_issues.append({
                                    "file": file_path,
                                    "line": node.lineno,
                                    "issue": f"Use of potentially dangerous function: {node.func.id}",
                                    "severity": "medium"
                                })
            except:
                continue
        
        return {
            "security_issues": security_issues,
            "total_issues": len(security_issues)
        }
    
    def architecture_analysis(self, python_files: List[str], repo_path: str) -> Dict[str, Any]:
        """Analyze architectural patterns"""
        patterns = {
            "mvc_pattern": False,
            "singleton_pattern": 0,
            "factory_pattern": 0,
            "observer_pattern": 0,
            "package_structure": {}
        }
        
        # Analyze package structure
        packages = defaultdict(list)
        for file_path in python_files:
            rel_path = os.path.relpath(file_path, repo_path)
            package = os.path.dirname(rel_path)
            if package:
                packages[package].append(os.path.basename(file_path))
        
        patterns["package_structure"] = dict(packages)
        
        # Look for common patterns in file names
        all_files = [os.path.basename(f) for f in python_files]
        if any('model' in f.lower() for f in all_files) and \
           any('view' in f.lower() for f in all_files) and \
           any('controller' in f.lower() for f in all_files):
            patterns["mvc_pattern"] = True
        
        return patterns