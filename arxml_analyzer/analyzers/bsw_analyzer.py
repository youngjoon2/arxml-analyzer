"""AUTOSAR Basic Software (BSW) analyzer implementation."""

from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field

from ..core.analyzer.base_analyzer import BaseAnalyzer, AnalysisResult, AnalysisMetadata
from ..core.analyzer.pattern_finder import PatternType


@dataclass
class BSWModule:
    """BSW 모듈 정보"""
    name: str
    module_type: str  # System, Memory, Communication, Diagnostic, etc.
    version: Optional[str] = None
    vendor: Optional[str] = None
    configuration: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    interfaces: List[str] = field(default_factory=list)


@dataclass
class BSWInterface:
    """BSW 인터페이스 정보"""
    name: str
    interface_type: str  # API, Callback, Service
    provider_module: Optional[str] = None
    consumer_modules: List[str] = field(default_factory=list)
    operations: List[str] = field(default_factory=list)


@dataclass 
class BSWService:
    """BSW 서비스 정보"""
    name: str
    service_type: str
    module: str
    api_functions: List[str] = field(default_factory=list)
    callbacks: List[str] = field(default_factory=list)
    configuration: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BSWConfiguration:
    """BSW 구성 정보"""
    parameter_name: str
    value: Any
    module: str
    container: Optional[str] = None
    description: Optional[str] = None
    


class BSWAnalyzer(BaseAnalyzer):
    """AUTOSAR Basic Software 분석기"""
    
    def __init__(self):
        """초기화"""
        super().__init__()
        self.type_identifier = "BSW"
        
        # BSW 모듈 카테고리
        self.module_categories = {
            "System": ["EcuM", "BswM", "ComM", "SchM"],
            "Memory": ["NvM", "MemIf", "Fee", "Ea", "Eep", "Fls"],
            "Communication": ["CanIf", "LinIf", "FrIf", "EthIf", "Com", "PduR", "IpduM", "CanTp", "LinTp", "FrTp"],
            "Diagnostic": ["Dcm", "Dem", "Det", "Dlt", "FiM"],
            "Crypto": ["Crypto", "Csm", "CryIf", "KeyM"],
            "IO": ["IoHwAb", "Adc", "Pwm", "Dio", "Port", "Icu", "Ocu", "Gpt", "Wdg"],
            "Network": ["SoAd", "DoIP", "TcpIp", "EthSM", "EthTrcv", "Sd"],
            "Security": ["SecOC", "IdsM", "TLS"],
            "Watchdog": ["WdgM", "WdgIf", "Wdg"],
            "Runtime": ["Rte", "Os"]
        }
        
    def can_analyze(self, root) -> bool:
        """BSW 문서 분석 가능 여부 확인"""
        patterns = [
            './/ECUC-MODULE-DEF[@UUID]',
            './/BSW-MODULE-DESCRIPTION',
            './/BSW-MODULE-ENTRY',
            './/BSW-IMPLEMENTATION',
            './/BSW-BEHAVIOR'
        ]
        
        # BSW 모듈 이름으로도 확인
        for category_modules in self.module_categories.values():
            for module in category_modules:
                if root.find(f'.//SHORT-NAME[.="{module}"]') is not None:
                    return True
        
        for pattern in patterns:
            if root.find(pattern) is not None:
                return True
                
        return False
    
    def get_patterns(self) -> Dict[PatternType, List[str]]:
        """BSW 관련 패턴 반환"""
        xpath_patterns = [
            './/BSW-MODULE-DESCRIPTION',
            './/BSW-MODULE-ENTRY',
            './/BSW-IMPLEMENTATION',
            './/BSW-BEHAVIOR',
            './/BSW-MODULE-INSTANCE',
            './/BSW-SCHEDULABLE-ENTITY'
        ]
        
        # 각 BSW 모듈에 대한 패턴 추가
        for category_modules in self.module_categories.values():
            for module in category_modules:
                xpath_patterns.append(f'.//ECUC-MODULE-DEF[SHORT-NAME="{module}"]')
                xpath_patterns.append(f'.//BSW-MODULE-DESCRIPTION[SHORT-NAME="{module}"]')
        
        return {
            PatternType.XPATH: xpath_patterns,
            PatternType.REFERENCE: [
                './/PROVIDED-INTERFACE-REF',
                './/REQUIRED-INTERFACE-REF',
                './/MODULE-REF',
                './/IMPLEMENTATION-REF'
            ]
        }
        
    def analyze(self, root) -> AnalysisResult:
        """BSW 분석 수행"""
        # 메타데이터 생성
        metadata = AnalysisMetadata(
            analyzer_name=self.name,
            analyzer_version=self.version,
            arxml_type="BSW"
        )
        result = AnalysisResult(metadata=metadata)
        
        try:
            # BSW 모듈 분석
            modules = self._analyze_bsw_modules(root)
            result.details["modules"] = modules
            
            # BSW 인터페이스 분석
            interfaces = self._analyze_bsw_interfaces(root)
            result.details["interfaces"] = interfaces
            
            # BSW 서비스 분석
            services = self._analyze_bsw_services(root)
            result.details["services"] = services
            
            # BSW 구성 분석
            configurations = self._analyze_bsw_configurations(root)
            result.details["configurations"] = configurations
            
            # BSW 의존성 분석
            dependencies = self._analyze_bsw_dependencies(root)
            result.details["dependencies"] = dependencies
            
            # 메트릭 계산
            result.statistics = self._calculate_bsw_metrics(result.details)
            
            # 검증 수행
            result.details["validation_results"] = self._validate_bsw_configuration(result)
            
            # 요약 생성
            result.summary = self._generate_summary(result)
            
        except Exception as e:
            result.metadata.errors.append(f"BSW analysis error: {str(e)}")
            
        return result
    
    def _analyze_bsw_modules(self, root) -> List[Dict[str, Any]]:
        """BSW 모듈 분석"""
        modules = []
        
        # ECUC 모듈 정의 분석
        for module_def in root.findall('.//ECUC-MODULE-DEF'):
            module_info = self._extract_ecuc_module_info(module_def)
            if module_info:
                modules.append(module_info)
        
        # BSW 모듈 설명 분석
        for bsw_desc in root.findall('.//BSW-MODULE-DESCRIPTION'):
            module_info = self._extract_bsw_module_info(bsw_desc)
            if module_info:
                modules.append(module_info)
        
        # BSW 모듈 엔트리 분석
        for bsw_entry in root.findall('.//BSW-MODULE-ENTRY'):
            entry_info = self._extract_bsw_entry_info(bsw_entry)
            if entry_info:
                # 해당 모듈에 엔트리 정보 추가
                module_name = bsw_entry.findtext('.//MODULE-NAME', '')
                for module in modules:
                    if module.get('name') == module_name:
                        if 'entries' not in module:
                            module['entries'] = []
                        module['entries'].append(entry_info)
                        break
        
        return modules
    
    def _analyze_bsw_interfaces(self, root) -> List[Dict[str, Any]]:
        """BSW 인터페이스 분석"""
        interfaces = []
        
        # Provided interfaces
        for provided in root.findall('.//PROVIDED-INTERFACE'):
            interface = {
                "name": provided.findtext('.//SHORT-NAME', ''),
                "type": "PROVIDED",
                "provider": provided.findtext('../SHORT-NAME', ''),
                "operations": []
            }
            
            # 인터페이스 operations
            for operation in provided.findall('.//OPERATION'):
                interface["operations"].append(operation.findtext('.//SHORT-NAME', ''))
            
            interfaces.append(interface)
        
        # Required interfaces
        for required in root.findall('.//REQUIRED-INTERFACE'):
            interface = {
                "name": required.findtext('.//SHORT-NAME', ''),
                "type": "REQUIRED",
                "consumer": required.findtext('../SHORT-NAME', ''),
                "operations": []
            }
            
            for operation in required.findall('.//OPERATION'):
                interface["operations"].append(operation.findtext('.//SHORT-NAME', ''))
            
            interfaces.append(interface)
        
        return interfaces
    
    def _analyze_bsw_services(self, root) -> List[Dict[str, Any]]:
        """BSW 서비스 분석"""
        services = []
        
        # BSW Service Dependency 분석
        for service_dep in root.findall('.//BSW-SERVICE-DEPENDENCY'):
            service = {
                "name": service_dep.findtext('.//SHORT-NAME', ''),
                "type": service_dep.findtext('.//SERVICE-KIND', ''),
                "assigned_controller": service_dep.findtext('.//ASSIGNED-CONTROLLER-REF', ''),
                "service_points": []
            }
            
            # Service points
            for point in service_dep.findall('.//SERVICE-POINT'):
                service["service_points"].append(point.findtext('.//SHORT-NAME', ''))
            
            services.append(service)
        
        # BSW Called Entity 분석
        for called_entity in root.findall('.//BSW-CALLED-ENTITY'):
            service = {
                "name": called_entity.findtext('.//SHORT-NAME', ''),
                "type": "CALLED_ENTITY",
                "minimum_start_interval": called_entity.findtext('.//MINIMUM-START-INTERVAL', ''),
                "implemented_entry_ref": called_entity.findtext('.//IMPLEMENTED-ENTRY-REF', '')
            }
            services.append(service)
        
        # BSW Schedulable Entity 분석
        for sched_entity in root.findall('.//BSW-SCHEDULABLE-ENTITY'):
            service = {
                "name": sched_entity.findtext('.//SHORT-NAME', ''),
                "type": "SCHEDULABLE",
                "can_interrupt": sched_entity.findtext('.//CAN-INTERRUPT', 'false') == 'true',
                "exclusive_area_refs": []
            }
            
            for area_ref in sched_entity.findall('.//EXCLUSIVE-AREA-REF'):
                service["exclusive_area_refs"].append(area_ref.get('DEST', ''))
            
            services.append(service)
        
        return services
    
    def _analyze_bsw_configurations(self, root) -> List[Dict[str, Any]]:
        """BSW 구성 분석"""
        configurations = []
        
        # ECUC Parameter Definition
        for param_def in root.findall('.//ECUC-PARAM-CONF-CONTAINER-DEF'):
            container_name = param_def.findtext('.//SHORT-NAME', '')
            
            # 각 파라미터 정의
            for param in param_def.findall('.//ECUC-ENUMERATION-PARAM-DEF'):
                config = {
                    "container": container_name,
                    "parameter": param.findtext('.//SHORT-NAME', ''),
                    "type": "ENUMERATION",
                    "default_value": param.findtext('.//DEFAULT-VALUE', ''),
                    "possible_values": []
                }
                
                for literal in param.findall('.//ECUC-ENUMERATION-LITERAL-DEF'):
                    config["possible_values"].append(literal.findtext('.//SHORT-NAME', ''))
                
                configurations.append(config)
            
            for param in param_def.findall('.//ECUC-INTEGER-PARAM-DEF'):
                config = {
                    "container": container_name,
                    "parameter": param.findtext('.//SHORT-NAME', ''),
                    "type": "INTEGER",
                    "min": param.findtext('.//MIN', ''),
                    "max": param.findtext('.//MAX', ''),
                    "default_value": param.findtext('.//DEFAULT-VALUE', '')
                }
                configurations.append(config)
            
            for param in param_def.findall('.//ECUC-BOOLEAN-PARAM-DEF'):
                config = {
                    "container": container_name,
                    "parameter": param.findtext('.//SHORT-NAME', ''),
                    "type": "BOOLEAN",
                    "default_value": param.findtext('.//DEFAULT-VALUE', 'false')
                }
                configurations.append(config)
        
        return configurations
    
    def _analyze_bsw_dependencies(self, root) -> Dict[str, List[str]]:
        """BSW 의존성 분석"""
        dependencies = {}
        
        # Module dependencies
        for module in root.findall('.//BSW-MODULE-DESCRIPTION'):
            module_name = module.findtext('.//SHORT-NAME', '')
            deps = []
            
            # Required module entries
            for req_entry in module.findall('.//REQUIRED-MODULE-ENTRY'):
                deps.append(req_entry.findtext('.//MODULE-NAME', ''))
            
            # Required interfaces
            for req_interface in module.findall('.//REQUIRED-INTERFACE-REF'):
                interface_name = req_interface.get('DEST', '')
                if interface_name:
                    deps.append(f"Interface:{interface_name}")
            
            if deps:
                dependencies[module_name] = deps
        
        # BSW Module Dependency
        for module_dep in root.findall('.//BSW-MODULE-DEPENDENCY'):
            module_name = module_dep.findtext('.//MODULE-NAME', '')
            required_module = module_dep.findtext('.//REQUIRED-MODULE-REF', '')
            
            if module_name and required_module:
                if module_name not in dependencies:
                    dependencies[module_name] = []
                dependencies[module_name].append(required_module)
        
        return dependencies
    
    def _extract_ecuc_module_info(self, elem) -> Dict[str, Any]:
        """ECUC 모듈 정보 추출"""
        try:
            name = elem.findtext('.//SHORT-NAME', '')
            if not name:
                return None
                
            # 모듈 카테고리 결정
            category = "Unknown"
            for cat, modules in self.module_categories.items():
                if name in modules:
                    category = cat
                    break
            
            return {
                "name": name,
                "type": category,
                "uuid": elem.get('UUID', ''),
                "vendor_id": elem.findtext('.//VENDOR-ID', ''),
                "vendor_api_infix": elem.findtext('.//VENDOR-API-INFIX', ''),
                "ar_release": elem.findtext('.//AR-RELEASE-VERSION', ''),
                "module_id": elem.findtext('.//MODULE-ID', ''),
                "container_count": len(elem.findall('.//ECUC-PARAM-CONF-CONTAINER-DEF')),
                "parameter_count": len(elem.findall('.//ECUC-PARAMETER-DEF'))
            }
        except Exception:
            return None
    
    def _extract_bsw_module_info(self, elem) -> Dict[str, Any]:
        """BSW 모듈 정보 추출"""
        try:
            name = elem.findtext('.//SHORT-NAME', '')
            if not name:
                return None
            
            # 모듈 카테고리 결정
            category = "Unknown"
            for cat, modules in self.module_categories.items():
                if name in modules:
                    category = cat
                    break
            
            return {
                "name": name,
                "type": category,
                "module_id": elem.findtext('.//MODULE-ID', ''),
                "provided_interfaces": len(elem.findall('.//PROVIDED-INTERFACE')),
                "required_interfaces": len(elem.findall('.//REQUIRED-INTERFACE')),
                "implementation_refs": len(elem.findall('.//IMPLEMENTATION-REF')),
                "vendor_specific": elem.findtext('.//VENDOR-SPECIFIC', 'false') == 'true'
            }
        except Exception:
            return None
    
    def _extract_bsw_entry_info(self, elem) -> Dict[str, Any]:
        """BSW 엔트리 정보 추출"""
        try:
            return {
                "name": elem.findtext('.//SHORT-NAME', ''),
                "service_id": elem.findtext('.//SERVICE-ID', ''),
                "is_synchronous": elem.findtext('.//IS-SYNCHRONOUS', 'true') == 'true',
                "is_reentrant": elem.findtext('.//IS-REENTRANT', 'false') == 'true',
                "can_interrupt": elem.findtext('.//CAN-INTERRUPT', 'false') == 'true',
                "execution_context": elem.findtext('.//EXECUTION-CONTEXT', ''),
                "sw_service_impl_policy": elem.findtext('.//SW-SERVICE-IMPL-POLICY', '')
            }
        except Exception:
            return None
    
    def _calculate_bsw_metrics(self, details: Dict[str, Any]) -> Dict[str, Any]:
        """BSW 메트릭 계산"""
        metrics = {
            "total_modules": len(details.get("modules", [])),
            "total_interfaces": len(details.get("interfaces", [])),
            "total_services": len(details.get("services", [])),
            "total_configurations": len(details.get("configurations", [])),
            "module_categories": {},
            "interface_balance": 0.0,
            "configuration_complexity": 0.0,
            "dependency_depth": 0
        }
        
        # 카테고리별 모듈 수
        for module in details.get("modules", []):
            category = module.get("type", "Unknown")
            if category not in metrics["module_categories"]:
                metrics["module_categories"][category] = 0
            metrics["module_categories"][category] += 1
        
        # 인터페이스 균형 (PROVIDED vs REQUIRED)
        provided = sum(1 for i in details.get("interfaces", []) if i.get("type") == "PROVIDED")
        required = sum(1 for i in details.get("interfaces", []) if i.get("type") == "REQUIRED")
        if provided + required > 0:
            metrics["interface_balance"] = abs(provided - required) / (provided + required)
        
        # 구성 복잡도 (0-10 scale)
        config_count = len(details.get("configurations", []))
        metrics["configuration_complexity"] = min(config_count / 100.0 * 10, 10.0)
        
        # 의존성 깊이 계산
        dependencies = details.get("dependencies", {})
        if dependencies:
            metrics["dependency_depth"] = self._calculate_dependency_depth(dependencies)
        
        return metrics
    
    def _calculate_dependency_depth(self, dependencies: Dict[str, List[str]], 
                                   module: str = None, visited: Set[str] = None) -> int:
        """의존성 깊이 계산 (재귀)"""
        if visited is None:
            visited = set()
        
        if module is None:
            # 모든 모듈에 대해 최대 깊이 계산
            max_depth = 0
            for mod in dependencies.keys():
                depth = self._calculate_dependency_depth(dependencies, mod, visited.copy())
                max_depth = max(max_depth, depth)
            return max_depth
        
        if module in visited or module not in dependencies:
            return 0
        
        visited.add(module)
        max_child_depth = 0
        
        for dep in dependencies.get(module, []):
            # Interface 의존성은 제외
            if not dep.startswith("Interface:"):
                child_depth = self._calculate_dependency_depth(dependencies, dep, visited.copy())
                max_child_depth = max(max_child_depth, child_depth)
        
        return 1 + max_child_depth
    
    def _validate_bsw_configuration(self, result: AnalysisResult) -> List[Dict[str, Any]]:
        """BSW 구성 검증"""
        validations = []
        
        # 모듈 검증
        modules = result.details.get("modules", [])
        module_names = set()
        
        for module in modules:
            name = module.get("name")
            if name in module_names:
                validations.append({
                    "level": "ERROR",
                    "message": f"Duplicate module definition: {name}"
                })
            module_names.add(name)
            
            # 알 수 없는 모듈 타입
            if module.get("type") == "Unknown":
                validations.append({
                    "level": "WARNING", 
                    "message": f"Unknown module category for: {name}"
                })
        
        # 인터페이스 검증
        interfaces = result.details.get("interfaces", [])
        provided_interfaces = set()
        required_interfaces = set()
        
        for interface in interfaces:
            if interface.get("type") == "PROVIDED":
                provided_interfaces.add(interface.get("name"))
            else:
                required_interfaces.add(interface.get("name"))
        
        # 미사용 제공 인터페이스
        unused_provided = provided_interfaces - required_interfaces
        if unused_provided:
            validations.append({
                "level": "INFO",
                "message": f"Unused provided interfaces: {', '.join(unused_provided)}"
            })
        
        # 미해결 필수 인터페이스
        unresolved_required = required_interfaces - provided_interfaces
        if unresolved_required:
            validations.append({
                "level": "WARNING",
                "message": f"Unresolved required interfaces: {', '.join(unresolved_required)}"
            })
        
        # 순환 의존성 검사
        dependencies = result.details.get("dependencies", {})
        cycles = self._detect_dependency_cycles(dependencies)
        if cycles:
            validations.append({
                "level": "ERROR",
                "message": f"Circular dependencies detected: {cycles}"
            })
        
        return validations
    
    def _detect_dependency_cycles(self, dependencies: Dict[str, List[str]]) -> List[List[str]]:
        """순환 의존성 감지"""
        cycles = []
        visited = set()
        rec_stack = set()
        
        def dfs(module: str, path: List[str]) -> bool:
            visited.add(module)
            rec_stack.add(module)
            path.append(module)
            
            for dep in dependencies.get(module, []):
                # Interface 의존성은 제외
                if dep.startswith("Interface:"):
                    continue
                    
                if dep not in visited:
                    if dfs(dep, path.copy()):
                        return True
                elif dep in rec_stack:
                    # 순환 발견
                    cycle_start = path.index(dep)
                    cycle = path[cycle_start:] + [dep]
                    cycles.append(cycle)
                    return True
            
            rec_stack.remove(module)
            return False
        
        for module in dependencies.keys():
            if module not in visited:
                dfs(module, [])
        
        return cycles
    
    def _generate_summary(self, result: AnalysisResult) -> str:
        """분석 요약 생성"""
        summary_lines = ["BSW Analysis Summary:"]
        
        if result.statistics:
            stats = result.statistics
            summary_lines.extend([
                f"  - Total BSW Modules: {stats.get('total_modules', 0)}",
                f"  - Total Interfaces: {stats.get('total_interfaces', 0)}",
                f"  - Total Services: {stats.get('total_services', 0)}",
                f"  - Total Configurations: {stats.get('total_configurations', 0)}",
                f"  - Module Categories: {len(stats.get('module_categories', {}))}",
                f"  - Dependency Depth: {stats.get('dependency_depth', 0)}",
                f"  - Configuration Complexity: {stats.get('configuration_complexity', 0):.2f}/10"
            ])
        
        # 검증 요약
        validations = result.details.get("validation_results", [])
        if validations:
            errors = sum(1 for v in validations if v.get("level") == "ERROR")
            warnings = sum(1 for v in validations if v.get("level") == "WARNING")
            summary_lines.append(f"  - Validation: {errors} errors, {warnings} warnings")
        
        # 카테고리별 분포
        if result.statistics and "module_categories" in result.statistics:
            summary_lines.append("  - Module Distribution:")
            for category, count in result.statistics["module_categories"].items():
                summary_lines.append(f"    * {category}: {count}")
        
        return "\n".join(summary_lines)