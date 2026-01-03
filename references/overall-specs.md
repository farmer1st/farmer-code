I want to build an application that coordinate multiple ai agents to build applications. the flow is describe in the sldc-worflow.md document.
The front-end will have multiple pages, with the first/main one being a kanban board that shows in real time the porgress of the agents
The agents will be spawn via a claude cli (using my claude pro max plan), I already have some example of implementation.
for testing purposed I have created a dedicated repo in github called farmcode-tests, where we can create issues, subissues, commetns at will.

In terms of functionality, this app is an electron app.
On startup, we need to choose a project to work on (this will ask the user to choose a local folder, basically the repo of the app we want to build, and where issues will be created and code done). We will also have the option to choose the agent to assign to one task (there maybe different agent for a different project, or different version of that agent, etc...). the idea of this app is very similar to this app (https://github.com/AndyMik90/Auto-Claude), except that will also conver the deployment phase (potentially one phase for each of the env: dev, staging, production)