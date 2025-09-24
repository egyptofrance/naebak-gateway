"""
AI Code Governor - نظام حاكم متقدم للتحكم في نماذج الذكاء الاصطناعي

هذا النظام يضمن أن أي نموذج ذكاء اصطناعي يساعد في البرمجة:
1. لا ينتج كود بدون اختبارات
2. لا يقدم اختبارات وهمية أو غير فعالة
3. يتبع مسار محدد ومقيد للبرمجة
"""

import ast
import re
import subprocess
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger('ai_governance.code_governor')


class CodeQualityLevel(Enum):
    """مستويات جودة الكود"""
    BLOCKED = "blocked"
    POOR = "poor"
    ACCEPTABLE = "acceptable"
    GOOD = "good"
    EXCELLENT = "excellent"


class TestQualityLevel(Enum):
    """مستويات جودة الاختبارات"""
    NO_TESTS = "no_tests"
    FAKE_TESTS = "fake_tests"
    WEAK_TESTS = "weak_tests"
    ADEQUATE_TESTS = "adequate_tests"
    COMPREHENSIVE_TESTS = "comprehensive_tests"


@dataclass
class CodeAnalysisResult:
    """نتيجة تحليل الكود"""
    has_code: bool
    has_tests: bool
    code_quality: CodeQualityLevel
    test_quality: TestQualityLevel
    coverage_estimate: float
    violations: List[str]
    suggestions: List[str]
    is_approved: bool


@dataclass
class AIGovernanceRule:
    """قاعدة حوكمة للذكاء الاصطناعي"""
    name: str
    description: str
    is_mandatory: bool
    violation_action: str  # "block", "warn", "modify"


class CodeGovernor:
    """
    نظام حاكم للكود المُولد بواسطة الذكاء الاصطناعي
    يضمن جودة الكود والاختبارات قبل السماح بالاستخدام
    """
    
    def __init__(self):
        self.rules = self._load_governance_rules()
        self.mandatory_patterns = self._load_mandatory_patterns()
        self.forbidden_patterns = self._load_forbidden_patterns()
        
    def _load_governance_rules(self) -> List[AIGovernanceRule]:
        """تحميل قواعد الحوكمة"""
        return [
            AIGovernanceRule(
                name="code_must_have_tests",
                description="أي كود يجب أن يكون مصحوب باختبارات",
                is_mandatory=True,
                violation_action="block"
            ),
            AIGovernanceRule(
                name="tests_must_be_real",
                description="الاختبارات يجب أن تكون حقيقية وليست وهمية",
                is_mandatory=True,
                violation_action="block"
            ),
            AIGovernanceRule(
                name="minimum_coverage",
                description="الاختبارات يجب أن تغطي 80% على الأقل من الكود",
                is_mandatory=True,
                violation_action="warn"
            ),
            AIGovernanceRule(
                name="follow_coding_standards",
                description="الكود يجب أن يتبع معايير البرمجة المحددة",
                is_mandatory=True,
                violation_action="modify"
            ),
            AIGovernanceRule(
                name="security_best_practices",
                description="الكود يجب أن يتبع أفضل ممارسات الأمان",
                is_mandatory=True,
                violation_action="block"
            ),
            AIGovernanceRule(
                name="documentation_required",
                description="الكود يجب أن يحتوي على توثيق مناسب",
                is_mandatory=False,
                violation_action="warn"
            )
        ]
    
    def _load_mandatory_patterns(self) -> Dict[str, List[str]]:
        """أنماط إجبارية يجب وجودها في الكود"""
        return {
            "test_patterns": [
                r"def test_\w+\(",
                r"class Test\w+\(",
                r"@pytest\.",
                r"assert\s+",
                r"self\.assert\w+\("
            ],
            "security_patterns": [
                r"@login_required",
                r"@permission_required",
                r"authenticate\(",
                r"validate_\w+\(",
                r"sanitize_\w+\("
            ],
            "documentation_patterns": [
                r'"""[\s\S]*?"""',
                r"# TODO:",
                r"# FIXME:",
                r"Args:",
                r"Returns:"
            ]
        }
    
    def _load_forbidden_patterns(self) -> Dict[str, List[str]]:
        """أنماط محظورة في الكود"""
        return {
            "fake_test_patterns": [
                r"pass\s*$",
                r"assert True",
                r"assert 1 == 1",
                r"# TODO: implement test",
                r"# placeholder test",
                r"mock\.return_value = True",
                r"@patch.*return_value=True"
            ],
            "security_violations": [
                r"eval\(",
                r"exec\(",
                r"__import__\(",
                r"input\(\)",
                r"raw_input\(\)",
                r"shell=True",
                r"password\s*=\s*['\"].*['\"]",
                r"secret\s*=\s*['\"].*['\"]"
            ],
            "bad_practices": [
                r"except:\s*pass",
                r"except Exception:\s*pass",
                r"print\(",
                r"import \*",
                r"global \w+",
                r"# hack",
                r"# quick fix"
            ]
        }
    
    def analyze_ai_response(self, response: str, context: Dict[str, Any] = None) -> CodeAnalysisResult:
        """
        تحليل شامل لاستجابة الذكاء الاصطناعي
        """
        logger.info("بدء تحليل استجابة الذكاء الاصطناعي")
        
        # استخراج الكود من الاستجابة
        code_blocks = self._extract_code_blocks(response)
        test_blocks = self._extract_test_blocks(response)
        
        # تحليل جودة الكود
        code_quality = self._analyze_code_quality(code_blocks)
        
        # تحليل جودة الاختبارات
        test_quality = self._analyze_test_quality(test_blocks)
        
        # تقدير التغطية
        coverage_estimate = self._estimate_coverage(code_blocks, test_blocks)
        
        # البحث عن انتهاكات
        violations = self._find_violations(response, code_blocks, test_blocks)
        
        # إنشاء اقتراحات للتحسين
        suggestions = self._generate_suggestions(code_blocks, test_blocks, violations)
        
        # تحديد ما إذا كانت الاستجابة مقبولة
        is_approved = self._is_response_approved(code_quality, test_quality, violations)
        
        result = CodeAnalysisResult(
            has_code=len(code_blocks) > 0,
            has_tests=len(test_blocks) > 0,
            code_quality=code_quality,
            test_quality=test_quality,
            coverage_estimate=coverage_estimate,
            violations=violations,
            suggestions=suggestions,
            is_approved=is_approved
        )
        
        logger.info(f"تم تحليل الاستجابة: جودة الكود={code_quality.value}, جودة الاختبارات={test_quality.value}, مقبول={is_approved}")
        
        return result
    
    def _extract_code_blocks(self, response: str) -> List[str]:
        """استخراج كتل الكود من الاستجابة"""
        # البحث عن كتل الكود المحاطة بـ ```
        code_pattern = r"```(?:python|py)?\n(.*?)\n```"
        code_blocks = re.findall(code_pattern, response, re.DOTALL | re.IGNORECASE)
        
        # البحث عن كتل الكود المحاطة بـ `
        inline_code_pattern = r"`([^`\n]+)`"
        inline_codes = re.findall(inline_code_pattern, response)
        
        # فلترة الكود الحقيقي (يحتوي على كلمات مفتاحية Python)
        python_keywords = ['def ', 'class ', 'import ', 'from ', 'if ', 'for ', 'while ', 'try:', 'except:']
        
        real_code_blocks = []
        for block in code_blocks + inline_codes:
            if any(keyword in block for keyword in python_keywords):
                real_code_blocks.append(block.strip())
        
        return real_code_blocks
    
    def _extract_test_blocks(self, response: str) -> List[str]:
        """استخراج كتل الاختبارات من الاستجابة"""
        code_blocks = self._extract_code_blocks(response)
        test_blocks = []
        
        test_indicators = ['test_', 'Test', 'pytest', 'unittest', 'assert', 'mock']
        
        for block in code_blocks:
            if any(indicator in block for indicator in test_indicators):
                test_blocks.append(block)
        
        return test_blocks
    
    def _analyze_code_quality(self, code_blocks: List[str]) -> CodeQualityLevel:
        """تحليل جودة الكود"""
        if not code_blocks:
            return CodeQualityLevel.ACCEPTABLE
        
        total_score = 0
        total_blocks = len(code_blocks)
        
        for block in code_blocks:
            score = 0
            
            # فحص البنية الأساسية
            if self._has_proper_structure(block):
                score += 2
            
            # فحص التوثيق
            if self._has_documentation(block):
                score += 2
            
            # فحص معالجة الأخطاء
            if self._has_error_handling(block):
                score += 2
            
            # فحص الأمان
            if not self._has_security_issues(block):
                score += 2
            
            # فحص أفضل الممارسات
            if self._follows_best_practices(block):
                score += 2
            
            total_score += score
        
        average_score = total_score / (total_blocks * 10)  # النتيجة من 0 إلى 1
        
        if average_score >= 0.9:
            return CodeQualityLevel.EXCELLENT
        elif average_score >= 0.7:
            return CodeQualityLevel.GOOD
        elif average_score >= 0.5:
            return CodeQualityLevel.ACCEPTABLE
        elif average_score >= 0.3:
            return CodeQualityLevel.POOR
        else:
            return CodeQualityLevel.BLOCKED
    
    def _analyze_test_quality(self, test_blocks: List[str]) -> TestQualityLevel:
        """تحليل جودة الاختبارات"""
        if not test_blocks:
            return TestQualityLevel.NO_TESTS
        
        fake_test_count = 0
        weak_test_count = 0
        good_test_count = 0
        
        for test_block in test_blocks:
            if self._is_fake_test(test_block):
                fake_test_count += 1
            elif self._is_weak_test(test_block):
                weak_test_count += 1
            else:
                good_test_count += 1
        
        total_tests = len(test_blocks)
        
        if fake_test_count > total_tests * 0.5:
            return TestQualityLevel.FAKE_TESTS
        elif weak_test_count > total_tests * 0.5:
            return TestQualityLevel.WEAK_TESTS
        elif good_test_count > total_tests * 0.8:
            return TestQualityLevel.COMPREHENSIVE_TESTS
        else:
            return TestQualityLevel.ADEQUATE_TESTS
    
    def _estimate_coverage(self, code_blocks: List[str], test_blocks: List[str]) -> float:
        """تقدير تغطية الاختبارات"""
        if not code_blocks or not test_blocks:
            return 0.0
        
        # استخراج الدوال والكلاسات من الكود
        code_functions = []
        for block in code_blocks:
            functions = re.findall(r'def\s+(\w+)\s*\(', block)
            classes = re.findall(r'class\s+(\w+)\s*\(', block)
            code_functions.extend(functions + classes)
        
        if not code_functions:
            return 0.0
        
        # البحث عن اختبارات لكل دالة/كلاس
        tested_functions = 0
        for func in code_functions:
            for test_block in test_blocks:
                if func.lower() in test_block.lower():
                    tested_functions += 1
                    break
        
        coverage = tested_functions / len(code_functions)
        return min(coverage, 1.0)
    
    def _find_violations(self, response: str, code_blocks: List[str], test_blocks: List[str]) -> List[str]:
        """البحث عن انتهاكات قواعد الحوكمة"""
        violations = []
        
        # فحص وجود الكود مع الاختبارات
        if code_blocks and not test_blocks:
            violations.append("الكود المقدم لا يحتوي على اختبارات - مطلوب إضافة اختبارات شاملة")
        
        # فحص الاختبارات الوهمية
        for i, test_block in enumerate(test_blocks):
            if self._is_fake_test(test_block):
                violations.append(f"الاختبار رقم {i+1} يبدو وهمياً أو غير فعال")
        
        # فحص الأنماط المحظورة
        all_code = " ".join(code_blocks + test_blocks)
        
        for category, patterns in self.forbidden_patterns.items():
            for pattern in patterns:
                if re.search(pattern, all_code, re.IGNORECASE):
                    violations.append(f"تم العثور على نمط محظور ({category}): {pattern}")
        
        # فحص الأمان
        security_issues = self._check_security_issues(code_blocks)
        violations.extend(security_issues)
        
        return violations
    
    def _generate_suggestions(self, code_blocks: List[str], test_blocks: List[str], violations: List[str]) -> List[str]:
        """إنشاء اقتراحات للتحسين"""
        suggestions = []
        
        if not test_blocks and code_blocks:
            suggestions.append("يُنصح بإضافة اختبارات شاملة تغطي جميع الحالات المحتملة")
            suggestions.append("استخدم pytest لكتابة اختبارات فعالة ومقروءة")
        
        if test_blocks:
            for test_block in test_blocks:
                if 'assert' not in test_block:
                    suggestions.append("تأكد من وجود assertions واضحة في الاختبارات")
                
                if 'mock' in test_block.lower() and 'return_value' in test_block:
                    suggestions.append("تجنب الاعتماد المفرط على mocks - استخدم بيانات حقيقية عند الإمكان")
        
        for code_block in code_blocks:
            if '"""' not in code_block and "'''" not in code_block:
                suggestions.append("أضف docstrings للدوال والكلاسات لتحسين التوثيق")
            
            if 'try:' not in code_block and ('open(' in code_block or 'requests.' in code_block):
                suggestions.append("أضف معالجة للأخطاء للعمليات التي قد تفشل")
        
        if violations:
            suggestions.append("راجع الانتهاكات المذكورة وقم بإصلاحها قبل استخدام الكود")
        
        return suggestions
    
    def _is_response_approved(self, code_quality: CodeQualityLevel, test_quality: TestQualityLevel, violations: List[str]) -> bool:
        """تحديد ما إذا كانت الاستجابة مقبولة"""
        # رفض الكود ذو الجودة المنخفضة
        if code_quality in [CodeQualityLevel.BLOCKED, CodeQualityLevel.POOR]:
            return False
        
        # رفض الاختبارات الوهمية أو المفقودة
        if test_quality in [TestQualityLevel.NO_TESTS, TestQualityLevel.FAKE_TESTS]:
            return False
        
        # رفض في حالة وجود انتهاكات أمنية خطيرة
        critical_violations = [v for v in violations if any(word in v.lower() for word in ['أمان', 'security', 'محظور', 'خطر'])]
        if critical_violations:
            return False
        
        return True
    
    def _has_proper_structure(self, code: str) -> bool:
        """فحص البنية الصحيحة للكود"""
        try:
            ast.parse(code)
            return True
        except SyntaxError:
            return False
    
    def _has_documentation(self, code: str) -> bool:
        """فحص وجود التوثيق"""
        return '"""' in code or "'''" in code or re.search(r'#.*\w+', code)
    
    def _has_error_handling(self, code: str) -> bool:
        """فحص معالجة الأخطاء"""
        return 'try:' in code and 'except' in code
    
    def _has_security_issues(self, code: str) -> bool:
        """فحص المشاكل الأمنية"""
        for pattern in self.forbidden_patterns['security_violations']:
            if re.search(pattern, code, re.IGNORECASE):
                return True
        return False
    
    def _follows_best_practices(self, code: str) -> bool:
        """فحص اتباع أفضل الممارسات"""
        bad_patterns = self.forbidden_patterns['bad_practices']
        for pattern in bad_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                return False
        return True
    
    def _is_fake_test(self, test_code: str) -> bool:
        """فحص ما إذا كان الاختبار وهمياً"""
        fake_patterns = self.forbidden_patterns['fake_test_patterns']
        for pattern in fake_patterns:
            if re.search(pattern, test_code, re.IGNORECASE):
                return True
        
        # فحص إضافي: اختبار يحتوي على assert واحد فقط وبسيط
        assert_count = len(re.findall(r'assert\s+', test_code))
        if assert_count == 1 and ('True' in test_code or '1 == 1' in test_code):
            return True
        
        return False
    
    def _is_weak_test(self, test_code: str) -> bool:
        """فحص ما إذا كان الاختبار ضعيفاً"""
        # اختبار ضعيف إذا كان:
        # 1. لا يحتوي على assertions كافية
        assert_count = len(re.findall(r'assert\s+', test_code))
        if assert_count < 2:
            return True
        
        # 2. يعتمد بشكل مفرط على mocks
        mock_count = len(re.findall(r'mock\.|Mock\(|patch\(', test_code))
        if mock_count > assert_count:
            return True
        
        # 3. لا يختبر حالات مختلفة
        if 'for' not in test_code and 'if' not in test_code and assert_count < 3:
            return True
        
        return False
    
    def _check_security_issues(self, code_blocks: List[str]) -> List[str]:
        """فحص المشاكل الأمنية في الكود"""
        security_issues = []
        
        for i, code in enumerate(code_blocks):
            # فحص كلمات المرور المكشوفة
            if re.search(r'password\s*=\s*[\'"][^\'"]+[\'"]', code, re.IGNORECASE):
                security_issues.append(f"كتلة الكود {i+1}: كلمة مرور مكشوفة في الكود")
            
            # فحص استخدام eval أو exec
            if re.search(r'\b(eval|exec)\s*\(', code):
                security_issues.append(f"كتلة الكود {i+1}: استخدام دوال خطيرة (eval/exec)")
            
            # فحص SQL injection محتمل
            if re.search(r'execute\s*\(\s*[\'"].*%.*[\'"]', code):
                security_issues.append(f"كتلة الكود {i+1}: احتمالية SQL injection")
            
            # فحص استيراد غير آمن
            if re.search(r'from\s+\*\s+import|import\s+\*', code):
                security_issues.append(f"كتلة الكود {i+1}: استيراد غير آمن (*)")
        
        return security_issues
    
    def generate_governance_prompt(self, original_prompt: str) -> str:
        """
        إنشاء prompt محكوم يضمن اتباع قواعد الحوكمة
        """
        governance_instructions = """
        
        === قواعد حوكمة الذكاء الاصطناعي الإجبارية ===
        
        يجب عليك الالتزام الصارم بالقواعد التالية:
        
        1. **لا تكتب أي كود بدون اختبارات شاملة**
           - كل دالة يجب أن تحتوي على اختبار واحد على الأقل
           - الاختبارات يجب أن تغطي الحالات العادية والاستثنائية
           - استخدم assertions حقيقية وليس assert True
        
        2. **لا تقدم اختبارات وهمية أو غير فعالة**
           - تجنب: assert True, assert 1==1, pass
           - تجنب: اختبارات تحتوي على TODO فقط
           - تجنب: الاعتماد المفرط على mocks بدون assertions حقيقية
        
        3. **اتبع معايير الأمان**
           - لا تستخدم eval() أو exec()
           - لا تكشف كلمات المرور في الكود
           - استخدم معالجة الأخطاء المناسبة
        
        4. **اتبع أفضل ممارسات البرمجة**
           - أضف docstrings للدوال والكلاسات
           - استخدم أسماء متغيرات واضحة
           - تجنب الكود المكرر
        
        5. **تنسيق الاستجابة**
           - ابدأ بشرح مختصر لما ستفعله
           - اكتب الكود الرئيسي أولاً
           - اكتب الاختبارات ثانياً
           - اختتم بتعليمات التشغيل
        
        إذا لم تتمكن من كتابة اختبارات شاملة، فلا تكتب الكود أصلاً.
        
        === الطلب الأصلي ===
        """
        
        return governance_instructions + original_prompt
    
    def validate_and_improve_response(self, response: str) -> Tuple[str, bool]:
        """
        التحقق من الاستجابة وتحسينها إذا لزم الأمر
        """
        analysis = self.analyze_ai_response(response)
        
        if analysis.is_approved:
            return response, True
        
        # إنشاء استجابة محسنة
        improved_response = self._generate_improved_response(response, analysis)
        
        return improved_response, False
    
    def _generate_improved_response(self, original_response: str, analysis: CodeAnalysisResult) -> str:
        """إنشاء استجابة محسنة بناءً على التحليل"""
        improvements = []
        
        improvements.append("⚠️ **تم رفض الاستجابة الأصلية لعدم اتباع قواعد الحوكمة**\n")
        
        if analysis.violations:
            improvements.append("**الانتهاكات المكتشفة:**")
            for violation in analysis.violations:
                improvements.append(f"- {violation}")
            improvements.append("")
        
        if analysis.suggestions:
            improvements.append("**التحسينات المطلوبة:**")
            for suggestion in analysis.suggestions:
                improvements.append(f"- {suggestion}")
            improvements.append("")
        
        improvements.append("**يرجى إعادة كتابة الكود مع مراعاة النقاط التالية:**")
        improvements.append("1. إضافة اختبارات شاملة لكل دالة")
        improvements.append("2. استخدام assertions حقيقية في الاختبارات")
        improvements.append("3. إضافة معالجة للأخطاء")
        improvements.append("4. إضافة توثيق مناسب")
        improvements.append("5. اتباع معايير الأمان")
        
        return "\n".join(improvements)


class AIPromptEnforcer:
    """
    نظام فرض قواعد الـ prompts للذكاء الاصطناعي
    """
    
    def __init__(self, code_governor: CodeGovernor):
        self.code_governor = code_governor
        
    def enforce_coding_standards(self, prompt: str, context: Dict[str, Any] = None) -> str:
        """فرض معايير البرمجة على الـ prompt"""
        
        # إضافة قواعد الحوكمة للـ prompt
        governed_prompt = self.code_governor.generate_governance_prompt(prompt)
        
        # إضافة سياق إضافي إذا لزم الأمر
        if context and context.get('project_type'):
            project_specific_rules = self._get_project_specific_rules(context['project_type'])
            governed_prompt += f"\n\n=== قواعد خاصة بمشروع {context['project_type']} ===\n{project_specific_rules}"
        
        return governed_prompt
    
    def _get_project_specific_rules(self, project_type: str) -> str:
        """الحصول على قواعد خاصة بنوع المشروع"""
        rules = {
            'django': """
            - استخدم Django ORM بدلاً من SQL مباشر
            - أضف اختبارات للـ models والـ views والـ serializers
            - استخدم Django's built-in authentication
            - اتبع Django's naming conventions
            """,
            'fastapi': """
            - استخدم Pydantic models للـ validation
            - أضف type hints لجميع الدوال
            - استخدم dependency injection
            - اكتب اختبارات للـ endpoints باستخدام TestClient
            """,
            'microservice': """
            - اتبع مبادئ الـ microservices
            - أضف health checks
            - استخدم logging مناسب
            - اكتب اختبارات للـ integration بين الخدمات
            """
        }
        
        return rules.get(project_type, "")


# مثال على الاستخدام
if __name__ == "__main__":
    # إنشاء نظام الحوكمة
    governor = CodeGovernor()
    enforcer = AIPromptEnforcer(governor)
    
    # مثال على استجابة ذكاء اصطناعي
    ai_response = """
    إليك دالة لحساب المجموع:
    
    ```python
    def calculate_sum(a, b):
        return a + b
    ```
    
    يمكنك استخدامها هكذا:
    ```python
    result = calculate_sum(5, 3)
    print(result)
    ```
    """
    
    # تحليل الاستجابة
    analysis = governor.analyze_ai_response(ai_response)
    print(f"جودة الكود: {analysis.code_quality.value}")
    print(f"جودة الاختبارات: {analysis.test_quality.value}")
    print(f"مقبول: {analysis.is_approved}")
    print(f"الانتهاكات: {analysis.violations}")
    print(f"الاقتراحات: {analysis.suggestions}")
