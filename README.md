![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![Django](https://img.shields.io/badge/django-%23092e20.svg?style=for-the-badge&logo=django&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/redis-%23DD0031.svg?style=for-the-badge&logo=redis&logoColor=white)
![Swagger](https://img.shields.io/badge/-Swagger-%23C1E81C?style=for-the-badge&logo=swagger&logoColor=black)

# TweetFlow API

Production-minded backend architecture for an X-clone, built as a modular monolith with a strong focus on idempotency, atomicity, and low-latency read paths.

## Why This Project Exists

This project is designed to solve the non-trivial backend problems behind social products:

- high-churn user interactions (like/unlike, follow/unfollow)
- mixed-content timelines (tweets + retweets) that still paginate correctly
- notification consistency under concurrency
- scalable read performance as graph and content density grow

## Core Architecture

### Modular Monolith by Domain

The codebase is split into clear business domains while remaining deployable as one service:

- **Accounts**: authentication, profile lifecycle, password/reset/deactivate/reactivate flows
- **Tweets**: tweet CRUD, comments, likes, retweets, bookmarks, feed assembly
- **Relationships**: follow graph and follower/following queries
- **Interactions / Notifications**: mentions, notifications, read-state management

This structure keeps local development and deployment simple (single process boundary), while preserving clean domain boundaries and minimizing cross-domain coupling.

### Hybrid Feed System

The feed endpoint intentionally merges two independently optimized query paths:

- Tweet QuerySet with `select_related`, `annotate(Count(...), Exists(...))`
- Retweet QuerySet with equivalent metrics projected onto the original tweet

Both streams are merged into a single in-memory collection and globally sorted by `created_at` to produce one chronological feed.

## Engineering Challenges

### 1) Notification Race Condition Under Rapid Interaction Cycles

#### The problem

In real traffic, users can trigger rapid interaction cycles (like -> unlike -> like, repeated taps, concurrent requests). A naive notification write path can create duplicate rows or integrity failures.

#### Failure mode in naive designs

- duplicated notifications for the same actor/receiver/action/target
- race-window collisions around uniqueness checks
- stale read-state when an existing notification should be re-surfaced

#### Solution implemented

- **Database-level idempotency contract**: `Notification` enforces uniqueness across `(sender, receiver, verb, content_type, content_id)`.
- **Atomic write path**: notification creation runs inside `transaction.atomic()`.
- **Concurrency-safe create**: uses `get_or_create(...)` with `IntegrityError` fallback to recover from same-key concurrent inserts.
- **Read-state resurrection**: if a notification already exists and was marked as read, a new equivalent event flips `is_read=False` instead of duplicating data.
- **Commit-aware background trigger**: registration-related notification dispatch is attached via `transaction.on_commit(...)` to prevent out-of-transaction side effects.

#### Outcome

The system is idempotent by design and resilient to race conditions, preserving data integrity without sacrificing UX feedback speed.

### 2) Feed Search + Pagination Trap in Mixed Timelines

#### The problem

A hybrid feed (Tweet + Retweet) cannot be represented as one simple model QuerySet. Standard DRF search/filter flows assume a QuerySet-backed pipeline and can break when the feed becomes a Python list.

#### Hidden trap

If search is delegated to default QuerySet-based filtering while the feed is list-backed, pagination and filtering can diverge or fail, especially under mixed object types.

#### Solution implemented

- Build two optimized QuerySets first (tweets and retweets).
- Merge and sort in memory to guarantee global chronology across types.
- Apply explicit in-memory search over normalized fields (`content`, `quote`, `username`) to keep behavior deterministic.
- Paginate after merge/search to avoid cross-type ordering distortion.
- Cache feed responses using keys scoped by **user + page + search + version**, preventing cache collisions and stale cross-query reads.

#### Outcome

The feed remains semantically correct, paginates consistently, and avoids the common search/pagination regressions seen in mixed-content timelines.

## Scalability and Performance

- **SQLite -> PostgreSQL migration**: prototype-friendly local beginnings evolved into PostgreSQL-backed relational workloads for stronger concurrency semantics and production readiness.
- **N+1 mitigation in nested comments**: `select_related` + targeted `Prefetch` pipelines reduce query fan-out for comment trees and replies.
- **Multi-level caching with Redis**:
  - feed-level caching
  - user-posts caching
  - tweet-detail caching
  - versioned cache invalidation keys for low-cost stale-busting

## Security Model

- JWT authentication using `djangorestframework-simplejwt`
- refresh token blacklisting on logout
- scoped throttling for abuse control:
  - auth endpoints (brute-force mitigation)
  - content creation (anti-spam)
  - interaction endpoints (bot-like rapid actions)
  - sensitive account operations

## Background Processing

Celery workers are integrated to move high-latency and side-effect work off the request cycle:

- asynchronous email dispatch (password/reset/account lifecycle)
- asynchronous mention parsing for tweets
- the same task pipeline pattern is used for extending text parsing workflows such as hashtag extraction/indexing

## Tech Stack

- Django 5 + Django REST Framework
- PostgreSQL
- Redis (cache + Celery broker/result backend)
- Celery
- drf-spectacular (OpenAPI 3.0)

## API Documentation

OpenAPI schema and interactive docs are available out of the box:

- Swagger UI: `/api/docs/`
- ReDoc: `/api/redoc/`
- Raw schema: `/api/schema/`

## System Design Notes

### Follow Graph: Self-Referential Many-to-Many (Through Model)

The social graph is implemented as an explicit `Follow` model containing two foreign keys to the same user table:

- `follower` -> who initiates the relationship
- `following` -> who is being followed

Why this design:

- preserves directionality (`A follows B` != `B follows A`)
- allows relational constraints (`unique_together`) to prevent duplicate edges
- supports metadata (`created_at`) on edges
- keeps follower/following queries index-friendly and expressive

## Future Roadmap

- real-time fan-out and notifications using WebSockets with Django Channels
- media storage and delivery via S3 + CDN
- PostgreSQL trigram-based search optimization for faster fuzzy search at scale

## Quick Start

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Configure environment variables for PostgreSQL, email, and secrets.

3. Apply migrations:

   ```bash
   python manage.py migrate
   ```

4. Run API server:

   ```bash
   python manage.py runserver
   ```

5. Start Celery worker (separate terminal):

   ```bash
   celery -A config worker -l info
   ```
