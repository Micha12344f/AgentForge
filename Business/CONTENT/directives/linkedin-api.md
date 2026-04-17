# LinkedIn API — Content Agent Directive

## Purpose

Give the Content agent full programmatic access to LinkedIn so it can publish, manage, and analyse posts on behalf of the authenticated member without leaving the workspace.

---

## Authentication

| Key | Source |
|-----|--------|
| `LINKEDIN_ACCESS_TOKEN` | Root `.env` — obtained via `shared/linkedin_oauth.py` (3-legged OAuth) |
| `LINKEDIN_CLIENT_ID` | Root `.env` |
| `LINKEDIN_CLIENT_SECRET` | Root `.env` |
| Person URN (`sub`) | Call `GET /v2/userinfo` → `sub` field gives the member ID |

**Token lifetime**: ~60 days. Re-run `shared/linkedin_oauth.py` when expired.

### Required headers on every REST API call

```
Authorization: Bearer {LINKEDIN_ACCESS_TOKEN}
X-Restli-Protocol-Version: 2.0.0
LinkedIn-Version: 202604
Content-Type: application/json
```

### Scopes available

| Scope | Grants |
|-------|--------|
| `openid` | OIDC sign-in, ID token |
| `profile` | Name, picture |
| `email` | Primary email |
| `w_member_social` | Create/edit/delete posts, comments, reactions on behalf of the member |
| `r_member_social` | Read own posts (restricted — may not be provisioned) |

---

## API Surface — Complete Reference

### 1. Profile / Identity

| Action | Method | Endpoint |
|--------|--------|----------|
| Get authenticated member info | `GET` | `https://api.linkedin.com/v2/userinfo` |

Response includes `sub` (person ID), `name`, `given_name`, `family_name`, `picture`, `email`.  
Construct person URN as `urn:li:person:{sub}`.

---

### 2. Posts API (`/rest/posts`)

The Posts API replaces the legacy `ugcPosts` API.

#### Create a post

```
POST https://api.linkedin.com/rest/posts
```

**Text-only post**:
```json
{
  "author": "urn:li:person:{sub}",
  "commentary": "Your post text here. #hashtags and @[Name](urn:li:organization:ID) mentions supported.",
  "visibility": "PUBLIC",
  "distribution": {
    "feedDistribution": "MAIN_FEED",
    "targetEntities": [],
    "thirdPartyDistributionChannels": []
  },
  "lifecycleState": "PUBLISHED",
  "isReshareDisabledByAuthor": false
}
```

**Post with image** (requires image URN from Images API):
```json
{
  "author": "urn:li:person:{sub}",
  "commentary": "Check this out!",
  "visibility": "PUBLIC",
  "distribution": { "feedDistribution": "MAIN_FEED", "targetEntities": [], "thirdPartyDistributionChannels": [] },
  "content": {
    "media": {
      "altText": "Description for accessibility",
      "id": "urn:li:image:{imageId}"
    }
  },
  "lifecycleState": "PUBLISHED",
  "isReshareDisabledByAuthor": false
}
```

**Post with video** (requires video URN from Videos API):
```json
{
  "content": {
    "media": {
      "title": "Video title",
      "id": "urn:li:video:{videoId}"
    }
  }
}
```

**Post with article/URL**:
```json
{
  "content": {
    "article": {
      "source": "https://example.com/article",
      "thumbnail": "urn:li:image:{thumbId}",
      "title": "Article Title",
      "description": "Short description"
    }
  }
}
```

**Reshare a post** — add `reshareContext`:
```json
{
  "reshareContext": {
    "parent": "urn:li:share:{originalPostId}"
  }
}
```

#### Content types supported

| Type | Organic | Sponsored |
|------|---------|-----------|
| Text only | Yes | Yes |
| Image | Yes | Yes |
| Video | Yes | Yes |
| Document | Yes | Yes |
| Article | Yes | Yes |
| MultiImage | Yes | No |
| Poll | Yes | No |
| Carousel | No | Yes |

#### Mentions & Hashtags in commentary

- **Mention org**: `@[Org Name](urn:li:organization:{id})`
- **Mention person**: `@[Person Name](urn:li:person:{id})`
- **Hashtag**: `#keyword` (auto-converted by LinkedIn)

#### Get posts

| Action | Method | Endpoint |
|--------|--------|----------|
| Get single post | `GET` | `/rest/posts/{encoded postUrn}` |
| Batch get posts | `GET` | `/rest/posts?ids=List({urn1},{urn2})` — add header `X-RestLi-Method: BATCH_GET` |
| Find by author | `GET` | `/rest/posts?author={encoded personUrn}&q=author&count=10&sortBy=LAST_MODIFIED` |

Optional param `viewContext=AUTHOR` returns drafts and processing posts.

#### Update a post

```
POST https://api.linkedin.com/rest/posts/{encoded postUrn}
X-RestLi-Method: PARTIAL_UPDATE
```
```json
{
  "patch": {
    "$set": {
      "commentary": "Updated text"
    }
  }
}
```

Updatable fields: `commentary`, `contentCallToActionLabel`, `contentLandingPage`, `lifecycleState`, `adContext`.

#### Delete a post

```
DELETE https://api.linkedin.com/rest/posts/{encoded postUrn}
```
Returns `204`. Idempotent.

---

### 3. Images API (`/rest/images`)

#### Upload workflow

1. **Initialize**:
```
POST https://api.linkedin.com/rest/images?action=initializeUpload
```
```json
{ "initializeUploadRequest": { "owner": "urn:li:person:{sub}" } }
```
Response: `uploadUrl`, `image` URN (e.g. `urn:li:image:C4E10AQFoyyAjHPMQuQ`)

2. **Upload binary**:
```
PUT {uploadUrl}
Content-Type: application/octet-stream
Body: <raw image bytes>
```

3. Use the `image` URN in a post's `content.media.id`.

**Supported formats**: JPG, PNG, GIF (up to 250 frames). Max ~36M pixels.

#### Read images

| Action | Endpoint |
|--------|----------|
| Get single | `GET /rest/images/{imageUrn}` |
| Batch get | `GET /rest/images?ids=List(...)` |

---

### 4. Videos API (`/rest/videos`)

#### Upload workflow (multi-part)

1. **Initialize**:
```
POST https://api.linkedin.com/rest/videos?action=initializeUpload
```
```json
{
  "initializeUploadRequest": {
    "owner": "urn:li:person:{sub}",
    "fileSizeBytes": 1055736,
    "uploadCaptions": false,
    "uploadThumbnail": false
  }
}
```
Response: `uploadInstructions[]` (array of `{uploadUrl, firstByte, lastByte}`), `uploadToken`, `video` URN.

2. **Upload parts** — split file into 4 MB chunks, PUT each to its `uploadUrl`. Save the `ETag` from each response header.

3. **Finalize**:
```
POST https://api.linkedin.com/rest/videos?action=finalizeUpload
```
```json
{
  "finalizeUploadRequest": {
    "video": "urn:li:video:{id}",
    "uploadToken": "",
    "uploadedPartIds": ["etag1", "etag2"]
  }
}
```

4. Use the `video` URN in a post.

**Specs**: MP4, 3s–30min, 75KB–500MB.

Optional: `uploadCaptions: true` (SRT, English only), `uploadThumbnail: true`.

---

### 5. Comments API (`/rest/socialActions/.../comments`)

| Action | Method | Endpoint |
|--------|--------|----------|
| Get comments on post | `GET` | `/rest/socialActions/{postUrn}/comments` |
| Get nested comments | `GET` | `/rest/socialActions/{commentUrn}/comments` |
| Get single comment | `GET` | `/rest/socialActions/{postUrn}/comments/{commentId}` |
| Create comment | `POST` | `/rest/socialActions/{postUrn}/comments` |
| Create nested comment | `POST` | `/rest/socialActions/{commentUrn}/comments` (add `parentComment` field) |
| Edit comment | `POST` | `/rest/socialActions/{postUrn}/comments/{id}?actor={actorUrn}` |
| Delete comment | `DELETE` | `/rest/socialActions/{postUrn}/comments/{id}?actor={actorUrn}` |

**Create comment body**:
```json
{
  "actor": "urn:li:person:{sub}",
  "object": "urn:li:activity:{activityId}",
  "message": { "text": "Great post!" }
}
```

**Comment with image**:
```json
{
  "actor": "urn:li:person:{sub}",
  "object": "urn:li:activity:{activityId}",
  "message": { "text": "See this screenshot" },
  "content": [{ "entity": { "image": "urn:li:image:{id}" } }]
}
```

**Comment mentioning** — use `attributes` array in `message`:
```json
{
  "message": {
    "text": "Great work @PersonName!",
    "attributes": [
      { "start": 11, "length": 11, "value": { "person": { "person": "urn:li:person:{id}" } } }
    ]
  }
}
```

---

### 6. Reactions API (`/rest/reactions`)

| Action | Method | Endpoint |
|--------|--------|----------|
| React to post | `POST` | `/rest/reactions?actor={encoded personUrn}` |
| React to comment | `POST` | `/rest/reactions?actor={encoded personUrn}` |
| Get reactions on post | `GET` | `/rest/reactions/(entity:{encoded postUrn})?q=entity` |
| Get single reaction | `GET` | `/rest/reactions/(actor:{actorUrn},entity:{entityUrn})` |
| Delete reaction | `DELETE` | `/rest/reactions/(actor:{actorUrn},entity:{entityUrn})` |

**Reaction types**: `LIKE`, `PRAISE` (Celebrate), `EMPATHY` (Love), `INTEREST` (Insightful), `APPRECIATION` (Support), `ENTERTAINMENT` (Funny).

**Create reaction body**:
```json
{
  "root": "urn:li:activity:{activityId}",
  "reactionType": "LIKE"
}
```

---

### 7. Social Metadata API (`/rest/socialMetadata`)

| Action | Method | Endpoint |
|--------|--------|----------|
| Get engagement summary | `GET` | `/rest/socialMetadata/{postUrn}` |
| Batch get summaries | `GET` | `/rest/socialMetadata?ids=List(...)` |
| Enable/disable comments | `POST` | `/rest/socialMetadata/{postUrn}?actor={personUrn}` |

**Response fields**: `commentSummary.count`, `commentSummary.topLevelCount`, `reactionSummaries` (by type + count), `commentsState`.

**Close comments**:
```json
{ "patch": { "$set": { "commentsState": "CLOSED" } } }
```

---

## Rate Limits

| Resource | Limit |
|----------|-------|
| Member posts (Share on LinkedIn) | 150 requests/day |
| Application total | 100,000 requests/day |
| Comment creation | Short-term 1-min throttle per member |
| Userinfo | 500 requests/day |

---

## URN Encoding Rules

All URNs in URL path/query params must be URL-encoded:
- `urn:li:person:abc` → `urn%3Ali%3Aperson%3Aabc`
- Commas separating URNs in `List(...)` do NOT need encoding

---

## Error Handling

| Code | Meaning | Action |
|------|---------|--------|
| 400 | Bad request (missing field, invalid URN, field too long) | Fix payload |
| 401 | Expired or missing token | Re-run `shared/linkedin_oauth.py` |
| 403 | Insufficient scope or role | Check scopes granted to token |
| 404 | Post/resource not found | Verify URN |
| 409 | Write conflict | Retry |
| 422 | Semantic validation error | Review field values |
| 429 | Rate limit exceeded | Back off and retry |
| 500/503 | Server error | Retry after delay |

---

## Execution Module

The Python helper at `Business/CONTENT/executions/linkedin_api.py` wraps the full API surface:
- `get_profile()` — fetch authenticated user info
- `create_text_post(text)` — publish a text-only post
- `create_article_post(text, url, title, description)` — publish a link post
- `upload_image(file_path)` — initialize + upload, returns image URN
- `create_image_post(text, image_urn)` — publish post with image
- `get_posts(count=10)` — list own posts
- `get_post(post_urn)` — fetch single post
- `update_post(post_urn, commentary)` — edit post text
- `delete_post(post_urn)` — delete a post
- `create_comment(post_urn, text)` — comment on a post
- `create_reaction(entity_urn, reaction_type)` — react to a post or comment
- `delete_reaction(entity_urn)` — remove own reaction
- `get_social_metadata(post_urn)` — get engagement summary
