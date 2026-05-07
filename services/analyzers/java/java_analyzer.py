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

class JavaAnalyzer:
    def __init__(self):
        self.supported_analysis_types = [
            "syntax_analysis",
            "dependency_analysis", 
            "complexity_analysis",
            "security_analysis",
            "architecture_analysis"
        ]
    
    def analyze_repository(self, repo_path: str, analysis_types: List[str]) -> Dict[str, Any]:
        """Analyze Java code in a repository"""
        results = {
            "language": "java",
            "repository_path": repo_path,
            "analysis_types": analysis_types,
            "files_analyzed": 0,
            "analysis_results": {}
        }
        
        # Find all Java files
        java_files = self.find_java_files(repo_path)
        results["files_analyzed"] = len(java_files)
        
        if not java_files:
            logger.warning(f"No Java files found in {repo_path}")
            return results
        
        # Perform requested analysis types
        for analysis_type in analysis_types:
            if analysis_type in self.supported_analysis_types:
                logger.info(f"Running {analysis_type} on {len(java_files)} files")
                results["analysis_results"][analysis_type] = self.run_analysis(
                    analysis_type, java_files, repo_path
                )
        
        return results
    
    def find_java_files(self, repo_path: str) -> List[str]:
        """Find all Java files in the repository"""
        java_files = []
        
        for root, dirs, files in os.walk(repo_path):
            # Skip common directories
            dirs[:] = [d for d in dirs if d not in ['.git', 'target', 'build', '.gradle', 'bin']]
            
            for file in files:
                if file.endswith('.java'):
                    java_files.append(os.path.join(root, file))
        
        return java_files
    
    def run_analysis(self, analysis_type: str, java_files: List[str], repo_path: str) -> Dict[str, Any]:
        """Run specific analysis type"""
        if analysis_type == "syntax_analysis":
            return self.syntax_analysis(java_files, repo_path)
        elif analysis_type == "dependency_analysis":
            return self.dependency_analysis(java_files, repo_path)
        elif analysis_type == "complexity_analysis":
            return self.complexity_analysis(java_files)
        elif analysis_type == "security_analysis":
            return self.security_analysis(java_files)
        elif analysis_type == "architecture_analysis":
            return self.architecture_analysis(java_files, repo_path)
        else:
            return {"error": f"Unsupported analysis type: {analysis_type}"}
    
    def syntax_analysis(self, java_files: List[str], repo_path: str) -> Dict[str, Any]:
        """Analyze syntax using javac or build tools"""
        results = {
            "total_files": len(java_files),
            "valid_files": 0,
            "build_errors": [],
            "file_stats": {}
        }
        
        # Try Maven build first
        if os.path.exists(os.path.join(repo_path, 'pom.xml')):
            try:
                build_result = subprocess.run(
                    ["mvn", "compile", "-q"],
                    cwd=repo_path,
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                
                if build_result.returncode == 0:
                    results["valid_files"] = len(java_files)
                else:
                    self.parse_maven_errors(build_result.stderr, results)
                    
            except subprocess.TimeoutExpired:
                results["build_errors"].append("Maven build timeout")
            except Exception as e:
                results["build_errors"].append(f"Maven build failed: {str(e)}")
        
        # Try Gradle build
        elif os.path.exists(os.path.join(repo_path, 'build.gradle')) or os.path.exists(os.path.join(repo_path, 'build.gradle.kts')):
            try:
                build_result = subprocess.run(
                    ["gradle", "compileJava", "-q"],
                    cwd=repo_path,
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                
                if build_result.returncode == 0:
                    results["valid_files"] = len(java_files)
                else:
                    self.parse_gradle_errors(build_result.stderr, results)
                    
            except subprocess.TimeoutExpired:
                results["build_errors"].append("Gradle build timeout")
            except Exception as e:
                results["build_errors"].append(f"Gradle build failed: {str(e)}")
        
        # Analyze individual files
        valid_count = 0
        for file_path in java_files:
            try:
                stats = self.collect_file_stats(file_path)
                results["file_stats"][file_path] = stats
                if stats.get("syntax_valid", True):
                    valid_count += 1
            except Exception as e:
                logger.warning(f"Failed to analyze file {file_path}: {e}")
        
        # Update valid files count if no build tool was used
        if not results["build_errors"]:
            results["valid_files"] = valid_count
        
        return results
    
    def parse_maven_errors(self, stderr: str, results: Dict[str, Any]):
        """Parse Maven compilation errors"""
        lines = stderr.split('\n')
        for line in lines:
            if 'ERROR' in line or 'COMPILATION ERROR' in line:
                results["build_errors"].append(line.strip())
    
    def parse_gradle_errors(self, stderr: str, results: Dict[str, Any]):
        """Parse Gradle compilation errors"""
        lines = stderr.split('\n')
        for line in lines:
            if 'error:' in line.lower():
                results["build_errors"].append(line.strip())
    
    def collect_file_stats(self, file_path: str) -> Dict[str, Any]:
        """Collect statistics from Java file"""
        stats = {
            "classes": 0,
            "interfaces": 0,
            "methods": 0,
            "fields": 0,
            "imports": 0,
            "lines_of_code": 0,
            "classes_list": [],
            "interfaces_list": [],
            "methods_list": [],
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
            
            # Classes
            class_pattern = r'(?:public|private|protected)?\s*(?:abstract|final)?\s*class\s+(\w+)'
            classes = re.findall(class_pattern, content)
            stats["classes"] = len(classes)
            stats["classes_list"] = classes
            
            # Interfaces
            interface_pattern = r'(?:public|private|protected)?\s*interface\s+(\w+)'
            interfaces = re.findall(interface_pattern, content)
            stats["interfaces"] = len(interfaces)
            stats["interfaces_list"] = interfaces
            
            # Methods
            method_pattern = r'(?:public|private|protected)?\s*(?:static)?\s*(?:final)?\s*\w+\s+(\w+)\s*\([^)]*\)\s*(?:throws[^{]*)?{'
            methods = re.findall(method_pattern, content)
            stats["methods"] = len(methods)
            stats["methods_list"] = methods
            
            # Fields
            field_pattern = r'(?:public|private|protected)?\s*(?:static)?\s*(?:final)?\s*\w+\s+(\w+)\s*[=;]'
            fields = re.findall(field_pattern, content)
            stats["fields"] = len(fields)
            
            # Imports
            import_pattern = r'import\s+(?:static\s+)?([\w.]+(?:\.\*)?);'
            imports = re.findall(import_pattern, content)
            stats["imports"] = len(imports)
            stats["imports_list"] = imports
            
        except Exception as e:
            logger.warning(f"Error analyzing file {file_path}: {e}")
            stats["syntax_valid"] = False
        
        return stats
    
    def dependency_analysis(self, java_files: List[str], repo_path: str) -> Dict[str, Any]:
        """Analyze dependencies from pom.xml, build.gradle, and imports"""
        dependencies = defaultdict(set)
        external_dependencies = set()
        
        # Parse Maven dependencies
        pom_path = os.path.join(repo_path, 'pom.xml')
        if os.path.exists(pom_path):
            try:
                self.parse_maven_dependencies(pom_path, external_dependencies)
            except Exception as e:
                logger.warning(f"Failed to parse pom.xml: {e}")
        
        # Parse Gradle dependencies
        build_gradle_path = os.path.join(repo_path, 'build.gradle')
        if os.path.exists(build_gradle_path):
            try:
                self.parse_gradle_dependencies(build_gradle_path, external_dependencies)
            except Exception as e:
                logger.warning(f"Failed to parse build.gradle: {e}")
        
        # Analyze import statements
        for file_path in java_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                import_pattern = r'import\s+(?:static\s+)?([\w.]+(?:\.\*)?);'
                imports = re.findall(import_pattern, content)
                dependencies[file_path].update(imports)
                
            except Exception as e:
                logger.warning(f"Failed to analyze dependencies in {file_path}: {e}")
        
        # Convert to serializable format
        dependency_graph = {}
        for file_path, deps in dependencies.items():
            dependency_graph[file_path] = list(deps)
        
        return {
            "dependency_graph": dependency_graph,
            "external_dependencies": list(external_dependencies),
            "total_dependencies": sum(len(deps) for deps in dependencies.values()),
            "total_external": len(external_dependencies)
        }
    
    def parse_maven_dependencies(self, pom_path: str, external_dependencies: set):
        """Parse Maven pom.xml for dependencies"""
        tree = ET.parse(pom_path)
        root = tree.getroot()
        
        # Handle namespaces
        ns = {'maven': 'http://maven.apache.org/POM/4.0.0'}
        if root.tag.startswith('{'):
            ns_uri = root.tag.split('}')[0][1:]
            ns = {'maven': ns_uri}
        
        # Find dependencies
        for dependency in root.findall('.//maven:dependency', ns):
            group_id = dependency.find('maven:groupId', ns)
            artifact_id = dependency.find('maven:artifactId', ns)
            version = dependency.find('maven:version', ns)
            
            if group_id is not None and artifact_id is not None:
                dep_name = f"{group_id.text}:{artifact_id.text}"
                if version is not None:
                    dep_name += f":{version.text}"
                external_dependencies.add(dep_name)
    
    def parse_gradle_dependencies(self, build_gradle_path: str, external_dependencies: set):
        """Parse Gradle build.gradle for dependencies"""
        with open(build_gradle_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Simple regex parsing for dependencies
        dep_patterns = [
            r'implementation\s+[\'"]([^\'"]+)[\'"]',
            r'compile\s+[\'"]([^\'"]+)[\'"]',
            r'testImplementation\s+[\'"]([^\'"]+)[\'"]',
            r'api\s+[\'"]([^\'"]+)[\'"]'
        ]
        
        for pattern in dep_patterns:
            matches = re.findall(pattern, content)
            external_dependencies.update(matches)
    
    def complexity_analysis(self, java_files: List[str]) -> Dict[str, Any]:
        """Analyze code complexity"""
        results = {
            "file_complexity": {},
            "total_complexity": 0,
            "high_complexity_methods": []
        }
        
        for file_path in java_files:
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
        """Calculate cyclomatic complexity for Java code"""
        complexity_info = {
            "total_complexity": 1,
            "methods": []
        }
        
        # Find methods and calculate their complexity
        method_pattern = r'(?:public|private|protected)?\s*(?:static)?\s*(?:final)?\s*\w+\s+(\w+)\s*\([^)]*\)\s*(?:throws[^{]*)?{'
        matches = re.finditer(method_pattern, content)
        
        for match in matches:
            method_name = match.group(1)
            
            # Find method body (simplified)
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
                method_body = content[start_pos:end_pos + 1]
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
            r'\bswitch\s*\(',
            r'\bcatch\s*\(',
            r'\?\s*.*?\s*:',  # Ternary operator
            r'&&',            # Logical AND
            r'\|\|'           # Logical OR
        ]
        
        for pattern in decision_patterns:
            matches = re.findall(pattern, method_body)
            complexity += len(matches)
        
        return complexity
    
    def security_analysis(self, java_files: List[str]) -> Dict[str, Any]:
        """Basic security analysis"""
        security_issues = []
        
        dangerous_patterns = [
            (r'Runtime\.getRuntime\(\)\.exec', 'Runtime.exec() - command injection risk'),
            (r'ProcessBuilder', 'ProcessBuilder - command execution risk'),
            (r'Class\.forName', 'Class.forName() - code injection risk'),
            (r'System\.getProperty\s*\(\s*"(?:user\.home|java\.io\.tmpdir)"', 'System property access - path traversal risk'),
            (r'new\s+FileInputStream\s*\(\s*[^)]*\)', 'FileInputStream - ensure input validation'),
            (r'new\s+FileOutputStream\s*\(\s*[^)]*\)', 'FileOutputStream - ensure path validation'),
            (r'MessageDigest\.getInstance\s*\(\s*"MD5"', 'MD5 usage - weak cryptography'),
            (r'MessageDigest\.getInstance\s*\(\s*"SHA1"', 'SHA1 usage - weak cryptography'),
            (r'new\s+Random\s*\(\s*\)', 'java.util.Random - not cryptographically secure'),
            (r'setHostnameVerifier.*ALLOW_ALL', 'Hostname verification disabled'),
        ]
        
        for file_path in java_files:
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
    
    def architecture_analysis(self, java_files: List[str], repo_path: str) -> Dict[str, Any]:
        """Analyze architectural patterns"""
        patterns = {
            "build_tool": None,
            "framework_detected": [],
            "package_structure": {},
            "design_patterns": [],
            "spring_annotations": []
        }
        
        # Detect build tool
        if os.path.exists(os.path.join(repo_path, 'pom.xml')):
            patterns["build_tool"] = "Maven"
        elif os.path.exists(os.path.join(repo_path, 'build.gradle')):
            patterns["build_tool"] = "Gradle"
        
        # Analyze package structure and detect frameworks
        packages = defaultdict(list)
        all_content = ""
        
        for file_path in java_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    all_content += content
                
                # Find package declaration
                package_match = re.search(r'package\s+([\w.]+);', content)
                if package_match:
                    package_name = package_match.group(1)
                    packages[package_name].append(os.path.basename(file_path))
                    
            except Exception as e:
                logger.warning(f"Failed to analyze package in {file_path}: {e}")
        
        patterns["package_structure"] = dict(packages)
        
        # Framework detection
        frameworks = []
        if 'org.springframework' in all_content:
            frameworks.append("Spring Framework")
        if 'javax.servlet' in all_content or 'jakarta.servlet' in all_content:
            frameworks.append("Java Servlets")
        if 'org.hibernate' in all_content:
            frameworks.append("Hibernate")
        if 'com.fasterxml.jackson' in all_content:
            frameworks.append("Jackson")
        if 'org.junit' in all_content:
            frameworks.append("JUnit")
        
        patterns["framework_detected"] = frameworks
        
        # Design pattern detection
        design_patterns = []
        if re.search(r'class\s+\w*Factory', all_content):
            design_patterns.append("Factory Pattern")
        if re.search(r'class\s+\w*Builder', all_content):
            design_patterns.append("Builder Pattern")
        if re.search(r'class\s+\w*Singleton', all_content):
            design_patterns.append("Singleton Pattern")
        if re.search(r'class\s+\w*Observer', all_content):
            design_patterns.append("Observer Pattern")
        
        patterns["design_patterns"] = design_patterns
        
        # Spring annotations
        spring_annotations = []
        spring_annotation_patterns = [
            r'@Controller', r'@Service', r'@Repository', r'@Component',
            r'@RestController', r'@Autowired', r'@RequestMapping'
        ]
        
        for pattern in spring_annotation_patterns:
            if re.search(pattern, all_content):
                spring_annotations.append(pattern[1:])  # Remove @ symbol
        
        patterns["spring_annotations"] = spring_annotations
        
        return patterns