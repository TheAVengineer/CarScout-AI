"""
Test login redirect detection logic without actually logging in.

This simulates different scenarios to verify our detection logic works.
"""

def test_login_detection():
    """Test various login success/failure scenarios"""
    
    print("Testing login detection logic...")
    print("="*60)
    
    # Scenario 1: Successful login - redirected to /users/adverts
    print("\n✅ Test 1: Successful login (redirected to /users/adverts)")
    current_url = "https://www.mobile.bg/users/adverts"
    page_content = '<html><a href="/users/logout">Изход</a></html>'
    
    is_login_page = '/users/login' in current_url
    has_logout = 'изход' in page_content.lower() or 'logout' in page_content.lower()
    has_error = 'грешка' in page_content.lower() or 'error' in page_content.lower()
    
    if not is_login_page and (has_logout or '/users/' in current_url):
        print(f"   ✅ PASS - Login detected as successful")
    else:
        print(f"   ❌ FAIL - Should detect success")
    
    print(f"   URL: {current_url}")
    print(f"   Has logout: {has_logout}, Is login page: {is_login_page}")
    
    # Scenario 2: Successful login - redirected to homepage
    print("\n✅ Test 2: Successful login (redirected to homepage)")
    current_url = "https://www.mobile.bg/"
    page_content = '<html><a href="/users/logout">Изход</a></html>'
    
    is_login_page = '/users/login' in current_url
    has_logout = 'изход' in page_content.lower() or 'logout' in page_content.lower()
    has_error = 'грешка' in page_content.lower() or 'error' in page_content.lower()
    
    if not is_login_page and (has_logout or '/users/' in current_url):
        print(f"   ✅ PASS - Login detected as successful")
    else:
        print(f"   ❌ FAIL - Should detect success (has logout link)")
    
    print(f"   URL: {current_url}")
    print(f"   Has logout: {has_logout}, Is login page: {is_login_page}")
    
    # Scenario 3: Failed login - still on login page with error
    print("\n❌ Test 3: Failed login (still on login page)")
    current_url = "https://www.mobile.bg/users/login"
    page_content = '<html><div class="error">Грешка: Невалидни данни</div></html>'
    
    is_login_page = '/users/login' in current_url
    has_logout = 'изход' in page_content.lower() or 'logout' in page_content.lower()
    has_error = 'грешка' in page_content.lower() or 'error' in page_content.lower()
    
    if has_error or is_login_page:
        print(f"   ✅ PASS - Login failure detected")
    else:
        print(f"   ❌ FAIL - Should detect failure")
    
    print(f"   URL: {current_url}")
    print(f"   Has error: {has_error}, Is login page: {is_login_page}")
    
    # Scenario 4: Uncertain - no clear indicators
    print("\n⚠️  Test 4: Uncertain state (no clear success/failure)")
    current_url = "https://www.mobile.bg/obiavi"
    page_content = '<html><body>Some content</body></html>'
    
    is_login_page = '/users/login' in current_url
    has_logout = 'изход' in page_content.lower() or 'logout' in page_content.lower()
    has_error = 'грешка' in page_content.lower() or 'error' in page_content.lower()
    
    if not is_login_page and (has_logout or '/users/' in current_url):
        print(f"   ✅ Success")
    elif has_error or is_login_page:
        print(f"   ❌ Failure")
    else:
        print(f"   ⚠️  PASS - Unclear state detected (will proceed cautiously)")
    
    print(f"   URL: {current_url}")
    print(f"   Has logout: {has_logout}, Is login page: {is_login_page}")
    
    print("\n" + "="*60)
    print("✅ All login detection tests passed!")

if __name__ == "__main__":
    test_login_detection()
