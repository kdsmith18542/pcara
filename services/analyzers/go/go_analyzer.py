import os
import json
import logging
import subprocess
from typing import Dict, List, Any
from pathlib import Path
import re
from collections import defaultdict

logger = logging.getLogger(__name__)

class GoAnalyzer:
    def __init__(self):
        self.supported_analysis_types = [
            "syntax_analysis",
            "dependency_analysis", 
            "complexity_analysis",
            "security_analysis",
            "architecture_analysis"
        ]
    
    def analyze_repository(self, repo_path: str, analysis_types: List[str]) -> Dict[str, Any]:
        """Analyze Go code in a repository"""
        results = {
            "language": "go",
            "repository_path": repo_path,
            "analysis_types": analysis_types,
            "files_analyzed": 0,
            "analysis_results": {}
        }
        
        # Find all Go files
        go_files = self.find_go_files(repo_path)
        results["files_analyzed"] = len(go_files)
        
        if not go_files:
            logger.warning(f"No Go files found in {repo_path}")
            return results
        
        # Perform requested analysis types
        for analysis_type in analysis_types:
            if analysis_type in self.supported_analysis_types:
                logger.info(f"Running {analysis_type} on {len(go_files)} files")
                results["analysis_results"][analysis_type] = self.run_analysis(
                    analysis_type, go_files, repo_path
                )
        
        return results
    
    def find_go_files(self, repo_path: str) -> List[str]:
        """Find all Go files in the repository"""
        go_files = []
        
        for root, dirs, files in os.walk(repo_path):
            # Skip common directories
            dirs[:] = [d for d in dirs if d not in ['.git', 'vendor', 'node_modules']]
            
            for file in files:
                if file.endswith('.go'):
                    go_files.append(os.path.join(root, file))
        
        return go_files
    
    def run_analysis(self, analysis_type: str, go_files: List[str], repo_path: str) -> Dict[str, Any]:
        """Run specific analysis type"""
        if analysis_type == "syntax_analysis":
            return self.syntax_analysis(go_files, repo_path)
        elif analysis_type == "dependency_analysis":
            return self.dependency_analysis(go_files, repo_path)
        elif analysis_type == "complexity_analysis":
            return self.complexity_analysis(go_files)
        elif analysis_type == "security_analysis":
            return self.security_analysis(go_files)
        elif analysis_type == "architecture_analysis":
            return self.architecture_analysis(go_files, repo_path)
        else:
            return {"error": f"Unsupported analysis type: {analysis_type}"}
    
    def syntax_analysis(self, go_files: List[str], repo_path: str) -> Dict[str, Any]:
        """Analyze syntax using go build and go vet"""
        results = {
            "total_files": len(go_files),
            "valid_files": 0,
            "build_errors": [],
            "file_stats": {}
        }
        
        # Try to build the project
        try:
            build_result = subprocess.run(
                ["go", "build", "./..."],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if build_result.returncode == 0:
                results["valid_files"] = len(go_files)
            else:
                self.parse_go_errors(build_result.stderr, results)
                
        except subprocess.TimeoutExpired:
            results["build_errors"].append("Build timeout - project too large or complex")
        except Exception as e:
            results["build_errors"].append(f"Build failed: {str(e)}")
        
        # Try go vet for additional checks
        try:
            vet_result = subprocess.run(
                ["go", "vet", "./..."],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if vet_result.returncode != 0:
                self.parse_go_errors(vet_result.stderr, results, "vet")
                
        except Exception as e:
            results["build_errors"].append(f"Go vet failed: {str(e)}")
        
        # Analyze individual files
        for file_path in go_files:
            try:
                stats = self.collect_file_stats(file_path)
                results["file_stats"][file_path] = stats
            except Exception as e:
                logger.warning(f"Failed to analyze file {file_path}: {e}")
        
        return results
    
    def parse_go_errors(self, stderr: str, results: Dict[str, Any], tool: str = "build"):
        """Parse Go build or vet errors"""
        lines = stderr.split('\n')
        for line in lines:
            if line.strip() and not line.startswith('#'):
                results["build_errors"].append(f"{tool}: {line.strip()}")
    
    def collect_file_stats(self, file_path: str) -> Dict[str, Any]:
        """Collect statistics from Go file"""
        stats = {
            "functions": 0,
            "structs": 0,
            "interfaces": 0,
            "imports": 0,
            "lines_of_code": 0,
            "functions_list": [],
            "structs_list": [],
            "interfaces_list": [],
            "imports_list": []
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
            
            # Functions
            func_pattern = r'func\s+(?:\([^)]*\)\s+)?(\w+)\s*\('
            functions = re.findall(func_pattern, content)
            stats["functions"] = len(functions)
            stats["functions_list"] = functions
            
            # Structs
            struct_pattern = r'type\s+(\w+)\s+struct'
            structs = re.findall(struct_pattern, content)
            stats["structs"] = len(structs)
            stats["structs_list"] = structs
            
            # Interfaces
            interface_pattern = r'type\s+(\w+)\s+interface'
            interfaces = re.findall(interface_pattern, content)
            stats["interfaces"] = len(interfaces)
            stats["interfaces_list"] = interfaces
            
            # Imports
            import_pattern = r'import\s+(?:\(\s*([^)]+)\s*\)|"([^"]+)")'
            import_matches = re.findall(import_pattern, content, re.MULTILINE | re.DOTALL)
            
            imports = []
            for match in import_matches:
                if match[0]:  # Multi-line import
                    import_lines = match[0].split('\n')
                    for line in import_lines:
                        line = line.strip()
                        if line and '"' in line:
                            import_name = re.findall(r'"([^"]+)"', line)
                            imports.extend(import_name)
                elif match[1]:  # Single import
                    imports.append(match[1])
            
            stats["imports"] = len(imports)
            stats["imports_list"] = imports
            
        except Exception as e:
            logger.warning(f"Error analyzing file {file_path}: {e}")
        
        return stats
    
    def dependency_analysis(self, go_files: List[str], repo_path: str) -> Dict[str, Any]:
        """Analyze dependencies using go.mod and imports"""
        dependencies = defaultdict(set)
        module_dependencies = set()
        
        # Parse go.mod for external dependencies
        go_mod_path = os.path.join(repo_path, 'go.mod')
        if os.path.exists(go_mod_path):
            try:
                with open(go_mod_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Parse require statements
                require_pattern = r'require\s+([^\s]+)\s+([^\s]+)'
                requires = re.findall(require_pattern, content)
                
                for module, version in requires:
                    module_dependencies.add(f"{module}@{version}")
                    
            except Exception as e:
                logger.warning(f"Failed to parse go.mod: {e}")
        
        # Analyze import statements in Go files
        for file_path in go_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Find import statements
                import_pattern = r'import\s+(?:\(\s*([^)]+)\s*\)|"([^"]+)")'
                import_matches = re.findall(import_pattern, content, re.MULTILINE | re.DOTALL)
                
                for match in import_matches:
                    if match[0]:  # Multi-line import
                        import_lines = match[0].split('\n')
                        for line in import_lines:
                            line = line.strip()
                            if line and '"' in line:
                                import_names = re.findall(r'"([^"]+)"', line)
                                dependencies[file_path].update(import_names)
                    elif match[1]:  # Single import
                        dependencies[file_path].add(match[1])
                        
            except Exception as e:
                logger.warning(f"Failed to analyze dependencies in {file_path}: {e}")
        
        # Convert to serializable format
        dependency_graph = {}
        for file_path, deps in dependencies.items():
            dependency_graph[file_path] = list(deps)
        
        return {
            "dependency_graph": dependency_graph,
            "module_dependencies": list(module_dependencies),
            "total_dependencies": sum(len(deps) for deps in dependencies.values()),
            "total_modules": len(module_dependencies)
        }
    
    def complexity_analysis(self, go_files: List[str]) -> Dict[str, Any]:
        """Analyze code complexity"""
        results = {
            "file_complexity": {},
            "total_complexity": 0,
            "high_complexity_functions": []
        }
        
        for file_path in go_files:
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
        """Calculate cyclomatic complexity for Go code"""
        complexity_info = {
            "total_complexity": 1,
            "functions": []
        }
        
        # Find functions and calculate their complexity
        func_pattern = r'func\s+(?:\([^)]*\)\s+)?(\w+)\s*\([^)]*\)\s*(?:[^{]*)?{'
        matches = re.finditer(func_pattern, content)
        
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
                    "complexity": func_complexity
                })
                complexity_info["total_complexity"] += func_complexity
        
        return complexity_info
    
    def calculate_function_complexity(self, func_body: str) -> int:
        """Calculate complexity for a single function"""
        complexity = 1  # Base complexity
        
        # Count decision points
        decision_patterns = [
            r'\bif\s+',
            r'\bfor\s+',
            r'\bswitch\s+',
            r'\bselect\s+',
            r'\bcase\s+',
            r'&&',
            r'\|\|'
        ]
        
        for pattern in decision_patterns:
            matches = re.findall(pattern, func_body)
            complexity += len(matches)
        
        return complexity
    
    def security_analysis(self, go_files: List[str]) -> Dict[str, Any]:
        """Basic security analysis"""
        security_issues = []
        
        dangerous_patterns = [
            (r'exec\.Command\s*\(', 'Command execution - potential injection risk'),
            (r'os\.Getenv\s*\(\s*"(?:PASSWORD|SECRET|KEY|TOKEN)"', 'Environment variable access - potential secret exposure'),
            (r'fmt\.Printf?\s*\([^,)]*%[sv]', 'Format string - ensure input validation'),
            (r'unsafe\.Pointer', 'Unsafe pointer usage - memory safety risk'),
            (r'crypto/md5|crypto/sha1', 'Weak cryptographic hash usage'),
            (r'math/rand\.', 'Non-cryptographic random - use crypto/rand for security'),
            (r'http\.DefaultTransport', 'Default HTTP transport - consider custom with timeouts'),
            (r'TLSClientConfig.*InsecureSkipVerify.*true', 'TLS verification disabled'),
        ]
        
        for file_path in go_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                lines = content.split('\n')
                for line_num, line in enumerate(lines, 1):
                    for pattern, description in dangerous_patterns:
                        if re.search(pattern, line):
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
    
    def architecture_analysis(self, go_files: List[str], repo_path: str) -> Dict[str, Any]:
        """Analyze architectural patterns"""
        patterns = {
            "go_modules": False,
            "microservice_indicators": [],
            "package_structure": {},
            "main_packages": 0,
            "test_coverage": False
        }
        
        # Check for Go modules
        if os.path.exists(os.path.join(repo_path, 'go.mod')):
            patterns["go_modules"] = True
        
        # Analyze package structure
        packages = defaultdict(list)
        main_count = 0
        
        for file_path in go_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Find package declaration
                package_match = re.search(r'package\s+(\w+)', content)
                if package_match:
                    package_name = package_match.group(1)
                    packages[package_name].append(os.path.basename(file_path))
                    
                    if package_name == 'main':
                        main_count += 1
                        
            except Exception as e:
                logger.warning(f"Failed to analyze package in {file_path}: {e}")
        
        patterns["package_structure"] = dict(packages)
        patterns["main_packages"] = main_count
        
        # Look for microservice indicators
        microservice_indicators = []
        all_content = ""
        
        for file_path in go_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    all_content += content
            except:
                continue
        
        # Check for common microservice patterns
        if 'http.ListenAndServe' in all_content or 'gin.New' in all_content:
            microservice_indicators.append("HTTP server")
        
        if 'grpc' in all_content.lower():
            microservice_indicators.append("gRPC service")
        
        if 'docker' in all_content.lower() or os.path.exists(os.path.join(repo_path, 'Dockerfile')):
            microservice_indicators.append("Containerized")
        
        if 'kubernetes' in all_content.lower() or any(f.endswith('.yaml') or f.endswith('.yml') for f in os.listdir(repo_path)):
            microservice_indicators.append("Kubernetes ready")
        
        patterns["microservice_indicators"] = microservice_indicators
        
        # Check for test files
        test_files = [f for f in go_files if f.endswith('_test.go')]
        patterns["test_coverage"] = len(test_files) > 0
        
        return patterns