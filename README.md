# AI Coding Toolkit for Plaid

A toolkit designed to accelerate Plaid integration development using AI coding assistants. This repository provides local MCP tools (mock data generation, documentation search capabilities, etc.) and product-specific guides to help developers build Plaid integrations faster and more efficiently with AI assistance.

## Plaid AI tools

The AI toolkit is part of a suite of tools to accelerate AI-powered development. Other tools include:

- [Plaid CLI](https://plaid.com/docs/resources/cli/) - Install and use the Plaid CLI to access your financial data from the terminal
- [Plaid Dashboard MCP](https://plaid.com/docs/resources/mcp/) - Access the Plaid Dashboard at runtime 
- [LLMs.txt](https://plaid.com/docs/llms.txt) - An index of markdown documentation

## Repository Structure

- `/sandbox`: Contains a sandbox MCP server implementation that helps developers integrate with Plaid more quickly by providing mock data and sandbox API access.
- `/rules`: Contains product-specific guides that can be used as instructions for AI coding assistants to accelerate Plaid integration development.

## Sandbox MCP Server

The sandbox MCP server in `/sandbox` provides tools to test Plaid integrations without using real financial data:

- **Generate mock financial data** for testing purposes
- **Search Plaid documentation** for relevant API information
- **Obtain sandbox access tokens** for testing
- **Simulate webhooks** to test application handling

See [sandbox/README.md](sandbox/README.md) for setup instructions across Claude Code, Cursor, Codex, VS Code, Claude Desktop, and Zed.

## Rules for AI Integration

The `/rules` directory contains product-specific guides for Plaid integrations. You can use them in two ways:

1. **Project instructions**: Drop the content into your AI tool's instructions file (`CLAUDE.md` for Claude Code, `AGENTS.md` for Codex, Cursor rules, etc.) so the assistant has the context automatically.
2. **Direct prompts**: Paste the content directly into a conversation with your AI assistant.

Using these rules significantly accelerates development by giving AI models the context they need to generate code for Plaid integrations.

> [!WARNING]
> These guides are designed to be used for the purpose of building a sample Plaid integration with the use of AI coding tools. You are solely responsible for ensuring the correctness, legality, security, privacy, and compliance of your own app and Plaid integration. This guide is provided under the MIT license and is provided as-is and without warranty of any kind.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
