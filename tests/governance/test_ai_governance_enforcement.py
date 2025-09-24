"""
اختبارات تنفيذ حوكمة الذكاء الاصطناعي
تتحقق من أن النظام يطبق القواعد بشكل صحيح
"""

import pytest
from unittest.mock import Mock, patch
from app.ai_governance.code_governor import (
    CodeGovernor, 
    AIPromptEnforcer,
    CodeQualityLevel,
    TestQualityLevel,
    AIGovernanceAnalysis
)


class TestCodeGovernorEnforcement:
    """اختبارات تنفيذ CodeGovernor"""
    
    def setup_method(self):
        """إعداد الاختبارات"""
        self.governor = CodeGovernor()
        self.enforcer = AIPromptEnforcer(self.governor)
    
    @pytest.mark.governance
    def test_blocks_code_without_tests(self):
        """يجب أن يرفض الكود بدون اختبارات"""
        code_without_tests = '''
def calculate_sum(a, b):
    """حساب مجموع رقمين"""
    return a + b

class Calculator:
    def multiply(self, a, b):
        return a * b
'''
        
        analysis = self.governor.analyze_ai_response(code_without_tests)
        
        assert not analysis.is_approved
        assert analysis.code_quality == CodeQualityLevel.BLOCKED
        assert "لا يحتوي على اختبارات" in str(analysis.violations)
    
    @pytest.mark.governance
    def test_blocks_fake_tests(self):
        """يجب أن يرفض الاختبارات الوهمية"""
        fake_tests = '''
def test_calculate_sum():
    """اختبار دالة الجمع"""
    assert True  # اختبار وهمي
    
def test_multiply():
    """اختبار دالة الضرب"""
    pass  # TODO: إضافة اختبار
'''
        
        analysis = self.governor.analyze_ai_response(fake_tests)
        
        assert not analysis.is_approved
        assert analysis.test_quality == TestQualityLevel.FAKE_TESTS
        assert any("وهمي" in violation for violation in analysis.violations)
    
    @pytest.mark.governance
    def test_approves_good_code_with_tests(self):
        """يجب أن يوافق على الكود الجيد مع الاختبارات"""
        good_code_with_tests = '''
def calculate_sum(a, b):
    """حساب مجموع رقمين"""
    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
        raise TypeError("المعاملات يجب أن تكون أرقام")
    return a + b

def test_calculate_sum():
    """اختبار دالة الجمع"""
    # اختبار الحالة العادية
    assert calculate_sum(2, 3) == 5
    assert calculate_sum(-1, 1) == 0
    assert calculate_sum(0.5, 0.5) == 1.0
    
    # اختبار الحالات الاستثنائية
    with pytest.raises(TypeError):
        calculate_sum("a", 2)
    
    with pytest.raises(TypeError):
        calculate_sum(2, None)
'''
        
        analysis = self.governor.analyze_ai_response(good_code_with_tests)
        
        assert analysis.is_approved
        assert analysis.code_quality in [CodeQualityLevel.GOOD, CodeQualityLevel.EXCELLENT]
        assert analysis.test_quality in [TestQualityLevel.GOOD, TestQualityLevel.EXCELLENT]
    
    @pytest.mark.governance
    def test_enforces_security_rules(self):
        """يجب أن يطبق القواعد الأمنية"""
        insecure_code = '''
def dangerous_function(user_input):
    """دالة خطيرة"""
    result = eval(user_input)  # خطر أمني
    return result

password = "123456"  # كلمة مرور مكشوفة
api_key = "sk-1234567890abcdef"  # مفتاح API مكشوف
'''
        
        analysis = self.governor.analyze_ai_response(insecure_code)
        
        assert not analysis.is_approved
        assert analysis.code_quality == CodeQualityLevel.BLOCKED
        assert any("أمني" in violation or "security" in violation.lower() 
                  for violation in analysis.violations)
    
    @pytest.mark.governance
    def test_prompt_enforcer_adds_governance_rules(self):
        """يجب أن يضيف AIPromptEnforcer قواعد الحوكمة للـ prompts"""
        original_prompt = "اكتب دالة لحساب المجموع"
        
        governed_prompt = self.enforcer.enforce_coding_standards(
            original_prompt, 
            context={"project_type": "django"}
        )
        
        # يجب أن يحتوي الـ prompt المحكوم على قواعد إضافية
        assert "اختبارات" in governed_prompt
        assert "assert" in governed_prompt
        assert "pytest" in governed_prompt or "unittest" in governed_prompt
        assert len(governed_prompt) > len(original_prompt)
    
    @pytest.mark.governance
    def test_calculates_coverage_estimate(self):
        """يجب أن يحسب تقدير التغطية بشكل صحيح"""
        code_with_partial_tests = '''
def function_a():
    return "a"

def function_b():
    return "b"

def function_c():
    return "c"

def test_function_a():
    assert function_a() == "a"

def test_function_b():
    assert function_b() == "b"
    
# function_c غير مُختبرة
'''
        
        analysis = self.governor.analyze_ai_response(code_with_partial_tests)
        
        # يجب أن تكون التغطية حوالي 67% (2 من 3 دوال مُختبرة)
        assert 0.6 <= analysis.coverage_estimate <= 0.8
    
    @pytest.mark.governance
    def test_handles_complex_code_structures(self):
        """يجب أن يتعامل مع هياكل الكود المعقدة"""
        complex_code = '''
class UserManager:
    """مدير المستخدمين"""
    
    def __init__(self, database):
        self.db = database
    
    def create_user(self, username, email):
        """إنشاء مستخدم جديد"""
        if not username or not email:
            raise ValueError("اسم المستخدم والإيميل مطلوبان")
        
        if self.db.user_exists(username):
            raise ValueError("المستخدم موجود بالفعل")
        
        return self.db.create_user(username, email)
    
    def delete_user(self, username):
        """حذف مستخدم"""
        if not self.db.user_exists(username):
            raise ValueError("المستخدم غير موجود")
        
        return self.db.delete_user(username)

class TestUserManager:
    """اختبارات مدير المستخدمين"""
    
    def setup_method(self):
        self.mock_db = Mock()
        self.user_manager = UserManager(self.mock_db)
    
    def test_create_user_success(self):
        """اختبار إنشاء مستخدم بنجاح"""
        self.mock_db.user_exists.return_value = False
        self.mock_db.create_user.return_value = {"id": 1, "username": "test"}
        
        result = self.user_manager.create_user("test", "test@example.com")
        
        assert result["username"] == "test"
        self.mock_db.create_user.assert_called_once_with("test", "test@example.com")
    
    def test_create_user_validation(self):
        """اختبار التحقق من صحة البيانات"""
        with pytest.raises(ValueError, match="اسم المستخدم والإيميل مطلوبان"):
            self.user_manager.create_user("", "test@example.com")
        
        with pytest.raises(ValueError, match="اسم المستخدم والإيميل مطلوبان"):
            self.user_manager.create_user("test", "")
    
    def test_create_user_already_exists(self):
        """اختبار إنشاء مستخدم موجود بالفعل"""
        self.mock_db.user_exists.return_value = True
        
        with pytest.raises(ValueError, match="المستخدم موجود بالفعل"):
            self.user_manager.create_user("existing", "test@example.com")
'''
        
        analysis = self.governor.analyze_ai_response(complex_code)
        
        assert analysis.is_approved
        assert analysis.has_code
        assert analysis.has_tests
        assert analysis.coverage_estimate > 0.8
        assert analysis.code_quality in [CodeQualityLevel.GOOD, CodeQualityLevel.EXCELLENT]


class TestAIGovernanceIntegration:
    """اختبارات تكامل نظام الحوكمة"""
    
    @pytest.mark.governance
    @pytest.mark.integration
    def test_end_to_end_governance_flow(self):
        """اختبار تدفق الحوكمة من البداية للنهاية"""
        governor = CodeGovernor()
        enforcer = AIPromptEnforcer(governor)
        
        # 1. إنشاء prompt محكوم
        original_prompt = "اكتب API endpoint لإنشاء مستخدم"
        governed_prompt = enforcer.enforce_coding_standards(original_prompt)
        
        # 2. محاكاة استجابة ذكاء اصطناعي جيدة
        ai_response = '''
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib.auth.models import User

@api_view(['POST'])
def create_user(request):
    """إنشاء مستخدم جديد"""
    username = request.data.get('username')
    email = request.data.get('email')
    
    if not username or not email:
        return Response(
            {'error': 'اسم المستخدم والإيميل مطلوبان'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if User.objects.filter(username=username).exists():
        return Response(
            {'error': 'المستخدم موجود بالفعل'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    user = User.objects.create_user(username=username, email=email)
    return Response(
        {'id': user.id, 'username': user.username}, 
        status=status.HTTP_201_CREATED
    )

# الاختبارات
import pytest
from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient

class TestCreateUserAPI(TestCase):
    """اختبارات API إنشاء المستخدم"""
    
    def setUp(self):
        self.client = APIClient()
    
    def test_create_user_success(self):
        """اختبار إنشاء مستخدم بنجاح"""
        data = {'username': 'testuser', 'email': 'test@example.com'}
        response = self.client.post('/api/users/', data)
        
        assert response.status_code == 201
        assert response.data['username'] == 'testuser'
        assert User.objects.filter(username='testuser').exists()
    
    def test_create_user_missing_data(self):
        """اختبار إنشاء مستخدم بدون بيانات"""
        response = self.client.post('/api/users/', {})
        
        assert response.status_code == 400
        assert 'error' in response.data
    
    def test_create_user_duplicate(self):
        """اختبار إنشاء مستخدم مكرر"""
        User.objects.create_user(username='existing', email='existing@example.com')
        
        data = {'username': 'existing', 'email': 'new@example.com'}
        response = self.client.post('/api/users/', data)
        
        assert response.status_code == 400
        assert 'موجود بالفعل' in response.data['error']
'''
        
        # 3. تحليل الاستجابة
        analysis = governor.analyze_ai_response(ai_response)
        
        # 4. التحقق من النتائج
        assert analysis.is_approved
        assert analysis.has_code
        assert analysis.has_tests
        assert analysis.coverage_estimate >= 0.8
        assert len(analysis.violations) == 0
    
    @pytest.mark.governance
    def test_governance_metrics_collection(self):
        """اختبار جمع مقاييس الحوكمة"""
        governor = CodeGovernor()
        
        # محاكاة عدة تحليلات
        test_codes = [
            "def good_function(): pass\ndef test_good_function(): assert True",
            "def bad_function(): eval('1+1')",  # كود سيء
            "def another_good(): return 1\ndef test_another(): assert another_good() == 1"
        ]
        
        results = []
        for code in test_codes:
            analysis = governor.analyze_ai_response(code)
            results.append(analysis)
        
        # التحقق من جمع المقاييس
        approved_count = sum(1 for r in results if r.is_approved)
        blocked_count = sum(1 for r in results if not r.is_approved)
        
        assert approved_count == 2
        assert blocked_count == 1
    
    @pytest.mark.governance
    @pytest.mark.slow
    def test_performance_under_load(self):
        """اختبار أداء النظام تحت الحمل"""
        governor = CodeGovernor()
        
        # محاكاة حمل متوسط
        test_code = '''
def sample_function(x):
    return x * 2

def test_sample_function():
    assert sample_function(5) == 10
'''
        
        import time
        start_time = time.time()
        
        # تشغيل 100 تحليل
        for _ in range(100):
            analysis = governor.analyze_ai_response(test_code)
            assert analysis.is_approved
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # يجب أن يكون الأداء معقول (أقل من 10 ثواني لـ 100 تحليل)
        assert total_time < 10.0
        
        # متوسط الوقت لكل تحليل يجب أن يكون أقل من 100ms
        avg_time = total_time / 100
        assert avg_time < 0.1
