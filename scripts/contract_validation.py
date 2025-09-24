#!/usr/bin/env python3
"""
Contract Testing Validation Hook
يتحقق من صحة عقود الـ API بين الخدمات باستخدام Pact.io و Schemathesis
"""

import sys
import subprocess
import json
import os
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
import requests


class ContractValidator:
    """مُتحقق من عقود الـ API"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.pact_dir = self.project_root / 'pacts'
        self.openapi_spec = self.project_root / 'docs' / 'openapi.yaml'
        
    def validate_contracts(self) -> bool:
        """التحقق من جميع عقود الـ API"""
        print("🔍 فحص عقود الـ API...")
        
        all_passed = True
        
        # فحص Pact contracts
        if not self._validate_pact_contracts():
            all_passed = False
        
        # فحص OpenAPI schema
        if not self._validate_openapi_schema():
            all_passed = False
        
        # فحص Schemathesis
        if not self._run_schemathesis_tests():
            all_passed = False
        
        return all_passed
    
    def _validate_pact_contracts(self) -> bool:
        """التحقق من عقود Pact"""
        print("📋 فحص عقود Pact...")
        
        if not self.pact_dir.exists():
            print("⚠️ مجلد pacts غير موجود - تخطي فحص Pact")
            return True
        
        pact_files = list(self.pact_dir.glob('*.json'))
        
        if not pact_files:
            print("⚠️ لا توجد ملفات Pact للفحص")
            return True
        
        all_valid = True
        
        for pact_file in pact_files:
            if not self._validate_single_pact(pact_file):
                all_valid = False
        
        if all_valid:
            print("✅ جميع عقود Pact صحيحة")
        
        return all_valid
    
    def _validate_single_pact(self, pact_file: Path) -> bool:
        """التحقق من ملف Pact واحد"""
        try:
            with open(pact_file, 'r') as f:
                pact_data = json.load(f)
        except Exception as e:
            print(f"❌ خطأ في قراءة {pact_file.name}: {e}")
            return False
        
        # التحقق من البنية الأساسية لـ Pact
        required_fields = ['consumer', 'provider', 'interactions']
        
        for field in required_fields:
            if field not in pact_data:
                print(f"❌ {pact_file.name}: حقل مطلوب مفقود - {field}")
                return False
        
        # التحقق من الـ interactions
        interactions = pact_data.get('interactions', [])
        
        if not interactions:
            print(f"⚠️ {pact_file.name}: لا توجد interactions")
            return True
        
        for i, interaction in enumerate(interactions):
            if not self._validate_interaction(pact_file.name, i, interaction):
                return False
        
        print(f"✅ {pact_file.name}: صحيح ({len(interactions)} interactions)")
        return True
    
    def _validate_interaction(self, file_name: str, index: int, interaction: Dict) -> bool:
        """التحقق من interaction واحد"""
        required_fields = ['description', 'request', 'response']
        
        for field in required_fields:
            if field not in interaction:
                print(f"❌ {file_name}: interaction {index} - حقل مطلوب مفقود - {field}")
                return False
        
        # التحقق من بنية الـ request
        request = interaction['request']
        if 'method' not in request or 'path' not in request:
            print(f"❌ {file_name}: interaction {index} - request غير مكتمل")
            return False
        
        # التحقق من بنية الـ response
        response = interaction['response']
        if 'status' not in response:
            print(f"❌ {file_name}: interaction {index} - response status مفقود")
            return False
        
        return True
    
    def _validate_openapi_schema(self) -> bool:
        """التحقق من مخطط OpenAPI"""
        print("📋 فحص مخطط OpenAPI...")
        
        if not self.openapi_spec.exists():
            print("⚠️ ملف OpenAPI غير موجود - تخطي الفحص")
            return True
        
        try:
            # قراءة ملف OpenAPI
            with open(self.openapi_spec, 'r') as f:
                if self.openapi_spec.suffix.lower() == '.yaml':
                    spec_data = yaml.safe_load(f)
                else:
                    spec_data = json.load(f)
            
            # التحقق من البنية الأساسية
            required_fields = ['openapi', 'info', 'paths']
            
            for field in required_fields:
                if field not in spec_data:
                    print(f"❌ OpenAPI: حقل مطلوب مفقود - {field}")
                    return False
            
            # التحقق من الإصدار
            openapi_version = spec_data.get('openapi', '')
            if not openapi_version.startswith('3.'):
                print(f"⚠️ OpenAPI: إصدار غير مدعوم - {openapi_version}")
            
            # التحقق من الـ paths
            paths = spec_data.get('paths', {})
            if not paths:
                print("⚠️ OpenAPI: لا توجد paths محددة")
                return True
            
            # فحص كل path
            for path, methods in paths.items():
                for method, details in methods.items():
                    if method.upper() in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
                        if 'responses' not in details:
                            print(f"❌ OpenAPI: {method.upper()} {path} - responses مفقود")
                            return False
            
            print(f"✅ OpenAPI: صحيح ({len(paths)} paths)")
            return True
            
        except Exception as e:
            print(f"❌ خطأ في فحص OpenAPI: {e}")
            return False
    
    def _run_schemathesis_tests(self) -> bool:
        """تشغيل اختبارات Schemathesis"""
        print("🧪 تشغيل اختبارات Schemathesis...")
        
        if not self.openapi_spec.exists():
            print("⚠️ ملف OpenAPI غير موجود - تخطي Schemathesis")
            return True
        
        try:
            # التحقق من وجود schemathesis
            subprocess.run(['schemathesis', '--version'], 
                         capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("⚠️ Schemathesis غير مثبت - تخطي الاختبارات")
            return True
        
        try:
            # تشغيل اختبارات Schemathesis
            result = subprocess.run([
                'schemathesis', 'run',
                str(self.openapi_spec),
                '--checks', 'all',
                '--max-examples', '10',
                '--hypothesis-max-examples', '10'
            ], 
            capture_output=True, 
            text=True,
            timeout=120  # 2 دقائق timeout
            )
            
            if result.returncode == 0:
                print("✅ اختبارات Schemathesis نجحت")
                return True
            else:
                print("❌ فشل في اختبارات Schemathesis:")
                print(result.stdout)
                print(result.stderr)
                return False
                
        except subprocess.TimeoutExpired:
            print("❌ انتهت مهلة اختبارات Schemathesis")
            return False
        except Exception as e:
            print(f"❌ خطأ في تشغيل Schemathesis: {e}")
            return False
    
    def check_api_compatibility(self) -> bool:
        """فحص توافق الـ API مع الإصدارات السابقة"""
        print("🔄 فحص توافق الـ API...")
        
        # هذا مثال بسيط - في الواقع ستحتاج لمقارنة مع إصدار سابق
        if not self.openapi_spec.exists():
            print("⚠️ لا يمكن فحص التوافق - ملف OpenAPI غير موجود")
            return True
        
        try:
            with open(self.openapi_spec, 'r') as f:
                if self.openapi_spec.suffix.lower() == '.yaml':
                    current_spec = yaml.safe_load(f)
                else:
                    current_spec = json.load(f)
            
            # فحص أساسي للتغييرات المحتملة
            breaking_changes = self._detect_breaking_changes(current_spec)
            
            if breaking_changes:
                print("⚠️ تغييرات محتملة قد تكسر التوافق:")
                for change in breaking_changes:
                    print(f"  - {change}")
                return False
            else:
                print("✅ لا توجد تغييرات تكسر التوافق")
                return True
                
        except Exception as e:
            print(f"❌ خطأ في فحص التوافق: {e}")
            return False
    
    def _detect_breaking_changes(self, spec: Dict) -> List[str]:
        """كشف التغييرات التي قد تكسر التوافق"""
        breaking_changes = []
        
        # هذا مثال بسيط - في الواقع تحتاج لمقارنة مع إصدار سابق
        paths = spec.get('paths', {})
        
        for path, methods in paths.items():
            for method, details in methods.items():
                if method.upper() in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
                    # فحص المعاملات المطلوبة
                    parameters = details.get('parameters', [])
                    required_params = [p for p in parameters if p.get('required', False)]
                    
                    # فحص الـ request body المطلوب
                    request_body = details.get('requestBody', {})
                    if request_body.get('required', False):
                        # هذا قد يكون تغيير يكسر التوافق إذا كان جديد
                        pass
                    
                    # فحص الـ responses
                    responses = details.get('responses', {})
                    if '200' not in responses and '201' not in responses:
                        breaking_changes.append(f"{method.upper()} {path}: لا يوجد response ناجح")
        
        return breaking_changes
    
    def generate_contract_tests(self) -> bool:
        """إنشاء اختبارات عقود تلقائية"""
        print("🏗️ إنشاء اختبارات العقود...")
        
        if not self.openapi_spec.exists():
            print("⚠️ لا يمكن إنشاء اختبارات - ملف OpenAPI غير موجود")
            return False
        
        try:
            # إنشاء مجلد للاختبارات المُولدة
            generated_tests_dir = self.project_root / 'tests' / 'generated'
            generated_tests_dir.mkdir(parents=True, exist_ok=True)
            
            # قراءة مخطط OpenAPI
            with open(self.openapi_spec, 'r') as f:
                if self.openapi_spec.suffix.lower() == '.yaml':
                    spec = yaml.safe_load(f)
                else:
                    spec = json.load(f)
            
            # إنشاء اختبارات لكل endpoint
            test_content = self._generate_test_content(spec)
            
            # كتابة ملف الاختبارات
            test_file = generated_tests_dir / 'test_api_contracts.py'
            with open(test_file, 'w') as f:
                f.write(test_content)
            
            print(f"✅ تم إنشاء اختبارات العقود في {test_file}")
            return True
            
        except Exception as e:
            print(f"❌ خطأ في إنشاء اختبارات العقود: {e}")
            return False
    
    def _generate_test_content(self, spec: Dict) -> str:
        """إنشاء محتوى ملف الاختبارات"""
        content = '''"""
اختبارات العقود المُولدة تلقائياً
تم إنشاؤها من مخطط OpenAPI
"""

import pytest
import requests
from typing import Dict, Any


class TestAPIContracts:
    """اختبارات عقود الـ API"""
    
    base_url = "http://localhost:8000"  # يجب تحديثه حسب البيئة
    
'''
        
        paths = spec.get('paths', {})
        
        for path, methods in paths.items():
            for method, details in methods.items():
                if method.upper() in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
                    test_method = self._generate_test_method(path, method, details)
                    content += test_method + '\n'
        
        return content
    
    def _generate_test_method(self, path: str, method: str, details: Dict) -> str:
        """إنشاء دالة اختبار لـ endpoint واحد"""
        method_upper = method.upper()
        test_name = f"test_{method.lower()}_{path.replace('/', '_').replace('{', '').replace('}', '')}"
        
        # تنظيف اسم الاختبار
        test_name = test_name.replace('__', '_').strip('_')
        
        test_code = f'''
    def {test_name}(self):
        """اختبار {method_upper} {path}"""
        url = self.base_url + "{path}"
        
        # TODO: إضافة بيانات الاختبار المناسبة
        response = requests.{method.lower()}(url)
        
        # التحقق من الاستجابة
        assert response.status_code in [200, 201, 204], f"Unexpected status: {{response.status_code}}"
        
        # TODO: إضافة تحققات إضافية حسب المخطط
'''
        
        return test_code


def main():
    """النقطة الرئيسية للـ hook"""
    validator = ContractValidator()
    
    # التحقق من العقود
    contracts_valid = validator.validate_contracts()
    
    # فحص التوافق
    compatibility_ok = validator.check_api_compatibility()
    
    # إنشاء اختبارات إذا لزم الأمر
    if contracts_valid and compatibility_ok:
        validator.generate_contract_tests()
    
    if contracts_valid and compatibility_ok:
        print("\n✅ جميع فحوصات العقود نجحت!")
        return 0
    else:
        print("\n❌ فشل في فحص العقود")
        return 1


if __name__ == "__main__":
    sys.exit(main())
