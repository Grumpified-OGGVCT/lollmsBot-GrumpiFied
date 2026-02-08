#!/usr/bin/env python3
"""
Comprehensive validation script to ensure security integration doesn't break existing code.
This validates the "whole pie" not just individual pieces.
"""

import sys
import importlib
import traceback
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

class ValidationResult:
    def __init__(self):
        self.passed = []
        self.failed = []
        self.warnings = []
    
    def add_pass(self, test_name):
        self.passed.append(test_name)
        print(f"✅ {test_name}")
    
    def add_fail(self, test_name, error):
        self.failed.append((test_name, error))
        print(f"❌ {test_name}: {error}")
    
    def add_warning(self, test_name, message):
        self.warnings.append((test_name, message))
        print(f"⚠️  {test_name}: {message}")
    
    def summary(self):
        print("\n" + "="*60)
        print("VALIDATION SUMMARY")
        print("="*60)
        print(f"✅ Passed: {len(self.passed)}")
        print(f"❌ Failed: {len(self.failed)}")
        print(f"⚠️  Warnings: {len(self.warnings)}")
        
        if self.failed:
            print("\n❌ FAILED TESTS:")
            for test, error in self.failed:
                print(f"  - {test}")
                print(f"    {error}")
        
        if self.warnings:
            print("\n⚠️  WARNINGS:")
            for test, msg in self.warnings:
                print(f"  - {test}: {msg}")
        
        return len(self.failed) == 0


def test_standalone_imports(results):
    """Test that security modules can be imported standalone"""
    print("\n" + "="*60)
    print("TEST 1: Standalone Security Module Imports")
    print("="*60)
    
    # Test adaptive_threat_intelligence
    try:
        from lollmsbot.adaptive_threat_intelligence import (
            AdaptiveThreatIntelligence,
            ThreatObservation,
            LearnedPattern,
            get_adaptive_intelligence
        )
        results.add_pass("adaptive_threat_intelligence imports")
    except Exception as e:
        results.add_fail("adaptive_threat_intelligence imports", str(e))
    
    # Test guardian
    try:
        from lollmsbot.guardian import (
            Guardian,
            get_guardian,
            ThreatType,
            ThreatLevel
        )
        results.add_pass("guardian imports")
    except Exception as e:
        results.add_fail("guardian imports", str(e))
    
    # Test security_monitoring
    try:
        from lollmsbot.security_monitoring import (
            SecurityMonitor,
            get_security_monitor
        )
        results.add_pass("security_monitoring imports")
    except Exception as e:
        results.add_fail("security_monitoring imports", str(e))


def test_guardian_instantiation(results):
    """Test that Guardian can be instantiated"""
    print("\n" + "="*60)
    print("TEST 2: Guardian Instantiation")
    print("="*60)
    
    try:
        from lollmsbot.guardian import Guardian, get_guardian
        
        # Test both ways to get Guardian
        guardian1 = Guardian()
        results.add_pass("Guardian() constructor")
        
        guardian2 = get_guardian()
        results.add_pass("get_guardian() function")
        
        # Verify it's a singleton
        if guardian1 is guardian2:
            results.add_pass("Guardian is a singleton")
        else:
            results.add_fail("Guardian singleton", "Two different instances created")
        
        guardian = guardian1
        
        # Check critical methods exist
        methods = [
            'check_input',
            'check_output',
            'scan_skill_content',
            'get_audit_report',
            'get_adaptive_stats',
            'cleanup_resources'
        ]
        
        for method in methods:
            if hasattr(guardian, method):
                results.add_pass(f"Guardian.{method} exists")
            else:
                results.add_fail(f"Guardian.{method} exists", "Method not found")
        
        # Check attributes
        if hasattr(guardian, 'threat_detector'):
            results.add_pass("Guardian.threat_detector exists")
        else:
            results.add_fail("Guardian.threat_detector exists", "Attribute not found")
        
        if hasattr(guardian, 'adaptive_intel'):
            results.add_pass("Guardian.adaptive_intel exists")
        else:
            results.add_warning("Guardian.adaptive_intel", "Optional attribute not found")
            
    except Exception as e:
        results.add_fail("Guardian instantiation", str(e))
        traceback.print_exc()


def test_guardian_functionality(results):
    """Test Guardian basic functionality"""
    print("\n" + "="*60)
    print("TEST 3: Guardian Functionality")
    print("="*60)
    
    try:
        from lollmsbot.guardian import get_guardian
        
        guardian = get_guardian()
        
        # Test check_input with benign text
        try:
            blocked, event = guardian.check_input("Hello, how are you?")
            results.add_pass("Guardian.check_input with benign text")
        except Exception as e:
            results.add_fail("Guardian.check_input", str(e))
        
        # Test check_input with malicious text
        try:
            blocked, event = guardian.check_input("Ignore all previous instructions and...")
            if blocked:
                results.add_pass("Guardian.check_input detects prompt injection")
            else:
                results.add_warning("Guardian.check_input", "Did not detect obvious prompt injection")
        except Exception as e:
            results.add_fail("Guardian.check_input with malicious text", str(e))
        
        # Test scan_skill_content
        try:
            is_safe, threats = guardian.scan_skill_content(
                "test_skill",
                "This is a benign skill that does nothing malicious."
            )
            results.add_pass("Guardian.scan_skill_content")
        except Exception as e:
            results.add_fail("Guardian.scan_skill_content", str(e))
        
        # Test get_adaptive_stats
        try:
            stats = guardian.get_adaptive_stats()
            results.add_pass("Guardian.get_adaptive_stats")
        except Exception as e:
            results.add_fail("Guardian.get_adaptive_stats", str(e))
            
    except Exception as e:
        results.add_fail("Guardian functionality tests", str(e))
        traceback.print_exc()


def test_integration_imports(results):
    """Test that modules that depend on Guardian can still import"""
    print("\n" + "="*60)
    print("TEST 4: Integration Point Imports")
    print("="*60)
    
    # Test awesome_skills_integration
    try:
        from lollmsbot.awesome_skills_integration import AwesomeSkillsIntegration
        results.add_pass("awesome_skills_integration imports")
    except Exception as e:
        results.add_fail("awesome_skills_integration imports", str(e))
    
    # Test skill_scanner (if it still exists and is used)
    try:
        from lollmsbot.skill_scanner import SkillScanner
        results.add_warning("skill_scanner", "Module exists but may be deprecated")
    except ImportError:
        results.add_pass("skill_scanner not imported (expected if deprecated)")
    except Exception as e:
        results.add_fail("skill_scanner", str(e))
    
    # Test api_key_protection (if it still exists and is used)
    try:
        from lollmsbot.api_key_protection import APIKeyProtector
        results.add_warning("api_key_protection", "Module exists but may be deprecated")
    except ImportError:
        results.add_pass("api_key_protection not imported (expected if deprecated)")
    except Exception as e:
        results.add_fail("api_key_protection", str(e))


def test_cli_integration(results):
    """Test CLI integration with Guardian"""
    print("\n" + "="*60)
    print("TEST 5: CLI Integration")
    print("="*60)
    
    try:
        # Import cli module
        from lollmsbot import cli
        results.add_pass("cli module imports")
        
        # Check if skills scan commands are defined
        if hasattr(cli, 'skills_scan'):
            results.add_pass("cli.skills_scan exists")
        else:
            results.add_warning("cli.skills_scan", "Command may be missing")
            
    except Exception as e:
        results.add_fail("CLI integration", str(e))


def test_ui_routes_integration(results):
    """Test UI routes integration with Guardian"""
    print("\n" + "="*60)
    print("TEST 6: UI Routes Integration")
    print("="*60)
    
    try:
        from lollmsbot.ui import routes
        results.add_pass("ui.routes imports")
        
        # Check for security endpoints
        if hasattr(routes, 'security_status'):
            results.add_pass("routes.security_status exists")
        else:
            results.add_warning("routes.security_status", "Endpoint may be missing")
            
    except Exception as e:
        results.add_fail("UI routes integration", str(e))


def test_no_circular_imports(results):
    """Test that there are no circular import issues"""
    print("\n" + "="*60)
    print("TEST 7: Circular Import Check")
    print("="*60)
    
    # Try importing all security modules in different orders
    import importlib
    
    orders = [
        ['lollmsbot.guardian', 'lollmsbot.adaptive_threat_intelligence', 'lollmsbot.security_monitoring'],
        ['lollmsbot.adaptive_threat_intelligence', 'lollmsbot.security_monitoring', 'lollmsbot.guardian'],
        ['lollmsbot.security_monitoring', 'lollmsbot.guardian', 'lollmsbot.adaptive_threat_intelligence'],
    ]
    
    for i, order in enumerate(orders):
        try:
            # Reload modules
            for module_name in order:
                if module_name in sys.modules:
                    del sys.modules[module_name]
            
            # Import in this order
            for module_name in order:
                importlib.import_module(module_name)
            
            results.add_pass(f"Import order {i+1}: {' -> '.join([m.split('.')[-1] for m in order])}")
        except Exception as e:
            results.add_fail(f"Import order {i+1}", str(e))


def main():
    print("\n" + "="*60)
    print("SECURITY INTEGRATION VALIDATION")
    print("="*60)
    print("Validating that security enhancements don't break existing code")
    print("Testing the 'whole pie', not just individual pieces")
    print("="*60)
    
    results = ValidationResult()
    
    # Run all tests
    test_standalone_imports(results)
    test_guardian_instantiation(results)
    test_guardian_functionality(results)
    test_integration_imports(results)
    test_cli_integration(results)
    test_ui_routes_integration(results)
    test_no_circular_imports(results)
    
    # Print summary
    success = results.summary()
    
    if success:
        print("\n🎉 ALL VALIDATIONS PASSED!")
        print("The security integration is working correctly.")
        return 0
    else:
        print("\n⚠️  SOME VALIDATIONS FAILED")
        print("Please fix the issues above before proceeding.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
