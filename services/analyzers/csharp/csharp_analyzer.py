import os
import json
import logging
import subprocess
import xml.etree.ElementTree as ET
from typing import Dict, List, Any
from pathlib import Path
import re
from collections import defaultdict

logger = logging.getLogger(__name__)

class CSharpAnalyzer:
    def __init__(self):
        self.supported_analysis_types = [
            "syntax_analysis",
            "dependency_analysis", 
            "complexity_analysis",
            "security_analysis",
            "architecture_analysis"
        ]
    
    def analyze_repository(self, repo_path: str, analysis_types: List[str]) -> Dict[str, Any]:
        """Analyze C# code in a repository"""
        results = {
            "language": "csharp",
            "repository_path": repo_path,
            "analysis_types": analysis_types,
            "files_analyzed": 0,
            "analysis_results": {}
        }
        
        # Find all C# files
        csharp_files = self.find_csharp_files(repo_path)
        results["files_analyzed"] = len(csharp_files)
        
        if not csharp_files:
            logger.warning(f"No C# files found in {repo_path}")
            return results
        
        # Perform requested analysis types
        for analysis_type in analysis_types:
            if analysis_type in self.supported_analysis_types:
                logger.info(f"Running {analysis_type} on {len(csharp_files)} files")
                results["analysis_results"][analysis_type] = self.run_analysis(
                    analysis_type, csharp_files, repo_path
                )
        
        return results
    
    def find_csharp_files(self, repo_path: str) -> List[str]:
        """Find all C# files in the repository"""
        csharp_files = []
        
        for root, dirs, files in os.walk(repo_path):
            # Skip common directories
            dirs[:] = [d for d in dirs if d not in ['.git', 'bin', 'obj', 'packages', '.vs']]
            
            for file in files:
                if file.endswith('.cs'):
                    csharp_files.append(os.path.join(root, file))
        
        return csharp_files
    
    def run_analysis(self, analysis_type: str, csharp_files: List[str], repo_path: str) -> Dict[str, Any]:
        """Run specific analysis type"""
        if analysis_type == "syntax_analysis":
            return self.syntax_analysis(csharp_files, repo_path)
        elif analysis_type == "dependency_analysis":
            return self.dependency_analysis(csharp_files, repo_path)
        elif analysis_type == "complexity_analysis":
            return self.complexity_analysis(csharp_files)
        elif analysis_type == "security_analysis":
            return self.security_analysis(csharp_files)
        elif analysis_type == "architecture_analysis":
            return self.architecture_analysis(csharp_files, repo_path)
        else:
            return {"error": f"Unsupported analysis type: {analysis_type}"}
    
    def syntax_analysis(self, csharp_files: List[str], repo_path: str) -> Dict[str, Any]:
        """Analyze syntax using dotnet build"""
        results = {
            "total_files": len(csharp_files),
            "valid_files": 0,
            "build_errors": [],
            "file_stats": {}
        }
        
        # Try to build the project to catch syntax errors
        try:
            build_result = subprocess.run(
                ["dotnet", "build", "--no-restore", "--verbosity", "quiet"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if build_result.returncode == 0:
                results["valid_files"] = len(csharp_files)
            else:
                # Parse build errors
                self.parse_build_errors(build_result.stderr, results)
        except subprocess.TimeoutExpired:
            results["build_errors"].append("Build timeout - project too large or complex")
        except Exception as e:
            results["build_errors"].append(f"Build failed: {str(e)}")
        
        # Analyze individual files
        for file_path in csharp_files:
            try:
                stats = self.collect_file_stats(file_path)
                results["file_stats"][file_path] = stats
            except Exception as e:
                logger.warning(f"Failed to analyze file {file_path}: {e}")
        
        return results
    
    def parse_build_errors(self, stderr: str, results: Dict[str, Any]):
        """Parse dotnet build errors"""
        lines = stderr.split('\n')
        for line in lines:
            if 'error CS' in line:
                results["build_errors"].append(line.strip())
    
    def collect_file_stats(self, file_path: str) -> Dict[str, Any]:
        """Collect statistics from C# file"""
        stats = {
            "classes": 0,
            "interfaces": 0,
            "methods": 0,
            "properties": 0,
            "usings": 0,
            "lines_of_code": 0,
            "classes_list": [],
            "interfaces_list": [],
            "methods_list": [],
            "usings_list": []
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
            
            # Use regex patterns to find C# constructs
            # Classes
            class_pattern = r'(?:public|private|protected|internal)?\s*(?:abstract|sealed)?\s*class\s+(\w+)'
            classes = re.findall(class_pattern, content, re.MULTILINE)
            stats["classes"] = len(classes)
            stats["classes_list"] = classes
            
            # Interfaces
            interface_pattern = r'(?:public|private|protected|internal)?\s*interface\s+(\w+)'
            interfaces = re.findall(interface_pattern, content, re.MULTILINE)
            stats["interfaces"] = len(interfaces)
            stats["interfaces_list"] = interfaces
            
            # Methods
            method_pattern = r'(?:public|private|protected|internal)?\s*(?:static)?\s*(?:virtual|override|abstract)?\s*\w+\s+(\w+)\s*\([^)]*\)'
            methods = re.findall(method_pattern, content, re.MULTILINE)
            stats["methods"] = len(methods)
            stats["methods_list"] = methods
            
            # Properties
            property_pattern = r'(?:public|private|protected|internal)?\s*(?:static)?\s*\w+\s+(\w+)\s*{\s*(?:get|set)'
            properties = re.findall(property_pattern, content, re.MULTILINE)
            stats["properties"] = len(properties)
            
            # Using statements
            using_pattern = r'using\s+([\w.]+);'
            usings = re.findall(using_pattern, content)
            stats["usings"] = len(usings)
            stats["usings_list"] = usings
            
        except Exception as e:
            logger.warning(f"Error analyzing file {file_path}: {e}")
        
        return stats
    
    def dependency_analysis(self, csharp_files: List[str], repo_path: str) -> Dict[str, Any]:
        """Analyze dependencies between files and external packages"""
        dependencies = defaultdict(set)
        package_dependencies = set()
        
        # Analyze project files for package references
        project_files = []
        for root, dirs, files in os.walk(repo_path):
            for file in files:
                if file.endswith('.csproj') or file.endswith('.sln'):
                    project_files.append(os.path.join(root, file))
        
        # Parse project files for package references
        for proj_file in project_files:
            try:
                self.parse_project_file(proj_file, package_dependencies)
            except Exception as e:
                logger.warning(f"Failed to parse project file {proj_file}: {e}")
        
        # Analyze using statements in C# files
        for file_path in csharp_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Find using statements
                using_pattern = r'using\s+([\w.]+);'
                usings = re.findall(using_pattern, content)
                
                for using in usings:
                    dependencies[file_path].add(using)
                    
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
    
    def parse_project_file(self, proj_file: str, package_dependencies: set):
        """Parse .csproj file for package references"""
        try:
            tree = ET.parse(proj_file)
            root = tree.getroot()
            
            # Find PackageReference elements
            for package_ref in root.findall('.//PackageReference'):
                include = package_ref.get('Include')
                if include:
                    package_dependencies.add(include)
                    
        except ET.ParseError:
            # Try simple regex parsing for malformed XML
            with open(proj_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            package_pattern = r'<PackageReference\s+Include="([^"]+)"'
            packages = re.findall(package_pattern, content)
            package_dependencies.update(packages)
    
    def complexity_analysis(self, csharp_files: List[str]) -> Dict[str, Any]:
        """Analyze code complexity"""
        results = {
            "file_complexity": {},
            "total_complexity": 0,
            "high_complexity_methods": []
        }
        
        for file_path in csharp_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                complexity = self.calculate_cyclomatic_complexity(content, file_path)
                results["file_complexity"][file_path] = complexity
                results["total_complexity"] += complexity["total_complexity"]
                
                # Identify high complexity methods
                for method_info in complexity["methods"]:
                    if method_info["complexity"] > 10:
                        results["high_complexity_methods"].append({
                            "file": file_path,
                            "method": method_info["name"],
                            "complexity": method_info["complexity"]
                        })
                        
            except Exception as e:
                logger.warning(f"Failed to analyze complexity in {file_path}: {e}")
        
        return results
    
    def calculate_cyclomatic_complexity(self, content: str, file_path: str) -> Dict[str, Any]:
        """Calculate cyclomatic complexity for C# code"""
        complexity_info = {
            "total_complexity": 1,
            "methods": []
        }
        
        # Find methods and calculate their complexity
        method_pattern = r'(?:public|private|protected|internal)?\s*(?:static)?\s*(?:virtual|override|abstract)?\s*\w+\s+(\w+)\s*\([^)]*\)\s*{'
        methods = re.finditer(method_pattern, content, re.MULTILINE)
        
        for method_match in methods:
            method_name = method_match.group(1)
            
            # Find the method body (simplified - assumes proper bracing)
            start_pos = method_match.end()
            brace_count = 1
            end_pos = start_pos
            
            for i, char in enumerate(content[start_pos:], start_pos):
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end_pos = i
                        break
            
            method_body = content[start_pos:end_pos]
            method_complexity = self.calculate_method_complexity(method_body)
            
            complexity_info["methods"].append({
                "name": method_name,
                "complexity": method_complexity
            })
            complexity_info["total_complexity"] += method_complexity
        
        return complexity_info
    
    def calculate_method_complexity(self, method_body: str) -> int:
        """Calculate complexity for a single method"""
        complexity = 1  # Base complexity
        
        # Count decision points
        decision_patterns = [
            r'\bif\s*\(',
            r'\bwhile\s*\(',
            r'\bfor\s*\(',
            r'\bforeach\s*\(',
            r'\bswitch\s*\(',
            r'\bcatch\s*\(',
            r'\?\s*',  # Ternary operator
            r'&&',     # Logical AND
            r'\|\|'    # Logical OR
        ]
        
        for pattern in decision_patterns:
            matches = re.findall(pattern, method_body)
            complexity += len(matches)
        
        return complexity
    
    def security_analysis(self, csharp_files: List[str]) -> Dict[str, Any]:
        """Basic security analysis"""
        security_issues = []
        
        dangerous_patterns = [
            (r'System\.Diagnostics\.Process\.Start', 'Process execution - potential command injection'),
            (r'System\.IO\.File\.Delete', 'File deletion - ensure proper validation'),
            (r'System\.Reflection\.Assembly\.Load', 'Dynamic assembly loading - security risk'),
            (r'eval\s*\(', 'Dynamic code evaluation - avoid if possible'),
            (r'innerHTML\s*=', 'innerHTML assignment - potential XSS'),
            (r'password.*=.*".*"', 'Hardcoded password detected'),
            (r'connectionString.*=.*".*"', 'Hardcoded connection string'),
        ]
        
        for file_path in csharp_files:
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
    
    def architecture_analysis(self, csharp_files: List[str], repo_path: str) -> Dict[str, Any]:
        """Analyze architectural patterns"""
        patterns = {
            "mvc_pattern": False,
            "repository_pattern": False,
            "dependency_injection": False,
            "namespace_structure": {},
            "project_structure": {}
        }
        
        # Analyze namespace structure
        namespaces = defaultdict(list)
        for file_path in csharp_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                namespace_pattern = r'namespace\s+([\w.]+)'
                namespace_matches = re.findall(namespace_pattern, content)
                
                for namespace in namespace_matches:
                    namespaces[namespace].append(os.path.basename(file_path))
                    
            except Exception as e:
                logger.warning(f"Failed to analyze namespace in {file_path}: {e}")
        
        patterns["namespace_structure"] = dict(namespaces)
        
        # Check for common patterns
        all_content = ""
        for file_path in csharp_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    all_content += f.read()
            except:
                continue
        
        # MVC pattern detection
        if any(keyword in all_content for keyword in ['Controller', 'Model', 'View']):
            patterns["mvc_pattern"] = True
        
        # Repository pattern detection
        if 'Repository' in all_content and 'interface' in all_content:
            patterns["repository_pattern"] = True
        
        # Dependency injection detection
        if any(keyword in all_content for keyword in ['IServiceCollection', 'AddScoped', 'AddTransient']):
            patterns["dependency_injection"] = True
        
        return patterns