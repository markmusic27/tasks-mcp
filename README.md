<p align="center">
  <a href="#">
    <img width="130" height="130" src="https://github.com/markmusic27/tasks-mcp/blob/main/demo/logo.png?raw=true" alt="Logo">
  </a>
  <h1 align="center"><b>tasks-mcp</b></h1>
  <p align="center">
  ✶ An MCP server for seamless Notion task management ✶
    <br />
    <a href="https://tasks-mcp-280200773515.us-west1.run.app/mcp/">Explore Tasks MCP »</a>
    <br />
    <br />
    <b>Available for </b>
    MCP-compatible clients & Claude Desktop
    <br />
  </p>
</p>

Tasks MCP is a Model Context Protocol (MCP) server that provides seamless integration with your Notion workspace for task management. It enables AI assistants to create, retrieve, and manage tasks, projects, and courses directly from your Notion databases.

> NOTE: Tasks MCP is currently in active development. Features may evolve, and we're continually working to enhance the experience.

## Features

With Tasks MCP, you can:

- **Retrieve Tasks:** Get pending tasks filtered by time range (today, tomorrow, or this week) with "Not Started" status
- **Create Tasks:** Add new tasks with title, due date, priority, and optional project/course associations
- **Manage Projects:** Fetch active projects from your Notion workspace for task organization
- **Manage Courses:** Access active courses to associate academic tasks
- **Smart Filtering:** Automatically filters tasks based on status and time ranges
- **Rich Context:** Tasks include associated project and course information for better context

## Available Tools

The MCP server provides four main tools:

### `get-tasks`
Fetches pending tasks from Notion based on time range filtering.
- **Parameters:** `time_range` (required) - One of "today", "tomorrow", or "week_from_today"
- **Returns:** List of tasks with title, due date, and associated project/course information

### `create-task`
Creates a new task in your Notion Tasks database.
- **Parameters:**
  - `title` (required) - Task description
  - `due_date` (required) - ISO date format (YYYY-MM-DD)
  - `priority` (required) - Integer 1-3 (1=highest, 3=lowest)
  - `project_id` (optional) - Related project ID
  - `course_id` (optional) - Related course ID
- **Returns:** URL to the created task in Notion

### `get-projects`
Fetches active projects from your Notion workspace.
- **Parameters:** None
- **Returns:** List of active projects with ID and title

### `get-courses`
Fetches active courses from your Notion workspace.
- **Parameters:** None
- **Returns:** List of active courses with ID, title, and description

## Motivation

Tasks MCP was created to bridge the gap between AI assistants and personal productivity systems. By providing direct access to Notion task databases through the Model Context Protocol, it enables AI assistants to understand your task context and help manage your workflow more effectively.

## Technical Overview

Tasks MCP is built using modern Python technologies and follows MCP best practices:

- **MCP Framework:** Built on the official MCP Python SDK for reliable protocol compliance
- **Notion Integration:** Uses the official Notion API client for robust database interactions
- **Starlette Web Framework:** Provides HTTP endpoints with CORS support and authentication
- **Authentication:** Bearer token authentication for secure API access
- **Environment Configuration:** Flexible configuration through environment variables and .env files
- **Error Handling:** Comprehensive error handling with detailed logging
- **Data Source Management:** Automatic retrieval of Notion database data source IDs

## Setup

1. **Environment Variables:**
   ```
   API_AUTH_TOKEN=your-api-auth-token
   NOTION_AUTH_TOKEN=your-notion-integration-token
   TASK_DATABASE=your-notion-tasks-database-id
   PROJECT_DATABASE=your-notion-projects-database-id
   COURSE_DATABASE=your-notion-courses-database-id
   ```

2. **Installation:**
   ```bash
   uv sync
   ```

3. **Running:**
   ```bash
   uv run python -m src --port 8000
   ```

## MCP Endpoint

The server is deployed and available at:
**https://tasks-mcp-280200773515.us-west1.run.app/mcp/**

For MCP client configuration, use this endpoint with proper authentication headers.

## Client Usage

### For MCP Inspector

Use these headers when connecting to the MCP server:

```json
{
  "Authorization": "Bearer YJAna9RQePF@-uVw7_qBQt*apMF4*bZZfbTcybLobw*nGKCwteJMGh",
  "Accept": "application/json, text/event-stream"
}
```

### For Claude Desktop

Add this configuration to your Claude Desktop `claude_desktop_config.json`:

```json
"mcpServers": {
    "stanford-mcp": {
      "command": "npx",
      "args": [
        "mcp-remote",
        "https://tasks-mcp-280200773515.us-west1.run.app/mcp/",
        "--header", "Authorization: Bearer YJAna9RQePF@-uVw7_qBQt*apMF4*bZZfbTcybLobw*nGKCwteJMGh",
        "--header", "Accept: application/json, text/event-stream"
      ]
    }
  },
```

**Made with 🫶 by [@markmusic27](https://x.com/markmusic27)**