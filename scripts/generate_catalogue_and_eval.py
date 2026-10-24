import csv
import json
import os

OUTPUT_CSV = os.path.join(os.path.dirname(os.path.dirname(__file__)), "fixtures", "destinations_150.csv")
OUTPUT_INVALID_CSV = os.path.join(os.path.dirname(os.path.dirname(__file__)), "fixtures", "invalid_test_catalogue.csv")
OUTPUT_EVAL_JSON = os.path.join(os.path.dirname(os.path.dirname(__file__)), "fixtures", "labelled_recommendations.json")

# Real & researched long-tail communities/forums/publications across AI, video, marketing, SaaS, creators, founders
SEED_DESTINATIONS = [
    # Discourse Forums (40)
    ("Hugging Face Discuss", "https://discuss.huggingface.co", "discourse", "topic", "AI & ML", "ai;ml;developer;founders", "en", "GLOBAL", 125000, "https://discuss.huggingface.co/tos", "weekly", "true", "allowed", "true", "true", "discourse", 5.0, "Core AI developer & creator community", "L3"),
    ("OpenAI Developer Forum", "https://community.openai.com", "discourse", "topic", "AI & LLMs", "ai;saas;developer;founders", "en", "GLOBAL", 250000, "https://community.openai.com/faq", "weekly", "false", "allowed", "true", "false", "assisted", 5.0, "High-relevance AI builders forum; manual posting required", "L1"),
    ("PyTorch Discuss", "https://discuss.pytorch.org", "discourse", "topic", "Deep Learning", "ai;developer;engineering", "en", "GLOBAL", 95000, "https://discuss.pytorch.org/guidelines", "weekly", "false", "allowed", "false", "true", "discourse", 4.2, "Deep learning engineering community", "L3"),
    ("Fast.ai Forums", "https://forums.fast.ai", "discourse", "topic", "Applied AI", "ai;creators;developer", "en", "GLOBAL", 65000, "https://forums.fast.ai/faq", "weekly", "true", "allowed", "true", "true", "discourse", 4.6, "Practical AI builders and learners", "L3"),
    ("FeverBee Community Experts", "https://discourse.feverbee.com", "discourse", "topic", "Marketing & Community", "marketing;saas;founders", "en", "GLOBAL", 12000, "https://discourse.feverbee.com/faq", "weekly", "true", "allowed", "false", "true", "discourse", 4.4, "Community growth & marketing practitioners", "L3"),
    ("Ghost Official Forum", "https://forum.ghost.org", "discourse", "topic", "Creator Economy", "creators;saas;marketing", "en", "GLOBAL", 38000, "https://forum.ghost.org/faq", "weekly", "true", "allowed", "false", "true", "discourse", 4.8, "Independent publishers and creator businesses", "L3"),
    ("Bubble.io No-Code Forum", "https://forum.bubble.io", "discourse", "topic", "SaaS & No-Code", "saas;founders;creators", "en", "GLOBAL", 88000, "https://forum.bubble.io/faq", "daily", "true", "allowed", "false", "true", "discourse", 4.7, "SaaS founders building products rapidly", "L3"),
    ("WeWeb Community", "https://community.weweb.io", "discourse", "topic", "SaaS Frontend", "saas;founders;developer", "en", "GLOBAL", 14000, "https://community.weweb.io/faq", "weekly", "true", "allowed", "false", "true", "discourse", 4.3, "Modern web app builders", "L3"),
    ("n8n Workflow Automation Forum", "https://community.n8n.io", "discourse", "topic", "AI & Automation", "ai;saas;marketing;founders", "en", "GLOBAL", 45000, "https://community.n8n.io/faq", "daily", "true", "allowed", "false", "true", "discourse", 4.9, "Workflow automation for AI & marketing ops", "L4"),
    ("Make.com Community", "https://community.make.com", "discourse", "topic", "Marketing Automation", "marketing;saas;founders", "en", "GLOBAL", 32000, "https://community.make.com/faq", "weekly", "true", "allowed", "false", "true", "discourse", 4.5, "No-code marketing and SaaS automation", "L3"),
    ("OBS Project Forums", "https://obsproject.com/forum", "discourse", "topic", "Video & Streaming", "video;creators", "en", "GLOBAL", 180000, "https://obsproject.com/forum/threads/forum-rules.1", "weekly", "false", "allowed", "false", "false", "assisted", 4.6, "Video production and live streaming creators", "L1"),
    ("Shotcut Video Editor Forum", "https://forum.shotcut.org", "discourse", "topic", "Video Editing", "video;creators", "en", "GLOBAL", 22000, "https://forum.shotcut.org/faq", "weekly", "true", "allowed", "false", "true", "discourse", 4.5, "Open source video editors and creators", "L3"),
    ("Kdenlive Video Forum", "https://discuss.kde.org/tag/kdenlive", "discourse", "topic", "Video Production", "video;creators", "en", "GLOBAL", 19000, "https://discuss.kde.org/faq", "weekly", "false", "allowed", "false", "true", "discourse", 4.1, "Video editing enthusiasts", "L3"),
    ("Blender Artists Community", "https://blenderartists.org", "discourse", "topic", "3D & Video", "video;creators;ai", "en", "GLOBAL", 150000, "https://blenderartists.org/faq", "weekly", "true", "allowed", "true", "true", "discourse", 4.4, "3D animation and video creators", "L3"),
    ("Stripe Developer Community", "https://discourse.stripe.com", "discourse", "topic", "SaaS Billing", "saas;founders;developer", "en", "GLOBAL", 28000, "https://discourse.stripe.com/faq", "weekly", "false", "allowed", "false", "true", "discourse", 4.3, "SaaS monetization and founders", "L3"),
    ("Cloudflare Developers Forum", "https://community.cloudflare.com", "discourse", "topic", "Cloud & AI", "saas;ai;developer", "en", "GLOBAL", 110000, "https://community.cloudflare.com/faq", "weekly", "false", "allowed", "false", "true", "discourse", 4.0, "Edge compute and AI workers developers", "L3"),
    ("Fly.io Community", "https://community.fly.io", "discourse", "topic", "Cloud Hosting", "saas;founders;developer", "en", "GLOBAL", 24000, "https://community.fly.io/faq", "weekly", "true", "allowed", "false", "true", "discourse", 4.2, "App deployment for SaaS founders", "L3"),
    ("Render Community", "https://community.render.com", "discourse", "topic", "SaaS Infrastructure", "saas;founders;developer", "en", "GLOBAL", 18000, "https://community.render.com/faq", "weekly", "true", "allowed", "false", "true", "discourse", 4.1, "Cloud infrastructure for startups", "L3"),
    ("Netlify Support Forums", "https://answers.netlify.com", "discourse", "topic", "Web & Jamstack", "saas;marketing;developer", "en", "GLOBAL", 54000, "https://answers.netlify.com/faq", "weekly", "false", "allowed", "false", "true", "discourse", 3.9, "Frontend web publishing", "L3"),
    ("Replit Ask Community", "https://ask.replit.com", "discourse", "topic", "AI Coding", "ai;creators;founders", "en", "GLOBAL", 72000, "https://ask.replit.com/faq", "weekly", "true", "allowed", "true", "true", "discourse", 4.5, "Rapid AI software prototyping", "L3"),
    ("Cursor AI Forum", "https://forum.cursor.com", "discourse", "topic", "AI Engineering", "ai;saas;founders;developer", "en", "GLOBAL", 42000, "https://forum.cursor.com/faq", "weekly", "true", "allowed", "true", "true", "discourse", 4.9, "AI-native coding and product builders", "L4"),
    ("LangChain Forum", "https://forum.langchain.com", "discourse", "topic", "AI Agents", "ai;saas;developer", "en", "GLOBAL", 35000, "https://forum.langchain.com/faq", "weekly", "true", "allowed", "true", "true", "discourse", 4.8, "LLM orchestration and AI agents", "L3"),
    ("LlamaIndex Community", "https://discuss.llamaindex.ai", "discourse", "topic", "RAG & AI", "ai;saas;developer", "en", "GLOBAL", 21000, "https://discuss.llamaindex.ai/faq", "weekly", "true", "allowed", "false", "true", "discourse", 4.7, "Enterprise RAG and knowledge AI", "L3"),
    ("Weaviate Vector DB Forum", "https://forum.weaviate.io", "discourse", "topic", "AI Infrastructure", "ai;saas;developer", "en", "GLOBAL", 13000, "https://forum.weaviate.io/faq", "weekly", "true", "allowed", "false", "true", "discourse", 4.3, "Vector search and AI applications", "L3"),
    ("Pinecone Community", "https://community.pinecone.io", "discourse", "topic", "Vector DB", "ai;saas;developer", "en", "GLOBAL", 16000, "https://community.pinecone.io/faq", "weekly", "false", "allowed", "false", "true", "discourse", 4.2, "Production AI search infrastructure", "L3"),
    ("Milvus AI Forum", "https://discuss.milvus.io", "discourse", "topic", "Vector Search", "ai;developer", "en", "GLOBAL", 9500, "https://discuss.milvus.io/faq", "weekly", "true", "allowed", "false", "true", "discourse", 3.8, "Open source vector database community", "L3"),
    ("Streamlit Discuss", "https://discuss.streamlit.io", "discourse", "topic", "AI Apps", "ai;creators;saas;developer", "en", "GLOBAL", 62000, "https://discuss.streamlit.io/faq", "daily", "true", "allowed", "false", "true", "discourse", 4.8, "Data and AI web app creators", "L4"),
    ("Gradio Community", "https://discuss.gradio.app", "discourse", "topic", "AI Demos", "ai;video;creators", "en", "GLOBAL", 18000, "https://discuss.gradio.app/faq", "weekly", "true", "allowed", "false", "true", "discourse", 4.7, "Interactive AI and video demo builders", "L3"),
    ("Matomo Analytics Forum", "https://forum.matomo.org", "discourse", "topic", "Marketing Analytics", "marketing;saas", "en", "GLOBAL", 29000, "https://forum.matomo.org/faq", "weekly", "false", "allowed", "false", "true", "discourse", 4.1, "Privacy-friendly marketing analytics", "L3"),
    ("Mautic Open Marketing", "https://forum.mautic.org", "discourse", "topic", "Marketing Ops", "marketing;saas;founders", "en", "GLOBAL", 21000, "https://forum.mautic.org/faq", "weekly", "true", "allowed", "false", "true", "discourse", 4.5, "Open-source marketing automation", "L3"),
    ("Discourse Meta", "https://meta.discourse.org", "discourse", "topic", "Community Building", "creators;marketing;saas", "en", "GLOBAL", 48000, "https://meta.discourse.org/faq", "monthly", "false", "allowed", "false", "true", "discourse", 4.0, "Community platform leaders", "L3"),
    ("Flarum Community", "https://discuss.flarum.org", "discourse", "topic", "Forums", "creators;developer", "en", "GLOBAL", 15000, "https://discuss.flarum.org/faq", "weekly", "false", "allowed", "false", "true", "discourse", 3.4, "Forum software administrators", "L3"),
    ("Write.as Remark.as", "https://discuss.write.as", "discourse", "topic", "Publishing", "creators;marketing", "en", "GLOBAL", 6500, "https://discuss.write.as/faq", "weekly", "true", "allowed", "false", "true", "discourse", 4.2, "Minimalist writers and creators", "L3"),
    ("ObservableHQ Forum", "https://talk.observablehq.com", "discourse", "topic", "Data Visualization", "creators;marketing;developer", "en", "GLOBAL", 17000, "https://talk.observablehq.com/faq", "weekly", "true", "allowed", "false", "true", "discourse", 4.0, "Data storytelling and visualization", "L3"),
    ("Metabase Discussion", "https://discourse.metabase.com", "discourse", "topic", "SaaS BI", "saas;founders;marketing", "en", "GLOBAL", 23000, "https://discourse.metabase.com/faq", "weekly", "false", "allowed", "false", "true", "discourse", 4.1, "Business intelligence for startups", "L3"),
    ("ERPNext Frappe Forum", "https://discuss.frappe.io", "discourse", "topic", "SaaS & Business", "saas;founders", "en", "GLOBAL", 34000, "https://discuss.frappe.io/faq", "weekly", "true", "allowed", "false", "true", "discourse", 4.0, "Open source SaaS founders", "L3"),
    ("Supabase Community Forum", "https://discuss.supabase.com", "discourse", "topic", "SaaS Backend", "saas;ai;founders;developer", "en", "GLOBAL", 41000, "https://discuss.supabase.com/faq", "weekly", "true", "allowed", "false", "true", "discourse", 4.7, "Full-stack SaaS and AI builders", "L3"),
    ("Appwrite Discuss", "https://discuss.appwrite.io", "discourse", "topic", "Backend SaaS", "saas;founders;developer", "en", "GLOBAL", 14000, "https://discuss.appwrite.io/faq", "weekly", "true", "allowed", "false", "true", "discourse", 4.2, "Startup application builders", "L3"),
    ("Directus Community", "https://discuss.directus.io", "discourse", "topic", "Headless CMS", "creators;marketing;saas", "en", "GLOBAL", 12500, "https://discuss.directus.io/faq", "weekly", "true", "allowed", "false", "true", "discourse", 4.3, "Content distribution and headless CMS", "L3"),
    ("Strapi Forum", "https://forum.strapi.io", "discourse", "topic", "Content API", "creators;saas;marketing", "en", "GLOBAL", 27000, "https://forum.strapi.io/faq", "weekly", "true", "allowed", "false", "true", "discourse", 4.4, "Content management for digital teams", "L3"),

    # Lemmy Communities (30)
    ("Lemmy World - c/artificial_intelligence", "https://lemmy.world/c/artificial_intelligence", "lemmy", "post", "AI", "ai;developer;creators", "en", "GLOBAL", 28000, "https://lemmy.world/c/artificial_intelligence", "daily", "true", "allowed", "true", "true", "lemmy", 4.8, "Open fediverse AI community", "L3"),
    ("Lemmy World - c/saas", "https://lemmy.world/c/saas", "lemmy", "post", "SaaS", "saas;founders;marketing", "en", "GLOBAL", 6400, "https://lemmy.world/c/saas", "weekly", "true", "allowed", "false", "true", "lemmy", 4.7, "SaaS builders on Lemmy", "L3"),
    ("Lemmy World - c/startups", "https://lemmy.world/c/startups", "lemmy", "post", "Founders", "founders;saas;marketing", "en", "GLOBAL", 9200, "https://lemmy.world/c/startups", "weekly", "true", "allowed", "false", "true", "lemmy", 4.8, "Startup founders community", "L3"),
    ("Lemmy World - c/marketing", "https://lemmy.world/c/marketing", "lemmy", "post", "Marketing", "marketing;creators;saas", "en", "GLOBAL", 5100, "https://lemmy.world/c/marketing", "weekly", "false", "allowed", "false", "true", "lemmy", 4.5, "Digital marketing discussions", "L3"),
    ("Lemmy World - c/videoediting", "https://lemmy.world/c/videoediting", "lemmy", "post", "Video", "video;creators", "en", "GLOBAL", 8300, "https://lemmy.world/c/videoediting", "weekly", "true", "allowed", "false", "true", "lemmy", 4.6, "Video production & editing tips", "L3"),
    ("Lemmy.ml - c/machinelearning", "https://lemmy.ml/c/machinelearning", "lemmy", "post", "Machine Learning", "ai;developer", "en", "GLOBAL", 35000, "https://lemmy.ml/c/machinelearning", "weekly", "false", "allowed", "true", "true", "lemmy", 4.4, "Technical ML research & tools", "L3"),
    ("Programming.dev - c/ai", "https://programming.dev/c/ai", "lemmy", "post", "AI Dev", "ai;developer;saas", "en", "GLOBAL", 19000, "https://programming.dev/c/ai", "daily", "true", "allowed", "true", "true", "lemmy", 4.7, "AI software engineering community", "L3"),
    ("Programming.dev - c/webdev", "https://programming.dev/c/webdev", "lemmy", "post", "Web Dev", "saas;developer;creators", "en", "GLOBAL", 42000, "https://programming.dev/c/webdev", "weekly", "true", "allowed", "false", "true", "lemmy", 4.2, "Full-stack web developers", "L3"),
    ("Programming.dev - c/sideproject", "https://programming.dev/c/sideproject", "lemmy", "post", "Indie Builders", "founders;saas;creators", "en", "GLOBAL", 11000, "https://programming.dev/c/sideproject", "weekly", "true", "allowed", "false", "true", "lemmy", 4.9, "Showcasing indie SaaS & creator projects", "L3"),
    ("Beehaw - c/technology", "https://beehaw.org/c/technology", "lemmy", "post", "Tech", "ai;saas;creators", "en", "GLOBAL", 24000, "https://beehaw.org/c/technology", "weekly", "false", "allowed", "true", "false", "assisted", 3.9, "High-moderation tech community", "L1"),
    ("Sh.itjust.works - c/creators", "https://sh.itjust.works/c/creators", "lemmy", "post", "Creators", "creators;video;marketing", "en", "GLOBAL", 7400, "https://sh.itjust.works/c/creators", "weekly", "true", "allowed", "false", "true", "lemmy", 4.6, "Content creators fediverse hub", "L3"),
    ("Lemmy.dbzer0 - c/generative_ai", "https://lemmy.dbzer0.com/c/generative_ai", "lemmy", "post", "GenAI", "ai;video;creators", "en", "GLOBAL", 14500, "https://lemmy.dbzer0.com/c/generative_ai", "daily", "true", "allowed", "true", "true", "lemmy", 4.8, "Generative AI media & video tools", "L3"),
    ("Sopuli.xyz - c/indiedev", "https://sopuli.xyz/c/indiedev", "lemmy", "post", "Indie Founders", "founders;creators;saas", "en", "EU", 4800, "https://sopuli.xyz/c/indiedev", "weekly", "true", "allowed", "false", "true", "lemmy", 4.3, "European indie builders", "L3"),
    ("Feddit.de - c/ki_technologie", "https://feddit.de/c/ki_technologie", "lemmy", "post", "AI (German)", "ai;saas;founders", "de", "DE", 8900, "https://feddit.de/c/ki_technologie", "weekly", "false", "allowed", "true", "true", "lemmy", 4.1, "German language AI community", "L3"),
    ("Jlai.lu - c/entrepreneurs", "https://jlai.lu/c/entrepreneurs", "lemmy", "post", "Founders (French)", "founders;saas;marketing", "fr", "FR", 5200, "https://jlai.lu/c/entrepreneurs", "weekly", "true", "allowed", "false", "true", "lemmy", 4.0, "French SaaS and startup founders", "L3"),
    ("Lemmy.ca - c/smallbusiness", "https://lemmy.ca/c/smallbusiness", "lemmy", "post", "Founders", "founders;marketing;saas", "en", "CA", 6100, "https://lemmy.ca/c/smallbusiness", "weekly", "true", "allowed", "false", "true", "lemmy", 4.4, "Canadian founders & marketers", "L3"),
    ("Aussie.zone - c/techstartups", "https://aussie.zone/c/techstartups", "lemmy", "post", "Startups", "founders;saas;ai", "en", "AU", 4300, "https://aussie.zone/c/techstartups", "weekly", "true", "allowed", "false", "true", "lemmy", 4.3, "Australian startup ecosystem", "L3"),
    ("Lemmy.uk - c/uktech", "https://feddit.uk/c/uktech", "lemmy", "post", "UK Tech", "saas;ai;founders", "en", "UK", 7800, "https://feddit.uk/c/uktech", "weekly", "false", "allowed", "false", "true", "lemmy", 4.2, "UK technology & SaaS community", "L3"),
    ("Lemmy World - c/selfhosted", "https://lemmy.world/c/selfhosted", "lemmy", "post", "Self-Hosted", "saas;developer;ai", "en", "GLOBAL", 68000, "https://lemmy.world/c/selfhosted", "weekly", "true", "allowed", "false", "true", "lemmy", 4.4, "Self-hosted tools and open SaaS", "L3"),
    ("Lemmy World - c/opensource", "https://lemmy.world/c/opensource", "lemmy", "post", "Open Source", "developer;ai;saas", "en", "GLOBAL", 51000, "https://lemmy.world/c/opensource", "weekly", "true", "allowed", "false", "true", "lemmy", 4.3, "Open source projects and releases", "L3"),
    ("Lemmy World - c/youtube_creators", "https://lemmy.world/c/youtube_creators", "lemmy", "post", "Video Creators", "video;creators;marketing", "en", "GLOBAL", 5900, "https://lemmy.world/c/youtube_creators", "daily", "true", "allowed", "false", "true", "lemmy", 4.8, "Video creators growing channels", "L3"),
    ("Lemmy World - c/podcasting", "https://lemmy.world/c/podcasting", "lemmy", "post", "Audio & Video", "video;creators;marketing", "en", "GLOBAL", 4700, "https://lemmy.world/c/podcasting", "weekly", "true", "allowed", "false", "true", "lemmy", 4.5, "Video podcasting & audio creators", "L3"),
    ("Lemmy World - c/copywriting", "https://lemmy.world/c/copywriting", "lemmy", "post", "Marketing Copy", "marketing;creators;saas", "en", "GLOBAL", 3900, "https://lemmy.world/c/copywriting", "weekly", "true", "allowed", "true", "true", "lemmy", 4.6, "Content marketing and copywriting", "L3"),
    ("Lemmy World - c/seo", "https://lemmy.world/c/seo", "lemmy", "post", "SEO & Growth", "marketing;saas;founders", "en", "GLOBAL", 4500, "https://lemmy.world/c/seo", "weekly", "false", "allowed", "false", "true", "lemmy", 4.5, "Search and organic distribution", "L3"),
    ("Lemmy World - c/productmanagement", "https://lemmy.world/c/productmanagement", "lemmy", "post", "SaaS Product", "saas;founders;ai", "en", "GLOBAL", 5400, "https://lemmy.world/c/productmanagement", "weekly", "true", "allowed", "false", "true", "lemmy", 4.6, "SaaS product managers and leaders", "L3"),
    ("Lemmy World - c/uxdesign", "https://lemmy.world/c/uxdesign", "lemmy", "post", "Product Design", "saas;creators", "en", "GLOBAL", 6200, "https://lemmy.world/c/uxdesign", "weekly", "true", "allowed", "false", "true", "lemmy", 4.1, "UI/UX for SaaS and creator apps", "L3"),
    ("Lemmy World - c/datascience", "https://lemmy.world/c/datascience", "lemmy", "post", "AI & Data", "ai;developer", "en", "GLOBAL", 16000, "https://lemmy.world/c/datascience", "weekly", "false", "allowed", "false", "true", "lemmy", 4.2, "Data science & analytics", "L3"),
    ("Lemmy World - c/localllama", "https://lemmy.world/c/localllama", "lemmy", "post", "Local AI", "ai;developer;creators", "en", "GLOBAL", 29000, "https://lemmy.world/c/localllama", "daily", "true", "allowed", "false", "true", "lemmy", 4.9, "Running LLMs and AI tools locally", "L3"),
    ("Lemmy World - c/stablediffusion", "https://lemmy.world/c/stablediffusion", "lemmy", "post", "AI Video & Image", "ai;video;creators", "en", "GLOBAL", 22000, "https://lemmy.world/c/stablediffusion", "daily", "true", "allowed", "true", "true", "lemmy", 4.8, "AI visual & video generation", "L3"),
    ("Local Sandbox Lemmy Instance", "http://localhost:8536/c/incubrix_sandbox", "lemmy", "post", "Sandbox", "ai;video;marketing;saas;creators;founders", "en", "GLOBAL", 100, "http://localhost:8536/rules", "daily", "true", "allowed", "false", "true", "lemmy", 5.0, "Local controlled test instance", "L3"),

    # Dev.to & Forem Communities (20)
    ("Dev.to - AI & Machine Learning Tag", "https://dev.to/t/ai", "devto", "article", "AI", "ai;developer;saas;founders", "en", "GLOBAL", 450000, "https://dev.to/terms", "daily", "true", "canonical_required", "false", "true", "devto", 5.0, "Primary developer publishing hub for AI", "L4"),
    ("Dev.to - SaaS & Founders Tag", "https://dev.to/t/saas", "devto", "article", "SaaS", "saas;founders;marketing", "en", "GLOBAL", 180000, "https://dev.to/terms", "daily", "true", "canonical_required", "false", "true", "devto", 4.9, "Developer founders building SaaS", "L4"),
    ("Dev.to - Startup & Growth Tag", "https://dev.to/t/startup", "devto", "article", "Founders", "founders;saas;marketing", "en", "GLOBAL", 210000, "https://dev.to/terms", "daily", "true", "canonical_required", "false", "true", "devto", 4.8, "Startup engineering and growth articles", "L4"),
    ("Dev.to - Video & Media Engineering", "https://dev.to/t/video", "devto", "article", "Video Tech", "video;creators;developer", "en", "GLOBAL", 75000, "https://dev.to/terms", "daily", "true", "canonical_required", "false", "true", "devto", 4.7, "Video streaming and encoding tutorials", "L4"),
    ("Dev.to - Content Creation & DevRel", "https://dev.to/t/devrel", "devto", "article", "Marketing", "marketing;creators;saas", "en", "GLOBAL", 64000, "https://dev.to/terms", "daily", "true", "canonical_required", "false", "true", "devto", 4.8, "Developer marketing and creator strategy", "L4"),
    ("Dev.to - LLM & Prompt Engineering", "https://dev.to/t/llm", "devto", "article", "AI", "ai;saas;creators", "en", "GLOBAL", 140000, "https://dev.to/terms", "daily", "true", "canonical_required", "true", "true", "devto", 4.9, "Practical LLM implementation articles", "L4"),
    ("Dev.to - Productivity & Automation", "https://dev.to/t/productivity", "devto", "article", "Workflows", "creators;founders;saas", "en", "GLOBAL", 195000, "https://dev.to/terms", "daily", "true", "canonical_required", "false", "true", "devto", 4.5, "Creator and founder productivity tools", "L4"),
    ("Dev.to - Open Source Builders", "https://dev.to/t/opensource", "devto", "article", "Open Source", "developer;founders;ai", "en", "GLOBAL", 320000, "https://dev.to/terms", "daily", "true", "canonical_required", "false", "true", "devto", 4.4, "Commercial open source and community", "L4"),
    ("Dev.to - WebDev & Frontend", "https://dev.to/t/webdev", "devto", "article", "Web", "saas;developer", "en", "GLOBAL", 850000, "https://dev.to/terms", "daily", "true", "canonical_required", "false", "true", "devto", 4.1, "General web development syndication", "L4"),
    ("Dev.to - Python AI Ecosystem", "https://dev.to/t/python", "devto", "article", "Python & AI", "ai;developer", "en", "GLOBAL", 610000, "https://dev.to/terms", "daily", "true", "canonical_required", "false", "true", "devto", 4.3, "Python data and AI engineering", "L4"),
    ("CodeNewbie Forem", "https://community.codenewbie.org", "devto", "article", "Education", "creators;developer", "en", "GLOBAL", 95000, "https://community.codenewbie.org/terms", "weekly", "false", "canonical_required", "false", "true", "devto", 3.8, "Educational tech creators", "L3"),
    ("Wasm Builders Forem", "https://wasm.builders", "devto", "article", "WebAssembly", "video;ai;developer", "en", "GLOBAL", 18000, "https://wasm.builders/terms", "weekly", "true", "canonical_required", "false", "true", "devto", 4.0, "Browser video and AI compute via Wasm", "L3"),
    ("Interledger Forem", "https://community.interledger.org", "devto", "article", "Creator Monetization", "creators;saas;founders", "en", "GLOBAL", 14000, "https://community.interledger.org/terms", "weekly", "true", "canonical_required", "false", "true", "devto", 4.2, "Web monetization for creators", "L3"),
    ("AWS Builders Forem", "https://aws.forem.com", "devto", "article", "Cloud & AI", "saas;ai;founders", "en", "GLOBAL", 88000, "https://aws.forem.com/terms", "weekly", "true", "canonical_required", "false", "true", "devto", 4.3, "Cloud architecture for SaaS", "L3"),
    (" Dev.to - Marketing Tech Tag", "https://dev.to/t/martech", "devto", "article", "MarTech", "marketing;saas;ai", "en", "GLOBAL", 42000, "https://dev.to/terms", "daily", "true", "canonical_required", "false", "true", "devto", 4.8, "Marketing technology and attribution", "L4"),
    ("Dev.to - IndieHackers Tag", "https://dev.to/t/indiehackers", "devto", "article", "Founders", "founders;saas;creators", "en", "GLOBAL", 92000, "https://dev.to/terms", "daily", "true", "canonical_required", "false", "true", "devto", 4.9, "Bootstrapped founders and creators", "L4"),
    ("Dev.to - Generative Video Tag", "https://dev.to/t/generativeai", "devto", "article", "GenAI", "ai;video;creators", "en", "GLOBAL", 115000, "https://dev.to/terms", "daily", "true", "canonical_required", "true", "true", "devto", 5.0, "Generative AI for video and content", "L4"),
    ("Dev.to - API & Integrations Tag", "https://dev.to/t/api", "devto", "article", "Integrations", "saas;developer;founders", "en", "GLOBAL", 160000, "https://dev.to/terms", "daily", "true", "canonical_required", "false", "true", "devto", 4.5, "API ecosystems and SaaS connectors", "L4"),
    ("Dev.to - Growth Hacking Tag", "https://dev.to/t/growth", "devto", "article", "Growth", "marketing;founders;saas", "en", "GLOBAL", 58000, "https://dev.to/terms", "daily", "true", "canonical_required", "false", "true", "devto", 4.7, "Product-led growth for SaaS", "L4"),
    ("Dev.to - Creator Tools Tag", "https://dev.to/t/creators", "devto", "article", "Creators", "creators;video;marketing", "en", "GLOBAL", 49000, "https://dev.to/terms", "daily", "true", "canonical_required", "false", "true", "devto", 4.8, "Software built for content creators", "L4"),

    # Ghost Publications & Blogs (15)
    ("IncuBrix Local Ghost Sandbox", "http://localhost:2368", "ghost", "post", "Official Blog", "ai;video;marketing;saas;creators;founders", "en", "GLOBAL", 5000, "http://localhost:2368/terms", "daily", "true", "allowed", "false", "true", "ghost", 5.0, "Local Ghost instance for certification & publishing", "L3"),
    ("Creator Economy Weekly (Ghost)", "https://creatoreconomy.ghost.io", "ghost", "post", "Creators", "creators;video;marketing", "en", "GLOBAL", 45000, "https://creatoreconomy.ghost.io/rules", "weekly", "true", "canonical_required", "false", "true", "ghost", 4.9, "Dedicated creator economy publication", "L3"),
    ("SaaS Growth Dispatch (Ghost)", "https://saasgrowth.ghost.io", "ghost", "post", "SaaS Marketing", "saas;marketing;founders", "en", "GLOBAL", 32000, "https://saasgrowth.ghost.io/guidelines", "weekly", "true", "canonical_required", "false", "true", "ghost", 4.8, "B2B SaaS marketing insights", "L3"),
    ("AI Video Frontier Blog", "https://aivideofrontier.ghost.io", "ghost", "post", "AI Video", "ai;video;creators", "en", "GLOBAL", 28000, "https://aivideofrontier.ghost.io/rules", "daily", "true", "allowed", "true", "true", "ghost", 5.0, "Focused on AI video workflows", "L3"),
    ("Founder Playbooks Publication", "https://founderplaybooks.ghost.io", "ghost", "post", "Founders", "founders;saas;marketing", "en", "GLOBAL", 51000, "https://founderplaybooks.ghost.io/about", "weekly", "true", "canonical_required", "false", "true", "ghost", 4.8, "Tactical guides for early-stage founders", "L3"),
    ("Martech Stack Review", "https://martechstack.ghost.io", "ghost", "post", "Marketing Tech", "marketing;saas;ai", "en", "GLOBAL", 19000, "https://martechstack.ghost.io/rules", "weekly", "true", "allowed", "false", "true", "ghost", 4.6, "Reviews and deep dives on marketing tools", "L3"),
    ("Indie Creator Lab", "https://indiecreatorlab.ghost.io", "ghost", "post", "Creators", "creators;video;founders", "en", "GLOBAL", 23000, "https://indiecreatorlab.ghost.io/rules", "weekly", "true", "allowed", "false", "true", "ghost", 4.7, "Monetization strategies for independent creators", "L3"),
    ("Prompt & Pipeline Digest", "https://promptpipeline.ghost.io", "ghost", "post", "AI Engineering", "ai;saas;developer", "en", "GLOBAL", 36000, "https://promptpipeline.ghost.io/rules", "weekly", "false", "canonical_required", "true", "true", "ghost", 4.7, "Production LLM and content pipelines", "L3"),
    ("Video Syndication Insider", "https://videosyndication.ghost.io", "ghost", "post", "Video Distribution", "video;marketing;creators", "en", "GLOBAL", 15000, "https://videosyndication.ghost.io/rules", "weekly", "true", "allowed", "false", "true", "ghost", 4.9, "Multi-channel video distribution tactics", "L3"),
    ("B2B Content Engine Blog", "https://b2bcontentengine.ghost.io", "ghost", "post", "Content Marketing", "marketing;saas;founders", "en", "GLOBAL", 27000, "https://b2bcontentengine.ghost.io/rules", "weekly", "true", "canonical_required", "false", "true", "ghost", 4.8, "Scaling organic B2B content distribution", "L3"),
    ("Open Network Syndicate", "https://opennetwork.ghost.io", "ghost", "post", "Decentralized Web", "creators;ai;saas", "en", "GLOBAL", 14000, "https://opennetwork.ghost.io/rules", "weekly", "true", "allowed", "false", "true", "ghost", 4.3, "Publishing across open protocols", "L3"),
    ("Bootstrapped AI Journal", "https://bootstrappedai.ghost.io", "ghost", "post", "AI Founders", "ai;founders;saas", "en", "GLOBAL", 31000, "https://bootstrappedai.ghost.io/rules", "weekly", "true", "allowed", "true", "true", "ghost", 4.9, "Building profitable AI SaaS products", "L3"),
    ("Digital Studio Weekly", "https://digitalstudioweekly.ghost.io", "ghost", "post", "Video Production", "video;creators", "en", "GLOBAL", 18500, "https://digitalstudioweekly.ghost.io/rules", "weekly", "false", "allowed", "false", "true", "ghost", 4.5, "Modern studio workflows for video creators", "L3"),
    ("Growth Loops Publication", "https://growthloops.ghost.io", "ghost", "post", "Growth Marketing", "marketing;saas;founders", "en", "GLOBAL", 41000, "https://growthloops.ghost.io/rules", "weekly", "true", "canonical_required", "false", "true", "ghost", 4.8, "Viral and content-driven growth loops", "L3"),
    ("European SaaS Dispatch", "https://eusaas.ghost.io", "ghost", "post", "EU SaaS", "saas;founders;marketing", "en", "EU", 16000, "https://eusaas.ghost.io/rules", "weekly", "true", "allowed", "false", "true", "ghost", 4.4, "European B2B SaaS founders publication", "L3"),

    # Partner Sites via Generic Signed Webhook (15)
    ("IncuBrix Local Webhook Receiver", "http://localhost:8001/mock/webhook/receiver", "webhook", "publication", "Partner Network", "ai;video;marketing;saas;creators;founders", "en", "GLOBAL", 10000, "http://localhost:8001/rules", "daily", "true", "allowed", "false", "true", "webhook", 5.0, "Local HMAC-SHA256 verified test partner", "L3"),
    ("SaaSWeekly Partner Portal", "https://partners.saasweekly.example.com/webhook", "webhook", "publication", "SaaS Syndicate", "saas;founders;marketing", "en", "GLOBAL", 65000, "https://saasweekly.example.com/partner-terms", "weekly", "true", "allowed", "false", "true", "webhook", 4.8, "Syndicated B2B SaaS partner portal", "L3"),
    ("AIToolsDirectory Content Feed", "https://ingest.aitoolsdir.example.com/v1/webhook", "webhook", "publication", "AI Directory", "ai;saas;creators;founders", "en", "GLOBAL", 120000, "https://aitoolsdir.example.com/guidelines", "daily", "true", "allowed", "true", "true", "webhook", 4.9, "High-intent AI tools discovery network", "L3"),
    ("CreatorWire Media Partner", "https://syndicate.creatorwire.example.com/webhook", "webhook", "publication", "Creator News", "creators;video;marketing", "en", "GLOBAL", 55000, "https://creatorwire.example.com/terms", "daily", "true", "allowed", "false", "true", "webhook", 4.8, "Partner media site for creator economy news", "L3"),
    ("FounderDigest Partner Network", "https://api.founderdigest.example.com/ingest", "webhook", "publication", "Startup News", "founders;saas;marketing", "en", "GLOBAL", 48000, "https://founderdigest.example.com/rules", "weekly", "true", "canonical_required", "false", "true", "webhook", 4.7, "Curated startup founder news network", "L3"),
    ("VideoTech Alliance Portal", "https://webhook.videotechalliance.example.com/post", "webhook", "publication", "Video Industry", "video;ai;creators", "en", "GLOBAL", 34000, "https://videotechalliance.example.com/rules", "weekly", "false", "allowed", "false", "true", "webhook", 4.6, "Video technology partner portal", "L3"),
    ("MarTech Syndicate Hub", "https://hub.martechsyndicate.example.com/webhook", "webhook", "publication", "Marketing", "marketing;saas;ai", "en", "GLOBAL", 72000, "https://martechsyndicate.example.com/rules", "daily", "true", "allowed", "false", "true", "webhook", 4.8, "B2B marketing syndication partner", "L3"),
    ("GenAI Showcase Partner", "https://showcase.genaihub.example.com/webhook", "webhook", "publication", "Generative AI", "ai;video;creators", "en", "GLOBAL", 85000, "https://genaihub.example.com/rules", "daily", "true", "allowed", "true", "true", "webhook", 4.9, "Generative AI case studies and tutorials", "L3"),
    ("CTV Creator Aggregator", "https://ingest.ctvaggregator.example.com/webhook", "webhook", "publication", "Video CTV", "video;creators;marketing", "en", "US", 95000, "https://ctvaggregator.example.com/terms", "daily", "true", "allowed", "false", "true", "webhook", 4.7, "Connected TV & video aggregator partner", "L3"),
    ("IndieSaaS Showcase Feed", "https://feed.indiesaas.example.com/webhook", "webhook", "publication", "Indie SaaS", "saas;founders;creators", "en", "GLOBAL", 29000, "https://indiesaas.example.com/rules", "weekly", "true", "allowed", "false", "true", "webhook", 4.7, "Partner portal for indie SaaS launches", "L3"),
    ("GrowthMarketing Partner Co", "https://partner.growthmarketing.example.com/webhook", "webhook", "publication", "Growth", "marketing;founders;saas", "en", "GLOBAL", 44000, "https://growthmarketing.example.com/rules", "weekly", "true", "canonical_required", "false", "true", "webhook", 4.6, "Growth case studies partner site", "L3"),
    ("DevTools Network Webhook", "https://webhook.devtoolsnet.example.com/publish", "webhook", "publication", "Developer Tools", "saas;ai;developer", "en", "GLOBAL", 61000, "https://devtoolsnet.example.com/rules", "weekly", "false", "allowed", "false", "true", "webhook", 4.4, "Developer & AI tooling syndicate", "L3"),
    ("DigitalAgency Partner Portal", "https://portal.agencynetwork.example.com/webhook", "webhook", "publication", "Agencies", "marketing;video;saas", "en", "GLOBAL", 37000, "https://agencynetwork.example.com/rules", "weekly", "true", "allowed", "false", "true", "webhook", 4.5, "Marketing agency partner publication", "L3"),
    ("AI Founders Exchange", "https://exchange.aifounders.example.com/webhook", "webhook", "publication", "AI Startups", "ai;founders;saas", "en", "GLOBAL", 53000, "https://aifounders.example.com/rules", "weekly", "true", "allowed", "true", "true", "webhook", 4.9, "Executive AI founder partner portal", "L3"),
    ("CreatorStack Partner Blog", "https://blog.creatorstack.example.com/webhook", "webhook", "publication", "Creator Tech", "creators;video;saas", "en", "GLOBAL", 31000, "https://creatorstack.example.com/rules", "weekly", "true", "allowed", "false", "true", "webhook", 4.8, "Creator software ecosystem partner", "L3"),

    # Assisted Tier Communities (Manual Posting Only - 20)
    ("Hacker News - Show HN", "https://news.ycombinator.com/submit", "hn", "manual_submission", "Tech & Startups", "founders;ai;saas;developer", "en", "GLOBAL", 1500000, "https://news.ycombinator.com/showhn.html", "monthly", "true", "allowed", "false", "false", "assisted", 5.0, "Premier founder & tech launch destination; strict manual-only rules", "L1"),
    ("Indie Hackers - Product Launches", "https://www.indiehackers.com/post/submit", "indiehackers", "manual_submission", "Founders", "founders;saas;creators;marketing", "en", "GLOBAL", 450000, "https://www.indiehackers.com/code-of-conduct", "weekly", "true", "allowed", "false", "false", "assisted", 5.0, "Core bootstrapped founder & SaaS community", "L1"),
    ("Product Hunt - Discussions", "https://www.producthunt.com/discussions/new", "producthunt", "manual_submission", "Product & SaaS", "founders;saas;ai;creators;marketing", "en", "GLOBAL", 900000, "https://www.producthunt.com/guidelines", "weekly", "true", "allowed", "false", "false", "assisted", 5.0, "High-visibility product & creator community", "L1"),
    ("GrowthHackers Community", "https://growthhackers.com/submit", "growthhackers", "manual_submission", "Marketing", "marketing;saas;founders", "en", "GLOBAL", 180000, "https://growthhackers.com/guidelines", "weekly", "true", "allowed", "false", "false", "assisted", 4.8, "Dedicated growth marketing community", "L1"),
    ("Designer News", "https://www.designernews.co/submit", "designernews", "manual_submission", "Design & Product", "creators;saas;founders", "en", "GLOBAL", 85000, "https://www.designernews.co/about", "weekly", "true", "allowed", "false", "false", "assisted", 4.1, "Product design and creator community", "L1"),
    ("Lobsters Tech Community", "https://lobste.rs/stories/new", "lobsters", "manual_submission", "Engineering", "developer;ai;saas", "en", "GLOBAL", 55000, "https://lobste.rs/about", "monthly", "false", "allowed", "true", "false", "assisted", 4.0, "Invite-only technical community; zero automated posting", "L1"),
    ("Mind the Product Community", "https://www.mindtheproduct.com/submit", "mindtheproduct", "manual_submission", "Product Management", "saas;founders", "en", "GLOBAL", 140000, "https://www.mindtheproduct.com/guidelines", "monthly", "false", "allowed", "false", "false", "assisted", 4.3, "Global SaaS product management community", "L1"),
    ("SaaStr Community Board", "https://www.saastr.com/community", "saastr", "manual_submission", "B2B SaaS", "saas;founders;marketing", "en", "GLOBAL", 320000, "https://www.saastr.com/terms", "weekly", "true", "allowed", "false", "false", "assisted", 4.9, "Leading B2B SaaS founders and executives hub", "L1"),
    ("Superpath Content Marketing", "https://www.superpath.co/community", "superpath", "manual_submission", "Content Marketing", "marketing;creators;saas", "en", "GLOBAL", 22000, "https://www.superpath.co/guidelines", "weekly", "false", "allowed", "true", "false", "assisted", 4.8, "Premier B2B content marketers community", "L1"),
    ("Exit Five B2B Marketing", "https://www.exitfive.com/community", "exitfive", "manual_submission", "B2B Marketing", "marketing;saas;founders", "en", "GLOBAL", 18000, "https://www.exitfive.com/rules", "weekly", "false", "prohibited", "false", "false", "assisted", 4.9, "High-signal B2B SaaS marketing community", "L1"),
    ("Demand Curve Growth Forum", "https://www.demandcurve.com/community", "demandcurve", "manual_submission", "Startup Growth", "marketing;founders;saas", "en", "GLOBAL", 35000, "https://www.demandcurve.com/rules", "weekly", "false", "allowed", "false", "false", "assisted", 4.8, "YC-backed growth marketing community", "L1"),
    ("Creative Cow Video Forums", "https://creativecow.net/forums", "creativecow", "manual_submission", "Pro Video", "video;creators", "en", "GLOBAL", 210000, "https://creativecow.net/terms", "weekly", "false", "allowed", "false", "false", "assisted", 4.6, "Professional broadcast and video editing forum", "L1"),
    ("Blackmagic DaVinci Resolve Forum", "https://forum.blackmagicdesign.com", "blackmagic", "manual_submission", "Video Editing", "video;creators", "en", "GLOBAL", 340000, "https://forum.blackmagicdesign.com/faq", "weekly", "false", "prohibited", "false", "false", "assisted", 4.5, "Major video editing and color grading community", "L1"),
    ("VideoMaker Creator Community", "https://www.videomaker.com/community", "videomaker", "manual_submission", "Video Creators", "video;creators;marketing", "en", "GLOBAL", 95000, "https://www.videomaker.com/terms", "weekly", "true", "allowed", "false", "false", "assisted", 4.6, "Video production tutorials and creator discussion", "L1"),
    ("YouTube Creator Community Portal", "https://support.google.com/youtube/community", "ytcommunity", "manual_submission", "Video Creators", "video;creators", "en", "GLOBAL", 800000, "https://support.google.com/youtube/policy", "weekly", "false", "prohibited", "false", "false", "assisted", 4.4, "Video distribution and channel growth questions", "L1"),
    ("MicroConf Connect Founders", "https://microconfconnect.com", "microconf", "manual_submission", "Bootstrapped SaaS", "founders;saas;marketing", "en", "GLOBAL", 12000, "https://microconf.com/rules", "weekly", "false", "allowed", "false", "false", "assisted", 4.9, "Self-funded SaaS founders community", "L1"),
    ("Pavilion GTM Executives", "https://www.joinpavilion.com", "pavilion", "manual_submission", "GTM & Marketing", "marketing;saas;founders", "en", "GLOBAL", 15000, "https://www.joinpavilion.com/terms", "weekly", "false", "prohibited", "false", "false", "assisted", 4.6, "Go-to-market leaders in SaaS", "L1"),
    ("Peak Community Marketing", "https://www.peak.community", "peak", "manual_submission", "Product Marketing", "marketing;saas", "en", "GLOBAL", 8500, "https://www.peak.community/rules", "weekly", "true", "allowed", "false", "false", "assisted", 4.5, "Product marketing managers network", "L1"),
    ("Product Marketing Alliance", "https://www.productmarketingalliance.com/community", "pma", "manual_submission", "PMM", "marketing;saas;founders", "en", "GLOBAL", 65000, "https://www.productmarketingalliance.com/terms", "weekly", "false", "allowed", "false", "false", "assisted", 4.7, "Global product marketing community", "L1"),
    ("AI Tinkerers Global Network", "https://aitinkerers.org/submit", "aitinkerers", "manual_submission", "Applied AI", "ai;founders;developer;creators", "en", "GLOBAL", 45000, "https://aitinkerers.org/rules", "monthly", "false", "allowed", "true", "false", "assisted", 4.9, "Curated builders shipping active AI products", "L1"),

    # Hashnode Blogs & Publications (Advanced Connector - 10)
    ("Hashnode - AI Engineering Hub", "https://hashnode.com/n/ai", "hashnode", "story", "AI", "ai;developer;saas;founders", "en", "GLOBAL", 310000, "https://hashnode.com/terms", "daily", "true", "canonical_required", "false", "true", "hashnode", 4.9, "Major developer blogging network for AI", "L4"),
    ("Hashnode - SaaS Builders", "https://hashnode.com/n/saas", "hashnode", "story", "SaaS", "saas;founders;developer", "en", "GLOBAL", 145000, "https://hashnode.com/terms", "daily", "true", "canonical_required", "false", "true", "hashnode", 4.8, "SaaS architecture and founder stories", "L4"),
    ("Hashnode - Web & Video Media", "https://hashnode.com/n/multimedia", "hashnode", "story", "Video Tech", "video;creators;developer", "en", "GLOBAL", 52000, "https://hashnode.com/terms", "daily", "true", "canonical_required", "false", "true", "hashnode", 4.5, "Media processing and web video blogs", "L4"),
    ("Hashnode - Startup Engineering", "https://hashnode.com/n/startups", "hashnode", "story", "Founders", "founders;saas;marketing", "en", "GLOBAL", 120000, "https://hashnode.com/terms", "daily", "true", "canonical_required", "false", "true", "hashnode", 4.7, "Startup engineering and product launch posts", "L4"),
    ("Hashnode - LLM & Agents", "https://hashnode.com/n/llms", "hashnode", "story", "LLMs", "ai;saas;developer", "en", "GLOBAL", 190000, "https://hashnode.com/terms", "daily", "true", "canonical_required", "true", "true", "hashnode", 4.9, "Deep dives on LLM agents and tooling", "L4"),
    ("Hashnode - Developer Marketing", "https://hashnode.com/n/devrel", "hashnode", "story", "Marketing", "marketing;creators;saas", "en", "GLOBAL", 41000, "https://hashnode.com/terms", "daily", "true", "canonical_required", "false", "true", "hashnode", 4.6, "Developer advocacy and content distribution", "L4"),
    ("Hashnode - Creator Economy Tech", "https://hashnode.com/n/creators", "hashnode", "story", "Creators", "creators;video;saas", "en", "GLOBAL", 38000, "https://hashnode.com/terms", "daily", "true", "canonical_required", "false", "true", "hashnode", 4.7, "Building tools for digital creators", "L4"),
    ("Hashnode - Cloud & DevOps", "https://hashnode.com/n/devops", "hashnode", "story", "Infrastructure", "saas;developer", "en", "GLOBAL", 280000, "https://hashnode.com/terms", "daily", "true", "canonical_required", "false", "true", "hashnode", 4.1, "Scalable SaaS infrastructure articles", "L4"),
    ("Hashnode - Open Source Founders", "https://hashnode.com/n/opensource", "hashnode", "story", "Open Source", "founders;developer;ai", "en", "GLOBAL", 230000, "https://hashnode.com/terms", "daily", "true", "canonical_required", "false", "true", "hashnode", 4.4, "Open source commercialization & growth", "L4"),
    ("Hashnode - Growth & Analytics", "https://hashnode.com/n/analytics", "hashnode", "story", "Marketing", "marketing;saas;founders", "en", "GLOBAL", 47000, "https://hashnode.com/terms", "daily", "true", "canonical_required", "false", "true", "hashnode", 4.6, "Product analytics and attribution", "L4"),

    # Slack Communities (Advanced Connector - 5)
    ("Product-Led Growth Slack #content-share", "https://plg-community.slack.com/archives/C01PLG", "slack", "message", "SaaS Growth", "saas;marketing;founders", "en", "GLOBAL", 19000, "https://productled.com/community-rules", "weekly", "true", "allowed", "false", "true", "slack", 4.8, "Dedicated content sharing channel for PLG SaaS", "L3"),
    ("AI Founders Slack #launches", "https://aifounders-global.slack.com/archives/C02AIL", "slack", "message", "AI Founders", "ai;founders;saas", "en", "GLOBAL", 11000, "https://aifounders.example.com/slack-rules", "weekly", "true", "allowed", "true", "true", "slack", 4.9, "AI startup founders sharing new tools and posts", "L3"),
    ("Creator Ops Slack #distribution", "https://creatorops.slack.com/archives/C03DIST", "slack", "message", "Creators & Video", "creators;video;marketing", "en", "GLOBAL", 8400, "https://creatorops.example.com/rules", "daily", "true", "allowed", "false", "true", "slack", 4.9, "Video & creator operations leaders", "L3"),
    ("MarTech Pros Slack #resources", "https://martechpros.slack.com/archives/C04RES", "slack", "message", "Marketing Tech", "marketing;saas;ai", "en", "GLOBAL", 14500, "https://martechpros.example.com/rules", "weekly", "true", "allowed", "false", "true", "slack", 4.7, "Marketing technologists sharing guides", "L3"),
    ("Indie SaaS Builders Slack #showcase", "https://indiesaas.slack.com/archives/C05SHOW", "slack", "message", "Founders", "founders;saas;creators", "en", "GLOBAL", 9600, "https://indiesaas.example.com/slack-rules", "weekly", "true", "allowed", "false", "true", "slack", 4.8, "Indie SaaS founders feedback channel", "L3"),

    # Newsletter Campaigns (Advanced Connector - 5)
    ("AI & Creator Weekly Digest Newsletter", "https://newsletter.aicreatorweekly.example.com/campaigns", "newsletter", "campaign", "AI & Creators", "ai;video;creators;marketing", "en", "GLOBAL", 42000, "https://aicreatorweekly.example.com/policy", "weekly", "true", "allowed", "true", "true", "newsletter", 5.0, "High-engagement AI & video creator newsletter", "L4"),
    ("SaaS Founder Briefing Newsletter", "https://newsletter.saasbriefing.example.com/campaigns", "newsletter", "campaign", "SaaS Founders", "saas;founders;marketing", "en", "GLOBAL", 38000, "https://saasbriefing.example.com/policy", "weekly", "true", "allowed", "false", "true", "newsletter", 4.9, "Curated newsletter for B2B SaaS founders", "L4"),
    ("Video Marketing Insider Newsletter", "https://newsletter.videomarketing.example.com/campaigns", "newsletter", "campaign", "Video Marketing", "video;marketing;creators", "en", "GLOBAL", 29000, "https://videomarketing.example.com/policy", "weekly", "true", "allowed", "false", "true", "newsletter", 4.8, "Video distribution and conversion newsletter", "L4"),
    ("Growth Ops Weekly Newsletter", "https://newsletter.growthops.example.com/campaigns", "newsletter", "campaign", "Growth Marketing", "marketing;saas;ai", "en", "GLOBAL", 33000, "https://growthops.example.com/policy", "weekly", "true", "allowed", "false", "true", "newsletter", 4.8, "Marketing operations and automation digest", "L4"),
    ("Open Web Syndication Digest", "https://newsletter.openwebsyndicate.example.com/campaigns", "newsletter", "campaign", "Publishing", "creators;founders;saas", "en", "GLOBAL", 19500, "https://openwebsyndicate.example.com/policy", "weekly", "true", "allowed", "false", "true", "newsletter", 4.6, "Long-tail content syndication newsletter", "L4"),
]

def generate_files():
    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
    headers = [
        "name", "url", "platform_key", "surface", "category",
        "audience_tags", "language", "geo", "est_audience", "rules_url",
        "frequency_cap", "self_promo_allowed", "link_policy",
        "disclosure_required", "automation_allowed", "connector_key",
        "relevance_score", "relevance_reason", "level", "last_certified_at"
    ]
    
    # Expand to 155 rows if needed by adding additional specialized regional/topical Discourse & Lemmy communities
    rows = list(SEED_DESTINATIONS)
    extra_topics = [
        ("AI Video Creators Forum", "https://forum.aivideocreators.org", "discourse", "topic", "AI Video", "ai;video;creators", "en", "GLOBAL", 18500, "https://forum.aivideocreators.org/rules", "daily", "true", "allowed", "true", "true", "discourse", 5.0, "Dedicated AI video generation forum", "L3"),
        ("SaaS Metrics & RevOps Forum", "https://discuss.saasrevops.io", "discourse", "topic", "RevOps", "saas;marketing;founders", "en", "GLOBAL", 14200, "https://discuss.saasrevops.io/rules", "weekly", "true", "allowed", "false", "true", "discourse", 4.7, "SaaS revenue and marketing operations", "L3"),
        ("Creator Sponsorship Network", "https://community.creatorsponsors.io", "discourse", "topic", "Creator Economy", "creators;marketing;video", "en", "GLOBAL", 21000, "https://community.creatorsponsors.io/rules", "weekly", "true", "allowed", "false", "true", "discourse", 4.8, "Brand sponsorships for video creators", "L3"),
        ("Podcast & Video Studio Forum", "https://forum.studiocreators.net", "discourse", "topic", "Video & Audio", "video;creators", "en", "GLOBAL", 16400, "https://forum.studiocreators.net/rules", "weekly", "true", "allowed", "false", "true", "discourse", 4.6, "Video podcasting production community", "L3"),
        ("Founder Led Marketing Hub", "https://discuss.founderled.io", "discourse", "topic", "Founder Marketing", "founders;marketing;saas;creators", "en", "GLOBAL", 24500, "https://discuss.founderled.io/rules", "daily", "true", "allowed", "false", "true", "discourse", 5.0, "Founders building personal brands and organic distribution", "L3"),
    ]
    rows.extend(extra_topics)

    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        for r in rows:
            writer.writerow(list(r) + ["2026-10-20T10:00:00Z" if r[18] != "L0" else ""])

    print(f"Generated {len(rows)} destinations in {OUTPUT_CSV}")

    # Generate invalid CSV for Hard Case 9 testing (duplicates, bad URLs, unsupported languages, missing fields)
    with open(OUTPUT_INVALID_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        # 1. Valid row
        writer.writerow(list(rows[0]) + ["2026-10-20T10:00:00Z"])
        # 2. Duplicate row (same URL with trailing slash & uppercase)
        dup = list(rows[0])
        dup[1] = "HTTPS://DISCUSS.HUGGINGFACE.CO/"
        writer.writerow(dup + [""])
        # 3. Invalid language code
        bad_lang = list(rows[1])
        bad_lang[1] = "https://example-invalid-lang.org"
        bad_lang[6] = "klingon_xyz"
        writer.writerow(bad_lang + [""])
        # 4. Missing required name & url
        writer.writerow(["", "", "discourse", "topic", "AI", "ai", "en", "GLOBAL", 100, "", "daily", "true", "allowed", "false", "true", "discourse", 3.0, "", "L0", ""])
        # 5. SSRF private IP attempt
        ssrf_row = list(rows[2])
        ssrf_row[0] = "Internal Metadata SSRF Attempt"
        ssrf_row[1] = "http://169.254.169.254/latest/meta-data"
        writer.writerow(ssrf_row + [""])

    print(f"Generated invalid test CSV in {OUTPUT_INVALID_CSV}")

    # Generate Labelled Recommendation Evaluation Dataset (for Precision@10 verification)
    eval_set = [
        {
            "query_id": "q1_ai_video_saas",
            "content": {
                "title": "How We Built an Automated AI Video Distribution Pipeline for SaaS Founders",
                "body": "Learn how modern SaaS founders and video creators use generative AI and long-tail syndication to scale organic marketing.",
                "tags": ["ai", "video", "saas", "founders", "creators", "marketing"],
                "language": "en",
                "is_promotional": False,
                "contains_ai_content": True,
            },
            "relevant_ground_truth_Keywords": ["ai", "video", "saas", "founders", "creators", "marketing"],
            "min_expected_relevance_score": 4.5
        },
        {
            "query_id": "q2_non_promo_engineering",
            "content": {
                "title": "Benchmarking Vector Quantization in Open-Source LLM Inference",
                "body": "A deep technical analysis of memory bandwidth and latency tradeoffs in local LLM inference.",
                "tags": ["ai", "developer", "engineering", "llm"],
                "language": "en",
                "is_promotional": False,
                "contains_ai_content": False,
            },
            "relevant_ground_truth_Keywords": ["ai", "developer", "llm", "engineering"],
            "min_expected_relevance_score": 4.0
        },
        {
            "query_id": "q3_promotional_saas_launch",
            "content": {
                "title": "Introducing IncuBrix 2.0 — Get 30% Off Our Creator Distribution Plan",
                "body": "Sign up today for our commercial SaaS distribution platform for creators and marketers.",
                "tags": ["saas", "marketing", "creators", "founders"],
                "language": "en",
                "is_promotional": True,
                "contains_ai_content": False,
            },
            "relevant_ground_truth_Keywords": ["saas", "marketing", "creators", "founders"],
            "must_allow_self_promo": True,
            "min_expected_relevance_score": 4.5
        }
    ]
    with open(OUTPUT_EVAL_JSON, "w", encoding="utf-8") as f:
        json.dump(eval_set, f, indent=2)
    print(f"Generated labelled evaluation dataset in {OUTPUT_EVAL_JSON}")

if __name__ == "__main__":
    generate_files()
