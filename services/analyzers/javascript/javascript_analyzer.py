import os
import json
import logging
import subprocess
from typing import Dict, List, Any
from pathlib import Path
import re
from collections import defaultdict

logger = logging.getLogger(__name__)

class JavaScriptAnalyzer:
    def __init__(self):
        self.supported_analysis_types = [
            "syntax_analysis",
            "dependency_analysis", 
            "complexity_analysis",
            "security_analysis",
            "architecture_analysis"
        ]
    
    def analyze_repository(self, repo_path: str, analysis_types: List[str]) -> Dict[str, Any]:
        """Analyze JavaScript/TypeScript code in a repository"""
        results = {
            "language": "javascript",
            "repository_path": repo_path,
            "analysis_types": analysis_types,
            "files_analyzed": 0,
            "analysis_results": {}
        }
        
        # Find all JavaScript/TypeScript files
        js_files = self.find_javascript_files(repo_path)
        results["files_analyzed"] = len(js_files)
        
        if not js_files:
            logger.warning(f"No JavaScript/TypeScript files found in {repo_path}")
            return results
        
        # Perform requested analysis types
        for analysis_type in analysis_types:
            if analysis_type in self.supported_analysis_types:
                logger.info(f"Running {analysis_type} on {len(js_files)} files")
                results["analysis_results"][analysis_type] = self.run_analysis(
                    analysis_type, js_files, repo_path
                )
        
        return results
    
    def find_javascript_files(self, repo_path: str) -> List[str]:
        """Find all JavaScript/TypeScript files in the repository"""
        js_files = []
        
        for root, dirs, files in os.walk(repo_path):
            # Skip common directories
            dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules', 'dist', 'build', '.next']]
            
            for file in files:
                if any(file.endswith(ext) for ext in ['.js', '.jsx', '.ts', '.tsx', '.mjs']):
                    js_files.append(os.path.join(root, file))
        
        return js_files
    
    def run_analysis(self, analysis_type: str, js_files: List[str], repo_path: str) -> Dict[str, Any]:
        """Run specific analysis type"""
        if analysis_type == "syntax_analysis":
            return self.syntax_analysis(js_files, repo_path)
        elif analysis_type == "dependency_analysis":
            return self.dependency_analysis(js_files, repo_path)
        elif analysis_type == "complexity_analysis":
            return self.complexity_analysis(js_files)
        elif analysis_type == "security_analysis":
            return self.security_analysis(js_files)
        elif analysis_type == "architecture_analysis":
            return self.architecture_analysis(js_files, repo_path)
        else:
            return {"error": f"Unsupported analysis type: {analysis_type}"}
    
    def syntax_analysis(self, js_files: List[str], repo_path: str) -> Dict[str, Any]:
        """Analyze syntax using ESLint and TypeScript compiler"""
        results = {
            "total_files": len(js_files),
            "valid_files": 0,
            "syntax_errors": [],
            "file_stats": {}
        }
        
        # Try to run TypeScript compiler if tsconfig.json exists
        tsconfig_path = os.path.join(repo_path, 'tsconfig.json')
        if os.path.exists(tsconfig_path):
            try:
                tsc_result = subprocess.run(
                    ["npx", "tsc", "--noEmit", "--skipLibCheck"],
                    cwd=repo_path,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                if tsc_result.returncode != 0:
                    self.parse_typescript_errors(tsc_result.stderr, results)
                    
            except subprocess.TimeoutExpired:
                results["syntax_errors"].append("TypeScript compilation timeout")
            except Exception as e:
                results["syntax_errors"].append(f"TypeScript compilation failed: {str(e)}")
        
        # Analyze individual files
        valid_count = 0
        for file_path in js_files:
            try:
                stats = self.collect_file_stats(file_path)
                results["file_stats"][file_path] = stats
                if stats.get("syntax_valid", True):
                    valid_count += 1
            except Exception as e:
                logger.warning(f"Failed to analyze file {file_path}: {e}")
                results["syntax_errors"].append({
                    "file": file_path,
                    "error": str(e)
                })
        
        results["valid_files"] = valid_count
        return results
    
    def parse_typescript_errors(self, stderr: str, results: Dict[str, Any]):
        """Parse TypeScript compilation errors"""
        lines = stderr.split('\n')
        for line in lines:
            if 'error TS' in line:
                results["syntax_errors"].append(line.strip())
    
    def collect_file_stats(self, file_path: str) -> Dict[str, Any]:
        """Collect statistics from JavaScript/TypeScript file"""
        stats = {
            "functions": 0,
            "classes": 0,
            "imports": 0,
            "exports": 0,
            "lines_of_code": 0,
            "functions_list": [],
            "classes_list": [],
            "imports_list": [],
            "syntax_valid": True
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Count lines of code (excluding comments and empty lines)
            lines = content.split('\n')
            stats["lines_of_code"] = len([
                line for line in lines 
                if line.strip() and not line.strip().startswith('//')
            ])
            
            # Functions (including arrow functions)
            function_patterns = [
                r'function\s+(\w+)\s*\(',
                r'(\w+)\s*:\s*function\s*\(',
                r'(\w+)\s*=\s*function\s*\(',
                r'(\w+)\s*=\s*\([^)]*\)\s*=>'
            ]
            
            functions = set()
            for pattern in function_patterns:
                matches = re.findall(pattern, content)
                functions.update(matches)
            
            stats["functions"] = len(functions)
            stats["functions_list"] = list(functions)
            
            # Classes
            class_pattern = r'class\s+(\w+)'
            classes = re.findall(class_pattern, content)
            stats["classes"] = len(classes)
            stats["classes_list"] = classes
            
            # Imports
            import_patterns = [
                r'import\s+.*?from\s+[\'"]([^\'"]+)[\'"]',
                r'import\s+[\'"]([^\'"]+)[\'"]',
                r'require\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)'
            ]
            
            imports = set()
            for pattern in import_patterns:
                matches = re.findall(pattern, content)
                imports.update(matches)
            
            stats["imports"] = len(imports)
            stats["imports_list"] = list(imports)
            
            # Exports
            export_patterns = [
                r'export\s+(?:default\s+)?(?:class|function|const|let|var)\s+(\w+)',
                r'export\s*{\s*([^}]+)\s*}',
                r'module\.exports\s*=\s*(\w+)'
            ]
            
            exports = set()
            for pattern in export_patterns:
                matches = re.findall(pattern, content)
                if isinstance(matches, list) and matches:
                    if ',' in str(matches[0]):  # Handle export { a, b, c }
                        exports.update([name.strip() for name in matches[0].split(',')])
                    else:
                        exports.update(matches)
            
            stats["exports"] = len(exports)
            
        except Exception as e:
            logger.warning(f"Error analyzing file {file_path}: {e}")
            stats["syntax_valid"] = False
        
        return stats
    
    def dependency_analysis(self, js_files: List[str], repo_path: str) -> Dict[str, Any]:
        """Analyze dependencies between files and external packages"""
        dependencies = defaultdict(set)
        package_dependencies = set()
        
        # Parse package.json for external dependencies
        package_json_path = os.path.join(repo_path, 'package.json')
        if os.path.exists(package_json_path):
            try:
                with open(package_json_path, 'r', encoding='utf-8') as f:
                    package_data = json.load(f)
                
                for dep_type in ['dependencies', 'devDependencies', 'peerDependencies']:
                    if dep_type in package_data:
                        package_dependencies.update(package_data[dep_type].keys())
                        
            except Exception as e:
                logger.warning(f"Failed to parse package.json: {e}")
        
        # Analyze import/require statements in files
        for file_path in js_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Find import statements
                import_patterns = [
                    r'import\s+.*?from\s+[\'"]([^\'"]+)[\'"]',
                    r'import\s+[\'"]([^\'"]+)[\'"]',
                    r'require\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)'
                ]
                
                for pattern in import_patterns:
                    imports = re.findall(pattern, content)
                    dependencies[file_path].update(imports)
                    
            except Exception as e:
                logger.warning(f"Failed to analyze dependencies in {file_path}: {e}")
        
        # Convert to serializable format
        dependency_graph = {}
        for file_path, deps in dependencies.items():
            dependency_graph[file_path] = list(deps)
        
        return {
            "dependency_graph": dependency_graph,
            "package_dependencies": list(package_dependencies),
            "total_dependencies": sum(len(deps) for deps in dependencies.values()),
            "total_packages": len(package_dependencies)
        }
    
    def complexity_analysis(self, js_files: List[str]) -> Dict[str, Any]:
        """Analyze code complexity"""
        results = {
            "file_complexity": {},
            "total_complexity": 0,
            "high_complexity_functions": []
        }
        
        for file_path in js_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                complexity = self.calculate_cyclomatic_complexity(content, file_path)
                results["file_complexity"][file_path] = complexity
                results["total_complexity"] += complexity["total_complexity"]
                
                # Identify high complexity functions
                for func_info in complexity["functions"]:
                    if func_info["complexity"] > 10:
                        results["high_complexity_functions"].append({
                            "file": file_path,
                            "function": func_info["name"],
                            "complexity": func_info["complexity"]
                        })
                        
            except Exception as e:
                logger.warning(f"Failed to analyze complexity in {file_path}: {e}")
        
        return results
    
    def calculate_cyclomatic_complexity(self, content: str, file_path: str) -> Dict[str, Any]:
        """Calculate cyclomatic complexity for JavaScript code"""
        complexity_info = {
            "total_complexity": 1,
            "functions": []
        }
        
        # Find functions and calculate their complexity
        function_patterns = [
            (r'function\s+(\w+)\s*\([^)]*\)\s*{', 'function'),
            (r'(\w+)\s*:\s*function\s*\([^)]*\)\s*{', 'method'),
            (r'(\w+)\s*=\s*function\s*\([^)]*\)\s*{', 'assignment'),
            (r'(\w+)\s*=\s*\([^)]*\)\s*=>\s*{', 'arrow')
        ]
        
        for pattern, func_type in function_patterns:
            matches = re.finditer(pattern, content)
            
            for match in matches:
                func_name = match.group(1)
                
                # Find function body (simplified)
                start_pos = match.end() - 1  # Start at opening brace
                brace_count = 1
                end_pos = start_pos + 1
                
                for i, char in enumerate(content[start_pos + 1:], start_pos + 1):
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            end_pos = i
                            break
                
                if end_pos > start_pos:
                    func_body = content[start_pos:end_pos + 1]
                    func_complexity = self.calculate_function_complexity(func_body)
                    
                    complexity_info["functions"].append({
                        "name": func_name,
                        "type": func_type,
                        "complexity": func_complexity
                    })
                    complexity_info["total_complexity"] += func_complexity
        
        return complexity_info
    
    def calculate_function_complexity(self, func_body: str) -> int:
        """Calculate complexity for a single function"""
        complexity = 1  # Base complexity
        
        # Count decision points
        decision_patterns = [
            r'\bif\s*\(',
            r'\bwhile\s*\(',
            r'\bfor\s*\(',
            r'\bswitch\s*\(',
            r'\bcatch\s*\(',
            r'\?\s*.*?\s*:',  # Ternary operator
            r'&&',            # Logical AND
            r'\|\|'           # Logical OR
        ]
        
        for pattern in decision_patterns:
            matches = re.findall(pattern, func_body)
            complexity += len(matches)
        
        return complexity
    
    def security_analysis(self, js_files: List[str]) -> Dict[str, Any]:
        """Basic security analysis"""
        security_issues = []
        
        dangerous_patterns = [
            (r'eval\s*\(', 'Use of eval() - code injection risk'),
            (r'innerHTML\s*=', 'innerHTML assignment - potential XSS'),
            (r'document\.write\s*\(', 'document.write() - potential XSS'),
            (r'dangerouslySetInnerHTML', 'dangerouslySetInnerHTML - XSS risk'),
            (r'exec\s*\(', 'exec() usage - command injection risk'),
            (r'setTimeout\s*\(\s*[\'"]', 'setTimeout with string - code injection'),
            (r'setInterval\s*\(\s*[\'"]', 'setInterval with string - code injection'),
            (r'crypto\.createHash\s*\(\s*[\'"]md5[\'"]', 'MD5 hash usage - weak cryptography'),
            (r'Math\.random\s*\(\s*\)', 'Math.random() - not cryptographically secure'),
        ]
        
        for file_path in js_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                lines = content.split('\n')
                for line_num, line in enumerate(lines, 1):
                    for pattern, description in dangerous_patterns:
                        if re.search(pattern, line, re.IGNORECASE):
                            security_issues.append({
                                "file": file_path,
                                "line": line_num,
                                "issue": description,
                                "severity": "medium",
                                "code": line.strip()
                            })
                            
            except Exception as e:
                logger.warning(f"Failed to analyze security in {file_path}: {e}")
        
        return {
            "security_issues": security_issues,
            "total_issues": len(security_issues)
        }
    
    def architecture_analysis(self, js_files: List[str], repo_path: str) -> Dict[str, Any]:
        """Analyze architectural patterns"""
        patterns = {
            "framework_detected": None,
            "module_system": None,
            "testing_framework": None,
            "build_tool": None,
            "file_structure": {}
        }
        
        # Analyze package.json for framework detection
        package_json_path = os.path.join(repo_path, 'package.json')
        if os.path.exists(package_json_path):
            try:
                with open(package_json_path, 'r', encoding='utf-8') as f:
                    package_data = json.load(f)
                
                deps = {**package_data.get('dependencies', {}), 
                       **package_data.get('devDependencies', {})}
                
                # Framework detection
                if 'react' in deps:
                    patterns["framework_detected"] = "React"
                elif 'vue' in deps:
                    patterns["framework_detected"] = "Vue.js"
                elif 'angular' in deps or '@angular/core' in deps:
                    patterns["framework_detected"] = "Angular"
                elif 'svelte' in deps:
                    patterns["framework_detected"] = "Svelte"
                elif 'express' in deps:
                    patterns["framework_detected"] = "Express.js"
                
                # Testing framework detection
                if 'jest' in deps:
                    patterns["testing_framework"] = "Jest"
                elif 'mocha' in deps:
                    patterns["testing_framework"] = "Mocha"
                elif 'cypress' in deps:
                    patterns["testing_framework"] = "Cypress"
                
                # Build tool detection
                if 'webpack' in deps:
                    patterns["build_tool"] = "Webpack"
                elif 'vite' in deps:
                    patterns["build_tool"] = "Vite"
                elif 'rollup' in deps:
                    patterns["build_tool"] = "Rollup"
                    
            except Exception as e:
                logger.warning(f"Failed to parse package.json: {e}")
        
        # Analyze module system
        for file_path in js_files[:10]:  # Sample first 10 files
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if 'import ' in content or 'export ' in content:
                    patterns["module_system"] = "ES6 Modules"
                    break
                elif 'require(' in content or 'module.exports' in content:
                    patterns["module_system"] = "CommonJS"
                    break
                    
            except Exception as e:
                continue
        
        # Analyze file structure
        structure = defaultdict(list)
        for file_path in js_files:
            rel_path = os.path.relpath(file_path, repo_path)
            directory = os.path.dirname(rel_path)
            if directory:
                structure[directory].append(os.path.basename(file_path))
        
        patterns["file_structure"] = dict(structure)
        
        return patterns