#!/usr/bin/env python3
"""
Test Coverage Check Hook
يتحقق من أن تغطية الاختبارات تتجاوز الحد الأدنى المطلوب (90%)
"""

import sys
import subprocess
import json
import os
from pathlib import Path


class CoverageChecker:
    """فاحص تغطية الاختبارات"""
    
    def __init__(self, minimum_coverage: float = 90.0):
        self.minimum_coverage = minimum_coverage
        self.project_root = Path(__file__).parent.parent
        
    def check_coverage(self) -> bool:
        """فحص تغطية الاختبارات"""
        print(f"🔍 فحص تغطية الاختبارات (الحد الأدنى: {self.minimum_coverage}%)...")
        
        try:
            # تشغيل الاختبارات مع قياس التغطية
            result = subprocess.run([
                'python', '-m', 'pytest',
                '--cov=app',
                '--cov-report=json',
                '--cov-report=term-missing',
                '--cov-fail-under=' + str(self.minimum_coverage),
                'tests/'
            ], 
            cwd=self.project_root,
            capture_output=True,
            text=True,
            timeout=300  # 5 دقائق timeout
            )
            
            # قراءة تقرير التغطية JSON
            coverage_data = self._read_coverage_report()
            
            if coverage_data:
                self._print_coverage_summary(coverage_data)
                
                total_coverage = coverage_data.get('totals', {}).get('percent_covered', 0)
                
                if total_coverage >= self.minimum_coverage:
                    print(f"✅ تغطية الاختبارات مقبولة: {total_coverage:.1f}%")
                    return True
                else:
                    print(f"❌ تغطية الاختبارات منخفضة: {total_coverage:.1f}% (المطلوب: {self.minimum_coverage}%)")
                    self._print_uncovered_lines(coverage_data)
                    return False
            else:
                print("⚠️ تعذر قراءة تقرير التغطية")
                return result.returncode == 0
                
        except subprocess.TimeoutExpired:
            print("❌ انتهت مهلة تشغيل الاختبارات (5 دقائق)")
            return False
        except Exception as e:
            print(f"❌ خطأ في تشغيل فحص التغطية: {e}")
            return False
    
    def _read_coverage_report(self) -> dict:
        """قراءة تقرير التغطية من ملف JSON"""
        coverage_file = self.project_root / 'coverage.json'
        
        if not coverage_file.exists():
            return {}
        
        try:
            with open(coverage_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ تعذر قراءة ملف التغطية: {e}")
            return {}
    
    def _print_coverage_summary(self, coverage_data: dict):
        """طباعة ملخص التغطية"""
        totals = coverage_data.get('totals', {})
        
        print("\n📊 ملخص تغطية الاختبارات:")
        print(f"  إجمالي الأسطر: {totals.get('num_statements', 0)}")
        print(f"  الأسطر المُختبرة: {totals.get('covered_lines', 0)}")
        print(f"  الأسطر غير المُختبرة: {totals.get('missing_lines', 0)}")
        print(f"  نسبة التغطية: {totals.get('percent_covered', 0):.1f}%")
        
        # عرض تفاصيل الملفات ذات التغطية المنخفضة
        files = coverage_data.get('files', {})
        low_coverage_files = []
        
        for file_path, file_data in files.items():
            coverage_percent = file_data.get('summary', {}).get('percent_covered', 0)
            if coverage_percent < self.minimum_coverage:
                low_coverage_files.append((file_path, coverage_percent))
        
        if low_coverage_files:
            print(f"\n⚠️ ملفات بتغطية أقل من {self.minimum_coverage}%:")
            for file_path, coverage in sorted(low_coverage_files, key=lambda x: x[1]):
                print(f"  {file_path}: {coverage:.1f}%")
    
    def _print_uncovered_lines(self, coverage_data: dict):
        """طباعة الأسطر غير المُختبرة"""
        files = coverage_data.get('files', {})
        
        print("\n🔍 الأسطر غير المُختبرة:")
        
        for file_path, file_data in files.items():
            missing_lines = file_data.get('missing_lines', [])
            if missing_lines:
                print(f"\n  📄 {file_path}:")
                
                # تجميع الأسطر المتتالية
                ranges = self._group_consecutive_lines(missing_lines)
                for range_str in ranges:
                    print(f"    السطر {range_str}")
    
    def _group_consecutive_lines(self, lines: list) -> list:
        """تجميع الأسطر المتتالية في نطاقات"""
        if not lines:
            return []
        
        lines = sorted(lines)
        ranges = []
        start = lines[0]
        end = lines[0]
        
        for line in lines[1:]:
            if line == end + 1:
                end = line
            else:
                if start == end:
                    ranges.append(str(start))
                else:
                    ranges.append(f"{start}-{end}")
                start = end = line
        
        # إضافة النطاق الأخير
        if start == end:
            ranges.append(str(start))
        else:
            ranges.append(f"{start}-{end}")
        
        return ranges
    
    def check_test_quality(self) -> bool:
        """فحص جودة الاختبارات"""
        print("🔍 فحص جودة الاختبارات...")
        
        test_files = list(self.project_root.glob('tests/**/*.py'))
        test_files = [f for f in test_files if not f.name.startswith('__')]
        
        if not test_files:
            print("❌ لا توجد ملفات اختبارات")
            return False
        
        quality_issues = []
        
        for test_file in test_files:
            issues = self._check_test_file_quality(test_file)
            if issues:
                quality_issues.extend([(test_file, issue) for issue in issues])
        
        if quality_issues:
            print("\n⚠️ مشاكل في جودة الاختبارات:")
            for test_file, issue in quality_issues:
                print(f"  {test_file.relative_to(self.project_root)}: {issue}")
            return False
        else:
            print("✅ جودة الاختبارات مقبولة")
            return True
    
    def _check_test_file_quality(self, test_file: Path) -> list:
        """فحص جودة ملف اختبار واحد"""
        issues = []
        
        try:
            with open(test_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception:
            issues.append("تعذر قراءة الملف")
            return issues
        
        # فحص الاختبارات الوهمية
        fake_test_patterns = [
            r'assert True',
            r'assert 1 == 1',
            r'pass\s*$',
            r'# TODO.*test',
            r'# placeholder',
        ]
        
        for pattern in fake_test_patterns:
            if re.search(pattern, content, re.IGNORECASE | re.MULTILINE):
                issues.append(f"اختبار وهمي محتمل: {pattern}")
        
        # فحص عدد الـ assertions
        import re
        assert_count = len(re.findall(r'\bassert\s+', content))
        test_function_count = len(re.findall(r'def\s+test_\w+', content))
        
        if test_function_count > 0 and assert_count / test_function_count < 1.5:
            issues.append("عدد assertions قليل نسبة للاختبارات")
        
        # فحص استخدام mocks المفرط
        mock_count = len(re.findall(r'mock\.|Mock\(|patch\(', content, re.IGNORECASE))
        if mock_count > assert_count:
            issues.append("استخدام مفرط للـ mocks")
        
        return issues


def main():
    """النقطة الرئيسية للـ hook"""
    checker = CoverageChecker()
    
    # فحص تغطية الاختبارات
    coverage_passed = checker.check_coverage()
    
    # فحص جودة الاختبارات
    quality_passed = checker.check_test_quality()
    
    if coverage_passed and quality_passed:
        print("\n✅ جميع فحوصات الاختبارات نجحت!")
        return 0
    else:
        print("\n❌ فشل في فحص الاختبارات")
        print("يرجى إصلاح المشاكل المذكورة أعلاه قبل المتابعة")
        return 1


if __name__ == "__main__":
    import re
    sys.exit(main())
