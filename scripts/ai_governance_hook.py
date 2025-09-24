#!/usr/bin/env python3
"""
AI Governance Pre-commit Hook
يتحقق من أن الكود المُضاف يتبع قواعد حوكمة الذكاء الاصطناعي
"""

import sys
import os
import ast
import re
from pathlib import Path
from typing import List, Dict, Tuple

# إضافة مسار المشروع للـ Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from app.ai_governance.code_governor import CodeGovernor, CodeQualityLevel, TestQualityLevel
except ImportError:
    print("⚠️ تعذر استيراد CodeGovernor - سيتم استخدام فحص أساسي")
    CodeGovernor = None


class AIGovernanceHook:
    """Hook للتحقق من حوكمة الذكاء الاصطناعي قبل الـ commit"""
    
    def __init__(self):
        self.governor = CodeGovernor() if CodeGovernor else None
        self.errors = []
        self.warnings = []
        
    def check_files(self, file_paths: List[str]) -> bool:
        """فحص الملفات المُضافة أو المُعدلة"""
        print("🔍 فحص حوكمة الذكاء الاصطناعي...")
        
        python_files = [f for f in file_paths if f.endswith('.py')]
        
        if not python_files:
            print("✅ لا توجد ملفات Python للفحص")
            return True
        
        all_passed = True
        
        for file_path in python_files:
            if not self._check_single_file(file_path):
                all_passed = False
        
        self._print_results()
        return all_passed
    
    def _check_single_file(self, file_path: str) -> bool:
        """فحص ملف واحد"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            self.errors.append(f"❌ {file_path}: تعذر قراءة الملف - {e}")
            return False
        
        # تخطي الملفات الفارغة أو ملفات __init__.py
        if not content.strip() or file_path.endswith('__init__.py'):
            return True
        
        # فحص أساسي للبنية
        if not self._check_basic_structure(file_path, content):
            return False
        
        # فحص متقدم باستخدام CodeGovernor إذا كان متاحاً
        if self.governor:
            return self._check_with_governor(file_path, content)
        else:
            return self._check_basic_rules(file_path, content)
    
    def _check_basic_structure(self, file_path: str, content: str) -> bool:
        """فحص البنية الأساسية للكود"""
        try:
            ast.parse(content)
        except SyntaxError as e:
            self.errors.append(f"❌ {file_path}: خطأ في بناء الجملة - {e}")
            return False
        
        return True
    
    def _check_with_governor(self, file_path: str, content: str) -> bool:
        """فحص متقدم باستخدام CodeGovernor"""
        analysis = self.governor.analyze_ai_response(content)
        
        file_passed = True
        
        # فحص جودة الكود
        if analysis.code_quality == CodeQualityLevel.BLOCKED:
            self.errors.append(f"❌ {file_path}: جودة الكود غير مقبولة")
            file_passed = False
        elif analysis.code_quality == CodeQualityLevel.POOR:
            self.warnings.append(f"⚠️ {file_path}: جودة الكود ضعيفة")
        
        # فحص الاختبارات
        if analysis.has_code and not analysis.has_tests:
            # تحقق إذا كان الملف يحتوي على دوال أو كلاسات تحتاج اختبارات
            if self._needs_tests(content):
                self.errors.append(f"❌ {file_path}: الكود يحتاج إلى اختبارات")
                file_passed = False
        
        if analysis.test_quality == TestQualityLevel.FAKE_TESTS:
            self.errors.append(f"❌ {file_path}: الاختبارات وهمية أو غير فعالة")
            file_passed = False
        
        # فحص التغطية
        if analysis.coverage_estimate < 0.8 and analysis.has_tests:
            self.warnings.append(f"⚠️ {file_path}: تغطية الاختبارات منخفضة ({analysis.coverage_estimate:.1%})")
        
        # إضافة الانتهاكات
        for violation in analysis.violations:
            if any(word in violation.lower() for word in ['أمان', 'security', 'محظور']):
                self.errors.append(f"❌ {file_path}: {violation}")
                file_passed = False
            else:
                self.warnings.append(f"⚠️ {file_path}: {violation}")
        
        return file_passed
    
    def _check_basic_rules(self, file_path: str, content: str) -> bool:
        """فحص أساسي للقواعد بدون CodeGovernor"""
        file_passed = True
        
        # فحص الأنماط المحظورة
        forbidden_patterns = [
            (r'\beval\s*\(', "استخدام eval() محظور لأسباب أمنية"),
            (r'\bexec\s*\(', "استخدام exec() محظور لأسباب أمنية"),
            (r'password\s*=\s*[\'"][^\'"]+[\'"]', "كلمة مرور مكشوفة في الكود"),
            (r'secret\s*=\s*[\'"][^\'"]+[\'"]', "مفتاح سري مكشوف في الكود"),
            (r'except:\s*pass', "معالجة أخطاء فارغة غير مسموحة"),
        ]
        
        for pattern, message in forbidden_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                self.errors.append(f"❌ {file_path}: {message}")
                file_passed = False
        
        # فحص وجود الاختبارات للكود الجديد
        if self._needs_tests(content) and not self._has_tests(content):
            # تحقق إذا كان هناك ملف اختبار منفصل
            test_file_paths = [
                file_path.replace('.py', '_test.py'),
                file_path.replace('.py', '_tests.py'),
                file_path.replace('app/', 'tests/').replace('.py', '_test.py'),
                file_path.replace('app/', 'tests/unit/').replace('.py', '_test.py'),
            ]
            
            has_separate_test_file = any(os.path.exists(test_path) for test_path in test_file_paths)
            
            if not has_separate_test_file:
                self.warnings.append(f"⚠️ {file_path}: الكود يحتاج إلى اختبارات")
        
        return file_passed
    
    def _needs_tests(self, content: str) -> bool:
        """تحديد ما إذا كان الكود يحتاج إلى اختبارات"""
        # البحث عن دوال أو كلاسات (باستثناء الـ private methods)
        functions = re.findall(r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', content)
        classes = re.findall(r'class\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', content)
        
        # تصفية الدوال الخاصة والداخلية
        public_functions = [f for f in functions if not f.startswith('_')]
        public_classes = [c for c in classes if not c.startswith('_')]
        
        return len(public_functions) > 0 or len(public_classes) > 0
    
    def _has_tests(self, content: str) -> bool:
        """تحديد ما إذا كان الملف يحتوي على اختبارات"""
        test_indicators = [
            r'def\s+test_\w+\s*\(',
            r'class\s+Test\w+\s*\(',
            r'@pytest\.',
            r'import\s+pytest',
            r'from\s+.*\s+import\s+.*test',
            r'assert\s+',
            r'self\.assert\w+\(',
        ]
        
        for pattern in test_indicators:
            if re.search(pattern, content, re.IGNORECASE):
                return True
        
        return False
    
    def _print_results(self):
        """طباعة نتائج الفحص"""
        if self.errors:
            print("\n❌ أخطاء يجب إصلاحها:")
            for error in self.errors:
                print(f"  {error}")
        
        if self.warnings:
            print("\n⚠️ تحذيرات:")
            for warning in self.warnings:
                print(f"  {warning}")
        
        if not self.errors and not self.warnings:
            print("✅ جميع الفحوصات نجحت!")
        elif not self.errors:
            print("✅ لا توجد أخطاء حرجة")


def main():
    """النقطة الرئيسية للـ hook"""
    if len(sys.argv) < 2:
        print("❌ لم يتم تمرير ملفات للفحص")
        return 1
    
    file_paths = sys.argv[1:]
    hook = AIGovernanceHook()
    
    if hook.check_files(file_paths):
        return 0
    else:
        print("\n❌ فشل فحص حوكمة الذكاء الاصطناعي")
        print("يرجى إصلاح الأخطاء المذكورة أعلاه قبل المتابعة")
        return 1


if __name__ == "__main__":
    sys.exit(main())
