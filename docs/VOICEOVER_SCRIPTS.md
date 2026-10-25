# IncuBrix Distribution Hub — Complete Voiceover Scripts

This document provides word-for-word voiceover scripts for both required submission videos:
1. **Product Walkthrough Video** (Target: Up to 5 minutes | Actual Runtime: **03:46**)
2. **Technical Demo Video** (Target: Up to 8 minutes | Actual Runtime: **05:36**)

Each video is encoded with lower-third visual banners, live timecodes (`MM:SS / TOTAL`), scene badges, and on-screen narration prompts matching these exact timestamps.

---

# VIDEO 1: Product Walkthrough Video (03:46)
**File Location**: [`evidence/product_walkthrough_video.mp4`](file:///A:/SDE/evidence/product_walkthrough_video.mp4)  
**Submission Field**: *Product walkthrough video URL (up to 5 minutes) \**

### Scene 1: Welcome & Overview Dashboard (00:00 – 00:22)
- **On Screen**: Live SaaS Dashboard at `http://localhost:8000/ui/index.html` displaying network telemetry cards.
- **Voiceover**:
  > *"Welcome to the IncuBrix Distribution Hub — an intelligent long-tail content distribution network. IncuBrix enables creators to submit one piece of high-quality content and distribute it across dozens of relevant developer forums, publications, blogs, and communities while strictly respecting each destination's rules. As you can see on our overview dashboard, we have 165 destinations catalogued, all 165 certified from Level 1 to Level 4, 9 active connectors, and real-time tracking of published posts and rule violations blocked."*

### Scene 2: Content Studio — Authoring & Tagging (00:22 – 00:44)
- **On Screen**: Content Studio form with title, Markdown body, canonical URL, audience tags, and checkboxes.
- **Voiceover**:
  > *"Let's navigate to Content Studio. Here, creators write their core post once in standard Markdown. We attach canonical URL attribution to protect SEO, specify audience tags such as Python, architecture, and backend, and declare whether our article contains commercial offers or AI-assisted content. This metadata is essential for our pre-flight rules engine to guarantee policy compliance across all downstream platforms."*

### Scene 3: Saved Content Library (00:44 – 01:04)
- **On Screen**: Saved content library table showing content items, tags, language, and compliance flags.
- **Voiceover**:
  > *"Once saved, our content item is stored in the database with canonical links, technical tags, and mandatory AI disclosure statements. It is now ready for intelligent destination matching and automated adaptation."*

### Scene 4: Destination Explorer & 165 Communities (01:04 – 01:28)
- **On Screen**: Destination Explorer table listing real developer communities with audience tags, relevance scores, and rule summaries.
- **Voiceover**:
  > *"Now let's open the Destination Explorer. IncuBrix ships with 165 real, researched destinations spanning developer forums, niche technology publications, community blogs, and newsletters. For every single destination, we track audience tags, estimated reach, posting rules, frequency caps, self-promotion policies, and required certification levels."*

### Scene 5: One Connector, Many Destinations (01:28 – 01:50)
- **On Screen**: Platform filter dropdown selecting 'Discourse', showing multiple independent forums.
- **Voiceover**:
  > *"A fundamental philosophy of IncuBrix is 'One Connector, Many Destinations'. Notice how selecting the Discourse platform displays multiple distinct developer and creator forums. A single Discourse connector codebase supports all of these forums dynamically through configuration alone — no new code is needed to onboard another Discourse community."*

### Scene 6: Publishing Workspace — Fit-Ranked Recommendations (01:50 – 02:15)
- **On Screen**: Publishing Workspace with content selection and the 'Recommend Top Destinations' button clicked.
- **Voiceover**:
  > *"In the Publishing Workspace, we select our article and request AI recommendations. Our recommendation engine scores and ranks destinations based on topic and tag overlap, language, geo fit, certification tier, and rules compatibility. On our benchmark dataset, this recommender achieves a measured Precision@10 of 1.0, highlighting the exact reasons why each community is a top match."*

### Scene 7: Live Background Publishing & Real-time Progress (02:15 – 02:40)
- **On Screen**: 'Publish to Selected Destinations' clicked, progress bar advancing to 100%, and results displayed.
- **Voiceover**:
  > *"When we click 'Publish to Selected Destinations', IncuBrix dispatches an HTTP 202 Accepted background job with an Idempotency-Key. Our frontend tracks job progress in real time as our orchestrator adapts the content for each destination, validates platform limits, and securely publishes. Within seconds, the job reaches 100% completion with verified live post URLs."*

### Scene 8: Publishing History & Zero Spam Enforcement (02:40 – 03:02)
- **On Screen**: Publishing History audit log showing live URLs, attempt timestamps, and rule decisions.
- **Voiceover**:
  > *"Over in Publishing History, we maintain a complete, immutable audit log. We can click directly through to verified live post URLs. Notice also how our system strictly enforces community rules: when a promotional post was submitted to a community that prohibits self-promotion, our rules engine blocked it pre-flight, ensuring zero spam and protecting creator reputation."*

### Scene 9: Assisted Publishing Pack (03:02 – 03:24)
- **On Screen**: Assisted Publishing pack with deep link, rules checklist, and downloadable ZIP package.
- **Voiceover**:
  > *"For platforms where automated API posting is prohibited by community terms, IncuBrix never fakes an API call. Instead, our Assisted Publishing connector compiles a complete ready-to-submit ZIP package containing pre-formatted assets, direct submission deep links, and a destination-specific rules checklist marked as 'manual action required'."*

### Scene 10: Analytics Dashboard & Conclusion (03:24 – 03:46)
- **On Screen**: Analytics screen showing platform reliability metrics, zero duplicate posts, and cost breakdown.
- **Voiceover**:
  > *"Finally, our Analytics dashboard provides operational clarity: 100% rule violation catch rate, zero duplicate posts across retries, and high-efficiency distribution at just fractions of a cent per post. IncuBrix makes long-tail content distribution intelligent, safe, and effortless. Thank you!"*

---

# VIDEO 2: Technical Demo Video (04:27 — 3 Parts)
**File Location**: [`evidence/technical_demo_video.mp4`](file:///A:/SDE/evidence/technical_demo_video.mp4)  
**Requirement**: *Technical demo video, up to 5 minutes: one normal run, a refresh on new input, and recovery from one simple failure.*

### Part 1: One Normal Run (00:00 – 01:32)
- **00:00 – 00:20** (Dashboard Overview):
  > *"Welcome to the technical demonstration of IncuBrix Distribution Hub. In this demo, we will show three core scenarios: a normal publishing run, a dynamic refresh on new input, and automatic recovery from a simple policy failure. Here on our dashboard, all 9 connectors and 165 destinations are active and monitored in real time."*
- **00:20 – 00:42** (Content Studio — Standard Input):
  > *"For our normal run, we start in Content Studio. We compose an educational technical article: 'Building Resilient Event-Driven Microservices in Python'. We attach canonical URL attribution for SEO safety, assign backend audience tags, and confirm this post is non-promotional. We save the item to our database."*
- **00:42 – 01:07** (Publishing Workspace — Recommendations & Rules Pass):
  > *"We navigate to the Publishing Workspace, select our article, and request destination recommendations. The engine analyzes topic fit and runs pre-flight deterministic rules evaluation. All target communities return an eligibility status of PASS, confirming that character limits, frequency caps, and link policies are fully satisfied."*
- **01:07 – 01:32** (Background Publishing & Live Confirmation):
  > *"We click 'Publish to Selected Destinations'. IncuBrix dispatches an asynchronous HTTP 202 job with an Idempotency-Key. The frontend polls progress in real time as the orchestrator adapts the content and invokes the Appendix A connector contract. The job reaches 100% completion, delivering verified live post URLs directly."*

### Part 2: A Refresh on New Input (01:32 – 02:27)
- **01:32 – 01:57** (Content Studio — New Input with Distinct Profile):
  > *"Now let's demonstrate a refresh on new input. We return to Content Studio and author a completely different article: 'Enterprise Cloud Migration & Kubernetes Cost Optimization'. This post targets infrastructure engineers with distinct tags: cloud, kubernetes, devops, and aws. We save this new content item."*
- **01:57 – 02:27** (Publishing Workspace — Dynamic Re-ranking on New Input):
  > *"Back in the Publishing Workspace, we select our new Kubernetes article and request fresh recommendations. Notice how the destination ranking instantly refreshes in real time: cloud and DevOps communities are now elevated to top positions with high relevance scores, proving that our recommender dynamically adapts to new content profiles without manual reconfiguration."*

### Part 3: Recovery from One Simple Failure (02:27 – 04:27)
- **02:27 – 02:51** (Triggering Failure — Self-Promotion Violation):
  > *"Next, let's demonstrate recovery from a failure. In Content Studio, we create an article with a commercial discount offer and explicitly enable the 'Contains Self-Promotion / Commercial Offer' flag, targeting communities that strictly prohibit self-promotion."*
- **02:51 – 03:19** (Failure Caught Pre-Flight by Rules Engine):
  > *"When this promotional content is evaluated against strict community destinations, our Deterministic Rules Engine intervenes immediately. As shown in Publishing History, the attempt is blocked pre-flight with SELF_PROMO_PROHIBITED. No outbound request is sent, zero spam reaches the community, and creator reputation is protected."*
- **03:19 – 03:44** (Recovery — Content Adjustment to Technical Guidelines):
  > *"Now let's execute the recovery. We return to Content Studio and adjust the content to comply with community policies: we remove the commercial coupon offer, uncheck the promotional flag, and re-frame the article around technical multi-tenant architecture patterns. We save the compliant revision."*
- **03:44 – 04:09** (Successful Re-attempt & Live URL):
  > *"We re-select our adjusted post in the Publishing Workspace and trigger publishing. The pre-flight rules evaluation now passes cleanly. The background orchestrator dispatches the job, reaching 100% completion and successfully generating the live post URL."*
- **04:09 – 04:27** (Analytics Wrap-Up & Conclusion):
  > *"In Analytics, we verify that the failure was safely intercepted, zero duplicate posts occurred, and our recovery was completely successful. This concludes our technical demonstration of IncuBrix Distribution Hub."*
