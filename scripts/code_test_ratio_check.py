#!/usr/bin/env python3
"""
Code-Test Ratio Check
يتحقق من أن كل ملف كود له اختبارات مقابلة ومناسبة
"""

import sys
import os
import ast
import re
from pathlib import Path
from typing import Dict, List, Tuple, Set
from dataclasses import dataclass


@dataclass
class CodeFile:
    """معلومات ملف الكود"""
    path: Path
    functions: List[str]
    classes: List[str]
    complexity_score: int
    needs_tests: bool


@dataclass
class TestFile:
    """معلومات ملف الاختبار"""
    path: Path
    test_functions: List[str]
    tested_targets: Set[str]
    quality_score: int


class CodeTestRatioChecker:
    """فاحص نسبة الكود إلى الاختبارات"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.app_dir = self.project_root / 'app'
        self.tests_dir = self.project_root / 'tests'
        
        self.code_files: List[CodeFile] = []
        self.test_files: List[TestFile] = []
        
        # ملفات مستثناة من فحص الاختبارات
        self.excluded_patterns = [
            '__init__.py',
            'migrations/',
            'settings.py',
            'wsgi.py',
            'asgi.py',
            'manage.py',
        ]
    
    def check_ratio(self) -> bool:
        """فحص نسبة الكود إلى الاختبارات"""
        print("🔍 فحص نسبة الكود إلى الاختبارات...")
        
        # تحليل ملفات الكود
        self._analyze_code_files()
        
        # تحليل ملفات الاختبارات
        self._analyze_test_files()
        
        # فحص التغطية
        coverage_issues = self._check_test_coverage()
        
        # فحص جودة الاختبارات
        quality_issues = self._check_test_quality()
        
        # طباعة النتائج
        self._print_results(coverage_issues, quality_issues)
        
        return len(coverage_issues) == 0 and len(quality_issues) == 0
    
    def _analyze_code_files(self):
        """تحليل ملفات الكود"""
        print("📊 تحليل ملفات الكود...")
        
        for py_file in self.app_dir.rglob('*.py'):
            if self._should_exclude_file(py_file):
                continue
            
            code_file = self._analyze_single_code_file(py_file)
            if code_file and code_file.needs_tests:
                self.code_files.append(code_file)
        
        print(f"  وُجد {len(self.code_files)} ملف كود يحتاج اختبارات")
    
    def _analyze_test_files(self):
        """تحليل ملفات الاختبارات"""
        print("🧪 تحليل ملفات الاختبارات...")
        
        if not self.tests_dir.exists():
            print("⚠️ مجلد tests غير موجود")
            return
        
        for py_file in self.tests_dir.rglob('*.py'):
            if py_file.name.startswith('__'):
                continue
            
            test_file = self._analyze_single_test_file(py_file)
            if test_file:
                self.test_files.append(test_file)
        
        print(f"  وُجد {len(self.test_files)} ملف اختبار")
    
    def _should_exclude_file(self, file_path: Path) -> bool:
        """تحديد ما إذا كان يجب استثناء الملف"""
        file_str = str(file_path)
        return any(pattern in file_str for pattern in self.excluded_patterns)
    
    def _analyze_single_code_file(self, file_path: Path) -> CodeFile:
        """تحليل ملف كود واحد"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # تحليل AST
            tree = ast.parse(content)
            
            functions = []
            classes = []
            complexity_score = 0
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # تجاهل الدوال الخاصة والداخلية
                    if not node.name.startswith('_'):
                        functions.append(node.name)
                        complexity_score += self._calculate_function_complexity(node)
                
                elif isinstance(node, ast.ClassDef):
                    if not node.name.startswith('_'):
                        classes.append(node.name)
                        complexity_score += 2  # نقاط إضافية للكلاسات
            
            # تحديد ما إذا كان الملف يحتاج اختبارات
            needs_tests = len(functions) > 0 or len(classes) > 0
            
            return CodeFile(
                path=file_path,
                functions=functions,
                classes=classes,
                complexity_score=complexity_score,
                needs_tests=needs_tests
            )
            
        except Exception as e:
            print(f"⚠️ خطأ في تحليل {file_path}: {e}")
            return None
    
    def _calculate_function_complexity(self, func_node: ast.FunctionDef) -> int:
        """حساب تعقد الدالة"""
        complexity = 1  # نقطة أساسية
        
        for node in ast.walk(func_node):
            # إضافة نقاط للتعقد
            if isinstance(node, (ast.If, ast.While, ast.For)):
                complexity += 1
            elif isinstance(node, ast.Try):
                complexity += 1
            elif isinstance(node, ast.ExceptHandler):
                complexity += 1
        
        return complexity
    
    def _analyze_single_test_file(self, file_path: Path) -> TestFile:
        """تحليل ملف اختبار واحد"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # البحث عن دوال الاختبار
            test_functions = re.findall(r'def\s+(test_\w+)\s*\(', content)
            
            # البحث عن الأهداف المُختبرة
            tested_targets = set()
            
            # البحث عن imports من app
            app_imports = re.findall(r'from\s+app\.[\w.]+\s+import\s+([\w,\s]+)', content)
            for import_line in app_imports:
                targets = [t.strip() for t in import_line.split(',')]
                tested_targets.update(targets)
            
            # البحث عن استخدام الكلاسات والدوال في الاختبارات
            for code_file in self.code_files:
                for func in code_file.functions:
                    if func in content:
                        tested_targets.add(func)
                for cls in code_file.classes:
                    if cls in content:
                        tested_targets.add(cls)
            
            # حساب جودة الاختبارات
            quality_score = self._calculate_test_quality(content, test_functions)
            
            return TestFile(
                path=file_path,
                test_functions=test_functions,
                tested_targets=tested_targets,
                quality_score=quality_score
            )
            
        except Exception as e:
            print(f"⚠️ خطأ في تحليل {file_path}: {e}")
            return None
    
    def _calculate_test_quality(self, content: str, test_functions: List[str]) -> int:
        """حساب جودة الاختبارات"""
        if not test_functions:
            return 0
        
        quality_score = 0
        
        # عدد الـ assertions
        assert_count = len(re.findall(r'\bassert\s+', content))
        quality_score += min(assert_count, 20)  # حد أقصى 20 نقطة
        
        # تنوع الاختبارات
        if 'setUp' in content or 'fixture' in content:
            quality_score += 5
        
        # معالجة الاستثناءات
        if 'pytest.raises' in content or 'assertRaises' in content:
            quality_score += 5
        
        # استخدام mocks بشكل معقول
        mock_count = len(re.findall(r'mock\.|Mock\(|patch\(', content, re.IGNORECASE))
        if 0 < mock_count <= assert_count:
            quality_score += 3
        elif mock_count > assert_count:
            quality_score -= 5  # خصم نقاط للاستخدام المفرط
        
        # فحص الاختبارات الوهمية
        fake_patterns = [
            r'assert True',
            r'assert 1 == 1',
            r'pass\s*$',
            r'# TODO.*test',
        ]
        
        for pattern in fake_patterns:
            if re.search(pattern, content, re.IGNORECASE | re.MULTILINE):
                quality_score -= 10  # خصم كبير للاختبارات الوهمية
        
        return max(quality_score, 0)
    
    def _check_test_coverage(self) -> List[str]:
        """فحص تغطية الاختبارات"""
        coverage_issues = []
        
        # إنشاء خريطة للأهداف المُختبرة
        all_tested_targets = set()
        for test_file in self.test_files:
            all_tested_targets.update(test_file.tested_targets)
        
        # فحص كل ملف كود
        for code_file in self.code_files:
            untested_functions = []
            untested_classes = []
            
            # فحص الدوال
            for func in code_file.functions:
                if func not in all_tested_targets:
                    untested_functions.append(func)
            
            # فحص الكلاسات
            for cls in code_file.classes:
                if cls not in all_tested_targets:
                    untested_classes.append(cls)
            
            # إضافة المشاكل
            if untested_functions:
                coverage_issues.append(
                    f"❌ {code_file.path.relative_to(self.project_root)}: "
                    f"دوال غير مُختبرة: {', '.join(untested_functions)}"
                )
            
            if untested_classes:
                coverage_issues.append(
                    f"❌ {code_file.path.relative_to(self.project_root)}: "
                    f"كلاسات غير مُختبرة: {', '.join(untested_classes)}"
                )
            
            # فحص التعقد مقابل عدد الاختبارات
            expected_tests = max(1, code_file.complexity_score // 3)
            actual_tests = len([tf for tf in self.test_files 
                             if any(target in code_file.functions + code_file.classes 
                                   for target in tf.tested_targets)])
            
            if actual_tests < expected_tests:
                coverage_issues.append(
                    f"⚠️ {code_file.path.relative_to(self.project_root)}: "
                    f"عدد الاختبارات قليل (موجود: {actual_tests}, مطلوب: {expected_tests})"
                )
        
        return coverage_issues
    
    def _check_test_quality(self) -> List[str]:
        """فحص جودة الاختبارات"""
        quality_issues = []
        
        for test_file in self.test_files:
            # فحص الجودة العامة
            if test_file.quality_score < 10:
                quality_issues.append(
                    f"⚠️ {test_file.path.relative_to(self.project_root)}: "
                    f"جودة الاختبارات منخفضة (النقاط: {test_file.quality_score})"
                )
            
            # فحص عدد الاختبارات
            if len(test_file.test_functions) == 0:
                quality_issues.append(
                    f"❌ {test_file.path.relative_to(self.project_root)}: "
                    f"لا يحتوي على دوال اختبار"
                )
            
            # فحص نسبة الاختبارات إلى الأهداف
            if len(test_file.tested_targets) == 0:
                quality_issues.append(
                    f"❌ {test_file.path.relative_to(self.project_root)}: "
                    f"لا يختبر أي أهداف واضحة"
                )
        
        return quality_issues
    
    def _print_results(self, coverage_issues: List[str], quality_issues: List[str]):
        """طباعة النتائج"""
        print("\n📊 نتائج فحص نسبة الكود إلى الاختبارات:")
        
        # إحصائيات عامة
        total_functions = sum(len(cf.functions) for cf in self.code_files)
        total_classes = sum(len(cf.classes) for cf in self.code_files)
        total_test_functions = sum(len(tf.test_functions) for tf in self.test_files)
        
        print(f"  📈 إجمالي الدوال: {total_functions}")
        print(f"  📈 إجمالي الكلاسات: {total_classes}")
        print(f"  🧪 إجمالي اختبارات الدوال: {total_test_functions}")
        
        if total_functions + total_classes > 0:
            test_ratio = total_test_functions / (total_functions + total_classes)
            print(f"  📊 نسبة الاختبارات: {test_ratio:.2f}")
            
            if test_ratio < 0.8:
                print("  ⚠️ نسبة الاختبارات منخفضة (المطلوب: 0.8 على الأقل)")
        
        # مشاكل التغطية
        if coverage_issues:
            print(f"\n❌ مشاكل التغطية ({len(coverage_issues)}):")
            for issue in coverage_issues:
                print(f"  {issue}")
        
        # مشاكل الجودة
        if quality_issues:
            print(f"\n⚠️ مشاكل الجودة ({len(quality_issues)}):")
            for issue in quality_issues:
                print(f"  {issue}")
        
        # النتيجة النهائية
        if not coverage_issues and not quality_issues:
            print("\n✅ جميع فحوصات نسبة الكود إلى الاختبارات نجحت!")
        else:
            print(f"\n❌ وُجدت {len(coverage_issues + quality_issues)} مشكلة")
    
    def generate_missing_tests_template(self) -> bool:
        """إنشاء قوالب للاختبارات المفقودة"""
        print("🏗️ إنشاء قوالب للاختبارات المفقودة...")
        
        # إنشاء مجلد للقوالب
        templates_dir = self.project_root / 'tests' / 'templates'
        templates_dir.mkdir(parents=True, exist_ok=True)
        
        for code_file in self.code_files:
            # تحديد ما إذا كان هناك اختبارات موجودة
            has_tests = any(
                any(target in code_file.functions + code_file.classes 
                    for target in tf.tested_targets)
                for tf in self.test_files
            )
            
            if not has_tests:
                template_content = self._generate_test_template(code_file)
                
                # تحديد اسم ملف الاختبار
                relative_path = code_file.path.relative_to(self.app_dir)
                test_file_name = f"test_{relative_path.stem}.py"
                test_file_path = templates_dir / test_file_name
                
                with open(test_file_path, 'w', encoding='utf-8') as f:
                    f.write(template_content)
                
                print(f"  📝 تم إنشاء قالب: {test_file_path}")
        
        return True
    
    def _generate_test_template(self, code_file: CodeFile) -> str:
        """إنشاء قالب اختبار لملف كود"""
        relative_path = code_file.path.relative_to(self.app_dir)
        module_path = str(relative_path.with_suffix('')).replace('/', '.')
        
        template = f'''"""
اختبارات لـ {code_file.path.name}
تم إنشاؤها تلقائياً - يرجى تخصيصها حسب الحاجة
"""

import pytest
from unittest.mock import Mock, patch
from app.{module_path} import (
'''
        
        # إضافة imports
        all_targets = code_file.functions + code_file.classes
        for target in all_targets:
            template += f"    {target},\n"
        
        template += ")\n\n\n"
        
        # إنشاء اختبارات للكلاسات
        for cls in code_file.classes:
            template += f'''class Test{cls}:
    """اختبارات كلاس {cls}"""
    
    def test_{cls.lower()}_creation(self):
        """اختبار إنشاء كائن من {cls}"""
        # TODO: إضافة اختبار إنشاء الكائن
        instance = {cls}()
        assert instance is not None
    
    def test_{cls.lower()}_methods(self):
        """اختبار دوال {cls}"""
        # TODO: إضافة اختبارات للدوال
        pass

'''
        
        # إنشاء اختبارات للدوال
        for func in code_file.functions:
            template += f'''def test_{func}():
    """اختبار دالة {func}"""
    # TODO: إضافة اختبار شامل للدالة
    # تأكد من اختبار:
    # - الحالات العادية
    # - الحالات الاستثنائية
    # - القيم الحدية
    pass

'''
        
        return template


def main():
    """النقطة الرئيسية للسكريبت"""
    checker = CodeTestRatioChecker()
    
    # فحص النسبة
    ratio_ok = checker.check_ratio()
    
    # إنشاء قوالب إذا لزم الأمر
    if not ratio_ok:
        checker.generate_missing_tests_template()
        print("\n💡 تم إنشاء قوالب للاختبارات المفقودة في مجلد tests/templates/")
        print("يرجى مراجعتها وتخصيصها ونقلها إلى المكان المناسب")
    
    return 0 if ratio_ok else 1


if __name__ == "__main__":
    sys.exit(main())
