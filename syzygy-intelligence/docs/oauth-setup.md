# OAuth Provider Setup

Both Google and GitHub OAuth providers are fully implemented in the backend. You just need to create OAuth apps and provide the client ID/secret.

## GitHub OAuth App

1. Go to https://github.com/settings/developers
2. Click **New OAuth App**
3. Fill in:
   - **Application name**: `Syzygy Intelligence`
   - **Homepage URL**: `https://verilysovereign.org`
   - **Authorization callback URL**: `https://verilysovereign.org/api/auth/oauth/github/callback`
4. Click **Register application**
5. On the next page, copy:
   - **Client ID** (e.g., `Iv23...`)
   - Click **Generate a new client secret**, copy the secret
6. Tell me both values — I'll set them in the VPS `.env`

## Google OAuth App (Google Cloud Console)

1. Go to https://console.cloud.google.com/
2. Create a new project or select existing → **Syzygy Intelligence**
3. Navigate to **APIs & Services → OAuth consent screen**
   - Choose **External** user type
   - App name: `Syzygy Intelligence`
   - User support email: your email
   - Developer contact: your email
4. **Scopes**: Add `openid`, `email`, `profile`
5. **Test users**: Add your own email initially
6. Navigate to **APIs & Services → Credentials**
7. Click **Create Credentials → OAuth client ID**
   - Application type: **Web application**
   - Name: `Syzygy Web`
   - Authorized redirect URIs: `https://verilysovereign.org/api/auth/oauth/google/callback`
8. Copy the **Client ID** and **Client Secret**
9. Tell me both values — I'll set them in the VPS `.env`

## What I'll Do

Once you provide the credentials, I'll SSH into the VPS and set:

```
SYZYGY_GOOGLE_CLIENT_ID=your_client_id
SYZYGY_GOOGLE_CLIENT_SECRET=your_client_secret
SYZYGY_GITHUB_CLIENT_ID=your_client_id
SYZYGY_GITHUB_CLIENT_SECRET=your_client_secret
SYZYGY_OAUTH_REDIRECT_URL=https://verilysovereign.org/api/auth/oauth
```

Then restart the backend container. Users will see **"Sign in with Google"** and **"Sign in with GitHub"** buttons on the login page.
