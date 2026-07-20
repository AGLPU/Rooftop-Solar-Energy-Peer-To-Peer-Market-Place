# JWT Validation Analysis

## Overview

The system uses **JWT (JSON Web Token)** for stateless authentication without storing tokens in the database. Here's how it works:

## How JWT Validation Works (Current Implementation)

### 1. Token Creation Flow

```python
def _create_token(data: dict, expires_delta: timedelta) -> str:
    payload = data.copy()
    payload["exp"] = datetime.now(timezone.utc) + expires_delta    # Expiration time
    payload["iat"] = datetime.now(timezone.utc)                    # Issued at time
    payload["jti"] = str(uuid.uuid4())                             # Unique token ID
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)
```

**Token contains:**
- `sub` (subject): User ID
- `role`: User role (ADMIN, SELLER, BUYER)
- `type`: Token type (access or refresh)
- `exp`: Expiration timestamp (Unix time)
- `iat`: Issued-at timestamp (Unix time)
- `jti`: Unique token identifier (for revocation support)

### 2. Token Validation Flow

```python
def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    # Step 1: Decode and verify token signature
    payload = _decode_token(token)  # Cryptographically verified!
    
    # Step 2: Check token type
    if payload.get("type") != "access":
        raise HTTPException(401, "Invalid token type")
    
    # Step 3: Extract user ID
    user_id: Optional[str] = payload.get("sub")
    if user_id is None:
        raise HTTPException(401, "Token missing subject")
    
    # Step 4: Verify user still exists and is active
    user = db.query(User).filter(User.id == uuid.UUID(user_id)).first()
    if user is None or not user.is_active:
        raise HTTPException(401, "User not found or inactive")
    
    # Step 5: Check if token was issued BEFORE user logged out
    token_issued_at = datetime.fromtimestamp(payload.get("iat"), tz=timezone.utc)
    if user.last_logout_at and user.last_logout_at > token_issued_at:
        raise HTTPException(401, "Token has been invalidated. Please login again.")
    
    return user
```

## Key Security Mechanisms

### 1. Cryptographic Signature Verification

```
Token Structure: header.payload.signature
                 [base64].[base64].[hmac_sha256]
                 
Example:
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.
eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.
SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c
```

**How it works:**
1. Token creator signs payload with `settings.secret_key` (HMAC-SHA256)
2. Signature = HMAC-SHA256(header.payload, secret_key)
3. Token receiver verifies signature = HMAC-SHA256(header.payload, secret_key)
4. If someone tampersencoded with data, signature won't match
5. Verification fails → Exception thrown

**Guarantee:** Token data is unchanged (immutable proof)

### 2. Expiration Time Check

```python
payload["exp"] = datetime.now(timezone.utc) + expires_delta
# jwt.decode() automatically checks if datetime.now() > exp
# If expired → JWTError raised → 401 Unauthorized
```

**Default expiration:**
- Access token: 30 minutes
- Refresh token: 7 days

### 3. User Still Active Check

```python
user = db.query(User).filter(User.id == uuid.UUID(user_id)).first()
if user is None or not user.is_active:
    raise HTTPException(401, "User not found or inactive")
```

**Prevents:**
- Deleted accounts using old tokens
- Disabled accounts using tokens
- Admin deactivating user mid-session

### 4. Token Revocation (Logout)

```python
# On logout, update user.last_logout_at
user.last_logout_at = datetime.utcnow()
db.commit()

# On any request with that token:
token_issued_at = datetime.fromtimestamp(payload.get("iat"), tz=timezone.utc)
if user.last_logout_at and user.last_logout_at > token_issued_at:
    # Token was issued BEFORE logout → INVALID
    raise HTTPException(401, "Token has been invalidated.")
```

**How it works:**
- Old tokens: `iat` = 10:00, `last_logout_at` = 10:05 → INVALID (issued before logout)
- New tokens: `iat` = 10:06, `last_logout_at` = 10:05 → VALID (issued after logout)

## Why NOT Store Tokens in Database?

### Stateless JWT Approach (Current)

**Pros:**
- ✓ Scalable (no session state to sync across servers)
- ✓ Fast (no DB query to validate token)
- ✓ Distributed-friendly (Render can scale horizontally)
- ✓ No session storage overhead
- ✓ Cryptographic guarantee of token integrity

**Cons:**
- ✗ Cannot instantly revoke specific tokens (only user logout)
- ✗ Revoked tokens are still valid until expiration
- ✗ If secret key is compromised, all tokens are compromised

### Traditional Stored Sessions Approach

**Would require:**
```python
# Pseudocode - NOT implemented
token_store = {
    "jti_uuid": {
        "user_id": "...",
        "created_at": "...",
        "revoked": False,  # Track revocation per token
        "expires_at": "..."
    }
}

# On every request: SELECT * FROM token_store WHERE jti = ?
# Slower, less scalable, but allows instant revocation
```

## Security Strengths

| Feature | How Enforced | Strength |
|---------|--------------|----------|
| Token Tampering | HMAC-SHA256 signature | Cryptographic guarantee |
| Expiration | JWT `exp` claim | Automatic expiration |
| Token Revocation | `user.last_logout_at` comparison | Time-based (good for logout) |
| User Deactivation | DB user query | Can deactivate mid-session |
| Role Verification | Claims in token + DB verification | Dual validation |
| Token Type | `type` claim check | Prevents token type confusion |

## Potential Vulnerabilities & Mitigations

### 1. Secret Key Compromise

**Risk:** If `settings.secret_key` is leaked, attacker can forge any token

**Mitigation:**
- [ ] Keep secret key in environment variables (done)
- [ ] Rotate secret key periodically
- [ ] Use strong secret key (>256 bits)
- [ ] Don't commit key to git (done)
- [ ] Use Render secrets feature for production

**Check current key:**
```bash
# In .env
SECRET_KEY=<must be 32+ characters>
```

### 2. Token Theft (Interception)

**Risk:** HTTPS-in-transit capture, XSS attacks stealing token from localStorage

**Mitigation:**
- ✓ Always use HTTPS (required)
- [ ] Store token in HTTP-only cookie (not localStorage)
  - Currently: Frontend likely stores in localStorage
  - Recommended: HTTP-only + Secure cookies
  
### 3. Long-Lived Refresh Tokens

**Risk:** If refresh token is stolen, attacker can get new access tokens forever (7 days)

**Mitigation:**
- [ ] Implement refresh token rotation
- [ ] Store refresh token hashes in DB (not plaintext)
- [ ] Detect reuse patterns (rotating token invalidates old ones)
- [ ] Shorter refresh token expiry

### 4. Race Condition on Logout

**Risk:** Multiple requests with same token during logout window

**Example:**
```
10:00 - User has token
10:05 - User clicks logout, sets last_logout_at = 10:05
10:05 - In-flight request still has old token
       Check: iat=10:00 < last_logout_at=10:05 → REJECT (good)
10:06 - Attacker tries old token
       Check: iat=10:00 < last_logout_at=10:05 → REJECT (good)
```

**Verdict:** ✓ Safe (logout takes effect immediately for new requests)

### 5. Stolen Tokens Still Valid Until Expiration

**Scenario:**
```
10:00 - Attacker steals user's token (iat=10:00, exp=10:30)
10:05 - Token is stolen
10:06 - User tries to logout, sets last_logout_at=10:06
10:07 - Attacker uses stolen token (iat=10:00 < last_logout_at=10:06)
        → REJECTED (good!)
        
BUT: Immediate window (10:05-10:06):
10:05 - Token is stolen  
10:05:30 - Attacker immediately uses token (before logout)
          Logout hasn't happened yet → VALID
          Window of ~30-60 seconds where stolen token works
```

**Mitigation:**
- [ ] Shorter access token lifetime (15-20 minutes instead of 30)
- [ ] Implement token blacklist for stolen tokens
- [ ] Monitor unusual activity patterns
- [ ] Implement rate limiting per user

## Comparison: JWT vs Database Tokens

| Aspect | JWT (Current) | DB Tokens |
|--------|---------------|-----------|
| Scalability | High (stateless) | Low (DB queries) |
| Revocation Speed | Minutes (refresh) | Instant |
| DB Queries per Request | 1 (user check) | 2 (user + token) |
| Token Forgery Protection | Signature | Hash + DB |
| Instant User Deactivation | ✓ Yes | ✓ Yes |
| Instant Token Revocation | ✗ No (until logout) | ✓ Yes |
| Session Sync Complexity | None | High (cache invalidation) |
| Infrastructure Dependency | None | Redis/DB required |

## Recommended Security Improvements

### Priority 1 (Critical)

1. **Verify secret key strength**
   ```bash
   # Check that SECRET_KEY is 32+ characters of random data
   # NOT hardcoded DEFAULT_KEY
   ```

2. **Implement HTTPS-only cookies**
   ```python
   # Instead of localStorage (vulnerable to XSS)
   response.set_cookie(
       "access_token",
       token,
       httponly=True,      # Can't access from JS
       secure=True,        # Only over HTTPS
       samesite="strict",  # CSRF protection
       max_age=1800        # 30 minutes
   )
   ```

3. **Add login/logout audit logging**
   ```python
   # Log all auth events with timestamp, IP, user agent
   AuditService.log_event(
       event_type=AuditEventType.USER_LOGIN,
       user_id=user.id,
       details={"ip": request.client.host, "user_agent": request.headers.get("user-agent")}
   )
   ```

### Priority 2 (High)

4. **Implement refresh token rotation**
   ```python
   # Old refresh token becomes invalid when used
   # Issue new refresh token with each use
   # Track issued refresh tokens to detect reuse/theft
   ```

5. **Reduce access token expiry**
   - Current: 30 minutes
   - Recommended: 15 minutes

6. **Add rate limiting on login**
   ```python
   # Max 5 login attempts per IP per hour
   # Prevents brute force attacks
   ```

### Priority 3 (Medium)

7. **Implement token blacklist**
   ```python
   # For sensitive operations, add token to blacklist
   # Check blacklist before accepting request
   # Clear blacklist after token expiration
   ```

8. **Monitor token reuse patterns**
   ```python
   # Detect if same token used from multiple IPs
   # Detect if token used after logout
   # Alert on suspicious patterns
   ```

## Implementation Example: Enhanced Token Validation

```python
def get_current_user_enhanced(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
    request: Request = Depends(),
) -> User:
    # Existing checks
    payload = _decode_token(token)
    user = validate_user(payload, db)
    
    # NEW: Check token blacklist
    jti = payload.get("jti")
    if is_token_blacklisted(db, jti):
        raise HTTPException(401, "Token has been revoked")
    
    # NEW: Detect unusual activity
    client_ip = request.client.host
    if is_suspicious_login(db, user.id, client_ip):
        # Track for investigation
        log_suspicious_activity(db, user.id, client_ip)
    
    # NEW: Check concurrent device limit
    if too_many_concurrent_devices(db, user.id):
        # Revoke oldest token
        revoke_oldest_token(db, user.id)
    
    return user
```

## Deployment Checklist

- [ ] Verify `SECRET_KEY` is NOT default value
- [ ] Verify `SECRET_KEY` length >= 32 characters
- [ ] Verify `ALGORITHM` = "HS256" (HMAC-SHA256)
- [ ] Verify `ACCESS_TOKEN_EXPIRE_MINUTES` is set (recommend 15-30)
- [ ] Verify `REFRESH_TOKEN_EXPIRE_DAYS` is set (recommend 7)
- [ ] HTTPS enabled on production
- [ ] Audit logging for login/logout
- [ ] Rate limiting on login endpoint
- [ ] Monitor failed login attempts
- [ ] User logout functionality tested

## Security Posture

**Current:** 
- Base JWT validation: ✓ Secure
- Token expiration: ✓ Secure
- User active check: ✓ Secure
- Token revocation: ⚠ Basic (logout only)
- Token storage: ⚠ Unclear (likely localStorage - vulnerable to XSS)
- Secret key management: ⚠ Needs verification

**Rating:** 6/10 - Solid base, needs hardening for production

## References

- JWT Spec: https://tools.ietf.org/html/rfc7519
- OWASP Token Security: https://owasp.org/www-community/attacks/jwt
- PyJWT Library: https://pyjwt.readthedocs.io/
- OAuth2 Security: https://owasp.org/www-project-oauth-2-0-security-best-practices/
