# 🤖 AI FAQ Chatbot — Live Demo

> A chatbot trained on your business documents that answers customer questions 24/7, in any language, across any channel.

**[🔴 Live Demo](https://twojname.github.io/faq-chatbot-demo)** &nbsp;|&nbsp; Built by [Tomasz Witkowski](mailto:tomekw2323@gmail.com)

---

## What it does

Customers always ask the same questions. This bot answers them — instantly, accurately, 24/7:

- Opening hours
- Pricing and services
- How to book / reserve
- Product availability
- Returns and policies

The bot answers **only** from your actual documents — no hallucinations, no wrong prices.

---

## Demo

The `index.html` demo includes 4 business types with real sample knowledge bases:

- **Café** — menu, hours, reservations (Polish)
- **Beauty salon** — services, pricing, booking
- **Law firm** — specializations, consultation info
- **Gym** — memberships, classes, schedule

Each bot uses the Claude API live — real AI inference, not hardcoded replies.

### Deploy to GitHub Pages
1. Fork this repo
2. **Settings → Pages → Deploy from branch → main / root**
3. Live at `https://yourusername.github.io/faq-chatbot-demo`

---

## Production Setup

```bash
git clone https://github.com/yourusername/faq-chatbot-demo
cd faq-chatbot-demo
pip install -r requirements.txt
cp .env.example .env
# Add ANTHROPIC_API_KEY to .env
# Add your business documents to /docs folder
python chatbot.py
```

### How to train on your documents

Drop any of these into the `/docs` folder:
- `.pdf` — price lists, brochures, service descriptions
- `.docx` — FAQ documents, company info
- `.txt` — plain text knowledge base
- `.csv` — product lists with prices

The bot reads all files on startup and uses them as its knowledge base.

### Deployment channels

| Channel | How |
|---|---|
| Website widget | Embed HTML/JS snippet |
| Telegram | `python-telegram-bot` |
| Messenger | Meta Webhooks API |
| WhatsApp | Twilio or Meta Cloud API |
| Slack | Slack Bolt SDK |
| Streamlit app | Standalone web app |

### Stack

| Component | Library |
|---|---|
| AI brain | Claude API (claude-opus-4-5) |
| Document parsing | PyPDF2, python-docx |
| Web interface | Streamlit or FastAPI |
| Telegram | python-telegram-bot |
| Hosting | Any VPS, Railway, Render |

---

## Customization

To configure for a real business, edit `config.py`:

```python
BUSINESS_NAME = "Your Business Name"
DOCS_FOLDER = "./docs"
BOT_PERSONALITY = "friendly and professional"
LANGUAGE = "auto"  # detects customer language
ESCALATION_TRIGGER = ["complaint", "lawsuit", "refund"]
ESCALATION_EMAIL = "support@yourbusiness.com"
```

---

## Contact

Want this chatbot set up for your business? I handle everything — document upload, deployment, testing, and handover.

**Tomasz Witkowski** — Automation & AI specialist  
📧 tomekw2323@gmail.com  
📱 +48 784 237 870  
🔗 [LinkedIn](https://linkedin.com/in/twojprofil)

*First setup call is free — 15 minutes to see if it's a fit.*

---

*Demo runs in the browser. Production bot runs on Python — deployable on any server, VPS, or cloud.*
