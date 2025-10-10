# User System Architecture
## Authentication, Authorization, Ownership & Privacy

**Created:** October 2025
**Status:** Design Proposal
**Philosophy:** Local-first, privacy-respecting, scalable to multi-user

---

## Executive Summary

**Current State:**
- ✅ User model exists (`users` table)
- ✅ All entities have `user_id` foreign keys (ownership infrastructure ready)
- ✅ Anonymous users supported (`is_anonymous` flag)
- ⚠️ No authentication system
- ⚠️ No avatars
- ⚠️ No authorization/privacy controls

**Proposed Additions:**
1. **Avatar system** (deterministic generation + optional upload)
2. **Authentication** (password-based + OAuth ready)
3. **Authorization** (role-based access control)
4. **Privacy controls** (private/shared/public)

**Migration Path:**
- **Phase 1 (Today):** Add missing columns, create default user
- **Phase 2 (MVP):** Single-user mode with avatar
- **Phase 3 (Multi-user):** Authentication + privacy
- **Phase 4 (Future):** Sharing, teams, public links

---

## Current Database Schema

### Users Table (Existing)

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE,
    username VARCHAR(100),
    is_anonymous BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    preferences JSONB DEFAULT '{}'
);
```

**Foreign Key Coverage:** ✅ Complete
- agent_conversations.user_id
- belief_frameworks.user_id
- belief_patterns.user_id
- books.user_id
- chunks.user_id
- collections.user_id
- media.user_id
- messages.user_id
- semantic_regions.user_id
- sessions.user_id
- transformation_jobs.user_id
- transformations.user_id

All with `ON DELETE CASCADE` (ownership enforced at DB level).

---

## Proposed Enhancements

### 1. Avatar System

**Philosophy:** Deterministic generation for privacy, optional upload for personalization.

#### Database Changes

```sql
-- Migration: Add avatar columns to users table
ALTER TABLE users ADD COLUMN avatar_url VARCHAR(500);
ALTER TABLE users ADD COLUMN avatar_seed VARCHAR(100);
ALTER TABLE users ADD COLUMN avatar_provider VARCHAR(20) DEFAULT 'dicebear';
```

**Columns:**
- `avatar_url` - Full URL to avatar image (S3/R2 for uploads, null for generated)
- `avatar_seed` - Seed for deterministic generation (user_id or email hash)
- `avatar_provider` - 'dicebear', 'gravatar', 'upload', 'identicon'

#### Implementation

**Option 1: DiceBear (Recommended for MVP)**
```python
def get_avatar_url(user: User) -> str:
    """Generate deterministic avatar URL."""
    if user.avatar_url:
        return user.avatar_url

    seed = user.avatar_seed or str(user.id)
    style = 'avataaars'  # or 'bottts', 'identicon', etc.
    return f"https://api.dicebear.com/7.x/{style}/svg?seed={seed}"
```

**Pros:**
- No storage needed
- Deterministic (same seed = same avatar)
- No privacy leaks (no email hashing service)
- Many styles available

**Cons:**
- External dependency (can self-host if needed)

**Option 2: Gravatar**
```python
import hashlib

def get_avatar_url(user: User) -> str:
    if user.avatar_url:
        return user.avatar_url

    if user.email:
        email_hash = hashlib.md5(user.email.lower().encode()).hexdigest()
        return f"https://www.gravatar.com/avatar/{email_hash}?d=identicon"

    # Fallback to DiceBear for anonymous users
    return f"https://api.dicebear.com/7.x/identicon/svg?seed={user.id}"
```

**Pros:**
- Familiar to users
- Works across sites

**Cons:**
- Privacy concern (email → MD5, can be rainbow-tabled)
- Requires email

**Option 3: Cloudflare R2 Upload (Future)**
```python
async def upload_avatar(user_id: UUID, file: UploadFile) -> str:
    """Upload custom avatar to R2."""
    # Validate image (size, format)
    # Resize to 256x256
    # Upload to R2: avatars/{user_id}.jpg
    # Return public URL
    return f"https://assets.humanizer.com/avatars/{user_id}.jpg"
```

**Pros:**
- Full customization
- User choice

**Cons:**
- Storage costs (minimal with R2)
- Moderation concerns (if public)

**Recommendation for MVP:**
- Default: DiceBear with `seed=user_id`
- Future: Add upload option

---

### 2. Authentication System

**Philosophy:** Start simple (password), scale to OAuth, future passkeys.

#### Database Changes

```sql
-- Migration: Add authentication columns
ALTER TABLE users ADD COLUMN password_hash VARCHAR(255);
ALTER TABLE users ADD COLUMN oauth_provider VARCHAR(50);  -- 'github', 'google', null
ALTER TABLE users ADD COLUMN oauth_id VARCHAR(255);       -- Provider's user ID
ALTER TABLE users ADD COLUMN email_verified BOOLEAN DEFAULT false;
ALTER TABLE users ADD COLUMN last_login_at TIMESTAMPTZ;

-- Unique constraint for OAuth
CREATE UNIQUE INDEX users_oauth_provider_id_key
    ON users (oauth_provider, oauth_id)
    WHERE oauth_provider IS NOT NULL;
```

#### Implementation

**Password-Based (MVP)**

```python
# backend/services/auth_service.py
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    @staticmethod
    def hash_password(password: str) -> str:
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain: str, hashed: str) -> bool:
        return pwd_context.verify(plain, hashed)

    @staticmethod
    async def create_user(
        db: AsyncSession,
        email: str,
        password: str,
        username: str
    ) -> User:
        """Create authenticated user."""
        user = User(
            email=email.lower(),
            username=username,
            password_hash=AuthService.hash_password(password),
            is_anonymous=False,
            avatar_seed=email.lower()  # For deterministic avatar
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def authenticate(
        db: AsyncSession,
        email: str,
        password: str
    ) -> Optional[User]:
        """Authenticate user by email/password."""
        result = await db.execute(
            select(User).where(User.email == email.lower())
        )
        user = result.scalar_one_or_none()

        if not user or not user.password_hash:
            return None

        if not AuthService.verify_password(password, user.password_hash):
            return None

        user.last_login_at = datetime.utcnow()
        await db.commit()
        return user
```

**JWT Tokens**

```python
# backend/services/jwt_service.py
from datetime import datetime, timedelta
from jose import JWTError, jwt
from typing import Optional

SECRET_KEY = os.getenv("JWT_SECRET_KEY")  # Generate: openssl rand -hex 32
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

class JWTService:
    @staticmethod
    def create_access_token(user_id: UUID) -> str:
        """Create JWT access token."""
        expires = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode = {
            "sub": str(user_id),
            "exp": expires
        }
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    @staticmethod
    def decode_token(token: str) -> Optional[UUID]:
        """Decode JWT and return user_id."""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id = payload.get("sub")
            return UUID(user_id) if user_id else None
        except JWTError:
            return None
```

**API Endpoints**

```python
# backend/api/auth_routes.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

router = APIRouter(prefix="/api/auth", tags=["auth"])
security = HTTPBearer()

class RegisterRequest(BaseModel):
    email: str
    password: str
    username: str

class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict

@router.post("/register", response_model=TokenResponse)
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    """Register new user."""
    # Check if email exists
    existing = await db.execute(
        select(User).where(User.email == request.email.lower())
    )
    if existing.scalar_one_or_none():
        raise HTTPException(400, "Email already registered")

    # Create user
    user = await AuthService.create_user(
        db, request.email, request.password, request.username
    )

    # Generate token
    token = JWTService.create_access_token(user.id)

    return {
        "access_token": token,
        "user": user.to_dict()
    }

@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """Login existing user."""
    user = await AuthService.authenticate(db, request.email, request.password)
    if not user:
        raise HTTPException(401, "Invalid credentials")

    token = JWTService.create_access_token(user.id)

    return {
        "access_token": token,
        "user": user.to_dict()
    }

@router.get("/me")
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """Get current user from token."""
    user_id = JWTService.decode_token(credentials.credentials)
    if not user_id:
        raise HTTPException(401, "Invalid token")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(401, "User not found")

    return user.to_dict()
```

**OAuth (Future - Phase 3)**

```python
# backend/api/oauth_routes.py
from authlib.integrations.starlette_client import OAuth

oauth = OAuth()
oauth.register(
    name='github',
    client_id=os.getenv('GITHUB_CLIENT_ID'),
    client_secret=os.getenv('GITHUB_CLIENT_SECRET'),
    authorize_url='https://github.com/login/oauth/authorize',
    access_token_url='https://github.com/login/oauth/access_token',
    api_base_url='https://api.github.com/',
    client_kwargs={'scope': 'user:email'},
)

@router.get("/oauth/github")
async def github_login(request: Request):
    """Initiate GitHub OAuth flow."""
    redirect_uri = request.url_for('github_callback')
    return await oauth.github.authorize_redirect(request, redirect_uri)

@router.get("/oauth/github/callback")
async def github_callback(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """GitHub OAuth callback."""
    token = await oauth.github.authorize_access_token(request)
    user_data = await oauth.github.get('user', token=token)

    # Get or create user
    github_id = str(user_data['id'])
    result = await db.execute(
        select(User).where(
            User.oauth_provider == 'github',
            User.oauth_id == github_id
        )
    )
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            email=user_data.get('email'),
            username=user_data['login'],
            oauth_provider='github',
            oauth_id=github_id,
            is_anonymous=False,
            avatar_url=user_data.get('avatar_url'),
            avatar_seed=user_data['login']
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    # Generate JWT
    access_token = JWTService.create_access_token(user.id)

    # Redirect to frontend with token
    return RedirectResponse(
        url=f"http://localhost:3000/auth/callback?token={access_token}"
    )
```

---

### 3. Authorization & Roles

**Philosophy:** Simple RBAC for MVP, extensible to teams later.

#### Database Changes

```sql
-- Migration: Add role column
ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'user';

-- Create enum constraint
ALTER TABLE users ADD CONSTRAINT users_role_check
    CHECK (role IN ('user', 'admin'));
```

#### Implementation

```python
# backend/models/db_models.py
from enum import Enum

class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"

class User(Base):
    # ... existing fields ...
    role = Column(String(20), default=UserRole.USER)

    def is_admin(self) -> bool:
        return self.role == UserRole.ADMIN

# backend/api/dependencies.py
from fastapi import Depends, HTTPException

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current authenticated user."""
    user_id = JWTService.decode_token(credentials.credentials)
    if not user_id:
        raise HTTPException(401, "Invalid token")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(401, "User not found")

    return user

async def require_admin(
    user: User = Depends(get_current_user)
) -> User:
    """Require admin role."""
    if not user.is_admin():
        raise HTTPException(403, "Admin access required")
    return user

# Usage in routes
@router.delete("/api/users/{user_id}")
async def delete_user(
    user_id: UUID,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Admin-only: Delete any user."""
    # ... delete logic ...
```

---

### 4. Privacy & Ownership Controls

**Philosophy:** Everything private by default, opt-in sharing.

#### Database Changes

```sql
-- Migration: Add privacy levels to shareable entities
-- Example: books table
ALTER TABLE books ADD COLUMN privacy VARCHAR(20) DEFAULT 'private';
ALTER TABLE books ADD CONSTRAINT books_privacy_check
    CHECK (privacy IN ('private', 'shared', 'public'));

-- Shared access table (for "shared" privacy level)
CREATE TABLE shared_access (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    resource_type VARCHAR(50) NOT NULL,  -- 'book', 'collection', etc.
    resource_id UUID NOT NULL,
    owner_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    shared_with_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    permission VARCHAR(20) DEFAULT 'view',  -- 'view', 'edit'
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(resource_type, resource_id, shared_with_user_id)
);

CREATE INDEX shared_access_user_idx ON shared_access(shared_with_user_id);
CREATE INDEX shared_access_resource_idx ON shared_access(resource_type, resource_id);

-- Public links table (for "public" privacy level)
CREATE TABLE public_links (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    resource_type VARCHAR(50) NOT NULL,
    resource_id UUID NOT NULL,
    owner_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    slug VARCHAR(100) UNIQUE NOT NULL,  -- Short readable identifier
    expires_at TIMESTAMPTZ,              -- Optional expiration
    view_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(resource_type, resource_id)
);

CREATE INDEX public_links_slug_idx ON public_links(slug);
```

#### Implementation

```python
# backend/models/privacy.py
from enum import Enum

class PrivacyLevel(str, Enum):
    PRIVATE = "private"   # Owner only
    SHARED = "shared"     # Owner + specific users
    PUBLIC = "public"     # Anyone with link

class Permission(str, Enum):
    VIEW = "view"
    EDIT = "edit"

# backend/services/privacy_service.py
class PrivacyService:
    @staticmethod
    async def can_access(
        db: AsyncSession,
        user_id: UUID,
        resource_type: str,
        resource_id: UUID,
        required_permission: Permission = Permission.VIEW
    ) -> bool:
        """Check if user can access resource."""

        # Get resource (example: book)
        result = await db.execute(
            select(Book).where(Book.id == resource_id)
        )
        resource = result.scalar_one_or_none()
        if not resource:
            return False

        # Owner always has access
        if resource.user_id == user_id:
            return True

        # Public resources: view-only access
        if resource.privacy == PrivacyLevel.PUBLIC:
            return required_permission == Permission.VIEW

        # Shared resources: check shared_access table
        if resource.privacy == PrivacyLevel.SHARED:
            result = await db.execute(
                select(SharedAccess).where(
                    SharedAccess.resource_type == resource_type,
                    SharedAccess.resource_id == resource_id,
                    SharedAccess.shared_with_user_id == user_id
                )
            )
            access = result.scalar_one_or_none()
            if not access:
                return False

            # Check permission level
            if required_permission == Permission.EDIT:
                return access.permission == Permission.EDIT
            return True

        # Private: no access
        return False

    @staticmethod
    async def share_resource(
        db: AsyncSession,
        owner_id: UUID,
        resource_type: str,
        resource_id: UUID,
        share_with_user_id: UUID,
        permission: Permission = Permission.VIEW
    ):
        """Share resource with another user."""
        # Verify ownership
        # ... (check owner_id matches resource.user_id)

        # Create or update shared_access
        access = SharedAccess(
            resource_type=resource_type,
            resource_id=resource_id,
            owner_id=owner_id,
            shared_with_user_id=share_with_user_id,
            permission=permission
        )
        db.add(access)
        await db.commit()

    @staticmethod
    async def create_public_link(
        db: AsyncSession,
        owner_id: UUID,
        resource_type: str,
        resource_id: UUID,
        slug: Optional[str] = None
    ) -> str:
        """Create public shareable link."""
        if not slug:
            slug = secrets.token_urlsafe(8)

        link = PublicLink(
            resource_type=resource_type,
            resource_id=resource_id,
            owner_id=owner_id,
            slug=slug
        )
        db.add(link)
        await db.commit()

        return f"https://humanizer.com/shared/{slug}"

# Usage in routes
@router.get("/api/books/{book_id}")
async def get_book(
    book_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get book if user has access."""
    can_view = await PrivacyService.can_access(
        db, current_user.id, "book", book_id, Permission.VIEW
    )
    if not can_view:
        raise HTTPException(403, "Access denied")

    # ... return book ...
```

---

## Migration Strategy

### Phase 1: Database Migrations (Today)

```bash
# Create migration
cd /Users/tem/humanizer-agent/backend
source venv/bin/activate
alembic revision -m "add_user_system_enhancements"
```

**Migration file:**

```python
# backend/alembic/versions/XXX_add_user_system_enhancements.py

def upgrade():
    # Avatar system
    op.add_column('users', sa.Column('avatar_url', sa.String(500), nullable=True))
    op.add_column('users', sa.Column('avatar_seed', sa.String(100), nullable=True))
    op.add_column('users', sa.Column('avatar_provider', sa.String(20), server_default='dicebear'))

    # Authentication
    op.add_column('users', sa.Column('password_hash', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('oauth_provider', sa.String(50), nullable=True))
    op.add_column('users', sa.Column('oauth_id', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('email_verified', sa.Boolean, server_default='false'))
    op.add_column('users', sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True))

    # Authorization
    op.add_column('users', sa.Column('role', sa.String(20), server_default='user'))

    # Constraints
    op.create_check_constraint(
        'users_role_check',
        'users',
        "role IN ('user', 'admin')"
    )

    op.create_index(
        'users_oauth_provider_id_idx',
        'users',
        ['oauth_provider', 'oauth_id'],
        unique=True,
        postgresql_where=sa.text('oauth_provider IS NOT NULL')
    )

    # Privacy tables (for Phase 3)
    # (Can add later when needed)

def downgrade():
    op.drop_constraint('users_role_check', 'users')
    op.drop_index('users_oauth_provider_id_idx', 'users')

    op.drop_column('users', 'role')
    op.drop_column('users', 'last_login_at')
    op.drop_column('users', 'email_verified')
    op.drop_column('users', 'oauth_id')
    op.drop_column('users', 'oauth_provider')
    op.drop_column('users', 'password_hash')
    op.drop_column('users', 'avatar_provider')
    op.drop_column('users', 'avatar_seed')
    op.drop_column('users', 'avatar_url')
```

**Run migration:**

```bash
alembic upgrade head
```

### Phase 2: Create Default User & Update MCP (Today)

```bash
# Create default user for MCP
psql -d humanizer << EOF
INSERT INTO users (id, username, is_anonymous, avatar_seed, role)
VALUES (
    'a0000000-0000-0000-0000-000000000001',
    'default_user',
    true,
    'a0000000-0000-0000-0000-000000000001',
    'user'
)
ON CONFLICT (id) DO NOTHING;
EOF
```

**Update MCP config:**

```python
# humanizer_mcp/src/config.py
DEFAULT_USER_ID = os.getenv(
    "HUMANIZER_USER_ID",
    "a0000000-0000-0000-0000-000000000001"  # Use UUID, not "user_1"
)
```

**Restart MCP server** to pick up new user_id.

### Phase 3: Frontend Integration (MVP - Next Week)

**Add avatar display:**

```typescript
// frontend/src/components/UserAvatar.tsx
interface UserAvatarProps {
  user: User;
  size?: number;
}

export function UserAvatar({ user, size = 40 }: UserAvatarProps) {
  const avatarUrl = user.avatar_url ||
    `https://api.dicebear.com/7.x/avataaars/svg?seed=${user.avatar_seed || user.id}`;

  return (
    <img
      src={avatarUrl}
      alt={user.username || 'User'}
      width={size}
      height={size}
      className="rounded-full"
    />
  );
}
```

**Add user context:**

```typescript
// frontend/src/contexts/AuthContext.tsx
interface AuthContextType {
  user: User | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
}

export const AuthProvider = ({ children }: PropsWithChildren) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(
    localStorage.getItem('auth_token')
  );

  useEffect(() => {
    if (token) {
      // Fetch current user
      fetch('/api/auth/me', {
        headers: { 'Authorization': `Bearer ${token}` }
      })
        .then(res => res.json())
        .then(setUser)
        .catch(() => {
          localStorage.removeItem('auth_token');
          setToken(null);
        });
    }
  }, [token]);

  const login = async (email: string, password: string) => {
    const res = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });

    if (!res.ok) throw new Error('Login failed');

    const { access_token, user } = await res.json();
    localStorage.setItem('auth_token', access_token);
    setToken(access_token);
    setUser(user);
  };

  const logout = () => {
    localStorage.removeItem('auth_token');
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{
      user,
      login,
      logout,
      isAuthenticated: !!user
    }}>
      {children}
    </AuthContext.Provider>
  );
};
```

### Phase 4: Authentication UI (Multi-user)

**Login page:**

```typescript
// frontend/src/pages/Login.tsx
export function LoginPage() {
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    try {
      await login(email, password);
      navigate('/');
    } catch (error) {
      // Show error
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <input
        type="email"
        value={email}
        onChange={e => setEmail(e.target.value)}
        placeholder="Email"
        required
      />
      <input
        type="password"
        value={password}
        onChange={e => setPassword(e.target.value)}
        placeholder="Password"
        required
      />
      <button type="submit">Login</button>

      <div className="oauth-buttons">
        <a href="/api/oauth/github">
          <GitHubIcon /> Login with GitHub
        </a>
      </div>
    </form>
  );
}
```

### Phase 5: Privacy Controls (Future)

**Add privacy settings to entities:**

```typescript
// frontend/src/components/BookPrivacySettings.tsx
export function BookPrivacySettings({ book }: { book: Book }) {
  const [privacy, setPrivacy] = useState(book.privacy);

  const handleUpdate = async (newPrivacy: PrivacyLevel) => {
    await fetch(`/api/books/${book.id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ privacy: newPrivacy })
    });
    setPrivacy(newPrivacy);
  };

  return (
    <select value={privacy} onChange={e => handleUpdate(e.target.value)}>
      <option value="private">🔒 Private (only you)</option>
      <option value="shared">👥 Shared (specific people)</option>
      <option value="public">🌍 Public (anyone with link)</option>
    </select>
  );
}
```

---

## Security Considerations

### Password Security
- ✅ Use bcrypt (via passlib) - industry standard
- ✅ Minimum 8 characters, complexity requirements
- ✅ Rate limiting on login attempts (TODO: implement)
- ✅ Password reset flow (TODO: implement email service)

### Token Security
- ✅ JWT with 24-hour expiration
- ✅ HTTPS only (enforce in production)
- ✅ HttpOnly cookies option (alternative to localStorage)
- ⚠️ Refresh tokens (TODO: for long-lived sessions)

### Database Security
- ✅ Parameterized queries (SQLAlchemy ORM)
- ✅ Foreign key constraints with CASCADE
- ✅ Row-level security via user_id filters
- ⚠️ Postgres RLS policies (future: database-level enforcement)

### API Security
- ✅ Authentication required for all non-public endpoints
- ✅ CORS configured for frontend origin
- ✅ Rate limiting (TODO: implement with Redis)
- ✅ Input validation (Pydantic models)

---

## Testing Strategy

### Unit Tests

```python
# tests/test_auth_service.py
def test_password_hashing():
    password = "test123"
    hashed = AuthService.hash_password(password)

    assert hashed != password
    assert AuthService.verify_password(password, hashed)
    assert not AuthService.verify_password("wrong", hashed)

async def test_create_user(db_session):
    user = await AuthService.create_user(
        db_session,
        email="test@example.com",
        password="test123",
        username="testuser"
    )

    assert user.id is not None
    assert user.email == "test@example.com"
    assert user.is_anonymous is False
    assert user.password_hash is not None
    assert user.avatar_seed == "test@example.com"

async def test_authenticate(db_session):
    # Create user
    user = await AuthService.create_user(
        db_session, "test@example.com", "test123", "testuser"
    )

    # Authenticate successfully
    auth_user = await AuthService.authenticate(
        db_session, "test@example.com", "test123"
    )
    assert auth_user.id == user.id

    # Fail with wrong password
    auth_user = await AuthService.authenticate(
        db_session, "test@example.com", "wrong"
    )
    assert auth_user is None
```

### Integration Tests

```python
# tests/test_auth_routes.py
async def test_register_login_flow(client):
    # Register
    response = await client.post("/api/auth/register", json={
        "email": "test@example.com",
        "password": "test123",
        "username": "testuser"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    token = data["access_token"]

    # Access protected route
    response = await client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    user = response.json()
    assert user["email"] == "test@example.com"

    # Login
    response = await client.post("/api/auth/login", json={
        "email": "test@example.com",
        "password": "test123"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
```

### Privacy Tests

```python
# tests/test_privacy_service.py
async def test_ownership_access(db_session):
    # Create two users
    owner = User(username="owner", is_anonymous=False)
    other = User(username="other", is_anonymous=False)
    db_session.add_all([owner, other])
    await db_session.commit()

    # Create private book
    book = Book(user_id=owner.id, title="Private", privacy="private")
    db_session.add(book)
    await db_session.commit()

    # Owner can access
    assert await PrivacyService.can_access(
        db_session, owner.id, "book", book.id
    )

    # Other user cannot
    assert not await PrivacyService.can_access(
        db_session, other.id, "book", book.id
    )

async def test_shared_access(db_session):
    # Create shared book
    book = Book(user_id=owner.id, title="Shared", privacy="shared")
    db_session.add(book)
    await db_session.commit()

    # Share with other user
    await PrivacyService.share_resource(
        db_session, owner.id, "book", book.id, other.id, Permission.VIEW
    )

    # Other user can now view
    assert await PrivacyService.can_access(
        db_session, other.id, "book", book.id, Permission.VIEW
    )

    # But cannot edit
    assert not await PrivacyService.can_access(
        db_session, other.id, "book", book.id, Permission.EDIT
    )
```

---

## Performance Considerations

### Caching
- **User sessions:** Cache user objects in Redis (1 hour TTL)
- **Avatar URLs:** Generated URLs can be cached indefinitely (deterministic)
- **Privacy checks:** Cache access decisions (5 minute TTL)

### Indexes
- ✅ users.email (unique index exists)
- ✅ users.id (primary key)
- ✅ users.(oauth_provider, oauth_id) (partial unique index)
- ✅ shared_access.shared_with_user_id
- ✅ shared_access.(resource_type, resource_id)
- ✅ public_links.slug

### Database Queries
- **N+1 Prevention:** Use `joinedload` for relationships
- **Pagination:** All list endpoints must paginate
- **Filtering:** Always filter by user_id first (indexed)

---

## Deployment Checklist

### Environment Variables

```bash
# .env
JWT_SECRET_KEY=<generate with: openssl rand -hex 32>
GITHUB_CLIENT_ID=<from GitHub OAuth app>
GITHUB_CLIENT_SECRET=<from GitHub OAuth app>
FRONTEND_URL=https://humanizer.com
```

### Database
- [ ] Run migrations: `alembic upgrade head`
- [ ] Create default user (for MCP)
- [ ] Verify foreign key constraints
- [ ] Set up database backups

### Backend
- [ ] Update MCP config with UUID user_id
- [ ] Add auth routes to main app
- [ ] Configure CORS for frontend
- [ ] Enable HTTPS in production
- [ ] Set up rate limiting

### Frontend
- [ ] Add AuthContext provider
- [ ] Create login/register pages
- [ ] Add UserAvatar component
- [ ] Protect routes requiring authentication
- [ ] Handle 401 responses (redirect to login)

---

## Future Enhancements

### Passkeys (WebAuthn)
- Passwordless authentication
- Biometric login
- Industry standard (Apple, Google, Microsoft)

### Teams & Organizations
- Multi-user workspaces
- Role-based access within teams
- Shared billing

### Activity Logs
- Audit trail of all actions
- User activity dashboard
- Security alerts

### API Keys
- Programmatic access
- Scoped permissions
- Rate limiting per key

---

## Summary

**This design provides:**

1. ✅ **Real User IDs** - UUID-based, already in place
2. ✅ **User Avatars** - DiceBear (deterministic) + upload option
3. ✅ **Simple but Scalable** - Start with password auth, scale to OAuth
4. ✅ **Object Ownership** - Foreign keys already exist, enforce in queries
5. ✅ **Relations** - User → Collections/Books/Conversations via foreign keys
6. ✅ **Privacy Controls** - Private/Shared/Public with granular permissions

**Migration path:**
- **Today:** Database changes, default user, MCP fix
- **MVP:** Avatars + single-user mode
- **Multi-user:** Authentication + login UI
- **Future:** Sharing, teams, advanced features

**Philosophy alignment:**
- Local-first (anonymous users supported)
- Privacy-respecting (private by default)
- Scalable (OAuth + teams ready)
- Consciousness work (not social features, just infrastructure)

---

**Next Steps:**
1. Run database migration (add columns)
2. Create default user UUID
3. Update MCP config
4. Test `read_quantum` tool
5. Add avatar display to frontend (MVP)
