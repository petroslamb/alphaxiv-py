from __future__ import annotations

from typing import Any, cast

SEARCH_PAYLOAD = [
    {
        "link": "/abs/2603.04379",
        "paperId": "2603.04379",
        "title": "Helios: Real Real-Time Long Video Generation Model",
        "snippet": "A 14B autoregressive diffusion model for real-time long video generation.",
    }
]

ORGANIZATION_SEARCH_PAYLOAD = [
    {
        "id": "org-mit",
        "name": "MIT",
        "image": "images/organizations/mit.png",
        "slug": "mit",
    }
]

TOPIC_SEARCH_PAYLOAD = {"data": ["deep-reinforcement-learning", "reinforcement-learning"]}

LEGACY_PAYLOAD = {
    "paper": {
        "paper_version": {
            "id": "019cbc05-f158-7e3a-b9c1-a43274c0130b",
            "version_label": "v1",
            "version_order": 1,
            "title": "Helios: Real Real-Time Long Video Generation Model",
            "abstract": "We introduce Helios.",
            "publication_date": "Wed Mar 04 2026 18:45:21 GMT+0000 (Coordinated Universal Time)",
            "license": "http://creativecommons.org/licenses/by/4.0/",
            "created_at": "Thu Mar 05 2026 03:23:52 GMT+0000 (Coordinated Universal Time)",
            "updated_at": "Thu Mar 05 2026 03:23:52 GMT+0000 (Coordinated Universal Time)",
            "is_hidden": False,
            "imageURL": "image/2603.04379v1.png",
            "universal_paper_id": "2603.04379",
        },
        "paper_group": {
            "id": "019cbc05-f11c-75c7-a13b-b028107d6a76",
            "universal_paper_id": "2603.04379",
            "title": "Helios: Real Real-Time Long Video Generation Model",
            "created_at": "Thu Mar 05 2026 03:23:51 GMT+0000 (Coordinated Universal Time)",
            "updated_at": "Thu Mar 05 2026 03:23:51 GMT+0000 (Coordinated Universal Time)",
            "topics": ["Computer Science", "cs.CV", "generative-models"],
            "metrics": {
                "questions_count": 0,
                "upvotes_count": 106,
                "downvotes_count": 0,
                "total_votes": 38,
                "public_total_votes": 106,
                "visits_count": {"all": 2974, "last7Days": 2974},
            },
            "podcast_path": "019cbc05-f11c-75c7-a13b-b028107d6a76/podcast.mp3",
            "source": {"name": "alphaXiv", "url": "https://arxiv.org/abs/2603.04379"},
            "is_hidden": False,
            "first_publication_date": "Wed Mar 04 2026 18:45:21 GMT+0000 (Coordinated Universal Time)",
            "variant": "public",
            "citation": {
                "bibtex": "@article{yuan2026helios,\n  title={Helios},\n  author={Yuan, Shenghai}\n}"
            },
            "resources": {
                "github": {
                    "url": "https://github.com/PKU-YuanGroup/Helios",
                    "description": "Helios repo",
                    "language": "Python",
                    "stars": 235,
                }
            },
        },
        "authors": [
            {
                "id": "01985c82-17c5-7fe9-a058-756a906fff19",
                "full_name": "Shenghai Yuan",
                "user_id": None,
                "username": None,
            }
        ],
        "verified_authors": [],
        "pdf_info": {"fetcher_url": "https://fetcher.alphaxiv.org/v2/pdf/2603.04379v1.pdf"},
        "implementation": None,
        "marimo_implementation": None,
        "organization_info": [],
    },
    "comments": [],
}

OVERVIEW_PAYLOAD = {
    "title": "Helios: Real Real-Time Long Video Generation Model",
    "abstract": "We introduce Helios.",
    "summary": {
        "summary": "Helios achieves real-time, minute-scale video generation on a single GPU.",
        "originalProblem": ["Long videos drift.", "Video generation is slow."],
        "solution": ["Unified History Injection.", "Deep Compression Flow."],
        "keyInsights": ["Relative RoPE stabilizes long contexts."],
        "results": ["19.53 FPS on H100."],
    },
    "overview": "## Problem\n\nHelios addresses long-video drift.",
    "intermediateReport": "Detailed research report",
    "citations": [
        {
            "title": "Self forcing",
            "fullCitation": "Xun Huang et al., 2025.",
            "justification": "Referenced for anti-drifting comparison.",
            "alphaxivLink": None,
        }
    ],
}

OVERVIEW_STATUS_PAYLOAD = {
    "state": "done",
    "updatedAt": 1750189412402,
    "translations": {
        "en": {
            "state": "done",
            "requestedAt": 1750189412402,
            "updatedAt": 1750189412402,
            "error": None,
        },
        "fr": {
            "state": "done",
            "requestedAt": 1750189406545,
            "updatedAt": 1750189406545,
            "error": None,
        },
    },
}

FULL_TEXT_PAYLOAD = {
    "pages": [
        {
            "pageNumber": 1,
            "text": "Attention Is All You Need\n\nAbstract\nThe dominant sequence transduction models...",
        },
        {
            "pageNumber": 2,
            "text": "1 Introduction\nRecurrent neural networks, long short-term memory...",
        },
    ]
}

TRANSCRIPT_PAYLOAD = [
    {
        "speaker": "John",
        "line": "Welcome to Advanced Topics in Natural Language Processing.",
    },
    {
        "speaker": "Noah",
        "line": "Was this a direct challenge to recurrent encoder-decoder models?",
    },
]

MENTIONS_PAYLOAD = {
    "mentions": [
        {
            "id": "019b915e-0cd1-7d21-8572-cc7655ad3dc8",
            "postId": "2007286573457650127",
            "conversationId": "2007286573457650127",
            "text": "This paper changed AI.",
            "postedAt": "2026-01-03T03:03:07.000Z",
            "authorUsername": "why_lyon",
            "authorName": "Why Lyon",
            "authorAvatarUrl": "https://pbs.twimg.com/profile_images/example.jpg",
            "likes": 5,
            "retweets": 1,
            "replies": 0,
        }
    ]
}

COMMENTS_PAYLOAD = [
    {
        "id": "comment-root",
        "userId": "user-1",
        "isAuthor": False,
        "title": "Interesting compression result",
        "body": "How does this compare against the baseline at longer horizons?",
        "annotation": None,
        "tag": "question",
        "upvotes": 12,
        "wasEdited": False,
        "hasUpvoted": False,
        "hasDownvoted": False,
        "hasFlagged": False,
        "universalId": "1706.03762",
        "paperGroupId": "015c9ef4-ac30-768d-928b-847320902575",
        "paperVersionId": "0189b531-a930-7613-9d2e-dd918c8435a5",
        "paperTitle": "Attention Is All You Need",
        "parentCommentId": None,
        "author": {
            "id": "author-1",
            "username": "research_reader",
            "realName": "Research Reader",
            "avatar": "https://example.com/avatar.png",
            "institution": "MIT",
            "reputation": 42,
            "verified": True,
            "role": "user",
        },
        "endorsements": [],
        "date": "2026-03-10T10:11:12.000Z",
        "authorResponded": True,
        "responses": [
            {
                "id": "comment-child",
                "userId": "user-2",
                "isAuthor": True,
                "title": None,
                "body": "The appendix includes the long-horizon comparison table.",
                "annotation": None,
                "tag": "author-response",
                "upvotes": 5,
                "wasEdited": False,
                "hasUpvoted": False,
                "hasDownvoted": False,
                "hasFlagged": False,
                "universalId": "1706.03762",
                "paperGroupId": "015c9ef4-ac30-768d-928b-847320902575",
                "paperVersionId": "0189b531-a930-7613-9d2e-dd918c8435a5",
                "paperTitle": "Attention Is All You Need",
                "parentCommentId": "comment-root",
                "author": {
                    "id": "author-2",
                    "username": "paper_author",
                    "realName": "Paper Author",
                    "avatar": "https://example.com/author.png",
                    "institution": "Google Brain",
                    "reputation": 100,
                    "verified": True,
                    "role": "author",
                },
                "endorsements": [],
                "date": "2026-03-10T11:00:00.000Z",
                "authorResponded": False,
                "responses": [],
            }
        ],
    }
]

COMMENT_CREATE_RESPONSE = cast(dict[str, Any], COMMENTS_PAYLOAD[0]).copy()
COMMENT_CREATE_RESPONSE["responses"] = []

COMMENT_REPLY_RESPONSE = cast(
    dict[str, Any],
    cast(list[dict[str, Any]], cast(dict[str, Any], COMMENTS_PAYLOAD[0])["responses"])[0],
).copy()
COMMENT_REPLY_RESPONSE["responses"] = []

SIMILAR_PAPERS_PAYLOAD = [
    {
        "id": "group-helios",
        "paper_group_id": "group-helios",
        "title": "Helios: Real Real-Time Long Video Generation Model",
        "abstract": "We introduce Helios.",
        "paper_summary": {"summary": "Helios summary", "results": ["19.53 FPS"]},
        "image_url": "image/2603.04379v1.png",
        "universal_paper_id": "2603.04379",
        "metrics": {
            "visits_count": {"all": 2974, "last_7_days": 2974},
            "total_votes": 39,
            "public_total_votes": 107,
            "x_likes": 0,
        },
        "publication_date": "2026-03-04T18:45:21.000Z",
        "updated_at": "2026-03-05T03:23:51.964Z",
        "topics": ["Computer Science", "generative-models"],
        "organization_info": [{"name": "MIT"}],
        "authors": ["Shenghai Yuan"],
        "github_stars": 235,
        "github_url": "https://github.com/PKU-YuanGroup/Helios",
        "canonical_id": "2603.04379v1",
        "version_id": "019cbc05-f158-7e3a-b9c1-a43274c0130b",
    },
    {
        "id": "group-helios-duplicate",
        "paper_group_id": "group-helios-duplicate",
        "title": "Helios duplicate listing",
        "abstract": "Duplicate entry that should be removed.",
        "paper_summary": {"summary": "Duplicate", "results": []},
        "image_url": "image/2603.04379v1.png",
        "universal_paper_id": "2603.04379",
        "metrics": {
            "visits_count": {"all": 10, "last_7_days": 5},
            "total_votes": 1,
            "public_total_votes": 1,
            "x_likes": 0,
        },
        "publication_date": "2026-03-04T18:45:21.000Z",
        "updated_at": "2026-03-05T03:23:51.964Z",
        "topics": ["Computer Science"],
        "organization_info": [],
        "authors": ["Shenghai Yuan"],
        "canonical_id": "2603.04379v1",
        "version_id": "019cbc05-f158-7e3a-b9c1-a43274c0130b",
    },
    {
        "id": "group-rlm",
        "paper_group_id": "group-rlm",
        "title": "Recursive Language Models",
        "abstract": "A new model family.",
        "paper_summary": {"summary": "RLM summary", "results": ["325 X likes"]},
        "image_url": "image/2512.24601v1.png",
        "universal_paper_id": "2512.24601",
        "metrics": {
            "visits_count": {"all": 1200, "last_7_days": 800},
            "total_votes": 188,
            "public_total_votes": 514,
            "x_likes": 325,
        },
        "publication_date": "2025-12-20T08:00:00.000Z",
        "updated_at": "2025-12-21T08:00:00.000Z",
        "topics": ["Computer Science", "artificial-intelligence"],
        "organization_info": [{"name": "Meta"}],
        "authors": ["Andrew McCallum"],
        "github_stars": 165,
        "github_url": "https://github.com/example/rlm",
        "canonical_id": "2512.24601v1",
        "version_id": "version-rlm",
    },
]

FOLDERS_PAYLOAD = [
    {
        "id": "folder-reading",
        "name": "Reading List",
        "type": "collection",
        "order": 1,
        "parentId": None,
        "sharingStatus": "private",
        "papers": [
            {
                "paperGroupId": "019cbc05-f11c-75c7-a13b-b028107d6a76",
                "universalPaperId": "2603.04379",
                "canonicalId": "2603.04379v1",
                "paperVersionId": "019cbc05-f158-7e3a-b9c1-a43274c0130b",
                "topics": ["Computer Science", "cs.CV"],
                "title": "Helios: Real Real-Time Long Video Generation Model",
                "abstract": "We introduce Helios.",
            }
        ],
    },
    {
        "id": "folder-bookmarks",
        "name": "Bookmarks",
        "type": "bookmark",
        "order": 2,
        "parentId": None,
        "sharingStatus": "private",
        "papers": [],
    },
]

URL_METADATA_PAYLOAD = {
    "title": "PKU-YuanGroup/Helios",
    "description": "Code for the Helios paper.",
    "image": "https://opengraph.githubassets.com/helios.png",
    "favicon": "https://github.githubassets.com/favicons/favicon.svg",
    "siteName": "GitHub",
    "author": "PKU-YuanGroup",
}

PAPER_VIEW_RESPONSE = {"ok": True, "recorded": True}
PAPER_VOTE_RESPONSE = {"ok": True, "toggled": True}
COMMENT_UPVOTE_RESPONSE = {"ok": True, "toggled": True}
EXPLORE_FEED_PAYLOAD = {
    "papers": [
        {
            "id": "group-helios",
            "paper_group_id": "group-helios",
            "title": "Helios: Real Real-Time Long Video Generation Model",
            "abstract": "We introduce Helios.",
            "paper_summary": {"summary": "Helios summary", "results": ["19.53 FPS"]},
            "image_url": "image/2603.04379v1.png",
            "universal_paper_id": "2603.04379",
            "metrics": {
                "visits_count": {"all": 2974, "last_7_days": 2974},
                "total_votes": 39,
                "public_total_votes": 107,
                "x_likes": 0,
            },
            "first_publication_date": "2026-03-04T18:45:21.000Z",
            "publication_date": "2026-03-04T18:45:21.000Z",
            "updated_at": "2026-03-05T03:23:51.964Z",
            "topics": ["Computer Science", "cs.CV", "generative-models"],
            "organization_info": [],
            "authors": ["Shenghai Yuan", "Yuanyang Yin", "Zongjian Li"],
            "full_authors": [{"id": "author-1", "full_name": "Shenghai Yuan", "verified": False}],
            "author_info": [],
            "github_stars": 235,
            "github_url": "https://github.com/PKU-YuanGroup/Helios",
            "canonical_id": "2603.04379v1",
            "version_id": "019cbc05-f158-7e3a-b9c1-a43274c0130b",
        },
        {
            "id": "group-rlm",
            "paper_group_id": "group-rlm",
            "title": "Recursive Language Models",
            "abstract": "A new model family.",
            "paper_summary": {"summary": "RLM summary", "results": ["325 X likes"]},
            "image_url": "image/2512.24601v1.png",
            "universal_paper_id": "2512.24601",
            "metrics": {
                "visits_count": {"all": 1200, "last_7_days": 800},
                "total_votes": 188,
                "public_total_votes": 514,
                "x_likes": 325,
            },
            "first_publication_date": "2025-12-20T08:00:00.000Z",
            "publication_date": "2025-12-20T08:00:00.000Z",
            "updated_at": "2025-12-21T08:00:00.000Z",
            "topics": ["Computer Science", "machine-learning", "artificial-intelligence"],
            "organization_info": [
                {"name": "MIT", "image": "images/organizations/mit.png"},
                {"name": "Meta", "image": "images/organizations/meta.png"},
            ],
            "authors": ["Andrew McCallum", "Dhiraj Gandhi"],
            "full_authors": [{"id": "author-2", "full_name": "Andrew McCallum", "verified": False}],
            "author_info": [],
            "github_stars": 165,
            "github_url": "https://github.com/example/rlm",
            "canonical_id": "2512.24601v1",
            "version_id": "version-rlm",
        },
    ],
    "page": {
        "pageNum": 0,
        "pageSize": 20,
        "totalPages": 1,
        "totalCount": 2,
    },
}

ASSISTANT_HOME_SESSIONS_BEFORE_PAYLOAD = [
    {
        "id": "session-existing",
        "title": "Earlier chat",
        "newestMessage": 1773270000000,
    }
]

ASSISTANT_HOME_SESSIONS_AFTER_PAYLOAD = [
    {
        "id": "session-new",
        "title": "Helios follow-up",
        "newestMessage": 1773272000000,
    },
    {
        "id": "session-existing",
        "title": "Earlier chat",
        "newestMessage": 1773270000000,
    },
]

ASSISTANT_PAPER_SESSIONS_PAYLOAD = [
    {
        "id": "paper-session",
        "title": "Attention paper discussion",
        "newestMessage": 1773272100000,
    }
]

ASSISTANT_USER_PAYLOAD = {
    "user": {
        "preferences": {
            "base": {
                "preferredLlmModel": "claude-4.6-sonnet",
                "assistantStyleSelection": "default",
                "webSearch": "off",
                "showModelThinking": True,
            }
        }
    }
}

ASSISTANT_HISTORY_PAYLOAD = [
    {
        "id": "message-input",
        "parentMessageId": None,
        "selectedAt": "2026-03-11T23:22:09.494Z",
        "type": "input_text",
        "toolUseId": None,
        "kind": None,
        "content": "What is Helios?",
        "model": "aurelle-1",
        "feedbackType": None,
        "feedbackCategory": None,
        "feedbackDetails": None,
    },
    {
        "id": "message-output",
        "parentMessageId": "message-input",
        "selectedAt": "2026-03-11T23:22:33.656Z",
        "type": "output_text",
        "toolUseId": None,
        "kind": None,
        "content": "Helios is a real-time long video generation model.",
        "model": "aurelle-1",
        "feedbackType": None,
        "feedbackCategory": None,
        "feedbackDetails": None,
    },
    {
        "id": "message-tool",
        "parentMessageId": "message-output",
        "selectedAt": "2026-03-11T23:22:33.656Z",
        "type": "tool_use",
        "toolUseId": None,
        "kind": "Embedding Similarity Search",
        "content": '{"query":"helios video generation"}',
        "model": "aurelle-1",
        "feedbackType": None,
        "feedbackCategory": None,
        "feedbackDetails": None,
    },
]

ASSISTANT_STREAM_RESPONSE = """
:

data: {"type":"delta_output_reasoning","delta":"Searching alphaXiv...","index":0}

data: {"type":"tool_use","kind":"Embedding Similarity Search","content":"{\\"query\\":\\"helios video generation\\"}","index":1}

data: {"type":"tool_result_text","content":"1. Helios paper","index":2}

data: {"type":"delta_output_text","delta":"Helios is ","index":3}

data: {"type":"delta_output_text","delta":"a real-time long video generation model.","index":3}

"""

ASSISTANT_ERROR_STREAM_RESPONSE = """
:

data: {"type":"error","error":{"message":"Assistant backend failed"}}

"""
