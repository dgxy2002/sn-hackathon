# Project Anchors
- User Requirement Sheet (URS)
- Product Requirements Document (PRD)
- Backlog Tickets

Each of them has to have a subfolder for the above. In general ask for project documents to keep agent on track.

# Technical Anchors
Ask for workflow diagram, sequence diagram, architecture diagram.
State machine diagram.

# CI/CD Anchors
Create this to ensure AI commits are functional. Base level CI/CD is ok.

# Always Dockerize
Always ask to dockerize a project so it is easy to setup/teardown. Everyone will have the same environment to test with.
Anything you dockerize is easily portable to K8's kubernetes (Container Orchestrator). Good for future portability.

# Easy to deploy & any changes to infrastructure is code-based
E.g. Python version upgrade from 3.11 > 3.12 is easy to upgrade. CI/CD pipeline. Easy to find what library is missing with CI/CD pipeline tests instead of having to hunt it down yourself.

# Tickets
Backlog Tickets = List of TODOs + Definition of done
E.g. Which URS is it attached to? Named as Epics. SCRUM methodology for creating tickets + organising development
Sprint = Goal for this development cycle [E.g. must clear half of an epic]
Epics = High-level goals related to URS [Group of Features] - Must have DOD (definition of done)
Ticket = Small-steps within an Epic [Individual feature]

# Create User-Level System Prompt
Anchor copilot's coding workflow, be specific and aggressive so the agent follows it.

# Ideas
1. For coverage questions > convert to a statement selection e.g. "I want ..." > translates to which coverage will be good for user. Can be ranvking vs checkbox
Examples:
    "When I pass, I want my family to be financially stable without me" - Death coverage.

2.