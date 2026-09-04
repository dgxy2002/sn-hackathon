> **Historical scoping input:** This file preserves early brainstorming. Current runtime, provider, and extraction decisions are defined in [PLAN.md](PLAN.md), [URS.md](urs/URS.md), and [PRD.md](prd/PRD.md). Docker Compose, OpenRouter `5.6 Luna`, and local PostgreSQL/pgvector supersede the dedicated-OCR assumptions below.

FA Agent:
Problem Statement:
**How might we help first-time working adults understand which financial decisions matter to them, based on their personal circumstances, without requiring them to piece together fragmented financial information themselves?**

Information
\- Agents that help with choices by analyzing data and recommending actions
\- Our FA agent has to scrape sites from the different insurance providers and make accurate comparisons of their plans between one another
\- Possibly implement a RAG system (Darren can do this?) to store the scraped information from FA sites

Extraction
\- Agents (not really, it'll be ML for us) agents that convert unstructured content into structured, actionable data.
\- Our FA agent will use UnlimitedOCR by Baidu (Show the token/cost savings of using a dedicated OCR module vs throwing it to ChatGPT to process PDF vs converted Markdown files)
\- Tim can handle this

Decision-Support
\- Agents that help with choices by analyzing data and recommending actions
\- Our FA agent will recommend plans to users based on their needs
\- Deborah can do this as your intern touched on this type of system?

Personalized
\- Agents that customize responses based on semantic and episodic context
\- More \*importantly\* our FA agent has to do information gathering/understand the user needs explicitly as insufficient/generalised info is helpful to no-one
\- Jana will do this, more related to prompt tweaking/orchestrating the agent

(Possibly?) Orchestration
\- Agents that combine multiple systems and flows, acting as a control tower
\- Jana do this? Maybe we need an over-arching agent to control all the above sub-agents like a Project Manager role

(Possibly?) Embedded
\- Agents that exist inside other apps or processes rather than as standalone chatbots
\- We can package our entire solution into a simple chrome extension so it is accessible to everyone?

1. user submit information or submit data (OCR) (taking text from images, costs many tokens, so using UnlimitedOCR will allow us to reduce token usage)

Basic Tier

- Based on information that the user inputs (e.g. their pay or if they know their insurance plan), then inform the user about what they are missing out (HAVE PREDEFINED ANSWERS)
- have an open textbox to state goals \- have semantic understanding to guess the age range and goals, to be able to further refine the responses
- At the end, have a summary, and have a separate link or dropdown to click and get more details
  - If the user gets into a car accident, how much can they get back via insurance
-  Gamify it (like buzzfeed quizzes/poomang)
  - [https://poomang.com/en/t/godlife\_test?from\_detail=True\&c=26\&kc=4](https://poomang.com/en/t/godlife_test?from_detail=True&c=26&kc=4) (but more professional)
- Website hit rate (who logged in)

Next Tier

- States the standard rate for your plan, if can get this or cheaper: better for you
- Agent send email to FA
  - Link to FA, state the plan and indicate interest
  - Send it to FA (like gemini)

Roles

- Frontend
- Backend
- Agent \- four systems
  - Info retrieval: diff websites
  - use mcp system
    - Comparing users to other user’s: actual coding (how do u compare to other users)
      - have a weight for each ans and calculate a score to be able to exchange
    - RAG : how to convert documents into processable content for llm
  - Decision support: map user’s choices to our data and create a response
    - summary
  - Personalized: change recommendations if goals change