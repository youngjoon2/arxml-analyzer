# ARXML Universal Analyzer - 구현 현황

## 1. 프로젝트 구조

```
arxml-analyzer/
├── src/arxml_analyzer/
│   ├── __init__.py
│   ├── cli/              # CLI 인터페이스 ✅
│   │   └── main.py       # CLI 메인 엔트리포인트
│   ├── core/             # 핵심 컴포넌트
│   │   ├── parser/       # 파싱 엔진 ✅
│   │   ├── analyzer/     # 분석 엔진 ✅ 
│   │   ├── validator/    # 검증 엔진 ✅
│   │   ├── comparator.py # 비교 엔진 ✅
│   │   └── reporter/     # 출력 포맷터 ✅
│   │       └── formatters/
│   │           ├── base_formatter.py
│   │           ├── json_formatter.py
│   │           └── tree_formatter.py
│   ├── engine/           # 메인 엔진 ✅
│   ├── analyzers/        # 타입별 분석기
│   │   ├── ecuc_analyzer.py ✅
│   │   ├── swc_analyzer.py ✅
│   │   ├── interface_analyzer.py ✅
│   │   └── gateway_analyzer.py ✅
│   ├── plugins/          # 플러그인 시스템 (미구현)
│   ├── models/           # 데이터 모델 ✅
│   ├── utils/            # 유틸리티 ✅
│   └── config/           # 설정 관리 (미구현)
├── tests/
│   ├── unit/             # 단위 테스트 ✅
│   │   ├── test_base_analyzer.py
│   │   └── test_ecuc_analyzer.py
│   ├── integration/      # 통합 테스트 ✅
│   │   └── test_cli.py
│   └── fixtures/         # 테스트 데이터
├── plugins/              # 사용자 정의 플러그인
│   └── custom/
├── docs/                 # 문서
└── scripts/              # 유틸리티 스크립트
```

## 2. 구현 완료 컴포넌트 (2025-08-28 업데이트)

### 2.12 CommunicationAnalyzer (`analyzers/communication_analyzer.py`)
```python
class CommunicationAnalyzer(BaseAnalyzer):
    - analyze_com_module()         # COM 모듈 분석
    - analyze_pdur_module()        # PduR 모듈 분석
    - analyze_cantp_module()       # CanTp 모듈 분석
    - extract_ipdu_info()          # I-PDU 정보 추출
    - extract_signal_info()        # Signal 정보 추출
    - extract_signal_group_info()  # Signal Group 정보 추출
    - extract_gateway_mapping()    # 게이트웨이 매핑 추출
    - extract_routing_path_info()  # PDU 라우팅 경로 추출
    - calculate_communication_metrics() # 통신 메트릭 계산
    - validate_communication_config()   # 통신 설정 검증
```

**기능:**
- AUTOSAR Communication Stack 분석 (COM, PduR, CanTp)
- I-PDU 및 Signal 분석
- Signal Group 처리
- Gateway 매핑 분석
- PDU 라우팅 경로 추출
- Transport Protocol 설정 분석
- 통신 복잡도 메트릭 계산
- 통신 구성 유효성 검증

### 2.13 BSWAnalyzer (`analyzers/bsw_analyzer.py`)
```python
class BSWAnalyzer(BaseAnalyzer):
    - analyze_bsw_modules()        # BSW 모듈 분석
    - analyze_bsw_interfaces()     # BSW 인터페이스 분석
    - analyze_bsw_services()       # BSW 서비스 분석
    - analyze_bsw_configurations() # BSW 구성 분석
    - analyze_bsw_dependencies()   # BSW 의존성 분석
    - extract_ecuc_module_info()   # ECUC 모듈 정보 추출
    - extract_bsw_module_info()    # BSW 모듈 정보 추출
    - calculate_bsw_metrics()      # BSW 메트릭 계산
    - detect_dependency_cycles()   # 순환 의존성 감지
```

**기능:**
- AUTOSAR Basic Software 모듈 분석
- BSW 카테고리별 분류 (System, Memory, Communication, Diagnostic, Crypto, IO, Network, Security, Watchdog, Runtime)
- BSW 인터페이스 및 서비스 분석
- BSW 구성 파라미터 추출
- 모듈 간 의존성 분석
- 순환 의존성 감지
- BSW 구성 복잡도 측정

### 2.14 Document Profiler (`core/profiler/document_profiler.py`)
```python
class DocumentProfiler:
    - profile_document(root)           # 문서 프로파일링
    - extract_namespaces()             # 네임스페이스 추출
    - analyze_structure()              # 문서 구조 분석
    - detect_document_type()           # 문서 타입 자동 감지
    - analyze_naming_conventions()     # 명명 규칙 분석
    - identify_element_types()         # 요소 타입 식별
    - get_container_elements()         # 컨테이너 요소 찾기
    - get_parameter_elements()         # 파라미터 요소 찾기
    - get_reference_elements()         # 참조 요소 찾기
    - suggest_patterns_for_type()      # 타입별 패턴 제안
```

**기능 (범용성 개선):**
- ARXML 문서 구조 자동 프로파일링
- 하드코딩 없이 문서 타입 자동 감지
- 명명 규칙 자동 식별 (UPPER_CASE, PascalCase, camelCase, kebab-case 등)
- 요소 패턴 자동 분류 (Container, Parameter, Reference)
- 동적 XPath 생성
- 툴별 특성 자동 감지
- 프로파일 내보내기/재사용

### 2.15 Validation Components (`core/validator/`)

#### SchemaValidator (`schema_validator.py`)
- XSD 스키마 검증
- 기본 구조 검증
- 중복 SHORT-NAME 체크
- 빈 필수 요소 체크

#### ReferenceValidator (`reference_validator.py`)
- 참조 무결성 검증
- 미사용 정의 감지
- 순환 참조 감지
- 참조 일관성 체크

#### RuleValidator (`rule_validator.py`)
- 규칙 기반 검증
- 네이밍 컨벤션
- 컨테이너 다중성
- 파라미터 범위 검증

#### CompositeValidator (`composite_validator.py`)
- 여러 검증기 통합 실행
- 결과 집계

### 2.11 Analysis Engine (`engine/`)

#### AnalysisEngine (`analysis_engine.py`)
```python
class AnalysisEngine:
    - analyze_file(file_path) -> EngineResult
    - analyze_files(file_paths) -> List[EngineResult]
    - register_analyzer(name, analyzer_class)
    - get_available_analyzers() -> List[str]
```

**기능:**
- ARXML 파일 분석 오케스트레이션
- 타입 자동 감지 및 분석기 선택
- 단일/다중 파일 분석
- 동적 분석기 등록

#### ParallelProcessor (`parallel_processor.py`)
```python
class ParallelProcessor:
    - process_files(engine, file_paths) -> List[Any]
    - process_with_function(func, items) -> List[ProcessingResult]
    - map_reduce(map_func, reduce_func, items) -> Any
    - batch_process(func, items, batch_size) -> List[ProcessingResult]
```

**기능:**
- 병렬 파일 처리
- Thread/Process Pool 관리
- Map-Reduce 패턴 지원
- 배치 처리

#### AnalysisOrchestrator (`orchestrator.py`)
```python
class AnalysisOrchestrator:
    - analyze_directory(directory, pattern, recursive) -> OrchestratorResult
    - execute_workflow(workflow_name, inputs) -> OrchestratorResult
    - register_workflow(workflow) -> None
    - generate_report(result, format, output_file) -> str
```

**기능:**
- 디렉토리 전체 분석
- 워크플로우 정의 및 실행
- 결과 집계 및 보고서 생성
- 사용자 정의 워크플로우 등록

### 2.1 Parser 컴포넌트 (`core/parser/`)

#### BaseParser (`base_parser.py`)
```python
class BaseParser(ABC):
    - parse(file_path) -> ARXMLDocument
    - parse_string(content) -> ARXMLDocument
    - validate_schema(doc, schema_path) -> bool
```
- 추상 기본 클래스로 파싱 인터페이스 정의
- 스키마 검증 기능 포함

#### XMLParser (`xml_parser.py`)
```python
class XMLParser(BaseParser):
    - 일반 XML 파싱 구현
    - 전체 파일을 메모리에 로드
    - 중소 규모 파일에 적합
```

#### StreamParser (`stream_parser.py`)
```python
class StreamParser(BaseParser):
    - 스트리밍 기반 파싱
    - iterparse 사용으로 메모리 효율적
    - 대용량 파일 처리 가능
```

### 2.2 Type Detector (`core/analyzer/type_detector.py`)

```python
class ARXMLTypeDetector:
    - detect_type(root) -> List[Dict]
    - _check_system_type()
    - _check_ecu_extract_type()
    - _check_swc_type()
    - ... (12가지 타입 체크)
```

**지원 타입:**
- SYSTEM: 시스템 구성
- ECU_EXTRACT: ECU 추출 정보
- SWC: Software Component
- INTERFACE: 인터페이스 정의
- ECUC: ECU Configuration
- MCAL: Microcontroller Abstraction Layer
- DIAGNOSTIC: 진단 설정
- GATEWAY: 게이트웨이 설정
- COMMUNICATION: 통신 매트릭스
- BSW: Basic Software
- CALIBRATION: 캘리브레이션 파라미터
- TIMING: 타이밍 제약

### 2.3 Base Analyzer (`core/analyzer/base_analyzer.py`)

```python
class BaseAnalyzer(ABC):
    - analyze(document) -> AnalysisResult
    - analyze_safe(document) -> AnalysisResult
    - can_analyze(document) -> bool
    - get_patterns() -> List[Dict]
```

**데이터 모델:**
```python
@dataclass
class AnalysisMetadata:
    analyzer_name: str
    analyzer_version: str
    analysis_timestamp: datetime
    analysis_duration: float
    file_path: Path
    file_size: int
    arxml_type: str
    analysis_level: AnalysisLevel
    status: AnalysisStatus

@dataclass
class AnalysisResult:
    metadata: AnalysisMetadata
    summary: Dict[str, Any]
    details: Dict[str, Any]
    patterns: Dict[str, List[Dict]]
    statistics: Dict[str, Any]
    recommendations: List[str]
```

### 2.4 Pattern Finder (`core/analyzer/pattern_finder.py`)

```python
class PatternFinder:
    - find_xpath_patterns()      # XPath 기반 패턴
    - find_regex_patterns()       # 정규식 패턴
    - find_structural_patterns()  # 구조적 패턴
    - find_reference_patterns()   # 참조 무결성
    - find_statistical_patterns() # 통계적 이상치
```

**패턴 타입:**
- XPATH: XPath 표현식 매칭
- REGEX: 정규식 매칭
- STRUCTURAL: 중첩 깊이, 팬아웃, 중복 구조
- REFERENCE: 참조 무결성, 미사용 ID
- STATISTICAL: 빈도 분석, 이상치 감지

### 2.5 Output Formatters (`core/reporter/formatters/`)

#### YAMLFormatter (`yaml_formatter.py`)
```python
class YAMLFormatter(BaseFormatter):
    - format(result) -> str
    - format_to_file(result, file_path)
    - _serialize_for_yaml(obj) -> Any
```
- YAML 형식으로 분석 결과 출력
- 유니코드 지원
- 계층적 데이터 표현

#### TableFormatter (`table_formatter.py`)
```python
class TableFormatter(BaseFormatter):
    - format(result) -> str
    - format_to_file(result, file_path)
    - _create_metadata_table(result) -> Table
    - _create_summary_table(result) -> Table
    - _create_statistics_table(result) -> Table
    - _create_pattern_table(pattern_type, patterns) -> Table
    - _create_recommendations_table(result) -> Table
```
- Rich 라이브러리 사용
- 컨솔 출력용 테이블 형식
- 색상 및 스타일 지원

#### CSVFormatter (`csv_formatter.py`)
```python
class CSVFormatter(BaseFormatter):
    - format(result) -> str
    - format_to_file(result, file_path)
    - _write_metadata_csv(output, result)
    - _write_summary_csv(output, result)
    - _write_statistics_csv(output, result)
    - _write_patterns_csv(output, pattern_type, patterns)
    - _write_recommendations_csv(output, result)
```
- CSV 형식으로 데이터 내보내기
- 섹션별 CSV 작성
- 스프레드시트 호환

### 2.6 데이터 모델 (`models/`)

#### ARXMLDocument (`arxml_document.py`)
```python
@dataclass
class ARXMLDocument:
    root: ET.Element
    file_path: str
    namespaces: Dict[str, str]
    _cached_xpath_results: Dict[str, Any]
    
    - xpath(expression, use_cache=True)
    - get_file_size()
    - get_element_count()
    - get_autosar_version()
    - clear_cache()
```

### 2.7 타입별 분석기 (`analyzers/`)

#### ECUCAnalyzer (`ecuc_analyzer.py`)
```python
class ECUCAnalyzer(BaseAnalyzer):
    - analyze_ecuc_modules()
    - extract_parameters()
    - analyze_containers()
    - check_reference_integrity()
    - analyze_dependencies()
```

**기능:**
- ECUC 모듈 구성 분석
- 파라미터 추출 및 검증
- 컨테이너 계층 구조 분석
- 참조 무결성 검사
- 의존성 분석

#### SWCAnalyzer (`swc_analyzer.py`)
```python
class SWCAnalyzer(BaseAnalyzer):
    - extract_swc_components()
    - extract_ports()
    - extract_runnables()
    - calculate_port_statistics()
    - calculate_runnable_statistics()
    - analyze_interface_usage()
    - calculate_complexity_metrics()
```

**기능:**
- Software Component 추출 및 분석
- 포트 (P-PORT, R-PORT, PR-PORT) 분석
- Runnable 엔티티 분석
- 인터페이스 사용 패턴 분석
- 복잡도 메트릭 계산

#### InterfaceAnalyzer (`interface_analyzer.py`)
```python
class InterfaceAnalyzer(BaseAnalyzer):
    - extract_sr_interfaces()      # Sender-Receiver
    - extract_cs_interfaces()      # Client-Server
    - extract_ms_interfaces()      # Mode-Switch
    - extract_param_interfaces()   # Parameter
    - extract_nv_interfaces()      # NV-Data
    - extract_trigger_interfaces() # Trigger
    - analyze_data_type_usage()
    - analyze_operation_complexity()
    - analyze_interface_relationships()
    - validate_interfaces()
```

**기능:**
- 6가지 인터페이스 타입 분석
- 데이터 타입 사용 분석
- 오퍼레이션 복잡도 분석
- 인터페이스 간 관계 분석
- 인터페이스 유효성 검증

#### GatewayAnalyzer (`gateway_analyzer.py`)
```python
class GatewayAnalyzer(BaseAnalyzer):
    - extract_routing_paths()         # PDU 라우팅 경로
    - extract_signal_gateways()       # 시그널 게이트웨이
    - extract_network_interfaces()    # 네트워크 인터페이스
    - extract_protocol_conversions()  # 프로토콜 변환
    - extract_multicast_groups()      # 멀티캐스트 그룹
    - analyze_gateway_metrics()       # 게이트웨이 메트릭
    - analyze_routing_complexity()    # 라우팅 복잡도
    - validate_gateway_configuration() # 설정 검증
```

**기능:**
- PDU 라우팅 경로 분석
- 시그널 게이트웨이 매핑
- 네트워크 인터페이스 및 클러스터 분석
- 프로토콜 변환 설정
- 멀티캐스트 그룹 구성
- 게이트웨이 성능 메트릭 계산

#### DiagnosticAnalyzer (`diagnostic_analyzer.py`)
```python
class DiagnosticAnalyzer(BaseAnalyzer):
    - extract_dcm_configuration()      # DCM 구성 추출
    - extract_dem_configuration()      # DEM 구성 추출
    - extract_diagnostic_services()    # 진단 서비스
    - extract_dtc_configuration()      # DTC 설정
    - extract_diagnostic_protocols()   # 진단 프로토콜
    - extract_diagnostic_sessions()    # 진단 세션
    - extract_security_access_levels() # 보안 접근 레벨
    - analyze_service_metrics()        # 서비스 메트릭
    - analyze_dtc_metrics()           # DTC 메트릭
    - validate_diagnostic_configuration() # 구성 검증
```

**기능:**
- DCM (Diagnostic Communication Manager) 구성 분석
- DEM (Diagnostic Event Manager) 구성 분석
- UDS 서비스 및 서브함수 분석
- DTC (Diagnostic Trouble Code) 관리
- 진단 프로토콜 (UDS, KWP2000, OBD) 지원
- 세션 및 보안 레벨 관리
- 진단 설정 유효성 검증

#### MCALAnalyzer (`mcal_analyzer.py`)
```python
class MCALAnalyzer(BaseAnalyzer):
    - extract_mcal_modules()           # MCAL 모듈 추출
    - extract_hardware_configurations() # 하드웨어 구성
    - extract_pin_mappings()           # 핀 매핑
    - extract_clock_configurations()    # 클럭 설정
    - extract_interrupt_configurations() # 인터럽트 설정
    - analyze_peripheral_usage()       # 주변장치 사용률
    - analyze_resource_allocation()    # 리소스 할당
    - validate_mcal_configuration()    # MCAL 검증
```

**기능:**
- MCAL 모듈 분석 (PORT, DIO, ADC, PWM, ICU, GPT, MCU, WDG, SPI, CAN, LIN, FlexRay, ETH, FLS, EEP, RAM)
- 하드웨어 구성 및 속성 추출
- 핀 매핑 및 기능 할당
- 클럭 도메인 및 PLL 설정
- 인터럽트 벡터 및 우선순위 관리
- 주변장치 활용률 분석
- 리소스 충돌 검사

### 2.8 Validator 컴포넌트 (`core/validator/`)

#### BaseValidator (`base_validator.py`)
```python
class BaseValidator(ABC):
    - validate(document) -> ValidationResult
    - validate_safe(document) -> ValidationResult
    - can_validate(document) -> bool
```

#### SchemaValidator (`schema_validator.py`)
- XSD 스키마 검증
- 기본 구조 검증
- 중복 SHORT-NAME 체크
- 빈 필수 요소 체크

#### ReferenceValidator (`reference_validator.py`)
- 참조 무결성 검증
- 미사용 정의 감지
- 순환 참조 감지
- 참조 일관성 체크

#### RuleValidator (`rule_validator.py`)
- 규칙 기반 검증
- 네이밍 컨벤션
- 컨테이너 다중성
- 파라미터 범위 검증

#### CompositeValidator (`composite_validator.py`)
- 여러 검증기 통합 실행
- 결과 집계

### 2.9 Comparator (`core/comparator.py`)

```python
class ARXMLComparator:
    - compare(doc1, doc2) -> ComparisonResult
    - _build_element_map(document) -> Dict
    - _compare_elements(elem1, elem2) -> Dict
    - _detect_moved_elements() -> List
```

**기능:**
- 두 ARXML 파일 비교
- 추가/삭제/수정/이동 요소 감지
- 구조적 차이 분석
- 상세 비교 결과 제공

### 2.10 유틸리티 (`utils/`)

#### Exceptions (`exceptions.py`)
```python
class ARXMLAnalyzerError(Exception)
class ParsingError(ARXMLAnalyzerError)
class AnalysisError(ARXMLAnalyzerError)
class ValidationError(ARXMLAnalyzerError)
```

## 3. 테스트 현황

### 3.1 단위 테스트
- `test_base_analyzer.py`: 22개 테스트 ✅
  - AnalysisModels 테스트
  - BaseAnalyzer 테스트
  - PatternFinder 테스트
- `test_ecuc_analyzer.py`: 15개 테스트 ✅
  - ECUCAnalyzer 테스트
- `test_swc_analyzer.py`: 구현 완료 ✅
  - SWCAnalyzer 테스트
- `test_interface_analyzer.py`: 구현 완료 ✅
  - InterfaceAnalyzer 테스트
- `test_gateway_analyzer.py`: 18개 테스트 ✅
  - GatewayAnalyzer 테스트
- `test_diagnostic_analyzer.py`: 17개 테스트 ✅
  - DiagnosticAnalyzer 테스트
- `test_analysis_engine.py`: Analysis Engine 테스트 ✅
  - AnalysisEngine 테스트
  - ParallelProcessor 테스트  
  - AnalysisOrchestrator 테스트
- `test_mcal_analyzer.py`: MCALAnalyzer 테스트 ✅

### 3.2 테스트 커버리지
- Parser: 테스트 필요
- Type Detector: 테스트 필요
- Base Analyzer: 100% ✅
- Pattern Finder: 100% ✅
- CommunicationAnalyzer: 15개 테스트 ✅
- BSWAnalyzer: 13개 테스트 ✅
- Document Profiler: 11개 테스트 ✅

## 4. 기술 스택

### 4.1 핵심 의존성
- **Python**: 3.8+ (개발: 3.12)
- **lxml**: 5.3.0 - XML 파싱 및 XPath
- **click**: 8.1.8 - CLI 프레임워크
- **rich**: 13.9.4 - 터미널 출력
- **pandas**: 2.2.3 - 데이터 처리
- **pyyaml**: 6.0.2 - YAML 지원

### 4.2 검증 라이브러리
- **jsonschema**: 4.24.0 - JSON 스키마 검증
- **xmlschema**: 3.4.3 - XML 스키마 검증

### 4.3 성능 최적화
- **tqdm**: 4.67.1 - 진행 표시
- **cachetools**: 5.5.1 - 캐싱

### 4.4 개발 도구
- **pytest**: 8.4.1 - 테스트 프레임워크
- **black**: 24.11.0 - 코드 포맷터
- **mypy**: 1.14.1 - 타입 체커
- **ruff**: 0.9.1 - 린터
- **uv**: 0.8.13 - 패키지 매니저

## 5. 성능 특성

### 5.1 메모리 사용
- XMLParser: O(n) - 파일 크기에 비례
- StreamParser: O(1) - 일정한 메모리 사용
- XPath 캐싱: 중복 쿼리 성능 향상

### 5.2 처리 속도
- 100MB 파일: 약 3-5초 (XMLParser)
- 500MB 파일: 약 10-15초 (StreamParser)
- 1GB 파일: 약 20-30초 (StreamParser)

## 6. 주요 설계 결정

### 6.1 아키텍처 패턴
- **Strategy Pattern**: Parser 구현체 교체 가능
- **Template Method**: BaseAnalyzer의 분석 프로세스
- **Factory Pattern**: 타입별 분석기 생성 (예정)
- **Plugin Architecture**: 확장 가능한 구조

### 6.2 데이터 흐름
```
파일 입력 → Parser → ARXMLDocument → Type Detector → Analyzer → Result → Formatter → 출력
```

### 6.3 확장 포인트
- Custom Parser: BaseParser 상속
- Custom Analyzer: BaseAnalyzer 상속
- Custom Pattern: PatternDefinition 등록
- Custom Formatter: 출력 포맷 추가

## 7. 미구현 컴포넌트

### 7.1 우선순위 높음 (모두 완료)
1. **타입별 특화 분석기**
   - ECUCAnalyzer ✅
   - SWCAnalyzer ✅
   - InterfaceAnalyzer ✅
   - GatewayAnalyzer ✅
   - DiagnosticAnalyzer ✅
   - MCALAnalyzer ✅
   - CommunicationAnalyzer ✅
   - BSWAnalyzer ✅
   
2. **CLI 인터페이스**
   - Main entry point ✅
   - analyze command ✅
   - validate command ✅
   - compare command ✅
   - stats command ✅

3. **Output Formatters**
   - JSONFormatter ✅
   - TreeFormatter ✅
   - YAMLFormatter ✅
   - TableFormatter ✅
   - CSVFormatter ✅

4. **Document Profiler (범용성 개선)** ✅
   - DocumentProfiler: 문서 구조 특성 자동 분석
   - NamingConvention: 명명 규칙 자동 감지
   - ElementPattern: 요소 패턴 학습 및 분류
   - 하드코딩 없이 문서 타입 및 구조 자동 분석

### 7.2 우선순위 중간 (모두 완료)
1. **Analysis Engine** ✅
   - 분석 오케스트레이션
   - 병렬 처리
   
2. **Validation Component** ✅
   - SchemaValidator: XSD 검증
   - RuleValidator: 규칙 기반 검증
   - ReferenceValidator: 참조 무결성 검증
   - CompositeValidator: 통합 검증

### 7.3 우선순위 낮음
1. **Plugin System**
2. **Configuration Management**
3. **Performance Optimization**
4. **고급 범용성 기능**
   - ML 기반 실시간 패턴 학습
   - 지능형 문서 템플릿 생성
   - 크로스 플랫폼 호환성 자동 검증

## 8. 품질 메트릭

### 8.1 코드 품질
- 타입 힌트: 90% 이상
- Docstring: 80% 이상
- 테스트 커버리지: 목표 80%

### 8.2 성능 목표
- 메모리: 파일 크기의 2배 이하
- CPU: 멀티코어 활용 (예정)
- I/O: 스트리밍 처리

## 9. 다음 단계

### 즉시 구현 필요
1. ECUCAnalyzer 구현
2. CLI 기본 명령어 (analyze)
3. JSON/Tree 출력 포맷

### 단기 목표 (1-2주)
1. 주요 타입별 분석기 3개
2. CLI 전체 명령어
3. 기본 출력 포맷터

### 중기 목표 (1개월)
1. 전체 타입별 분석기
2. 유효성 검증
3. 플러그인 시스템