> **Historical scoping input:** This file preserves the original project notes. Current runtime, provider, and extraction decisions are defined in [PLAN.md](PLAN.md), [URS.md](urs/URS.md), and [PRD.md](prd/PRD.md). Docker Compose, OpenRouter `5.6 Luna`, and local PostgreSQL/pgvector supersede the Bedrock-first and dedicated-OCR assumptions below.

Now read and understand both requirements and initial project scoping in full.

Here is what I envision the final project to be:

A web-app. First landing page is a buzz-feed style quiz to get people curious onto what they might be missing out in terms of insurance coverage. At the end of the quiz compare them with their peers to introduce a sense of FOMO so they continue to stay curious about our app.

Next there will be an account creation step. Users can sign up to the web-app to get more personalised recommendation for insurance plan. On the onboarding page ask what their goals are, what their situation is etc. Search the web for the best Insurance Plan Questionaire/FA Questionaire so we can build a user profile that can then be used to patch various insurance plans to.

This entire project is in the context of Singapore so keep the scope as such. Target audience is first-time working adults. From the CNA article linked it mentions 1/4 of Gen-Z still rely on their parents insurance plan and do not know what their coverage is. Our goal is to improve the financial literacy while preventing people from going through the pain or potentially getting scammed/keeping their best interests at heart in an unbiased manner as compared to talking to an FA.

There are 4 agent systems as outlined:
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

Do not build any of these systems.

Overall just understand the problem and help me plan it out such that it is clear and concise. I currently have the raw thoughts I want you to help me organise it.

**Problem Context:** While many young working adults take over legacy insurance policies purchased by their parents, **1 in 4 Gen Zs in Singapore (26%)** remain financially unprepared—lacking adequate life insurance and long-term planning. Without clear visibility, young adults risk paying for outdated family policies that no longer fit their individual budget or independent life goals.
**
How Might We:** Help first-time working adults seamlessly transition from inherited parental plans to an independent, objective financial portfolio tailored to their personal circumstances?

[https://www.channelnewsasia.com/listen/money-talks/your-parents-bought-you-insurance-it-still-enough-today-6155256](https://www.channelnewsasia.com/listen/money-talks/your-parents-bought-you-insurance-it-still-enough-today-6155256)

**How Might We:** Help first-time working adults seamlessly transition from inherited parental plans to an independent, objective financial portfolio tailored to their personal circumstances?

shift the independent, objective financial portfolio tailored to their personal circumstances? to the front to be able to add proof,

must use aws bedrock and ??? (sry i forgor)

show the ocr use in video, to be able to show how ours more efficient by showing baseline

Ok anyways by Friday:
Tim - Build front end back end of website with mock systems

Debs - Build the agent plan recommendation system using fake insurance plans and fake user profiles, it must be able to accurately say what plan is for what user and WHY

AKA it must be justifiably and provably correct

Jana - Do landscaping to see if our problem is actually a problem. Come up with a unified metric to measure financial literacy in terms of insurance readiness etc. Build an agent system to compare users with their peers to FOMO them into using our website.

AKA make the BuzzFeed quiz, test on people, compare quiz results

Darren - Build RAG engine, scraping system and vector database.

AKA our ground source of truth for all current FA plans

Plan this for me and place it into a PLAN.md file. Refine my problem statement as well according to the IGNITE brief. Search the web where needed.