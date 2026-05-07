import os
import json
import logging
import re
from typing import Dict, List, Any, Set, Tuple
from pathlib import Path
import networkx as nx
from collections import defaultdict
import pandas as pd

logger = logging.getLogger(__name__)

class PolyglotAnalyzer:
    """
    Analyzes cross-language dependencies and architectural patterns
    This is PCARA's unique value proposition - understanding polyglot codebases
    """
    
    def __init__(self):
        self.language_extensions = {
            'python': ['.py'],
            'javascript': ['.js', '.jsx', '.ts', '.tsx', '.mjs'],
            'csharp': ['.cs'],
            'java': ['.java'],
            'go': ['.go'],
            'rust': ['.rs'],
            'php': ['.php'],
            'ruby': ['.rb'],
            'cpp': ['.cpp', '.cxx', '.cc', '.h', '.hpp'],
            'c': ['.c', '.h']
        }
        
        # Common inter-language communication patterns
        self.communication_patterns = {
            'api_calls': [
                r'fetch\s*\(\s*[\'"`]([^\'"`]+)[\'"`]',  # JavaScript fetch
                r'requests\.(get|post|put|delete)\s*\(\s*[\'"`]([^\'"`]+)[\'"`]',  # Python requests
                r'HttpClient\.\w+\s*\(\s*[\'"`]([^\'"`]+)[\'"`]',  # C# HttpClient
                r'curl\s+[\'"`]([^\'"`]+)[\'"`]',  # cURL commands
            ],
            'database_connections': [
                r'(?:postgres|mysql|mongodb|redis)://[^\s\'"`]+',  # Connection strings
                r'(?:Server|Host|Endpoint)\s*=\s*[\'"`]?([^\'"`;\s]+)',  # DB server configs
            ],
            'message_queues': [
                r'(?:rabbitmq|kafka|redis|sqs)://[^\s\'"`]+',  # Message queue URLs
                r'(?:queue|topic|channel)\s*[=:]\s*[\'"`]([^\'"`]+)[\'"`]',  # Queue names
            ],
            'file_references': [
                r'(?:import|require|include)\s+[\'"`]([^\'"`]+\.\w+)[\'"`]',  # File imports
                r'(?:open|read|write)\s*\(\s*[\'"`]([^\'"`]+\.\w+)[\'"`]',  # File operations
            ]
        }
    
    def analyze_cross_language_dependencies(self, repo_path: str, languages: List[str]) -> Dict[str, Any]:
        """
        Main method to analyze cross-language dependencies in a polyglot codebase
        """
        results = {
            "analysis_type": "polyglot_cross_language",
            "repository_path": repo_path,
            "languages_found": [],
            "total_files": 0,
            "cross_language_dependencies": {},
            "communication_patterns": {},
            "architectural_insights": {},
            "dependency_graph": {},
            "hotspots": [],
            "recommendations": []
        }
        
        # Discover all languages in the repository
        language_files = self.discover_languages(repo_path)
        results["languages_found"] = list(language_files.keys())
        results["total_files"] = sum(len(files) for files in language_files.values())
        
        if len(language_files) < 2:
            results["recommendations"].append("Repository appears to be single-language. Consider polyglot analysis when multiple languages are present.")
            return results
        
        # Analyze cross-language dependencies
        results["cross_language_dependencies"] = self.analyze_cross_dependencies(language_files, repo_path)
        
        # Detect communication patterns
        results["communication_patterns"] = self.detect_communication_patterns(language_files, repo_path)
        
        # Build dependency graph
        results["dependency_graph"] = self.build_dependency_graph(results["cross_language_dependencies"])
        
        # Generate architectural insights
        results["architectural_insights"] = self.generate_architectural_insights(
            language_files, results["cross_language_dependencies"], results["communication_patterns"]
        )
        
        # Identify hotspots
        results["hotspots"] = self.identify_hotspots(results["dependency_graph"])
        
        # Generate recommendations
        results["recommendations"] = self.generate_recommendations(results)
        
        return results
    
    def discover_languages(self, repo_path: str) -> Dict[str, List[str]]:
        """Discover all programming languages in the repository"""
        language_files = defaultdict(list)
        
        for root, dirs, files in os.walk(repo_path):
            # Skip common directories
            dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules', 'bin', 'obj', '__pycache__', 'target', 'build', 'dist']]
            
            for file in files:
                file_path = os.path.join(root, file)
                
                # Determine language by extension
                for language, extensions in self.language_extensions.items():
                    if any(file.endswith(ext) for ext in extensions):
                        language_files[language].append(file_path)
                        break
        
        return dict(language_files)
    
    def analyze_cross_dependencies(self, language_files: Dict[str, List[str]], repo_path: str) -> Dict[str, Any]:
        """Analyze dependencies between different languages"""
        cross_deps = {
            "api_dependencies": [],
            "shared_resources": [],
            "configuration_dependencies": [],
            "build_dependencies": []
        }
        
        # Analyze API dependencies
        cross_deps["api_dependencies"] = self.find_api_dependencies(language_files, repo_path)
        
        # Analyze shared resources (configs, data files, etc.)
        cross_deps["shared_resources"] = self.find_shared_resources(language_files, repo_path)
        
        # Analyze configuration dependencies
        cross_deps["configuration_dependencies"] = self.find_config_dependencies(language_files, repo_path)
        
        # Analyze build dependencies
        cross_deps["build_dependencies"] = self.find_build_dependencies(language_files, repo_path)
        
        return cross_deps
    
    def find_api_dependencies(self, language_files: Dict[str, List[str]], repo_path: str) -> List[Dict[str, Any]]:
        """Find API calls between different language components"""
        api_deps = []
        
        # Common API endpoint patterns
        endpoint_patterns = [
            r'[\'"`]/api/[^\'"`\s]+[\'"`]',
            r'[\'"`]/v\d+/[^\'"`\s]+[\'"`]',
            r'localhost:\d+[^\'"`\s]*',
            r'127\.0\.0\.1:\d+[^\'"`\s]*',
        ]
        
        for language, files in language_files.items():
            for file_path in files:
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    for pattern in endpoint_patterns:
                        matches = re.findall(pattern, content, re.IGNORECASE)
                        for match in matches:
                            api_deps.append({
                                "source_file": file_path,
                                "source_language": language,
                                "endpoint": match.strip('\'"'),
                                "type": "api_call"
                            })
                            
                except Exception as e:
                    logger.warning(f"Failed to analyze API dependencies in {file_path}: {e}")
        
        return api_deps
    
    def find_shared_resources(self, language_files: Dict[str, List[str]], repo_path: str) -> List[Dict[str, Any]]:
        """Find shared resources referenced by multiple languages"""
        shared_resources = []
        
        # Find configuration files, data files, etc.
        config_files = []
        data_files = []
        
        for root, dirs, files in os.walk(repo_path):
            for file in files:
                file_path = os.path.join(root, file)
                
                # Configuration files
                if any(file.endswith(ext) for ext in ['.json', '.yaml', '.yml', '.toml', '.ini', '.env', '.config']):
                    config_files.append(file_path)
                
                # Data files
                if any(file.endswith(ext) for ext in ['.csv', '.xml', '.sql', '.db', '.sqlite']):
                    data_files.append(file_path)
        
        # Check which languages reference these shared resources
        for config_file in config_files:
            referring_languages = []
            config_name = os.path.basename(config_file)
            
            for language, files in language_files.items():
                for file_path in files:
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        
                        if config_name in content:
                            referring_languages.append(language)
                            break
                            
                    except Exception:
                        continue
            
            if len(referring_languages) > 1:
                shared_resources.append({
                    "resource_path": config_file,
                    "resource_type": "configuration",
                    "referring_languages": referring_languages,
                    "cross_language_usage": True
                })
        
        return shared_resources
    
    def find_config_dependencies(self, language_files: Dict[str, List[str]], repo_path: str) -> List[Dict[str, Any]]:
        """Find configuration dependencies between languages"""
        config_deps = []
        
        # Common configuration patterns
        config_patterns = [
            (r'PORT\s*=\s*(\d+)', 'port_config'),
            (r'DATABASE_URL\s*=\s*[\'"`]([^\'"`]+)[\'"`]', 'database_config'),
            (r'API_KEY\s*=\s*[\'"`]([^\'"`]+)[\'"`]', 'api_key_config'),
            (r'REDIS_URL\s*=\s*[\'"`]([^\'"`]+)[\'"`]', 'redis_config'),
        ]
        
        for language, files in language_files.items():
            for file_path in files:
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    for pattern, config_type in config_patterns:
                        matches = re.findall(pattern, content, re.IGNORECASE)
                        for match in matches:
                            config_deps.append({
                                "source_file": file_path,
                                "source_language": language,
                                "config_type": config_type,
                                "config_value": match,
                                "line_context": self.get_line_context(content, pattern)
                            })
                            
                except Exception as e:
                    logger.warning(f"Failed to analyze config dependencies in {file_path}: {e}")
        
        return config_deps
    
    def find_build_dependencies(self, language_files: Dict[str, List[str]], repo_path: str) -> List[Dict[str, Any]]:
        """Find build system dependencies between languages"""
        build_deps = []
        
        # Look for build files
        build_files = {
            'docker': ['Dockerfile', 'docker-compose.yml', 'docker-compose.yaml'],
            'make': ['Makefile', 'makefile'],
            'gradle': ['build.gradle', 'settings.gradle'],
            'maven': ['pom.xml'],
            'npm': ['package.json'],
            'pip': ['requirements.txt', 'setup.py', 'pyproject.toml'],
            'go': ['go.mod', 'go.sum'],
            'cargo': ['Cargo.toml'],
            'cmake': ['CMakeLists.txt']
        }
        
        found_build_systems = []
        
        for root, dirs, files in os.walk(repo_path):
            for file in files:
                for build_system, build_file_names in build_files.items():
                    if file in build_file_names:
                        found_build_systems.append({
                            "build_system": build_system,
                            "build_file": os.path.join(root, file),
                            "affects_languages": self.determine_affected_languages(build_system, language_files.keys())
                        })
        
        return found_build_systems
    
    def detect_communication_patterns(self, language_files: Dict[str, List[str]], repo_path: str) -> Dict[str, Any]:
        """Detect communication patterns between language components"""
        patterns = {
            "http_apis": [],
            "message_queues": [],
            "shared_databases": [],
            "file_sharing": []
        }
        
        all_content = ""
        file_contexts = {}
        
        # Collect all file contents for pattern matching
        for language, files in language_files.items():
            for file_path in files:
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        all_content += content + "\n"
                        file_contexts[file_path] = {"language": language, "content": content}
                except Exception:
                    continue
        
        # Detect HTTP API patterns
        http_patterns = [
            r'(?:GET|POST|PUT|DELETE|PATCH)\s+[\'"`]/[^\'"`\s]+[\'"`]',
            r'@app\.route\s*\(\s*[\'"`]([^\'"`]+)[\'"`]',  # Flask routes
            r'app\.(get|post|put|delete)\s*\(\s*[\'"`]([^\'"`]+)[\'"`]',  # Express routes
            r'\[Route\s*\(\s*[\'"`]([^\'"`]+)[\'"`]\s*\)\]',  # ASP.NET routes
        ]
        
        for pattern in http_patterns:
            matches = re.findall(pattern, all_content, re.IGNORECASE)
            patterns["http_apis"].extend(matches)
        
        # Detect message queue usage
        mq_patterns = [
            r'(?:rabbitmq|kafka|redis|sqs|activemq)',
            r'(?:publish|subscribe|queue|topic)',
        ]
        
        for pattern in mq_patterns:
            if re.search(pattern, all_content, re.IGNORECASE):
                patterns["message_queues"].append(pattern)
        
        return patterns
    
    def build_dependency_graph(self, cross_dependencies: Dict[str, Any]) -> Dict[str, Any]:
        """Build a graph representation of cross-language dependencies"""
        G = nx.DiGraph()
        
        # Add nodes for each file/component
        nodes = set()
        edges = []
        
        # Process API dependencies
        for api_dep in cross_dependencies.get("api_dependencies", []):
            source = f"{api_dep['source_language']}:{os.path.basename(api_dep['source_file'])}"
            target = f"api:{api_dep['endpoint']}"
            nodes.add(source)
            nodes.add(target)
            edges.append((source, target, {"type": "api_call"}))
        
        # Process shared resources
        for resource in cross_dependencies.get("shared_resources", []):
            resource_node = f"resource:{os.path.basename(resource['resource_path'])}"
            nodes.add(resource_node)
            
            for language in resource["referring_languages"]:
                lang_node = f"{language}:component"
                nodes.add(lang_node)
                edges.append((lang_node, resource_node, {"type": "shared_resource"}))
        
        # Add nodes and edges to graph
        G.add_nodes_from(nodes)
        G.add_edges_from(edges)
        
        # Calculate graph metrics
        return {
            "nodes": list(G.nodes()),
            "edges": list(G.edges(data=True)),
            "metrics": {
                "total_nodes": G.number_of_nodes(),
                "total_edges": G.number_of_edges(),
                "density": nx.density(G),
                "strongly_connected_components": len(list(nx.strongly_connected_components(G)))
            }
        }
    
    def generate_architectural_insights(self, language_files: Dict[str, List[str]], 
                                      cross_deps: Dict[str, Any], 
                                      comm_patterns: Dict[str, Any]) -> Dict[str, Any]:
        """Generate high-level architectural insights"""
        insights = {
            "architecture_style": "unknown",
            "coupling_level": "unknown",
            "communication_complexity": "low",
            "maintainability_score": 0.0,
            "architectural_patterns": []
        }
        
        # Determine architecture style
        if len(language_files) > 3:
            insights["architecture_style"] = "microservices"
        elif len(language_files) == 2:
            insights["architecture_style"] = "hybrid"
        else:
            insights["architecture_style"] = "monolithic"
        
        # Assess coupling level
        total_cross_deps = sum(len(deps) for deps in cross_deps.values() if isinstance(deps, list))
        total_files = sum(len(files) for files in language_files.values())
        
        if total_cross_deps == 0:
            insights["coupling_level"] = "loose"
        elif total_cross_deps / total_files < 0.1:
            insights["coupling_level"] = "moderate"
        else:
            insights["coupling_level"] = "tight"
        
        # Assess communication complexity
        comm_count = sum(len(patterns) for patterns in comm_patterns.values() if isinstance(patterns, list))
        if comm_count > 10:
            insights["communication_complexity"] = "high"
        elif comm_count > 5:
            insights["communication_complexity"] = "medium"
        else:
            insights["communication_complexity"] = "low"
        
        # Calculate maintainability score (0-100)
        base_score = 70
        
        # Deduct points for high coupling
        if insights["coupling_level"] == "tight":
            base_score -= 20
        elif insights["coupling_level"] == "moderate":
            base_score -= 10
        
        # Deduct points for high communication complexity
        if insights["communication_complexity"] == "high":
            base_score -= 15
        elif insights["communication_complexity"] == "medium":
            base_score -= 10
        
        # Add points for good architecture
        if insights["architecture_style"] == "microservices" and insights["coupling_level"] == "loose":
            base_score += 15
        
        insights["maintainability_score"] = max(0, min(100, base_score))
        
        return insights
    
    def identify_hotspots(self, dependency_graph: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify architectural hotspots that need attention"""
        hotspots = []
        
        # Analyze node degrees to find highly connected components
        edges = dependency_graph.get("edges", [])
        node_degrees = defaultdict(int)
        
        for source, target, _ in edges:
            node_degrees[source] += 1
            node_degrees[target] += 1
        
        # Find nodes with high connectivity (potential hotspots)
        for node, degree in node_degrees.items():
            if degree > 5:  # Threshold for high connectivity
                hotspots.append({
                    "component": node,
                    "issue_type": "high_connectivity",
                    "degree": degree,
                    "severity": "high" if degree > 10 else "medium",
                    "description": f"Component {node} has {degree} connections, indicating potential architectural bottleneck"
                })
        
        return hotspots
    
    def generate_recommendations(self, analysis_results: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations based on analysis"""
        recommendations = []
        
        insights = analysis_results.get("architectural_insights", {})
        hotspots = analysis_results.get("hotspots", [])
        
        # Coupling recommendations
        if insights.get("coupling_level") == "tight":
            recommendations.append("Consider implementing interface segregation to reduce tight coupling between language components")
            recommendations.append("Evaluate using message queues or event-driven architecture to decouple components")
        
        # Architecture recommendations
        if insights.get("architecture_style") == "monolithic" and len(analysis_results.get("languages_found", [])) > 2:
            recommendations.append("Consider migrating to a microservices architecture to better isolate language-specific components")
        
        # Hotspot recommendations
        for hotspot in hotspots:
            if hotspot["severity"] == "high":
                recommendations.append(f"Refactor {hotspot['component']} to reduce architectural complexity and improve maintainability")
        
        # Communication recommendations
        if insights.get("communication_complexity") == "high":
            recommendations.append("Implement API versioning and standardize communication protocols between language components")
            recommendations.append("Consider using API gateways to centralize and manage inter-service communication")
        
        # General recommendations
        if insights.get("maintainability_score", 0) < 60:
            recommendations.append("Overall maintainability is low - prioritize architectural refactoring")
            recommendations.append("Implement comprehensive integration testing for cross-language components")
        
        return recommendations
    
    def get_line_context(self, content: str, pattern: str) -> str:
        """Get line context for a pattern match"""
        lines = content.split('\n')
        for line in lines:
            if re.search(pattern, line, re.IGNORECASE):
                return line.strip()
        return ""
    
    def determine_affected_languages(self, build_system: str, available_languages: List[str]) -> List[str]:
        """Determine which languages are affected by a build system"""
        build_to_languages = {
            'docker': available_languages,  # Docker can affect all languages
            'npm': ['javascript'],
            'pip': ['python'],
            'go': ['go'],
            'cargo': ['rust'],
            'gradle': ['java'],
            'maven': ['java'],
            'make': available_languages,  # Make can affect multiple languages
            'cmake': ['cpp', 'c']
        }
        
        return [lang for lang in build_to_languages.get(build_system, []) if lang in available_languages]