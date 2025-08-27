#!/usr/bin/env python3
"""ARXML 파일 유효성 검증 스크립트"""

import os
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Tuple

def validate_arxml_file(filepath: str) -> Tuple[bool, Dict]:
    """단일 ARXML 파일 유효성 검증"""
    result = {
        'path': filepath,
        'exists': False,
        'valid_xml': False,
        'size_bytes': 0,
        'has_autosar_root': False,
        'error': None
    }
    
    try:
        # 파일 존재 여부 확인
        if not os.path.exists(filepath):
            result['error'] = 'File not found'
            return False, result
            
        result['exists'] = True
        result['size_bytes'] = os.path.getsize(filepath)
        
        # XML 파싱 시도
        tree = ET.parse(filepath)
        root = tree.getroot()
        result['valid_xml'] = True
        
        # AUTOSAR 루트 엘리먼트 확인
        if 'AUTOSAR' in root.tag or 'AR-PACKAGES' in root.tag:
            result['has_autosar_root'] = True
            
        return True, result
        
    except ET.ParseError as e:
        result['error'] = f'XML parse error: {str(e)}'
        return False, result
    except Exception as e:
        result['error'] = f'Unexpected error: {str(e)}'
        return False, result

def main():
    """모든 ARXML 파일 검증"""
    base_dir = Path('/home/yjchoi/company/arxml-analyzer/data')
    
    # 문서에 나열된 모든 파일
    expected_files = [
        # Communication
        'official/communication/ArcCore_EcucDefs_CanSM.arxml',
        'official/communication/ArcCore_EcucDefs_CanTp.arxml',
        'official/communication/ArcCore_EcucDefs_Com.arxml',
        'official/communication/ArcCore_EcucDefs_PduR.arxml',
        'official/communication/ArcCore_EcucDefs_SoAd.arxml',
        # Diagnostic
        'official/diagnostic/AUTOSAR_MOD_DiagnosticManagement_Blueprint.arxml',
        'official/diagnostic/ArcCore_EcucDefs_Dcm.arxml',
        'official/diagnostic/ArcCore_EcucDefs_Dem.arxml',
        # ECUC
        'official/ecuc/ArcCore_EcucDefs_BswM.arxml',
        'official/ecuc/ArcCore_EcucDefs_ComM.arxml',
        'official/ecuc/ArcCore_EcucDefs_EcuM.arxml',
        'official/ecuc/ArcCore_EcucDefs_Fee.arxml',
        'official/ecuc/ArcCore_EcucDefs_MemIf.arxml',
        'official/ecuc/ArcCore_EcucDefs_NvM.arxml',
        'official/ecuc/ArcCore_EcucDefs_WdgM.arxml',
        'official/ecuc/CanIf_Ecuc.arxml',
        'official/ecuc/Os_Ecuc.arxml',
        # Interface
        'official/interface/ArcCore_EcucDefs_Rte.arxml',
        'official/interface/PortInterfaces.arxml',
        # SWC
        'official/swc/ApplicationSwComponentType.arxml',
        # System
        'official/system/AUTOSAR_MOD_UpdateAndConfigManagement_Blueprint.arxml',
        'official/system/EcuExtract.arxml',
        'official/system/SCU_Configuration.arxml',
        'official/system/System.arxml',
    ]
    
    print("=" * 80)
    print("ARXML 데이터 파일 유효성 검증 결과")
    print("=" * 80)
    
    total_files = len(expected_files)
    valid_files = 0
    missing_files = []
    invalid_files = []
    
    # 카테고리별로 검증
    categories = {
        'Communication': [],
        'Diagnostic': [],
        'ECUC': [],
        'Interface': [],
        'SWC': [],
        'System': []
    }
    
    for rel_path in expected_files:
        full_path = base_dir / rel_path
        is_valid, result = validate_arxml_file(str(full_path))
        
        # 카테고리 판별
        if 'communication' in rel_path:
            category = 'Communication'
        elif 'diagnostic' in rel_path:
            category = 'Diagnostic'
        elif 'ecuc' in rel_path:
            category = 'ECUC'
        elif 'interface' in rel_path:
            category = 'Interface'
        elif 'swc' in rel_path:
            category = 'SWC'
        elif 'system' in rel_path:
            category = 'System'
        else:
            category = 'Unknown'
            
        categories[category].append((rel_path, is_valid, result))
        
        if is_valid:
            valid_files += 1
        elif not result['exists']:
            missing_files.append(rel_path)
        else:
            invalid_files.append((rel_path, result['error']))
    
    # 카테고리별 결과 출력
    for category, files in categories.items():
        if not files:
            continue
            
        print(f"\n## {category} ({len(files)} files)")
        print("-" * 40)
        
        for rel_path, is_valid, result in files:
            filename = os.path.basename(rel_path)
            size_kb = result['size_bytes'] / 1024 if result['exists'] else 0
            
            if is_valid:
                status = "✓"
                details = f"{size_kb:.1f}KB"
                if result['has_autosar_root']:
                    details += ", AUTOSAR valid"
            elif not result['exists']:
                status = "✗"
                details = "FILE NOT FOUND"
            else:
                status = "⚠"
                details = result['error'][:50] if result['error'] else "Invalid"
                
            print(f"  {status} {filename:<45} {details}")
    
    # 전체 요약
    print("\n" + "=" * 80)
    print("요약:")
    print(f"  - 전체 파일: {total_files}개")
    print(f"  - 유효한 파일: {valid_files}개 ({valid_files/total_files*100:.1f}%)")
    if missing_files:
        print(f"  - 누락된 파일: {len(missing_files)}개")
    if invalid_files:
        print(f"  - 무효한 파일: {len(invalid_files)}개")
    
    # 추가로 발견된 파일 확인
    print("\n추가 파일 확인...")
    actual_files = list(base_dir.glob('**/*.arxml'))
    expected_set = set(base_dir / f for f in expected_files)
    actual_set = set(actual_files)
    
    additional_files = actual_set - expected_set
    if additional_files:
        print(f"\n문서에 없지만 존재하는 파일 ({len(additional_files)}개):")
        for f in sorted(additional_files):
            rel = f.relative_to(base_dir)
            print(f"  + {rel}")
    
    print("\n" + "=" * 80)
    
    # 상세 문제 리포트
    if missing_files or invalid_files:
        print("\n⚠️  문제점 상세:")
        if missing_files:
            print("\n누락된 파일:")
            for f in missing_files:
                print(f"  - {f}")
        if invalid_files:
            print("\n무효한 파일:")
            for f, error in invalid_files:
                print(f"  - {f}: {error}")
    else:
        print("\n✅ 모든 문서화된 파일이 유효합니다!")
    
    return valid_files == total_files

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)